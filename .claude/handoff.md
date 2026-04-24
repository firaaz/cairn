---
slice: cost-discipline/lever-1-per-phase-model
phase: complete
branch: feature/compression
as-of: 2026-04-24 ea3b45e
---

## State
Lever 1 closed (`23f1db0`): `AGENT_MODEL_CONFIG` + `_resolve_model_config` + dispatch `--model`/`--effort` splice + honest `model_by_phase` recording. 746 tests pass. Closed on Phase-4 run 4 after Phase-3 commit-discipline bug tripped B15 cap (recovered via manual `7feebbd`). Two lessons filed at `ea3b45e`.

## Next
Restore `.claude/sweep.yaml` control keys (`last-sweep-at-slice-id: cost-discipline/lever-1-per-phase-model`, `sweep-interval: 1`) OR open the L-009 follow-on slice — either fixes the sweep-due regression before next close.

## Blocked / Pending
- `.claude/sweep.yaml` clobbered at `23f1db0` — control keys missing → `docs/lessons.md:L-009`
- L-008 follow-on: orchestrator non-empty-handoff check at Phase-3 boundary → `docs/lessons.md:L-008` §Mechanism
- L-009 follow-on: remove `.claude/sweep.yaml` from `.claude/agents/phase-4-integrator.md:9` Writes list
- Cross-slice Lever 1 validation: default vs `CAIRN_MODEL_PHASE_{3,4}_*=opus` comparison needs two post-Lever-1 slices
- compression Slice C — blocked on `/decision` shape a vs b → `docs/plans/2026-04-18-session-compression-audit.md:61`

## Features
- cost-discipline: Track 0 + Lever 1 complete; L-008/L-009 hardening queued
- compression: C blocked, D/F not opened

## Pointers
- `docs/lessons.md:L-008/L-009` — phase-3 empty-handoff + sweep.yaml clobbering; read before either follow-on
- `.claude/features/cost-discipline.yaml` — both slices marked complete
- `scripts/slice_orchestrator.py:1288-1303` — dispatch splice, exemplar for new orchestrator code
