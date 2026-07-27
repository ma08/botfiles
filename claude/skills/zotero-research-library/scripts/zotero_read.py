#!/usr/bin/env python3
"""Read Zotero local SQLite data without modifying the library."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any


COLOR_LABELS = {
    "#ffd400": "yellow",
    "#ff6666": "red",
    "#5fb236": "green",
    "#2ea8e5": "blue",
    "#a28ae5": "purple",
    "#e56eee": "magenta",
    "#f19837": "orange",
    "#aaaaaa": "gray",
}


def default_db_path() -> Path:
    env = os.environ.get("ZOTERO_DB_PATH")
    if env:
        return Path(env).expanduser()
    return Path.home() / "Zotero" / "zotero.sqlite"


def connect(db_path: Path) -> sqlite3.Connection:
    uri = f"file:{db_path.expanduser()}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def clean_note_html(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.I)
    text = re.sub(r"</h[1-6]\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def field_value(conn: sqlite3.Connection, item_id: int, field_name: str) -> str:
    row = conn.execute(
        """
        SELECT iv.value
        FROM itemData id
        JOIN fieldsCombined f ON f.fieldID = id.fieldID
        JOIN itemDataValues iv ON iv.valueID = id.valueID
        WHERE id.itemID = ? AND f.fieldName = ?
        LIMIT 1
        """,
        (item_id, field_name),
    ).fetchone()
    return row[0] if row else ""


def item_type(conn: sqlite3.Connection, item_id: int) -> str:
    row = conn.execute(
        """
        SELECT it.typeName
        FROM items i JOIN itemTypes it ON it.itemTypeID = i.itemTypeID
        WHERE i.itemID = ?
        """,
        (item_id,),
    ).fetchone()
    return row[0] if row else ""


def creators(conn: sqlite3.Connection, item_id: int) -> list[str]:
    rows = conn.execute(
        """
        SELECT c.firstName, c.lastName, ct.creatorType
        FROM itemCreators ic
        JOIN creators c ON c.creatorID = ic.creatorID
        JOIN creatorTypes ct ON ct.creatorTypeID = ic.creatorTypeID
        WHERE ic.itemID = ?
        ORDER BY ic.orderIndex
        """,
        (item_id,),
    ).fetchall()
    out = []
    for row in rows:
        name = " ".join(part for part in [row["firstName"], row["lastName"]] if part)
        out.append(f"{name} ({row['creatorType']})" if row["creatorType"] else name)
    return out


def item_summary(conn: sqlite3.Connection, item_id: int) -> dict[str, Any]:
    row = conn.execute("SELECT itemID, key, dateAdded, dateModified FROM items WHERE itemID = ?", (item_id,)).fetchone()
    if not row:
        raise SystemExit(f"No Zotero item with itemID {item_id}")
    return {
        "itemID": row["itemID"],
        "key": row["key"],
        "type": item_type(conn, item_id),
        "title": field_value(conn, item_id, "title"),
        "date": field_value(conn, item_id, "date"),
        "DOI": field_value(conn, item_id, "DOI"),
        "url": field_value(conn, item_id, "url"),
        "dateAdded": row["dateAdded"],
        "dateModified": row["dateModified"],
        "creators": creators(conn, item_id),
    }


def resolve_item_id(conn: sqlite3.Connection, item_key: str | None, item_id: int | None) -> int:
    if item_id is not None:
        return item_id
    if not item_key:
        raise SystemExit("Provide --item-key or --item-id")
    row = conn.execute("SELECT itemID FROM items WHERE key = ?", (item_key,)).fetchone()
    if not row:
        raise SystemExit(f"No Zotero item with key {item_key}")
    return int(row["itemID"])


def command_search(args: argparse.Namespace) -> int:
    conn = connect(args.db)
    like = f"%{args.query}%"
    rows = conn.execute(
        """
        SELECT DISTINCT i.itemID
        FROM items i
        LEFT JOIN itemData id ON id.itemID = i.itemID
        LEFT JOIN itemDataValues iv ON iv.valueID = id.valueID
        LEFT JOIN itemNotes n ON n.itemID = i.itemID
        WHERE i.key LIKE ? OR iv.value LIKE ? OR n.note LIKE ?
        ORDER BY i.dateModified DESC
        LIMIT ?
        """,
        (like, like, like, args.limit),
    ).fetchall()
    print(json.dumps([item_summary(conn, int(row["itemID"])) for row in rows], indent=2, ensure_ascii=False))
    return 0


def attachment_rows(conn: sqlite3.Connection, parent_item_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT ia.itemID, i.key, ia.contentType, ia.path, ia.linkMode, ia.lastRead
        FROM itemAttachments ia
        JOIN items i ON i.itemID = ia.itemID
        WHERE ia.parentItemID = ?
        ORDER BY ia.itemID
        """,
        (parent_item_id,),
    ).fetchall()


