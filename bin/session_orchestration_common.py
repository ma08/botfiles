#!/usr/bin/env python3
"""Shared helpers for cross-session orchestration workflows."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BOTFILES_ROOT = Path(__file__).resolve().parent.parent
TASK_STATUS_SCRIPTS = (
    BOTFILES_ROOT / "codex" / "skills" / "_shared" / "task_status" / "scripts"
)
if str(TASK_STATUS_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(TASK_STATUS_SCRIPTS))

from task_status_common import (  # noqa: E402
    TRACKER_KIND_NONE,
    TaskCandidate,
    TrackerTaskHome,
    build_task_recap,
    extract_primary_tracker_ref,
    infer_project_root_from_path,
    load_task_candidates,
    local_project_roots,
    merged_env_with_botfiles_defaults,
    normalize_task_metadata,
    read_task_metadata,
    resolve_machine_name,
    resolve_status_file,
    resolve_task_status_root,
    slugify,
    sort_task_candidates_by_recency,
    task_candidate_sort_key,
)

CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MAX_MESSAGE_CHARS = 2_000
DEFAULT_TRANSCRIPT_MESSAGE_LIMIT = 4
ZELLIJ_LIST_HEADER = "CLIENT_ID ZELLIJ_PANE_ID RUNNING_COMMAND"


@dataclass(frozen=True)
class CandidateHome:
    project_root: str
    task_status_root: str
    task_dir: str
    status_file: str
    metadata: dict[str, str]
    recap: list[str]


@dataclass(frozen=True)
class SessionClient:
    client_id: str
    pane_id: str
    running_command: str


@dataclass(frozen=True)
class SessionInspection:
    session_name: str
    state: str
    tab_names: list[str]
    selected_tab_name: str
    tab_selection_reason: str
    clients: list[SessionClient]
    warnings: list[str]


def add_target_resolution_arguments(parser) -> None:
    parser.add_argument(
        "target",
        nargs="?",
        help=(
            "Task slug, Linear issue id/url, GitHub issue url, or explicit target token. "
            "If omitted, use --task-dir, --status-file, or --zellij-session."
        ),
    )
    parser.add_argument(
        "--project-root",
        default=os.getcwd(),
        help="Project root used for local task-home discovery.",
    )
    parser.add_argument("--task-dir", help="Explicit task directory override.")
    parser.add_argument("--status-file", help="Explicit status.md/README.md override.")
    parser.add_argument(
        "--zellij-session",
        help="Explicit zellij session override. When provided, task metadata lookup becomes optional.",
    )
    parser.add_argument(
        "--tab-name",
        help="Explicit zellij tab name override. Otherwise resolve from tracker id or single-tab sessions.",
    )


def run_local_command(
    args: list[str],
    *,
    cwd: Path | None = None,
    timeout_seconds: int = 20,
) -> tuple[int, str, str]:
    process = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    return process.returncode, process.stdout, process.stderr


def _unique_candidates(candidates: list[TrackerTaskHome | tuple[Path, Path, TaskCandidate]]) -> list[CandidateHome]:
    by_task_dir: dict[Path, CandidateHome] = {}
    for item in candidates:
        if isinstance(item, TrackerTaskHome):
            project_root = item.project_root
            task_status_root = item.task_status_root
            candidate = item.candidate
        else:
            project_root, task_status_root, candidate = item
        task_dir = candidate.task_dir.resolve()
        status_file = candidate.status_file or resolve_status_file(candidate.task_dir)
        metadata = normalize_task_metadata(
            candidate.metadata,
            status_file=status_file,
            hydrate_transcript_path=True,
        )
        existing = by_task_dir.get(task_dir)
        home = CandidateHome(
            project_root=str(project_root.resolve()),
            task_status_root=str(task_status_root.resolve()),
            task_dir=str(task_dir),
            status_file=str(status_file.resolve()) if status_file else TRACKER_KIND_NONE,
            metadata=metadata,
            recap=build_task_recap(status_file),
        )
        if not existing:
            by_task_dir[task_dir] = home
            continue
        existing_candidate = TaskCandidate(
            task_dir=Path(existing.task_dir),
            status_file=Path(existing.status_file)
            if existing.status_file != TRACKER_KIND_NONE
            else None,
            metadata=existing.metadata,
        )
        if task_candidate_sort_key(candidate) > task_candidate_sort_key(existing_candidate):
            by_task_dir[task_dir] = home
    return sorted(
        by_task_dir.values(),
        key=lambda home: task_candidate_sort_key(
            TaskCandidate(
                task_dir=Path(home.task_dir),
                status_file=Path(home.status_file)
                if home.status_file != TRACKER_KIND_NONE
                else None,
                metadata=home.metadata,
            )
        ),
        reverse=True,
    )


def find_task_homes_for_slug(
    slug_or_query: str,
    *,
    current_project_root: Path,
) -> list[CandidateHome]:
    matches: list[tuple[Path, Path, TaskCandidate]] = []
    seen: set[Path] = set()
    raw = (slug_or_query or "").strip().lower()
    if not raw:
        return []
    slug_token = slugify(slug_or_query)
    tokens = [raw]
    if slug_token and slug_token != raw:
        tokens.append(slug_token)

    for project_root in local_project_roots(current_project_root):
        task_status_root = resolve_task_status_root(
            project_root,
            caller_path=TASK_STATUS_SCRIPTS / "get_task_details.py",
        )
        project_candidates: list[TaskCandidate] = []
        for token in tokens:
            project_candidates.extend(load_task_candidates(task_status_root, slug=token))
        unique_project_candidates = {
            candidate.task_dir.resolve(): candidate
            for candidate in sort_task_candidates_by_recency(project_candidates)
        }
        for task_dir, candidate in unique_project_candidates.items():
            if task_dir in seen:
                continue
            seen.add(task_dir)
            matches.append((project_root, task_status_root, candidate))

    return _unique_candidates(matches)


def find_task_homes_for_session(
    session_name: str,
    *,
    current_project_root: Path,
) -> list[CandidateHome]:
    matches: list[tuple[Path, Path, TaskCandidate]] = []
    normalized = (session_name or "").strip()
    if not normalized or normalized == TRACKER_KIND_NONE:
        return []

    for project_root in local_project_roots(current_project_root):
        task_status_root = resolve_task_status_root(
            project_root,
            caller_path=TASK_STATUS_SCRIPTS / "get_task_details.py",
        )
        for candidate in sort_task_candidates_by_recency(load_task_candidates(task_status_root)):
            metadata = normalize_task_metadata(
                candidate.metadata,
                status_file=candidate.status_file,
                hydrate_transcript_path=True,
            )
            if metadata.get("zellij_session", TRACKER_KIND_NONE) != normalized:
                continue
            matches.append((project_root, task_status_root, candidate))

    return _unique_candidates(matches)


def build_home_from_task_dir(task_dir: Path) -> CandidateHome:
    resolved_task_dir = task_dir.expanduser().resolve()
    status_file = resolve_status_file(resolved_task_dir)
    metadata = normalize_task_metadata(
        read_task_metadata(status_file),
        status_file=status_file,
        hydrate_transcript_path=True,
    )
    project_root = infer_project_root_from_path(resolved_task_dir) or resolved_task_dir
    task_status_root = resolve_task_status_root(
        project_root,
        caller_path=TASK_STATUS_SCRIPTS / "get_task_details.py",
    )
    return CandidateHome(
        project_root=str(project_root.resolve()),
        task_status_root=str(task_status_root.resolve()),
        task_dir=str(resolved_task_dir),
        status_file=str(status_file.resolve()) if status_file else TRACKER_KIND_NONE,
        metadata=metadata,
        recap=build_task_recap(status_file),
    )


def resolve_target(
    *,
    project_root: Path,
    target: str | None = None,
    task_dir: str | None = None,
    status_file: str | None = None,
    zellij_session: str | None = None,
) -> dict[str, Any]:
    resolved_project_root = project_root.expanduser().resolve()
    merged_env = merged_env_with_botfiles_defaults(
        dict(os.environ),
        caller_path=TASK_STATUS_SCRIPTS / "get_task_details.py",
    )
    current_machine = resolve_machine_name(merged_env)

    if status_file:
        home = build_home_from_task_dir(Path(status_file).expanduser().resolve().parent)
        return {
            "status": "resolved",
            "resolution_source": "status_file",
            "current_machine": current_machine,
            "query": status_file,
            "primary": asdict(home),
        }

    if task_dir:
        home = build_home_from_task_dir(Path(task_dir))
        return {
            "status": "resolved",
            "resolution_source": "task_dir",
            "current_machine": current_machine,
            "query": task_dir,
            "primary": asdict(home),
        }

    if zellij_session:
        matches = find_task_homes_for_session(
            zellij_session,
            current_project_root=resolved_project_root,
        )
        if len(matches) == 1:
            return {
                "status": "resolved",
                "resolution_source": "zellij_session",
                "current_machine": current_machine,
                "query": zellij_session,
                "primary": asdict(matches[0]),
            }
        if len(matches) > 1:
            return {
                "status": "ambiguous",
                "resolution_source": "zellij_session",
                "current_machine": current_machine,
                "query": zellij_session,
                "candidates": [asdict(match) for match in matches],
                "warning": "Multiple tracked task homes reference this zellij session.",
            }
        return {
            "status": "resolved",
            "resolution_source": "zellij_session",
            "current_machine": current_machine,
            "query": zellij_session,
            "primary": {
                "project_root": TRACKER_KIND_NONE,
                "task_status_root": TRACKER_KIND_NONE,
                "task_dir": TRACKER_KIND_NONE,
                "status_file": TRACKER_KIND_NONE,
                "metadata": {
                    "tracker_kind": TRACKER_KIND_NONE,
                    "tracker_url": TRACKER_KIND_NONE,
                    "tracker_human_id": TRACKER_KIND_NONE,
                    "tracker_title": TRACKER_KIND_NONE,
                    "machine": current_machine,
                    "coding_agent": TRACKER_KIND_NONE,
                    "agent_session_id": TRACKER_KIND_NONE,
                    "task_folder": TRACKER_KIND_NONE,
                    "task_status_path": TRACKER_KIND_NONE,
                    "transcript_path": TRACKER_KIND_NONE,
                    "workspace_path": TRACKER_KIND_NONE,
                    "zellij_session": zellij_session,
                    "zellij_link": TRACKER_KIND_NONE,
                    "remote_session_anchor_kind": TRACKER_KIND_NONE,
                    "remote_session_anchor_id": TRACKER_KIND_NONE,
                    "github_issue": TRACKER_KIND_NONE,
                    "github_repo": TRACKER_KIND_NONE,
                    "github_issue_number": TRACKER_KIND_NONE,
                    "linear_issue_id": TRACKER_KIND_NONE,
                    "linear_issue_identifier": TRACKER_KIND_NONE,
                    "linear_team_id": TRACKER_KIND_NONE,
                    "linear_team_name": TRACKER_KIND_NONE,
                    "linear_project_id": TRACKER_KIND_NONE,
                    "linear_project_name": TRACKER_KIND_NONE,
                },
                "recap": [
                    "What this task is about: No tracked task metadata was found for this session name.",
                    "Current status: Use the explicit zellij session override for local control only.",
                    "Next steps: Add --task-dir or --status-file if you need tracker-backed task context.",
                ],
            },
        }

    if not target:
        return {
            "status": "no_match",
            "resolution_source": "unspecified",
            "current_machine": current_machine,
            "query": TRACKER_KIND_NONE,
            "warning": "Provide a task slug, tracker reference, or explicit task/session override.",
        }

    tracker_ref = extract_primary_tracker_ref(
        target,
        env=merged_env,
        caller_path=TASK_STATUS_SCRIPTS / "resolve_task_context.py",
    )
    if tracker_ref:
        from task_status_common import find_local_task_homes_for_tracker  # noqa: E402

        matches = _unique_candidates(
            find_local_task_homes_for_tracker(
                tracker_ref,
                current_project_root=resolved_project_root,
                caller_path=TASK_STATUS_SCRIPTS / "resolve_task_context.py",
            )
        )
        if len(matches) == 1:
            return {
                "status": "resolved",
                "resolution_source": "tracker",
                "current_machine": current_machine,
                "query": target,
                "primary": asdict(matches[0]),
            }
        if len(matches) > 1:
            return {
                "status": "ambiguous",
                "resolution_source": "tracker",
                "current_machine": current_machine,
                "query": target,
                "candidates": [asdict(match) for match in matches],
                "warning": "Multiple tracked task homes match this tracker reference.",
            }
        return {
            "status": "no_match",
            "resolution_source": "tracker",
            "current_machine": current_machine,
            "query": target,
            "warning": "No tracked task home matched this tracker reference.",
        }

    matches = find_task_homes_for_slug(target, current_project_root=resolved_project_root)
    if len(matches) == 1:
        return {
            "status": "resolved",
            "resolution_source": "task_slug",
            "current_machine": current_machine,
            "query": target,
            "primary": asdict(matches[0]),
        }
    if len(matches) > 1:
        return {
            "status": "ambiguous",
            "resolution_source": "task_slug",
            "current_machine": current_machine,
            "query": target,
            "candidates": [asdict(match) for match in matches],
            "warning": "Multiple tracked task homes matched this task slug.",
        }
    return {
        "status": "no_match",
        "resolution_source": "task_slug",
        "current_machine": current_machine,
        "query": target,
        "warning": "No tracked task home matched this task slug.",
    }


def list_zellij_sessions() -> dict[str, str]:
    code, stdout, _ = run_local_command(
        ["zellij", "list-sessions", "--reverse", "--no-formatting"],
        timeout_seconds=10,
    )
    if code != 0:
        return {}

    states: dict[str, str] = {}
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("No active zellij sessions found"):
            continue
        session_name = line.split(" [Created", 1)[0].strip()
        if "(current)" in line:
            states[session_name] = "current"
        elif "EXITED" in line:
            states[session_name] = "exited"
        else:
            states[session_name] = "active"
    return states


def query_zellij_tab_names(session_name: str) -> tuple[list[str], str]:
    if not session_name or session_name == TRACKER_KIND_NONE:
        return ([], "")
    code, stdout, stderr = run_local_command(
        ["zellij", "-s", session_name, "action", "query-tab-names"],
        timeout_seconds=10,
    )
    if code != 0:
        return ([], (stderr or stdout).strip())
    tabs = [line.strip() for line in stdout.splitlines() if line.strip()]
    return (tabs, "")


def list_zellij_clients(session_name: str) -> tuple[list[SessionClient], str]:
    if not session_name or session_name == TRACKER_KIND_NONE:
        return ([], "")
    code, stdout, stderr = run_local_command(
        ["zellij", "-s", session_name, "action", "list-clients"],
        timeout_seconds=10,
    )
    if code != 0:
        return ([], (stderr or stdout).strip())
    lines = [line.rstrip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        return ([], "")
    rows = lines[1:] if lines[0].strip() == ZELLIJ_LIST_HEADER else lines
    clients: list[SessionClient] = []
    for row in rows:
        match = re.match(r"^(?P<id>\S+)\s+(?P<pane>\S+)\s+(?P<cmd>.+)$", row)
        if not match:
            continue
        clients.append(
            SessionClient(
                client_id=match.group("id"),
                pane_id=match.group("pane"),
                running_command=match.group("cmd"),
            )
        )
    return (clients, "")


def choose_tab_name(
    tab_names: list[str],
    *,
    explicit_tab_name: str | None,
    tracker_human_id: str,
) -> tuple[str, str]:
    if explicit_tab_name:
        if tab_names and explicit_tab_name not in tab_names:
            return ("", "explicit-tab-missing")
        return (explicit_tab_name, "explicit")

    normalized_tracker = (tracker_human_id or "").strip()
    if normalized_tracker and normalized_tracker != TRACKER_KIND_NONE:
        for candidate in (
            f"[{normalized_tracker}]",
            normalized_tracker,
            f"[{normalized_tracker.upper()}]",
            normalized_tracker.upper(),
        ):
            if candidate in tab_names:
                return (candidate, "tracker-human-id")

    if len(tab_names) == 1:
        return (tab_names[0], "single-tab")
    return ("", "ambiguous-or-missing")


def inspect_session_target(
    session_name: str,
    *,
    tracker_human_id: str,
    explicit_tab_name: str | None = None,
) -> SessionInspection:
    warnings: list[str] = []
    normalized = (session_name or "").strip() or TRACKER_KIND_NONE
    session_states = list_zellij_sessions()
    state = session_states.get(normalized, "unknown")
    tab_names, tab_error = query_zellij_tab_names(normalized)
    if tab_error:
        warnings.append(tab_error)
    clients, client_error = list_zellij_clients(normalized)
    if client_error:
        warnings.append(client_error)
    selected_tab_name, tab_reason = choose_tab_name(
        tab_names,
        explicit_tab_name=explicit_tab_name,
        tracker_human_id=tracker_human_id,
    )
    if not selected_tab_name and explicit_tab_name:
        warnings.append(
            f"Explicit tab `{explicit_tab_name}` was not present in the live session tab list."
        )
    if not selected_tab_name and len(tab_names) > 1:
        warnings.append(
            "Multiple tab names exist for this session; pass --tab-name to avoid guessing."
        )
    return SessionInspection(
        session_name=normalized,
        state=state,
        tab_names=tab_names,
        selected_tab_name=selected_tab_name,
        tab_selection_reason=tab_reason,
        clients=clients,
        warnings=warnings,
    )


def extract_transcript_messages(
    transcript_path: str,
    *,
    agent_session_id: str | None = None,
    limit: int = DEFAULT_TRANSCRIPT_MESSAGE_LIMIT,
    max_chars: int = 400,
) -> list[dict[str, str]]:
    path = Path((transcript_path or "").strip())
    if not path.is_file() or limit <= 0:
        return []

    messages: list[dict[str, str]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        role = ""
        phase = ""
        timestamp = str(event.get("timestamp") or "")
        text_parts: list[str] = []

        if event.get("type") == "response_item":
            payload = event.get("payload") or {}
            if payload.get("type") != "message":
                continue
            role = str(payload.get("role") or "").strip()
            phase = str(payload.get("phase") or "")
            if role not in {"assistant", "user"}:
                continue
            for item in payload.get("content") or []:
                item_type = str(item.get("type") or "")
                if item_type in {"output_text", "input_text"}:
                    text = str(item.get("text") or "").strip()
                    if text:
                        text_parts.append(text)
        elif event.get("type") in {"user", "assistant"}:
            role = str(event.get("type") or "").strip()
            message = event.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    stripped = content.strip()
                    if stripped:
                        text_parts.append(stripped)
                elif isinstance(content, list):
                    for item in content:
                        if not isinstance(item, dict):
                            continue
                        item_type = str(item.get("type") or "")
                        if item_type == "text":
                            text = str(item.get("text") or "").strip()
                            if text:
                                text_parts.append(text)
            elif isinstance(message, str):
                stripped = message.strip()
                if stripped:
                    text_parts.append(stripped)
        elif path.name == "history.jsonl":
            if agent_session_id and str(event.get("sessionId") or "").strip() != agent_session_id:
                continue
            role = "user"
            raw_display = str(event.get("display") or "").strip()
            if raw_display:
                text_parts.append(raw_display)
            raw_timestamp = event.get("timestamp")
            if isinstance(raw_timestamp, (int, float)):
                timestamp = (
                    datetime.fromtimestamp(raw_timestamp / 1000, tz=timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z")
                )

        if role not in {"assistant", "user"} or not text_parts:
            continue

        text = "\n".join(text_parts).strip()
        if len(text) > max_chars:
            text = text[: max_chars - 3].rstrip() + "..."
        messages.append(
            {
                "timestamp": timestamp,
                "role": role,
                "phase": phase,
                "text": text,
            }
        )
    if not messages:
        return []
    return messages[-limit:]


def validate_message_text(text: str) -> str | None:
    if not text:
        return "message text is required"
    if len(text) > MAX_MESSAGE_CHARS:
        return f"message exceeds {MAX_MESSAGE_CHARS} characters"
    if "\r" in text:
        return "carriage return characters are not allowed; use \\n and --submit enter instead"
    if CONTROL_CHAR_RE.search(text):
        return "message contains unsupported control characters"
    return None


def truncate_preview(text: str, *, max_chars: int = 120) -> str:
    stripped = text.replace("\n", "\\n")
    if len(stripped) <= max_chars:
        return stripped
    return stripped[: max_chars - 3] + "..."


def json_dump(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)
