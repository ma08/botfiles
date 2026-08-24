"""Tests for the portable Gmail draft-only helper."""

from __future__ import annotations

import base64
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
HELPER = REPO_ROOT / "bin" / "gws-gmail-draft"
ACCOUNT_HELPER = REPO_ROOT / "bin" / "gws-account"
LOADER = importlib.machinery.SourceFileLoader("gws_gmail_draft", str(HELPER))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
assert SPEC
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        del args

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def run_helper(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(HELPER), *args],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


class GmailDraftHelperTests(unittest.TestCase):
    def _write_credentials(
        self,
        directory: Path,
        *,
        mode: int = 0o600,
        token_uri: str = "https://oauth2.googleapis.com/token",
    ) -> Path:
        path = directory / "work.json"
        path.write_text(
            json.dumps(
                {
                    "client_id": "test-client",
                    "client_secret": "test-secret",
                    "refresh_token": "test-refresh",
                    "token_uri": token_uri,
                }
            ),
            encoding="utf-8",
        )
        path.chmod(mode)
        return path

    def test_plain_text_dry_run_is_draft_only(self) -> None:
        result = run_helper(
            "personal",
            "--to",
            "one@example.com,two@example.com",
            "--cc",
            "copy@example.com",
            "--bcc",
            "hidden@example.com",
            "--subject",
            "Test draft",
            "--body",
            "Hello",
            "--dry-run",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "dry_run")
        self.assertEqual(payload["account"], "personal")
        self.assertEqual(payload["to"], ["one@example.com", "two@example.com"])
        self.assertEqual(payload["cc"], ["copy@example.com"])
        self.assertNotIn("bcc", payload)
        self.assertEqual(payload["bccCount"], 1)
        self.assertNotIn("hidden@example.com", result.stdout)
        self.assertEqual(payload["gmailMethod"], "users.drafts.create")
        self.assertFalse(payload["willSend"])

    def test_html_body_file_and_attachment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            body_path = temp_path / "body.html"
            body_path.write_text("<p>Hello <b>world</b></p>", encoding="utf-8")
            attachment_path = temp_path / "note.txt"
            attachment_path.write_text("attachment", encoding="utf-8")

            result = run_helper(
                "work",
                "--subject",
                "HTML draft",
                "--body-file",
                str(body_path),
                "--html",
                "--attach",
                str(attachment_path),
                "--dry-run",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["bodyKind"], "html")
        self.assertEqual(payload["attachments"][0]["name"], "note.txt")
        self.assertEqual(payload["attachments"][0]["contentType"], "text/plain")

    def test_quoted_display_name_with_comma_is_one_recipient(self) -> None:
        result = run_helper(
            "personal",
            "--to",
            '"Doe, Jane" <jane@example.com>',
            "--subject",
            "Display name",
            "--body",
            "Hello",
            "--dry-run",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["to"], ['"Doe, Jane" <jane@example.com>'])

    def test_columbia_defaults_to_verified_send_as_address(self) -> None:
        result = run_helper(
            "columbia",
            "--subject",
            "Columbia sender",
            "--body",
            "Hello",
            "--dry-run",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["from"], "sourya.kakarla@columbia.edu")

    def test_columbia_primary_mailbox_address_can_be_requested(self) -> None:
        result = run_helper(
            "columbia",
            "--from-address",
            "sk5057@columbia.edu",
            "--subject",
            "Columbia primary sender",
            "--body",
            "Hello",
            "--dry-run",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["from"], "sk5057@columbia.edu")

    def test_header_injection_is_rejected(self) -> None:
        result = run_helper(
            "columbia",
            "--subject",
            "Safe\nBcc: attacker@example.com",
            "--body",
            "Hello",
            "--dry-run",
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot contain line breaks", result.stderr)

    def test_source_contains_no_send_api_route(self) -> None:
        source = HELPER.read_text(encoding="utf-8")
        self.assertIn("/gmail/v1/users/me/drafts", source)
        self.assertNotIn("/drafts/send", source)
        self.assertNotIn("/messages/send", source)

    def test_gmail_bootstrap_does_not_grant_calendar_write_scope(self) -> None:
        self.assertNotIn("calendar", MODULE.AUTH_SCOPES)
        for path in (REPO_ROOT / "bin" / "gws-account", REPO_ROOT / "bin" / "gws-save-account"):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("calendar.events", source)

    def test_large_message_payload_is_sent_in_https_body(self) -> None:
        raw = base64.urlsafe_b64encode(b"x" * 238_296).decode("ascii")
        captured: dict[str, object] = {}

        def opener(request: object, timeout: int) -> FakeResponse:
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse(
                {
                    "id": "draft-1",
                    "message": {"id": "message-1", "threadId": "thread-1"},
                }
            )

        response = MODULE._gmail_create_draft("test-access-token", raw, opener=opener)
        request = captured["request"]
        body = json.loads(request.data)

        self.assertEqual(response["id"], "draft-1")
        self.assertEqual(request.full_url, MODULE.GMAIL_DRAFTS_URL)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-access-token")
        self.assertEqual(body, {"message": {"raw": raw}})
        self.assertGreater(len(request.data), 300_000)
        self.assertEqual(captured["timeout"], 60)

    def test_credential_file_must_be_private(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            self._write_credentials(directory, mode=0o644)
            with (
                mock.patch.dict(os.environ, {"GWS_ACCOUNTS_DIR": temp_dir}),
                self.assertRaisesRegex(
                    MODULE.DraftCreationError, "permissions are too broad"
                ),
            ):
                MODULE._load_credentials("work")

    def test_token_refresh_rejects_unapproved_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            self._write_credentials(directory, token_uri="https://example.com/token")
            with (
                mock.patch.dict(os.environ, {"GWS_ACCOUNTS_DIR": temp_dir}),
                self.assertRaisesRegex(
                    MODULE.DraftCreationError, "not an approved Google HTTPS endpoint"
                ),
            ):
                MODULE._access_token("work")

    def test_token_refresh_requires_access_token(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            self._write_credentials(directory)
            with (
                mock.patch.dict(os.environ, {"GWS_ACCOUNTS_DIR": temp_dir}),
                mock.patch.object(MODULE, "urlopen", return_value=FakeResponse({})),
                self.assertRaisesRegex(
                    MODULE.DraftCreationError, "returned no access token"
                ),
            ):
                MODULE._access_token("work")

    def test_missing_compose_scope_stops_before_draft_create(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fake_gws = temp_path / "gws-account"
            create_marker = temp_path / "create-called"
            fake_gws.write_text(
                "#!/bin/sh\n"
                "if [ \"$2\" = auth ] && [ \"$3\" = status ]; then\n"
                "  printf '%s\\n' '{\"scopes\":[\"https://www.googleapis.com/auth/gmail.readonly\"]}'\n"
                "  exit 0\n"
                "fi\n"
                "touch \"$FAKE_GWS_CREATE_MARKER\"\n"
                "exit 99\n",
                encoding="utf-8",
            )
            fake_gws.chmod(0o700)
            env = os.environ.copy()
            env["PATH"] = f"{temp_path}:{env['PATH']}"
            env["FAKE_GWS_CREATE_MARKER"] = str(create_marker)

            result = run_helper(
                "columbia",
                "--to",
                "self@example.com",
                "--subject",
                "Scope test",
                "--body",
                "Never create",
                env=env,
            )

            self.assertFalse(create_marker.exists())

        self.assertEqual(result.returncode, 77)
        self.assertIn("missing the required gmail.compose scope", result.stderr)
        self.assertIn("gws-account columbia auth login --scopes", result.stderr)


class GwsAccountWrapperTests(unittest.TestCase):
    def test_derived_auth_cache_tracks_canonical_credential_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            accounts_dir = root / "accounts"
            state_root = root / "account-state"
            fake_bin = root / "bin"
            accounts_dir.mkdir()
            fake_bin.mkdir()

            credentials = accounts_dir / "personal.json"
            original = '{"refresh_token":"original","client_id":"id"}'
            replacement = '{"refresh_token":"replacement","client_id":"id"}'
            credentials.write_text(original, encoding="utf-8")
            credentials.chmod(0o600)

            state_dir = state_root / "personal"
            state_dir.mkdir(parents=True)
            encrypted_cache = state_dir / "credentials.enc"
            token_cache = state_dir / "token_cache.json"
            encrypted_cache.write_text("stale", encoding="utf-8")
            token_cache.write_text("stale", encoding="utf-8")

            fake_gws = fake_bin / "gws"
            fake_gws.write_text(
                "#!/bin/sh\n"
                'encrypted="$GOOGLE_WORKSPACE_CLI_CONFIG_DIR/credentials.enc"\n'
                'token="$GOOGLE_WORKSPACE_CLI_CONFIG_DIR/token_cache.json"\n'
                'if [ "$EXPECT_ENCRYPTED_CACHE" = absent ] && [ -e "$encrypted" ]; then exit 91; fi\n'
                'if [ "$EXPECT_ENCRYPTED_CACHE" = present ] && [ ! -e "$encrypted" ]; then exit 92; fi\n'
                'if [ "$EXPECT_TOKEN_CACHE" = absent ] && [ -e "$token" ]; then exit 93; fi\n'
                'if [ "$(umask)" != "$EXPECT_UMASK" ]; then exit 94; fi\n'
                'printf "%s\\n" refreshed > "$encrypted"\n'
                "printf '%s\\n' '{\"status\":\"ok\"}'\n",
                encoding="utf-8",
            )
            fake_gws.chmod(0o700)

            base_env = os.environ.copy()
            base_env.update(
                {
                    "HOME": str(root),
                    "GWS_ACCOUNTS_DIR": str(accounts_dir),
                    "GWS_ACCOUNT_STATE_DIR": str(state_root),
                    "GWS_REAL_BIN": str(fake_gws),
                    "PATH": f"{fake_bin}:{base_env['PATH']}",
                    "EXPECT_TOKEN_CACHE": "absent",
                    "EXPECT_UMASK": "0027",
                }
            )
            command = [
                "bash",
                "-c",
                'umask 0027; exec "$@"',
                "bash",
                str(ACCOUNT_HELPER),
                "personal",
                "auth",
                "status",
            ]

            first = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                env={**base_env, "EXPECT_ENCRYPTED_CACHE": "absent"},
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            marker = state_dir / "credentials.sha256"
            original_fingerprint = marker.read_text(encoding="utf-8")
            self.assertEqual(marker.stat().st_mode & 0o777, 0o600)

            second = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                env={**base_env, "EXPECT_ENCRYPTED_CACHE": "present"},
            )
            self.assertEqual(second.returncode, 0, second.stderr)

            credentials.write_text(replacement, encoding="utf-8")
            credentials.chmod(0o600)
            third = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                env={**base_env, "EXPECT_ENCRYPTED_CACHE": "absent"},
            )
            self.assertEqual(third.returncode, 0, third.stderr)
            self.assertNotEqual(
                marker.read_text(encoding="utf-8"), original_fingerprint
            )

            credentials.write_text(original, encoding="utf-8")
            credentials.chmod(0o600)
            os.utime(credentials, (1, 1))
            rollback = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                env={**base_env, "EXPECT_ENCRYPTED_CACHE": "absent"},
            )
            self.assertEqual(rollback.returncode, 0, rollback.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), original_fingerprint)


if __name__ == "__main__":
    unittest.main()
