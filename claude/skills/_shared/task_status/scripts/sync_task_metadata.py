#!/usr/bin/env python3
"""Upsert task metadata block and optionally sync GitHub live-session block."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from task_status_common import (  # noqa: E402
    LIVE_SESSION_END,
    LIVE_SESSION_START,
    TASK_METADATA_END,
    TASK_METADATA_START,
    build_attach_command,
    build_live_session_block,
    build_task_metadata_block,
    build_zellij_link,
    extract_marked_block,
    fetch_issue_data,
    gh_authenticated,
    gh_available,
    infer_agent_from_script,
    infer_project_root_from_path,
    merged_env_with_botfiles_defaults,
    now_pst_label,
    parse_bullet_metadata,
    parse_github_issue_url,
    read_text,
    resolve_agent_name,
    resolve_agent_session_id,
    resolve_machine_name,
    resolve_status_file,
    resolve_zellij_session,
    upsert_current_task_pointer,
    update_issue_body,
    upsert_marked_block,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status-file", help="Path to status.md or legacy README.md.")
    parser.add_argument("--task-dir", help="Task folder containing status.md/README.md.")
    parser.add_argument("--github-issue-url", help="Explicit GitHub issue URL override.")
    parser.add_argument("--machine", help="Explicit machine name override.")
    parser.add_argument("--coding-agent", help="Explicit coding-agent name override (e.g. codex, claude).")
    parser.add_argument("--agent-session-id", help="Explicit coding-agent session id override.")
    parser.add_argument("--zellij-session", help="Explicit zellij session override.")
    parser.add_argument("--zellij-link", help="Explicit zellij link override.")
    parser.add_argument(
        "--sync-github-issue",
        action="store_true",
        help="If enabled, upsert managed live-session block into linked issue body.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing changes.")
    return parser.parse_args()


def pick_status_file(args: argparse.Namespace) -> Path:
    if args.status_file:
        return Path(args.status_file).expanduser().resolve()
    if args.task_dir:
        task_dir = Path(args.task_dir).expanduser().resolve()
        status_file = resolve_status_file(task_dir)
        if status_file:
            return status_file
    raise FileNotFoundError("Provide --status-file or --task-dir with an existing status file.")


def log(msg: str) -> None:
    print(msg)


def warn(msg: str) -> None:
    print(f"WARNING: {msg}", file=sys.stderr)


def main() -> int:
    args = parse_args()
    env = merged_env_with_botfiles_defaults(dict(os.environ), caller_path=Path(__file__))

    try:
        status_file = pick_status_file(args)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not status_file.is_file():
        print(f"ERROR: status file does not exist: {status_file}", file=sys.stderr)
        return 2

    original_status = read_text(status_file)
    existing_block = extract_marked_block(
        original_status,
        start_marker=TASK_METADATA_START,
        end_marker=TASK_METADATA_END,
    )
    existing = parse_bullet_metadata(existing_block)

    project_root = infer_project_root_from_path(status_file)
    project_root_str = str(project_root) if project_root else None

    machine = args.machine or resolve_machine_name(env)
    default_agent = infer_agent_from_script(Path(__file__))
    coding_agent = args.coding_agent or resolve_agent_name(env, default_agent=default_agent)
    agent_session_id = args.agent_session_id or resolve_agent_session_id(env, project_root=project_root_str)
    zellij_session = args.zellij_session or resolve_zellij_session(env)
    zellij_link = args.zellij_link or build_zellij_link(zellij_session, env)

    issue_url = args.github_issue_url or existing.get("GitHub Issue", "none")
    if issue_url in {"", "none"}:
        issue_url = "none"

    issue_ref = parse_github_issue_url(issue_url) if issue_url != "none" else None
    issue_repo = issue_ref.repo_key if issue_ref else existing.get("GitHub Repo", "none")
    issue_number = str(issue_ref.number) if issue_ref else existing.get("GitHub Issue Number", "none")

    metadata_block = build_task_metadata_block(
        machine=machine,
        coding_agent=coding_agent,
        agent_session_id=agent_session_id,
        issue_url=issue_url,
        issue_repo=issue_repo or "none",
        issue_number=issue_number or "none",
        zellij_session=zellij_session,
        zellij_link=zellij_link,
        last_synced=now_pst_label(),
    )

    updated_status = upsert_marked_block(
        original_status,
        metadata_block,
        start_marker=TASK_METADATA_START,
        end_marker=TASK_METADATA_END,
        prefer_top=False,
    )

    if args.dry_run:
        log(f"Dry-run: would update task metadata in {status_file}")
    elif updated_status != original_status:
        status_file.write_text(updated_status, encoding="utf-8")
        log(f"Updated task metadata in {status_file}")
    else:
        log(f"No task metadata changes needed in {status_file}")

    if not args.dry_run:
        pointer_updated = upsert_current_task_pointer(
            status_file,
            coding_agent=coding_agent,
            agent_session_id=agent_session_id,
            caller_path=Path(__file__),
        )
        if pointer_updated:
            log(f"Updated current-task pointer for session {agent_session_id}")

    if not args.sync_github_issue:
        return 0

    if not issue_ref:
        warn("No valid GitHub issue URL found; skipping issue-body sync.")
        return 0
    if not gh_available():
        warn("GitHub CLI (gh) not found; skipping issue-body sync.")
        return 0
    if not gh_authenticated():
        warn("GitHub CLI not authenticated; skipping issue-body sync.")
        return 0

    issue_data = fetch_issue_data(issue_ref)
    if not issue_data:
        warn(f"Unable to fetch issue {issue_ref.url}; skipping issue-body sync.")
        return 0

    live_block = build_live_session_block(
        machine=machine,
        coding_agent=coding_agent,
        agent_session_id=agent_session_id,
        zellij_session=zellij_session,
        zellij_link=zellij_link,
        task_dir=str(status_file.parent),
        status_file=str(status_file),
        attach_command=build_attach_command(zellij_session),
        last_updated=now_pst_label(),
        project_root=project_root_str,
    )
    new_issue_body = upsert_marked_block(
        issue_data.body,
        live_block,
        start_marker=LIVE_SESSION_START,
        end_marker=LIVE_SESSION_END,
        prefer_top=True,
    )

    if new_issue_body == issue_data.body:
        log(f"No issue-body changes needed for {issue_ref.url}")
        return 0

    if args.dry_run:
        log(f"Dry-run: would update live-session block in {issue_ref.url}")
        return 0

    ok, message = update_issue_body(issue_ref, new_issue_body)
    if not ok:
        warn(f"Failed to update issue body for {issue_ref.url}: {message}")
        return 0

    log(f"Updated live-session block in {issue_ref.url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
