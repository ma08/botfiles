import AppleRemindersNativeCore
import CoreLocation
import CryptoKit
import Darwin
@preconcurrency import EventKit
import Foundation

private struct BridgeFailure: Error, LocalizedError {
  let code: String
  let message: String
  let exitCode: Int32
  let tccStatus: String?

  init(
    _ code: String,
    _ message: String,
    exitCode: Int32 = 70,
    tccStatus: String? = nil
  ) {
    self.code = code
    self.message = message
    self.exitCode = exitCode
    self.tccStatus = tccStatus
  }

  var errorDescription: String? { message }
}

private struct ParsedOptions {
  let values: [String: String]
  let flags: Set<String>

  init(
    _ arguments: ArraySlice<String>,
    valueNames: Set<String> = [],
    flagNames: Set<String> = []
  ) throws {
    var parsedValues: [String: String] = [:]
    var parsedFlags = Set<String>()
    var index = arguments.startIndex
    while index < arguments.endIndex {
      let argument = arguments[index]
      guard argument.hasPrefix("--") else {
        throw BridgeFailure("INVALID_ARGUMENT", "Unexpected positional argument: \(argument)", exitCode: 64)
      }
      let name = String(argument.dropFirst(2))
      if flagNames.contains(name) {
        guard parsedFlags.insert(name).inserted else {
          throw BridgeFailure("INVALID_ARGUMENT", "Duplicate flag: --\(name)", exitCode: 64)
        }
        index = arguments.index(after: index)
        continue
      }
      guard valueNames.contains(name) else {
        throw BridgeFailure("INVALID_ARGUMENT", "Unsupported option: --\(name)", exitCode: 64)
      }
      let valueIndex = arguments.index(after: index)
      guard valueIndex < arguments.endIndex else {
        throw BridgeFailure("INVALID_ARGUMENT", "Missing value for --\(name)", exitCode: 64)
      }
      guard parsedValues[name] == nil else {
        throw BridgeFailure("INVALID_ARGUMENT", "Duplicate option: --\(name)", exitCode: 64)
      }
      parsedValues[name] = arguments[valueIndex]
      index = arguments.index(after: valueIndex)
    }
    values = parsedValues
    flags = parsedFlags
  }

  func required(_ name: String) throws -> String {
    guard let value = values[name], !value.isEmpty else {
      throw BridgeFailure("INVALID_ARGUMENT", "Missing required option: --\(name)", exitCode: 64)
    }
    return value
  }

  func int(_ name: String, default defaultValue: Int) throws -> Int {
    guard let raw = values[name] else { return defaultValue }
    guard let value = Int(raw) else {
      throw BridgeFailure("INVALID_ARGUMENT", "--\(name) must be an integer", exitCode: 64)
    }
    return value
  }
}

private enum JSONIO {
  static func write<T: Encodable>(_ value: T, to handle: FileHandle = .standardOutput) throws {
    var data = try NativeProtocolSupport.encoder().encode(value)
    data.append(0x0A)
    try handle.write(contentsOf: data)
  }

  static func readRequest<T: Decodable>(
    _ type: T.Type,
    allowedKeys: Set<String>
  ) throws -> T {
    let data = try FileHandle.standardInput.readToEnd() ?? Data()
    guard !data.isEmpty else {
      throw BridgeFailure("INVALID_REQUEST", "A JSON request is required on standard input", exitCode: 64)
    }
    guard data.count <= 1_048_576 else {
      throw BridgeFailure("INVALID_REQUEST", "The JSON request exceeds 1 MiB", exitCode: 64)
    }
    let object: Any
    do {
      object = try JSONSerialization.jsonObject(with: data)
    } catch {
      throw BridgeFailure("INVALID_REQUEST", "The request is not valid JSON", exitCode: 64)
    }
    guard let dictionary = object as? [String: Any] else {
      throw BridgeFailure("INVALID_REQUEST", "The request must be a JSON object", exitCode: 64)
    }
    let unknown = Set(dictionary.keys).subtracting(allowedKeys)
    guard unknown.isEmpty else {
      throw BridgeFailure(
        "INVALID_REQUEST",
        "Unsupported request fields: \(unknown.sorted().joined(separator: ", "))",
        exitCode: 64
      )
    }
    do {
      return try JSONDecoder().decode(type, from: data)
    } catch {
      throw BridgeFailure("INVALID_REQUEST", "The request does not match the native protocol", exitCode: 64)
    }
  }
}

