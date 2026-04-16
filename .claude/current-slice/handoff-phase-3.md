---
slice: SLICE-016 (identifier-scheme/hook-tolerance)
phase: 3-implementation
branch: feature/identifier-scheme
as-of: 2026-04-16 d01ab72
---

## State
SLICE-016 Phase 3 complete. `reversibility-guard.sh` glob widened from `*/docs/adr/[0-9]*` to `*/docs/adr/*.md` with `index.md` first-match exclusion. 25/25 hook-tolerance tests GREEN; 227/229 full suite (2 pre-existing failures on older slice envelopes).

## Next
Run `/start-slice phase 4` to enter Integration.

## Blocked / Pending
- Pre-existing red: `test_v7_envelope_compliance` (SLICE-005), `test_v4_envelope_compliance` (SLICE-007) on `uv.lock` → housekeeping slice
- Validator substrate gap: `validate_architecture.py` does not recognize flat-slug ADR IDs → follow-on slice

## Pointers
- `checks/reversibility-guard.sh` — the implementation; Phase 4 audits this against intent
- `.claude/current-slice/intent.md` — envelope and verification criteria; load at Phase 4
- `tests/unit/test_hook_tolerance.py` — 25-test validation suite; Phase 4 runs full suite
