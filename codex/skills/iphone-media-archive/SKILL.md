---
name: iphone-media-archive
description: Backup-first iPhone photo/video archiving to an external drive. Use when creating or verifying a Finder-browsable raw archive from an iPhone, iOS backup, or libimobiledevice backup before any phone media deletion or cleanup.
---

# iPhone Media Archive

## Overview

Use this skill for backup-first iPhone media archive work where the durable deliverable is a raw Finder-browsable photo/video folder on an external drive.

Never delete media from the phone until a raw archive has been verified and the user gives a separate explicit cleanup go/no-go.

## Workflow

1. Confirm the external drive is mounted, writable, and has enough free space.
2. Diagnose any existing archive folders before writing into them.
3. Create or verify a pre-cleanup iPhone backup on the external drive. Prefer direct `idevicebackup2 backup <external-destination>` when Mac internal storage is tight.
4. Verify backup finalization before using it:
   - `Status.plist` exists and has `SnapshotState=finished`.
   - `Manifest.plist` is a valid plist.
   - `Manifest.db` opens read-only with SQLite immutable mode and `PRAGMA quick_check` returns `ok`.
5. Build a raw media plan from `Manifest.db` plus backed-up `Media/PhotoData/Photos.sqlite`.
   - Use only raw `Media/DCIM/...` backup files for the Finder-browsable archive.
   - Use `Photos.sqlite` `ZASSET.ZDATECREATED` mapped by `ZDIRECTORY` + `ZFILENAME` for capture-date ordering.
   - Use same-stem matching for Live Photo MOV files and AAE sidecars.
   - Treat backup file mtimes as weak fallback evidence, not capture dates.
6. Run a dry-run extraction report before copying.
7. Copy selected older media to a new date-organized archive folder on the external drive.
8. Verify count, size, extension distribution, capture-date range, and sample still/video decodability.
9. Stop for user cleanup approval. Do not clear Recently Deleted unless the user explicitly asks after verification.

## Scripts

Use bundled scripts from `scripts/`:

- `verify-iphone-backup-manifest.sh <backup-root> [out-dir]`
  - Read-only backup integrity and media manifest summary.
  - Uses SQLite immutable mode for ExFAT/removable-drive compatibility.
- `extract-iphone-backup-media.py --backup-root <backup-root> --dest-root <archive-root> [--older-fraction 0.80|--cutoff-date YYYY-MM-DD] [--execute] [--report <path>]`
  - Without `--execute`, writes a dry-run TSV and copies nothing.
  - With `--execute`, copies selected raw files into `YYYY/YYYY-MM-DD/` folders.
- `verify-raw-archive.sh <archive-root> [out-dir]`
  - Summarizes count, size, extensions, and sample file probes with `file`, `sips`, and `ffprobe` when available.

## Safety Rules

- Keep backups and archives on the external drive when internal disk space is low.
- Do not reformat or repartition an external drive unless the user explicitly asks.
- Do not rely on Photos libraries on ExFAT as the primary archive. Raw files are the durable deliverable.
- Ask the user only for unavoidable manual prompts: iPhone unlock/trust, backup password, macOS privacy access, or explicit cleanup confirmation.
- Save logs, reports, and one-off scripts into the active task folder so the archive can be audited later.
