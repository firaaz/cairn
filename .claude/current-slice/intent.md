---
slice: identifier-scheme/template-updates
date: 2026-04-17
phase: 1-intent
invariants-touched: []
adrs-referenced: [identifier-scheme]
envelope:
  - "CLAUDE.md"
  - "docs/operational-reference.md"
  - "commands/claude-code/start-slice.md"
  - "commands/claude-code/start-slice.full.md"
  - "commands/claude-code/new-adr.md"
  - "commands/claude-code/new-adr.full.md"
  - "commands/claude-code/handoff.md"
  - "commands/claude-code/handoff.full.md"
  - "commands/claude-code/decision.md"
  - "commands/claude-code/decision.full.md"
out-of-scope:
  - "No rename of any existing ADR, slice, or feature file (those are Phase 2 slices)"
  - "No edits to existing ADR frontmatter to add id:/name: (adr-rename-sweep)"
  - "No edits to existing slice/feature files to add name:/shaped-from: (slice-and-feature-rename)"
  - "No cross-reference sweep across prose/commands/scripts (doc-sweep)"
  - "No hook code, validator, or test changes (prior slices closed those)"
  - "No retirement of sweep.yaml.current-slice-number (Phase 2 action per ADR D7)"
  - "No writing of new ADRs or decision points"
  - "No change to scope-guard/reversibility-guard/reality-check regex or test coverage"
---

# Intent — identifier-scheme/template-updates

## What and Why

Update the command surfaces that spawn new ADRs, slices, features, decision points, and handoffs so they emit the ADR `identifier-scheme` two-field model (`id:` + `name:`) by default. After this slice, every new entity born from `/start-slice`, `/new-adr`, `/decision`, or `/handoff` conforms to the two-field scheme without operator recall. Also update `CLAUDE.md` (one-line prompt rule) and `docs/operational-reference.md` (operational elaboration) so the scheme is visible at prompt load and in the operational quick-reference.

This slice is the final substrate piece of ADR `identifier-scheme` §D7 Phase 1. Prior substrate — the governing ADR (`scheme-adr`), hook tolerance (`hook-tolerance`), hook relpath hardening (`hook-relpath-bypass`), and validator flat-slug recognition (`validator-flat-slug`) — has already landed. Templates are the last piece: until new entities auto-emit the scheme, Phase 2 rename-sweep slices would be contaminated by fresh entities still using the old convention.

## Specification Detail

**Slice template (start-slice.md + start-slice.full.md):**

- The `slice.yaml` YAML block gains a `name: "<human label>"` field. Placement is alongside `title:` or as its replacement; Phase 2 Skeptic resolves whether `title:` is retained as an alias, renamed to `name:`, or both. This slice's own slice.yaml uses `name:`.
- The `id:` field guidance documents the hierarchical form `<feature-id>/<slice-slug>` (per ADR D2) as the default for new slices. Legacy `SLICE-NNN` remains accepted by hooks during transition per ADR D7 Phase 1; guidance notes both coexist until the Phase 2 rename sweep.
- The intent `envelope` YAML block's `slice:` key documents hierarchical form as the default.
- Phase-gate tables and completion sequences update to show hierarchical slice IDs in their examples.

**Feature template (start-slice.md + start-slice.full.md "Feature file" block):**

- Feature YAML gains `name: "<human label>"` and `shaped-from: "<path-or-url-or-null>"` fields per ADR D5.
- `intent:` field retained as a short prose statement.
- Slice-list entry shape: each entry declares `id: <feature>/<slice-slug>` (hierarchical) and `added: <date>`. The `slice-yaml-id: SLICE-NNN` bridge field is documented as permitted during transition but not required for new entries whose slice.yaml already uses hierarchical `id:`.

**ADR template (new-adr.md + new-adr.full.md):**

- ADR frontmatter template gains `name: "<human label>"` per ADR D1.
- `id:` guidance: flat semantic slug per ADR D2 (e.g., `parallelism-v1`, not `007-parallelism-v1`). Versioning on supersession follows D3 (`-v1` → `-v2`).
- `supersedes:` and `adrs-referenced:` guidance: list items are target ADR `id:` values (e.g., `[feature-slice-model]`), not filenames and not numeric prefixes. Per D9.
- Decision-point guidance inside the ADR body: the hierarchical form `<adr-id>/<decision-slug>` is the canonical cross-ADR citation; bare `D1/D2/…` remains acceptable local shorthand within the same ADR.

**Handoff template (handoff.md + handoff.full.md):**

