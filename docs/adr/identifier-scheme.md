---
id: identifier-scheme
name: "Identifier scheme — id + name two-field model"
status: accepted
firmness: firm
supersedes: [semantic-identity]
supersedes-sections: []
superseded-by: null
topic: naming
invariants-touched: []
date: 2026-04-15
---

# Identifier scheme — id + name two-field model

## Status
Accepted. Supersedes semantic-identity.

## Date
2026-04-15

## Context

semantic-identity (Semantic Identity for Slices and ADRs) committed to a single semantic identifier per entity: one kebab-case string serving as both the immutable cross-reference key and the human-facing label. That single-field model has since proven inadequate on three counts:

1. **Conflation of mechanical and human concerns.** The same string must remain stable for hooks, glob patterns, and `adrs-referenced` lists *and* must read well for humans skimming `handoff.md`. These two forces pull in opposite directions: cross-reference stability rewards short opaque slugs that never change; human readability rewards descriptive phrases that may be revised as the team's understanding sharpens. A single field cannot serve both without one role degrading the other.

2. **Reach-into-prose anti-pattern.** Without a dedicated label field, callers wanting a readable name reach into `title:` (ADRs) or `intent:` (slices/features). Those fields were never specified as the canonical label — they're documentation prose — and the implicit promotion creates silent coupling: editing the title to clarify a thought breaks anything that grepped for it as a name.

3. **Decision points and features absent from the model.** semantic-identity addressed slices and ADRs only. Decision points (introduced as parallelism-v1 D-prefix entities) and features (feature-slice-model) now exist as first-class entities with their own cross-reference needs. semantic-identity has no opinion on either, so each entity type was inventing its own conventions.

This ADR introduces a two-field identity model — `id:` (immutable mechanical) plus `name:` (mutable human/LLM-facing) — and extends coverage to all four current entity types: ADRs, decision points, slices, features.

## Decision

### D1 — Two-field schema

Every cross-referenceable entity carries two identity fields:

- **`id:`** — immutable mechanical identifier. Stable across the entity's lifetime. Used by hooks, cross-references in YAML frontmatter, glob patterns, filenames, slice branch names, and any tooling that needs to find one entity from another.
- **`name:`** — mutable human/LLM-facing label. Free to be revised as understanding sharpens. Used in prose, `handoff.md` summaries, index entries, and anywhere a reader benefits from a descriptive phrase.

**The rule:** prose raises `name:`; cross-references, filenames, and hooks raise `id:`. If you are writing a sentence about an entity, use its `name:`. If you are pointing one entity at another or telling a tool how to find it, use its `id:`.

Two fields beat reaching into `title:` or `intent:` because both fields are explicitly named identity slots. Editing prose can never accidentally break a cross-reference; conversely, renaming an entity's mechanical identifier (a heavy operation requiring a sweep) is clearly distinct from polishing its label.

### D2 — ID shape per entity type

| Entity | `id:` shape | Example | Hierarchy? |
|--------|-------------|---------|------------|
| ADR | flat semantic slug; versioned on supersession | `parallelism-v1`, `feature-slice-model`, `identifier-scheme` | no |
| Decision point | hierarchical: `<adr-id>/<decision-slug>` | `parallelism-v1/d4-time-box`, `identifier-scheme/d2-id-shape` | yes |
| Slice | hierarchical: `<feature-id>/<slice-slug>` | `identifier-scheme/scheme-adr`, `identifier-scheme/hook-tolerance` | yes |
| Feature | flat semantic slug | `identifier-scheme`, `v1-defense-d2`, `fleet-coordinator` | no |

**Why hierarchy where used.** Decision points and slices have a natural parent (ADR and feature, respectively). Hierarchical IDs are self-identifying at a glance — `identifier-scheme/hook-tolerance` tells a reader the feature without a lookup, and avoids namespace collisions across features (two features can each have a `hook-tolerance` slice without disambiguation).

**Why flat where used.** ADRs and features have no natural parent within the project. Adding a synthetic prefix would create a fake hierarchy that consumers must learn and maintain. The flat slug is sufficient because the entity type is implicit from the directory the file lives in (`docs/adr/` for ADRs, `.claude/features/` for features).

### D3 — Versioning on supersession

When an ADR is superseded by a new ADR that re-decides on the same topic, the new ADR's `id:` carries an explicit version suffix and the old ADR's `id:` freezes:

- `parallelism-v1` → `parallelism-v2`
- Old IDs are never reused; they remain in the superseded ADR's frontmatter forever.
- The new ADR re-states the decisions it carries forward under its own `id:` namespace; cross-references that should follow the new commitment are updated to point at `parallelism-v2`.

**Decisions survive across ADR states via amendment.** A decision recorded in one ADR can be amended by a later ADR without superseding the whole parent. parallelism-v1 amending cliff-failure-mode-and-v1-defenses D4 is the worked example: parallelism-v1 took D4's time-box scope and refined it, but cliff-failure-mode-and-v1-defenses remained `accepted` because its other decisions (D1–D3) were not touched. The amended decision is identified by the original ADR's `id:` plus the decision slug — no version suffix is needed at the decision level because the amending ADR explicitly states which prior decision it amends.