def attachment_path(row: sqlite3.Row, storage_root: Path) -> str:
    path = row["path"] or ""
    if path.startswith("storage:"):
        return str(storage_root / row["key"] / path.removeprefix("storage:"))
    return path


def command_detail(args: argparse.Namespace) -> int:
    conn = connect(args.db)
    item_id = resolve_item_id(conn, args.item_key, args.item_id)
    data = item_summary(conn, item_id)
    data["attachments"] = [
        {
            "itemID": row["itemID"],
            "key": row["key"],
            "contentType": row["contentType"],
            "path": row["path"],
            "resolvedPath": attachment_path(row, args.storage_root),
        }
        for row in attachment_rows(conn, item_id)
    ]
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def build_digest(conn: sqlite3.Connection, item_id: int, storage_root: Path) -> str:
    summary = item_summary(conn, item_id)
    lines: list[str] = []
    lines.append(f"# Zotero Reading Digest: {summary['title'] or summary['key']}")
    lines.append("")
    lines.append(f"- Item key: {summary['key']}")
    lines.append(f"- Item ID: {summary['itemID']}")
    lines.append(f"- Type: {summary['type']}")
    if summary["creators"]:
        lines.append(f"- Creators: {', '.join(summary['creators'])}")
    for key in ["date", "DOI", "url", "dateAdded", "dateModified"]:
        if summary.get(key):
            lines.append(f"- {key}: {summary[key]}")

    notes = conn.execute(
        """
        SELECT n.itemID, i.key, n.title, n.note
        FROM itemNotes n
        JOIN items i ON i.itemID = n.itemID
        WHERE n.parentItemID = ?
        ORDER BY n.itemID
        """,
        (item_id,),
    ).fetchall()
    lines.extend(["", "## Child Notes", ""])
    if not notes:
        lines.append("_No child notes._")
    for note in notes:
        lines.extend([f"### {note['title'] or note['key']} [{note['itemID']}]", "", clean_note_html(note["note"]) or "_Empty note._", ""])

    attachments = attachment_rows(conn, item_id)
    lines.extend(["", "## Attachments", ""])
    if not attachments:
        lines.append("_No attachments._")
    for row in attachments:
        title = field_value(conn, int(row["itemID"]), "title") or row["path"] or row["key"]
        lines.append(f"- {title} (itemID {row['itemID']}, key {row['key']}, {row['contentType']})")
        resolved = attachment_path(row, storage_root)
        if resolved:
            lines.append(f"  - path: {resolved}")

    attachment_ids = [int(row["itemID"]) for row in attachments]
    if not attachment_ids:
        return "\n".join(lines) + "\n"

    placeholders = ",".join("?" for _ in attachment_ids)
    annotations = conn.execute(
        f"""
        SELECT a.itemID, a.parentItemID, a.type, a.text, a.comment, a.color,
               a.pageLabel, a.sortIndex, a.position
        FROM itemAnnotations a
        WHERE a.parentItemID IN ({placeholders})
        ORDER BY a.parentItemID, a.sortIndex, a.itemID
        """,
        attachment_ids,
    ).fetchall()
    by_color: dict[str, int] = {}
    for ann in annotations:
        label = COLOR_LABELS.get((ann["color"] or "").lower(), ann["color"] or "none")
        by_color[label] = by_color.get(label, 0) + 1

    lines.extend(["", "## Annotation Summary", "", f"- Total annotations: {len(annotations)}"])
    for label, count in sorted(by_color.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- {label}: {count}")

    lines.extend(["", "## Annotations", ""])
    for idx, ann in enumerate(annotations, 1):
        label = COLOR_LABELS.get((ann["color"] or "").lower(), ann["color"] or "none")
        page = ann["pageLabel"] or "?"
        text = clean_note_html(ann["text"]) or "_No selected text captured._"
        comment = clean_note_html(ann["comment"])
        lines.extend([f"### {idx}. {label} p. {page} [annotation {ann['itemID']}]", "", text])
        if comment:
            lines.extend(["", f"Comment: {comment}"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def command_digest(args: argparse.Namespace) -> int:
    conn = connect(args.db)
    item_id = resolve_item_id(conn, args.item_key, args.item_id)
    digest = build_digest(conn, item_id, args.storage_root)
    if args.output:
        args.output.write_text(digest)
    else:
        sys.stdout.write(digest)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=default_db_path())
    parser.add_argument("--storage-root", type=Path, default=Path.home() / "Zotero" / "storage")
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=20)
    search.set_defaults(func=command_search)

    detail = sub.add_parser("detail")
    detail.add_argument("--item-key")
    detail.add_argument("--item-id", type=int)
    detail.set_defaults(func=command_detail)

    digest = sub.add_parser("digest")
    digest.add_argument("--item-key")
    digest.add_argument("--item-id", type=int)
    digest.add_argument("--output", type=Path)
    digest.set_defaults(func=command_digest)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
