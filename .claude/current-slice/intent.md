---
slice: adr-rename-sweep
name: "ADR rename sweep — NNN-slug.md → <id>.md plus live cross-reference sweep (Phase 2 Part 1)"
date: 2026-04-17
phase: 1-intent
invariants-touched: [INV-005]
adrs-referenced: [identifier-scheme]
envelope:
  - "docs/adr/001-bootstrap-exception.md"
  - "docs/adr/002-context-discipline-protocol.md"
  - "docs/adr/003-cliff-failure-mode-and-v1-defenses.md"
  - "docs/adr/004-phase-lock-and-role-declaration.md"
  - "docs/adr/005-semantic-identity.md"
  - "docs/adr/006-feature-slice-model.md"
  - "docs/adr/007-parallelism-v1.md"
  - "docs/adr/008-context-tiers-integration.md"
  - "docs/adr/009-phase-pipeline-evaluation.md"
  - "docs/adr/bootstrap-exception.md"
  - "docs/adr/context-discipline-protocol.md"
  - "docs/adr/cliff-failure-mode-and-v1-defenses.md"
  - "docs/adr/phase-lock-and-role-declaration.md"
  - "docs/adr/semantic-identity.md"
  - "docs/adr/feature-slice-model.md"
  - "docs/adr/parallelism-v1.md"
  - "docs/adr/context-tiers-integration.md"
  - "docs/adr/phase-pipeline-evaluation.md"
  - "docs/adr/d3-bypass-classification.md"
  - "docs/adr/identifier-scheme.md"
  - "docs/adr/index.md"
  - "docs/ARCHITECTURE.md"
  - "docs/operational-reference.md"
  - "docs/spec-v1.md"
  - "docs/lessons.md"
  - "commands/claude-code/*.md"
  - "scripts/validate_architecture.py"
  - "scripts/dogfood_evaluate.py"
  - "tests/unit/*.py"
  - ".claude/features/*.yaml"
  - "CLAUDE.md"
  - "CHANGELOG.md"
out-of-scope:
  - "Slice ID renames (SLICE-NNN → hierarchical) — slice-and-feature-rename slice"
  - "Feature file slug renames — slice-and-feature-rename slice"
  - "Residual prose drift sweep — doc-sweep slice"
  - ".claude/completed-slices/** — frozen archive"
  - ".claude/sweep-results/** — historical outputs"
  - "docs/plans/**, .claude/plans/** — historical design artifacts"
  - "docs/reviews/** — historical review output"
  - "Removing legacy-format tolerance from hooks — Phase 3, deferred indefinitely per ADR identifier-scheme D7"
  - "Retiring sweep.yaml.current-slice-number — slice-and-feature-rename slice (after slice IDs are semantic)"
  - "Downstream consumer repo updates — consumer-grep surface, announced via CHANGELOG"
---

### What and Why

Execute Phase 2 Part 1 of ADR `identifier-scheme` D7's migration: rename the 9 numeric-prefix ADR files to flat-slug filenames, migrate each ADR's `id:` frontmatter from `ADR-NNN` to its flat semantic slug, and sweep every live cross-reference site in the same slice. The rename and the reference update ride together because renaming without updating references leaves the repo in a broken two-slice mid-state, and the references live in the same trees anyway. Phase 1's hook-tolerance + validator-flat-slug slices already widened enforcement to accept both formats; this slice flips the default to the new format.

### Specification Detail

**Rename table (mechanical, do not re-author slugs).** The new slug is the existing filename tail after the `NNN-` prefix, unchanged. Do not shorten, re-word, or stylistically edit.

| Old filename | Old `id:` | New filename | New `id:` |
|---|---|---|---|
| `docs/adr/001-bootstrap-exception.md` | `ADR-001` | `docs/adr/bootstrap-exception.md` | `bootstrap-exception` |
| `docs/adr/002-context-discipline-protocol.md` | `ADR-002` | `docs/adr/context-discipline-protocol.md` | `context-discipline-protocol` |
| `docs/adr/003-cliff-failure-mode-and-v1-defenses.md` | `ADR-003` | `docs/adr/cliff-failure-mode-and-v1-defenses.md` | `cliff-failure-mode-and-v1-defenses` |
| `docs/adr/004-phase-lock-and-role-declaration.md` | `ADR-004` | `docs/adr/phase-lock-and-role-declaration.md` | `phase-lock-and-role-declaration` |
| `docs/adr/005-semantic-identity.md` | `ADR-005` | `docs/adr/semantic-identity.md` | `semantic-identity` |
| `docs/adr/006-feature-slice-model.md` | `ADR-006` | `docs/adr/feature-slice-model.md` | `feature-slice-model` |
| `docs/adr/007-parallelism-v1.md` | `ADR-007` | `docs/adr/parallelism-v1.md` | `parallelism-v1` |
| `docs/adr/008-context-tiers-integration.md` | `ADR-008` | `docs/adr/context-tiers-integration.md` | `context-tiers-integration` |
| `docs/adr/009-phase-pipeline-evaluation.md` | `ADR-009` | `docs/adr/phase-pipeline-evaluation.md` | `phase-pipeline-evaluation` |

