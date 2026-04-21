# Phase 2 Approach — housekeeping/inv004-rebaseline-cc-2.1.116

**Role**: Skeptic. **Date**: 2026-04-21. **Skill**: `superpowers:test-driven-development` (RED + Verify-RED).

Follows prior `housekeeping/inv004-rebaseline` (phase 2 commit `973d351`): modify existing doc-contract assertions in-place, extend the regression-guard `required` list, add no new tests (intent §Verification fixes count at five).

## Ambiguity resolutions

1. **Does Phase 2 touch `BUDGET_HARD`, `BUDGET_ASPIRATIONAL`, module docstring, or `test_inv004_turn1_token_budget` docstring?** Intent lists these under Spec-Detail without pinning phase. **Resolution**: Phase 3. These are production state the asserter tests *read*; Phase 2 editing them would flip the docstring + live-budget tests GREEN at exit, violating Verify-RED.

2. **Banished-literal granularity: `≤30,000` vs `≤30,000 total tokens`.** **Resolution**: broader `≤30,000` for paragraph/block guards; narrower `≤30,000 tokens` for docstring guard (matches exact wording). Mirrors prior ≤22,000.

3. **`housekeeping/inv004-rebaseline` substring collides with new `-cc-2.1.116` variant.** **Resolution**: keep both assertions; tightening is out of scope. Auditor verifies the CC 2.1.110 provenance sentence separately per §Verification #5.

4. **Docstring rewrite risked breaking `the stale ``≤22,000`` literal is gone` substring guard.** **Resolution**: caught on first RED run; restructured so each "stale X literal is gone" clause sits on one physical line.

No operator escalation.

## Test-to-spec mapping

| Test | Phase 2 | Phase 3 flip trigger |
|---|---|---|
| `test_inv004_turn1_token_budget` | RED (30249>30000) | `BUDGET_HARD = 40_000` |
| `test_inv004_architecture_rebaselined` | RED | edit ARCHITECTURE.md paragraph |
| `test_inv004_invariant_check_block_description_rebaselined` | RED | edit invariant-check block desc |
| `test_inv004_turn1_token_budget_docstring_rebaselined` | RED | edit budget-test docstring |
| `test_inv004_regression_guards_preserved` | GREEN | stays GREEN (guardrail) |

## RED evidence

`uv run pytest tests/unit/test_context_budget.py -v` → 4 failed, 1 passed. Each failure cites file:line + expected-vs-actual string.

## Out of scope

Phase 3 writes the constants, docstrings, ARCHITECTURE.md edits, measurement file. Inherited reds/ruff errors → `housekeeping/post-inv008-tech-debt`.
