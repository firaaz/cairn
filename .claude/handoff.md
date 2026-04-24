---
slice: cost-discipline/track-0-telemetry
phase: complete
branch: feature/compression
as-of: 2026-04-24 c367677
---

## State
Track 0 closed (`c367677`): per-phase tokens/USD recorded at every subagent dispatch; `PRICING_TABLE_2026_04_24` seeded; INV-009 introduced provisional advisory-only. Closed on second cycle after phase-4 RAISE_ISSUE + op-adjudicated envelope amendment (`5223d53`) covering two Phase-1 scope-gaps: dispatch-site wiring + `test_invariant_assertions.py` guard.

## Next
Open `cost-discipline/lever-1-per-phase-model` via `/start-slice` — now measurable via Track 0 telemetry.

## Blocked / Pending
- compression Slice C — blocked on `/decision` shape a vs b → `docs/plans/2026-04-18-session-compression-audit.md:61`
- compression Slice D envelope-immutability + Slice F rolling-window /status — not opened
- INV-004 rebaseline under CC 2.1.119 → future `housekeeping/inv004-rebaseline`
- Track B lightweight-slice hatch + Track C consumer-surface docs — strategic-plan seeds
- Path C fleet-writes empirical gap → memory `path_c_fleet_writes_empirical.md`
- Lesson for `docs/lessons.md`: invariant-introduction slices MUST envelope `tests/unit/test_invariant_assertions.py` (EXPECTED_INVARIANT_IDS guard)

## Features
- cost-discipline: Track 0 complete; Lever 1 ready to open
- compression: C blocked, D/F not opened

## Pointers
- `.claude/features/cost-discipline.yaml:10-13` — Lever 1 envelope + intent; read before `/start-slice`
- `docs/plans/2026-04-23-cost-discipline-design.md` — §"Lever 1" insertion points at `:120-132`
- `~/.claude/plans/actually-it-looks-like-glimmering-journal.md` — strategic plan re-ground (cost as first-class)
- `scripts/slice_orchestrator.py:1262-1320` — Track 0 dispatch wiring (S2.a flag + S2.b `_record_phase_cost`)
- `docs/adr/cost-per-slice-budget.md` — INV-009 provisional; X/Y TBD pending baseline
