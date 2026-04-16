---
slice: SLICE-018 (identifier-scheme/hook-relpath-bypass)
phase: 4-integration
auditor: Phase 4 (ADR-004 D2 role)
as-of: 2026-04-16
verdict: PASS
---

## Verdict

**PASS.** All 12 declared verification points satisfied. INV-005 tolerance preserved and extended from filename shape to input-path shape. No regressions in adjacent hooks. Slice ship-ready.

## Evidence

### Full test suite
`uv run python -m pytest` → **290 passed, 1 skipped** (V10 `test_missing_jq_returns_exit_0_with_warning` skipped per intent.md §V10 — `jq` cannot be PATH-stripped cleanly in test env).

### Architecture validator
`uv run python scripts/validate_architecture.py` → **ALL CHECKS PASSED** (7 invariants, 9 ADRs).

### V1–V12 per-case evidence (tests/unit/test_hook_relpath_bypass.py)

| Clause | Test class | Result |
|---|---|---|
| V1 bare-relative flat-slug bypass closed | `TestV1FlatSlugBareRelative` | PASS |
| V2 bare-relative legacy bypass closed | `TestV2LegacyBareRelative` | PASS |
| V3 `.slice-system/`-prefixed denies consistent | `TestV3SliceSystemPrefixed` | PASS |
| V4 frontmatter edit allowed × 4 keys × 3 shapes × 2 shapes | `TestV4FrontmatterEditAllowedAllShapes` (24 params) | PASS |
| V5 new-ADR Write allowed × 3 shapes × 2 shapes | `TestV5NewAdrWriteAllowedAllShapes` (6 params) | PASS |
| V6 `index.md` exempt × 3 shapes | `TestV6IndexExemptAllShapes` | PASS |
| V7 `ADR_EDITORIAL_FIX=1` covers canonical forms | `TestV7EditorialFixCoversCanonicalForms` | PASS |
| V8 `.env` / lockfile denies unchanged | `TestV8EnvAndLockfileRegressions` | PASS |
| V9 SLICE-016 regression guard unmodified | `tests/unit/test_hook_tolerance.py` (25 tests) | PASS |
| V10 missing-jq contract | `TestV10MissingJqContract` | SKIPPED (per spec) |
| V11 no-crash under indeterminate project root | `TestV11NoCrashUnderIndeterminateProjectRoot` | PASS |
| V12 verdict symmetry across 3 shapes × 5 scenarios | `TestV12VerdictSymmetry` | PASS |

### INV-005 file:line verification

Invariant text: *"Hooks (`reversibility-guard.sh`, `scope-guard.sh`) and tooling tolerate both legacy `NNN-slug` filenames and flat-slug filenames during the migration window."* (docs/ARCHITECTURE.md:49)

- `checks/reversibility-guard.sh:43` — `PROJECT_ROOT` derivation mirrors scope-guard.
- `checks/reversibility-guard.sh:47-48` — Write-branch canonical normalization (strip PROJECT_ROOT then `.slice-system/`).
- `checks/reversibility-guard.sh:59-68` — Write-branch `case "$CANONICAL"` matches `docs/adr/*.md` across both legacy and flat-slug filenames.
- `checks/reversibility-guard.sh:62` — file-existence probe uses `$PROJECT_ROOT/$CANONICAL` (CWD-independent).
- `checks/reversibility-guard.sh:75-77` — Edit-branch canonical normalization and case matching, symmetric to Write branch.
- `checks/reversibility-guard.sh:60, 78` — `docs/adr/index.md` exemption on canonical form preserved.

### Adjacent-code regression audit

- `checks/scope-guard.sh` — untouched (empty diff vs. 87ea8b5).
- `checks/reality-check.sh` — untouched (empty diff vs. 87ea8b5).
- `tests/unit/test_hook_tolerance.py` — unmodified; 25/25 tests green (V9 regression guard satisfied).
- Deny-reason strings (§5 byte-identical requirement): verified by V9 staying green (reasons at `:51, 55, 63, 93`).

### Code review (superpowers:code-reviewer, Phase 4 primary skill)

Verdict: **PASS-with-notes**. Three non-blocking style observations:

1. `"${FILE#$PROJECT_ROOT/}"` at `:47, :75` uses unquoted `$PROJECT_ROOT` inside parameter expansion. Matches `scope-guard.sh:53` house style — consistent, not a defect under any realistic path.
2. Multiple `jq` subprocess spawns per branch — consistent with existing terse-hook convention.
3. V12 `_build_scenarios()` called twice at parametrize-collection time — style only.

No defects or intent violations surfaced. No implementation rewrites performed (Auditor anti-behavior honored).

## Next

- `/start-slice complete` — wipe `.claude/current-slice/` (Layer 3 slice-close).
- `/integration-sweep` — sweep #13 due (last 17, current 18, interval 1).
