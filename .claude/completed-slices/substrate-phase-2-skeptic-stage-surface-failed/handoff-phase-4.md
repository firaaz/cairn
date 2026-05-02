# Phase 4 handoff — substrate/phase-2-skeptic-stage-surface

Status: RAISE_ISSUE

## Why RAISE_ISSUE

Fix is functionally correct (lifecycle.py patch lands; 4/4 RED→GREEN; INV-008 PASS via validate_architecture.py). Blocker: `tests/unit/test_phase_2_handoff_staging_surface.py` is **untracked** — neither Phase 2 (ran with unfixed orchestrator) nor Phase 3 (committed only lifecycle.py at `ae9e6c8`, then empty handoff `14e065a`) staged it. Bisect-anchor acceptance gate in intent.md unsatisfied. DC-4 forbids Phase 4 commits.

## Tests

- Slice surface: 4/4 PASS.
- Full suite: 1177 passed, 2 pre-existing fails (out-of-scope, verified at slice init), 3 skipped, 3 xfailed.

## Architecture

`validate_architecture.py` PASS (10 invariants, 18 ADRs).

## Recommendation to triager

Either: (a) re-dispatch to Phase 3 to commit the missing test file (and any other Phase-3-owned diffs), or (b) close this slice as substantively complete and open a follow-up slice that lands the test alongside a "self-application check" mitigation.
