#!/usr/bin/env python3
"""Resolve issue/machine/session context from a task description."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from task_status_common import (  # noqa: E402
    build_issue_slug,
    build_zellij_link,
    enforce_slug_length,
    extract_primary_issue_ref,
    extract_urls,
    fetch_issue_data,
    fetch_page_title,
    infer_agent_from_script,
    merged_env_with_botfiles_defaults,
    non_issue_urls,
    resolve_agent_name,
    resolve_agent_session_id,
    resolve_machine_name,
    resolve_zellij_session,
    slugify,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--description",
        required=True,
        help="Raw task description text (can include issue URLs and other links).",
    )
    parser.add_argument(
        "--max-slug-length",
        type=int,
        default=60,
        help="Maximum generated slug length before hash suffix truncation.",
    )
    parser.add_argument(
        "--skip-link-titles",
        action="store_true",
        help="Skip best-effort page title extraction for non-GitHub URLs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env = merged_env_with_botfiles_defaults(dict(os.environ), caller_path=Path(__file__))

    machine = resolve_machine_name(env)
    default_agent = infer_agent_from_script(Path(__file__))
    coding_agent = resolve_agent_name(env, default_agent=default_agent)
    agent_session_id = resolve_agent_session_id(env)
    zellij_session = resolve_zellij_session(env)
    zellij_link = build_zellij_link(zellij_session, env)

    issue_ref = extract_primary_issue_ref(args.description)
    issue_title = "none"
    issue_state = "none"
    issue_slug = "none"

    if issue_ref:
        issue_data = fetch_issue_data(issue_ref)
        if issue_data and issue_data.title:
            issue_title = issue_data.title
        else:
            issue_title = "issue"
        if issue_data and issue_data.state:
            issue_state = issue_data.state
        issue_slug = build_issue_slug(
            issue_ref.repo,
            issue_ref.number,
            issue_title,
            max_length=args.max_slug_length,
        )
    else:
        issue_slug = enforce_slug_length(slugify(args.description), args.max_slug_length)

    print(f"Task Slug: {issue_slug}")
    print(f"Machine: {machine}")
    print(f"Coding Agent: {coding_agent}")
    print(f"Agent Session ID: {agent_session_id}")
    print(f"Zellij Session: {zellij_session}")
    print(f"Zellij Link: {zellij_link}")

    if issue_ref:
        print(f"GitHub Issue: {issue_ref.url}")
        print(f"GitHub Repo: {issue_ref.repo_key}")
        print(f"GitHub Issue Number: {issue_ref.number}")
        print(f"GitHub Issue Title: {issue_title}")
        print(f"GitHub Issue State: {issue_state}")
    else:
        print("GitHub Issue: none")

    if args.skip_link_titles:
        return 0

    urls = extract_urls(args.description)
    context_urls = non_issue_urls(urls, issue_ref)
    if not context_urls:
        return 0

    print("Context Links:")
    for url in context_urls:
        title = fetch_page_title(url) or "title unavailable"
        print(f"- {url} -> {title}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
