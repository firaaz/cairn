---
slice: SLICE-018 (identifier-scheme/hook-relpath-bypass)
phase: 4-integration
branch: slice/identifier-scheme-hook-relpath
as-of: 2026-04-16 3131096
---

## State
Phase 3 implementation committed. Canonical-form path normalization in `reversibility-guard.sh` closes the bare-relative + `.slice-system/`-prefixed ADR-protection bypass. Envelope: `checks/reversibility-guard.sh`. Invariants: INV-005. ADRs: identifier-scheme.

## Next
Fresh session → `/catchup` → `/start-slice phase 4` to verify INV-005, run full suite + validator, audit adjacent regressions.

## Blocked / Pending
- Phase 4 context: load intent.md + envelope hook + ARCHITECTURE.md only; do NOT load `validation/approach.md` or `implementation/notes.md` reasoning unless auditing.
- Two envelope-compliance tests fire only on uncommitted WIP — verified clean post-commit via stash.
- Sweep due: `.claude/sweep.yaml` interval 1, last 17, current 18 → integration sweep #13 follows slice close.

## Features
- identifier-scheme: SLICE-018 phase 4 (integration); SLICE-015/016 closed
- housekeeping: SLICE-017 closed
- v1-defense-d2: SLICE-010/011 queued
- v1-defense-d3: ADR landed; substrate slice pending post-sweep

## Pointers
- `.claude/current-slice/intent.md` — Phase 4 spec source; V1–V12 verification table
- `checks/reversibility-guard.sh` — envelope; canonical-form normalization at top, ADR cases on `$CANONICAL`
- `tests/unit/test_hook_relpath_bypass.py` — Phase 4 must run green
- `tests/unit/test_hook_tolerance.py` — V9 regression guard, must stay green unmodified