Already flat-slug (no rename, no frontmatter edit): `d3-bypass-classification.md`, `identifier-scheme.md`. Not an ADR (no rename): `index.md`.

**Rename mechanism.** `git mv <old> <new>` for each. History preservation is load-bearing — `git log --follow` must return the full history after the slice lands.

**Frontmatter migration per renamed ADR.** Edit three fields in order:
1. `id: ADR-NNN` → `id: <flat-slug>`
2. `supersedes:` — translate any `ADR-NNN` list items to `<flat-slug>` form
3. `supersedes-sections:`, `adrs-referenced:` — same translation

**ADR hook escape-hatch.** `reversibility-guard.sh` allows `Edit` on an ADR only when `old_string`'s first line begins with `status:`, `superseded-by:`, `superseded_by:`, or `firmness:`. Migrating `id:`, `supersedes:`, `supersedes-sections:`, `adrs-referenced:` is outside that allowlist. Use the `ADR_EDITORIAL_FIX=1` escape hatch for every such edit. Record each usage in `.claude/current-slice/implementation/notes.md` with the target file and edited field — the record is the audit trail for the one-shot migration exception.

**Cross-reference sweep (live-tree rewrites).** Two token-level substitutions across the files listed in the envelope:
- `ADR-NNN` → `<flat-slug>` (NNN and slug resolved via the rename table above)
- `docs/adr/NNN-<tail>.md` → `docs/adr/<tail>.md`

Apply across the live tree only. `docs/adr/index.md` is rebuilt as part of the sweep — every entry uses the flat-slug filename and id. Tests under `tests/unit/` may assert on `ADR-NNN` strings; update those assertions to flat-slug EXCEPT tests that verify hook/validator legacy-format tolerance (e.g., `test_hook_tolerance.py`) — those must continue asserting the legacy form accepts.

**CHANGELOG entry (mandatory).** Add a new entry in `CHANGELOG.md` under the current unreleased section with these exact pieces:
- Header: `ADR identifier migration (Phase 2 Part 1)`
- The full rename table above (9 rows)
- Consumer-impact paragraph: no mechanical breakage (hooks, commands, scripts paths unchanged); consumer docs citing cairn ADRs by numeric prefix won't mechanically break but will drift; recommend consumers run `rg 'ADR-00[1-9]'` in their own repos for their own grep-and-update pass. Name `complex-rag-analysis` as a known consumer.
- Cross-link back to ADR `identifier-scheme` D7 for the migration plan context.

### Boundary

Out of scope for this slice, listed in `out-of-scope` above. Key exclusions restated for emphasis:
- **Historical artifacts are frozen.** `.claude/completed-slices/`, `.claude/sweep-results/`, `docs/plans/`, `.claude/plans/`, `docs/reviews/` contain snapshots of prior state that should not be rewritten. Drift there is intentional — they record what was true at a point in time.
- **Slice and feature renames are the next slice** (`slice-and-feature-rename`). This slice does not touch `SLICE-NNN` identifiers in live files; those survive the sweep.
- **Consumer sweep is not cairn's job.** Downstream projects that symlink cairn must run their own grep pass; cairn announces the rename via CHANGELOG and stops there.

### Verification

1. `ls docs/adr/` returns exactly 12 files: 9 flat-slug renames + `d3-bypass-classification.md` + `identifier-scheme.md` + `index.md`. Zero files match `[0-9]*-*.md`.
2. For each renamed ADR, `head -2 <file> | grep ^id:` shows the flat-slug from the rename table (not `ADR-NNN`).
3. `git log --follow docs/adr/bootstrap-exception.md` shows the pre-rename history continuous with the rename commit (sample check for one; confirms `git mv` was used).
4. Live-tree grep returns zero hits:
   - `grep -rE 'ADR-00[0-9]' docs/ commands/ scripts/ tests/unit/ .claude/features/ CLAUDE.md CHANGELOG.md` (excluding explicitly-historical sections of `docs/lessons.md` if any).
   - `grep -rE 'docs/adr/00[0-9]' docs/ commands/ scripts/ tests/unit/ .claude/features/ CLAUDE.md CHANGELOG.md`.
5. `docs/adr/index.md` lists every ADR with flat-slug filename and flat-slug id; no numeric prefixes in body.
6. `CHANGELOG.md` contains the new migration entry: header text matches, rename table has all 9 rows, consumer-impact paragraph names `complex-rag-analysis`, link to ADR `identifier-scheme` D7 is present.
7. `uv run python scripts/validate_architecture.py` exits 0.
8. `uv run python -m pytest` passes fully.
9. `.claude/current-slice/implementation/notes.md` has an `ADR_EDITORIAL_FIX=1` audit trail listing every ADR edit that used the escape hatch, with file path and edited field.
10. Hook legacy-tolerance tests (`tests/unit/test_hook_tolerance.py`, `tests/unit/test_hook_relpath_bypass.py`) still pass — confirms we did not accidentally break the dual-format acceptance.
