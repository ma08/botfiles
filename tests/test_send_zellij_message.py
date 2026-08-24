"""Regression tests for fail-closed cross-session zellij delivery."""

from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER = REPO_ROOT / "bin" / "send-zellij-message"
BIN_DIR = str(REPO_ROOT / "bin")
if BIN_DIR not in sys.path:
    sys.path.insert(0, BIN_DIR)

LOADER = importlib.machinery.SourceFileLoader("send_zellij_message", str(HELPER))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
assert SPEC
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[LOADER.name] = MODULE
LOADER.exec_module(MODULE)

CLAUDE_EMPTY = """Claude Code
───────────────────────
❯\u00a0
───────────────────────
INSERT
"""
CLAUDE_NONEMPTY = """Claude Code
───────────────────────
❯\u00a0commit the task scaffold
───────────────────────
INSERT
"""
CODEX_EMPTY = (
    "Codex\n\x1b[1m›\x1b[m \x1b[2mImplement {feature}\x1b[m  gpt-5.6-sol medium\n"
)
CODEX_NONEMPTY = "Codex\n\x1b[1m›\x1b[m existing human text  gpt-5.6-sol medium\n"


def args(
    *,
    execute: bool = True,
    submit: str = "enter",
    replace_claude_suggestion: bool = False,
) -> argparse.Namespace:
    return argparse.Namespace(
        project_root=str(REPO_ROOT),
        target=None,
        task_dir=None,
        status_file=None,
        zellij_session="fixture-session",
        tab_name="Tab #1",
        text="new bounded instruction",
        submit=submit,
        execute=execute,
        replace_claude_suggestion=replace_claude_suggestion,
        json=True,
    )


def resolution() -> dict:
    return {
        "status": "resolved",
        "resolution_source": "zellij_session",
        "current_machine": "test-machine",
        "query": "fixture-session",
        "primary": {
            "task_dir": "none",
            "status_file": "none",
            "metadata": {
                "zellij_session": "fixture-session",
                "tracker_human_id": "none",
                "machine": "test-machine",
                "coding_agent": "claude",
            },
        },
    }


def session() -> object:
    return SimpleNamespace(
        session_name="fixture-session",
        state="active",
        tab_names=["Tab #1"],
        selected_tab_name="Tab #1",
        tab_selection_reason="explicit",
        clients=[],
        warnings=[],
    )


class ComposerClassificationTests(unittest.TestCase):
    def test_claude_empty_composer_is_safe(self) -> None:
        result = MODULE.inspect_composer("claude", CLAUDE_EMPTY)
        self.assertEqual(result.state, "empty")

    def test_claude_nonempty_composer_is_unsafe(self) -> None:
        result = MODULE.inspect_composer("claude", CLAUDE_NONEMPTY)
        self.assertEqual(result.state, "nonempty")
        self.assertIn("commit the task scaffold", result.composer_text)

    def test_claude_visible_suggestion_requires_cursor_at_empty_prompt(self) -> None:
        result = MODULE.inspect_composer("claude", CLAUDE_NONEMPTY, cursor_x=3)
        self.assertEqual(result.state, "suggestion")

    def test_claude_real_text_with_advanced_cursor_remains_unsafe(self) -> None:
        result = MODULE.inspect_composer("claude", CLAUDE_NONEMPTY, cursor_x=27)
        self.assertEqual(result.state, "nonempty")

    def test_claude_long_wrapped_composer_finds_its_boundary(self) -> None:
        wrapped = "\n".join(f"wrapped line {index}" for index in range(20))
        screen = (
            "Claude Code\n───────────────────────\n"
            f"❯\u00a0first line\n{wrapped}\n───────────────────────\nINSERT\n"
        )
        result = MODULE.inspect_composer("claude", screen, cursor_x=14)
        self.assertEqual(result.state, "nonempty")
        self.assertIn("wrapped line 19", result.composer_text)

    def test_codex_dim_placeholder_is_safe(self) -> None:
        result = MODULE.inspect_composer("codex", CODEX_EMPTY)
        self.assertEqual(result.state, "empty")

    def test_codex_normal_intensity_text_is_unsafe(self) -> None:
        result = MODULE.inspect_composer("codex", CODEX_NONEMPTY)
        self.assertEqual(result.state, "nonempty")

    def test_unknown_ui_fails_closed(self) -> None:
        result = MODULE.inspect_composer(
            "claude", "interactive selector without composer"
        )
        self.assertEqual(result.state, "unavailable")


