## Implementation Notes — SLICE-016 Phase 3

**Approach**: Widened both `case` patterns in `checks/reversibility-guard.sh` from
`*/docs/adr/[0-9]*` to `*/docs/adr/*.md`, with `*/docs/adr/index.md` as a no-op
first-match exclusion immediately before each widened pattern. Bash `case` evaluates
top-down and stops at first match, so `index.md` hits the no-op arm and never
reaches the enforcement arm.

**Files changed**: `checks/reversibility-guard.sh` (lines 51-52, 67-68)

**No deviations from intent envelope.** scope-guard.sh and reality-check.sh
confirmed unchanged (Phase 2 GREEN tests cover coexistence; no implementation
change needed).
