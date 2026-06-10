#!/usr/bin/env bash
# reality-check.sh — runs ruff format + check on edited Python files
# PostToolUse hook on Edit|Write. Reads JSON from stdin.

set -euo pipefail

# Dependency check: jq is required to parse tool input
if ! command -v jq &>/dev/null; then
  echo "ERROR: reality-check hook dependency missing: jq not found in PATH; failing closed" >&2
  exit 1
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

# Check ruff availability — fail closed if formatting is unavailable
if ! command -v ruff &>/dev/null; then
  echo "ERROR: reality-check hook dependency missing: ruff not found in PATH; failing closed" >&2
  exit 1
fi

# Format first, then lint with auto-fix. Both are fast (<500ms each).
ruff format --quiet "$FILE" 2>/dev/null || true
ruff check --fix --quiet "$FILE" 2>/dev/null || true

exit 0