private actor BridgeStore {
  private let eventStore = EKEventStore()

  static func authorizationStatusName() -> String {
    switch EKEventStore.authorizationStatus(for: .reminder) {
    case .notDetermined:
      "not-determined"
    case .restricted:
      "restricted"
    case .denied:
      "denied"
    case .writeOnly:
      "write-only"
    case .fullAccess, .authorized:
      "full-access"
    @unknown default:
      "unknown"
    }
  }

  static func isAuthorized() -> Bool {
    authorizationStatusName() == "full-access"
  }

  func authorize() async throws -> String {
    let current = Self.authorizationStatusName()
    guard current == "not-determined" else { return current }
    let granted = try await withCheckedThrowingContinuation {
      (continuation: CheckedContinuation<Bool, Error>) in
      eventStore.requestFullAccessToReminders { allowed, error in
        if let error {
          continuation.resume(throwing: error)
        } else {
          continuation.resume(returning: allowed)
        }
      }
    }
    return granted ? "full-access" : Self.authorizationStatusName()
  }

  func lists(limit: Int) throws -> (items: [ReminderListState], examined: Int, truncated: Bool) {
    try requireFullAccess()
    let all = eventStore.calendars(for: .reminder)
      .map(Self.listState)
      .sorted {
        if $0.source.id != $1.source.id { return $0.source.id < $1.source.id }
        let titleComparison = $0.title.localizedStandardCompare($1.title)
        if titleComparison != .orderedSame { return titleComparison == .orderedAscending }
        return $0.id < $1.id
      }
    return (Array(all.prefix(limit)), all.count, all.count > limit)
  }

  func scan(
    listId: String?,
    includeCompleted: Bool,
    afterCursor: String?,
    limit: Int
  ) async throws -> (items: [ReminderSnapshot], examined: Int, truncated: Bool, nextCursor: String?) {
    try requireFullAccess()
    let calendars = try selectedCalendars(listId: listId)
    let states = try await fetchStates(calendars: calendars)
    let examined = states.count
    var snapshots = try states
      .filter { includeCompleted || !$0.completed }
      .map(ReminderSnapshot.init)
      .sorted { $0.sortCursor < $1.sortCursor }
    if let afterCursor {
      let decoded = try NativeProtocolSupport.decodeCursor(afterCursor)
      snapshots = snapshots.filter {
        let raw = (try? NativeProtocolSupport.decodeCursor($0.sortCursor)) ?? ""
        return raw > decoded
      }
    }
    let truncated = snapshots.count > limit
    let selected = Array(snapshots.prefix(limit))
    try NativeProtocolSupport.validateNoteBounds(selected.map { $0.state.notes })
    return (selected, examined, truncated, truncated ? selected.last?.sortCursor : nil)
  }

  func search(
    query: String,
    listId: String?,
    includeCompleted: Bool,
    limit: Int
  ) async throws -> (items: [ReminderSnapshot], examined: Int, truncated: Bool) {
    try requireFullAccess()
    let needle = query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    guard !needle.isEmpty, needle.count <= 512 else {
      throw BridgeFailure("INVALID_ARGUMENT", "Search query must contain 1 to 512 characters", exitCode: 64)
    }
    let states = try await fetchStates(calendars: try selectedCalendars(listId: listId))
    let matches = try states
      .filter { state in
        guard includeCompleted || !state.completed else { return false }
        return state.title.lowercased().contains(needle)
          || (state.notes?.lowercased().contains(needle) ?? false)
          || (state.url?.lowercased().contains(needle) ?? false)
      }
      .map(ReminderSnapshot.init)
      .sorted { $0.sortCursor < $1.sortCursor }
    let selected = Array(matches.prefix(limit))
    try NativeProtocolSupport.validateNoteBounds(selected.map { $0.state.notes })
    return (selected, states.count, matches.count > limit)
  }

  func get(localId: String) throws -> ReminderSnapshot {
    try requireFullAccess()
    let reminder = try ReminderSnapshot(state: stateForLocalId(localId))
    try NativeProtocolSupport.validateNoteBounds([reminder.state.notes])
    return reminder
  }

  func get(listId: String, externalId: String) async throws -> ReminderSnapshot {
    try requireFullAccess()
    guard !externalId.isEmpty else {
      throw BridgeFailure("INVALID_ARGUMENT", "external-id cannot be empty", exitCode: 64)
    }
    let states = try await fetchStates(calendars: try selectedCalendars(listId: listId))
      .filter { $0.externalId == externalId }
    guard !states.isEmpty else {
      throw BridgeFailure("NOT_FOUND", "No reminder matches the exact external identifier", exitCode: 66)
    }
    guard states.count == 1 else {
      throw BridgeFailure("AMBIGUOUS_IDENTITY", "Multiple reminders match the external identifier", exitCode: 65)
    }
    let reminder = try ReminderSnapshot(state: states[0])
    try NativeProtocolSupport.validateNoteBounds([reminder.state.notes])
    return reminder
  }

  func create(_ request: CreateRequest) throws -> ReminderSnapshot {
    try requireFullAccess()
    try NativeProtocolSupport.validateCreate(request)
    let calendar = try exactCalendar(id: request.listId, requireWritable: true)
    let reminder = EKReminder(eventStore: eventStore)
    reminder.calendar = calendar
    reminder.title = request.title
    reminder.notes = request.notes
    reminder.priority = request.priority ?? 0
    if let url = request.url { reminder.url = URL(string: url) }
    if let due = request.due { reminder.dueDateComponents = try Self.dueComponents(due) }
    if let recurrence = request.recurrence {
      reminder.addRecurrenceRule(try Self.recurrenceRule(recurrence))
    }
    if let alarms = request.alarms {
      for alarm in alarms { reminder.addAlarm(try Self.alarm(alarm)) }
    }
    do {
      try eventStore.save(reminder, commit: true)
    } catch {
      throw BridgeFailure("EVENTKIT_WRITE_FAILED", "EventKit could not create the reminder")
    }
    return try ReminderSnapshot(state: Self.reminderState(reminder))
  }

  func update(_ request: UpdateRequest) throws -> ReminderSnapshot {
    try requireFullAccess()
    try NativeProtocolSupport.validateUpdate(request)
    let reminder = try exactReminder(id: request.localId)
    try requireRevision(request.expectedRevision, reminder: reminder)
    let fields = request.set
    if let title = fields.title { reminder.title = title }
    if let notes = fields.notes { reminder.notes = notes }
    if let url = fields.url { reminder.url = URL(string: url) }
    if let due = fields.due { reminder.dueDateComponents = try Self.dueComponents(due) }
    if let priority = fields.priority { reminder.priority = priority }
    if let recurrence = fields.recurrence {
      Self.clearRecurrence(reminder)
      reminder.addRecurrenceRule(try Self.recurrenceRule(recurrence))
    }
    if let alarms = fields.alarms {
      Self.clearAlarms(reminder)
      for alarm in alarms { reminder.addAlarm(try Self.alarm(alarm)) }
    }
    let clear = Set(request.clear)
    if clear.contains("notes") { reminder.notes = nil }
    if clear.contains("url") { reminder.url = nil }
    if clear.contains("due") { reminder.dueDateComponents = nil }
    if clear.contains("recurrence") { Self.clearRecurrence(reminder) }
    if clear.contains("alarms") { Self.clearAlarms(reminder) }
    if let target = request.moveToListId {
      reminder.calendar = try exactCalendar(id: target, requireWritable: true)
    }
    try save(reminder, operation: "update")
    return try ReminderSnapshot(state: Self.reminderState(reminder))
  }

  func setCompleted(_ request: CompletionRequest) throws -> ReminderSnapshot {
    try requireFullAccess()
    try NativeProtocolSupport.validateCompletion(request)
    let reminder = try exactReminder(id: request.localId)
    try requireRevision(request.expectedRevision, reminder: reminder)
    reminder.isCompleted = request.completed
    try save(reminder, operation: request.completed ? "complete" : "reopen")
    return try ReminderSnapshot(state: Self.reminderState(reminder))
  }

  func delete(_ request: DeleteRequest) throws -> DeleteData {
    try requireFullAccess()
    try NativeProtocolSupport.validateDelete(request)
    let reminder = try exactReminder(id: request.localId)
    try requireRevision(request.expectedRevision, reminder: reminder)
    let state = Self.reminderState(reminder)
    do {
      try eventStore.remove(reminder, commit: true)
    } catch {
      throw BridgeFailure("EVENTKIT_WRITE_FAILED", "EventKit could not delete the reminder")
    }
    if eventStore.calendarItem(withIdentifier: request.localId) != nil {
      throw BridgeFailure("WRITE_VERIFICATION_FAILED", "The reminder still exists after deletion")
    }
    return DeleteData(
      localId: state.localId,
      externalId: state.externalId,
      listId: state.list.id,
      deleted: true
    )
  }

  private func requireFullAccess() throws {
    let status = Self.authorizationStatusName()
    guard status == "full-access" else {
      let code: String
      switch status {
      case "not-determined": code = "TCC_NOT_DETERMINED"
      case "denied": code = "TCC_DENIED"
      case "restricted": code = "TCC_RESTRICTED"
      case "write-only": code = "TCC_WRITE_ONLY"
      default: code = "TCC_UNKNOWN"
      }
      throw BridgeFailure(code, "Full Apple Reminders access is not available", exitCode: 77, tccStatus: status)
    }
  }

  private func exactReminder(id: String) throws -> EKReminder {
    guard !id.isEmpty, let reminder = eventStore.calendarItem(withIdentifier: id) as? EKReminder else {
      throw BridgeFailure("NOT_FOUND", "No reminder matches the exact local identifier", exitCode: 66)
    }
    return reminder
  }

  private func stateForLocalId(_ id: String) throws -> ReminderState {
    Self.reminderState(try exactReminder(id: id))
  }

  private func exactCalendar(id: String, requireWritable: Bool) throws -> EKCalendar {
    let matches = eventStore.calendars(for: .reminder).filter { $0.calendarIdentifier == id }
    guard matches.count == 1, let calendar = matches.first else {
      throw BridgeFailure("LIST_NOT_FOUND", "No Reminder list matches the exact list identifier", exitCode: 66)
    }
    if requireWritable, !calendar.allowsContentModifications {
      throw BridgeFailure("LIST_READ_ONLY", "The selected Reminder list is not writable", exitCode: 77)
    }
    return calendar
  }

  private func selectedCalendars(listId: String?) throws -> [EKCalendar] {
    if let listId { return [try exactCalendar(id: listId, requireWritable: false)] }
    return eventStore.calendars(for: .reminder)
  }

  private func requireRevision(_ expected: String, reminder: EKReminder) throws {
    let actual = try ReminderSnapshot(state: Self.reminderState(reminder)).revision
    guard actual == expected else {
      throw BridgeFailure("DRIFT", "The reminder changed after preview; generate a new preview", exitCode: 75)
    }
  }

  private func save(_ reminder: EKReminder, operation: String) throws {
    do {
      try eventStore.save(reminder, commit: true)
    } catch {
      throw BridgeFailure("EVENTKIT_WRITE_FAILED", "EventKit could not \(operation) the reminder")
    }
  }

  private func fetchStates(calendars: [EKCalendar]) async throws -> [ReminderState] {
    let states = await withCheckedContinuation {
      (continuation: CheckedContinuation<[ReminderState]?, Never>) in
      let predicate = eventStore.predicateForReminders(in: calendars)
      eventStore.fetchReminders(matching: predicate) { reminders in
        continuation.resume(returning: reminders?.map(Self.reminderState))
      }
    }
    guard let states else {
      throw BridgeFailure(
        "FETCH_INCOMPLETE",
        "EventKit did not return a complete Reminders result"
      )
    }
    return states
  }

  private static func sourceType(_ type: EKSourceType) -> String {
    switch type {
    case .local: "local"
    case .exchange: "exchange"
    case .calDAV: "caldav"
    case .mobileMe: "mobileme"
    case .subscribed: "subscribed"
    case .birthdays: "birthdays"
    @unknown default: "unknown"
    }
  }

  private static func sourceState(_ source: EKSource) -> SourceState {
    SourceState(
      id: source.sourceIdentifier,
      title: source.title,
      type: sourceType(source.sourceType),
      typeCode: source.sourceType.rawValue
    )
  }

  private static func listState(_ calendar: EKCalendar) -> ReminderListState {
    ReminderListState(
      id: calendar.calendarIdentifier,
      title: calendar.title,
      allowsContentModifications: calendar.allowsContentModifications,
      source: sourceState(calendar.source)
    )
  }

  private static func reminderState(_ reminder: EKReminder) -> ReminderState {
    ReminderState(
      localId: reminder.calendarItemIdentifier,
      externalId: reminder.calendarItemExternalIdentifier,
      list: listState(reminder.calendar),
      title: reminder.title ?? "",
      notes: reminder.notes,
      url: reminder.url?.absoluteString,
      completed: reminder.isCompleted,
      completionDate: isoDate(reminder.completionDate),
      creationDate: isoDate(reminder.creationDate),
      lastModifiedDate: isoDate(reminder.lastModifiedDate),
      priority: reminder.priority,
      priorityLabel: priorityLabel(reminder.priority),
      due: dueState(reminder.dueDateComponents),
      recurrence: (reminder.recurrenceRules ?? []).map(recurrenceState),
      alarms: (reminder.alarms ?? []).map(alarmState)
    )
  }

  private static func isoDate(_ date: Date?) -> String? {
    guard let date else { return nil }
    let formatter = ISO8601DateFormatter()
    formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
    return formatter.string(from: date)
  }

  private static func dueState(_ components: DateComponents?) -> DueState? {
    guard let components, let year = components.year, let month = components.month, let day = components.day else {
      return nil
    }
    var values = ["year": year, "month": month, "day": day]
    let isAllDay = components.hour == nil && components.minute == nil && components.second == nil
    if let hour = components.hour { values["hour"] = hour }
    if let minute = components.minute { values["minute"] = minute }
    if let second = components.second { values["second"] = second }
    let value: String
    if isAllDay {
      value = String(format: "%04d-%02d-%02d", year, month, day)
    } else {
      value = String(
        format: "%04d-%02d-%02dT%02d:%02d:%02d",
        year,
        month,
        day,
        components.hour ?? 0,
        components.minute ?? 0,
        components.second ?? 0
      )
    }
    let timeZone = components.timeZone?.identifier
    return DueState(
      kind: isAllDay ? "all-day" : (timeZone == nil ? "floating" : "timed"),
      localValue: value,
      timeZone: timeZone,
      floating: !isAllDay && timeZone == nil,
      components: values
    )
  }

  private static func recurrenceState(_ rule: EKRecurrenceRule) -> RecurrenceState {
    let frequency: String
    switch rule.frequency {
    case .daily: frequency = "daily"
    case .weekly: frequency = "weekly"
    case .monthly: frequency = "monthly"
    case .yearly: frequency = "yearly"
    @unknown default: frequency = "unknown"
    }
    let end = rule.recurrenceEnd.map {
      RecurrenceEndState(
        occurrenceCount: $0.occurrenceCount == 0 ? nil : $0.occurrenceCount,
        endDate: isoDate($0.endDate)
      )
    }
    return RecurrenceState(
      frequency: frequency,
      interval: rule.interval,
      daysOfTheWeek: (rule.daysOfTheWeek ?? []).map { $0.dayOfTheWeek.rawValue },
      daysOfTheMonth: (rule.daysOfTheMonth ?? []).map(\.intValue),
      monthsOfTheYear: (rule.monthsOfTheYear ?? []).map(\.intValue),
      weeksOfTheYear: (rule.weeksOfTheYear ?? []).map(\.intValue),
      daysOfTheYear: (rule.daysOfTheYear ?? []).map(\.intValue),
      setPositions: (rule.setPositions ?? []).map(\.intValue),
      end: end
    )
  }

  private static func alarmState(_ alarm: EKAlarm) -> AlarmState {
    let structured = alarm.structuredLocation.map {
      AlarmLocationState(
        title: $0.title,
        latitude: $0.geoLocation?.coordinate.latitude,
        longitude: $0.geoLocation?.coordinate.longitude,
        radius: $0.radius,
        proximity: proximityName(alarm.proximity)
      )
    }
    return AlarmState(
      absoluteDate: isoDate(alarm.absoluteDate),
      relativeOffsetSeconds: alarm.absoluteDate == nil ? alarm.relativeOffset : nil,
      location: structured
    )
  }

  private static func proximityName(_ value: EKAlarmProximity) -> String? {
    switch value {
    case .none: nil
    case .enter: "enter"
    case .leave: "leave"
    @unknown default: "unknown"
    }
  }

  private static func priorityLabel(_ priority: Int) -> String {
    switch priority {
    case 1...4: "high"
    case 5: "medium"
    case 6...9: "low"
    default: "none"
    }
  }

  private static func dueComponents(_ input: DueInput) throws -> DateComponents {
    try NativeProtocolSupport.validateCreate(
      CreateRequest(listId: "validation", title: "validation", due: input)
    )
    switch input.kind {
    case "all-day":
      let parts = try parseDate(input.value)
      var components = DateComponents()
      components.calendar = Calendar(identifier: .gregorian)
      components.year = parts.0
      components.month = parts.1
      components.day = parts.2
      return components
    case "timed", "floating":
      let parts = try parseDateTime(input.value)
      var components = DateComponents()
      components.calendar = Calendar(identifier: .gregorian)
      components.year = parts.0
      components.month = parts.1
      components.day = parts.2
      components.hour = parts.3
      components.minute = parts.4
      components.second = parts.5
      if input.kind == "timed", let identifier = input.timeZone {
        components.timeZone = TimeZone(identifier: identifier)
      }
      guard components.calendar?.date(from: components) != nil else {
        throw BridgeFailure("INVALID_REQUEST", "The due value is not a valid calendar date", exitCode: 64)
      }
      return components
    default:
      throw BridgeFailure("INVALID_REQUEST", "Unsupported due kind", exitCode: 64)
    }
  }

  private static func parseDate(_ value: String) throws -> (Int, Int, Int) {
    let parts = value.split(separator: "-", omittingEmptySubsequences: false)
    guard parts.count == 3,
      parts[0].count == 4,
      parts[1].count == 2,
      parts[2].count == 2,
      let year = Int(parts[0]),
      let month = Int(parts[1]),
      let day = Int(parts[2])
    else {
      throw BridgeFailure("INVALID_REQUEST", "All-day due values must use YYYY-MM-DD", exitCode: 64)
    }
    var components = DateComponents()
    components.calendar = Calendar(identifier: .gregorian)
    components.year = year
    components.month = month
    components.day = day
    guard let date = components.calendar?.date(from: components) else {
      throw BridgeFailure("INVALID_REQUEST", "The due date is invalid", exitCode: 64)
    }
    let roundTrip = components.calendar?.dateComponents([.year, .month, .day], from: date)
    guard roundTrip?.year == year, roundTrip?.month == month, roundTrip?.day == day else {
      throw BridgeFailure("INVALID_REQUEST", "The due date is invalid", exitCode: 64)
    }
    return (year, month, day)
  }

  private static func parseDateTime(_ value: String) throws -> (Int, Int, Int, Int, Int, Int) {
    let components = value.split(separator: "T", omittingEmptySubsequences: false)
    guard components.count == 2 else {
      throw BridgeFailure("INVALID_REQUEST", "Timed due values must use YYYY-MM-DDTHH:MM:SS", exitCode: 64)
    }
    let date = try parseDate(String(components[0]))
    let time = components[1].split(separator: ":", omittingEmptySubsequences: false)
    guard time.count == 3,
      time.allSatisfy({ $0.count == 2 }),
      let hour = Int(time[0]),
      let minute = Int(time[1]),
      let second = Int(time[2]),
      (0...23).contains(hour),
      (0...59).contains(minute),
      (0...59).contains(second)
    else {
      throw BridgeFailure("INVALID_REQUEST", "Timed due values must use YYYY-MM-DDTHH:MM:SS", exitCode: 64)
    }
    return (date.0, date.1, date.2, hour, minute, second)
  }

  private static func recurrenceRule(_ input: RecurrenceInput) throws -> EKRecurrenceRule {
    let frequency: EKRecurrenceFrequency
    switch input.frequency {
    case "daily": frequency = .daily
    case "weekly": frequency = .weekly
    case "monthly": frequency = .monthly
    case "yearly": frequency = .yearly
    default:
      throw BridgeFailure("INVALID_REQUEST", "Unsupported recurrence frequency", exitCode: 64)
    }
    return EKRecurrenceRule(recurrenceWith: frequency, interval: input.interval, end: nil)
  }

  private static func alarm(_ input: AlarmInput) throws -> EKAlarm {
    if let dateValue = input.absoluteDate {
      let formatter = ISO8601DateFormatter()
      formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
      let date = formatter.date(from: dateValue) ?? {
        formatter.formatOptions = [.withInternetDateTime]
        return formatter.date(from: dateValue)
      }()
      guard let date else {
        throw BridgeFailure("INVALID_REQUEST", "Alarm absoluteDate must be RFC 3339", exitCode: 64)
      }
      return EKAlarm(absoluteDate: date)
    }
    if let relative = input.relativeOffsetSeconds {
      return EKAlarm(relativeOffset: relative)
    }
    throw BridgeFailure("INVALID_REQUEST", "Alarm requires one value", exitCode: 64)
  }

  private static func clearRecurrence(_ reminder: EKReminder) {
    for rule in reminder.recurrenceRules ?? [] { reminder.removeRecurrenceRule(rule) }
  }

  private static func clearAlarms(_ reminder: EKReminder) {
    for alarm in reminder.alarms ?? [] { reminder.removeAlarm(alarm) }
  }
}

