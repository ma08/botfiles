"""Tests for the guarded Apple Reminders bridge and portable policy wrapper."""

from __future__ import annotations

import copy
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER = REPO_ROOT / "bin" / "apple-reminders-safe"
PRIVATE_TEMP_ROOT = Path("/var/tmp")
LOADER = importlib.machinery.SourceFileLoader("apple_reminders_safe", str(HELPER))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
assert SPEC
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)


def reminder_list(
    *, list_id: str = "list-1", writable: bool = True
) -> dict[str, object]:
    return {
        "id": list_id,
        "title": "Tasks",
        "allowsContentModifications": writable,
        "source": {
            "id": "source-1",
            "title": "iCloud",
            "type": "caldav",
            "typeCode": 2,
        },
    }


def reminder_state(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "localId": "local-1",
        "externalId": "external-1",
        "list": reminder_list(),
        "title": "Existing reminder",
        "notes": "Keep private note",
        "url": "https://example.com/task",
        "completed": False,
        "completionDate": None,
        "creationDate": "2026-08-14T10:00:00.000Z",
        "lastModifiedDate": "2026-08-14T10:00:00.000Z",
        "priority": 5,
        "priorityLabel": "medium",
        "due": {
            "kind": "timed",
            "localValue": "2026-09-01T09:00:00",
            "timeZone": "America/Los_Angeles",
            "floating": False,
            "components": {
                "year": 2026,
                "month": 9,
                "day": 1,
                "hour": 9,
                "minute": 0,
                "second": 0,
            },
        },
        "recurrence": [],
        "alarms": [],
    }
    value.update(overrides)
    return value


def snapshot(*, revision: str = "revision-1", **overrides: object) -> dict[str, object]:
    return {
        "state": reminder_state(**overrides),
        "revision": revision,
        "sortCursor": "cursor",
    }


def native_response(
    operation: str,
    *,
    data: dict[str, object] | None = None,
    truncated: bool = False,
) -> dict[str, object]:
    return {
        "protocolVersion": 1,
        "nativeVersion": "1.0.0",
        "operation": operation,
        "status": "ok",
        "health": {
            "macReachable": True,
            "tccStatus": "full-access",
            "authorized": True,
            "fetchComplete": True,
            "truncated": truncated,
            "cloudFreshness": "unverified",
            "recordsExamined": 1,
            "recordsReturned": 1,
        },
        "data": data or {},
    }


