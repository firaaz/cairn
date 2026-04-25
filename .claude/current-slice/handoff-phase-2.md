---
slice: compression/lever-2-orchestrator-split
phase: 2-validation → 3-implementation
branch: feature/compression
as-of: 2026-04-25 68a0213
---

## State
Phase 2 (Skeptic) complete at 68a0213. `tests/unit/test_slice_orchestrator_package_split.py` holds 90 RED gate tests over V2–V6. `validation/approach.md` carries the gate-to-test map. Zero diff in any other test file.

## Next
Dispatch `phase-3-implementer` in a fresh session against `intent.md` + the gate test file; turn V2–V6 GREEN by creating the eight-file package, deleting `scripts/slice_orchestrator.py`, sweeping path strings in commands/ + docs/.

## Blocked / Pending
- OQ2 (CLI form): both `python -m` and direct-`__main__.py` forms tested — keep both working
- OQ3 (`__init__.py` re-export style): Builder's call → `implementation/notes.md`
- Test-file invariance: gate file is the only permitted test diff; all other test files byte-identical
- §S3 drift clause (intent.md:79): submodule helper relocation allowed; tests assert top-level resolution only

## Pointers
- `.claude/current-slice/intent.md` — slice contract; §S2 module map, §S3 re-exports, §V1–V8 gates
- `tests/unit/test_slice_orchestrator_package_split.py` — RED gates Phase 3 turns GREEN
- `.claude/current-slice/validation/approach.md` — gate-to-test map + ambiguity log
- `scripts/slice_orchestrator.py` — delete in the Phase 3 commit that creates the package
