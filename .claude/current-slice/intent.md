---
slice: identifier-scheme/scheme-adr
slice-yaml-id: SLICE-015
date: 2026-04-15
phase: 1-intent
invariants-touched: []
adrs-referenced: [ADR-005]
adrs-created: [identifier-scheme]
envelope:
  - "docs/adr/identifier-scheme.md"
  - "docs/adr/005-semantic-identity.md"
  - "docs/adr/index.md"
out-of-scope:
  - "Hook updates (scope-guard.sh, reversibility-guard.sh, reality-check.sh) — covered by identifier-scheme/hook-tolerance"
  - "Template updates (slice/ADR/feature/handoff) — covered by identifier-scheme/template-updates"
  - "CLAUDE.md prompt-rule line — covered by identifier-scheme/template-updates"
  - "operational-reference.md elaboration — covered by identifier-scheme/template-updates"
  - "Renaming existing ADR files, slices, decision points, features"
  - "Cross-reference sweep across docs/, commands/, scripts/, .claude/"
  - "Retiring sweep.yaml.current-slice-number"
  - "State taxonomy (Feature 1c — separate feature)"
---

## What and Why

Author the governing ADR `identifier-scheme` that defines a two-field (`id:` + `name:`) identity model for ADRs, decision points, slices, and features. The ADR supersedes ADR-005 (Semantic Identity for Slices and ADRs), which committed to single-field semantic IDs without distinguishing the immutable mechanical identifier from the mutable human/LLM-facing label. ADR-005 also lacked a treatment of decision points and features, both of which now exist as first-class entities (ADR-006, ADR-007 D-prefix decisions). This slice is pure ADR authorship — no source, no renames, no hook touches. It establishes the spec that subsequent migration slices implement.

## Specification Detail

**ADR identity (`id:` field of new ADR):** `identifier-scheme`. Filename: `docs/adr/identifier-scheme.md`. This slice writes a flat-slug filename even though hook tolerance for that pattern lands in `identifier-scheme/hook-tolerance`. The `Write` is permitted not because `reversibility-guard.sh` has a special new-file allow path, but because its ADR clauses (`reversibility-guard.sh:51,68`) match only the glob `*/docs/adr/[0-9]*` — `identifier-scheme.md` doesn't start with a digit, so the glob doesn't match and execution falls through to the default `exit 0`. **Bootstrap-window gap:** for the same reason, future `Edit` (body) and `Write` (overwrite) of `docs/adr/identifier-scheme.md` are also unprotected by the append-only invariant until `identifier-scheme/hook-tolerance` widens the glob. This slice creates the gap; the next slice closes it. Ordering recorded in `.claude/features/identifier-scheme.yaml`.

**Frontmatter the new ADR must carry:** `id: identifier-scheme`, `name: "Identifier scheme — id + name two-field model"`, `status: accepted`, `firmness: firm`, `supersedes: [ADR-005]`, `supersedes-sections: []`, `superseded-by: null`, `topic: naming`, `invariants-touched: []`, `date: 2026-04-15`. The `supersedes:` field uses the existing-format ID `ADR-005` (renaming to flat slug is a later slice's job; this slice does not retroactively rewrite ADR-005's `id:` field).

**Body content the new ADR must commit to (each section is a definition-of-done item, not a writing prompt):**

1. **Two-field schema** — `id:` immutable mechanical identifier, `name:` mutable human/LLM-facing label. State the rule that prose raises `name:` and cross-refs/filenames/hooks raise `id:`. Justify why two fields beat reaching into `title:`/`intent:`.
2. **ID shape per entity type** — table covering ADR (flat semantic slug, versioned on supersession: `parallelism-v1`, `feature-slice-model`, `identifier-scheme`), decision point (hierarchical `<adr-id>/<decision-slug>`), slice (hierarchical `<feature-id>/<slice-slug>`), feature (flat semantic slug). Justify hierarchy where used (self-identifying cross-refs, namespace collision avoidance) and flatness where used (no natural parent for ADRs/features).
3. **Versioning on supersession** — `parallelism-v2` replaces `parallelism-v1`; old IDs freeze with the superseded ADR; new ADR re-states decisions under its own namespace. Decisions survive across ADR states via amendment (cite ADR-007 amending ADR-003 D4 as worked example).
4. **Slice branch naming** — `slice/<feature>/<slice>` equals `slice/<slice-id>`. Git handles nested refs natively.
5. **Feature metadata** — `id:`, `name:`, `intent:`, `shaped-from:` (single string; path or URL; ticketing-system-agnostic). Explicit rejection of an `epic:` field or `.claude/epics/` entity (Shape Up shape, not Scrum; grouping is a grep query, not a first-class concept).
6. **`name:` style** — convention only, no lint. Short, sentence or title case by author judgment, no trailing punctuation. Total YAML size check is the only structural enforcement.
7. **Migration shape, three-phase** — Phase 1 (schema + hook tolerance + templates + CLAUDE.md/operational-reference; no renames), Phase 2 (one-shot rename sweep across ADRs/slices/decision points/features + cross-ref sweep + retire `sweep.yaml.current-slice-number`), Phase 3 (drop legacy-format tolerance — deferred indefinitely; cost ≈5 regex lines, benefit purely aesthetic). Migration shape is normative; per-slice envelope decisions are not.
8. **Open questions resolved in this ADR (not deferred to implementation):**
   - Hard-rename ADR files in Phase 2 with no legacy symlinks (rejected: symlink retention).
   - Slice frontmatter does not gain a `supersedes:` field; `git mv` is sufficient record for renames.
   - Handoff cross-feature index: provide one before/after example in the ADR body.
