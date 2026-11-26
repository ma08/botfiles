#!/usr/bin/env python3
"""Unit tests for Antigravity task-status, transcript, and ConversationService tooling."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import json
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BOTFILES_ROOT = Path(__file__).resolve().parents[1]
TASK_STATUS_SCRIPTS = (
    BOTFILES_ROOT / "codex" / "skills" / "_shared" / "task_status" / "scripts"
)
BIN_DIR = BOTFILES_ROOT / "bin"

for path_dir in (TASK_STATUS_SCRIPTS, BIN_DIR):
    if str(path_dir) not in sys.path:
        sys.path.insert(0, str(path_dir))

import session_orchestration_common  # noqa: E402
import task_status_common  # noqa: E402


def _load_antigravity_conversation_module():
    script_path = BIN_DIR / "antigravity-conversation"
    loader = importlib.machinery.SourceFileLoader(
        "antigravity_conversation_cli", str(script_path)
    )
    spec = importlib.util.spec_from_loader("antigravity_conversation_cli", loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


antigravity_conversation = _load_antigravity_conversation_module()


class AntigravityTaskStatusTests(unittest.TestCase):
    def test_resolve_agent_name_and_session_precedence(self) -> None:
        env = {
            "ANTIGRAVITY_CONVERSATION_ID": "conv-123",
            "CODEX_THREAD_ID": "codex-leaked-999",
        }
        self.assertEqual(task_status_common.resolve_agent_name(env), "antigravity")
        self.assertEqual(task_status_common.resolve_agent_session_id(env), "conv-123")

        flag_only_env = {"ANTIGRAVITY_AGENT": "1"}
        self.assertEqual(
            task_status_common.resolve_agent_name(flag_only_env), "antigravity"
        )

        explicit_override_env = {
            "CODING_AGENT": "codex",
            "AGENT_SESSION_ID": "explicit-777",
            "ANTIGRAVITY_CONVERSATION_ID": "conv-123",
            "CODEX_THREAD_ID": "codex-456",
        }
        self.assertEqual(
            task_status_common.resolve_agent_name(explicit_override_env), "codex"
        )
        self.assertEqual(
            task_status_common.resolve_agent_session_id(explicit_override_env),
            "explicit-777",
        )

        nested_codex_env = {
            "CODING_AGENT": "codex",
            "ANTIGRAVITY_CONVERSATION_ID": "conv-123",
            "CODEX_THREAD_ID": "codex-456",
        }
        self.assertEqual(
            task_status_common.resolve_agent_name(nested_codex_env), "codex"
        )
        self.assertEqual(
            task_status_common.resolve_agent_session_id(nested_codex_env), "codex-456"
        )

    def test_resolve_antigravity_transcript_path_from_app_data_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp) / "ag-data"
            transcript = (
                app_dir
                / "brain"
                / "conv-abc"
                / ".system_generated"
                / "logs"
                / "transcript.jsonl"
            )
            transcript.parent.mkdir(parents=True, exist_ok=True)
            transcript.write_text("", encoding="utf-8")

            resolved = task_status_common.resolve_transcript_path(
                "antigravity",
                "conv-abc",
                env={"ANTIGRAVITY_APP_DATA_DIR": str(app_dir)},
            )
            self.assertEqual(resolved, str(transcript.resolve()))

            missing = task_status_common.resolve_transcript_path(
                "antigravity",
                "does-not-exist",
                env={"ANTIGRAVITY_APP_DATA_DIR": str(app_dir)},
            )
            self.assertEqual(missing, "none")

    def test_extract_transcript_messages_antigravity_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            transcript = Path(tmp) / "transcript.jsonl"
            events = [
                {
                    "step_index": 0,
                    "source": "USER_EXPLICIT",
                    "type": "USER_INPUT",
                    "created_at": "2026-11-26T08:08:03Z",
                    "content": "<USER_REQUEST>\nHello Antigravity\n</USER_REQUEST>",
                },
                {
                    "step_index": 1,
                    "source": "MODEL",
                    "type": "PLANNER_RESPONSE",
                    "created_at": "2026-11-26T08:08:05Z",
                    "tool_calls": [{"name": "read_file"}],
                },
                {
                    "step_index": 2,
                    "source": "MODEL",
                    "type": "GENERIC",
                    "created_at": "2026-11-26T08:08:06Z",
                    "content": "tool output should be ignored",
                },
                {
                    "step_index": 3,
                    "source": "MODEL",
                    "type": "PLANNER_RESPONSE",
                    "created_at": "2026-11-26T08:08:10Z",
                    "content": "All done.",
                },
            ]
            transcript.write_text(
                "\n".join(json.dumps(item) for item in events) + "\n",
                encoding="utf-8",
            )

            messages = session_orchestration_common.extract_transcript_messages(
                str(transcript),
                limit=5,
            )
            self.assertEqual(
                messages,
                [
                    {
                        "timestamp": "2026-11-26T08:08:03Z",
                        "role": "user",
                        "phase": "",
                        "text": "Hello Antigravity",
                    },
                    {
                        "timestamp": "2026-11-26T08:08:10Z",
                        "role": "assistant",
                        "phase": "",
                        "text": "All done.",
                    },
                ],
            )


class _MockConversationHandler(BaseHTTPRequestHandler):
    recorded_calls: list[tuple[str, dict, str]] = []

    def log_message(self, format: str, *args) -> None:
        return

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        token = self.headers.get("x-antigravity-csrf-token", "")
        self.__class__.recorded_calls.append((self.path, body, token))

        if self.path.endswith("/GetConversation"):
            resp = {
                "id": body.get("conversationId", ""),
                "metadata": {"projectId": "proj-1"},
                "annotations": {"title": "TASK-999: Mock Title"},
                "state": {
                    "summary": "Mock summary",
                    "runState": "RUN_STATE_IDLE",
                    "updateTime": "2026-11-26T08:00:00Z",
                },
            }
        elif self.path.endswith("/UpdateConversation"):
            resp = {
                "id": body.get("conversationId", ""),
                "metadata": {"projectId": "proj-1"},
                "annotations": body.get("annotations", {}),
                "state": {"summary": "Mock summary", "runState": "RUN_STATE_IDLE"},
            }
        elif self.path.endswith("/ListConversations"):
            resp = {
                "conversations": [
                    {
                        "id": "conv-1",
                        "metadata": {"projectId": "proj-1"},
                        "annotations": {"title": "Alpha task"},
                        "state": {"summary": "First", "runState": "RUN_STATE_IDLE"},
                    },
                    {
                        "id": "conv-2",
                        "metadata": {"projectId": "proj-1"},
                        "annotations": {"title": "Beta task"},
                        "state": {"summary": "Second", "runState": "RUN_STATE_RUNNING"},
                    },
                ]
            }
        elif self.path.endswith("/CreateConversation"):
            resp = {
                "conversation": {
                    "id": "conv-new",
                    "metadata": {"projectId": body.get("projectId", "")},
                    "annotations": {"title": body.get("title", "")},
                    "state": {"summary": "Created", "runState": "RUN_STATE_RUNNING"},
                }
            }
        else:
            self.send_response(404)
            self.end_headers()
            return

        payload = json.dumps(resp).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class AntigravityConversationCliTests(unittest.TestCase):
    def setUp(self) -> None:
        _MockConversationHandler.recorded_calls = []
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _MockConversationHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.env = {
            "ANTIGRAVITY_LS_ADDRESS": f"{host}:{port}",
            "ANTIGRAVITY_CSRF_TOKEN": "csrf-secret",
            "ANTIGRAVITY_CONVERSATION_ID": "conv-1",
            "ANTIGRAVITY_PROJECT_ID": "proj-1",
        }

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def _run_cli(self, argv: list[str], env: dict[str, str] | None = None) -> tuple[int, str, str]:
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = antigravity_conversation.run_cli(argv, env=self.env if env is None else env)
        return code, out.getvalue(), err.getvalue()

    def test_missing_env_fails_closed(self) -> None:
        code, _, err = self._run_cli(["list"], env={})
        self.assertEqual(code, 1)
        self.assertIn("ANTIGRAVITY_LS_ADDRESS", err)
        self.assertIn("ANTIGRAVITY_CSRF_TOKEN", err)

        code, _, err = self._run_cli(
            ["get"],
            env={
                "ANTIGRAVITY_LS_ADDRESS": "127.0.0.1:1",
                "ANTIGRAVITY_CSRF_TOKEN": "tok",
            },
        )
        self.assertEqual(code, 1)
        self.assertIn("ANTIGRAVITY_CONVERSATION_ID", err)

    def test_get_rename_list_create_and_inspect(self) -> None:
        code, out, err = self._run_cli(["get", "--json"])
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["annotations"]["title"], "TASK-999: Mock Title")

        code, out, err = self._run_cli(["rename", "--title", "Updated Title", "--json"])
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["annotations"]["title"], "Updated Title")

        code, out, err = self._run_cli(["list", "--current-project", "--query", "beta", "--json"])
        self.assertEqual(code, 0, err)
        listed = json.loads(out)
        self.assertEqual([c["id"] for c in listed["conversations"]], ["conv-2"])

        code, out, err = self._run_cli(
            [
                "create",
                "--current-project",
                "--title",
                "Child task",
                "--model",
                "flash",
                "--tag",
                "worker",
                "--prompt",
                "/start-new-task TASK-1",
                "--json",
            ]
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["conversation"]["id"], "conv-new")

        inspected = session_orchestration_common.inspect_antigravity_conversation(
            "conv-1", env=self.env
        )
        self.assertEqual(
            inspected,
            {
                "id": "conv-1",
                "title": "TASK-999: Mock Title",
                "summary": "Mock summary",
                "run_state": "RUN_STATE_IDLE",
                "project_id": "proj-1",
                "update_time": "2026-11-26T08:00:00Z",
            },
        )
        self.assertEqual(_MockConversationHandler.recorded_calls[0][2], "csrf-secret")


if __name__ == "__main__":
    unittest.main()
