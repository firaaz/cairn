# SLICE-009 Validation Approach

Phase 2 — Skeptic. Tests written against intent.md + ADR-006 + ADR-008 only.

## Ambiguities Enumerated

**A1. Feature ID source.** Intent says `/start-slice` creates a feature file "if one does not already exist for the current feature" but doesn't specify how the feature ID is determined or associated with a slice.
- **Resolved:** ADR-006 D5 delegates to skill instructions at trigger events. Tests verify the instructions exist in start-slice.full.md, not the interaction mechanism.

**A2. "Active" feature definition.** Cross-feature index contains "one line per active feature" — what makes a feature active vs. inactive?
- **Resolved:** ADR-006 D4 derives status from observable state (branch existence, merge state, parked flag). Tests verify index format, not activity logic.

**A3. `## Features` section position in handoff.md template.** Where in the template relative to existing sections?
- **Resolved:** Not constrained by intent or ADR-008. Tests verify the section exists, not its position.

**A4. `slices` field optionality.** Listed as "Optional field" in schema spec, but V1 says "containing at least one entry" after `/start-slice`.
- **Resolved:** Schema allows feature files without `slices` (e.g., during brainstorming per ADR-006 D2). After `/start-slice`, at least one entry is required — this is a skill-behavior constraint, tested via start-slice.full.md conformance.

**A5. Scope-guard always-allowed mechanism.** Intent says "same category as `.claude/current-slice/`" — always-allowed regardless of slice phase.
- **Resolved:** Same always-allowed list. Test verifies the pattern appears in scope-guard.sh.

**A6. Token counting method for V9.** How to approximate tokens?
- **Resolved:** ADR-008 uses ~5 chars/token (same approximation as INV-002's 2000-char/400-token ceiling). Tests use the same method.

No ambiguities require human resolution.

## Test Plan

Four test files matching envelope pattern `tests/unit/test_feature_*.py`:

### test_feature_file_schema.py (V1, V2, V3, V7)
Pure validation logic — defines the feature file schema as a validator function, tests it against valid/invalid synthetic data. These tests pass immediately (they define the spec, not check the codebase).

- Valid complete feature file accepted
- Missing required fields (`id`, `intent`, `created`) rejected
- `id` must match filename stem
- Slice entry requires `id` and `added`
- `status` field only legal value is `dropped`
- Dropped slice with `reason` preserved
- Single-slice feature accepted (no special-case rejection)
- Update operation: adding slice entry preserves existing entries

### test_feature_skill_conformance.py (V1, V3, V4, V5, V8)
Static artifact checks — reads slash command files and templates, verifies they contain feature-model instructions. These tests FAIL until Phase 3 modifies the files.

- start-slice.full.md references feature file creation at `.claude/features/`
- start-slice.full.md references existing feature file update (adding slice entry)
- handoff.full.md references cross-feature index / `## Features` section
- templates/handoff.md contains `## Features` section
- catchup.full.md Tier 1 references cross-feature index from handoff
- catchup.full.md Tier 1 does NOT load feature files directly

### test_feature_scope_guard.py (V6)
Checks scope-guard.sh source for `.claude/features/` in always-allowed paths. FAILS until Phase 3 modifies scope-guard.sh.

- Source contains `.claude/features/` pattern in always-allowed section
- Subprocess test: scope-guard allows Write to `.claude/features/test.yaml`

### test_feature_cross_index.py (V4, V9)
Format and budget validation with synthetic data. PASSES immediately (defines the format spec).

- Single index line matches `- <id>: <summary>` format
- 5-feature index stays under 125 tokens (~625 chars at 5 chars/token)
- Empty index (no active features) is valid

## RED/GREEN Split

| Category | Expected in Phase 2 (RED) | Turns GREEN in Phase 3 |
|---|---|---|
| Schema validation | PASS (tests the validator, not codebase) | N/A |
| Skill conformance | FAIL (files not yet modified) | Phase 3 modifies skill files |
| Scope-guard | FAIL (path not yet added) | Phase 3 modifies scope-guard.sh |
| Cross-index format | PASS (synthetic data) | N/A |
