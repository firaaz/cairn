---
slice: SLICE-018 (identifier-scheme/hook-relpath-bypass)
phase: 2-validation
branch: slice/identifier-scheme-hook-relpath
as-of: 2026-04-16 d0118bb
---

## State
SLICE-018 Phase 1 intent committed at d0118bb. Envelope: `checks/reversibility-guard.sh`, `tests/unit/test_hook_relpath_bypass.py`. Invariants: INV-005. ADRs: `identifier-scheme` (cited; committed).

## Next
Fresh session → `/catchup` → `/start-slice phase 2` to enter Validation (Skeptic).

## Blocked / Pending
- Bypass reproduced pre-slice: bare-relative `docs/adr/<id>.md` Write/body-Edit both return exit 0 today; intent V1/V2 encode the target deny
- V9 requires existing `tests/unit/test_hook_tolerance.py` suite to stay green unmodified
- V11 no-crash contract requires running hook outside any git repo with `CLAUDE_PROJECT_DIR` unset

## Features
- identifier-scheme: SLICE-018 in flight (phase 2); SLICE-015/016 closed
- housekeeping: SLICE-017 closed
- v1-defense-d2: SLICE-010/011 queued
- v1-defense-d3: ADR landed; substrate slice pending post-sweep

## Pointers
- `.claude/current-slice/intent.md` — sole Phase 2 input; V1–V12 verification list
- `.claude/current-slice/slice.yaml` — slice id, status, envelope source of truth
- `docs/adr/identifier-scheme.md` — INV-005 origin; D1/D2 schema
- `tests/unit/test_hook_tolerance.py` — SLICE-016 regression suite; reuse helper patterns
- `checks/scope-guard.sh:53` — project-root discovery pattern intent references
