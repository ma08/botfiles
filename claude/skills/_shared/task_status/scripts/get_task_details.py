#!/usr/bin/env python3
"""Resolve task status file and rich task metadata for current context."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from task_status_common import (  # noqa: E402
    TaskCandidate,
    RuntimeTaskContext,
    build_runtime_task_recap,
    infer_project_root_from_path,
    load_task_candidates,
    normalize_task_metadata,
    read_task_metadata,
    resolve_current_task_pointer,
    resolve_transcript_path,
    resolve_status_file,
    resolve_runtime_task_context,
    resolve_task_status_root,
    session_matching_candidates,
    sort_task_candidates_by_recency,
    task_age_days,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        default=os.getcwd(),
        help="Project root containing AGENTS.md/CLAUDE.md and task-status root.",
    )
    parser.add_argument("--status-file", help="Explicit status.md or legacy README.md to inspect.")
    parser.add_argument("--task-dir", help="Explicit task directory to inspect.")
    parser.add_argument("--task-slug", help="Task slug or keyword for folder matching.")
    parser.add_argument(
        "--max-related",
        type=int,
        default=5,
        help="Maximum related/stale entries to display.",
    )
    return parser.parse_args()


def print_entry(
    label: str,
    candidate: TaskCandidate,
    age_days: int | None,
    *,
    include_recap: bool = False,
    recap_project_root: Path | None = None,
) -> None:
    metadata = normalize_task_metadata(
        candidate.metadata,
        status_file=candidate.status_file,
        hydrate_transcript_path=True,
    )
    print(f"{label}:")
    print(f"  Task Folder: {candidate.task_dir}")
    print(f"  Status File: {candidate.status_file if candidate.status_file else 'none'}")
    if age_days is not None:
        print(f"  Age (days): {age_days}")
    print(f"  Tracker Kind: {metadata.get('tracker_kind', 'none')}")
    print(f"  Tracker URL: {metadata.get('tracker_url', 'none')}")
    print(f"  Tracker Human ID: {metadata.get('tracker_human_id', 'none')}")
    print(f"  Tracker Title: {metadata.get('tracker_title', 'none')}")
    print(f"  Workspace Path: {metadata.get('workspace_path', 'none')}")
    if metadata.get("github_issue", "none") != "none":
        print(f"  GitHub Issue: {metadata.get('github_issue', 'none')}")
    if metadata.get("linear_issue_identifier", "none") != "none":
        print(f"  Linear Issue Identifier: {metadata.get('linear_issue_identifier', 'none')}")
    if metadata.get("linear_team_name", "none") != "none":
        print(f"  Linear Team: {metadata.get('linear_team_name', 'none')}")
    if metadata.get("linear_project_name", "none") != "none":
        print(f"  Linear Project: {metadata.get('linear_project_name', 'none')}")
    print(f"  Remote Session Anchor Kind: {metadata.get('remote_session_anchor_kind', 'none')}")
    print(f"  Remote Session Anchor ID: {metadata.get('remote_session_anchor_id', 'none')}")
    print(f"  Machine: {metadata.get('machine', 'none')}")
    print(f"  Coding Agent: {metadata.get('coding_agent', 'none')}")
    print(f"  Agent Session ID: {metadata.get('agent_session_id', 'none')}")
    print(f"  Transcript Path: {metadata.get('transcript_path', 'none')}")
    print(f"  Zellij Session: {metadata.get('zellij_session', 'none')}")
    print(f"  Zellij Link: {metadata.get('zellij_link', 'none')}")
    if include_recap:
        print("  Recap:")
        for line in build_runtime_task_recap(
            candidate.status_file,
            metadata=metadata,
            project_root=recap_project_root,
            caller_path=Path(__file__),
        ):
            print(f"    - {line}")


def print_runtime_context(context: RuntimeTaskContext) -> None:
    print("Current Session:")
    print(f"  Machine: {context.machine}")
    print(f"  Coding Agent: {context.coding_agent}")
    print(f"  Agent Session ID: {context.agent_session_id}")
    print(f"  Zellij Session: {context.zellij_session}")
    print(f"  Zellij Link: {context.zellij_link}")


def split_related_and_stale(
    candidates: list[TaskCandidate],
    today,
) -> tuple[list[TaskCandidate], list[TaskCandidate]]:
    related: list[TaskCandidate] = []
    stale: list[TaskCandidate] = []
    for candidate in candidates:
        age_days = task_age_days(candidate.task_dir, today)
        if age_days is not None and age_days > 7:
            stale.append(candidate)
        else:
            related.append(candidate)
    return related, stale


def print_candidate_group(
    label: str,
    candidates: list[TaskCandidate],
    today,
    max_entries: int,
    project_root: Path,
) -> None:
    if not candidates:
        return
    for candidate in candidates[:max_entries]:
        print_entry(
            label,
            candidate=candidate,
            age_days=task_age_days(candidate.task_dir, today),
            recap_project_root=project_root,
        )
        print("")
    if len(candidates) > max_entries:
        print(f"... {len(candidates) - max_entries} more {label.lower()} entries omitted")


def print_no_session_match(context: RuntimeTaskContext) -> int:
    print("No current task found for this session.")
    print("")
    print_runtime_context(context)
    print("")
    print("Suggestion: use save-task-status on the active task, or start-new-task if this session does not have one yet.")
    return 0


def find_pointer_candidate(
    candidates: list[TaskCandidate],
    *,
    task_dir: Path | None,
    status_file: Path | None,
) -> TaskCandidate | None:
    resolved_task_dir = task_dir.resolve() if task_dir else None
    resolved_status_file = status_file.resolve() if status_file else None
    for candidate in candidates:
        if resolved_status_file and candidate.status_file and candidate.status_file.resolve() == resolved_status_file:
            return candidate
        if resolved_task_dir and candidate.task_dir.resolve() == resolved_task_dir:
            return candidate
    return None


def build_pointer_candidate(pointer) -> TaskCandidate | None:
    if not pointer:
        return None
    if not pointer.task_dir.is_dir() or not pointer.status_file.is_file():
        return None
    return TaskCandidate(
        task_dir=pointer.task_dir,
        status_file=pointer.status_file,
        metadata=read_task_metadata(pointer.status_file),
    )


def resolve_direct_candidate(args: argparse.Namespace) -> TaskCandidate | None:
    if not args.status_file and not args.task_dir:
        return None

    if args.status_file:
        status_file = Path(args.status_file).expanduser().resolve()
        if not status_file.is_file():
            raise FileNotFoundError(f"status file does not exist: {status_file}")
        task_dir = status_file.parent
    else:
        task_dir = Path(args.task_dir).expanduser().resolve()
        if not task_dir.is_dir():
            raise FileNotFoundError(f"task directory does not exist: {task_dir}")
        status_file = resolve_status_file(task_dir)

    return TaskCandidate(
        task_dir=task_dir,
        status_file=status_file,
        metadata=read_task_metadata(status_file),
    )


def handle_current_session_lookup(
    *,
    project_root: Path,
    candidates: list[TaskCandidate],
    context: RuntimeTaskContext,
    today,
) -> int:
    pointer = resolve_current_task_pointer(
        project_root,
        coding_agent=context.coding_agent,
        agent_session_id=context.agent_session_id,
        caller_path=Path(__file__),
    )
    pointer_candidate = find_pointer_candidate(
        candidates,
        task_dir=pointer.task_dir if pointer else None,
        status_file=pointer.status_file if pointer else None,
    )
    if pointer_candidate:
        print_entry(
            "Primary",
            candidate=pointer_candidate,
            age_days=task_age_days(pointer_candidate.task_dir, today),
            include_recap=True,
            recap_project_root=project_root,
        )
        return 0

    direct_pointer_candidate = build_pointer_candidate(pointer)
    if direct_pointer_candidate:
        print("Note: current-task pointer resolves outside this repo's local task-status root.")
        print("")
        print_entry(
            "Primary",
            candidate=direct_pointer_candidate,
            age_days=task_age_days(direct_pointer_candidate.task_dir, today),
            include_recap=True,
            recap_project_root=project_root,
        )
        return 0

    matches = sort_task_candidates_by_recency(
        session_matching_candidates(candidates, context.agent_session_id)
    )
    if matches:
        if pointer is None:
            print("Note: current-task pointer not found; falling back to latest same-session task.")
        else:
            print("Note: current-task pointer is stale; falling back to latest same-session task.")
        print("")
        print_entry(
            "Primary",
            candidate=matches[0],
            age_days=task_age_days(matches[0].task_dir, today),
            include_recap=True,
            recap_project_root=project_root,
        )
        return 0

    return print_no_session_match(context)


def handle_slug_lookup(
    *,
    project_root: Path,
    candidates: list[TaskCandidate],
    context: RuntimeTaskContext,
    today,
    max_entries: int,
    task_slug: str,
) -> int:
    if not candidates:
        print(f"No task folder found matching task slug: {task_slug}")
        print("Suggestion: use start-new-task or choose a narrower task slug.")
        return 0

    sorted_candidates = sort_task_candidates_by_recency(candidates)
    pointer = resolve_current_task_pointer(
        project_root,
        coding_agent=context.coding_agent,
        agent_session_id=context.agent_session_id,
        caller_path=Path(__file__),
    )
    primary = find_pointer_candidate(
        sorted_candidates,
        task_dir=pointer.task_dir if pointer else None,
        status_file=pointer.status_file if pointer else None,
    )

    if primary is None:
        session_matches = sort_task_candidates_by_recency(
            session_matching_candidates(sorted_candidates, context.agent_session_id)
        )
        if session_matches:
            primary = session_matches[0]
        else:
            primary = sorted_candidates[0]

    remainder = [
        candidate
        for candidate in sorted_candidates
        if candidate.task_dir.resolve() != primary.task_dir.resolve()
    ]

    print_entry(
        "Primary",
        candidate=primary,
        age_days=task_age_days(primary.task_dir, today),
        include_recap=True,
        recap_project_root=project_root,
    )

    related, stale = split_related_and_stale(remainder, today)
    if related:
        print("")
        print_candidate_group("Related", related, today, max_entries, project_root)
    if stale:
        if related:
            print("")
        print_candidate_group("Stale", stale, today, max_entries, project_root)
    return 0


def main() -> int:
    args = parse_args()
    try:
        direct_candidate = resolve_direct_candidate(args)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if direct_candidate:
        today = datetime.now(ZoneInfo("America/Los_Angeles")).date()
        direct_project_root = infer_project_root_from_path(direct_candidate.status_file) or direct_candidate.task_dir
        print_entry(
            "Primary",
            candidate=direct_candidate,
            age_days=task_age_days(direct_candidate.task_dir, today),
            include_recap=True,
            recap_project_root=direct_project_root,
        )
        return 0

    project_root = Path(args.project_root).expanduser().resolve()
    status_root = resolve_task_status_root(project_root, caller_path=Path(__file__))
    today = datetime.now(ZoneInfo("America/Los_Angeles")).date()
    context = resolve_runtime_task_context(caller_path=Path(__file__))
    candidates = load_task_candidates(status_root, slug=args.task_slug)
    current_project_root = infer_project_root_from_path(project_root) or project_root

    if args.task_slug:
        return handle_slug_lookup(
            project_root=current_project_root,
            candidates=candidates,
            context=context,
            today=today,
            max_entries=args.max_related,
            task_slug=args.task_slug,
        )

    return handle_current_session_lookup(
        project_root=current_project_root,
        candidates=candidates,
        context=context,
        today=today,
    )


if __name__ == "__main__":
    raise SystemExit(main())
