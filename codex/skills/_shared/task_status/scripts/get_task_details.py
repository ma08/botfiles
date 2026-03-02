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
    TASK_METADATA_END,
    TASK_METADATA_START,
    extract_marked_block,
    find_task_dirs,
    parse_bullet_metadata,
    read_text,
    resolve_status_file,
    resolve_task_status_root,
    task_age_days,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        default=os.getcwd(),
        help="Project root containing AGENTS.md/CLAUDE.md and task-status root.",
    )
    parser.add_argument("--task-slug", help="Task slug or keyword for folder matching.")
    parser.add_argument(
        "--max-related",
        type=int,
        default=5,
        help="Maximum related/stale entries to display.",
    )
    return parser.parse_args()


def read_metadata(status_file: Path | None) -> dict[str, str]:
    if not status_file:
        return {}
    text = read_text(status_file)
    block = extract_marked_block(
        text,
        start_marker=TASK_METADATA_START,
        end_marker=TASK_METADATA_END,
    )
    return parse_bullet_metadata(block)


def print_entry(label: str, task_dir: Path, status_file: Path | None, metadata: dict[str, str], age_days: int | None) -> None:
    print(f"{label}:")
    print(f"  Task Folder: {task_dir}")
    print(f"  Status File: {status_file if status_file else 'none'}")
    if age_days is not None:
        print(f"  Age (days): {age_days}")
    print(f"  GitHub Issue: {metadata.get('GitHub Issue', 'none')}")
    print(f"  Machine: {metadata.get('Machine', 'none')}")
    print(f"  Coding Agent: {metadata.get('Coding Agent', 'none')}")
    print(f"  Agent Session ID: {metadata.get('Agent Session ID', 'none')}")
    print(f"  Zellij Session: {metadata.get('Zellij Session', 'none')}")
    print(f"  Zellij Link: {metadata.get('Zellij Link', 'none')}")


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    status_root = resolve_task_status_root(project_root, caller_path=Path(__file__))
    today = datetime.now(ZoneInfo("America/Los_Angeles")).date()

    task_dirs = find_task_dirs(status_root, slug=args.task_slug)
    if not task_dirs:
        print("No task folder found for the current context.")
        print("Suggestion: use /start-new-task")
        return 0

    primary = task_dirs[0]
    primary_status = resolve_status_file(primary)
    primary_meta = read_metadata(primary_status)
    print_entry(
        "Primary",
        task_dir=primary,
        status_file=primary_status,
        metadata=primary_meta,
        age_days=task_age_days(primary, today),
    )

    related: list[Path] = []
    stale: list[Path] = []
    for task_dir in task_dirs[1:]:
        age_days = task_age_days(task_dir, today)
        if age_days is not None and age_days > 7:
            stale.append(task_dir)
        else:
            related.append(task_dir)

    if related:
        print("")
        for task_dir in related[: args.max_related]:
            status_file = resolve_status_file(task_dir)
            metadata = read_metadata(status_file)
            print_entry(
                "Related",
                task_dir=task_dir,
                status_file=status_file,
                metadata=metadata,
                age_days=task_age_days(task_dir, today),
            )
            print("")
        if len(related) > args.max_related:
            print(f"... {len(related) - args.max_related} more related entries omitted")

    if stale:
        if related:
            print("")
        for task_dir in stale[: args.max_related]:
            status_file = resolve_status_file(task_dir)
            metadata = read_metadata(status_file)
            print_entry(
                "Stale",
                task_dir=task_dir,
                status_file=status_file,
                metadata=metadata,
                age_days=task_age_days(task_dir, today),
            )
            print("")
        if len(stale) > args.max_related:
            print(f"... {len(stale) - args.max_related} more stale entries omitted")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
