---
slice: identifier-scheme/slice-and-feature-rename
phase: 2-validation
branch: feature/identifier-scheme
as-of: 2026-04-18 170fa90
---

## State
Phase 2 validation committed at `170fa90`. `validation/approach.md` records §9 = drop, §8 = in-envelope analog in dogfood counter. `tests/unit/test_dogfood_evaluate.py` rewritten per intent §12: 14 RED on legacy `_read_sweep_yaml` path, 6 GREEN regression guards.

## Next
Run `/start-slice phase 3` in a fresh session. Builder lands git-log counter in `scripts/dogfood_evaluate.py` and executes feature-file + sweep.yaml + command-template migrations to green the RED suite.

## Blocked / Pending
- approach.md redirects verification items 1, 2, 4, 5, 8–10 to Phase 4 Auditor (grep + `file:line`). Phase 3 does not expand envelope.
- §8 literal logic lives in `commands/claude-code/start-slice.full.md` prose — Phase 4 grep-asserts the fallback paragraph.
- Baseline-missing conservative default: Phase 3 chooses between "proceed with first-commit baseline" or "exit 2 with diagnostic"; `TestBaselineMissingFallback` accepts either (exit 1 or 2 with stderr diagnostic).
- `CLAUDE.md` + `docs/plans/measurements/2026-04-12-slice-003.txt` uncommitted — operator changes, out of slice scope (Phase 1 carry-over).

## Pointers
- `.claude/current-slice/intent.md` — envelope + §§3, 5, 6, 7 normative migrations.
- `.claude/current-slice/validation/approach.md` — §9/§8 dispositions + envelope-correction rationale.
- `tests/unit/test_dogfood_evaluate.py` — 14 RED tests Phase 3 must green; `_init_git_with_adr_and_slices` models the new counter substrate.
