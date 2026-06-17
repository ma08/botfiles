#!/usr/bin/env bash
# Read-only verification for an unencrypted libimobiledevice/Finder-style iPhone backup.
# Usage: verify-iphone-backup-manifest.sh <backup-root> [out-dir]

set -u

BACKUP_ROOT="${1:-}"
OUT_DIR="${2:-./iphone-media-archive-artifacts}"

if [[ -z "$BACKUP_ROOT" ]]; then
  printf 'Usage: %s <backup-root> [out-dir]\n' "$0" >&2
  exit 2
fi

mkdir -p "$OUT_DIR"
STAMP="$(TZ=America/Los_Angeles date '+%Y%m%d-%H%M%S')"
LOG="$OUT_DIR/verify-iphone-backup-manifest-$STAMP.log"
MEDIA_TSV="$OUT_DIR/backup-media-manifest-$STAMP.tsv"

section() {
  printf '\n===== %s =====\n' "$1"
}

run() {
  printf '\n$ %s\n' "$*"
  "$@" 2>&1 || printf '[exit %s]\n' "$?"
}

fail() {
  printf 'ERROR: %s\n' "$1" | tee -a "$LOG" >&2
  exit "${2:-1}"
}

{
  section "timestamp"
  TZ=America/Los_Angeles date '+%Y-%m-%d ~%I:%M%p PST'
  printf 'backup_root: %s\n' "$BACKUP_ROOT"
  printf 'media_tsv: %s\n' "$MEDIA_TSV"
  section "space"
  run df -h "$BACKUP_ROOT"
} >"$LOG"

[[ -d "$BACKUP_ROOT" ]] || fail "backup root not found: $BACKUP_ROOT" 3

DEVICE_DIR="$(find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -print | head -1)"
[[ -n "$DEVICE_DIR" ]] || fail "no device directory found under backup root." 4

STATUS_PLIST="$DEVICE_DIR/Status.plist"
MANIFEST_PLIST="$DEVICE_DIR/Manifest.plist"
MANIFEST_DB="$DEVICE_DIR/Manifest.db"
INFO_PLIST="$DEVICE_DIR/Info.plist"

for required in "$STATUS_PLIST" "$MANIFEST_PLIST" "$MANIFEST_DB" "$INFO_PLIST"; do
  [[ -f "$required" ]] || fail "missing required backup file: $required" 5
done

SQLITE_DB_URI="file:$MANIFEST_DB?mode=ro&immutable=1"

{
  section "backup files"
  run du -sh "$BACKUP_ROOT"
  run ls -lh "$INFO_PLIST" "$STATUS_PLIST" "$MANIFEST_PLIST" "$MANIFEST_DB"

  section "status plist"
  run plutil -p "$STATUS_PLIST"

  section "manifest plist"
  run plutil -lint "$MANIFEST_PLIST"

  section "manifest db integrity"
  quick_check="$(sqlite3 "$SQLITE_DB_URI" 'PRAGMA quick_check;' 2>&1)" \
    || fail "sqlite quick_check failed: $quick_check" 6
  printf '%s\n' "$quick_check"
  [[ "$quick_check" == "ok" ]] || fail "sqlite quick_check returned non-ok result: $quick_check" 7

  section "manifest db counts"
  run sqlite3 "$SQLITE_DB_URI" "SELECT COUNT(*) AS total_files_rows FROM Files;"

  section "media candidate counts"
  sqlite3 -header -tabs "$SQLITE_DB_URI" "
    SELECT domain, COUNT(*) AS rows
    FROM Files
    WHERE relativePath LIKE 'Media/DCIM/%' OR relativePath LIKE 'DCIM/%'
    GROUP BY domain
    ORDER BY rows DESC, domain;
  " 2>&1

  section "writing media tsv"
  if ! sqlite3 -header -tabs "$SQLITE_DB_URI" "
    SELECT fileID, domain, relativePath
    FROM Files
    WHERE
      (relativePath LIKE 'Media/DCIM/%' OR relativePath LIKE 'DCIM/%')
      AND (
        lower(relativePath) LIKE '%.heic'
        OR lower(relativePath) LIKE '%.heif'
        OR lower(relativePath) LIKE '%.hif'
        OR lower(relativePath) LIKE '%.jpg'
        OR lower(relativePath) LIKE '%.jpeg'
        OR lower(relativePath) LIKE '%.png'
        OR lower(relativePath) LIKE '%.mov'
        OR lower(relativePath) LIKE '%.mp4'
        OR lower(relativePath) LIKE '%.dng'
        OR lower(relativePath) LIKE '%.tif'
        OR lower(relativePath) LIKE '%.tiff'
        OR lower(relativePath) LIKE '%.aae'
      )
    ORDER BY domain, relativePath, fileID;
  " >"$MEDIA_TSV"; then
    fail "failed to write media TSV from Manifest.db" 8
  fi
  printf 'media_tsv: %s\n' "$MEDIA_TSV"
  printf 'media_tsv_rows_including_header: '
  wc -l <"$MEDIA_TSV" | tr -d ' '
  printf '\n'
} >>"$LOG"

printf '%s\n' "$LOG"
