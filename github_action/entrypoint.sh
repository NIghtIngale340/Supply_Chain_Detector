#!/bin/sh
set -eu

API_BASE_URL="${1:-http://localhost:8000}"
THRESHOLD="${2:-70}"
POLL_TIMEOUT="${3:-90}"

python /action/scan_requirements.py \
  --api-base-url "$API_BASE_URL" \
  --threshold "$THRESHOLD" \
  --poll-timeout "$POLL_TIMEOUT"
