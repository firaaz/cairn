---
slice: d2-assertion-block-migration
date: 2026-04-14
phase: 1-intent
invariants-touched: []
adrs-referenced: [ADR-003]
envelope:
  - "docs/ARCHITECTURE.md"
  - "tests/unit/test_invariant_assertions.py"
out-of-scope:
  - "scripts/validate_architecture.py — already has Check D/E from SLICE-010"
  - "New assertion types beyond grep, file-exists, test-ref"
  - "Changes to invariant text — only adding assertion blocks"
---

### What and Why

SLICE-010 landed Check D (assertion execution) and Check E (missing-assertion warning) in the architecture validator, but deferred the actual assertion blocks. All seven invariants (INV-001 through INV-007) currently trigger Check E warnings because no assertion blocks exist in `docs/ARCHITECTURE.md`. This slice adds machine-checkable assertion blocks for every invariant that can be expressed using the three supported assertion types (`grep`, `file-exists`, `test-ref`), completing the D2 defense commitment from ADR-003.

Without assertion blocks, Check D is inert — the validator has the execution machinery but nothing to execute. This is the gap between "can check" and "does check."

### Specification Detail

Each assertion block is a fenced code block in `docs/ARCHITECTURE.md` placed immediately after its invariant's paragraph, formatted as:

```
```invariant-check INV-NNN
type: grep|file-exists|test-ref
pattern: "<regex or path>"
target: "<file glob>"
expect: match|no-match
description: "<what this checks>"
```​
```

Constraints:
- Every invariant (INV-001 through INV-007) must have exactly one assertion block after this slice completes.
- Assertions must use only the three v1 types: `grep`, `file-exists`, `test-ref`. If an invariant genuinely cannot be expressed with these types, mark its block as `type: custom` (v2-reserved) with a `description` explaining why — but this should be a last resort, not a first choice.
- Assertions must be falsifiable: a deliberate violation of the invariant must cause the assertion to fail. The test suite must include at least one falsification test per assertion.
- Assertion blocks must not alter the invariant text itself — they are addenda, not edits.
- The `target` field uses Python `Path.glob()` syntax (not shell glob).

### Boundary

- The validator (`scripts/validate_architecture.py`) is NOT in scope — SLICE-010 already landed Check D/E execution logic.
- Invariant text in ARCHITECTURE.md is not modified — only assertion blocks are added after each invariant paragraph.
- No new assertion types are introduced.

### Verification

1. `python3 scripts/validate_architecture.py` produces zero Check E warnings (all 7 invariants have assertion blocks).
2. `python3 scripts/validate_architecture.py` exits 0 with no Check D failures (all assertions pass against current codebase).
3. Test suite includes falsification tests: for each assertion, a test that corrupts the expected state and confirms the validator would report a Check D failure.
4. `python3 -m pytest tests/unit/test_invariant_assertions.py` passes.
5. Full test suite passes: `python3 -m pytest tests/unit/`.
