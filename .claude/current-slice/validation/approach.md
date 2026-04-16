---
slice: identifier-scheme/validator-flat-slug
slice-yaml-id: SLICE-018
phase: 2-validation
date: 2026-04-16
---

# Phase 2 approach — Skeptic notes

This document records the Skeptic's reasoning and is NOT read by Phase 3. Phase 3's input is `intent.md` + the test file only.

## Ambiguity resolutions

| # | Ambiguity | Resolution | Source |
|---|-----------|------------|--------|
| A1 | Reference-token grammar inside `(…)` | No new grammar asserted. Intent specifies two recognized shapes (`ADR-NNN`, flat-slug `id:` match) and pins commentary at "parity with current behavior". Commentary tolerance is covered as a whole-corpus regression via the existing `test_v1_cairn_self_dogfood_baseline` — live `docs/ARCHITECTURE.md` already exercises `(ADR-004; confirmed by ADR-009)` (INV-003) and `(ADR-002; dedicated ADR pending ...)` (INV-004). No hand-crafted commentary fixture would be role-legal since it requires reading the implementation grammar. | intent.md §Check A; ADR-004 D2 |
| A2 | "Reference token" vs "free text" (handoff flag) | Same resolution as A1. | intent.md:44 |
| A3 | Synthetic `ADR-NNN` alias for flat-slug ADRs? | **No** — covered by `test_flat_slug_not_addressable_via_synthetic_adr_nnn`. | intent.md §ADR id resolution |
| A4 | Flat-slug shape — what characters define it? | Governed by target ADR's `id:` field, not regex. Fixtures use real published slugs for positives; `no-such-adr` for negative. | identifier-scheme D2 |
| A5 | Error-message format precision | Assert token appears verbatim + invariant id appears. Do NOT pin exact wording (avoids over-constraining Phase 3). Exception: V4 asserts `"supersed"` substring to distinguish Check C from Check A (anti-vacuous-pass). | intent.md §Stdout/stderr |
| A6 | Fixture invocation idiom | `CLAUDE_PROJECT_DIR=tmp_path` env override + `cwd=tmp_path`, reusing existing `_run` helper. No `validate()` signature change (intent V7 pins `_resolve_project_root` as out-of-scope). | V1–V6 pattern |
| A7 | `superseded-by:` field shape | Truthy-string triggers Check C in fixtures (matches real-ADR convention). | intent.md §Check C |
| A8 | INV-005 `(ADR-006)` → `(identifier-scheme)` swap | Fixture-only per intent V10. Live ARCHITECTURE.md untouched. | intent.md §Verification V10 |
| A9 | Check B firmness gate | Accepted + firm triggers; soft does not. Pair of tests (positive + negative) exercises both paths. | intent.md §Check B |

No escalation items.

## Fixture strategy

New helper `_make_flat_slug_project(root, *, adrs, invariants)` is independent of existing `_make_consumer_project`. V1–V6 are byte-identical and remain untouched. Each ADR spec carries explicit id / filename / status / firmness / superseded_by / invariants_touched keys — no combinatorial kwargs bloat. Each invariant spec carries id / refs / optional text.

## Test → intent mapping (8 new tests)

| Intent # | Test |
|---|---|
| V1 | *(inherited)* `test_v1_cairn_self_dogfood_baseline` — covers legacy + commentary parity on live corpus |
| V2 | `test_flat_slug_adr_recognized_and_referenced` |
| V3 | `test_flat_slug_accepted_firm_without_invariant_fails_check_b` |
| V3-neg | `test_flat_slug_soft_without_invariant_no_check_b` |
| V4 | `test_flat_slug_superseded_reference_fails_check_c` |
| V5 | `test_unknown_flat_slug_token_fails_check_a` |
| V5-alias | `test_flat_slug_not_addressable_via_synthetic_adr_nnn` |
| V6 | `test_assertion_blocks_run_on_mixed_corpus` |
| V10 | `test_inv005_style_identifier_scheme_parenthetical_fixture` |

V7 covered by untouched `_resolve_project_root`. V8/V9 are Phase 3 run-time checks, not Phase 2 unit tests.

## Anti-vacuous-pass guards

Three tests carried a risk of passing for the wrong reason (discovery gap masking the behavior under test). Strengthened:

- **V2, V6, V10**: explicit `ADR files checked: N` count assertions prove flat-slug discovery actually ran.
- **V3-neg (soft)**: same — without the count assertion, the test passed vacuously (validator didn't discover soft-scheme.md at all, so "no Check B" held trivially).
- **V4 (superseded)**: asserts lowercase `"supersed"` substring — forces Phase 3 to route through Check C, not Check A (unknown-token) which would incidentally contain the slug.

## RED verification

`uv run pytest tests/unit/test_validate_architecture.py` at Phase 2 close:

- 6 passed (V1–V6 regression bank intact — no existing behavior disturbed)
- 8 failed (every new test fails because current validator neither discovers flat-slug ADR filenames nor recognizes flat-slug reference tokens — precisely the feature Phase 3 must implement)
- No failure is a crash / ImportError / syntax error. Every failure is an AssertionError tied to the declared behavior gap.
