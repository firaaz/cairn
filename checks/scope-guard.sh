#!/usr/bin/env bash
# scope-guard.sh — blocks edits outside the current slice's file envelope
# PreToolUse hook on Edit|Write. Reads JSON from stdin.
# Exit 2 + JSON stdout to block. Exit 0 to allow.

set -euo pipefail

# Dependency check: jq is required to parse tool input
if ! command -v jq &>/dev/null; then
  echo "WARNING: scope-guard hook skipped — jq not found in PATH" >&2
  exit 0
fi

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
INTENT_FILE="$PROJECT_ROOT/.claude/current-slice/intent.md"

# No active slice or missing intent → allow everything
if [ ! -f "$INTENT_FILE" ]; then
  exit 0
fi

# Completed or failed slices should not enforce scope guards
SLICE_YAML="$PROJECT_ROOT/.claude/current-slice/slice.yaml"
if [ -f "$SLICE_YAML" ]; then
  SLICE_STATUS=$(awk '/^status:/ { print $2 }' "$SLICE_YAML")
  case "$SLICE_STATUS" in
    complete|failed) exit 0 ;;
  esac
fi

# Extract envelope patterns from intent.md YAML block
# Expected format:
#   envelope:
#     - "src/mcp/*.py"
#     - "src/db/queries.py"
PATTERNS=$(awk '
  /^envelope:/ { capture=1; next }
  capture && /^[[:space:]]+-/ { gsub(/[[:space:]]*#.*$/, ""); gsub(/^[[:space:]]+-[[:space:]]*"?|"?[[:space:]]*$/, ""); print; next }
  capture && /^[^[:space:]]/ { capture=0 }
' "$INTENT_FILE")

# If no patterns found → allow everything
if [ -z "$PATTERNS" ]; then
  exit 0
fi

# Get the target file
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
[ -z "$FILE" ] && exit 0

# Make path relative to project root
REL_FILE="${FILE#$PROJECT_ROOT/}"

# Always allow writes to administrative/lifecycle files
# These paths are needed by the development system itself (handoff, sweep, ADR creation)
# and must not be blocked by the slice envelope. ADR append-only protection is handled
# separately by reversibility-guard.sh.
case "$REL_FILE" in
  .claude/current-slice/*|.claude/handoff.md|.claude/sweep.yaml|.claude/features/*) exit 0 ;;
  .claude/d1-bypasses.log|.claude/d3-bypasses.log) exit 0 ;;
  docs/adr/*|docs/ARCHITECTURE.md|docs/lessons.md) exit 0 ;;
  CLAUDE.md|.gitignore) exit 0 ;;
esac

# Check if file matches any envelope pattern
check_match() {
  local target="$1"
  while IFS= read -r pattern; do
    [ -z "$pattern" ] && continue
    # Use bash extended globbing
    # shellcheck disable=SC2254
    if [[ "$target" == $pattern ]]; then
      return 0
    fi
  done <<< "$PATTERNS"
  return 1
}

# Direct match
if check_match "$REL_FILE"; then
  exit 0
fi

# Auto-include: test infrastructure files (conftest.py, __init__.py in test dirs)
if [[ "$REL_FILE" == tests/* ]]; then
  BASENAME=$(basename "$REL_FILE")
  case "$BASENAME" in
    conftest.py|__init__.py) exit 0 ;;
  esac
fi

# Auto-include: test files for source files in envelope
# If editing tests/unit/foo/test_bar.py, check if src/foo/bar.py is in envelope
if [[ "$REL_FILE" == tests/* ]]; then
  # Strip known test directory prefixes, then strip test_ only from the filename
  SRC_MIRROR=$(echo "$REL_FILE" | sed 's|^tests/unit/||; s|^tests/[^/]*/||; s|^tests/||' | sed 's|/test_\([^/]*\)$|/\1|; s|^test_||')
  if check_match "$SRC_MIRROR" || check_match "src/$SRC_MIRROR"; then
    exit 0
  fi
fi

# Auto-include: if a source file is in envelope, its test mirror is allowed
if [[ "$REL_FILE" == tests/* ]]; then
  # Extract the base filename without test_ prefix
  BASE=$(basename "$REL_FILE" | sed 's|^test_||')
  # Check if any envelope pattern could match the corresponding source
  while IFS= read -r pattern; do
    [ -z "$pattern" ] && continue
    PATTERN_BASE=$(basename "$pattern")
    if [ "$BASE" = "$PATTERN_BASE" ]; then
      exit 0
    fi
  done <<< "$PATTERNS"
fi

# Expand-envelope escape hatch
if [ "${EXPAND_ENVELOPE:-}" = "1" ]; then
  echo "$REL_FILE" >> "$PROJECT_ROOT/.claude/current-slice/envelope-expansions.log"
  jq -n --arg file "$REL_FILE" \
    '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":("SCOPE: Envelope expanded to include " + $file + " (logged)")}}'
  exit 0
fi

# Block the edit
PATTERN_LIST=$(echo "$PATTERNS" | tr '\n' ', ' | sed 's/,$//')
jq -n --arg reason "SCOPE GUARD: $REL_FILE is outside the slice envelope. Permitted: $PATTERN_LIST. Set EXPAND_ENVELOPE=1 to override." \
  '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$reason}}'
exit 2