9. **Cross-reference format** — within ADR frontmatter (`adrs-referenced`, `supersedes`, `supersedes-sections`) use the target ADR's `id:` value. File references in prose use `docs/adr/<id>.md`. ADR-005's D2 stays in spirit; the ADR re-states it under the new model rather than reaching back.
10. **Consequences** — name the migration's blast radius (every cross-ref site touched in Phase 2), the **bootstrap-window gap** (precisely: `reversibility-guard.sh:51,68` glob `*/docs/adr/[0-9]*` does not match flat-slug filenames, so `docs/adr/identifier-scheme.md` is unprotected by the ADR append-only enforcement from this slice's close until `identifier-scheme/hook-tolerance` widens the glob; the constraint that hook-tolerance is the immediately-next slice in this feature is recorded in the feature file), the rejected alternatives (hash-suffixed IDs, date-prefixed IDs, epic entities as first-class), and the deferred work (state taxonomy / Feature 1c, Phase 3 of migration).

**ADR-005 update (envelope: `docs/adr/005-semantic-identity.md`):** frontmatter-only edit per `reversibility-guard.sh` rules. Set `status: superseded` and `superseded-by: identifier-scheme`. No body edits — ADR-005 is preserved as the prior commitment record.

**`docs/adr/index.md` update (envelope: `docs/adr/index.md`):** add the new ADR entry; mark ADR-005 as superseded in the index format the file already uses. Index format is whatever the file currently uses — this slice does not redesign the index.

## Boundary

- **No hook code changes.** `scope-guard.sh`, `reversibility-guard.sh`, `reality-check.sh` are untouched. The next slice (`identifier-scheme/hook-tolerance`) handles those.
- **No template files updated.** Slice template, ADR template, feature template, handoff template — all untouched.
- **No `CLAUDE.md` edits.** The prompt-rule line is `identifier-scheme/template-updates` scope.
- **No `docs/operational-reference.md` edits.** Same slice as above.
- **No rename of any existing entity** — ADR files keep `NNN-slug.md` form, slice IDs remain `SLICE-NNN`, decision points remain `D1`/`D2`/…, feature files keep current shape. Phase 2 rename sweep is later slices.
- **No `sweep.yaml.current-slice-number` retirement.** Keeps incrementing through this feature's slices; retired by a Phase 2 slice.
- **No state taxonomy** — Feature 1c, separate feature, deferred until fleet-coordinator Feature 2 needs it.
- **No `docs/ARCHITECTURE.md` regeneration in this slice.** Phase 4 D1 gate runs `/refresh-architecture` which will pick up the new ADR; that is part of close, not implementation.
- **Bootstrap-window ordering constraint.** This slice intentionally creates a gap: `docs/adr/identifier-scheme.md` is unprotected by `reversibility-guard.sh`'s ADR append-only clauses (glob mismatch — see Specification Detail). `identifier-scheme/hook-tolerance` MUST be the immediately-next slice in this feature; no other flat-slug ADRs may be authored in between. Constraint recorded as the next-listed slice with `after: identifier-scheme/scheme-adr` in `.claude/features/identifier-scheme.yaml`.

## Verification

1. `docs/adr/identifier-scheme.md` exists with the frontmatter listed in Specification Detail above (all fields present, `id` value is `identifier-scheme`, `supersedes` is `[ADR-005]`).
2. The ADR body covers all ten sections enumerated in Specification Detail. Each section makes a normative commitment, not a discussion. Spot-check by grep:
   - body contains a table with rows for ADR, Decision point, Slice, Feature
   - body contains the strings `parallelism-v1`, `parallelism-v2` (supersession-versioning worked example)
   - body contains the strings `shaped-from`, `epic` (the rejection)
   - body contains a Phase 1 / Phase 2 / Phase 3 migration breakdown
3. `docs/adr/005-semantic-identity.md` frontmatter has `status: superseded` and `superseded-by: identifier-scheme`. Body unchanged (`git diff --stat` shows only frontmatter delta on this file).
4. `docs/adr/index.md` lists the new ADR and marks ADR-005 as superseded.
5. `python3 -m pytest` passes (full suite, no regressions — this slice should not affect any test).
6. `python3 .slice-system/scripts/validate_architecture.py` passes (D1 gate). New ADR loads cleanly into the architecture refresh.
7. No files outside the envelope are modified (`git status --short` against the slice envelope confirms clean — checked by Phase 4 snapshot diff).
