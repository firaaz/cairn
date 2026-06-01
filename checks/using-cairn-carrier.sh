#!/usr/bin/env bash
# using-cairn-carrier.sh — Cairn SessionStart carrier (ADR using-cairn-carrier-contract, Approach D).
#
# Emits a NEUTRAL, state-accurate pointer to the active intent, or a no-intent
# statement, to stdout — which Claude Code injects as session context. It is a
# pointer, not a payload; byte-budgeted; and it NEVER gates (always exits 0).
#
# Emission is deliberately state-only with NO imperative instruction prose: a
# SessionStart hook's stdout merges into every agent's effective prompt, and an
# imperative line ("run the X / you must / cannot proceed") can be read by a
# tier-sensitive agent as a command or blocker and trigger a hard refusal
# (docs/lessons.md L-012). The carrier states facts; it never instructs.
#
# "Fired" (D2): the first stdout line is the machine marker CAIRN_CARRIER_FIRED.
# If the script never runs (non-Claude-Code host), the marker never appears and
# the cairn-intent skill's Step 1 load-or-form does the work unconditionally —
# the carrier is an optimization, not the only path (D4/D5).
#
# cairn-internal (D6): registered in .claude/settings.json SessionStart and NOT
# in scripts/build_dist.py — it does not ship to consumers until the D7 ADR.

set -euo pipefail

# Byte-budget proxy for the <=2k-token sub-budget (~4 bytes/token => 8000 bytes).
# Env-overridable per CLAUDE.md no-hardcoded-sizes. Truncation is visible, not silent.
BUDGET_BYTES="${CAIRN_CARRIER_BUDGET_BYTES:-8000}"

# SessionStart passes JSON on stdin; the carrier needs no field from it, but must
# drain the pipe so the producer does not see a broken pipe.
cat >/dev/null 2>&1 || true

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
HANDOFF="$PROJECT_DIR/.claude/handoff.md"

emit() { head -c "$BUDGET_BYTES"; }

{
  echo "CAIRN_CARRIER_FIRED"

  # Resume path: the most recent intent.md pointer whose handoff thread is `open`.
  # State-aware (INV-002 {open,blocked,deferred}): a deferred/blocked/closed thread
  # is not an active intent, so it is never emitted as one.
  POINTER=""
  if [ -f "$HANDOFF" ]; then
    POINTER=$(grep -E '\.claude/skill-runs/[^ ]+/intent\.md[[:space:]]+open([[:space:]]|$)' "$HANDOFF" 2>/dev/null \
      | grep -oE '\.claude/skill-runs/[^ ]+/intent\.md' \
      | tail -n1 || true)
  fi

  if [ -n "$POINTER" ] && [ -f "$PROJECT_DIR/$POINTER" ]; then
    echo "cairn intent (open): $POINTER"
    SCOPE=$(sed -n 's/^[[:space:]]*scope-statement:[[:space:]]*//p' "$PROJECT_DIR/$POINTER" 2>/dev/null | head -n1 || true)
    if [ -n "$SCOPE" ]; then
      printf 'scope: %s\n' "$(printf '%s' "$SCOPE" | head -c 200)"
    fi
  else
    echo "cairn: no active intent on record"
  fi
} | emit

exit 0
