#!/usr/bin/env bash
# role-cheatsheet.sh — emits a role cheatsheet on SessionStart.
#
# Reads .claude/current-slice/slice.yaml for status/id/name, looks up the
# matching row in docs/operational-reference.md § Phase Skill Guide, and
# emits one additionalContext line via SessionStart's JSON output shape.
# Always exits 0: never a session blocker.
#
# Also performs an idempotent measurements-artifact refresh: if the tracked
# file docs/plans/measurements/2026-04-12-slice-003.txt has drifted from
# HEAD, restore HEAD's bytes. If the working-tree content already matches
# HEAD (or git is unavailable), no write occurs — so repeated invocations
# leave `git status --porcelain` empty on that path. Addresses
# efficiency-program Item 2 (Form A: diff-then-write idempotency).

set -eu

# Idempotent measurements-artifact refresh. Runs first so a transient git
# failure never blocks the role-hint emission below (all errors swallowed).
# Uses `git checkout HEAD -- <path>` for byte-exact restoration — git
# internally no-ops when working-tree content already matches HEAD, so
# repeated invocations leave `git status --porcelain` empty.
refresh_measurements_idempotent() {
  rel_path="docs/plans/measurements/2026-04-12-slice-003.txt"
  project_dir="${CLAUDE_PROJECT_DIR:-$PWD}"
  abs_path="$project_dir/$rel_path"
  [ -f "$abs_path" ] || return 0
  command -v git >/dev/null 2>&1 || return 0
  git -C "$project_dir" ls-files --error-unmatch -- "$rel_path" >/dev/null 2>&1 || return 0
  git -C "$project_dir" checkout HEAD -- "$rel_path" >/dev/null 2>&1 || return 0
}

refresh_measurements_idempotent || true

emit_context() {
  # $1 = additionalContext string. Escape embedded double-quotes and backslashes
  # so the JSON stays valid even if a slice name carries a quote.
  msg=$1
  escaped=$(printf '%s' "$msg" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$escaped"
}

emit_generic() {
  emit_context "No active slice — /start-slice to open one"
  exit 0
}

PROJECT_DIR=${CLAUDE_PROJECT_DIR:-$PWD}
SLICE_YAML="$PROJECT_DIR/.claude/current-slice/slice.yaml"
REF_DOC="$PROJECT_DIR/docs/operational-reference.md"

[ -f "$SLICE_YAML" ] || emit_generic
[ -f "$REF_DOC" ] || emit_generic

# Parse slice.yaml minimally. A malformed file that blows up sed/grep still
# falls through to emit_generic because we never let a non-zero propagate.
status=$(sed -n 's/^status:[[:space:]]*\(.*\)$/\1/p' "$SLICE_YAML" 2>/dev/null | head -n1 | tr -d '"' | tr -d "'" | awk '{$1=$1;print}') || status=""
slice_name=$(sed -n 's/^name:[[:space:]]*\(.*\)$/\1/p' "$SLICE_YAML" 2>/dev/null | head -n1 | tr -d '"' | tr -d "'" | awk '{$1=$1;print}') || slice_name=""
slice_id=$(sed -n 's/^id:[[:space:]]*\(.*\)$/\1/p' "$SLICE_YAML" 2>/dev/null | head -n1 | tr -d '"' | tr -d "'" | awk '{$1=$1;print}') || slice_id=""

[ -n "$status" ] || emit_generic

case "$status" in
  complete|failed) emit_generic ;;
esac

case "$status" in
  1-intent)
    phase_num=1
    phase_name="Intent"
    role="Reader"
    anti="Reader does not propose implementation"
    ;;
  2-validation)
    phase_num=2
    phase_name="Validation"
    role="Skeptic"
    anti="Skeptic does not implement"
    ;;
  3-implementation)
    phase_num=3
    phase_name="Implementation"
    role="Builder"
    anti="Builder does not re-litigate the spec or the tests"
    ;;
  4-integration)
    phase_num=4
    phase_name="Integration"
    role="Auditor"
    anti="Auditor does not rewrite the implementation"
    ;;
  *)
    emit_generic
    ;;
esac

display_name=${slice_name:-$slice_id}
[ -n "$display_name" ] || display_name="(unnamed)"

emit_context "Slice: ${display_name}. Phase: ${phase_num} ${phase_name}. Role: ${role}. Anti-behavior: ${anti}."
exit 0
