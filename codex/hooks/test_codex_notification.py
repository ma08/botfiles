from __future__ import annotations

import os
import unittest
from unittest import mock

import codex_notification


class CodexNotificationSessionResolutionTests(unittest.TestCase):
    def test_payload_thread_id_wins_over_stale_environment(self) -> None:
        payload = {
            "type": "agent-turn-complete",
            "thread-id": "019e150c-64a6-7691-beae-db922879b7d9",
            "turn-id": "019e150c-6ebe-7e21-ab4e-3f83a9c13312",
        }

        with mock.patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": "019df5c3-04cf-77c1-bef4-a27b2e7e1f69"},
            clear=False,
        ):
            self.assertEqual(
                codex_notification._resolve_agent_session_id(payload),
                "019e150c-64a6-7691-beae-db922879b7d9",
            )

    def test_environment_is_fallback_when_payload_has_no_session_id(self) -> None:
        payload = {"type": "agent-turn-complete", "last-assistant-message": "done"}

        with mock.patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": "019df5c3-04cf-77c1-bef4-a27b2e7e1f69"},
            clear=False,
        ):
            self.assertEqual(
                codex_notification._resolve_agent_session_id(payload),
                "019df5c3-04cf-77c1-bef4-a27b2e7e1f69",
            )

    def test_nested_payload_session_id_is_supported(self) -> None:
        payload = {
            "type": "agent-turn-complete",
            "event": {"threadId": "019e14b5-5f52-7f92-a498-7f014107b928"},
        }

        self.assertEqual(
            codex_notification._resolve_agent_session_id(payload),
            "019e14b5-5f52-7f92-a498-7f014107b928",
        )

    def test_handle_notification_passes_payload_session_to_notifier(self) -> None:
        payload = {
            "type": "agent-turn-complete",
            "thread-id": "019e150c-64a6-7691-beae-db922879b7d9",
            "cwd": "/home/azureuser/pro/personal_os",
            "last-assistant-message": "done",
        }

        with mock.patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": "019df5c3-04cf-77c1-bef4-a27b2e7e1f69"},
            clear=False,
        ):
            with mock.patch.object(codex_notification, "send_notification") as send_notification:
                codex_notification.handle_notification(payload)

        self.assertEqual(send_notification.call_count, 1)
        self.assertEqual(
            send_notification.call_args.kwargs["agent_session_id_override"],
            "019e150c-64a6-7691-beae-db922879b7d9",
        )
        self.assertEqual(
            send_notification.call_args.kwargs["working_directory_override"],
            "/home/azureuser/pro/personal_os",
        )


if __name__ == "__main__":
    unittest.main()
