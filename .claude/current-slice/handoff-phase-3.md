---
slice: identifier-scheme/adr-rename-sweep
phase: 3-implementation
branch: feature/identifier-scheme
as-of: 2026-04-17 400a6f5
---

## State
Phase 3 implementation committed at 400a6f5. 9 ADRs renamed (git mv) + id: migrated; 40-file live-tree sweep landed; CHANGELOG migration entry added; tolerance fixtures routed through `legacy_adr_mirror` tmp_path pattern. Slice suite 25/25 green, full suite 379 passed + 1 skipped (jq-missing contract), validator exit 0. Phase 4 gate met.

## Next
Run `/start-slice phase 4` in a fresh session.

## Blocked / Pending
- `tests/unit/test_context_budget.py::test_inv004_turn1_token_budget` pre-existing CC-version-drift flake (2.1.110 baseline vs 2.1.112 current) — ran green on final suite pass but may oscillate; see `implementation/notes.md` §D6, ignore per operator.
- `docs/plans/measurements/2026-04-12-slice-003.txt` still uncommitted — continue to ignore per operator.
- `ARCHITECTURE.md:31` INV-003 paren restructured to drop "confirmed by" qualifier so `_extract_refs` sees `phase-pipeline-evaluation` as a clean fragment — see `implementation/notes.md` §D4.
- Sweep #16 `/integration-sweep` due after slice closes (last=20, current=22).

## Pointers
- `.claude/current-slice/implementation/notes.md` — Phase 3 decision log D1–D6 + `ADR_EDITORIAL_FIX` → `sed` substitution audit trail. Phase 4 reads this for Builder-judgment context without loading Phase 2's approach.md.
- `.claude/current-slice/intent.md` — Phase 4 Auditor reads for verification checklist (§Verification items 1–10) and invariants-touched (INV-005).
- `tests/unit/test_adr_rename_sweep.py` — 25 tests; Phase 4 re-runs as full-suite slice.
- `docs/adr/identifier-scheme.md` — governing ADR; referenced.
