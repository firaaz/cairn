---
slice: SLICE-018 (identifier-scheme/hook-relpath-bypass)
phase: 2-validation
branch: slice/identifier-scheme-hook-relpath
as-of: 2026-04-16 90c0868
---

## State
Validation suite committed at `tests/unit/test_hook_relpath_bypass.py` (61 cases). V1/V2/V7/V12 RED reproduce the bypass; V3–V6, V8, V11 regression guards hold; V10 skipped where jq is reachable via minimal PATH.

## Next
Phase 3 entry: implement canonical-form path normalization in `checks/reversibility-guard.sh`; pass V1–V12 without editing `tests/unit/test_hook_tolerance.py`.

## Blocked / Pending
- Phase 3 input is intent.md + the new test file only; MUST NOT load `validation/approach.md`
- V9 regression: `tests/unit/test_hook_tolerance.py` must stay green unmodified
- V11 no-crash contract: project-root derivation must survive `set -euo pipefail` with `CLAUDE_PROJECT_DIR` unset outside any git repo
- Intent §5: deny-reason strings are byte-identical to today
- Intent §6: editorial-fix log line may reference raw `$FILE` or canonical form (author choice, consistent)

## Pointers
- `.claude/current-slice/intent.md` — V1–V12 verification list; Phase 3 input
- `tests/unit/test_hook_relpath_bypass.py` — validation suite Phase 3 turns green
- `checks/reversibility-guard.sh` — envelope; ADR case blocks at :51, :68
- `checks/scope-guard.sh:53` — project-root derivation pattern intent mirrors
