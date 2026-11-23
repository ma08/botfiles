"""Unit tests for the Antigravity notification hook."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import antigravity_notification as hook


class AntigravityNotificationTests(unittest.TestCase):
    def test_stop_event_extracts_latest_planner_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript = Path(tmpdir) / "transcript.jsonl"
            transcript.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "USER_INPUT", "content": "Run tests"}),
                        json.dumps({"type": "PLANNER_RESPONSE", "content": "Running now."}),
                        json.dumps({"type": "GENERIC", "content": "tool output"}),
                        json.dumps({"type": "PLANNER_RESPONSE", "content": "All 12 tests passed."}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            payload = {
                "hookEventName": "Stop",
                "terminationReason": "NO_TOOL_CALL",
                "fullyIdle": True,
                "conversationId": "conv-12345678",
                "cwd": "/tmp/example-repo",
                "transcriptPath": str(transcript),
            }

            with mock.patch.object(hook, "send_notification") as send_mock:
                response = hook.handle_hook_payload(payload, sync=True)

            self.assertEqual(response, {})
            send_mock.assert_called_once_with(
                title="Antigravity",
                message="Finished Processing\nAll 12 tests passed.",
                agent_session_id_override="conv-12345678",
                coding_agent_override="antigravity",
                working_directory_override="/tmp/example-repo",
            )

    def test_stop_event_skips_user_canceled(self) -> None:
        payload = {
            "hookEventName": "Stop",
            "terminationReason": "USER_CANCELED",
            "fullyIdle": True,
            "conversationId": "conv-12345678",
        }
        with mock.patch.object(hook, "send_notification") as send_mock:
            response = hook.handle_hook_payload(payload, sync=True)

        self.assertEqual(response, {})
        send_mock.assert_not_called()

    def test_stop_event_skips_non_idle_normal_turn(self) -> None:
        payload = {
            "hookEventName": "Stop",
            "terminationReason": "NO_TOOL_CALL",
            "fullyIdle": False,
            "conversationId": "conv-12345678",
        }
        with mock.patch.object(hook, "send_notification") as send_mock:
            response = hook.handle_hook_payload(payload, sync=True)

        self.assertEqual(response, {})
        send_mock.assert_not_called()

    def test_stop_event_reports_error(self) -> None:
        payload = {
            "hookEventName": "Stop",
            "terminationReason": "ERROR",
            "error": "Model quota exceeded",
            "fullyIdle": True,
            "conversationId": "conv-err-9999",
            "workspacePaths": ["/tmp/ws-a"],
        }
        with mock.patch.object(hook, "send_notification") as send_mock:
            response = hook.handle_hook_payload(payload, sync=True)

        self.assertEqual(response, {})
        send_mock.assert_called_once_with(
            title="Antigravity",
            message="Stopped (ERROR)\nModel quota exceeded",
            agent_session_id_override="conv-err-9999",
            coding_agent_override="antigravity",
            working_directory_override="/tmp/ws-a",
        )

    def test_pretooluse_ask_question_notifies_and_allows(self) -> None:
        payload = {
            "hookEventName": "PreToolUse",
            "conversationId": "conv-ask-1234",
            "cwd": "/tmp/project",
            "toolCall": {
                "id": "call-1",
                "name": "ask_question",
                "args": {
                    "questions": [
                        {"question": "Which deployment environment should I target?"}
                    ]
                },
            },
        }
        with mock.patch.object(hook, "send_notification") as send_mock:
            response = hook.handle_hook_payload(payload, sync=True)

        self.assertEqual(response, {"decision": "allow"})
        send_mock.assert_called_once_with(
            title="Antigravity",
            message="Awaiting Your Input\nQuestion: Which deployment environment should I target?",
            agent_session_id_override="conv-ask-1234",
            coding_agent_override="antigravity",
            working_directory_override="/tmp/project",
        )


if __name__ == "__main__":
    unittest.main()
