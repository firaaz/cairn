---
slice: compression/upgrade-doc-bug-fixes
phase: 1-intent
branch: feature/compression-followup
as-of: 2026-05-02 7bc837e
---

## State
intent.md committed at 7bc837e with envelope `docs/upgrading-from-pre-compression.md` + `tests/unit/test_upgrade_doc_consumer_setup.py`; `adrs-referenced: []` and `invariants-touched: []` so D3 gate passes trivially.

## Next
Run `/start-slice phase 2` in a fresh session to enter Validation; Skeptic writes the seven verification checks from `intent.md` alone.

## Blocked / Pending
- Test 7 SHA-256 pin requires capturing the §3-§5 byte hash at slice open → compute fresh in Phase 2 against current `docs/upgrading-from-pre-compression.md`
- Test 6 needs the substrate venv resolvable via `uv run --directory .slice-system` → Phase 2 host must have `uv` on PATH and `.venv` populated

## Pointers
- `.claude/current-slice/intent.md` — read first; sole Phase 2 input per context-isolation rule
- `docs/plans/2026-04-27-compression-followup-design.md` §3 Slice 7 — read only if intent ambiguity surfaces