Versioning at the ADR level is the only versioning. Slices, features, and decision points do not version — they get superseded by deletion (slice marked failed, feature retired) or by direct edit of the parent ADR.

### D4 — Slice branch naming

Slice branches use the slice's full hierarchical `id:` directly:

```
slice/<feature>/<slice>   ==   slice/<slice-id>
```

Example: `slice/identifier-scheme/scheme-adr`. Git handles nested ref names natively, so no flattening or substitution is needed. The branch name is mechanically derivable from `slice.yaml`'s `id:` field and round-trips losslessly.

### D5 — Feature metadata

Feature files carry these identity and provenance fields:

- **`id:`** — flat semantic slug, per D2.
- **`name:`** — human-facing label, per D1.
- **`intent:`** — short prose statement of what the feature delivers (the why and the boundary).
- **`shaped-from:`** — single string. Path or URL pointing at the design artifact this feature is shaped from. May be a local path (`docs/plans/2026-04-15-fleet-coordinator-design.md`) or an external link (Notion, Linear, Shape Up pitch). Ticketing-system-agnostic by design.

**Explicit rejection of an `epic:` field or `.claude/epics/` entity.** Cairn's planning model is Shape Up shaping, not Scrum epics. Features are the unit of shaping; grouping multiple features under a parent is a grep query (`shaped-from:` value or a tag in `name:`), not a first-class concept. Adding an epic entity would introduce a layer with no decisions of its own, no envelope, and no lifecycle — pure organizational cruft.

### D6 — `name:` style

The `name:` field follows convention only — there is no lint, no schema validator that enforces capitalization or punctuation. The conventions:

- Short — fits comfortably on a single line in `handoff.md` or an index table.
- Sentence case or title case by author judgment. Either is acceptable; consistency within an entity type is preferred but not enforced.
- No trailing punctuation (no period, no exclamation point).
- May contain spaces, em-dashes, and any printable character. Not constrained to kebab-case.

The only structural enforcement is the standing total-YAML-size check that catches any frontmatter field growing unreasonably large. If `name:` is short enough to fit a `handoff.md` line, it passes.

### D7 — Migration shape (three-phase, normative)

The transition from the semantic-identity single-field model to this ADR's two-field model is structured into three phases. The phase shape is normative; the per-slice envelope decisions inside each phase are not (subsequent slices may split or merge work as appropriate).

- **Phase 1 — additive, no renames.**
  - Schema: introduce `name:` field on all entity templates (ADR, slice, feature, decision-point references in ADR frontmatter).
  - Hook tolerance: widen `reversibility-guard.sh:51,68` glob to match flat-slug ADR filenames; widen `scope-guard.sh` slice-ID matching to accept hierarchical IDs alongside legacy `SLICE-NNN`.
  - Templates: update slice template, ADR template, feature template, handoff template to include `name:` and emit hierarchical IDs for new entities.
  - `CLAUDE.md` and `docs/operational-reference.md`: add the prompt-rule line and operational guidance for the two-field model.
  - **No file renames in Phase 1.** Existing `NNN-slug.md` ADRs keep their filenames. Existing `SLICE-NNN` IDs keep their format. Both old and new conventions coexist.

- **Phase 2 — one-shot rename sweep.**
  - Rename ADR files from `NNN-slug.md` to `<id>.md` per D2's flat-slug rule.
  - Rename slices from `SLICE-NNN` to hierarchical `<feature>/<slice>` IDs.
  - Rename decision points to `<adr-id>/<decision-slug>` form in any place they're referenced.
  - Rename features to flat semantic slugs (most already are).
  - Cross-reference sweep across `docs/`, `commands/`, `scripts/`, `.claude/`. Every site touched.
  - Retire `sweep.yaml.current-slice-number` (no longer needed once slice IDs are semantic).
  - This phase is one-shot precisely because it is the cross-cutting one: doing it incrementally would mean maintaining the two-format tolerance across many small slices, each of which adds risk of partial rename leaving stale references.

- **Phase 3 — drop legacy-format tolerance.**
  - Remove the regex branches in hooks that accept `SLICE-NNN` and `NNN-slug.md` formats.
  - **Deferred indefinitely.** Cost is approximately five regex lines across the three hook scripts. Benefit is purely aesthetic — the legacy tolerance is dead code once Phase 2 lands, but harmless. There is no operational pressure to do Phase 3, and doing it commits the team to never accepting a contributor's PR that uses the old format. The deferral is recorded here so future readers don't waste time scoping it.

### D8 — Open questions resolved in this ADR

The following questions were raised during the design phase and are resolved here, not deferred to implementation:

