---
slice: identifier-scheme/doc-sweep
date: 2026-04-18
phase: 1-intent
invariants-touched: []
adrs-referenced:
  - identifier-scheme
envelope:
  - "commands/claude-code/handoff.full.md"
  - "tests/unit/test_dogfood_evaluate.py"
  - "tests/unit/test_identifier_scheme_sweep.py"
  - "docs/spec-v1.md"
  - "docs/lessons.md"
  - "docs/operational-reference.md"
  - "docs/ARCHITECTURE.md"
  - "docs/adr/*.md"
out-of-scope:
  - "Historical archives: .claude/completed-slices/**, .claude/sweep-results/**, .claude/plans/**, docs/plans/**, docs/reviews/**, CHANGELOG.md (per ADR identifier-scheme §D7 — historical record)"
  - ".claude/learning.md (append-only session-end log; entries are frozen capture, treated like commit messages)"
  - "Hook scripts (checks/*.sh) and validator code (scripts/validate_architecture.py, scripts/dogfood_evaluate.py) — mixed-window tolerance is permanent per ADR identifier-scheme §D7 Phase 1"
  - "Test files where SLICE-NNN/ADR-NNN appears as intentional fixture or regression input (e.g. test_hook_tolerance.py, test_adr_rename_sweep.py, test_invariant_assertions.py, test_validate_architecture.py beyond docstring/comment prose)"
  - "Frontmatter cross-reference fields (adrs-referenced:, supersedes:) in any file — already migrated by adr-rename-sweep"
  - "Feature file annotation gaps (e.g. missing name: field on .claude/features/identifier-scheme.yaml) — separate concern outside §D7 Phase 2 Part 3"
  - "commands/claude-code/start-slice.full.md — already clean (zero residual matches confirmed at envelope time)"
  - "CLAUDE.md — already clean (zero residual matches confirmed at envelope time); any future drift caught by the verification grep on the in-scope set, not by envelope inclusion"
---

### What and Why

Final mechanical scope of ADR `identifier-scheme` §D7 Phase 2 Part 3. Sweep the residual `SLICE-NNN` and `ADR-NNN` references out of the active long-form prose corpus so that the legacy two-format mixed window collapses to "tolerance only, no live use." After this slice, no active prose document refers to a current entity by its retired numeric identifier; the migration is mechanically complete and only intentional historical/test-fixture references remain.

This closes the identifier-scheme feature tail and unblocks the `feature/identifier-scheme` → `dev` merge plus the 2-overdue integration sweep.

### Specification Detail

**Active prose corpus.** The eight envelope entries above are the in-scope set. They are the user-facing long-form documentation, the slash-command full references, the lessons/spec corpus, the architecture overview, the project safety cheatsheet, the ADR body prose, and the one explicitly named test file with prose-form references in its module docstring. All other repository files are either historical archive (frozen and out of scope per ADR §D7) or substrate that intentionally retains both formats (hooks, validator, tolerance tests).

**Reference forms in scope.** Both `SLICE-NNN` (capital `SLICE` followed by `-` and one or more digits) and `ADR-NNN` (capital `ADR` followed by `-` and one or more digits). Lower-case variants and bare `NNN-slug` filename mentions are out of scope (already handled by adr-rename-sweep).

**Replacement protocol.** Each in-scope reference is replaced with the entity's current canonical `id:`:
- ADR references → flat semantic slug (e.g. `ADR-002` → `phase-pipeline-evaluation`)
- Slice references → hierarchical `<feature>/<slice>` form (e.g. `SLICE-017` → its current id, located via `.claude/completed-slices/` archive metadata or git history)

**Discussion-of-legacy-format exception.** Where a reference appears in prose that is itself *about* the legacy format — e.g. ADR `identifier-scheme`'s D7 explaining the migration window, or `docs/operational-reference.md`'s "Legacy transition" paragraph — the legacy form MAY remain. The discussion is *of* the format, not *in* the format. Phase 2 enumerates these per-occurrence exceptions before writing tests; the rule of thumb: if removing the legacy mention would make the surrounding sentence incoherent, it stays.

**ADR body prose constraint.** Edits to `docs/adr/*.md` body prose are blocked by `reversibility-guard.sh` unless `ADR_EDITORIAL_FIX=1` is set in the environment. This slice WILL require that escape hatch for ADR body sweeps. Frontmatter is not edited; only prose body. The escape hatch is the appropriate mechanism per CLAUDE.md "ADRs are append-only" — typo/migration-fix exception.

**Boundary.** Out-of-scope items are listed in the envelope's `out-of-scope:` field above. The two boundary calls most likely to be questioned:
- `.claude/learning.md` is excluded because its entries are append-only frozen capture of past sessions, semantically equivalent to commit messages — not active prose.
- Test files beyond `test_dogfood_evaluate.py` are excluded because their `SLICE-NNN`/`ADR-NNN` strings are deliberate inputs (legacy-tolerance regression tests, validator fixture data) — modifying them would weaken the very tolerance the migration window depends on.

### Verification

1. **Zero-residual grep on in-scope files.** After implementation: `git grep -E '(SLICE-[0-9]+|ADR-[0-9]+)' -- commands/claude-code/handoff.full.md docs/spec-v1.md docs/lessons.md docs/operational-reference.md docs/ARCHITECTURE.md docs/adr/` returns zero hits, EXCEPT for occurrences explicitly preserved under the discussion-of-legacy-format exception (Phase 2 enumerates and tests freeze the allowlist).

2. **Test docstring cleaned.** `tests/unit/test_dogfood_evaluate.py` line 3's `Originally SLICE-004` reference is rewritten to use the current entity id; the docstring still accurately describes the test's history.

3. **Out-of-scope files untouched.** `git diff --name-only main...HEAD` for this slice shows no files under `.claude/completed-slices/`, `.claude/sweep-results/`, `.claude/plans/`, `docs/plans/`, `docs/reviews/`, `.claude/learning.md`, `CHANGELOG.md`, `checks/`, or `scripts/validate_architecture.py`/`scripts/dogfood_evaluate.py`.

4. **Tolerance test suites still pass.** `uv run pytest tests/unit/test_hook_tolerance.py tests/unit/test_adr_rename_sweep.py tests/unit/test_invariant_assertions.py tests/unit/test_validate_architecture.py` all GREEN — confirms the legacy-tolerance substrate is unaffected.

5. **Full test suite passes.** `uv run pytest` GREEN.

6. **Architecture validator passes.** `uv run python scripts/validate_architecture.py` exit 0.

7. **No frontmatter cross-references touched.** `git diff main...HEAD` shows zero changes inside YAML frontmatter `adrs-referenced:` or `supersedes:` fields of any ADR file.

8. **ADR_EDITORIAL_FIX=1 invocations logged in commit message body.** Each commit that uses the escape hatch names the ADR file(s) edited and the prose-only nature of the edit, so the sweep can be audited post-hoc.
