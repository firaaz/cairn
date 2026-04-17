---
slice: identifier-scheme/adr-rename-sweep
phase: 2-validation
branch: feature/identifier-scheme
as-of: 2026-04-17 3e85b13
---

## State
Phase 2 validation committed at 3e85b13. Suite in `tests/unit/test_adr_rename_sweep.py` is 25 tests; currently 21 RED (V1–V6) + 4 GREEN regression guards (V5-no-path, V7 validator, V10×2 tolerance-files-present). Phase 3 gate met: tests in git.

## Next
Run `/start-slice phase 3` in a fresh session.

## Blocked / Pending
- Phase 3 must restructure `test_hook_tolerance.py` + `test_hook_relpath_bypass.py` fixtures — after rename, `docs/adr/006-feature-slice-model.md` is gone; tolerance V2 assertions lose their subject → approach.md §F2 (synthetic 999-slug sentinel or tmp_path).
- Verification #4 grep is interpreted to exclude the two tolerance test files; approach.md §F1 documents reconciliation of intent V4 vs V10.
- `identifier-scheme.md` + `d3-bypass-classification.md` frontmatter needs `supersedes:`/body `ADR-NNN` → flat-slug migration via the general sweep; approach.md §A5.
- CHANGELOG H3 placement inside `## [Unreleased]` is Phase-3 judgment; tests assert presence + content only.

## Features
- identifier-scheme: adr-rename-sweep Phase 2→3; slice-and-feature-rename + doc-sweep queued
- integration-gate: complete
- housekeeping: complete (SLICE-017/018)
- v1-defense-d2: complete (SLICE-010/011)
- v1-defense-d3: bypass-log-test-resilience complete; Decision 2 substrate queued

## Pointers
- `.claude/current-slice/intent.md` + `tests/unit/test_adr_rename_sweep.py` — Phase 3 Builder's sole inputs. Do NOT read `approach.md` (Skeptic reasoning, context-isolated).
- `docs/adr/identifier-scheme.md` — referenced ADR, available to Phase 3.
- `.claude/sweep.yaml` — cadence (last=20, current=22; /integration-sweep #16 due after slice closes).
