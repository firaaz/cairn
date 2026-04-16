---
slice: SLICE-018
phase: 4-integration
date: 2026-04-16
auditor-role: ADR-004 D2
verdict: PASS
---

## Verdict

**SLICE-018 housekeeping/stale-22k-cleanup — PASS.**

Declared invariant INV-004 verified with file:line evidence. Full pytest suite green (231/231). Architecture validator green (7 invariants, 9 ADRs).

## Verification commands (fresh, this phase)

| Check | Command | Exit | Result |
|---|---|---|---|
| Full suite | `uv run python -m pytest -q` | 0 | 231 passed in 14.48s |
| Validator | `uv run python scripts/validate_architecture.py` | 0 | ALL CHECKS PASSED — 7 invariants, 9 ADRs |

## Invariant evidence table

**INV-004 — PASS.** Session-start context on a fresh prompt uses ≤30,000 total tokens, machine-checked by `tests/unit/test_context_budget.py`.

| Aspect | File:line | Content | Status |
|---|---|---|---|
| Invariant paragraph (≤30,000 ceiling) | `docs/ARCHITECTURE.md:41` | "Session-start context on a fresh prompt in cairn uses ≤30,000 total tokens …" | Untouched by SLICE-018 (set by SLICE-017) |
| invariant-check block description | `docs/ARCHITECTURE.md:46` | `description: "Points to the test suite that machine-checks the 30k token budget"` | Updated by SLICE-018 (was `22k`) |
| Test budget constant | `tests/unit/test_context_budget.py:17` | `BUDGET_HARD = 30_000` | Untouched (set by SLICE-017) |
| Test docstring | `tests/unit/test_context_budget.py:103` | `"""INV-004 — turn-1 total context ≤30,000 tokens on a fresh 'hi' session."""` | Updated by SLICE-018 (was `≤22,000`) |
| Regression-guard literal (clause) | `tests/unit/test_context_budget.py:121` | `the stale ``≤22,000`` literal is gone` | Preserved (intentional) |
| Regression-guard assertion | `tests/unit/test_context_budget.py:148` | `assert "≤22,000" not in paragraph` | Preserved (intentional) |
| Regression-guard failure message | `tests/unit/test_context_budget.py:149` | `"INV-004 still contains stale '≤22,000' literal"` | Preserved (intentional) |

The four "preserved" entries are out-of-scope per intent.md:13 — they are the regression guards that prevent the stale `≤22,000` from creeping back into ARCHITECTURE.md and would be neutered if scrubbed.

## Adjacent-regression check

- **Envelope-expansion deletions audit.** Phase 3 deleted `test_slice_005_design_decomposition.py::test_v7_envelope_compliance` and `test_sweep_debt_cleanup.py::test_v4_envelope_compliance` (envelope-expansions.log:1-6). Grep `tests/` for `envelope_compliance|envelope-compliance` returns zero files — no orphaned references. Both tests' parent files load cleanly (suite green).
- **No new imports added/removed.** `git diff --stat` over SLICE-018's three implementation commits shows 1 insertion + 87 deletions across 3 test files; no source files modified.
- **Measurements drift (out of envelope).** `docs/plans/measurements/2026-04-12-slice-003.txt` shows uncommitted runtime drift, written by the live `test_inv004_turn1_token_budget` during pre-Phase-4 verification runs. Per intent.md:73 this file is explicitly out of scope for SLICE-018. Prior history (commits `a2f1d5f`, `ec1590e`) shows the established pattern is a separate `measurement:` commit, not folding it into a slice. Auditor recommendation: leave for the user to commit separately or discard; do NOT bundle into the slice-close commit.

## Cross-slice observations (sweep candidates, not blockers)

These do not gate SLICE-018; they are inputs for the upcoming integration sweep #13 (sweep.yaml: `last-sweep-at-slice: 17`, `sweep-interval: 1`, `current-slice-number: 18`):

- Handoff flagged a sweep follow-on for in-body `git diff --name-only HEAD` patterns in closed-slice tests. Outside SLICE-018's envelope; defer to `/integration-sweep`.
- d3-bypass-classification legacy log reclassification (SLICE-012/014/016) and identifier-scheme follow-ons remain pending. Outside SLICE-018's envelope.

## Phase 4 deliverable

This file is the Phase 4 output per `docs/operational-reference.md:60`. No implementation patches were made by the Auditor. INV-004 verdict: PASS.
