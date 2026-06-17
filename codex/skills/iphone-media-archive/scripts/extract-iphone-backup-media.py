#!/usr/bin/env python3
"""Extract raw iPhone Media/DCIM files from an unencrypted backup.

Dry-run by default. Add --execute to copy files.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import plistlib
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


APPLE_EPOCH_UNIX_OFFSET = 978_307_200
MEDIA_EXTENSIONS = {
    ".heic",
    ".heif",
    ".hif",
    ".jpg",
    ".jpeg",
    ".png",
    ".mov",
    ".mp4",
    ".dng",
    ".tif",
    ".tiff",
    ".aae",
}


@dataclass
class MediaRow:
    file_id: str
    domain: str
    relative_path: str
    source_path: Path
    byte_size: int
    capture_dt: datetime
    capture_source: str
    target_path: Path | None = None
    status: str = "pending"
    note: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup-root", type=Path, required=True)
    parser.add_argument("--dest-root", type=Path, required=True)
    parser.add_argument("--older-fraction", type=float, default=0.80)
    parser.add_argument("--cutoff-date", help="Inclusive local cutoff date YYYY-MM-DD.")
    parser.add_argument("--execute", action="store_true", help="Copy files. Omit for dry run.")
    parser.add_argument("--limit", type=int, default=0, help="Optional sample item limit.")
    parser.add_argument("--report", type=Path, default=None)
    return parser.parse_args()


def fail(message: str, code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def find_device_dir(backup_root: Path) -> Path:
    if not backup_root.is_dir():
        fail(f"backup root not found: {backup_root}", 3)
    candidates = [path for path in backup_root.iterdir() if (path / "Manifest.db").is_file()]
    if len(candidates) != 1:
        fail(f"expected one backup device directory under {backup_root}, found {len(candidates)}", 4)
    return candidates[0]


def normalize_dt(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value.replace(tzinfo=value.tzinfo or timezone.utc).astimezone(timezone.utc)
    if isinstance(value, (int, float)):
        if value > 100000000000:
            value = value / 1000
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    return None


def apple_coredata_dt(value: object) -> datetime | None:
    if value is None:
        return None
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        return None
    if seconds <= 0:
        return None
    try:
        return datetime.fromtimestamp(seconds + APPLE_EPOCH_UNIX_OFFSET, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def load_file_metadata(blob: bytes | None) -> dict:
    if not blob:
        return {}
    try:
        value = plistlib.loads(blob)
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def is_media_relative_path(relative_path: str) -> bool:
    return Path(relative_path).suffix.lower() in MEDIA_EXTENSIONS and (
        relative_path.startswith("Media/DCIM/") or relative_path.startswith("DCIM/")
    )


def find_photos_sqlite(device_dir: Path) -> Path | None:
    manifest_db = device_dir / "Manifest.db"
    conn = sqlite3.connect(f"file:{manifest_db}?mode=ro&immutable=1", uri=True)
    try:
        row = conn.execute(
            """
            SELECT fileID
            FROM Files
            WHERE domain = 'CameraRollDomain'
              AND relativePath = 'Media/PhotoData/Photos.sqlite'
            LIMIT 1
            """
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    file_id = row[0]
    path = device_dir / file_id[:2] / file_id
    return path if path.is_file() else None


def load_photos_asset_dates(device_dir: Path) -> tuple[dict[str, datetime], dict[str, datetime]]:
    photos_db = find_photos_sqlite(device_dir)
    if photos_db is None:
        return {}, {}
    exact_dates: dict[str, datetime] = {}
    stem_dates: dict[str, datetime] = {}
    conn = sqlite3.connect(f"file:{photos_db}?mode=ro&immutable=1", uri=True)
    try:
        cursor = conn.execute(
            """
            SELECT ZDIRECTORY, ZFILENAME, ZDATECREATED, ZADDEDDATE, ZTRASHEDSTATE
            FROM ZASSET
            WHERE ZDIRECTORY LIKE 'DCIM/%'
              AND ZFILENAME IS NOT NULL
              AND IFNULL(ZTRASHEDSTATE, 0) = 0
            """
        )
        for directory, filename, date_created, date_added, _trashed in cursor:
            dt = apple_coredata_dt(date_created) or apple_coredata_dt(date_added)
            if dt is None:
                continue
            relative_path = f"Media/{directory}/{filename}"
            exact_dates[relative_path] = dt
            stem_dates[f"Media/{directory}/{Path(filename).stem}"] = dt
    finally:
        conn.close()
    return exact_dates, stem_dates


def media_capture_date(
    metadata: dict,
    source_path: Path,
    relative_path: str,
    exact_dates: dict[str, datetime],
    stem_dates: dict[str, datetime],
) -> tuple[datetime, str]:
    exact_dt = exact_dates.get(relative_path)
    if exact_dt is not None:
        return exact_dt, "Photos.sqlite:asset"
    stem_dt = stem_dates.get(f"{Path(relative_path).parent}/{Path(relative_path).stem}")
    if stem_dt is not None:
        return stem_dt, "Photos.sqlite:stem"
    for key in ("Birth", "ModificationTime", "LastModified", "StatusChangeTime"):
        dt = normalize_dt(metadata.get(key))
        if dt is not None:
            return dt, f"manifest:{key}"
    return datetime.fromtimestamp(source_path.stat().st_mtime, tz=timezone.utc), "backup-file-mtime"


def load_media_rows(device_dir: Path) -> list[MediaRow]:
    db_path = device_dir / "Manifest.db"
    exact_dates, stem_dates = load_photos_asset_dates(device_dir)
    rows: list[MediaRow] = []
    conn = sqlite3.connect(f"file:{db_path}?mode=ro&immutable=1", uri=True)
    try:
        cursor = conn.execute(
            """
            SELECT fileID, domain, relativePath, file
            FROM Files
            WHERE relativePath LIKE 'Media/DCIM/%' OR relativePath LIKE 'DCIM/%'
            ORDER BY domain, relativePath, fileID
            """
        )
        for file_id, domain, relative_path, file_blob in cursor:
            if not relative_path or not is_media_relative_path(relative_path):
                continue
            source_path = device_dir / file_id[:2] / file_id
            if not source_path.is_file():
                continue
            metadata = load_file_metadata(file_blob)
            capture_dt, capture_source = media_capture_date(
                metadata, source_path, relative_path, exact_dates, stem_dates
            )
            rows.append(
                MediaRow(
                    file_id=file_id,
                    domain=domain,
                    relative_path=relative_path,
                    source_path=source_path,
                    byte_size=source_path.stat().st_size,
                    capture_dt=capture_dt,
                    capture_source=capture_source,
                )
            )
    finally:
        conn.close()
    rows.sort(key=lambda row: (row.capture_dt, row.relative_path, row.file_id))
    return rows


def apply_selection(rows: list[MediaRow], older_fraction: float, cutoff_date: str | None, limit: int) -> list[MediaRow]:
    if not rows:
        return []
    if cutoff_date:
        cutoff = datetime.strptime(cutoff_date, "%Y-%m-%d").date()
        selected = [row for row in rows if row.capture_dt.astimezone().date() <= cutoff]
    else:
        if not (0 < older_fraction <= 1):
            fail("--older-fraction must be greater than 0 and less than or equal to 1.", 6)
        count = max(1, int(len(rows) * older_fraction))
        cutoff_local_date = rows[count - 1].capture_dt.astimezone().date()
        selected = [row for row in rows if row.capture_dt.astimezone().date() <= cutoff_local_date]
    return selected[:limit] if limit > 0 else selected


def safe_basename(relative_path: str) -> str:
    return Path(relative_path).name.replace("/", "_").replace(":", "_") or "unnamed"


def target_for(row: MediaRow, dest_root: Path) -> Path:
    local_dt = row.capture_dt.astimezone()
    return dest_root / f"{local_dt:%Y}" / f"{local_dt:%Y-%m-%d}" / safe_basename(row.relative_path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unique_target(source_path: Path, requested_target: Path, file_id: str) -> tuple[Path, str]:
    if not requested_target.exists():
        return requested_target, "new"
    if requested_target.is_file() and requested_target.stat().st_size == source_path.stat().st_size:
        if sha256(requested_target) == sha256(source_path):
            return requested_target, "already-present-identical"
    stem, suffix = requested_target.stem, requested_target.suffix
    candidate = requested_target.with_name(f"{stem}__{file_id[:12]}{suffix}")
    index = 2
    while candidate.exists():
        if candidate.is_file() and candidate.stat().st_size == source_path.stat().st_size:
            if sha256(candidate) == sha256(source_path):
                return candidate, "already-present-identical"
        candidate = requested_target.with_name(f"{stem}__{file_id[:12]}-{index}{suffix}")
        index += 1
    return candidate, "renamed-collision"


def write_report(report_path: Path, rows: list[MediaRow]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "status",
                "note",
                "capture_datetime_utc",
                "capture_source",
                "bytes",
                "domain",
                "relative_path",
                "file_id",
                "source_path",
                "target_path",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.status,
                    row.note,
                    row.capture_dt.astimezone(timezone.utc).isoformat(),
                    row.capture_source,
                    row.byte_size,
                    row.domain,
                    row.relative_path,
                    row.file_id,
                    str(row.source_path),
                    str(row.target_path or ""),
                ]
            )


def summarize(rows: list[MediaRow], total_rows: int, execute: bool, report_path: Path) -> None:
    total_bytes = sum(row.byte_size for row in rows)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.capture_source] = counts.get(row.capture_source, 0) + 1
    print(f"mode: {'execute' if execute else 'dry-run'}")
    print(f"total_media_candidates: {total_rows}")
    print(f"selected_rows: {len(rows)}")
    print(f"selected_size_bytes: {total_bytes}")
    print(f"selected_size_gib: {total_bytes / (1024 ** 3):.2f}")
    if rows:
        print(f"oldest_selected_utc: {rows[0].capture_dt.astimezone(timezone.utc).isoformat()}")
        print(f"newest_selected_utc: {rows[-1].capture_dt.astimezone(timezone.utc).isoformat()}")
    print("selected_capture_sources:")
    for source, count in sorted(counts.items()):
        print(f"  {source}: {count}")
    print(f"report: {report_path}")


def main() -> int:
    args = parse_args()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = args.report or Path(f"extract-iphone-backup-media-{stamp}.tsv")
    device_dir = find_device_dir(args.backup_root)
    rows = load_media_rows(device_dir)
    selected = apply_selection(rows, args.older_fraction, args.cutoff_date, args.limit)

    for row in selected:
        requested_target = target_for(row, args.dest_root)
        if not args.execute:
            row.target_path = requested_target
            row.status = "dry-run"
            row.note = "exists" if requested_target.exists() else "new"
            continue
        final_target, target_status = unique_target(row.source_path, requested_target, row.file_id)
        row.target_path = final_target
        if target_status == "already-present-identical":
            row.status = "skipped"
            row.note = target_status
            continue
        final_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(row.source_path, final_target)
        row.status = "copied"
        row.note = target_status

    write_report(report_path, selected)
    summarize(selected, len(rows), args.execute, report_path)
    if not args.execute:
        print("No files were copied. Re-run with --execute after reviewing the report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
