import Foundation
import Testing

@testable import AppleRemindersNativeCore

@Test func reminderRevisionIsDeterministicAndContentSensitive() throws {
  let source = SourceState(id: "source", title: "iCloud", type: "caldav", typeCode: 2)
  let list = ReminderListState(
    id: "list",
    title: "Reminders",
    allowsContentModifications: true,
    source: source
  )
  let state = ReminderState(
    localId: "local",
    externalId: "external",
    list: list,
    title: "Fixture",
    notes: nil,
    url: nil,
    completed: false,
    completionDate: nil,
    creationDate: "2026-08-14T20:00:00Z",
    lastModifiedDate: "2026-08-14T20:00:00Z",
    priority: 0,
    priorityLabel: "none",
    due: nil,
    recurrence: [],
    alarms: []
  )

  let first = try ReminderSnapshot(state: state)
  let second = try ReminderSnapshot(state: state)
  #expect(first.revision == second.revision)
  #expect(first.sortCursor == second.sortCursor)

  let changed = ReminderState(
    localId: state.localId,
    externalId: state.externalId,
    list: state.list,
    title: "Changed",
    notes: state.notes,
    url: state.url,
    completed: state.completed,
    completionDate: state.completionDate,
    creationDate: state.creationDate,
    lastModifiedDate: state.lastModifiedDate,
    priority: state.priority,
    priorityLabel: state.priorityLabel,
    due: state.due,
    recurrence: state.recurrence,
    alarms: state.alarms
  )
  #expect(try ReminderSnapshot(state: changed).revision != first.revision)
}

@Test func cursorRoundTripsAndRejectsGarbage() throws {
  let raw = "source\u{1f}list\u{1f}external\u{1f}local"
  let encoded = NativeProtocolSupport.encodeCursor(raw)
  #expect(try NativeProtocolSupport.decodeCursor(encoded) == raw)
  #expect(throws: NativeProtocolError.invalidCursor) {
    try NativeProtocolSupport.decodeCursor("%%%")
  }
}

@Test func createRequiresExplicitListAndExactTimedZone() throws {
  #expect(throws: NativeProtocolError.self) {
    try NativeProtocolSupport.validateCreate(CreateRequest(listId: "", title: "Fixture"))
  }
  #expect(throws: NativeProtocolError.self) {
    try NativeProtocolSupport.validateCreate(
      CreateRequest(
        listId: "list",
        title: "Fixture",
        due: DueInput(kind: "timed", value: "2026-09-18T09:00:00")
      )
    )
  }
  try NativeProtocolSupport.validateCreate(
    CreateRequest(
      listId: "list",
      title: "Fixture",
      due: DueInput(
        kind: "timed",
        value: "2026-09-18T09:00:00",
        timeZone: "America/Los_Angeles"
      )
    )
  )
}

@Test func updateRejectsSetClearOverlapAndNoOp() throws {
  #expect(throws: NativeProtocolError.self) {
    try NativeProtocolSupport.validateUpdate(
      UpdateRequest(
        localId: "local",
        expectedRevision: "revision",
        set: UpdateFields(notes: "new"),
        clear: ["notes"]
      )
    )
  }
  #expect(throws: NativeProtocolError.self) {
    try NativeProtocolSupport.validateUpdate(
      UpdateRequest(
        localId: "local",
        expectedRevision: "revision",
        set: UpdateFields()
      )
    )
  }
}

@Test func alarmsRequireOneModeAndRespectHardCap() throws {
  #expect(throws: NativeProtocolError.self) {
    try NativeProtocolSupport.validateCreate(
      CreateRequest(
        listId: "list",
        title: "Fixture",
        alarms: [AlarmInput(absoluteDate: "2026-09-18T16:00:00Z", relativeOffsetSeconds: -600)]
      )
    )
  }
  #expect(throws: NativeProtocolError.self) {
    try NativeProtocolSupport.validateLimit(appleRemindersHardLimit + 1)
  }
}

@Test func redactedSearchSnapshotKeepsIdentityRevisionAndOnlyNoteMetadata() throws {
  let source = SourceState(id: "source", title: "iCloud", type: "caldav", typeCode: 2)
  let list = ReminderListState(
    id: "list",
    title: "Reminders",
    allowsContentModifications: true,
    source: source
  )
  let state = ReminderState(
    localId: "local",
    externalId: "external",
    list: list,
    title: "Fixture",
    notes: "private note text",
    url: nil,
    completed: false,
    completionDate: nil,
    creationDate: nil,
    lastModifiedDate: nil,
    priority: 0,
    priorityLabel: "none",
    due: nil,
    recurrence: [],
    alarms: []
  )
  let full = try ReminderSnapshot(state: state)
  let redacted = RedactedReminderSnapshot(full)
  let encoded = try NativeProtocolSupport.encoder(pretty: false).encode(redacted)
  let json = String(decoding: encoded, as: UTF8.self)

  #expect(redacted.revision == full.revision)
  #expect(redacted.sortCursor == full.sortCursor)
  #expect(redacted.state.localId == "local")
  #expect(redacted.state.notesState.present)
  #expect(redacted.state.notesState.length == 17)
  #expect(redacted.state.notesState.sha256 != nil)
  #expect(!json.contains("private note text"))
}

@Test func noteBoundsAreLosslessOrFailTheWholeResponse() throws {
  let atLimit = String(repeating: "a", count: appleRemindersMaxNoteBytes)
  try NativeProtocolSupport.validateNoteBounds([atLimit])

  let overLimit = String(repeating: "a", count: appleRemindersMaxNoteBytes + 1)
  #expect(throws: NativeProtocolError.contentBoundExceeded) {
    try NativeProtocolSupport.validateNoteBounds([overLimit])
  }
}

@Test func requestDecodingRejectsUnknownTopLevelAndNestedFields() throws {
  let decoder = JSONDecoder()
  let createTopLevel = Data(#"{"listId":"list","title":"Fixture","unexpected":true}"#.utf8)
  let createDue = Data(
    #"{"listId":"list","title":"Fixture","due":{"kind":"timed","value":"2026-09-18T09:00:00","timeZone":"America/Los_Angeles","unexpected":true}}"#.utf8
  )
  let updateSet = Data(
    #"{"localId":"local","expectedRevision":"revision","set":{"title":"Changed","unexpected":true}}"#.utf8
  )
  let createAlarm = Data(
    #"{"listId":"list","title":"Fixture","alarms":[{"relativeOffsetSeconds":-600,"unexpected":true}]}"#.utf8
  )

  #expect(throws: DecodingError.self) {
    try decoder.decode(CreateRequest.self, from: createTopLevel)
  }
  #expect(throws: DecodingError.self) {
    try decoder.decode(CreateRequest.self, from: createDue)
  }
  #expect(throws: DecodingError.self) {
    try decoder.decode(UpdateRequest.self, from: updateSet)
  }
  #expect(throws: DecodingError.self) {
    try decoder.decode(CreateRequest.self, from: createAlarm)
  }
}
