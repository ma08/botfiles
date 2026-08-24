import CryptoKit
import Foundation

public let appleRemindersProtocolVersion = 1
public let appleRemindersNativeVersion = "1.0.0"
public let appleRemindersHardLimit = 500
public let appleRemindersMaxNoteBytes = 1_048_576
public let appleRemindersMaxPageNoteBytes = 8_388_608

public enum NativeProtocolError: Error, Equatable, LocalizedError {
  case invalidRequest(String)
  case invalidCursor
  case limitOutOfRange(Int)
  case contentBoundExceeded

  public var errorDescription: String? {
    switch self {
    case .invalidRequest(let message):
      message
    case .invalidCursor:
      "The pagination cursor is invalid."
    case .limitOutOfRange(let value):
      "The limit must be between 1 and \(appleRemindersHardLimit), got \(value)."
    case .contentBoundExceeded:
      "Reminder notes exceed the lossless bounded-response policy."
    }
  }
}

private struct RequestCodingKey: CodingKey {
  let stringValue: String
  let intValue: Int?

  init?(stringValue: String) {
    self.stringValue = stringValue
    self.intValue = nil
  }

  init?(intValue: Int) {
    self.stringValue = String(intValue)
    self.intValue = intValue
  }
}

private func rejectUnknownRequestFields(
  _ decoder: Decoder,
  allowed: Set<String>
) throws {
  let container = try decoder.container(keyedBy: RequestCodingKey.self)
  let unknown = Set(container.allKeys.map(\.stringValue)).subtracting(allowed)
  guard unknown.isEmpty else {
    throw DecodingError.dataCorrupted(
      DecodingError.Context(
        codingPath: decoder.codingPath,
        debugDescription: "Unsupported request fields: \(unknown.sorted().joined(separator: ", "))"
      )
    )
  }
}

public struct SourceState: Codable, Equatable, Sendable {
  public let id: String
  public let title: String
  public let type: String
  public let typeCode: Int

  public init(id: String, title: String, type: String, typeCode: Int) {
    self.id = id
    self.title = title
    self.type = type
    self.typeCode = typeCode
  }
}

public struct ReminderListState: Codable, Equatable, Sendable {
  public let id: String
  public let title: String
  public let allowsContentModifications: Bool
  public let source: SourceState

  public init(
    id: String,
    title: String,
    allowsContentModifications: Bool,
    source: SourceState
  ) {
    self.id = id
    self.title = title
    self.allowsContentModifications = allowsContentModifications
    self.source = source
  }
}

public struct DueState: Codable, Equatable, Sendable {
  public let kind: String
  public let localValue: String
  public let timeZone: String?
  public let floating: Bool
  public let components: [String: Int]

  public init(
    kind: String,
    localValue: String,
    timeZone: String?,
    floating: Bool,
    components: [String: Int]
  ) {
    self.kind = kind
    self.localValue = localValue
    self.timeZone = timeZone
    self.floating = floating
    self.components = components
  }
}

public struct RecurrenceEndState: Codable, Equatable, Sendable {
  public let occurrenceCount: Int?
  public let endDate: String?

  public init(occurrenceCount: Int?, endDate: String?) {
    self.occurrenceCount = occurrenceCount
    self.endDate = endDate
  }
}

public struct RecurrenceState: Codable, Equatable, Sendable {
  public let frequency: String
  public let interval: Int
  public let daysOfTheWeek: [Int]
  public let daysOfTheMonth: [Int]
  public let monthsOfTheYear: [Int]
  public let weeksOfTheYear: [Int]
  public let daysOfTheYear: [Int]
  public let setPositions: [Int]
  public let end: RecurrenceEndState?

  public init(
    frequency: String,
    interval: Int,
    daysOfTheWeek: [Int] = [],
    daysOfTheMonth: [Int] = [],
    monthsOfTheYear: [Int] = [],
    weeksOfTheYear: [Int] = [],
    daysOfTheYear: [Int] = [],
    setPositions: [Int] = [],
    end: RecurrenceEndState? = nil
  ) {
    self.frequency = frequency
    self.interval = interval
    self.daysOfTheWeek = daysOfTheWeek
    self.daysOfTheMonth = daysOfTheMonth
    self.monthsOfTheYear = monthsOfTheYear
    self.weeksOfTheYear = weeksOfTheYear
    self.daysOfTheYear = daysOfTheYear
    self.setPositions = setPositions
    self.end = end
  }
}

