```yaml
slice: d2-code-invariant-binding
date: 2026-04-14
phase: 1-intent
invariants-touched: []
adrs-referenced: [ADR-003]
envelope:
  - "scripts/validate_architecture.py"
  - "docs/adr/003-*.md"
  - "docs/ARCHITECTURE.md"
  - "tests/unit/test_invariant_assertions.py"
out-of-scope:
  - "D1 refresh automation (already landed)"
  - "D3 unknown-unknown backstop (separate slice)"
  - "Hook enforcement of roles (ADR-003 D4 v2+ time-box)"
  - "Retroactive enforcement against consumer repos"
```

### What and Why

ADR-003 D2 requires every firm invariant in `docs/ARCHITECTURE.md` to carry a machine-checkable assertion — not just a markdown cross-reference to an ADR. Today the validator (`scripts/validate_architecture.py`) checks ADR↔invariant cross-reference consistency (checks A/B/C) but does not verify that the codebase actually *satisfies* the declared invariants. This slice adds per-invariant assertion definitions and an assertion runner to the validator so that `validate_architecture.py` can flag code that violates a declared invariant at each refresh.

### Specification Detail

**Assertion storage.** Each invariant's assertion is defined inline in `docs/ARCHITECTURE.md` as a fenced code block tagged with `invariant-check` immediately following the invariant paragraph. Format:

```
**INV-NNN** Invariant text. (ADR-NNN)

` ` `invariant-check INV-NNN
type: grep | ast | file-exists | test-ref | custom
pattern: "<regex or path glob>"
target: "<file glob to check against>"
expect: match | no-match | exists | pass
description: "one-line human summary of what the check verifies"
` ` `
```

Supported assertion types:
- `grep` — strict regex match against target files; `expect: match` means ≥1 hit required, `expect: no-match` means 0 hits required. Pattern is a Python `re` regex. Target is a glob resolved from project root.
- `file-exists` — target glob must resolve to ≥1 file.
- `test-ref` — names a pytest file:test that, when the full suite runs, exercises this invariant. The assertion runner verifies the test exists; the test itself runs as part of the normal suite.
- `ast` — reserved for v2. The runner recognizes the type but skips with a warning. Not counted toward D2 satisfaction.
- `custom` — reserved for v2. Same skip-with-warning behavior.

**Runner integration.** `validate_architecture.py` gains a new check (D) that:
1. Parses every `invariant-check` fenced block from `ARCHITECTURE.md`.
2. For each block, executes the assertion per its type.
3. Reports per-invariant PASS/FAIL with file:line evidence on failure.
4. Exits non-zero if any firm invariant's assertion fails.

Check D runs after the existing checks A/B/C. A failure in A/B/C still short-circuits before D runs.

**Firmness gating.** Invariants whose assertion block has `type: ast` or `type: custom` (v2-reserved) do not fail the validator — they emit a warning. Invariants with no assertion block at all are flagged as a new check (E): "INV-NNN has no machine-checkable assertion." Check E is a warning in this slice, not a hard failure — the migration of all seven invariants to machine-checkable form may span multiple sessions.

**Migration path for current invariants.** This slice must deliver assertion blocks for at least INV-004 (already has `test_context_budget.py` — wrappable as `test-ref`), INV-005 (naming convention — `grep` against `docs/adr/*.md` filenames), and INV-006 (feature file exists — `file-exists`). INV-001, INV-002, INV-003, and INV-007 are expected to start as advisory or with partial `grep` checks; full machine-checkability for process invariants is a known hard problem and is not a Phase 4 gate for this slice.

**ADR-004 A2 canary migration.** The A2 canary (novel design tokens in Phase 2 approach.md absent from intent.md) is scoped separately from D2 per ADR-003 but will migrate to D2's assertion runner when D2 lands. This slice defines the runner extension point but does NOT implement the A2 canary migration — that is a follow-on slice.

### Boundary

- This slice does NOT modify any hook (`checks/*.sh`). The assertion runner lives entirely in the validator.
- This slice does NOT enforce `firmness: advisory` downgrades on existing invariants — it provides the mechanism. Actual firmness changes to existing invariants require their own ADRs.
- This slice does NOT implement the A2 canary migration (follow-on).
- This slice does NOT add structural-snapshot-diff (that is D3).

### Verification

1. `uv run python scripts/validate_architecture.py` exits 0 when all firm invariants with assertion blocks pass.
2. A deliberately broken assertion (e.g., wrong file glob in an INV-004 test-ref) causes the validator to exit 1 with a message naming the failing invariant and the evidence.
3. An invariant with no assertion block produces a warning on stderr but does not cause exit 1.
4. An invariant with `type: ast` produces a skip-warning on stderr and does not cause exit 1.
5. At least three invariants (INV-004, INV-005, INV-006) have passing assertion blocks in the committed `ARCHITECTURE.md`.
6. `uv run python -m pytest tests/unit/test_invariant_assertions.py` passes — unit tests cover the assertion parser and each assertion type (grep, file-exists, test-ref, plus skip behavior for ast/custom).
