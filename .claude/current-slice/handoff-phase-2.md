---
slice: compression/orchestrator-hardening
phase: 2-validation
branch: feature/compression
as-of: 2026-04-19 2610e1c
---

## State
Phase 2 validation committed at `2610e1c`. Artifact: `tests/unit/test_orchestrator_hardening.py` (new, 8 RED) + monkeypatches added to `tests/unit/test_slice_orchestrator_state_machine.py:178,196` (2 GREEN) + `.claude/current-slice/validation/approach.md`. Phase gate for Phase 3 is met.

## Next
Builder: run tests, implement F1 in `scripts/slice_orchestrator.py:105-133`, implement F2 across `init_new_slice` (line 335) and `run_phase_loop` (line 237).

## Blocked / Pending
- F1 value `acceptEdits` is pinned in tests; alternative requires ADR-cite + same-commit test update → approach.md §A1.
- F1 constant NAME is not pinned — Builder chooses → approach.md §A2.
- F2 `brief` propagation site (once at loop entry vs per-iteration) is Builder's choice → approach.md §open-questions-2.
- Do not load `approach.md` in Phase 3 per phase-lock D2; tests alone carry the contract.

## Pointers
- `.claude/current-slice/intent.md` — the contract. Read first.
- `tests/unit/test_orchestrator_hardening.py` — RED tests to turn GREEN.
- `tests/unit/test_slice_orchestrator_state_machine.py` — already GREEN; do not regress.
- `scripts/slice_orchestrator.py` — envelope target (modification sites: line 111 cmd list, line 237 run_phase_loop inputs dict, line 335 init_new_slice write_text).