public struct AlarmLocationState: Codable, Equatable, Sendable {
  public let title: String?
  public let latitude: Double?
  public let longitude: Double?
  public let radius: Double?
  public let proximity: String?

  public init(
    title: String?,
    latitude: Double?,
    longitude: Double?,
    radius: Double?,
    proximity: String?
  ) {
    self.title = title
    self.latitude = latitude
    self.longitude = longitude
    self.radius = radius
    self.proximity = proximity
  }
}

public struct AlarmState: Codable, Equatable, Sendable {
  public let absoluteDate: String?
  public let relativeOffsetSeconds: Double?
  public let location: AlarmLocationState?

  public init(
    absoluteDate: String?,
    relativeOffsetSeconds: Double?,
    location: AlarmLocationState?
  ) {
    self.absoluteDate = absoluteDate
    self.relativeOffsetSeconds = relativeOffsetSeconds
    self.location = location
  }
}

public struct ReminderState: Codable, Equatable, Sendable {
  public let localId: String
  public let externalId: String?
  public let list: ReminderListState
  public let title: String
  public let notes: String?
  public let url: String?
  public let completed: Bool
  public let completionDate: String?
  public let creationDate: String?
  public let lastModifiedDate: String?
  public let priority: Int
  public let priorityLabel: String
  public let due: DueState?
  public let recurrence: [RecurrenceState]
  public let alarms: [AlarmState]

  public init(
    localId: String,
    externalId: String?,
    list: ReminderListState,
    title: String,
    notes: String?,
    url: String?,
    completed: Bool,
    completionDate: String?,
    creationDate: String?,
    lastModifiedDate: String?,
    priority: Int,
    priorityLabel: String,
    due: DueState?,
    recurrence: [RecurrenceState],
    alarms: [AlarmState]
  ) {
    self.localId = localId
    self.externalId = externalId
    self.list = list
    self.title = title
    self.notes = notes
    self.url = url
    self.completed = completed
    self.completionDate = completionDate
    self.creationDate = creationDate
    self.lastModifiedDate = lastModifiedDate
    self.priority = priority
    self.priorityLabel = priorityLabel
    self.due = due
    self.recurrence = recurrence
    self.alarms = alarms
  }
}

public struct ReminderSnapshot: Codable, Equatable, Sendable {
  public let state: ReminderState
  public let revision: String
  public let sortCursor: String

  public init(state: ReminderState) throws {
    self.state = state
    self.revision = try NativeProtocolSupport.sha256(state)
    self.sortCursor = NativeProtocolSupport.encodeCursor(
      [
        state.list.source.id,
        state.list.id,
        state.externalId ?? "",
        state.localId,
      ].joined(separator: "\u{1f}")
    )
  }
}

public struct NoteState: Codable, Equatable, Sendable {
  public let present: Bool
  public let length: Int
  public let sha256: String?

  public init(_ value: String?) {
    guard let value else {
      self.present = false
      self.length = 0
      self.sha256 = nil
      return
    }
    self.present = true
    self.length = value.count
    self.sha256 = SHA256.hash(data: Data(value.utf8))
      .map { String(format: "%02x", $0) }
      .joined()
  }
}

public struct RedactedReminderState: Codable, Equatable, Sendable {
  public let localId: String
  public let externalId: String?
  public let list: ReminderListState
  public let title: String
  public let notesState: NoteState
  public let url: String?
  public let completed: Bool
  public let completionDate: String?
  public let creationDate: String?
  public let lastModifiedDate: String?
  public let priority: Int
  public let priorityLabel: String
  public let due: DueState?
  public let recurrence: [RecurrenceState]
  public let alarms: [AlarmState]

