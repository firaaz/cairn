---
slice: SLICE-018 (identifier-scheme/hook-relpath-bypass)
phase: 3-implementation
branch: slice/identifier-scheme-hook-relpath
as-of: 2026-04-16 90c0868
---

## State
Phase 2 validation complete. Test suite + approach.md committed; slice advanced to implementation. Envelope: `checks/reversibility-guard.sh`, `tests/unit/test_hook_relpath_bypass.py`. Invariants: INV-005. ADRs: `identifier-scheme`.

## Next
Fresh session → `/catchup` → `/start-slice phase 3` to implement canonical-form path normalization in `reversibility-guard.sh` so bare-relative and `.slice-system/`-prefixed ADR paths deny consistently.

## Blocked / Pending
- Phase 3 context isolation: intent.md + test file only; MUST NOT load `validation/approach.md`
- V9 regression: `tests/unit/test_hook_tolerance.py` (25/25) must stay green unmodified
- V11 no-crash: project-root derivation must be safe under `set -euo pipefail` with `CLAUDE_PROJECT_DIR` unset outside git

## Features
- identifier-scheme: SLICE-018 in flight (phase 3); SLICE-015/016 closed
- housekeeping: SLICE-017 closed
- v1-defense-d2: SLICE-010/011 queued
- v1-defense-d3: ADR landed; substrate slice pending post-sweep

## Pointers
- `.claude/current-slice/intent.md` — sole Phase 3 input paired with the test file
- `tests/unit/test_hook_relpath_bypass.py` — validation suite Phase 3 must green
- `checks/reversibility-guard.sh` — envelope; ADR case blocks at :51, :68
- `checks/scope-guard.sh:53` — project-root derivation pattern intent references
