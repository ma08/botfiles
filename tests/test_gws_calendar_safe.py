"""Tests for the guarded multi-account Google Calendar helper."""

from __future__ import annotations

import copy
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER = REPO_ROOT / "bin" / "gws-calendar-safe"
LOADER = importlib.machinery.SourceFileLoader("gws_calendar_safe", str(HELPER))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
assert SPEC
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)


class FakeResponse:
    def __init__(self, payload: dict[str, object] | None = None) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        del args

    def read(self) -> bytes:
        if self.payload is None:
            return b""
        return json.dumps(self.payload).encode("utf-8")


def calendar(*, primary: bool = False, access_role: str = "owner") -> dict[str, object]:
    return {
        "id": "primary@example.com" if primary else "team@example.com",
        "summary": "Primary" if primary else "Team",
        "primary": primary,
        "accessRole": access_role,
        "timeZone": "America/Los_Angeles",
        "defaultReminders": [{"method": "popup", "minutes": 10}],
        "etag": '"calendar-etag"',
    }


def event(
    *,
    organizer: bool = True,
    guests: bool = False,
    recurring: bool = False,
    instance: bool = False,
) -> dict[str, object]:
    attendees: list[dict[str, object]] = [
        {"email": "sourya4@trymyzone.com", "self": True}
    ]
    if guests:
        attendees.append({"email": "guest@example.com", "responseStatus": "accepted"})
    value: dict[str, object] = {
        "id": "event-1",
        "summary": "Existing event",
        "description": "Keep this",
        "start": {
            "dateTime": "2026-09-01T10:00:00-07:00",
            "timeZone": "America/Los_Angeles",
        },
        "end": {
            "dateTime": "2026-09-01T11:00:00-07:00",
            "timeZone": "America/Los_Angeles",
        },
        "location": "Old room",
        "visibility": "private",
        "reminders": {"useDefault": True},
        "conferenceData": {
            "conferenceId": "meet-old",
            "conferenceSolution": {
                "key": {"type": "hangoutsMeet"},
                "name": "Google Meet",
            },
        },
        "hangoutLink": "https://meet.google.com/old-link",
        "attendees": attendees,
        "organizer": {
            "email": "sourya4@trymyzone.com" if organizer else "other@example.com",
            "self": organizer,
        },
        "status": "confirmed",
        "etag": '"event-etag"',
        "updated": "2026-08-14T00:00:00Z",
        "htmlLink": "https://calendar.google.com/event?eid=event-1",
    }
    if recurring:
        value["recurrence"] = ["RRULE:FREQ=WEEKLY;BYDAY=TU"]
    if instance:
        value["id"] = "event-1-instance"
        value["recurringEventId"] = "event-1"
        value["originalStartTime"] = copy.deepcopy(value["start"])
        value.pop("recurrence", None)
    return value


def create_request(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "summary": "ZON-325 self-only fixture",
        "start": {
            "dateTime": "2026-09-01T10:00:00-07:00",
            "timeZone": "America/Los_Angeles",
        },
        "end": {
            "dateTime": "2026-09-01T10:30:00-07:00",
            "timeZone": "America/Los_Angeles",
        },
        "idempotencyKey": "fixture-work-v1",
    }
    value.update(overrides)
    return value