  public init(_ state: ReminderState) {
    self.localId = state.localId
    self.externalId = state.externalId
    self.list = state.list
    self.title = state.title
    self.notesState = NoteState(state.notes)
    self.url = state.url
    self.completed = state.completed
    self.completionDate = state.completionDate
    self.creationDate = state.creationDate
    self.lastModifiedDate = state.lastModifiedDate
    self.priority = state.priority
    self.priorityLabel = state.priorityLabel
    self.due = state.due
    self.recurrence = state.recurrence
    self.alarms = state.alarms
  }
}

public struct RedactedReminderSnapshot: Codable, Equatable, Sendable {
  public let state: RedactedReminderState
  public let revision: String
  public let sortCursor: String

  public init(_ snapshot: ReminderSnapshot) {
    self.state = RedactedReminderState(snapshot.state)
    self.revision = snapshot.revision
    self.sortCursor = snapshot.sortCursor
  }
}

public struct NativeHealth: Codable, Equatable, Sendable {
  public let macReachable: Bool
  public let tccStatus: String
  public let authorized: Bool
  public let fetchComplete: Bool
  public let truncated: Bool
  public let cloudFreshness: String
  public let recordsExamined: Int
  public let recordsReturned: Int

  public init(
    macReachable: Bool = true,
    tccStatus: String,
    authorized: Bool,
    fetchComplete: Bool,
    truncated: Bool,
    cloudFreshness: String = "unverified",
    recordsExamined: Int,
    recordsReturned: Int
  ) {
    self.macReachable = macReachable
    self.tccStatus = tccStatus
    self.authorized = authorized
    self.fetchComplete = fetchComplete
    self.truncated = truncated
    self.cloudFreshness = cloudFreshness
    self.recordsExamined = recordsExamined
    self.recordsReturned = recordsReturned
  }
}

public struct NativeResponse<DataType: Codable & Sendable>: Codable, Sendable {
  public let protocolVersion: Int
  public let nativeVersion: String
  public let operation: String
  public let status: String
  public let health: NativeHealth
  public let data: DataType

  public init(operation: String, health: NativeHealth, data: DataType) {
    self.protocolVersion = appleRemindersProtocolVersion
    self.nativeVersion = appleRemindersNativeVersion
    self.operation = operation
    self.status = "ok"
    self.health = health
    self.data = data
  }
}

public struct EmptyData: Codable, Equatable, Sendable {
  public init() {}
}

public struct StatusData: Codable, Equatable, Sendable {
  public let tccStatus: String
  public let authorized: Bool

  public init(tccStatus: String, authorized: Bool) {
    self.tccStatus = tccStatus
    self.authorized = authorized
  }
}

public struct ListsData: Codable, Equatable, Sendable {
  public let lists: [ReminderListState]
  public let truncated: Bool

  public init(lists: [ReminderListState], truncated: Bool) {
    self.lists = lists
    self.truncated = truncated
  }
}

public struct RemindersData: Codable, Equatable, Sendable {
  public let reminders: [ReminderSnapshot]
  public let nextCursor: String?
  public let truncated: Bool

  public init(reminders: [ReminderSnapshot], nextCursor: String?, truncated: Bool) {
    self.reminders = reminders
    self.nextCursor = nextCursor
    self.truncated = truncated
  }
}

public struct RedactedRemindersData: Codable, Equatable, Sendable {
  public let reminders: [RedactedReminderSnapshot]
  public let truncated: Bool

  public init(reminders: [RedactedReminderSnapshot], truncated: Bool) {
    self.reminders = reminders
    self.truncated = truncated
  }
}

public struct ReminderData: Codable, Equatable, Sendable {
  public let reminder: ReminderSnapshot

  public init(reminder: ReminderSnapshot) {
    self.reminder = reminder
  }
}

public struct DeleteData: Codable, Equatable, Sendable {
  public let localId: String
  public let externalId: String?
  public let listId: String
  public let deleted: Bool

  public init(localId: String, externalId: String?, listId: String, deleted: Bool) {
    self.localId = localId
    self.externalId = externalId
    self.listId = listId
    self.deleted = deleted
  }
}

