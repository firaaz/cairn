---
slice: identifier-scheme/slice-and-feature-rename
phase: 1-intent
branch: feature/identifier-scheme
as-of: 2026-04-17 af660a5
---

## State
Phase 1 intent committed at `af660a5`. 11-file envelope: four `.claude/features/*.yaml`, `.claude/sweep.yaml`, `scripts/dogfood_evaluate.py`, its test, `start-slice.full.md` + `integration-sweep.full.md`, `docs/operational-reference.md`. Spec pins hierarchical slug renames for SLICE-010/011/012/013, `name:`/`shaped-from:` additions, `current-slice-number` retirement.

## Next
Close this session. In the next, run `/catchup` then `/start-slice phase 2`.

## Blocked / Pending
- `CLAUDE.md` uncommitted (trailing terse-replies line removed) — operator change, out of slice scope.
- `docs/plans/measurements/2026-04-12-slice-003.txt` uncommitted — ignore per operator.
- `test_context_budget::test_inv004_turn1_token_budget` pre-existing CC-drift flake — ignore per operator.
- d3-bypass-classification Decision 2 `exempt:` syntax + `snapshot_diff.py` classified-format parser — carried from sweep #14/#15/#16.
- 5 SLICE-020 reviewer suggestions → `docs/lessons.md`; `start-slice.full.md:220` rolling-window wording — low-priority carry-overs.

## Features
- identifier-scheme: slice-and-feature-rename Phase 1→2; doc-sweep queued (Phase 2 Part 3)
- integration-gate: complete
- housekeeping: complete (SLICE-017/018)
- v1-defense-d2: complete (SLICE-010/011)
- v1-defense-d3: bypass-log-test-resilience complete; Decision 2 substrate queued

## Pointers
- `.claude/current-slice/intent.md` — slice scope, per-feature migration tables, verification checklist; load for Phase 2 test design.
- `.claude/current-slice/handoff-phase-1.md` — phase gate state + §9/§8 ambiguity flags for Phase 2 Skeptic.
- `docs/adr/identifier-scheme.md` — §D2/D5/D6/D7 normative.