- **Hard-rename ADR files in Phase 2 with no legacy symlinks.** Resolution: hard rename, no symlinks. Symlink retention was rejected because it would leak the old format into directory listings indefinitely and require a dedicated "remove symlinks" slice that nobody would ever prioritize. Git history preserves the rename via `git mv`; that is sufficient for archaeological lookup.

- **Slice frontmatter does not gain a `supersedes:` field.** Resolution: `git mv` plus the commit message recording the rename is sufficient. Slices, unlike ADRs, are short-lived working units; cross-references to a renamed slice are rare and easily found by `git log --follow`. Adding `supersedes:` to slice frontmatter would imply slices have the same lifecycle weight as ADRs, which they do not.

- **Handoff cross-feature index format.** Resolution: the `## Features` section in `.claude/handoff.md` lists each active feature on one line, with the latest slice-id and a one-sentence status. Before/after example:

  Before (single-feature, semantic-identity era):
  ```
  ## Features
  - identifier-scheme: design committed, no slices yet (first: scheme-adr)
  ```

  After (cross-feature index, this ADR's model):
  ```
  ## Features
  - identifier-scheme: `identifier-scheme/scheme-adr` Phase 2→3 (scheme-adr); hook-tolerance scheduled next; 4 design-illustrative slices remaining per design §8.
  - v1-defense-d2: complete (`v1-defense-d2/code-invariant-binding`, `v1-defense-d2/assertion-block-migration`).
  - v1-defense-d3: complete (`v1-defense-d3/automated-backstop`, the failed ruff-cleanup attempt).
  ```

  The format is normative; the prose inside each line is author judgment.

### D9 — Cross-reference format

Within ADR frontmatter, fields that point at other ADRs (`adrs-referenced`, `supersedes`, `supersedes-sections`) carry the target ADR's `id:` value as a list item. Example: `adrs-referenced: [feature-slice-model, parallelism-v1]`.

File references in prose use `docs/adr/<id>.md`. Example: `see docs/adr/feature-slice-model.md § D3`.

semantic-identity's D2 (cross-reference format) stays in spirit — references use the `id:` field, not the filename — but is re-stated here under the two-field model rather than being inherited by reference. The new ADR is the canonical statement; semantic-identity's body remains as the prior commitment record but is no longer the source of truth for cross-reference semantics.

## Consequences

**Migration blast radius.** Every cross-reference site in the repository is touched in Phase 2: ADR `adrs-referenced` fields, ADR `supersedes` fields, prose references in `docs/`, slice references in `.claude/handoff.md` and feature files, hook glob patterns and regexes in `checks/*.sh`, slash-command surface in `commands/claude-code/`, and any scripts in `scripts/` that pattern-match identifiers. Phase 2 is one slice precisely because the cross-cutting nature makes incremental work hazardous — leaving a partial rename behind leaves stale references that won't fail loudly.

**Bootstrap-window gap (load-bearing for this slice's close).** `reversibility-guard.sh:51,68` matches ADR files with the glob `*/docs/adr/[0-9]*` — only filenames whose first character is a digit. The new ADR `docs/adr/identifier-scheme.md` does not start with a digit, so the glob does not match and the hook falls through to the default `exit 0`. The practical consequence: from this slice's close until `identifier-scheme/hook-tolerance` widens the glob, `docs/adr/identifier-scheme.md` is unprotected by the ADR append-only enforcement. Both `Edit` (body changes outside the frontmatter-only allow path) and `Write` (overwrite) of this file would currently be permitted by the hook. The risk is bounded by the constraint recorded in `.claude/features/identifier-scheme.yaml`: `identifier-scheme/hook-tolerance` MUST be the immediately-next slice in this feature, and no other flat-slug ADRs may be authored in the bootstrap window. The next slice's first verification step closes the gap.

**Rejected alternatives.**

- **Hash-suffixed IDs** (`auth-redesign-a3f9`). Rejected: a hash is unreadable, defeats the human-facing benefit of semantic IDs, and solves a collision problem (D1 of semantic-identity) that doesn't exist in practice — semantic names are naturally unique because they describe different things.
- **Date-prefixed IDs** (`2026-04-15-identifier-scheme`). Rejected: date prefixes leak a creation-time accident into the cross-reference key, force renames if the file is committed late, and create false ordering signal (a date-prefixed ID looks like it should sort meaningfully, but ADRs are read by `id:` not by date).
- **Epic entities as first-class** (`.claude/epics/`). Rejected: see D5. Shape Up planning model has no epic concept; grouping is a query, not an entity.

**Deferred work.**

- **State taxonomy** (Feature 1c in the fleet-coordinator design). Deferred until fleet-coordinator Feature 2 needs it. Not blocked by this ADR.
- **Phase 3 of migration** (drop legacy-format tolerance). Deferred indefinitely; see D7.

**Unaffected.**

- phase-lock-and-role-declaration INV-003 (four-phase pipeline lock) is unchanged. Phase names are not entity IDs.
- Existing slice envelopes and ongoing work are not affected — Phase 1 of migration is purely additive, and renames don't happen until Phase 2.