class CalendarSafeTests(unittest.TestCase):
    def test_account_policy_excludes_jiffy(self) -> None:
        self.assertEqual(
            MODULE.ACCOUNT_ADDRESSES,
            {
                "work": "sourya4@trymyzone.com",
                "personal": "sourya4@gmail.com",
                "columbia": "sk5057@columbia.edu",
            },
        )

    def test_secondary_create_is_private_self_only_and_notification_free(self) -> None:
        body, query = MODULE._build_create_event(
            "work", calendar(primary=False), create_request()
        )

        self.assertEqual(body["attendees"], [{"email": "sourya4@trymyzone.com"}])
        self.assertEqual(body["visibility"], "private")
        self.assertEqual(body["reminders"], {"useDefault": True})
        self.assertEqual(query["sendUpdates"], "none")
        self.assertNotIn("conferenceData", body)
        self.assertRegex(body["id"], r"^[0-9a-v]{5,1024}$")

    def test_create_event_id_is_deterministic_per_account_calendar_and_key(self) -> None:
        first, _ = MODULE._build_create_event(
            "work", calendar(), create_request(idempotencyKey="stable-key")
        )
        retry, _ = MODULE._build_create_event(
            "work", calendar(), create_request(idempotencyKey="stable-key")
        )
        changed, _ = MODULE._build_create_event(
            "work", calendar(), create_request(idempotencyKey="different-key")
        )
        self.assertEqual(first["id"], retry["id"])
        self.assertNotEqual(first["id"], changed["id"])

    def test_primary_create_uses_default_visibility(self) -> None:
        body, _ = MODULE._build_create_event(
            "personal", calendar(primary=True), create_request()
        )
        self.assertEqual(body["visibility"], "default")

    def test_create_rejects_any_caller_supplied_attendee_list(self) -> None:
        with self.assertRaisesRegex(MODULE.CalendarSafeError, "policy-owned"):
            MODULE._build_create_event(
                "work",
                calendar(),
                create_request(attendees=[{"email": "guest@example.com"}]),
            )

    def test_create_can_request_one_unique_google_meet(self) -> None:
        body, query = MODULE._build_create_event(
            "work",
            calendar(),
            create_request(conference="googleMeet"),
        )
        request = body["conferenceData"]["createRequest"]
        self.assertEqual(request["conferenceSolutionKey"], {"type": "hangoutsMeet"})
        self.assertTrue(request["requestId"].startswith("meet"))
        self.assertEqual(query["conferenceDataVersion"], 1)

    def test_calendar_default_reminders_are_resolved_in_preview(self) -> None:
        with mock.patch.object(MODULE, "_select_calendar", return_value=calendar()):
            preview = MODULE.create_preview(
                "work", "team@example.com", create_request(), access_token="token"
            )
        self.assertEqual(
            preview["resolvedDefaultReminders"],
            [{"method": "popup", "minutes": 10}],
        )
        self.assertEqual(preview["notificationBehavior"], "none")
        self.assertEqual(preview["after"]["attendeeState"], "self-only")

    def test_timed_event_requires_explicit_matching_timezone(self) -> None:
        request = create_request()
        request["end"] = {
            "dateTime": "2026-09-01T10:30:00-04:00",
            "timeZone": "America/New_York",
        }
        with self.assertRaisesRegex(MODULE.CalendarSafeError, "same explicit"):
            MODULE._build_create_event("work", calendar(), request)

    def test_all_day_end_is_exclusive(self) -> None:
        request = create_request(
            start={"date": "2026-09-01"},
            end={"date": "2026-09-01"},
        )
        with self.assertRaisesRegex(MODULE.CalendarSafeError, "exclusive"):
            MODULE._build_create_event("work", calendar(), request)

    def test_update_rejects_attendee_mutation(self) -> None:
        with self.assertRaisesRegex(MODULE.CalendarSafeError, "immutable"):
            MODULE._normalize_patch(
                {"attendees": [{"email": "guest@example.com"}]}, "request-id"
            )

    def test_update_omits_unspecified_arrays_and_conference(self) -> None:
        before = event(guests=True)
        patch, version = MODULE._normalize_patch({"location": "New room"}, "request")
        after = MODULE._merge_event(before, patch)
        self.assertIsNone(version)
        self.assertNotIn("attendees", patch)
        self.assertNotIn("conferenceData", patch)
        self.assertEqual(after["attendees"], before["attendees"])
        self.assertEqual(after["conferenceData"], before["conferenceData"])

    def test_guest_event_requires_explicit_notification_choice(self) -> None:
        with self.assertRaisesRegex(MODULE.CalendarSafeError, "explicit notification"):
            MODULE._notification_mode(event(guests=True), "work", None)
        mode, risk = MODULE._notification_mode(event(guests=True), "work", "none")
        self.assertEqual(mode, "none")
        self.assertIn("synchronization problems", risk)
        mode, risk = MODULE._notification_mode(event(guests=True), "work", "all")
        self.assertEqual(mode, "all")
        self.assertIn("may be notified", risk)

    def test_omitted_attendees_make_every_write_preview_fail_closed(self) -> None:
        source = event(guests=True)
        source["attendeesOmitted"] = True
        with (
            mock.patch.object(MODULE, "_select_calendar", return_value=calendar()),
            mock.patch.object(MODULE, "_get_event", return_value=source),
            self.assertRaisesRegex(MODULE.CalendarSafeError, "omitted part"),
        ):
            MODULE.update_preview(
                "work",
                "team@example.com",
                "event-1",
                {"location": "New room"},
                scope="occurrence",
                send_updates="none",
                access_token="token",
            )

    def test_non_organizer_update_is_preview_only(self) -> None:
        source = event(organizer=False)
        with (
            mock.patch.object(MODULE, "_select_calendar", return_value=calendar()),
            mock.patch.object(MODULE, "_get_event", return_value=source),
        ):
            preview = MODULE.update_preview(
                "work",
                "team@example.com",
                "event-1",
                {"location": "New room"},
                scope="occurrence",
                send_updates="none",
                access_token="token",
            )
        self.assertFalse(preview["applyAllowed"])
        with self.assertRaisesRegex(MODULE.CalendarSafeError, "read-only"):
            MODULE._validate_preview(preview, preview["approvalHash"])

    def test_organizer_update_preserves_attendees_and_conference(self) -> None:
        source = event(guests=True)
        with (
            mock.patch.object(MODULE, "_select_calendar", return_value=calendar()),
            mock.patch.object(MODULE, "_get_event", return_value=source),
        ):
            preview = MODULE.update_preview(
                "work",
                "team@example.com",
                "event-1",
                {"location": "New room"},
                scope="occurrence",
                send_updates="none",
                access_token="token",
            )
        self.assertTrue(preview["applyAllowed"])
        self.assertEqual(preview["before"]["attendees"], preview["after"]["attendees"])
        self.assertEqual(preview["before"]["conference"], preview["after"]["conference"])
        self.assertNotIn("attendees", preview["request"]["body"])
        self.assertNotIn("conferenceData", preview["request"]["body"])

    def test_split_recurrence_adds_until_without_changing_new_rule(self) -> None:
        old, new = MODULE._split_recurrence(
            ["RRULE:FREQ=WEEKLY;BYDAY=TU"],
            {
                "dateTime": "2026-09-01T10:00:00-07:00",
                "timeZone": "America/Los_Angeles",
            },
        )
        self.assertEqual(new, ["RRULE:FREQ=WEEKLY;BYDAY=TU"])
        self.assertIn("UNTIL=20260901T165959Z", old[0])

    def test_split_recurrence_rejects_count_series(self) -> None:
        with self.assertRaisesRegex(MODULE.CalendarSafeError, "COUNT-based"):
            MODULE._split_recurrence(
                ["RRULE:FREQ=WEEKLY;COUNT=10"],
                {
                    "dateTime": "2026-09-01T10:00:00-07:00",
                    "timeZone": "America/Los_Angeles",
                },
            )

    def test_following_split_requires_explicit_conference_choice(self) -> None:
        parent = event(guests=True, recurring=True)
        instance = event(guests=True, instance=True)
        with self.assertRaisesRegex(MODULE.CalendarSafeError, "cannot safely reuse"):
            MODULE._following_update_preview(
                "work",
                calendar(),
                parent,
                instance,
                {"location": "New room"},
                "none",
                "risk",
            )

    def test_following_split_copies_exact_attendees_and_generates_new_meet(self) -> None:
        parent = event(guests=True, recurring=True)
        parent["guestsCanModify"] = False
        parent["extendedProperties"] = {"private": {"owner": "zon-325"}}
        instance = event(guests=True, instance=True)
        preview = MODULE._following_update_preview(
            "work",
            calendar(),
            parent,
            instance,
            {"location": "New room", "conference": "googleMeet"},
            "none",
            "risk",
        )
        new_body = preview["request"]["steps"][1]["body"]
        self.assertEqual(new_body["attendees"], parent["attendees"])
        self.assertIn("createRequest", new_body["conferenceData"])
        self.assertNotEqual(
            new_body["conferenceData"], parent["conferenceData"]
        )
        self.assertEqual(new_body["guestsCanModify"], False)
        self.assertEqual(
            new_body["extendedProperties"], parent["extendedProperties"]
        )
        self.assertEqual(
            preview["after"]["newSeries"]["extendedProperties"],
            parent["extendedProperties"],
        )
        self.assertEqual(preview["recurrenceScope"], "following")

    def test_rehashed_hidden_split_field_tamper_is_rejected(self) -> None:
        parent = event(guests=True, recurring=True)
        parent["guestsCanModify"] = False
        instance = event(guests=True, instance=True)
        preview = MODULE._following_update_preview(
            "work",
            calendar(),
            parent,
            instance,
            {"location": "New room", "conference": "remove"},
            "none",
            "risk",
        )
        preview["request"]["steps"][1]["body"]["guestsCanModify"] = True
        preview = MODULE._finalize_preview(preview)
        with (
            mock.patch.object(MODULE, "_access_token") as access_token,
            mock.patch.object(MODULE, "_execute_request") as execute,
            self.assertRaisesRegex(MODULE.CalendarSafeError, "new-series state"),
        ):
            MODULE.apply_preview(preview, preview["approvalHash"])
        access_token.assert_not_called()
        execute.assert_not_called()

    def test_request_path_parser_accepts_only_calendar_event_routes(self) -> None:
        self.assertEqual(
            MODULE._parse_request_path("/calendars/team%40example.com/events"),
            ("team@example.com", None),
        )
        self.assertEqual(
            MODULE._parse_request_path(
                "/calendars/team%40example.com/events/event-1"
            ),
            ("team@example.com", "event-1"),
        )
        with self.assertRaisesRegex(MODULE.CalendarSafeError, "outside Calendar"):
            MODULE._parse_request_path(
                "/calendars/team%40example.com/acl/rule-1"
            )

    def test_rehashed_acl_tamper_is_rejected_before_any_write(self) -> None:
        with mock.patch.object(MODULE, "_select_calendar", return_value=calendar()):
            preview = MODULE.create_preview(
                "work", "team@example.com", create_request(), access_token="token"
            )
        preview["request"]["path"] = "/calendars/team%40example.com/acl/rule-1"
        preview.pop("approvalHash")
        preview = MODULE._finalize_preview(preview)
        with (
            mock.patch.object(MODULE, "_access_token") as access_token,
            mock.patch.object(MODULE, "_execute_request") as execute,
            self.assertRaisesRegex(MODULE.CalendarSafeError, "outside Calendar"),
        ):
            MODULE.apply_preview(preview, preview["approvalHash"])
        access_token.assert_not_called()
        execute.assert_not_called()

    def test_rehashed_attendee_tamper_is_rejected_before_any_write(self) -> None:
        source = event()
        with (
            mock.patch.object(MODULE, "_select_calendar", return_value=calendar()),
            mock.patch.object(MODULE, "_get_event", return_value=source),
        ):
            preview = MODULE.update_preview(
                "work",
                "team@example.com",
                "event-1",
                {"location": "New room"},
                scope="occurrence",
                send_updates=None,
                access_token="token",
            )
        preview["request"]["body"]["attendees"] = [
            {"email": "guest@example.com"}
        ]
        preview.pop("approvalHash")
        preview = MODULE._finalize_preview(preview)
        with (
            mock.patch.object(MODULE, "_access_token") as access_token,
            mock.patch.object(MODULE, "_execute_request") as execute,
            self.assertRaisesRegex(MODULE.CalendarSafeError, "attendees"),
        ):
            MODULE.apply_preview(preview, preview["approvalHash"])
        access_token.assert_not_called()
        execute.assert_not_called()

    def test_delete_preview_is_destructive_and_scope_exact(self) -> None:
        source = event()
        with (
            mock.patch.object(MODULE, "_select_calendar", return_value=calendar()),
            mock.patch.object(MODULE, "_get_event", return_value=source),
        ):
            preview = MODULE.delete_preview(
                "work",
                "team@example.com",
                "event-1",
                scope="occurrence",
                send_updates=None,
                access_token="token",
            )
        self.assertTrue(preview["destructive"])
        self.assertEqual(preview["request"]["method"], "DELETE")
        self.assertEqual(preview["recurrenceScope"], "occurrence")
        with self.assertRaisesRegex(MODULE.CalendarSafeError, "destructive confirmation"):
            MODULE._validate_preview(preview, preview["approvalHash"])
        MODULE._validate_preview(
            preview,
            preview["approvalHash"],
            preview["destructiveConfirmation"],
        )

    def test_preview_hash_detects_any_change(self) -> None:
        preview = MODULE._finalize_preview(
            {
                "kind": MODULE.PREVIEW_KIND,
                "schemaVersion": MODULE.PREVIEW_SCHEMA_VERSION,
                "expiresAt": MODULE._rfc3339(MODULE._now() + timedelta(minutes=5)),
                "applyAllowed": True,
                "title": "Original",
            }
        )
        MODULE._validate_preview(preview, preview["approvalHash"])
        preview["title"] = "Changed"
        with self.assertRaisesRegex(MODULE.CalendarSafeError, "does not match"):
            MODULE._validate_preview(preview, preview["approvalHash"])

    def test_api_request_places_etag_in_if_match_header(self) -> None:
        captured: dict[str, object] = {}

        def opener(request: object, timeout: int) -> FakeResponse:
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse({"id": "event-1", "etag": '"new"'})

        response = MODULE._api_request(
            "access-token",
            "PATCH",
            "/calendars/team/events/event-1",
            query={"sendUpdates": "none"},
            body={"location": "New room"},
            if_match='"old"',
            opener=opener,
        )
        request = captured["request"]
        self.assertEqual(response["etag"], '"new"')
        self.assertEqual(request.get_header("If-match"), '"old"')
        self.assertEqual(request.get_method(), "PATCH")
        self.assertIn("sendUpdates=none", request.full_url)
        self.assertEqual(captured["timeout"], 60)

    def test_apply_stops_before_write_when_scope_is_missing(self) -> None:
        with (
            mock.patch.object(
                MODULE,
                "_scope_status",
                return_value={MODULE.CALENDAR_LIST_SCOPE, MODULE.CALENDAR_READ_SCOPE},
            ),
            self.assertRaisesRegex(MODULE.CalendarSafeError, "exact approved"),
        ):
            MODULE._require_write_scopes("work")

    def test_auth_plan_preserves_non_calendar_scopes_and_replaces_calendar_scopes(self) -> None:
        current = {
            MODULE.CALENDAR_READ_SCOPE,
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/drive.readonly",
        }
        with mock.patch.object(MODULE, "_scope_status", return_value=current):
            plan = MODULE._auth_plan("work")
        self.assertEqual(
            set(plan["requestedCalendarScopes"]),
            {MODULE.CALENDAR_EVENTS_SCOPE, MODULE.CALENDAR_LIST_SCOPE},
        )
        self.assertIn(
            "https://www.googleapis.com/auth/gmail.compose",
            plan["requestedScopes"],
        )
        self.assertNotIn(MODULE.CALENDAR_READ_SCOPE, plan["requestedScopes"])
        self.assertEqual(
            plan["authorizationCommand"][0:4],
            ["gws-calendar-safe", "authorize", "--account", "work"],
        )
        unsigned = copy.deepcopy(plan)
        unsigned.pop("approvalHash")
        unsigned.pop("authorizationCommand")
        self.assertEqual(plan["approvalHash"], MODULE._sha256(unsigned))

    def test_authorize_rejects_stale_scope_plan_before_login(self) -> None:
        with (
            mock.patch.object(
                MODULE, "_auth_plan", return_value={"approvalHash": "current"}
            ),
            mock.patch.object(MODULE.subprocess, "run") as run,
            self.assertRaisesRegex(MODULE.CalendarSafeError, "does not match"),
        ):
            MODULE.authorize_account("work", "stale")
        run.assert_not_called()

    def test_authorize_stages_verifies_and_atomically_replaces_alias(self) -> None:
        requested = [
            "email",
            MODULE.CALENDAR_EVENTS_SCOPE,
            MODULE.CALENDAR_LIST_SCOPE,
            "https://www.googleapis.com/auth/gmail.readonly",
        ]
        status = {
            "user": "sourya4@trymyzone.com",
            "scopes": requested,
        }
        old_credentials = {
            "client_id": "client",
            "client_secret": "secret",
            "refresh_token": "old-refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        new_credentials = {
            **old_credentials,
            "refresh_token": "new-refresh",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            accounts_dir = Path(temp_dir)
            alias_path = accounts_dir / "work.json"
            alias_path.write_text(json.dumps(old_credentials), encoding="utf-8")
            alias_path.chmod(0o600)
            subprocess_results = [
                subprocess.CompletedProcess(args=[], returncode=0),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout=json.dumps(status), stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout=json.dumps(new_credentials),
                    stderr="",
                ),
            ]
            with (
                mock.patch.dict(os.environ, {"GWS_ACCOUNTS_DIR": temp_dir}),
                mock.patch.object(
                    MODULE,
                    "_auth_plan",
                    return_value={
                        "approvalHash": "approved",
                        "requestedScopes": requested,
                    },
                ),
                mock.patch.object(
                    MODULE.subprocess, "run", side_effect=subprocess_results
                ),
                mock.patch.object(MODULE, "_auth_status", return_value=status),
                mock.patch.object(MODULE, "_require_write_scopes"),
            ):
                result = MODULE.authorize_account("work", "approved")

            installed = json.loads(alias_path.read_text(encoding="utf-8"))
            backup_path = Path(result["backupPath"])
            backup = json.loads(backup_path.read_text(encoding="utf-8"))
            self.assertEqual(installed["refresh_token"], "new-refresh")
            self.assertEqual(backup["refresh_token"], "old-refresh")
            self.assertEqual(alias_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(backup_path.stat().st_mode & 0o777, 0o600)
            self.assertTrue(result["tokensRemainMachineLocal"])
            self.assertNotIn("refresh_token", json.dumps(result))
            self.assertFalse(list(accounts_dir.glob(".reauth-work-*")))

    def test_authorize_restores_old_alias_when_post_install_verification_fails(self) -> None:
        requested = [MODULE.CALENDAR_EVENTS_SCOPE, MODULE.CALENDAR_LIST_SCOPE]
        status = {
            "user": "sourya4@trymyzone.com",
            "scopes": requested,
        }
        old_credentials = {
            "client_id": "client",
            "client_secret": "secret",
            "refresh_token": "old-refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        new_credentials = {**old_credentials, "refresh_token": "new-refresh"}
        with tempfile.TemporaryDirectory() as temp_dir:
            alias_path = Path(temp_dir) / "work.json"
            alias_path.write_text(json.dumps(old_credentials), encoding="utf-8")
            alias_path.chmod(0o600)
            subprocess_results = [
                subprocess.CompletedProcess(args=[], returncode=0),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout=json.dumps(status), stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout=json.dumps(new_credentials),
                    stderr="",
                ),
            ]
            with (
                mock.patch.dict(os.environ, {"GWS_ACCOUNTS_DIR": temp_dir}),
                mock.patch.object(
                    MODULE,
                    "_auth_plan",
                    return_value={
                        "approvalHash": "approved",
                        "requestedScopes": requested,
                    },
                ),
                mock.patch.object(
                    MODULE.subprocess, "run", side_effect=subprocess_results
                ),
                mock.patch.object(
                    MODULE,
                    "_auth_status",
                    side_effect=MODULE.CalendarSafeError("verification failed"),
                ),
                mock.patch.object(MODULE, "_require_write_scopes") as require_scopes,
                self.assertRaisesRegex(MODULE.CalendarSafeError, "verification failed"),
            ):
                MODULE.authorize_account("work", "approved")

            restored = json.loads(alias_path.read_text(encoding="utf-8"))
            self.assertEqual(restored["refresh_token"], "old-refresh")
            self.assertFalse(list(Path(temp_dir).glob(".reauth-work-*")))
            require_scopes.assert_not_called()

    def test_authorize_surfaces_backup_when_automatic_restore_fails(self) -> None:
        requested = [MODULE.CALENDAR_EVENTS_SCOPE, MODULE.CALENDAR_LIST_SCOPE]
        status = {
            "user": "sourya4@trymyzone.com",
            "scopes": requested,
        }
        old_credentials = {
            "client_id": "client",
            "client_secret": "secret",
            "refresh_token": "old-refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        new_credentials = {**old_credentials, "refresh_token": "new-refresh"}
        real_copy2 = MODULE.shutil.copy2
        copy_count = 0

        def fail_restore_copy(source: Path, destination: Path) -> Path:
            nonlocal copy_count
            copy_count += 1
            if copy_count == 2:
                raise OSError("simulated restore failure")
            return real_copy2(source, destination)

        with tempfile.TemporaryDirectory() as temp_dir:
            alias_path = Path(temp_dir) / "work.json"
            alias_path.write_text(json.dumps(old_credentials), encoding="utf-8")
            alias_path.chmod(0o600)
            subprocess_results = [
                subprocess.CompletedProcess(args=[], returncode=0),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout=json.dumps(status), stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout=json.dumps(new_credentials),
                    stderr="",
                ),
            ]
            with (
                mock.patch.dict(os.environ, {"GWS_ACCOUNTS_DIR": temp_dir}),
                mock.patch.object(
                    MODULE,
                    "_auth_plan",
                    return_value={
                        "approvalHash": "approved",
                        "requestedScopes": requested,
                    },
                ),
                mock.patch.object(
                    MODULE.subprocess, "run", side_effect=subprocess_results
                ),
                mock.patch.object(
                    MODULE,
                    "_auth_status",
                    side_effect=MODULE.CalendarSafeError("verification failed"),
                ),
                mock.patch.object(MODULE.shutil, "copy2", side_effect=fail_restore_copy),
                self.assertRaisesRegex(
                    MODULE.CalendarSafeError, "manual restore is required"
                ),
            ):
                MODULE.authorize_account("work", "approved")

            active = json.loads(alias_path.read_text(encoding="utf-8"))
            backups = list((Path(temp_dir) / "backups").glob("work.json.*"))
            self.assertEqual(active["refresh_token"], "new-refresh")
            self.assertEqual(len(backups), 1)
            self.assertEqual(
                json.loads(backups[0].read_text(encoding="utf-8"))["refresh_token"],
                "old-refresh",
            )
            self.assertFalse(list(Path(temp_dir).glob(".reauth-work-*")))

    def test_auth_status_rejects_alias_identity_mismatch(self) -> None:
        result = mock.Mock(
            returncode=0,
            stdout=json.dumps(
                {
                    "user": "wrong@example.com",
                    "scopes": [MODULE.CALENDAR_READ_SCOPE],
                }
            ),
        )
        with (
            mock.patch.object(MODULE.subprocess, "run", return_value=result),
            self.assertRaisesRegex(MODULE.CalendarSafeError, "not sourya4@trymyzone.com"),
        ):
            MODULE._auth_status("work")

    def test_calendar_inventory_rejects_primary_identity_mismatch(self) -> None:
        with self.assertRaisesRegex(MODULE.CalendarSafeError, "identity mismatch"):
            MODULE._assert_calendar_identity(
                [
                    {
                        "id": "wrong@example.com",
                        "primary": True,
                        "accessRole": "owner",
                    }
                ],
                "work",
            )

    def test_apply_stops_on_etag_drift(self) -> None:
        source = event()
        with (
            mock.patch.object(MODULE, "_select_calendar", return_value=calendar()),
            mock.patch.object(MODULE, "_get_event", return_value=source),
        ):
            preview = MODULE.update_preview(
                "work",
                "team@example.com",
                "event-1",
                {"location": "New room"},
                scope="occurrence",
                send_updates=None,
                access_token="token",
            )
        drifted = copy.deepcopy(source)
        drifted["etag"] = '"drifted"'
        with (
            mock.patch.object(MODULE, "_require_write_scopes"),
            mock.patch.object(MODULE, "_access_token", return_value="token"),
            mock.patch.object(MODULE, "_select_calendar", return_value=calendar()),
            mock.patch.object(MODULE, "_get_event", return_value=drifted),
            mock.patch.object(MODULE, "_execute_request") as execute,
            self.assertRaisesRegex(MODULE.CalendarDriftError, "event state changed"),
        ):
            MODULE.apply_preview(preview, preview["approvalHash"])
        execute.assert_not_called()

    def test_apply_rejects_rehashed_misleading_before_state(self) -> None:
        source = event()
        with (
            mock.patch.object(MODULE, "_select_calendar", return_value=calendar()),
            mock.patch.object(MODULE, "_get_event", return_value=source),
        ):
            preview = MODULE.update_preview(
                "work",
                "team@example.com",
                "event-1",
                {"location": "New room"},
                scope="occurrence",
                send_updates=None,
                access_token="token",
            )
        preview["before"]["title"] = "Misleading title"
        preview.pop("approvalHash")
        preview = MODULE._finalize_preview(preview)
        with (
            mock.patch.object(MODULE, "_require_write_scopes"),
            mock.patch.object(MODULE, "_access_token", return_value="token"),
            mock.patch.object(MODULE, "_select_calendar", return_value=calendar()),
            mock.patch.object(MODULE, "_get_event", return_value=source),
            mock.patch.object(MODULE, "_execute_request") as execute,
            self.assertRaisesRegex(MODULE.CalendarDriftError, "before-state"),
        ):
            MODULE.apply_preview(preview, preview["approvalHash"])
        execute.assert_not_called()

    def test_following_rollback_reuses_approved_notification_mode(self) -> None:
        parent = event(guests=True, recurring=True)
        instance = event(guests=True, instance=True)
        preview = MODULE._finalize_preview(
            MODULE._following_update_preview(
                "work",
                calendar(),
                parent,
                instance,
                {"location": "New room", "conference": "remove"},
                "all",
                "risk",
            )
        )
        requests: list[dict[str, object]] = []

        def execute(_token: str, request: dict[str, object]) -> dict[str, object]:
            requests.append(copy.deepcopy(request))
            if len(requests) == 1:
                response = copy.deepcopy(parent)
                response["etag"] = '"shortened"'
                return response
            if len(requests) == 2:
                raise MODULE.CalendarSafeError("insert failed")
            response = copy.deepcopy(parent)
            response["etag"] = '"restored"'
            return response

        with (
            mock.patch.object(MODULE, "_require_write_scopes"),
            mock.patch.object(MODULE, "_access_token", return_value="token"),
            mock.patch.object(MODULE, "_select_calendar", return_value=calendar()),
            mock.patch.object(
                MODULE, "_get_event", side_effect=[parent, instance]
            ),
            mock.patch.object(MODULE, "_get_event_optional", return_value=None),
            mock.patch.object(MODULE, "_execute_request", side_effect=execute),
            self.assertRaisesRegex(MODULE.CalendarSafeError, "original series was restored"),
        ):
            MODULE.apply_preview(preview, preview["approvalHash"])

        self.assertEqual(len(requests), 3)
        self.assertEqual(requests[2]["query"]["sendUpdates"], "all")

    def test_apply_returns_exact_and_redacted_audit_records(self) -> None:
        source = event()
        source["summary"] = "Private source title"
        with (
            mock.patch.object(MODULE, "_select_calendar", return_value=calendar()),
            mock.patch.object(MODULE, "_get_event", return_value=source),
        ):
            preview = MODULE.update_preview(
                "work",
                "team@example.com",
                "event-1",
                {"description": "Private replacement notes"},
                scope="occurrence",
                send_updates=None,
                access_token="token",
            )
        response = MODULE._merge_event(source, preview["request"]["body"])
        response["etag"] = '"updated"'
        with (
            mock.patch.object(MODULE, "_require_write_scopes"),
            mock.patch.object(MODULE, "_access_token", return_value="token"),
            mock.patch.object(MODULE, "_select_calendar", return_value=calendar()),
            mock.patch.object(MODULE, "_get_event", return_value=source),
            mock.patch.object(MODULE, "_execute_request", return_value=response),
        ):
            audit = MODULE.apply_preview(preview, preview["approvalHash"])

        self.assertEqual(audit["status"], "applied")
        self.assertIn(
            "description",
            {change["field"] for change in audit["requestedDiff"]},
        )
        self.assertIn(
            "etag", {change["field"] for change in audit["appliedDiff"]}
        )
        self.assertEqual(
            audit["eventContext"]["before"]["attendeeState"], "self-only"
        )
        self.assertEqual(
            audit["eventContext"]["before"]["conference"]["state"], "present"
        )
        self.assertTrue(audit["verification"]["calendarRereadBeforeWrite"])
        self.assertTrue(audit["verification"]["writeResponseStateParsed"])
        exact_json = json.dumps(audit)
        redacted_json = json.dumps(audit["redacted"])
        self.assertIn("Private replacement notes", exact_json)
        self.assertNotIn("Private replacement notes", redacted_json)
        self.assertNotIn("Private source title", redacted_json)
        self.assertIn("description", audit["redacted"]["changedFields"])

    def test_create_audit_uses_google_response_for_organizer_state(self) -> None:
        with mock.patch.object(MODULE, "_select_calendar", return_value=calendar()):
            preview = MODULE.create_preview(
                "work", "team@example.com", create_request(), access_token="token"
            )
        response = copy.deepcopy(preview["request"]["body"])
        response.update(
            {
                "organizer": {
                    "email": "sourya4@trymyzone.com",
                    "self": True,
                },
                "creator": {
                    "email": "sourya4@trymyzone.com",
                    "self": True,
                },
                "status": "confirmed",
                "etag": '"created"',
                "htmlLink": "https://calendar.google.com/event?eid=fixture",
            }
        )
        with (
            mock.patch.object(MODULE, "_require_write_scopes"),
            mock.patch.object(MODULE, "_access_token", return_value="token"),
            mock.patch.object(MODULE, "_select_calendar", return_value=calendar()),
            mock.patch.object(MODULE, "_get_event_optional", return_value=None),
            mock.patch.object(MODULE, "_execute_request", return_value=response),
        ):
            audit = MODULE.apply_preview(preview, preview["approvalHash"])

        organizer = audit["eventContext"]["after"]["organizer"]
        self.assertTrue(organizer["self"])
        self.assertTrue(organizer["selectedAccountIsOrganizer"])
        self.assertEqual(audit["appliedState"]["status"], "confirmed")

    def test_credential_file_must_be_private(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "work.json"
            path.write_text(
                json.dumps(
                    {
                        "client_id": "client",
                        "client_secret": "secret",
                        "refresh_token": "refresh",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                ),
                encoding="utf-8",
            )
            path.chmod(0o644)
            with (
                mock.patch.dict(os.environ, {"GWS_ACCOUNTS_DIR": temp_dir}),
                self.assertRaisesRegex(MODULE.CalendarSafeError, "too broad"),
            ):
                MODULE._load_credentials("work")

    def test_missing_token_uri_defaults_to_google_endpoint_without_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "personal.json"
            path.write_text(
                json.dumps(
                    {
                        "client_id": "client",
                        "client_secret": "secret",
                        "refresh_token": "refresh",
                    }
                ),
                encoding="utf-8",
            )
            path.chmod(0o600)
            with mock.patch.dict(os.environ, {"GWS_ACCOUNTS_DIR": temp_dir}):
                credentials = MODULE._load_credentials("personal")
            self.assertEqual(
                credentials["token_uri"], "https://oauth2.googleapis.com/token"
            )
            self.assertNotIn("token_uri", json.loads(path.read_text(encoding="utf-8")))

    def test_help_runs_without_authentication(self) -> None:
        result = subprocess.run(
            [str(HELPER), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("create-preview", result.stdout)
        self.assertIn("delete-preview", result.stdout)


if __name__ == "__main__":
    unittest.main()