- The `## Features` section documents the normative one-line-per-feature format (per ADR D8): each active feature on one line using the feature's `name:` where available, with `id:` fallback, and a short status phrase. Prose within each line is author judgment; only the structural format is normative.
- The before/after examples in the template match ADR D8's worked examples.

**Decision command (decision.md + decision.full.md):**

- When `/decision` guides a new decision-point reference inside an ADR body or a cross-reference, the hierarchical form `<adr-id>/<decision-slug>` is documented as the default for cross-ADR citations. Bare `D1/D2/…` remains acceptable within the same ADR.
- Existing `D1/D2` references in prior ADRs are not rewritten by this slice.

**CLAUDE.md prompt rule:**

- A single sentence, injected at the prompt-rule level (top-of-file or in the existing safety-rules block), stating: every ADR, slice, feature, and decision point carries `id:` (immutable mechanical identifier) and `name:` (mutable human/LLM-facing label); prose uses `name:`, cross-references/filenames/hooks use `id:`. Full protocol lives in `docs/adr/identifier-scheme.md` and `docs/operational-reference.md` — not re-stated in `CLAUDE.md`.

**docs/operational-reference.md elaboration:**

- A new subsection (or extension of the existing identity-related section) covering the two-field model operationally: per-entity table from ADR D2 (ADR/decision-point/slice/feature → `id:` shape → hierarchy), where `name:` is written (frontmatter slot, not reach-into-prose), and the `shaped-from:` feature convention (D5).
- Single section, quick-reference tone. Theory stays in the ADR.

## Boundary

Out of scope for this slice:

- Editing any existing ADR file, slice.yaml, or feature file to add `id:` / `name:` / `shaped-from:`. Those are the `adr-rename-sweep` and `slice-and-feature-rename` slices.
- Renaming any file on disk. Rename sweeps are Phase 2.
- Cross-reference sweeps across docs/, commands/, scripts/, or prose. That is `doc-sweep`.
- Retiring `.claude/sweep.yaml.current-slice-number`. That is a rename-sweep cleanup per ADR D7 Phase 2.
- Hook code, validator code, or test-file edits. All closed by prior slices.
- Writing or superseding ADRs. This slice is template/docs only.
- Resolving whether `title:` in slice.yaml is renamed to `name:` or aliased. Phase 2 Skeptic decides.

## Verification

1. `commands/claude-code/start-slice.md` and `start-slice.full.md`: the `slice.yaml` YAML block shows `name: "<human label>"`; the `id:` guidance text names hierarchical `<feature-id>/<slice-slug>` form as the default for new slices; legacy `SLICE-NNN` is documented as accepted during transition.
2. start-slice.md and start-slice.full.md Feature-file blocks show `name:` and `shaped-from:` fields in the YAML template and describe the slice-list entry shape with hierarchical `id:`.
3. `commands/claude-code/new-adr.md` and `new-adr.full.md`: the ADR frontmatter template contains `name:`; `id:` guidance names flat-slug form; `supersedes:`/`adrs-referenced:` guidance names `id:`-values-not-filenames.
4. `commands/claude-code/handoff.md` and `handoff.full.md`: the `## Features` section contains the normative one-line-per-feature format with an example matching ADR D8.
5. `commands/claude-code/decision.md` and `decision.full.md`: decision-point guidance names hierarchical `<adr-id>/<decision-slug>` form as the cross-ADR citation default.
6. `CLAUDE.md` contains a single sentence asserting the two-field model at prompt level; the sentence uses the words `id:` and `name:`; a pointer exists to `docs/adr/identifier-scheme.md` or `docs/operational-reference.md` for the full protocol.
7. `docs/operational-reference.md` contains a subsection with the per-entity `id:`-shape table from ADR D2 and text describing `name:` as a frontmatter slot (not prose-reach) and `shaped-from:` as the feature-provenance field.
8. No file outside the declared envelope is modified. The structural-snapshot diff at Phase 4 close reports no out-of-envelope changes.
9. No existing ADR file's frontmatter is modified, no existing slice.yaml is edited beyond this slice's own, and no existing feature file slice-entry data is altered (only an append for this slice is permitted).
10. No test file is added or modified; the full test suite continues to pass.
11. `validate_architecture.py` (D1) passes at Phase 4 close; no invariant is claimed as touched.
12. The `/start-slice` skill's Step 4 guidance, when read after this slice lands, would produce a fresh slice.yaml containing `name:` and hierarchical `id:` — the template is self-consistent with what this slice itself produced.
