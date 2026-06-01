#!/usr/bin/env bash
# reality-check.sh — runs ruff format + check on edited Python files
# PostToolUse hook on Edit|Write. Reads JSON from stdin.

set -euo pipefail

# Dependency check: jq is required to parse tool input
if ! command -v jq &>/dev/null; then
  echo "WARNING: reality-check hook skipped — jq not found in PATH" >&2
  exit 0
fi

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only act on Python files
case "$FILE" in
  *.py) ;;
  *) exit 0 ;;
esac

# Skip if file was deleted
[ -f "$FILE" ] || exit 0

# Check ruff availability — warn once if missing so the user knows formatting is off
if ! command -v ruff &>/dev/null; then
  echo "WARNING: reality-check hook skipped — ruff not found in PATH. Install with: uv tool install ruff" >&2
  exit 0
fi

# Format first, then lint with auto-fix. Both are fast (<500ms each).
ruff format --quiet "$FILE" 2>/dev/null || true
ruff check --fix --quiet "$FILE" 2>/dev/null || true

exit 0
