#!/usr/bin/env bash
# Manual trigger for SessionEnd flush pipeline.
# Simulates the SessionEnd hook payload against the most recent Claude Code
# transcript for this project, so you can flush without closing the desktop app.
#
# Usage: ./flush-now.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_SLUG="$(echo "$PROJECT_DIR" | sed 's|[/_]|-|g')"
TRANSCRIPTS_DIR="$HOME/.claude/projects/$PROJECT_SLUG"

if [[ ! -d "$TRANSCRIPTS_DIR" ]]; then
    echo "No transcripts dir at: $TRANSCRIPTS_DIR" >&2
    echo "Open a Claude Code session in $PROJECT_DIR first." >&2
    exit 1
fi

TRANSCRIPT="$(ls -t "$TRANSCRIPTS_DIR"/*.jsonl 2>/dev/null | head -1 || true)"
if [[ -z "$TRANSCRIPT" ]]; then
    echo "No .jsonl transcripts in $TRANSCRIPTS_DIR" >&2
    exit 1
fi

SESSION_ID="$(basename "$TRANSCRIPT" .jsonl)"

echo "Flushing transcript: $TRANSCRIPT"
echo "Session ID: $SESSION_ID"

cd "$PROJECT_DIR"
printf '{"session_id":"%s","source":"manual","transcript_path":"%s"}' \
    "$SESSION_ID" "$TRANSCRIPT" \
  | uv run python hooks/session-end.py

echo "Waiting for flush.py to finish..."
while pgrep -f "scripts/flush.py" > /dev/null 2>&1; do
    sleep 1
done
echo "Flush complete. See scripts/flush.log and sessions/ for results."
