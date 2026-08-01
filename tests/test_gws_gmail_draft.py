"""Tests for the portable Gmail draft-only helper."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER = REPO_ROOT / "bin" / "gws-gmail-draft"


def run_helper(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(HELPER), *args],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


class GmailDraftHelperTests(unittest.TestCase):
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
        self.assertNotIn('"drafts",\n        "send"', source)
        self.assertNotIn('"messages",\n        "send"', source)
        self.assertIn('"drafts",\n        "create"', source)

    def test_live_path_invokes_only_drafts_create(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fake_gws = temp_path / "gws-account"
            args_log = temp_path / "args.log"
            fake_gws.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' \"$@\" > \"$FAKE_GWS_ARGS_LOG\"\n"
                "printf '%s\\n' '{\"id\":\"draft-1\",\"message\":{\"id\":\"message-1\",\"threadId\":\"thread-1\"}}'\n",
                encoding="utf-8",
            )
            fake_gws.chmod(0o700)
            env = os.environ.copy()
            env["PATH"] = f"{temp_path}:{env['PATH']}"
            env["FAKE_GWS_ARGS_LOG"] = str(args_log)

            result = run_helper(
                "work",
                "--to",
                "self@example.com",
                "--subject",
                "Route test",
                "--body",
                "Never send",
                env=env,
            )

            invoked_args = args_log.read_text(encoding="utf-8").splitlines()

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "draft_created")
        self.assertEqual(payload["draftId"], "draft-1")
        self.assertEqual(invoked_args[:5], ["work", "gmail", "users", "drafts", "create"])
        self.assertNotIn("send", invoked_args)


if __name__ == "__main__":
    unittest.main()