public struct NativeErrorBody: Codable, Equatable, Sendable {
  public let code: String
  public let message: String
  public let tccStatus: String?

  public init(code: String, message: String, tccStatus: String? = nil) {
    self.code = code
    self.message = message
    self.tccStatus = tccStatus
  }
}

public struct NativeErrorResponse: Codable, Equatable, Sendable {
  public let protocolVersion: Int
  public let nativeVersion: String
  public let status: String
  public let error: NativeErrorBody

  public init(error: NativeErrorBody) {
    self.protocolVersion = appleRemindersProtocolVersion
    self.nativeVersion = appleRemindersNativeVersion
    self.status = "error"
    self.error = error
  }
}

public struct DueInput: Codable, Equatable, Sendable {
  private enum CodingKeys: String, CodingKey {
    case kind
    case value
    case timeZone
  }

  public let kind: String
  public let value: String
  public let timeZone: String?

  public init(kind: String, value: String, timeZone: String? = nil) {
    self.kind = kind
    self.value = value
    self.timeZone = timeZone
  }

  public init(from decoder: Decoder) throws {
    try rejectUnknownRequestFields(decoder, allowed: ["kind", "value", "timeZone"])
    let container = try decoder.container(keyedBy: CodingKeys.self)
    self.kind = try container.decode(String.self, forKey: .kind)
    self.value = try container.decode(String.self, forKey: .value)
    self.timeZone = try container.decodeIfPresent(String.self, forKey: .timeZone)
  }
}

public struct RecurrenceInput: Codable, Equatable, Sendable {
  private enum CodingKeys: String, CodingKey {
    case frequency
    case interval
  }

  public let frequency: String
  public let interval: Int

  public init(frequency: String, interval: Int = 1) {
    self.frequency = frequency
    self.interval = interval
  }

  public init(from decoder: Decoder) throws {
    try rejectUnknownRequestFields(decoder, allowed: ["frequency", "interval"])
    let container = try decoder.container(keyedBy: CodingKeys.self)
    self.frequency = try container.decode(String.self, forKey: .frequency)
    self.interval = try container.decodeIfPresent(Int.self, forKey: .interval) ?? 1
  }
}

public struct AlarmInput: Codable, Equatable, Sendable {
  private enum CodingKeys: String, CodingKey {
    case absoluteDate
    case relativeOffsetSeconds
  }

  public let absoluteDate: String?
  public let relativeOffsetSeconds: Double?

  public init(absoluteDate: String? = nil, relativeOffsetSeconds: Double? = nil) {
    self.absoluteDate = absoluteDate
    self.relativeOffsetSeconds = relativeOffsetSeconds
  }

  public init(from decoder: Decoder) throws {
    try rejectUnknownRequestFields(
      decoder,
      allowed: ["absoluteDate", "relativeOffsetSeconds"]
    )
    let container = try decoder.container(keyedBy: CodingKeys.self)
    self.absoluteDate = try container.decodeIfPresent(String.self, forKey: .absoluteDate)
    self.relativeOffsetSeconds = try container.decodeIfPresent(
      Double.self,
      forKey: .relativeOffsetSeconds
    )
  }
}

public struct CreateRequest: Codable, Equatable, Sendable {
  private enum CodingKeys: String, CodingKey {
    case listId
    case title
    case notes
    case url
    case due
    case priority
    case recurrence
    case alarms
  }

  public let listId: String
  public let title: String
  public let notes: String?
  public let url: String?
  public let due: DueInput?
  public let priority: Int?
  public let recurrence: RecurrenceInput?
  public let alarms: [AlarmInput]?

  public init(
    listId: String,
    title: String,
    notes: String? = nil,
    url: String? = nil,
    due: DueInput? = nil,
    priority: Int? = nil,
    recurrence: RecurrenceInput? = nil,
    alarms: [AlarmInput]? = nil
  ) {
    self.listId = listId
    self.title = title
    self.notes = notes
    self.url = url
    self.due = due
    self.priority = priority
    self.recurrence = recurrence
    self.alarms = alarms
  }

