---
slice: SLICE-018 (identifier-scheme/validator-flat-slug)
phase: 2-validation
branch: slice/identifier-scheme-validator
as-of: 2026-04-16 c08db67
---

## State
Phase 2 complete. 8 flat-slug tests RED-verified in `tests/unit/test_validate_architecture.py`; V1–V6 regression bank intact. `approach.md` records ambiguity resolutions.

## Next
Fresh session → `/catchup` → `/start-slice phase 3` to enter Implementation (Builder).

## Blocked / Pending
- Phase 3 inputs: intent.md + the test file only. Do NOT read `validation/approach.md` (phase isolation per ADR-004 D2).
- Widening must touch ADR *discovery* (glob), not just reference-token parsing — V2/V3-neg/V6/V10 assert explicit `ADR files checked: N` counts.
- Check C must route distinctly from Check A; V4 pins `"supersed"` substring in stdout.
- Intent V7: `_resolve_project_root` untouched. `validate()` signature unchanged. Do NOT refactor it.
- Commentary tolerance inside parentheticals: already exercised by `test_v1_cairn_self_dogfood_baseline` against live ARCHITECTURE.md (INV-003/INV-004). Preserve parity.

## Pointers
- `.claude/current-slice/intent.md` — Phase 3 primary input; read in full
- `tests/unit/test_validate_architecture.py` — failing bank begins at `# --- Phase 2 (SLICE-018)` banner; turn GREEN
- `scripts/validate_architecture.py` — envelope source; `parse_adr`, `parse_invariants`, and the discovery glob are the widening sites
- `docs/adr/identifier-scheme.md` — D2 (id shape) and D9 (cross-reference format) govern the widening