class RuntimeNamespaceTests(unittest.TestCase):
    def test_live_systemd_namespace_replaces_exited_shadow(self) -> None:
        listings = iter(
            [
                (
                    0,
                    "target-session [Created now] (EXITED - attach to resurrect)\n",
                    "",
                ),
                (0, "target-session [Created now]\n", ""),
            ]
        )
        with (
            mock.patch.dict(os.environ, {}, clear=True),
            mock.patch.object(MODULE.os, "getuid", return_value=123),
            mock.patch.object(
                MODULE,
                "run_local_command",
                side_effect=lambda *_a, **_k: next(listings),
            ),
        ):
            notice = MODULE.select_zellij_runtime_namespace("target-session")
            selected = os.environ.get("XDG_RUNTIME_DIR")

        self.assertEqual(selected, "/run/user/123")
        self.assertIn("exited", notice)

    def test_active_default_namespace_is_preserved(self) -> None:
        with (
            mock.patch.dict(os.environ, {}, clear=True),
            mock.patch.object(
                MODULE,
                "run_local_command",
                return_value=(0, "target-session [Created now]\n", ""),
            ) as command,
        ):
            notice = MODULE.select_zellij_runtime_namespace("target-session")
            selected = os.environ.get("XDG_RUNTIME_DIR")

        self.assertIsNone(selected)
        self.assertEqual(notice, "")
        command.assert_called_once()


class PaneResolutionTests(unittest.TestCase):
    def test_agent_pane_is_selected_instead_of_focused_shell(self) -> None:
        panes = [
            {
                "id": 0,
                "is_plugin": False,
                "is_focused": True,
                "is_selectable": True,
                "exited": False,
                "is_held": False,
                "is_suppressed": False,
                "tab_name": "Tab #1",
                "terminal_command": "/bin/bash",
                "pane_command": "/bin/bash",
            },
            {
                "id": 1,
                "is_plugin": False,
                "is_focused": False,
                "is_selectable": True,
                "exited": False,
                "is_held": False,
                "is_suppressed": False,
                "tab_name": "Tab #1",
                "terminal_command": "/usr/local/bin/claude",
                "pane_command": "node",
            },
        ]
        with mock.patch.object(
            MODULE,
            "run_local_command",
            return_value=(0, json.dumps(panes), ""),
        ):
            pane, error = MODULE.resolve_agent_pane("fixture-session", "Tab #1", "none")

        self.assertEqual(error, "")
        self.assertIsNotNone(pane)
        self.assertEqual(pane.pane_id, "terminal_1")
        self.assertEqual(pane.agent, "claude")

    def test_explicit_session_identifies_wrapped_codex_from_ui(self) -> None:
        panes = [
            {
                "id": 0,
                "is_plugin": False,
                "is_focused": True,
                "is_selectable": True,
                "exited": False,
                "is_held": False,
                "is_suppressed": False,
                "tab_name": "Tab #1",
                "terminal_command": "",
                "pane_command": "",
                "cursor_coordinates_in_pane": [3, 45],
            }
        ]

        def command_result(
            command: list[str], **_kwargs: object
        ) -> tuple[int, str, str]:
            if "list-panes" in command:
                return 0, json.dumps(panes), ""
            if "terminal_0" in command:
                return 0, CODEX_EMPTY, ""
            return 1, "", "unexpected pane"

        with mock.patch.object(
            MODULE,
            "run_local_command",
            side_effect=command_result,
        ):
            pane, error = MODULE.resolve_agent_pane("fixture-session", "Tab #1", "none")

        self.assertEqual(error, "")
        self.assertIsNotNone(pane)
        self.assertEqual(pane.pane_id, "terminal_0")
        self.assertEqual(pane.agent, "codex")

    def test_expected_agent_metadata_does_not_turn_a_shell_into_an_agent_pane(
        self,
    ) -> None:
        panes = [
            {
                "id": 0,
                "is_plugin": False,
                "is_focused": True,
                "is_selectable": True,
                "exited": False,
                "is_held": False,
                "is_suppressed": False,
                "tab_name": "Tab #1",
                "terminal_command": "/bin/bash",
                "pane_command": "/bin/bash",
            }
        ]
        with mock.patch.object(
            MODULE,
            "run_local_command",
            return_value=(0, json.dumps(panes), ""),
        ):
            pane, error = MODULE.resolve_agent_pane(
                "fixture-session", "Tab #1", "claude"
            )

        self.assertIsNone(pane)
        self.assertIn("no unique matching agent pane", error)

    def test_wrapped_claude_pane_is_identified_by_read_only_ui_fingerprint(
        self,
    ) -> None:
        panes = [
            {
                "id": 0,
                "is_plugin": False,
                "is_focused": True,
                "is_selectable": True,
                "exited": False,
                "is_held": False,
                "is_suppressed": False,
                "tab_name": "Tab #1",
                "terminal_command": "/bin/bash",
                "pane_command": "/bin/bash",
            },
            {
                "id": 1,
                "is_plugin": False,
                "is_focused": False,
                "is_selectable": True,
                "exited": False,
                "is_held": False,
                "is_suppressed": False,
                "tab_name": "Tab #1",
                "terminal_command": "/task/bootstrap.sh",
                "pane_command": "npm exec @playwright/mcp@latest",
            },
        ]

        def command_result(
            command: list[str], **_kwargs: object
        ) -> tuple[int, str, str]:
            if "list-panes" in command:
                return 0, json.dumps(panes), ""
            if "terminal_1" in command:
                return 0, "Claude Code\n123 tokens\n" + CLAUDE_NONEMPTY, ""
            return 0, "shell prompt\n$ ", ""

        with mock.patch.object(
            MODULE,
            "run_local_command",
            side_effect=command_result,
        ):
            pane, error = MODULE.resolve_agent_pane(
                "fixture-session", "Tab #1", "claude"
            )

        self.assertEqual(error, "")
        self.assertIsNotNone(pane)
        self.assertEqual(pane.pane_id, "terminal_1")
        self.assertEqual(pane.agent, "claude")


@mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": "/run/user/test"})
class FailClosedExecutionTests(unittest.TestCase):
    def test_claude_suggestion_override_is_explicit_and_preview_first(self) -> None:
        pane = MODULE.AgentPane(
            "terminal_7", "claude", "Tab #1", "claude", "node", cursor_x=3
        )
        for enabled, outcome, phase in (
            (False, "preview_unsafe", "unsafe_suggestion"),
            (True, "preview_probe_required", "suggestion_probe_required"),
        ):
            output = io.StringIO()
            with (
                mock.patch.object(
                    MODULE,
                    "parse_args",
                    return_value=args(execute=False, replace_claude_suggestion=enabled),
                ),
                mock.patch.object(MODULE, "resolve_target", return_value=resolution()),
                mock.patch.object(
                    MODULE, "inspect_session_target", return_value=session()
                ),
                mock.patch.object(
                    MODULE, "resolve_agent_pane", return_value=(pane, "")
                ),
                mock.patch.object(
                    MODULE, "dump_agent_screen", return_value=(CLAUDE_NONEMPTY, "")
                ),
                redirect_stdout(output),
            ):
                return_code = MODULE.main()

            receipt = json.loads(output.getvalue())
            self.assertEqual(return_code, 0)
            self.assertEqual(receipt["outcome"], outcome)
            self.assertEqual(receipt["phases"]["composer_preflight"], phase)
            self.assertFalse(receipt["executed"])

    def test_real_draft_at_prompt_column_is_detected_and_left_unchanged(self) -> None:
        pane = MODULE.AgentPane(
            "terminal_7", "claude", "Tab #1", "claude", "node", cursor_x=3
        )
        commands: list[list[str]] = []

        def command_spy(command: list[str], **_kwargs: object) -> tuple[int, str, str]:
            commands.append(command)
            return 0, "", ""

        screens = iter(
            [
                (CLAUDE_NONEMPTY, ""),
                (CLAUDE_NONEMPTY, ""),
                (CLAUDE_NONEMPTY, ""),
            ]
        )
        output = io.StringIO()
        with (
            mock.patch.object(
                MODULE,
                "parse_args",
                return_value=args(replace_claude_suggestion=True),
            ),
            mock.patch.object(MODULE, "resolve_target", return_value=resolution()),
            mock.patch.object(MODULE, "inspect_session_target", return_value=session()),
            mock.patch.object(MODULE, "resolve_agent_pane", return_value=(pane, "")),
            mock.patch.object(
                MODULE, "dump_agent_screen", side_effect=lambda *_a, **_k: next(screens)
            ),
            mock.patch.object(
                MODULE,
                "read_pane_cursor_x",
                side_effect=[(27, ""), (3, "")],
            ),
            mock.patch.object(MODULE, "run_local_command", side_effect=command_spy),
            redirect_stdout(output),
        ):
            return_code = MODULE.main()

        receipt = json.loads(output.getvalue())
        self.assertEqual(return_code, 3)
        self.assertEqual(receipt["outcome"], "unsafe_composer")
        self.assertEqual(
            receipt["phases"]["suggestion_probe"],
            "buffered_draft_cursor_restored",
        )
        self.assertFalse(receipt["executed"])
        self.assertEqual([command[-1] for command in commands], ["5", "1"])
        self.assertTrue(all("write-chars" not in command for command in commands))

    def test_real_draft_restore_requires_original_cursor_position(self) -> None:
        pane = MODULE.AgentPane(
            "terminal_7", "claude", "Tab #1", "claude", "node", cursor_x=3
        )
        screens = iter(
            [
                (CLAUDE_NONEMPTY, ""),
                (CLAUDE_NONEMPTY, ""),
                (CLAUDE_NONEMPTY, ""),
            ]
        )
        output = io.StringIO()
        with (
            mock.patch.object(
                MODULE,
                "parse_args",
                return_value=args(replace_claude_suggestion=True),
            ),
            mock.patch.object(MODULE, "resolve_target", return_value=resolution()),
            mock.patch.object(MODULE, "inspect_session_target", return_value=session()),
            mock.patch.object(MODULE, "resolve_agent_pane", return_value=(pane, "")),
            mock.patch.object(
                MODULE, "dump_agent_screen", side_effect=lambda *_a, **_k: next(screens)
            ),
            mock.patch.object(
                MODULE,
                "read_pane_cursor_x",
                side_effect=[(27, ""), (4, "")],
            ),
            mock.patch.object(MODULE, "run_local_command", return_value=(0, "", "")),
            redirect_stdout(output),
        ):
            return_code = MODULE.main()

        receipt = json.loads(output.getvalue())
        self.assertEqual(return_code, 4)
        self.assertEqual(receipt["outcome"], "unverified")
        self.assertEqual(
            receipt["phases"]["suggestion_probe"],
            "buffered_draft_restore_unverified",
        )
        self.assertFalse(receipt["executed"])

    def test_proven_suggestion_can_stage_and_deliver(self) -> None:
        pane = MODULE.AgentPane(
            "terminal_7", "claude", "Tab #1", "claude", "node", cursor_x=3
        )
        staged = CLAUDE_NONEMPTY.replace(
            "commit the task scaffold", "new bounded instruction"
        )
        busy = "Claude Code\nnew bounded instruction\nWorking… esc to interrupt\n"
        screens = iter(
            [
                (CLAUDE_NONEMPTY, ""),
                (CLAUDE_NONEMPTY, ""),
                (staged, ""),
                (busy, ""),
                (busy, ""),
            ]
        )
        commands: list[list[str]] = []

        def command_spy(command: list[str], **_kwargs: object) -> tuple[int, str, str]:
            commands.append(command)
            return 0, "", ""

        output = io.StringIO()
        with (
            mock.patch.object(
                MODULE,
                "parse_args",
                return_value=args(replace_claude_suggestion=True),
            ),
            mock.patch.object(MODULE, "resolve_target", return_value=resolution()),
            mock.patch.object(MODULE, "inspect_session_target", return_value=session()),
            mock.patch.object(MODULE, "resolve_agent_pane", return_value=(pane, "")),
            mock.patch.object(
                MODULE, "dump_agent_screen", side_effect=lambda *_a, **_k: next(screens)
            ),
            mock.patch.object(MODULE, "read_pane_cursor_x", return_value=(3, "")),
            mock.patch.object(MODULE, "run_local_command", side_effect=command_spy),
            redirect_stdout(output),
        ):
            return_code = MODULE.main()

        receipt = json.loads(output.getvalue())
        self.assertEqual(return_code, 0)
        self.assertEqual(receipt["outcome"], "delivered")
        self.assertEqual(receipt["phases"]["suggestion_probe"], "verified_empty_buffer")
        self.assertEqual(receipt["phases"]["delivery"], "verified_new_turn")
        self.assertEqual(
            [command[-1] for command in commands],
            ["5", "new bounded instruction", "13"],
        )

    def test_nonempty_claude_composer_issues_no_mutating_command(self) -> None:
        pane = MODULE.AgentPane("terminal_7", "claude", "Tab #1", "claude", "node")
        mutating_calls: list[list[str]] = []

        def command_spy(command: list[str], **_kwargs: object) -> tuple[int, str, str]:
            mutating_calls.append(command)
            return 0, "", ""

        output = io.StringIO()
        with (
            mock.patch.object(MODULE, "parse_args", return_value=args()),
            mock.patch.object(MODULE, "resolve_target", return_value=resolution()),
            mock.patch.object(MODULE, "inspect_session_target", return_value=session()),
            mock.patch.object(MODULE, "resolve_agent_pane", return_value=(pane, "")),
            mock.patch.object(
                MODULE, "dump_agent_screen", return_value=(CLAUDE_NONEMPTY, "")
            ),
            mock.patch.object(MODULE, "run_local_command", side_effect=command_spy),
            redirect_stdout(output),
        ):
            return_code = MODULE.main()

        receipt = json.loads(output.getvalue())
        self.assertEqual(return_code, 3)
        self.assertEqual(receipt["outcome"], "unsafe_composer")
        self.assertFalse(receipt["executed"])
        self.assertFalse(receipt["delivered"])
        self.assertEqual(mutating_calls, [])

    def test_dry_run_reports_unsafe_without_mutation(self) -> None:
        pane = MODULE.AgentPane("terminal_7", "claude", "Tab #1", "claude", "node")
        output = io.StringIO()
        with (
            mock.patch.object(MODULE, "parse_args", return_value=args(execute=False)),
            mock.patch.object(MODULE, "resolve_target", return_value=resolution()),
            mock.patch.object(MODULE, "inspect_session_target", return_value=session()),
            mock.patch.object(MODULE, "resolve_agent_pane", return_value=(pane, "")),
            mock.patch.object(
                MODULE, "dump_agent_screen", return_value=(CLAUDE_NONEMPTY, "")
            ),
            redirect_stdout(output),
        ):
            return_code = MODULE.main()

        receipt = json.loads(output.getvalue())
        self.assertEqual(return_code, 0)
        self.assertEqual(receipt["outcome"], "preview_unsafe")
        self.assertEqual(receipt["phases"]["text_staging"], "not_attempted")

    def test_busy_agent_is_unsafe_even_when_composer_looks_empty(self) -> None:
        pane = MODULE.AgentPane("terminal_7", "claude", "Tab #1", "claude", "node")
        busy_empty = CLAUDE_EMPTY + "Working… esc to interrupt\n"
        output = io.StringIO()
        with (
            mock.patch.object(MODULE, "parse_args", return_value=args(execute=False)),
            mock.patch.object(MODULE, "resolve_target", return_value=resolution()),
            mock.patch.object(MODULE, "inspect_session_target", return_value=session()),
            mock.patch.object(MODULE, "resolve_agent_pane", return_value=(pane, "")),
            mock.patch.object(
                MODULE, "dump_agent_screen", return_value=(busy_empty, "")
            ),
            redirect_stdout(output),
        ):
            return_code = MODULE.main()

        receipt = json.loads(output.getvalue())
        self.assertEqual(return_code, 0)
        self.assertEqual(receipt["outcome"], "preview_unsafe")
        self.assertEqual(receipt["composer_state"], "busy")
        self.assertEqual(receipt["phases"]["composer_preflight"], "unsafe_busy")

    def test_verified_delivery_uses_exact_agent_pane(self) -> None:
        pane = MODULE.AgentPane("terminal_7", "claude", "Tab #1", "claude", "node")
        staged = CLAUDE_NONEMPTY.replace(
            "commit the task scaffold", "new bounded instruction"
        )
        screens = iter([(CLAUDE_EMPTY, ""), (staged, "")])
        busy = "Claude Code\nnew bounded instruction\nWorking… esc to interrupt\n"
        screens = iter([(CLAUDE_EMPTY, ""), (staged, ""), (busy, ""), (busy, "")])
        commands: list[list[str]] = []

        def command_spy(command: list[str], **_kwargs: object) -> tuple[int, str, str]:
            commands.append(command)
            return 0, "", ""

        output = io.StringIO()
        with (
            mock.patch.object(MODULE, "parse_args", return_value=args()),
            mock.patch.object(MODULE, "resolve_target", return_value=resolution()),
            mock.patch.object(MODULE, "inspect_session_target", return_value=session()),
            mock.patch.object(MODULE, "resolve_agent_pane", return_value=(pane, "")),
            mock.patch.object(
                MODULE, "dump_agent_screen", side_effect=lambda *_a, **_k: next(screens)
            ),
            mock.patch.object(MODULE, "run_local_command", side_effect=command_spy),
            redirect_stdout(output),
        ):
            return_code = MODULE.main()

        receipt = json.loads(output.getvalue())
        self.assertEqual(return_code, 0)
        self.assertEqual(receipt["outcome"], "delivered")
        self.assertTrue(receipt["delivered"])
        self.assertEqual(receipt["phases"]["delivery"], "verified_new_turn")
        self.assertEqual(len(commands), 2)
        self.assertIn("--pane-id", commands[0])
        self.assertIn("terminal_7", commands[0])
        self.assertIn("--pane-id", commands[1])
        self.assertIn("terminal_7", commands[1])

    def test_staging_must_verify_before_enter(self) -> None:
        pane = MODULE.AgentPane("terminal_7", "claude", "Tab #1", "claude", "node")
        screens = iter([(CLAUDE_EMPTY, ""), (CLAUDE_EMPTY, "")])
        commands: list[list[str]] = []

        def command_spy(command: list[str], **_kwargs: object) -> tuple[int, str, str]:
            commands.append(command)
            return 0, "", ""

        output = io.StringIO()
        with (
            mock.patch.object(MODULE, "parse_args", return_value=args()),
            mock.patch.object(MODULE, "resolve_target", return_value=resolution()),
            mock.patch.object(MODULE, "inspect_session_target", return_value=session()),
            mock.patch.object(MODULE, "resolve_agent_pane", return_value=(pane, "")),
            mock.patch.object(
                MODULE, "dump_agent_screen", side_effect=lambda *_a, **_k: next(screens)
            ),
            mock.patch.object(MODULE, "run_local_command", side_effect=command_spy),
            redirect_stdout(output),
        ):
            return_code = MODULE.main()

        receipt = json.loads(output.getvalue())
        self.assertEqual(return_code, 4)
        self.assertEqual(receipt["phases"]["text_staging"], "unverified")
        self.assertEqual(len(commands), 1)
        self.assertIn("write-chars", commands[0])
        self.assertNotIn("write", commands[0])

    def test_submit_without_delivery_proof_is_unverified(self) -> None:
        pane = MODULE.AgentPane("terminal_7", "claude", "Tab #1", "claude", "node")
        staged = CLAUDE_NONEMPTY.replace(
            "commit the task scaffold", "new bounded instruction"
        )
        screens = iter([(CLAUDE_EMPTY, ""), (staged, "")])
        commands: list[list[str]] = []

        def command_spy(command: list[str], **_kwargs: object) -> tuple[int, str, str]:
            commands.append(command)
            return 0, "", ""

        output = io.StringIO()
        with (
            mock.patch.object(MODULE, "parse_args", return_value=args()),
            mock.patch.object(MODULE, "resolve_target", return_value=resolution()),
            mock.patch.object(MODULE, "inspect_session_target", return_value=session()),
            mock.patch.object(MODULE, "resolve_agent_pane", return_value=(pane, "")),
            mock.patch.object(
                MODULE, "dump_agent_screen", side_effect=lambda *_a, **_k: next(screens)
            ),
            mock.patch.object(MODULE, "run_local_command", side_effect=command_spy),
            mock.patch.object(MODULE, "DELIVERY_VERIFY_TIMEOUT_SECONDS", 0.0),
            redirect_stdout(output),
        ):
            return_code = MODULE.main()

        receipt = json.loads(output.getvalue())
        self.assertEqual(return_code, 4)
        self.assertEqual(receipt["outcome"], "unverified")
        self.assertFalse(receipt["delivered"])
        self.assertEqual(receipt["phases"]["submit_action"], "sent")
        self.assertEqual(receipt["phases"]["delivery"], "unverified")

    def test_enter_failure_is_not_delivery(self) -> None:
        pane = MODULE.AgentPane("terminal_7", "claude", "Tab #1", "claude", "node")
        staged = CLAUDE_NONEMPTY.replace(
            "commit the task scaffold", "new bounded instruction"
        )
        screens = iter([(CLAUDE_EMPTY, ""), (staged, "")])
        call_count = 0

        def command_spy(_command: list[str], **_kwargs: object) -> tuple[int, str, str]:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return 1, "", "simulated Enter failure"
            return 0, "", ""

        output = io.StringIO()
        with (
            mock.patch.object(MODULE, "parse_args", return_value=args()),
            mock.patch.object(MODULE, "resolve_target", return_value=resolution()),
            mock.patch.object(MODULE, "inspect_session_target", return_value=session()),
            mock.patch.object(MODULE, "resolve_agent_pane", return_value=(pane, "")),
            mock.patch.object(
                MODULE, "dump_agent_screen", side_effect=lambda *_a, **_k: next(screens)
            ),
            mock.patch.object(MODULE, "run_local_command", side_effect=command_spy),
            redirect_stdout(output),
        ):
            return_code = MODULE.main()

        receipt = json.loads(output.getvalue())
        self.assertEqual(return_code, 4)
        self.assertEqual(receipt["outcome"], "unverified")
        self.assertEqual(receipt["phases"]["submit_action"], "failed")
        self.assertEqual(receipt["phases"]["delivery"], "unverified")
        self.assertFalse(receipt["delivered"])

    def test_historical_duplicate_cannot_verify_a_lost_new_turn(self) -> None:
        pane = MODULE.AgentPane("terminal_7", "claude", "Tab #1", "claude", "node")
        historical = "❯ new bounded instruction\n● old response\n"
        preflight = historical + CLAUDE_EMPTY
        staged = historical + CLAUDE_NONEMPTY.replace(
            "commit the task scaffold", "new bounded instruction"
        )
        post = historical + "Working… esc to interrupt\n"
        screens = iter([(preflight, ""), (staged, ""), (post, ""), (post, "")])
        monotonic_values = iter([0.0, 0.0, 11.0])
        output = io.StringIO()

        with (
            mock.patch.object(MODULE, "parse_args", return_value=args()),
            mock.patch.object(MODULE, "resolve_target", return_value=resolution()),
            mock.patch.object(MODULE, "inspect_session_target", return_value=session()),
            mock.patch.object(MODULE, "resolve_agent_pane", return_value=(pane, "")),
            mock.patch.object(
                MODULE,
                "dump_agent_screen",
                side_effect=lambda *_a, **_k: next(screens),
            ),
            mock.patch.object(MODULE, "run_local_command", return_value=(0, "", "")),
            mock.patch.object(
                MODULE.time, "monotonic", side_effect=lambda: next(monotonic_values)
            ),
            mock.patch.object(MODULE.time, "sleep"),
            redirect_stdout(output),
        ):
            return_code = MODULE.main()

        receipt = json.loads(output.getvalue())
        self.assertEqual(return_code, 4)
        self.assertEqual(receipt["outcome"], "unverified")
        self.assertFalse(receipt["delivered"])


if __name__ == "__main__":
    unittest.main()