  public init(from decoder: Decoder) throws {
    try rejectUnknownRequestFields(
      decoder,
      allowed: ["listId", "title", "notes", "url", "due", "priority", "recurrence", "alarms"]
    )
    let container = try decoder.container(keyedBy: CodingKeys.self)
    self.listId = try container.decode(String.self, forKey: .listId)
    self.title = try container.decode(String.self, forKey: .title)
    self.notes = try container.decodeIfPresent(String.self, forKey: .notes)
    self.url = try container.decodeIfPresent(String.self, forKey: .url)
    self.due = try container.decodeIfPresent(DueInput.self, forKey: .due)
    self.priority = try container.decodeIfPresent(Int.self, forKey: .priority)
    self.recurrence = try container.decodeIfPresent(RecurrenceInput.self, forKey: .recurrence)
    self.alarms = try container.decodeIfPresent([AlarmInput].self, forKey: .alarms)
  }
}

public struct UpdateFields: Codable, Equatable, Sendable {
  private enum CodingKeys: String, CodingKey {
    case title
    case notes
    case url
    case due
    case priority
    case recurrence
    case alarms
  }

  public let title: String?
  public let notes: String?
  public let url: String?
  public let due: DueInput?
  public let priority: Int?
  public let recurrence: RecurrenceInput?
  public let alarms: [AlarmInput]?

  public init(
    title: String? = nil,
    notes: String? = nil,
    url: String? = nil,
    due: DueInput? = nil,
    priority: Int? = nil,
    recurrence: RecurrenceInput? = nil,
    alarms: [AlarmInput]? = nil
  ) {
    self.title = title
    self.notes = notes
    self.url = url
    self.due = due
    self.priority = priority
    self.recurrence = recurrence
    self.alarms = alarms
  }

  public init(from decoder: Decoder) throws {
    try rejectUnknownRequestFields(
      decoder,
      allowed: ["title", "notes", "url", "due", "priority", "recurrence", "alarms"]
    )
    let container = try decoder.container(keyedBy: CodingKeys.self)
    self.title = try container.decodeIfPresent(String.self, forKey: .title)
    self.notes = try container.decodeIfPresent(String.self, forKey: .notes)
    self.url = try container.decodeIfPresent(String.self, forKey: .url)
    self.due = try container.decodeIfPresent(DueInput.self, forKey: .due)
    self.priority = try container.decodeIfPresent(Int.self, forKey: .priority)
    self.recurrence = try container.decodeIfPresent(RecurrenceInput.self, forKey: .recurrence)
    self.alarms = try container.decodeIfPresent([AlarmInput].self, forKey: .alarms)
  }

  public var populatedFields: Set<String> {
    var result = Set<String>()
    if title != nil { result.insert("title") }
    if notes != nil { result.insert("notes") }
    if url != nil { result.insert("url") }
    if due != nil { result.insert("due") }
    if priority != nil { result.insert("priority") }
    if recurrence != nil { result.insert("recurrence") }
    if alarms != nil { result.insert("alarms") }
    return result
  }
}

public struct UpdateRequest: Codable, Equatable, Sendable {
  private enum CodingKeys: String, CodingKey {
    case localId
    case expectedRevision
    case set
    case clear
    case moveToListId
  }

  public let localId: String
  public let expectedRevision: String
  public let set: UpdateFields
  public let clear: [String]
  public let moveToListId: String?

  public init(
    localId: String,
    expectedRevision: String,
    set: UpdateFields,
    clear: [String] = [],
    moveToListId: String? = nil
  ) {
    self.localId = localId
    self.expectedRevision = expectedRevision
    self.set = set
    self.clear = clear
    self.moveToListId = moveToListId
  }

  public init(from decoder: Decoder) throws {
    try rejectUnknownRequestFields(
      decoder,
      allowed: ["localId", "expectedRevision", "set", "clear", "moveToListId"]
    )
    let container = try decoder.container(keyedBy: CodingKeys.self)
    self.localId = try container.decode(String.self, forKey: .localId)
    self.expectedRevision = try container.decode(String.self, forKey: .expectedRevision)
    self.set = try container.decode(UpdateFields.self, forKey: .set)
    self.clear = try container.decodeIfPresent([String].self, forKey: .clear) ?? []
    self.moveToListId = try container.decodeIfPresent(String.self, forKey: .moveToListId)
  }
}

