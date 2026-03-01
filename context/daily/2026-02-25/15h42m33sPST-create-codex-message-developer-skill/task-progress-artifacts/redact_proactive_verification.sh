#!/usr/bin/env bash
set -euo pipefail
# Purpose: Redact sensitive WhatsApp identifiers from proactive notification verification logs.
# Input: Path to proactive-notification-verification.txt (defaults to this task's artifact file).
# Output: In-place sanitized file with phone numbers and message IDs replaced by placeholders.

TARGET="${1:-/home/azureuser/pro/botfiles/context/daily/2026-02-25/15h42m33sPST-create-codex-message-developer-skill/task-progress-artifacts/proactive-notification-verification.txt}"

if [[ ! -f "$TARGET" ]]; then
  echo "Target file not found: $TARGET" >&2
  exit 1
fi

TMP_PATH="${TARGET}.tmp.$$"

sed -E \
  -e "s/\+12408851299/<REDACTED_PHONE_E164>/g" \
  -e "s/\b12408851299\b/<REDACTED_PHONE_DIGITS>/g" \
  -e "s/phone_number_id=[0-9]+/phone_number_id=<REDACTED_PHONE_NUMBER_ID>/g" \
  -e "s/wa_id': '[^']*'/wa_id': '<REDACTED_WA_ID>'/g" \
  -e "s/wamid\.[A-Za-z0-9._-]+/<REDACTED_WAMID>/g" \
  "$TARGET" > "$TMP_PATH"

mv "$TMP_PATH" "$TARGET"
echo "Redaction complete: $TARGET"