class AppleRemindersSafeTests(unittest.TestCase):
    def test_private_json_files_require_mode_600_and_non_git_storage(self) -> None:
        with tempfile.TemporaryDirectory(dir=PRIVATE_TEMP_ROOT) as directory:
            root = Path(directory)
            request = root / "request.json"
            request.write_text('{"title":"Fixture"}', encoding="utf-8")
            request.chmod(0o644)
            with self.assertRaises(MODULE.RemindersSafeError) as broad:
                MODULE._load_json(request)
            self.assertEqual(broad.exception.code, "UNSAFE_PRIVATE_PATH")

            request.chmod(0o600)
            self.assertEqual(MODULE._load_json(request), {"title": "Fixture"})

            repository = root / "repo"
            (repository / ".git").mkdir(parents=True)
            private_file = repository / "preview.json"
            with self.assertRaises(MODULE.RemindersSafeError) as git_path:
                MODULE._write_output({}, private_file)
            self.assertEqual(git_path.exception.code, "UNSAFE_PRIVATE_PATH")

    def test_create_requires_explicit_list_and_exact_timed_timezone(self) -> None:
        with self.assertRaisesRegex(MODULE.RemindersSafeError, "explicit listId"):
            MODULE.validate_create({"title": "Fixture"})
        with self.assertRaisesRegex(MODULE.RemindersSafeError, "explicit IANA"):
            MODULE.validate_create(
                {
                    "listId": "list-1",
                    "title": "Fixture",
                    "due": {"kind": "timed", "value": "2026-09-01T09:00:00"},
                }
            )

    def test_create_preview_redacts_note_content_but_binds_exact_request(self) -> None:
        request = {
            "listId": "list-1",
            "title": "ZON-325 fixture",
            "notes": "private fixture note",
            "due": {
                "kind": "timed",
                "value": "2026-09-01T09:00:00",
                "timeZone": "America/Los_Angeles",
            },
        }
        with mock.patch.object(MODULE, "_exact_list", return_value=reminder_list()):
            preview = MODULE.create_preview(request)

        self.assertEqual(preview["request"]["notes"], "private fixture note")
        self.assertNotIn("notes", preview["after"])
        self.assertTrue(preview["after"]["notesState"]["present"])
        self.assertEqual(preview["after"]["due"]["timeZone"], "America/Los_Angeles")
        unsigned = copy.deepcopy(preview)
        approval_hash = unsigned.pop("approvalHash")
        self.assertEqual(approval_hash, MODULE._sha256(unsigned))

        display = MODULE._preview_for_display(
            preview, Path("/private/previews/create.json")
        )
        self.assertNotIn("notes", display["request"])
        self.assertTrue(display["request"]["notesState"]["present"])
        self.assertNotIn("private fixture note", json.dumps(display))

    def test_update_rejects_null_and_set_clear_overlap(self) -> None:
        with self.assertRaisesRegex(MODULE.RemindersSafeError, "use clear"):
            MODULE.validate_update({"set": {"notes": None}})
        with self.assertRaisesRegex(MODULE.RemindersSafeError, "set and cleared"):
            MODULE.validate_update({"set": {"notes": "new"}, "clear": ["notes"]})

    def test_update_preview_preserves_every_unspecified_field(self) -> None:
        before = snapshot()
        preview = MODULE.change_preview("update", before, {"set": {"title": "Changed"}})

        self.assertEqual(preview["after"]["title"], "Changed")
        self.assertEqual(
            preview["after"]["notesState"], preview["before"]["notesState"]
        )
        self.assertEqual(preview["after"]["due"], preview["before"]["due"])
        self.assertEqual(
            preview["after"]["recurrence"], preview["before"]["recurrence"]
        )
        self.assertEqual(preview["request"], {"set": {"title": "Changed"}, "clear": []})

    def test_delete_requires_separate_exact_confirmation(self) -> None:
        preview = MODULE.change_preview("delete", snapshot())
        with self.assertRaisesRegex(MODULE.RemindersSafeError, "fresh destructive"):
            MODULE.apply_preview(preview, preview["approvalHash"], None)

    def test_preview_tamper_and_expiry_fail_closed(self) -> None:
        preview = MODULE.change_preview("complete", snapshot())
        tampered = copy.deepcopy(preview)
        tampered["after"]["completed"] = False
        with self.assertRaisesRegex(MODULE.RemindersSafeError, "changed after sealing"):
            MODULE._validate_preview(tampered, preview["approvalHash"])

        expired = copy.deepcopy(preview)
        expired.pop("approvalHash")
        expired["expiresAt"] = "2020-01-01T00:00:00Z"
        expired = MODULE._seal_preview(expired)
        with self.assertRaisesRegex(MODULE.RemindersSafeError, "expired"):
            MODULE._validate_preview(expired, expired["approvalHash"])

    def test_preview_is_bound_to_the_exact_execution_boundary(self) -> None:
        with mock.patch.object(MODULE.platform, "system", return_value="Linux"):
            preview = MODULE.change_preview("complete", snapshot())

        with (
            mock.patch.object(MODULE.platform, "system", return_value="Darwin"),
            self.assertRaises(MODULE.RemindersSafeError) as caught,
        ):
            MODULE._validate_preview(preview, preview["approvalHash"])
        self.assertEqual(caught.exception.code, "EXECUTION_BOUNDARY_MISMATCH")

    def test_remote_command_quotes_untrusted_arguments_for_remote_shell(self) -> None:
        with (
            mock.patch.object(MODULE.platform, "system", return_value="Linux"),
            mock.patch.dict(os.environ, {}, clear=True),
        ):
            command, transport = MODULE._transport_command(
                ["search", "--query", "value; touch /tmp/unsafe"]
            )

        self.assertEqual(transport, "ssh:sourya-mac")
        self.assertEqual(command[-2], "sourya-mac")
        self.assertEqual(command[0], "/usr/bin/ssh")
        self.assertTrue(
            command[-1].startswith(
                'exec "$HOME/.local/bin/apple-reminders-native-run" '
            )
        )
        self.assertIn("'value; touch /tmp/unsafe'", command[-1])
        self.assertEqual(command.count("touch"), 0)

    def test_environment_cannot_redirect_the_fixed_mac_boundary(self) -> None:
        with (
            mock.patch.object(MODULE.platform, "system", return_value="Linux"),
            mock.patch.dict(
                os.environ,
                {
                    "APPLE_REMINDERS_NATIVE_COMMAND": "/tmp/untrusted",
                    "APPLE_REMINDERS_REMOTE_HOST": "untrusted-host",
                    "APPLE_REMINDERS_REMOTE_RUNNER": "/tmp/untrusted",
                    "APPLE_REMINDERS_SSH_COMMAND": "/tmp/untrusted",
                },
                clear=False,
            ),
        ):
            command, transport = MODULE._transport_command(["status"])

        self.assertEqual(transport, "ssh:sourya-mac")
        self.assertEqual(command[0], "/usr/bin/ssh")
        self.assertEqual(command[-2], "sourya-mac")
        self.assertIn("$HOME/.local/bin/apple-reminders-native-run", command[-1])
        self.assertNotIn("untrusted", " ".join(command))

    def test_native_call_distinguishes_mac_offline_and_ssh_failure(self) -> None:
        offline = subprocess.CompletedProcess(
            args=[],
            returncode=255,
            stdout="",
            stderr="ssh: connect: Operation timed out",
        )
        denied = subprocess.CompletedProcess(
            args=[], returncode=255, stdout="", stderr="Permission denied (publickey)."
        )
        with (
            mock.patch.object(MODULE.platform, "system", return_value="Linux"),
            mock.patch.object(MODULE.subprocess, "run", return_value=offline),
            self.assertRaises(MODULE.RemindersSafeError) as offline_error,
        ):
            MODULE.native_call(["status"])
        self.assertEqual(offline_error.exception.code, "MAC_OFFLINE")

        with (
            mock.patch.object(MODULE.platform, "system", return_value="Linux"),
            mock.patch.object(MODULE.subprocess, "run", return_value=denied),
            self.assertRaises(MODULE.RemindersSafeError) as ssh_error,
        ):
            MODULE.native_call(["status"])
        self.assertEqual(ssh_error.exception.code, "SSH_FAILURE")

    def test_native_tcc_error_remains_distinct_from_empty_results(self) -> None:
        error = {
            "protocolVersion": 1,
            "nativeVersion": "1.0.0",
            "status": "error",
            "error": {
                "code": "TCC_DENIED",
                "message": "Full Apple Reminders access is not available",
                "tccStatus": "denied",
            },
        }
        result = subprocess.CompletedProcess(
            args=[], returncode=77, stdout="", stderr=json.dumps(error)
        )
        with (
            mock.patch.object(
                MODULE, "_transport_command", return_value=(["/fake/native"], "test")
            ),
            mock.patch.object(MODULE.subprocess, "run", return_value=result),
            self.assertRaises(MODULE.NativeCallError) as caught,
        ):
            MODULE.native_call(["lists"])
        self.assertEqual(caught.exception.code, "TCC_DENIED")
        self.assertEqual(caught.exception.tcc_status, "denied")

    def test_hard_cap_truncation_is_an_error_not_an_empty_inventory(self) -> None:
        response = native_response(
            "lists", data={"lists": [], "truncated": True}, truncated=True
        )
        with (
            mock.patch.object(MODULE, "native_call", return_value=response),
            self.assertRaisesRegex(MODULE.RemindersSafeError, "incomplete") as caught,
        ):
            MODULE._native_lists()
        self.assertEqual(caught.exception.code, "HARD_CAP_TRUNCATED")

    def test_search_redacts_notes_while_exact_get_can_retain_them(self) -> None:
        response = native_response(
            "search",
            data={"reminders": [snapshot()], "nextCursor": None, "truncated": False},
        )
        with mock.patch.object(MODULE, "_record_identity"):
            redacted = MODULE._redact_search_notes(response)
        state = redacted["data"]["reminders"][0]["state"]
        self.assertNotIn("notes", state)
        self.assertTrue(state["notesState"]["present"])
        self.assertEqual(
            response["data"]["reminders"][0]["state"]["notes"], "Keep private note"
        )

    def test_search_preserves_native_note_metadata_without_note_text(self) -> None:
        response = native_response(
            "search",
            data={"reminders": [snapshot()], "truncated": False},
        )
        state = response["data"]["reminders"][0]["state"]
        note_state = MODULE._notes_state(state.pop("notes"))
        state["notesState"] = note_state
        with mock.patch.object(MODULE, "_record_identity"):
            redacted = MODULE._redact_search_notes(response)
        self.assertEqual(
            redacted["data"]["reminders"][0]["state"]["notesState"], note_state
        )

    def test_local_id_rotation_is_reconciled_only_with_same_external_state(
        self,
    ) -> None:
        before = snapshot()
        preview = MODULE.change_preview("complete", before)
        rotated = snapshot(revision="revision-2", localId="local-2")
        missing = MODULE.NativeCallError("missing", code="NOT_FOUND")
        with mock.patch.object(MODULE, "_get_snapshot", side_effect=[missing, rotated]):
            current = MODULE._reread_target(preview)
        self.assertEqual(current["state"]["localId"], "local-2")

        drifted = copy.deepcopy(rotated)
        drifted["state"]["title"] = "Changed elsewhere"
        with (
            mock.patch.object(MODULE, "_get_snapshot", side_effect=[missing, drifted]),
            self.assertRaises(MODULE.RemindersSafeError) as caught,
        ):
            MODULE._reread_target(preview)
        self.assertEqual(caught.exception.code, "DRIFT")

    def test_apply_update_sends_only_requested_fields_and_returns_content_free_audit(
        self,
    ) -> None:
        before = snapshot()
        preview = MODULE.change_preview("update", before, {"set": {"title": "Changed"}})
        after = snapshot(
            revision="revision-2",
            title="Changed",
            lastModifiedDate="2026-08-14T11:00:00.000Z",
        )
        calls: list[dict[str, object]] = []

        def fake_native(
            arguments: list[str],
            *,
            request: dict[str, object] | None = None,
            write: bool = False,
        ) -> dict[str, object]:
            calls.append({"arguments": arguments, "request": request, "write": write})
            return native_response("update", data={"reminder": after})

        with tempfile.TemporaryDirectory() as directory:
            audit_path = Path(directory) / "audit.json"
            with (
                mock.patch.object(MODULE, "_reread_target", return_value=before),
                mock.patch.object(MODULE, "native_call", side_effect=fake_native),
                mock.patch.object(MODULE, "_get_snapshot", return_value=after),
                mock.patch.object(MODULE, "_record_identity"),
                mock.patch.object(MODULE, "_write_audit", return_value=audit_path),
            ):
                result = MODULE.apply_preview(preview, preview["approvalHash"], None)

        request = calls[0]["request"]
        self.assertEqual(request["set"], {"title": "Changed"})
        self.assertEqual(request["clear"], [])
        self.assertNotIn("notes", request["set"])
        audit_text = json.dumps(result["audit"], sort_keys=True)
        self.assertNotIn("Existing reminder", audit_text)
        self.assertNotIn("Changed", audit_text)
        self.assertNotIn("Keep private note", audit_text)
        self.assertEqual(result["audit"]["appliedDiff"][0]["field"], "lastModifiedDate")

    def test_create_apply_is_single_shot_and_ledger_contains_no_content(self) -> None:
        request = {
            "listId": "list-1",
            "title": "ZON-325 fixture",
            "notes": "private create note",
        }
        created = snapshot(
            revision="created-revision",
            title=request["title"],
            notes=request["notes"],
            url=None,
            priority=0,
            priorityLabel="none",
            due=None,
        )
        response = native_response("create", data={"reminder": created})

        with tempfile.TemporaryDirectory(dir=PRIVATE_TEMP_ROOT) as directory:
            audit_path = Path(directory) / "audit.json"
            with (
                mock.patch.dict(
                    os.environ,
                    {"APPLE_REMINDERS_SAFE_STATE_DIR": directory},
                    clear=False,
                ),
                mock.patch.object(MODULE, "_exact_list", return_value=reminder_list()),
                mock.patch.object(
                    MODULE, "native_call", return_value=response
                ) as native,
                mock.patch.object(MODULE, "_get_snapshot", return_value=created),
                mock.patch.object(MODULE, "_write_audit", return_value=audit_path),
            ):
                preview = MODULE.create_preview(request)
                first = MODULE.apply_preview(preview, preview["approvalHash"], None)
                second = MODULE.apply_preview(preview, preview["approvalHash"], None)
                ledger_text = MODULE._apply_ledger_path().read_text(encoding="utf-8")

        self.assertEqual(first["status"], "applied")
        self.assertEqual(second["status"], "already_applied")
        native.assert_called_once_with(["create"], request=request, write=True)
        self.assertNotIn(request["title"], ledger_text)
        self.assertNotIn(request["notes"], ledger_text)

    def test_in_progress_create_ledger_refuses_a_second_write(self) -> None:
        request = {"listId": "list-1", "title": "ZON-325 fixture"}
        with (
            tempfile.TemporaryDirectory(dir=PRIVATE_TEMP_ROOT) as directory,
            mock.patch.dict(
                os.environ,
                {"APPLE_REMINDERS_SAFE_STATE_DIR": directory},
                clear=False,
            ),
            mock.patch.object(MODULE, "_exact_list", return_value=reminder_list()),
        ):
            preview = MODULE.create_preview(request)
            MODULE._atomic_json(
                MODULE._apply_ledger_path(),
                {
                    "schemaVersion": 1,
                    "entries": {
                        preview["approvalHash"]: {
                            "status": "in_progress",
                            "operation": "create",
                        }
                    },
                },
            )
            with (
                mock.patch.object(MODULE, "native_call") as native,
                self.assertRaises(MODULE.RemindersSafeError) as caught,
            ):
                MODULE.apply_preview(preview, preview["approvalHash"], None)

        self.assertEqual(caught.exception.code, "WRITE_OUTCOME_UNKNOWN")
        native.assert_not_called()

    def test_post_write_revision_mismatch_fails_verification(self) -> None:
        before = snapshot()
        preview = MODULE.change_preview("update", before, {"set": {"title": "Changed"}})
        written = snapshot(revision="revision-2", title="Changed")
        changed_again = snapshot(revision="revision-3", title="Changed")
        with (
            mock.patch.object(MODULE, "_reread_target", return_value=before),
            mock.patch.object(
                MODULE,
                "native_call",
                return_value=native_response("update", data={"reminder": written}),
            ),
            mock.patch.object(MODULE, "_get_snapshot", return_value=changed_again),
            mock.patch.object(MODULE, "_write_audit") as audit,
            self.assertRaises(MODULE.RemindersSafeError) as caught,
        ):
            MODULE.apply_preview(preview, preview["approvalHash"], None)

        self.assertEqual(caught.exception.code, "WRITE_VERIFICATION_FAILED")
        audit.assert_not_called()

    def test_authorization_preview_never_calls_authorize(self) -> None:
        status = native_response(
            "status",
            data={"tccStatus": "not-determined", "authorized": False},
        )
        status["health"]["tccStatus"] = "not-determined"
        status["health"]["authorized"] = False
        with mock.patch.object(MODULE, "native_call", return_value=status) as native:
            preview = MODULE.authorization_preview()
        native.assert_called_once_with(["status"])
        self.assertTrue(preview["willPrompt"])
        self.assertEqual(preview["currentTccStatus"], "not-determined")


if __name__ == "__main__":
    unittest.main()
