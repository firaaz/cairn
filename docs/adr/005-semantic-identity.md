---
id: ADR-005
title: Semantic Identity for Slices and ADRs
status: superseded
firmness: firm
supersedes: []
supersedes-sections: []
superseded-by: identifier-scheme
topic: naming
invariants-touched: []
date: 2026-04-12
---

# ADR-005: Semantic Identity for Slices and ADRs

## Status
Accepted

## Date
2026-04-12

## Context

Cairn's current naming convention uses sequential numeric prefixes for both slices (SLICE-001, SLICE-002) and ADRs (ADR-001, ADR-002). This convention was inherited from early bootstrapping (ADR-001) and never revisited.

Sequential numbering creates three concrete problems:

1. **Multi-developer collision.** A global counter requires coordination to increment. Two developers starting slices concurrently must negotiate who gets the next number, or risk collisions that require renaming after the fact. The same applies to ADRs written in parallel `/decision` sessions.

2. **Semantic opacity.** `SLICE-003` communicates nothing about what the slice does. Developers working across features must open `slice.yaml` or `intent.md` to identify a slice's purpose. In `handoff.md` and feature files, numeric IDs add a lookup cost at every reference.

3. **ADR cross-reference fragility.** ADR frontmatter fields like `supersedes` and `adrs-referenced` use numeric IDs. When ADRs are renumbered (e.g., to fill gaps left by rejected drafts), every cross-reference breaks. Semantic IDs are stable across reordering.

The feature-slice model design (approved 2026-04-12) adopts semantic kebab-case IDs as a foundational element. This ADR formalizes the naming convention so that downstream implementation slices — ADR renaming, feature file creation, hook updates — have a committed specification to build against.

## Decision

### D0 — Semantic kebab-case IDs replace sequential numbering

All slices and ADRs use kebab-case semantic identifiers. Examples:

- Slices: `context-discipline`, `token-refresh-fix`, `adr-rename`
- ADRs: `bootstrap-exception`, `cliff-failure-mode`, `semantic-identity`

No numeric prefix is required. Existing ADRs retain their numeric prefixes until an implementation slice renames them (see D3 migration path below). New ADRs created after this ADR lands use semantic IDs without numeric prefixes.

### D1 — Collision avoidance via semantic uniqueness

Semantic names are naturally unique across concurrent work because they describe different things. Two developers working on unrelated features will not independently choose the same kebab-case ID.

If a collision does occur (e.g., two ADRs both named `auth-redesign`), the second author appends a disambiguating suffix (e.g., `auth-redesign-token-store` vs. `auth-redesign-session-model`). No registry or locking mechanism is introduced; the cost of occasional suffix addition is lower than the cost of maintaining a global counter.

### D2 — Cross-reference format

Cross-references in YAML fields (`adrs-referenced`, `supersedes`, `supersedes-sections`) use the ADR's `id` frontmatter field value. Example: `adrs-referenced: [semantic-identity, cliff-failure-mode]`.

File references in prose use the filename stem: `docs/adr/semantic-identity.md`. The `id` field and filename stem must be consistent — the filename is the kebab-case form of the ID with an optional numeric prefix for pre-migration ADRs.

### D3 — Migration path for existing ADRs

Existing ADRs (001 through 004, plus any created before this ADR's implementation slice lands) are renamed from `NNN-slug.md` to `slug.md` in a dedicated implementation slice. The migration slice:

- Renames each file
- Updates all cross-references in ADR frontmatter and prose
- Updates `docs/adr/index.md`
- Updates `docs/ARCHITECTURE.md` references via `/refresh-architecture`

Until the migration slice lands, existing ADRs keep their numeric prefixes and both naming conventions coexist.

### D4 — Hook and guard updates

`reversibility-guard.sh` currently uses the glob pattern `*/docs/adr/[0-9]*` to match ADR files. After migration, this changes to `*/docs/adr/*.md` with `index.md` explicitly excluded from write-blocking (index updates are allowed).

`scope-guard.sh` pattern matching for slice IDs is updated to accept kebab-case identifiers in addition to the existing `SLICE-NNN` format. Both formats are accepted during the transition period; the `SLICE-NNN` format is removed after all existing slices complete.

### D5 — Slice ID format

Slice IDs in `slice.yaml` and feature files use kebab-case: `id: context-discipline`. The `SLICE-NNN` format is deprecated. New slices created after this ADR's implementation slice lands must use kebab-case IDs.

## Consequences

- **Downstream implementation slices have a committed spec.** The ADR rename slice, feature file creation slice, and hook update slices all reference this ADR via the D3 gate.

- **Parallel work is unblocked.** Developers can create slices and ADRs without coordinating on a global counter.

- **Handoff and feature files become self-documenting.** `after: [adr-rename]` communicates more than `after: [SLICE-007]`.

- **Transition period requires tolerance of both formats.** Until the migration slice lands, the codebase contains both `003-cliff-failure-mode-and-v1-defenses.md` and any new semantic-only ADRs. Tools and hooks must accept both during this window.

- **ADR-004 INV-003 is unaffected.** The four-phase pipeline lock references phase names, not slice IDs. Phase names remain unchanged.
