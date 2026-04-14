# SLICE-011 Phase 2 — Validation Approach

## Ambiguity Resolutions

| # | Ambiguity | Resolution |
|---|-----------|------------|
| A1 | Falsification tests can't know assertion types ahead of Phase 3 | Data-driven: tests parse assertion blocks from cairn's ARCHITECTURE.md at runtime and synthesize type-specific corruptions (grep → remove pattern; file-exists → omit target; test-ref → omit test file). Tests fail if no blocks to parse. |
| A2 | "Exactly one assertion block" — duplicates? | Parser returns dict keyed by INV-ID; second block overwrites first. Test verifies 7 unique keys. |
| A3 | Which invariants can use v1 types? | Test asserts all 7 use v1 types (grep, file-exists, test-ref). If Phase 3 must use `custom`, the test fails explicitly — making the choice visible. |
| A4 | Invariant text must not change — how to verify? | Test verifies the set {INV-001..INV-007} exists with unchanged count in ARCHITECTURE.md. |
| A5 | Extend or replace existing self-dogfood test? | Extended. Existing `test_cairn_self_validation_still_passes` stays; new classes add coverage/warning/falsification requirements. |

## Test Structure

Three new test classes appended to `tests/unit/test_invariant_assertions.py`:

1. **`TestSlice011AssertionCoverage`** (8 tests) — structural checks on assertion blocks: all 7 present, no extras, v1 types only, required fields per type, invariant count unchanged.

2. **`TestSlice011ZeroWarnings`** (2 tests) — validator integration: zero Check E warnings, zero Check D failures against cairn's own codebase.

3. **`TestSlice011Falsification`** (5 tests) — data-driven falsification: guard test (7+ blocks must exist), then per-type corruption tests for grep+match, grep+no-match, file-exists, test-ref.

## RED State

4 tests fail, 40 pass. Failures are all "assertion blocks missing" — correct RED. The 11 new passing tests are vacuous (iterate empty sets) and become meaningful once Phase 3 adds blocks.

## Phase 3 Contract

Phase 3 must:
- Add one `invariant-check` fenced block per invariant (INV-001 through INV-007) in `docs/ARCHITECTURE.md`
- Use only v1 assertion types: `grep`, `file-exists`, `test-ref`
- Include at least one `grep` assertion with `expect: match` (the falsification test hard-fails otherwise)
- Not modify invariant text
- Ensure all assertions pass against cairn's current codebase
