#!/usr/bin/env bash
# verify_handoff.sh — post-check for /handoff side-effect divergence (L-005 class).
#
# Three checks (intent efficiency-program/all-seven Item 4):
#   (a) If last commit subject is `phase-N:`, slice.yaml.status should reflect
#       a state compatible with having closed phase N (i.e. mentions N, N+1,
#       or a later/post-pipeline label). Forgiving match — the point is to
#       catch the divergence where status and commit disagree, not to police
#       exact label strings.
#   (b) If last commit subject is `phase-N:`, `.claude/current-slice/handoff-phase-<N>.md`
#       must exist.
#   (c) Last commit subject MUST begin with `handoff:`, `phase-<N>:`, or
#       `slice: <anything> — complete`.
#
# Exit 0 on pass. Non-zero on failure. Failing stderr names the check and
# remediation command.

set -euo pipefail

err() { printf '%s\n' "$*" >&2; }

subject="$(git log -1 --format=%s 2>/dev/null || true)"
if [ -z "$subject" ]; then
  err "verify_handoff: no commits in repo (expected a handoff or phase commit)"
  err "remediation: commit your handoff artifact before invoking the verifier"
  exit 2
fi

# Check (c): subject-prefix gate.
# Accepted forms:
#   handoff: ...
#   phase-<N>: ...
#   slice: ... — complete   (em-dash separator)
subject_ok=0
if printf '%s' "$subject" | grep -Eq '^handoff:'; then
  subject_ok=1
elif printf '%s' "$subject" | grep -Eq '^phase-[0-9]+:'; then
  subject_ok=1
elif printf '%s' "$subject" | grep -Eq '^slice: .* — complete$'; then
  subject_ok=1
fi

if [ "$subject_ok" -eq 0 ]; then
  err "verify_handoff: check (c) FAILED — commit subject does not match"
  err "  expected one of: 'handoff: ...', 'phase-<N>: ...', 'slice: ... — complete'"
  err "  got: '$subject'"
  err "  remediation: amend the commit subject (git commit --amend) to match one of the accepted forms"
  exit 1
fi

# Extract phase number if this is a phase-commit.
phase_n=""
if printf '%s' "$subject" | grep -Eq '^phase-[0-9]+:'; then
  phase_n="$(printf '%s' "$subject" | sed -E 's/^phase-([0-9]+):.*/\1/')"
fi

# Check (b): phase-commit → handoff-phase-<N>.md must exist.
if [ -n "$phase_n" ]; then
  expected_file=".claude/current-slice/handoff-phase-${phase_n}.md"
  if [ ! -f "$expected_file" ]; then
    err "verify_handoff: check (b) FAILED — missing $expected_file"
    err "  commit subject claims phase-${phase_n} but no handoff-phase-${phase_n}.md was written"
    err "  remediation: run /handoff phase to produce the phase handoff note, then amend the commit"
    exit 1
  fi
fi

# Check (a): pipeline-phase status compatibility (phase-commit subjects only).
# slice.yaml.status should reference phase N or N+1 or a post-pipeline label.
# Forgiving match — presence of the digit N or N+1 in status, OR a complete/failed label, passes.
if [ -n "$phase_n" ] && [ -f ".claude/current-slice/slice.yaml" ]; then
  status_line="$(grep -E '^status:' .claude/current-slice/slice.yaml | head -n1 || true)"
  status_val="$(printf '%s' "$status_line" | sed -E 's/^status:[[:space:]]*//; s/[[:space:]]*$//; s/^"(.*)"$/\1/; s/^'\''(.*)'\''$/\1/')"
  next_n=$((phase_n + 1))
  status_ok=0
  case "$status_val" in
    *complete*|*failed*) status_ok=1 ;;
    *"${next_n}"*|*"${phase_n}"*) status_ok=1 ;;
  esac
  if [ "$status_ok" -eq 0 ]; then
    err "verify_handoff: check (a) FAILED — slice.yaml.status '$status_val' is incompatible with commit subject '$subject'"
    err "  phase-${phase_n} commit expects status to mention phase ${phase_n} or ${next_n} (or a terminal label)"
    err "  remediation: update .claude/current-slice/slice.yaml status field to match the phase that was just closed"
    exit 1
  fi
fi

exit 0