@main
private enum AppleRemindersNativeMain {
  static func main() async {
    do {
      try await run()
    } catch let failure as BridgeFailure {
      emitError(failure)
    } catch let failure as NativeProtocolError {
      let code: String
      let exitCode: Int32
      switch failure {
      case .contentBoundExceeded:
        code = "CONTENT_BOUND_EXCEEDED"
        exitCode = 65
      default:
        code = "INVALID_REQUEST"
        exitCode = 64
      }
      emitError(
        BridgeFailure(code, failure.localizedDescription, exitCode: exitCode)
      )
    } catch {
      emitError(
        BridgeFailure("NATIVE_FAILURE", "The Apple Reminders native helper failed")
      )
    }
  }

  private static func run() async throws {
    var arguments = CommandLine.arguments.dropFirst()
    guard let command = arguments.first else {
      throw BridgeFailure("INVALID_ARGUMENT", usage, exitCode: 64)
    }
    arguments = arguments.dropFirst()

    switch command {
    case "version":
      _ = try ParsedOptions(arguments)
      let status = BridgeStore.authorizationStatusName()
      try JSONIO.write(
        NativeResponse(
          operation: "version",
          health: health(status: status, fetchComplete: true),
          data: [
            "protocolVersion": String(appleRemindersProtocolVersion),
            "nativeVersion": appleRemindersNativeVersion,
          ]
        )
      )
    case "status":
      _ = try ParsedOptions(arguments)
      let status = BridgeStore.authorizationStatusName()
      try JSONIO.write(
        NativeResponse(
          operation: "status",
          health: health(status: status, fetchComplete: true),
          data: StatusData(tccStatus: status, authorized: status == "full-access")
        )
      )
    case "authorize":
      _ = try ParsedOptions(arguments)
      let store = BridgeStore()
      let status = try await store.authorize()
      try JSONIO.write(
        NativeResponse(
          operation: "authorize",
          health: health(status: status, fetchComplete: true),
          data: StatusData(tccStatus: status, authorized: status == "full-access")
        )
      )
    case "lists":
      let options = try ParsedOptions(arguments, valueNames: ["limit"])
      let limit = try NativeProtocolSupport.validateLimit(options.int("limit", default: 100))
      let store = BridgeStore()
      let result = try await store.lists(limit: limit)
      let status = BridgeStore.authorizationStatusName()
      try JSONIO.write(
        NativeResponse(
          operation: "lists",
          health: health(
            status: status,
            fetchComplete: true,
            truncated: result.truncated,
            examined: result.examined,
            returned: result.items.count
          ),
          data: ListsData(lists: result.items, truncated: result.truncated)
        )
      )
    case "scan":
      let options = try ParsedOptions(
        arguments,
        valueNames: ["list-id", "limit", "after"],
        flagNames: ["include-completed"]
      )
      let limit = try NativeProtocolSupport.validateLimit(options.int("limit", default: 100))
      let store = BridgeStore()
      let result = try await store.scan(
        listId: options.values["list-id"],
        includeCompleted: options.flags.contains("include-completed"),
        afterCursor: options.values["after"],
        limit: limit
      )
      let status = BridgeStore.authorizationStatusName()
      try JSONIO.write(
        NativeResponse(
          operation: "scan",
          health: health(
            status: status,
            fetchComplete: true,
            truncated: result.truncated,
            examined: result.examined,
            returned: result.items.count
          ),
          data: RemindersData(
            reminders: result.items,
            nextCursor: result.nextCursor,
            truncated: result.truncated
          )
        )
      )
    case "search":
      let options = try ParsedOptions(
        arguments,
        valueNames: ["query", "list-id", "limit"],
        flagNames: ["include-completed"]
      )
      let limit = try NativeProtocolSupport.validateLimit(options.int("limit", default: 50))
      let store = BridgeStore()
      let result = try await store.search(
        query: options.required("query"),
        listId: options.values["list-id"],
        includeCompleted: options.flags.contains("include-completed"),
        limit: limit
      )
      let status = BridgeStore.authorizationStatusName()
      let redacted = result.items.map(RedactedReminderSnapshot.init)
      try JSONIO.write(
        NativeResponse(
          operation: "search",
          health: health(
            status: status,
            fetchComplete: true,
            truncated: result.truncated,
            examined: result.examined,
            returned: result.items.count
          ),
          data: RedactedRemindersData(reminders: redacted, truncated: result.truncated)
        )
      )
    case "get":
      let options = try ParsedOptions(
        arguments,
        valueNames: ["local-id", "external-id", "list-id"]
      )
      let reminder: ReminderSnapshot
      let store = BridgeStore()
      if let localId = options.values["local-id"] {
        guard options.values["external-id"] == nil, options.values["list-id"] == nil else {
          throw BridgeFailure("INVALID_ARGUMENT", "Use local-id alone or external-id with list-id", exitCode: 64)
        }
        reminder = try await store.get(localId: localId)
      } else {
        reminder = try await store.get(
          listId: options.required("list-id"),
          externalId: options.required("external-id")
        )
      }
      let status = BridgeStore.authorizationStatusName()
      try JSONIO.write(
        NativeResponse(
          operation: "get",
          health: health(status: status, fetchComplete: true, examined: 1, returned: 1),
          data: ReminderData(reminder: reminder)
        )
      )
    case "create":
      _ = try ParsedOptions(arguments)
      let request = try JSONIO.readRequest(
        CreateRequest.self,
        allowedKeys: ["listId", "title", "notes", "url", "due", "priority", "recurrence", "alarms"]
      )
      let store = BridgeStore()
      let reminder = try await store.create(request)
      let status = BridgeStore.authorizationStatusName()
      try JSONIO.write(
        NativeResponse(
          operation: "create",
          health: health(status: status, fetchComplete: true, examined: 1, returned: 1),
          data: ReminderData(reminder: reminder)
        )
      )
    case "update":
      _ = try ParsedOptions(arguments)
      let request = try JSONIO.readRequest(
        UpdateRequest.self,
        allowedKeys: ["localId", "expectedRevision", "set", "clear", "moveToListId"]
      )
      let store = BridgeStore()
      let reminder = try await store.update(request)
      let status = BridgeStore.authorizationStatusName()
      try JSONIO.write(
        NativeResponse(
          operation: "update",
          health: health(status: status, fetchComplete: true, examined: 1, returned: 1),
          data: ReminderData(reminder: reminder)
        )
      )
    case "set-completed":
      _ = try ParsedOptions(arguments)
      let request = try JSONIO.readRequest(
        CompletionRequest.self,
        allowedKeys: ["localId", "expectedRevision", "completed"]
      )
      let store = BridgeStore()
      let reminder = try await store.setCompleted(request)
      let status = BridgeStore.authorizationStatusName()
      try JSONIO.write(
        NativeResponse(
          operation: request.completed ? "complete" : "reopen",
          health: health(status: status, fetchComplete: true, examined: 1, returned: 1),
          data: ReminderData(reminder: reminder)
        )
      )
    case "delete":
      _ = try ParsedOptions(arguments)
      let request = try JSONIO.readRequest(
        DeleteRequest.self,
        allowedKeys: ["localId", "expectedRevision"]
      )
      let store = BridgeStore()
      let result = try await store.delete(request)
      let status = BridgeStore.authorizationStatusName()
      try JSONIO.write(
        NativeResponse(
          operation: "delete",
          health: health(status: status, fetchComplete: true, examined: 1, returned: 0),
          data: result
        )
      )
    default:
      throw BridgeFailure("INVALID_ARGUMENT", "Unsupported command: \(command)\n\(usage)", exitCode: 64)
    }
  }

  private static func health(
    status: String,
    fetchComplete: Bool,
    truncated: Bool = false,
    examined: Int = 0,
    returned: Int = 0
  ) -> NativeHealth {
    NativeHealth(
      tccStatus: status,
      authorized: status == "full-access",
      fetchComplete: fetchComplete,
      truncated: truncated,
      recordsExamined: examined,
      recordsReturned: returned
    )
  }

  private static func emitError(_ failure: BridgeFailure) -> Never {
    let response = NativeErrorResponse(
      error: NativeErrorBody(
        code: failure.code,
        message: failure.message,
        tccStatus: failure.tccStatus
      )
    )
    try? JSONIO.write(response, to: .standardError)
    Darwin.exit(failure.exitCode)
  }

  private static let usage = """
    Usage: apple-reminders-native <command> [options]

    Read-only: version, status, lists, scan, search, get
    Permission: authorize
    Exact writes via JSON stdin: create, update, set-completed, delete
    """
}
