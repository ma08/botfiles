#!/usr/bin/env python3
"""Create a Zotero child note through the Zotero Web API.

Writes require --execute. Dry-run is the default.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def markdown_to_note_html(markdown: str, title: str | None) -> str:
    escaped = html.escape(markdown).replace("\n", "<br/>\n")
    if title:
        return f'<div class="zotero-note znv1"><h2>{html.escape(title)}</h2><p>{escaped}</p></div>'
    return f'<div class="zotero-note znv1"><p>{escaped}</p></div>'


def request_json(url: str, api_key: str, method: str = "GET", payload: object | None = None) -> tuple[int, str]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Zotero-API-Version", "3")
    req.add_header("Zotero-API-Key", api_key)
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"Zotero API error {exc.code}: {body}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-key", default=os.environ.get("ZOTERO_API_KEY"))
    parser.add_argument("--user-id", default=os.environ.get("ZOTERO_USER_ID"))
    parser.add_argument("--group-id", default=os.environ.get("ZOTERO_GROUP_ID"))
    parser.add_argument("--parent", required=True, help="Parent Zotero item key")
    parser.add_argument("--title", default="")
    body = parser.add_mutually_exclusive_group(required=True)
    body.add_argument("--markdown", type=Path)
    body.add_argument("--text")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--execute", action="store_true", help="Actually POST the note")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.execute:
        if not args.api_key:
            raise SystemExit("Set ZOTERO_API_KEY or pass --api-key")
        if bool(args.user_id) == bool(args.group_id):
            raise SystemExit("Set exactly one of ZOTERO_USER_ID or ZOTERO_GROUP_ID")
    elif not args.user_id and not args.group_id:
        args.user_id = "DRY_RUN_USER_ID"
    library = f"users/{args.user_id}" if args.user_id else f"groups/{args.group_id}"
    base = f"https://api.zotero.org/{library}/items"

    text = args.text if args.text is not None else args.markdown.read_text()
    note_html = markdown_to_note_html(text, args.title)
    payload = [
        {
            "itemType": "note",
            "parentItem": args.parent,
            "note": note_html,
            "tags": [{"tag": tag} for tag in args.tag],
        }
    ]
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if not args.execute:
        print("Dry run only. Add --execute to POST this note.", file=sys.stderr)
        return 0
    status, body = request_json(base, args.api_key, method="POST", payload=payload)
    print(f"HTTP {status}")
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
