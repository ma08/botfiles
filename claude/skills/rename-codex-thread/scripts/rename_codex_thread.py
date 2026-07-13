#!/usr/bin/env python3
"""Rename Codex app thread labels in the local Codex SQLite state."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def natural_state_key(path: Path) -> tuple[int, str]:
    stem = path.stem
    suffix = stem.removeprefix("state_")
    try:
        return int(suffix), path.name
    except ValueError:
        return -1, path.name


def default_db(codex_home: Path) -> Path:
    preferred = codex_home / "state_5.sqlite"
    if preferred.exists():
        return preferred
    candidates = sorted(codex_home.glob("state_*.sqlite"), key=natural_state_key)
    if candidates:
        return candidates[-1]
    return preferred


def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise SystemExit(f"Codex state database not found: {db_path}")
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"pragma table_info({table})")}


def ensure_threads_table(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "select name from sqlite_master where type='table' and name='threads'"
    ).fetchone()
    if row is None:
        raise SystemExit("Codex state database has no threads table.")


def recent_threads(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            select id, title, preview, first_user_message, updated_at, updated_at_ms
            from threads
            where coalesce(archived, 0) = 0
            order by coalesce(updated_at_ms, updated_at * 1000, 0) desc
            limit ?
            """,
            (limit,),
        )
    )


def choose_thread(conn: sqlite3.Connection, args: argparse.Namespace) -> sqlite3.Row:
    if args.thread_id:
        row = conn.execute(
            """
            select id, title, preview, first_user_message, updated_at, updated_at_ms
            from threads
            where id = ?
            """,
            (args.thread_id,),
        ).fetchone()
        if row is None:
            raise SystemExit(f"No Codex thread found with id: {args.thread_id}")
        return row

    if args.current:
        rows = recent_threads(conn, 1)
        if not rows:
            raise SystemExit("No unarchived Codex threads found.")
        return rows[0]

    raise SystemExit("Pass --thread-id <id>, --current, or --list.")


def make_backup(conn: sqlite3.Connection, db_path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = db_path.with_name(f"{db_path.name}.bak.rename-thread-{stamp}")
    with sqlite3.connect(backup_path) as dst:
        conn.backup(dst)
    return backup_path


def append_session_index(codex_home: Path, thread_id: str, title: str) -> None:
    index_path = codex_home / "session_index.jsonl"
    if not index_path.exists():
        return
    record = {
        "id": thread_id,
        "thread_name": title,
        "updated_at": iso_now(),
    }
    with index_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def update_thread(
    conn: sqlite3.Connection,
    thread_id: str,
    title: str,
    update_first_message: bool,
    touch_updated_at: bool,
) -> None:
    available = columns(conn, "threads")

    values: dict[str, object] = {"title": title}
    if "preview" in available:
        values["preview"] = title
    if update_first_message and "first_user_message" in available:
        values["first_user_message"] = title
    if touch_updated_at:
        now_seconds = int(time.time())
        now_ms = int(time.time() * 1000)
        if "updated_at" in available:
            values["updated_at"] = now_seconds
        if "updated_at_ms" in available:
            values["updated_at_ms"] = now_ms

    assignments = ", ".join(f"{key} = ?" for key in values)
    params = list(values.values()) + [thread_id]
    conn.execute(f"update threads set {assignments} where id = ?", params)
    conn.commit()


def print_row(row: sqlite3.Row) -> None:
    print(f"{row['id']}\t{row['title']}\t{row['preview'] or ''}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rename a Codex app thread title in local Codex state."
    )
    parser.add_argument("--title", help="New human-readable thread title.")
    parser.add_argument("--thread-id", help="Codex thread id to rename.")
    parser.add_argument(
        "--current",
        action="store_true",
        help="Rename the most recently updated unarchived thread.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List recent unarchived threads and exit.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=12,
        help="Number of threads to show with --list.",
    )
    parser.add_argument(
        "--codex-home",
        default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")),
        help="Codex home directory.",
    )
    parser.add_argument("--db", help="Explicit Codex SQLite state database path.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the target thread without writing.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a SQLite backup before writing.",
    )
    parser.add_argument(
        "--no-session-index",
        action="store_true",
        help="Do not append a matching session_index.jsonl entry.",
    )
    parser.add_argument(
        "--update-first-message",
        action="store_true",
        help="Also overwrite first_user_message. Usually leave this off.",
    )
    parser.add_argument(
        "--touch-updated-at",
        action="store_true",
        help="Also refresh thread activity timestamps. Off by default.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    codex_home = Path(args.codex_home).expanduser()
    db_path = Path(args.db).expanduser() if args.db else default_db(codex_home)

    with connect(db_path) as conn:
        ensure_threads_table(conn)

        if args.list:
            for row in recent_threads(conn, args.limit):
                print_row(row)
            return 0

        if not args.title:
            raise SystemExit("--title is required unless --list is used.")

        target = choose_thread(conn, args)
        print("Target thread:")
        print_row(target)
        print(f"New title:\t{args.title}")

        if args.dry_run:
            print("Dry run: no changes written.")
            return 0

        backup_path = None
        if not args.no_backup:
            backup_path = make_backup(conn, db_path)

        update_thread(
            conn,
            target["id"],
            args.title,
            args.update_first_message,
            args.touch_updated_at,
        )

        if not args.no_session_index:
            append_session_index(codex_home, target["id"], args.title)

    if backup_path:
        print(f"Backup:\t{backup_path}")
    print("Updated Codex thread title.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