public struct CompletionRequest: Codable, Equatable, Sendable {
  private enum CodingKeys: String, CodingKey {
    case localId
    case expectedRevision
    case completed
  }

  public let localId: String
  public let expectedRevision: String
  public let completed: Bool

  public init(localId: String, expectedRevision: String, completed: Bool) {
    self.localId = localId
    self.expectedRevision = expectedRevision
    self.completed = completed
  }

  public init(from decoder: Decoder) throws {
    try rejectUnknownRequestFields(
      decoder,
      allowed: ["localId", "expectedRevision", "completed"]
    )
    let container = try decoder.container(keyedBy: CodingKeys.self)
    self.localId = try container.decode(String.self, forKey: .localId)
    self.expectedRevision = try container.decode(String.self, forKey: .expectedRevision)
    self.completed = try container.decode(Bool.self, forKey: .completed)
  }
}

public struct DeleteRequest: Codable, Equatable, Sendable {
  private enum CodingKeys: String, CodingKey {
    case localId
    case expectedRevision
  }

  public let localId: String
  public let expectedRevision: String

  public init(localId: String, expectedRevision: String) {
    self.localId = localId
    self.expectedRevision = expectedRevision
  }

  public init(from decoder: Decoder) throws {
    try rejectUnknownRequestFields(decoder, allowed: ["localId", "expectedRevision"])
    let container = try decoder.container(keyedBy: CodingKeys.self)
    self.localId = try container.decode(String.self, forKey: .localId)
    self.expectedRevision = try container.decode(String.self, forKey: .expectedRevision)
  }
}

public enum NativeProtocolSupport {
  public static func encoder(pretty: Bool = true) -> JSONEncoder {
    let encoder = JSONEncoder()
    encoder.outputFormatting = pretty ? [.prettyPrinted, .sortedKeys] : [.sortedKeys]
    return encoder
  }

  public static func sha256<T: Encodable>(_ value: T) throws -> String {
    let data = try encoder(pretty: false).encode(value)
    return SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
  }

  public static func validateLimit(_ value: Int) throws -> Int {
    guard (1...appleRemindersHardLimit).contains(value) else {
      throw NativeProtocolError.limitOutOfRange(value)
    }
    return value
  }

  public static func validateNoteBounds(_ notes: [String?]) throws {
    var totalBytes = 0
    for note in notes {
      let byteCount = note?.utf8.count ?? 0
      guard byteCount <= appleRemindersMaxNoteBytes else {
        throw NativeProtocolError.contentBoundExceeded
      }
      totalBytes += byteCount
      guard totalBytes <= appleRemindersMaxPageNoteBytes else {
        throw NativeProtocolError.contentBoundExceeded
      }
    }
  }

  public static func encodeCursor(_ value: String) -> String {
    Data(value.utf8).base64EncodedString()
  }

  public static func decodeCursor(_ value: String) throws -> String {
    guard let data = Data(base64Encoded: value), let decoded = String(data: data, encoding: .utf8) else {
      throw NativeProtocolError.invalidCursor
    }
    return decoded
  }

