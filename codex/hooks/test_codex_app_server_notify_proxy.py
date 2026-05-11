from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from codex_app_server_notify_proxy import (
    StateStore,
    ThreadContext,
    build_notification_message,
    decode_json_frame,
    first_question_summary,
    parse_request_user_input,
)


REQUEST_USER_INPUT_PAYLOAD = {
    "method": "item/tool/requestUserInput",
    "id": 0,
    "params": {
        "threadId": "thread-12345678",
        "turnId": "turn-87654321",
        "itemId": "call-abc12345",
        "questions": [
            {
                "id": "choice",
                "header": "Choose",
                "question": "Which option do you want?",
                "options": [
                    {"label": "A (Recommended)", "description": "Pick A."},
                    {"label": "B", "description": "Pick B."},
                    {"label": "C", "description": "Pick C."},
                ],
            }
        ],
    },
}


class RequestUserInputParsingTests(unittest.TestCase):
    def test_parse_request_user_input_extracts_context_and_question_summary(self) -> None:
        context = ThreadContext()
        context.note_server_payload(
            {
                "method": "thread/started",
                "params": {
                    "thread": {
                        "id": "thread-12345678",
                        "cwd": "/home/azureuser/pro/personal_os",
                    }
                },
            }
        )

        event = parse_request_user_input(REQUEST_USER_INPUT_PAYLOAD, context=context)

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.request_id, 0)
        self.assertEqual(event.thread_id, "thread-12345678")
        self.assertEqual(event.turn_id, "turn-87654321")
        self.assertEqual(event.item_id, "call-abc12345")
        self.assertEqual(event.cwd, "/home/azureuser/pro/personal_os")
        self.assertEqual(
            event.dedupe_key,
            "thread-12345678|turn-87654321|call-abc12345|0",
        )

        summary = first_question_summary(event)
        self.assertEqual(summary["question_count"], 1)
        self.assertEqual(summary["first_question_header"], "Choose")
        self.assertEqual(summary["first_question"], "Which option do you want?")
        self.assertEqual(summary["option_count"], 3)
        self.assertEqual(summary["recommended_option"], "A (Recommended)")

    def test_build_notification_message_is_concise(self) -> None:
        event = parse_request_user_input(REQUEST_USER_INPUT_PAYLOAD, context=ThreadContext())
        self.assertIsNotNone(event)
        assert event is not None

        message = build_notification_message(event)

        self.assertIn("Awaiting Your Input", message)
        self.assertIn("Question 1/1 - Choose: Which option do you want?", message)
        self.assertIn("Suggested: A (Recommended)", message)
        self.assertIn("Thread: thread-1", message)

    def test_ignores_malformed_json_and_unrelated_methods(self) -> None:
        self.assertIsNone(decode_json_frame("{not json"))
        self.assertIsNone(
            parse_request_user_input(
                {
                    "method": "item/started",
                    "params": {"threadId": "thread", "turnId": "turn", "itemId": "item"},
                }
            )
        )


class RequestUserInputStateTests(unittest.IsolatedAsyncioTestCase):
    async def test_state_suppresses_duplicate_after_reload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            event = parse_request_user_input(REQUEST_USER_INPUT_PAYLOAD)
            self.assertIsNotNone(event)
            assert event is not None

            first_store = StateStore(state_path)
            self.assertFalse(await first_store.mark_request_seen(event))

            second_store = StateStore(state_path)
            self.assertTrue(await second_store.mark_request_seen(event))

    async def test_state_clears_on_server_request_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            event = parse_request_user_input(REQUEST_USER_INPUT_PAYLOAD)
            self.assertIsNotNone(event)
            assert event is not None

            store = StateStore(state_path)
            await store.mark_request_seen(event)
            cleared = await store.clear_resolved(
                thread_id=event.thread_id,
                request_id=event.request_id,
                reason="serverRequest/resolved",
            )

            self.assertEqual(cleared, [event.dedupe_key])
            reloaded = StateStore(state_path)
            self.assertEqual(reloaded.data["pending_requests"], {})

    async def test_state_cleans_up_on_turn_completed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            event = parse_request_user_input(REQUEST_USER_INPUT_PAYLOAD)
            self.assertIsNotNone(event)
            assert event is not None

            store = StateStore(state_path)
            await store.mark_request_seen(event)
            cleared = await store.cleanup_thread_turn(
                thread_id=event.thread_id,
                turn_id=event.turn_id,
                reason="turn/completed",
            )

            self.assertEqual(cleared, [event.dedupe_key])


if __name__ == "__main__":
    unittest.main()
