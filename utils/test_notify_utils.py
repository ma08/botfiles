from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import notify_utils


def write_task_status(
    project_root: Path,
    *,
    folder_name: str,
    agent_session_id: str,
    zellij_session: str,
    zellij_link: str,
) -> Path:
    task_dir = project_root / "context" / "daily" / "2026-05-10" / folder_name
    task_dir.mkdir(parents=True, exist_ok=True)
    status_file = task_dir / "status.md"
    status_file.write_text(
        "\n".join(
            [
                f"# {folder_name}",
                "",
                "<!-- TASK-METADATA:START -->",
                "## Task Metadata",
                "- Tracker Kind: linear",
                f"- Tracker URL: https://linear.app/trymyzone/issue/{folder_name}",
                f"- Tracker Human ID: {folder_name}",
                "- Tracker Title: Test Task",
                "- Machine: TestMachine",
                "- Coding Agent: codex",
                f"- Agent Session ID: {agent_session_id}",
                f"- Task Folder: {task_dir}",
                f"- Task Status Path: {status_file}",
                "- Transcript Path: none",
                "- Last Synced: 2026-05-10 ~06:00pm PST",
                f"- Workspace Path: {project_root}",
                f"- Zellij Session: {zellij_session}",
                f"- Zellij Link: {zellij_link}",
                "- Remote Session Anchor Kind: linear_issue_body",
                "- Remote Session Anchor ID: LIVE-SESSION",
                "- GitHub Issue: none",
                "- GitHub Repo: none",
                "- GitHub Issue Number: none",
                "<!-- TASK-METADATA:END -->",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return status_file


class TaskZellijContextTests(unittest.TestCase):
    def test_resolves_zellij_context_by_agent_session_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            (project_root / "AGENTS.md").write_text("# Test\n", encoding="utf-8")
            write_task_status(
                project_root,
                folder_name="zon-128-alpha",
                agent_session_id="thread-alpha",
                zellij_session="zellij-alpha",
                zellij_link="https://zellij.example/alpha",
            )
            write_task_status(
                project_root,
                folder_name="zon-170-beta",
                agent_session_id="thread-beta",
                zellij_session="zellij-beta",
                zellij_link="https://zellij.example/beta",
            )

            context = notify_utils.get_task_zellij_context(
                working_directory_override=project_root,
                agent_session_id="thread-alpha",
                coding_agent_override="codex",
            )

            self.assertEqual(context["session_name"], "zellij-alpha")
            self.assertEqual(context["session_url"], "https://zellij.example/alpha")

    def test_send_notification_prefers_task_zellij_context_over_proxy_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            (project_root / "AGENTS.md").write_text("# Test\n", encoding="utf-8")
            write_task_status(
                project_root,
                folder_name="zon-128-alpha",
                agent_session_id="thread-alpha",
                zellij_session="zellij-alpha",
                zellij_link="https://zellij.example/alpha",
            )
            config = {
                "whatsapp_enabled": False,
                "whatsapp_token": "",
                "phone_number_id": "",
                "notify_phone_number": "",
                "zellij_web_enable_links": True,
                "zellij_web_base_url": "https://fallback.example",
                "zellij_send_attach_command": True,
                "email_enabled": True,
                "email_provider": "gmail",
                "email_to": "dev@example.com",
                "email_from": "agent@example.com",
                "email_subject_prefix": "AgentAlert",
                "email_task_label": "",
                "gmail_oauth_client_secret_path": "",
                "gmail_oauth_token_path": "",
                "gmail_thread_state_path": "",
            }

            with mock.patch.dict(
                os.environ,
                {
                    "ZELLIJ_SESSION_NAME": "stale-zellij",
                    "ZELLIJ": "",
                    "SYSTEM_NAME": "TestMachine",
                },
            ):
                with mock.patch.object(notify_utils, "get_config", return_value=config):
                    with mock.patch.object(notify_utils, "send_email_notification") as send_email:
                        notify_utils.send_notification(
                            title="Codex Needs Input",
                            message="Awaiting input",
                            send_local=False,
                            agent_session_id_override="thread-alpha",
                            coding_agent_override="codex",
                            working_directory_override=project_root,
                        )

            self.assertEqual(send_email.call_count, 1)
            kwargs = send_email.call_args.kwargs
            self.assertEqual(kwargs["session_name"], "zellij-alpha")
            self.assertEqual(kwargs["session_url"], "https://zellij.example/alpha")
            self.assertEqual(kwargs["attach_command"], "zellij attach zellij-alpha")
            self.assertIn("zj:zellij-alpha", kwargs["preview_line"])
            self.assertNotIn("stale-zellij", kwargs["preview_line"])

    def test_send_notification_uses_app_notify_session_for_untracked_thread(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project_root = tmp_path / "personal_os"
            project_root.mkdir()
            (project_root / "AGENTS.md").write_text("# Test\n", encoding="utf-8")
            session_dir = tmp_path / "notify" / "sessions" / "test-new-notify"
            session_dir.mkdir(parents=True)
            (session_dir / "events.jsonl").write_text(
                "\n".join(
                    [
                        '{"direction":"client_to_server","event":"frame","method":"turn/start",'
                        '"threadId":"thread-untracked","ts":"2026-05-11T03:40:44Z"}',
                        '{"direction":"server_to_client","event":"frame","method":"turn/completed",'
                        '"threadId":"thread-untracked","ts":"2026-05-11T03:40:48Z"}',
                    ]
                ),
                encoding="utf-8",
            )
            config = {
                "whatsapp_enabled": False,
                "whatsapp_token": "",
                "phone_number_id": "",
                "notify_phone_number": "",
                "zellij_web_enable_links": True,
                "zellij_web_base_url": "https://fallback.example",
                "zellij_send_attach_command": True,
                "email_enabled": True,
                "email_provider": "gmail",
                "email_to": "dev@example.com",
                "email_from": "agent@example.com",
                "email_subject_prefix": "AgentAlert",
                "email_task_label": "",
                "gmail_oauth_client_secret_path": "",
                "gmail_oauth_token_path": "",
                "gmail_thread_state_path": "",
            }

            with mock.patch.dict(
                os.environ,
                {
                    "CODEX_APP_NOTIFY_STATE_DIR": str(session_dir),
                    "ZELLIJ_SESSION_NAME": "stale-zellij",
                    "ZELLIJ": "",
                    "SYSTEM_NAME": "TestMachine",
                },
            ):
                with mock.patch.object(notify_utils, "get_config", return_value=config):
                    with mock.patch.object(notify_utils, "send_email_notification") as send_email:
                        notify_utils.send_notification(
                            title="Codex",
                            message="Finished",
                            send_local=False,
                            agent_session_id_override="thread-untracked",
                            coding_agent_override="codex",
                            working_directory_override=project_root,
                        )

            self.assertEqual(send_email.call_count, 1)
            kwargs = send_email.call_args.kwargs
            self.assertEqual(kwargs["session_name"], "test-new-notify")
            self.assertEqual(kwargs["session_url"], "https://fallback.example/test-new-notify")
            self.assertEqual(kwargs["attach_command"], "zellij attach test-new-notify")
            self.assertIn("personal-os | zj:test-new-notify", kwargs["preview_line"])
            self.assertNotIn("stale-zellij", kwargs["preview_line"])

    def test_send_notification_keeps_environment_context_without_explicit_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            (project_root / "AGENTS.md").write_text("# Test\n", encoding="utf-8")
            write_task_status(
                project_root,
                folder_name="zon-128-alpha",
                agent_session_id="thread-alpha",
                zellij_session="zellij-alpha",
                zellij_link="https://zellij.example/alpha",
            )
            config = {
                "whatsapp_enabled": False,
                "whatsapp_token": "",
                "phone_number_id": "",
                "notify_phone_number": "",
                "zellij_web_enable_links": True,
                "zellij_web_base_url": "https://fallback.example",
                "zellij_send_attach_command": True,
                "email_enabled": True,
                "email_provider": "gmail",
                "email_to": "dev@example.com",
                "email_from": "agent@example.com",
                "email_subject_prefix": "AgentAlert",
                "email_task_label": "",
                "gmail_oauth_client_secret_path": "",
                "gmail_oauth_token_path": "",
                "gmail_thread_state_path": "",
            }

            with mock.patch.dict(
                os.environ,
                {
                    "ZELLIJ_SESSION_NAME": "env-zellij",
                    "ZELLIJ": "",
                    "SYSTEM_NAME": "TestMachine",
                    "CODEX_THREAD_ID": "thread-alpha",
                },
            ):
                with mock.patch.object(notify_utils, "get_config", return_value=config):
                    with mock.patch.object(notify_utils, "send_email_notification") as send_email:
                        notify_utils.send_notification(
                            title="Codex",
                            message="Finished",
                            send_local=False,
                            coding_agent_override="codex",
                            working_directory_override=project_root,
                        )

            self.assertEqual(send_email.call_count, 1)
            kwargs = send_email.call_args.kwargs
            self.assertEqual(kwargs["session_name"], "env-zellij")
            self.assertEqual(kwargs["session_url"], "https://fallback.example/env-zellij")
            self.assertEqual(kwargs["attach_command"], "zellij attach env-zellij")


if __name__ == "__main__":
    unittest.main()
