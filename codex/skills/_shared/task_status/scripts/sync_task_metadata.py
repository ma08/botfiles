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
    TRACKER_KIND_GITHUB,
    TRACKER_KIND_LINEAR,
    TRACKER_KIND_NONE,
    TRACKER_REMOTE_SESSION_MARKER,
    LIVE_SESSION_END,
    LIVE_SESSION_START,
    TASK_METADATA_END,
    TASK_METADATA_START,
    build_attach_command,
    build_live_session_block,
    build_task_metadata_block,
    build_zellij_link,
    extract_marked_block,
    fetch_linear_issue_data,
    fetch_issue_data,
    gh_authenticated,
    gh_available,
    infer_agent_from_script,
    infer_project_root_from_path,
    merged_env_with_botfiles_defaults,
    normalize_task_metadata,
    now_pst_label,
    parse_bullet_metadata,
    parse_github_issue_url,
    parse_tracker_url,
    read_text,
    resolve_agent_name,
    resolve_agent_session_id,
    resolve_machine_name,
    resolve_transcript_path,
    resolve_tracker_title,
    resolve_status_file,
    resolve_zellij_session,
    upsert_current_task_pointer,
    update_issue_body,
    update_linear_issue_body,
    upsert_marked_block,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status-file", help="Path to status.md or legacy README.md.")
    parser.add_argument("--task-dir", help="Task folder containing status.md/README.md.")
    parser.add_argument(
        "--tracker-url",
        help="Primary tracker URL override (Linear takes precedence when both Linear and GitHub exist).",
    )
    parser.add_argument(
        "--tracker-kind",
        help="Explicit primary tracker kind override (for example linear or github).",
    )
    parser.add_argument(
        "--tracker-human-id",
        help="Explicit primary tracker human ID override (for example ZON-8 or owner/repo#123).",
    )
    parser.add_argument("--tracker-title", help="Explicit primary tracker title override.")
    parser.add_argument("--github-issue-url", help="Explicit GitHub issue URL override.")
    parser.add_argument("--workspace-path", help="Explicit workspace/project root path override.")
    parser.add_argument("--machine", help="Explicit machine name override.")
    parser.add_argument("--coding-agent", help="Explicit coding-agent name override (e.g. codex, claude).")
    parser.add_argument("--agent-session-id", help="Explicit coding-agent session id override.")
    parser.add_argument("--zellij-session", help="Explicit zellij session override.")
    parser.add_argument("--zellij-link", help="Explicit zellij link override.")
    parser.add_argument(
        "--remote-session-anchor-kind",
        help="Explicit remote-session anchor kind override (for example linear_issue_body).",
    )
    parser.add_argument(
        "--remote-session-anchor-id",
        help="Explicit remote-session anchor identifier override.",
    )
    parser.add_argument("--linear-issue-id", help="Explicit Linear issue UUID override.")
    parser.add_argument("--linear-issue-identifier", help="Explicit Linear issue identifier override (for example ZON-8).")
    parser.add_argument("--linear-team-id", help="Explicit Linear team UUID override.")
    parser.add_argument("--linear-team-name", help="Explicit Linear team name override.")
    parser.add_argument("--linear-project-id", help="Explicit Linear project UUID override.")
    parser.add_argument("--linear-project-name", help="Explicit Linear project name override.")
    parser.add_argument(
        "--sync-github-issue",
        action="store_true",
        help="If enabled, upsert the managed live-session block into the primary tracker body (GitHub name retained for compatibility).",
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


def pick_value(*values: str | None) -> str:
    for value in values:
        resolved = str(value or "").strip()
        if resolved and resolved.lower() != TRACKER_KIND_NONE:
            return resolved
    return TRACKER_KIND_NONE


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
    normalized_existing = normalize_task_metadata(existing, status_file=status_file)

    machine = args.machine or resolve_machine_name(env)
    default_agent = infer_agent_from_script(Path(__file__))
    coding_agent = args.coding_agent or resolve_agent_name(env, default_agent=default_agent)
    agent_session_id = args.agent_session_id or resolve_agent_session_id(env)
    zellij_session = args.zellij_session or resolve_zellij_session(env)
    zellij_link = args.zellij_link or build_zellij_link(zellij_session, env)
    project_root = infer_project_root_from_path(status_file)
    project_root_str = str(project_root) if project_root else TRACKER_KIND_NONE
    task_folder = str(status_file.parent.resolve())
    task_status_path = str(status_file.resolve())
    transcript_path = resolve_transcript_path(
        coding_agent,
        agent_session_id,
        project_root=project_root_str if project_root else None,
    )

    tracker_url = pick_value(
        args.tracker_url,
        normalized_existing.get("tracker_url"),
        args.github_issue_url,
        normalized_existing.get("github_issue"),
    )
    tracker_ref = parse_tracker_url(tracker_url) if tracker_url != TRACKER_KIND_NONE else None
    if tracker_ref:
        tracker_url = tracker_ref.url

    tracker_kind = pick_value(
        args.tracker_kind,
        tracker_ref.kind if tracker_ref else None,
        normalized_existing.get("tracker_kind"),
        TRACKER_KIND_GITHUB if args.github_issue_url else None,
    ).lower()
    if tracker_kind not in {TRACKER_KIND_GITHUB, TRACKER_KIND_LINEAR}:
        tracker_kind = TRACKER_KIND_NONE

    tracker_human_id = pick_value(
        args.tracker_human_id,
        tracker_ref.human_id if tracker_ref else None,
        normalized_existing.get("tracker_human_id"),
    )
    tracker_title = pick_value(
        args.tracker_title,
        normalized_existing.get("tracker_title"),
        resolve_tracker_title(tracker_ref) if tracker_ref else None,
    )

    workspace_path = pick_value(
        args.workspace_path,
        normalized_existing.get("workspace_path"),
        project_root_str if project_root else None,
    )
    issue_url = pick_value(
        args.github_issue_url,
        normalized_existing.get("github_issue"),
        tracker_ref.url if tracker_kind == TRACKER_KIND_GITHUB and tracker_ref else None,
    )
    issue_ref = parse_github_issue_url(issue_url) if issue_url != TRACKER_KIND_NONE else None
    issue_repo = pick_value(
        issue_ref.repo_key if issue_ref else None,
        normalized_existing.get("github_repo"),
    )
    issue_number = pick_value(
        str(issue_ref.number) if issue_ref else None,
        normalized_existing.get("github_issue_number"),
    )

    linear_ref = tracker_ref.linear_issue if tracker_ref and tracker_ref.kind == TRACKER_KIND_LINEAR else None
    linear_issue_data = fetch_linear_issue_data(linear_ref, env=env, caller_path=Path(__file__)) if linear_ref else None
    linear_issue_id = pick_value(
        args.linear_issue_id,
        linear_issue_data.id if linear_issue_data else None,
        normalized_existing.get("linear_issue_id"),
    )
    linear_issue_identifier = pick_value(
        args.linear_issue_identifier,
        linear_issue_data.identifier if linear_issue_data else None,
        normalized_existing.get("linear_issue_identifier"),
        linear_ref.identifier if linear_ref else None,
    )
    linear_team_id = pick_value(
        args.linear_team_id,
        linear_issue_data.team_id if linear_issue_data else None,
        normalized_existing.get("linear_team_id"),
    )
    linear_team_name = pick_value(
        args.linear_team_name,
        linear_issue_data.team_name if linear_issue_data else None,
        normalized_existing.get("linear_team_name"),
    )
    linear_project_id = pick_value(
        args.linear_project_id,
        linear_issue_data.project_id if linear_issue_data else None,
        normalized_existing.get("linear_project_id"),
    )
    linear_project_name = pick_value(
        args.linear_project_name,
        linear_issue_data.project_name if linear_issue_data else None,
        normalized_existing.get("linear_project_name"),
    )
    if linear_issue_data and not args.tracker_title and linear_issue_data.title:
        tracker_title = linear_issue_data.title

    remote_session_anchor_kind = pick_value(
        args.remote_session_anchor_kind,
        normalized_existing.get("remote_session_anchor_kind"),
    )
    if remote_session_anchor_kind == TRACKER_KIND_NONE:
        if tracker_kind == TRACKER_KIND_LINEAR and tracker_url != TRACKER_KIND_NONE:
            remote_session_anchor_kind = "linear_issue_body"
        elif issue_ref:
            remote_session_anchor_kind = "github_issue_body"

    remote_session_anchor_id = pick_value(
        args.remote_session_anchor_id,
        normalized_existing.get("remote_session_anchor_id"),
        TRACKER_REMOTE_SESSION_MARKER if remote_session_anchor_kind != TRACKER_KIND_NONE else None,
    )

    metadata_block = build_task_metadata_block(
        tracker_kind=tracker_kind,
        tracker_url=tracker_url,
        tracker_human_id=tracker_human_id,
        tracker_title=tracker_title,
        machine=machine,
        coding_agent=coding_agent,
        agent_session_id=agent_session_id,
        task_folder=task_folder,
        task_status_path=task_status_path,
        transcript_path=transcript_path,
        last_synced_at=now_pst_label(),
        workspace_path=workspace_path,
        zellij_session=zellij_session,
        zellij_link=zellij_link,
        remote_session_anchor_kind=remote_session_anchor_kind,
        remote_session_anchor_id=remote_session_anchor_id,
        github_issue=issue_url,
        github_repo=issue_repo,
        github_issue_number=issue_number,
        linear_issue_id=linear_issue_id,
        linear_issue_identifier=linear_issue_identifier,
        linear_team_id=linear_team_id,
        linear_team_name=linear_team_name,
        linear_project_id=linear_project_id,
        linear_project_name=linear_project_name,
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
            workspace_path=workspace_path,
            caller_path=Path(__file__),
        )
        if pointer_updated:
            log(f"Updated current-task pointer for session {agent_session_id}")

    if not args.sync_github_issue:
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
        project_root=workspace_path if workspace_path != TRACKER_KIND_NONE else None,
        include_authorship_byline=tracker_kind == TRACKER_KIND_GITHUB,
    )

    if tracker_kind == TRACKER_KIND_LINEAR and linear_ref:
        issue_data = linear_issue_data or fetch_linear_issue_data(
            linear_ref,
            env=env,
            caller_path=Path(__file__),
        )
        if not issue_data:
            warn(f"Unable to fetch Linear issue {linear_ref.url}; skipping issue-body sync.")
            return 0

        new_issue_body = upsert_marked_block(
            issue_data.description,
            live_block,
            start_marker=LIVE_SESSION_START,
            end_marker=LIVE_SESSION_END,
            prefer_top=True,
            include_surrounding_rules=True,
        )
        if new_issue_body == issue_data.description:
            log(f"No issue-body changes needed for {linear_ref.url}")
            return 0
        if args.dry_run:
            log(f"Dry-run: would update live-session block in {linear_ref.url}")
            return 0

        ok, message = update_linear_issue_body(
            issue_data.id,
            new_issue_body,
            env=env,
            caller_path=Path(__file__),
        )
        if not ok:
            warn(f"Failed to update issue body for {linear_ref.url}: {message}")
            return 0

        log(f"Updated live-session block in {linear_ref.url}")
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

    new_issue_body = upsert_marked_block(
        issue_data.body,
        live_block,
        start_marker=LIVE_SESSION_START,
        end_marker=LIVE_SESSION_END,
        prefer_top=True,
        include_surrounding_rules=True,
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
