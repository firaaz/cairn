---
slice: compression/upgrade-doc-bug-fixes
phase: 2-validation
branch: feature/compression-followup
as-of: 2026-05-02 9decbec
---

## State
Phase 2 RED committed at 9decbec: 7 tests in `tests/unit/test_upgrade_doc_consumer_setup.py` (6 failed for the discriminated bug, 1 GREEN by construction); D3 gate for Phase 3 is `tests/` committed → met.

## Next
Run `/start-slice phase 3` in a fresh session to enter Implementation; Builder edits `docs/upgrading-from-pre-compression.md` to turn the 6 RED tests GREEN.

## Blocked / Pending
- Tests 5/6 carry `snippet == DELTA{1,2}_CORRECTED_SNIPPET` text-equality before runtime-invoke → snippet text must match the corrected form verbatim from intent §Specification Detail
- Test 7 SHA-256 baseline `b136326e...43d2b` (4009 bytes from `## 3. Python dependencies`) → Deltas 3/4/5 must remain byte-identical
- Phase 3 must NOT load `.claude/current-slice/validation/approach.md` per phase-lock-and-role-declaration D2

## Pointers
- `.claude/current-slice/intent.md` — sole spec input for Phase 3
- `tests/unit/test_upgrade_doc_consumer_setup.py` — the GREEN target; read to confirm exact expected snippet strings and JSON shape
