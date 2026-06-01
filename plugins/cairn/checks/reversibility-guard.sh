#!/usr/bin/env bash
# reversibility-guard.sh — blocks destructive operations
# PreToolUse hook on Bash|Edit|Write. Reads JSON from stdin.
# Exit 2 + JSON stdout to block. Exit 0 to allow.

set -euo pipefail

# Dependency check: jq is required to parse tool input
if ! command -v jq &>/dev/null; then
  echo "WARNING: reversibility-guard hook skipped — jq not found in PATH" >&2
  exit 0
fi

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name')

if [ "$TOOL" = "Bash" ]; then
  CMD=$(echo "$INPUT" | jq -r '.tool_input.command')

  BLOCKED=""
  case "$CMD" in
    *"rm -rf"*)                    BLOCKED="rm -rf: use rm with explicit paths instead" ;;
    *"rm -fr"*)                    BLOCKED="rm -fr: use rm with explicit paths instead" ;;
    *"git push --force-with-lease"*) ;; # Safe variant — allow
    *"git push --force"*)          BLOCKED="git push --force: use --force-with-lease instead" ;;
    *"git push -f"*)               BLOCKED="git push -f: use --force-with-lease instead" ;;
    *"git reset --hard"*)          BLOCKED="git reset --hard: use git stash or a backup branch" ;;
    *"git clean -fd"*)             BLOCKED="git clean -fd: destructive — enumerate files first" ;;
    *"DROP TABLE"*|*"drop table"*) BLOCKED="DROP TABLE: export data first" ;;
    *"DROP DATABASE"*|*"drop database"*) BLOCKED="DROP DATABASE: export data first" ;;
  esac

  if [ -n "$BLOCKED" ]; then
    jq -n --arg reason "REVERSIBILITY GUARD: $BLOCKED" \
      '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$reason}}'
    exit 2
  fi
fi

# Canonicalize tool-input paths to a project-root-relative form so bare-relative,
# absolute, and .slice-system/-prefixed shapes produce one deny/allow verdict
# per tool semantics. Mirrors scope-guard.sh's PROJECT_ROOT derivation.
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

if [ "$TOOL" = "Write" ]; then
  FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path')
  CANONICAL="${FILE#$PROJECT_ROOT/}"
  CANONICAL="${CANONICAL#.slice-system/}"
  case "$FILE" in
    *.env|*.env.*)
      jq -n --arg reason "REVERSIBILITY GUARD: blocked write to env file — update .env.example instead" \
        '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$reason}}'
      exit 2 ;;
    *uv.lock|*package-lock.json|*poetry.lock)
      jq -n --arg reason "REVERSIBILITY GUARD: lock files are auto-generated — use uv add / npm install" \
        '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$reason}}'
      exit 2 ;;
  esac
  case "$CANONICAL" in
    docs/adr/index.md) ;;
    docs/adr/*.md)
      if [ -f "$PROJECT_ROOT/$CANONICAL" ]; then
        jq -n --arg reason "REVERSIBILITY GUARD: ADRs are append-only. To change a decision, use /new-adr supersede ADR-NNN. Only frontmatter updates (status, superseded-by) are permitted via Edit." \
          '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$reason}}'
        exit 2
      fi
      ;;
  esac
fi

# Edit on ADR files: allow frontmatter-only changes (status, superseded-by)
# Block body modifications — use /new-adr supersede instead
if [ "$TOOL" = "Edit" ]; then
  FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path')
  CANONICAL="${FILE#$PROJECT_ROOT/}"
  CANONICAL="${CANONICAL#.slice-system/}"
  case "$CANONICAL" in
    docs/adr/index.md) ;;
    docs/adr/*.md)
      OLD=$(echo "$INPUT" | jq -r '.tool_input.old_string')
      # Allow edits that touch only YAML frontmatter fields
      # (status:, superseded-by:, superseded_by:, firmness:)
      # Check FIRST LINE ONLY — a multiline old_string with a frontmatter keyword
      # on a later line could be a body edit disguised as a frontmatter change.
      if echo "$OLD" | head -1 | grep -qE '^(status:|superseded-by:|superseded_by:|firmness:)'; then
        exit 0
      fi
      # Editorial-fix escape hatch: ADR_EDITORIAL_FIX=1 narrowed to ADDITIVE
      # edits where new_string contains old_string. A leaked shell
      # ADR_EDITORIAL_FIX=1 no longer masks wholesale body rewrites; typo
      # patches (append/insert of annotation markers) and footnote additions
      # remain unblocked. Full replacements require /new-adr supersede per
      # append-only invariant. Prevents pytest session-env leaks from
      # spuriously greenlighting deny-path tests.
      if [ "${ADR_EDITORIAL_FIX:-}" = "1" ]; then
        NEW=$(echo "$INPUT" | jq -r '.tool_input.new_string')
        if [[ "$NEW" == *"$OLD"* ]]; then
          echo "ADR_EDITORIAL_FIX: allowing edit to $FILE" >> .claude/adr-editorial-fixes.log 2>/dev/null || true
          exit 0
        fi
      fi
      jq -n --arg reason "REVERSIBILITY GUARD: ADR body is append-only. Only frontmatter updates (status, superseded-by) are permitted. Use /new-adr supersede to create a replacement." \
        '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$reason}}'
      exit 2
      ;;
  esac
fi

exit 0