  public static func validateCreate(_ request: CreateRequest) throws {
    guard !request.listId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
      throw NativeProtocolError.invalidRequest("listId is required")
    }
    try validateTitle(request.title)
    if let priority = request.priority { try validatePriority(priority) }
    if let due = request.due { try validateDue(due) }
    if let recurrence = request.recurrence { try validateRecurrence(recurrence) }
    if let alarms = request.alarms { try validateAlarms(alarms) }
    if let url = request.url { try validateURL(url) }
  }

  public static func validateUpdate(_ request: UpdateRequest) throws {
    guard !request.localId.isEmpty, !request.expectedRevision.isEmpty else {
      throw NativeProtocolError.invalidRequest("localId and expectedRevision are required")
    }
    let clear = Set(request.clear)
    let clearable: Set<String> = ["notes", "url", "due", "recurrence", "alarms"]
    let unknown = clear.subtracting(clearable)
    guard unknown.isEmpty else {
      throw NativeProtocolError.invalidRequest("unsupported clear fields: \(unknown.sorted().joined(separator: ", "))")
    }
    let overlap = clear.intersection(request.set.populatedFields)
    guard overlap.isEmpty else {
      throw NativeProtocolError.invalidRequest("fields cannot be set and cleared together: \(overlap.sorted().joined(separator: ", "))")
    }
    let hasChange = !request.set.populatedFields.isEmpty || !clear.isEmpty || request.moveToListId != nil
    guard hasChange else {
      throw NativeProtocolError.invalidRequest("the update contains no changes")
    }
    if let title = request.set.title { try validateTitle(title) }
    if let priority = request.set.priority { try validatePriority(priority) }
    if let due = request.set.due { try validateDue(due) }
    if let recurrence = request.set.recurrence { try validateRecurrence(recurrence) }
    if let alarms = request.set.alarms { try validateAlarms(alarms) }
    if let url = request.set.url { try validateURL(url) }
    if let listId = request.moveToListId, listId.isEmpty {
      throw NativeProtocolError.invalidRequest("moveToListId cannot be empty")
    }
  }

  public static func validateCompletion(_ request: CompletionRequest) throws {
    guard !request.localId.isEmpty, !request.expectedRevision.isEmpty else {
      throw NativeProtocolError.invalidRequest("localId and expectedRevision are required")
    }
  }

  public static func validateDelete(_ request: DeleteRequest) throws {
    guard !request.localId.isEmpty, !request.expectedRevision.isEmpty else {
      throw NativeProtocolError.invalidRequest("localId and expectedRevision are required")
    }
  }

  private static func validateTitle(_ title: String) throws {
    let trimmed = title.trimmingCharacters(in: .whitespacesAndNewlines)
    guard !trimmed.isEmpty, title.count <= 1_024 else {
      throw NativeProtocolError.invalidRequest("title must contain 1 to 1024 characters")
    }
  }

  private static func validatePriority(_ priority: Int) throws {
    guard (0...9).contains(priority) else {
      throw NativeProtocolError.invalidRequest("priority must be between 0 and 9")
    }
  }

  private static func validateDue(_ due: DueInput) throws {
    let kinds = Set(["all-day", "timed", "floating"])
    guard kinds.contains(due.kind), !due.value.isEmpty else {
      throw NativeProtocolError.invalidRequest("due kind must be all-day, timed, or floating with a value")
    }
    if due.kind == "timed" {
      guard let timeZone = due.timeZone, TimeZone(identifier: timeZone) != nil else {
        throw NativeProtocolError.invalidRequest("timed due values require a valid IANA timeZone")
      }
    } else if due.timeZone != nil {
      throw NativeProtocolError.invalidRequest("only timed due values may include timeZone")
    }
  }

  private static func validateRecurrence(_ recurrence: RecurrenceInput) throws {
    let frequencies = Set(["daily", "weekly", "monthly", "yearly"])
    guard frequencies.contains(recurrence.frequency), (1...999).contains(recurrence.interval) else {
      throw NativeProtocolError.invalidRequest("recurrence must use a supported frequency and interval from 1 to 999")
    }
  }

  private static func validateAlarms(_ alarms: [AlarmInput]) throws {
    guard alarms.count <= 20 else {
      throw NativeProtocolError.invalidRequest("no more than 20 alarms are allowed")
    }
    for alarm in alarms {
      let populated = [alarm.absoluteDate != nil, alarm.relativeOffsetSeconds != nil].filter { $0 }.count
      guard populated == 1 else {
        throw NativeProtocolError.invalidRequest("each alarm requires exactly one absoluteDate or relativeOffsetSeconds")
      }
    }
  }

  private static func validateURL(_ value: String) throws {
    guard let url = URL(string: value), let scheme = url.scheme?.lowercased(), ["https", "http"].contains(scheme) else {
      throw NativeProtocolError.invalidRequest("url must be an HTTP or HTTPS URL")
    }
  }
}
