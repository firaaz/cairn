# Identifier Scheme — Design

**Feature:** `identifier-scheme`
**Shaped from:** `docs/plans/2026-04-15-fleet-coordinator-design.md` § Feature 1 (prerequisite)
**Status:** design complete, pending first slice
**Date:** 2026-04-15

## 1. Context

The fleet-coordinator epic names "Identifier, naming, and state taxonomy overhaul" as its blocking prerequisite. Brainstorming (this session, 2026-04-15) re-scoped that lumped feature. The original Feature 1 bundled five concerns: slice IDs, ADR IDs, decision-point IDs, feature IDs, and state taxonomy. Three are **mechanical identifier** concerns (how scripts/hooks/grep address an entity); one is a **human/LLM comprehension** concern (how entities are raised in prose); one is a **behavioral model** concern (slice state transitions, which the harness needs).

These are different audiences, different failure modes, different migrations. Lumping them invites one big rename slice with two concerns attached; splitting them by intent lets each land on its own merits.

**Cleavage:**

- **1a — ID scheme.** Mechanical, for cross-refs, hooks, filenames, branches.
- **1b — Naming convention.** Human + LLM-facing, the short citable labels raised in prose.
- **1c — State taxonomy.** Slice states, transitions, autonomous-vs-gated classification. Needed by fleet-coordinator Feature 2 (phase automation ADR).

**Filing decision (D):** combine 1a + 1b as this feature (`identifier-scheme`) because they share migration/sweep machinery and every internal decision touches both. Defer 1c to its own feature when Feature 2 actually needs it. Serial execution — parallelism is technically blessed by ADR-007 but practically unexercised; the identifier migration's high churn would create brutal merges on any concurrent branch.

## 2. Scope

**In scope:**

- New ADR defining the ID + Name schema, superseding ADR-005.
- Hook tolerance for the new formats (`scope-guard.sh`, `reversibility-guard.sh`, `reality-check.sh`).
- Template updates (slice, ADR, handoff, feature, decision commands).
- `CLAUDE.md` edit surfacing the "raise names, not IDs in prose" rule.
- `docs/operational-reference.md` elaboration of the rule and style conventions.
- One-shot rename of existing ADRs (001–009), slices (SLICE-001 through SLICE-014), decision points, and feature files.
- Cross-reference sweep across `docs/`, `CLAUDE.md`, `commands/`, `scripts/`, `.claude/`.
- Retirement of `.claude/sweep.yaml.current-slice-number` (semantic IDs need no counter).

**Out of scope (deferred):**

- State taxonomy (Feature 1c, future feature).
- Dropping legacy-format tolerance from hooks (Phase 3, indefinitely deferred — pure aesthetics, historical artifacts reference old form).
- Hash-suffixed IDs, date-prefixed IDs, epic entities as first-class — explicitly rejected.

## 3. Core schema principle

Every entity carries **two distinct YAML fields**:

```yaml
id: parallelism-v1                         # immutable mechanical identifier
name: "ADR-007 parallelism, first pass"    # human/LLM-facing label
```

- **`id:`** — immutable after creation. Stable in cross-refs, hooks, filenames, branches. Changing it means superseding the entity.
- **`name:`** — mutable uniformly across all entity types. Proper YAML field (not reach into `title:` or `intent:`). Change history captured by git log; no separate `name-history:` list.
- **Shape constraint on `name:`** — convention only (style guide in `docs/operational-reference.md`). No lint. Total YAML size check suffices.

**Why two fields:** IDs are mechanical and need stability; names need to evolve as scope narrows or framing shifts without breaking cross-refs. "According to D1 <something>" is opaque; "according to parallelism-v1 / no-global-pointer <something>" is readable.

**Why not reach into `title:`/`intent:`:** prose fields have different purposes (title can be longer, intent is a paragraph). A dedicated `name:` field is short, citable, and parseable without ambiguity about which string is "the name."

## 4. ID shape per entity type

| Entity | Shape | Example |
|---|---|---|
| **ADR** | Flat semantic slug, versioned on supersession | `parallelism-v1`, `feature-slice-model`, `identifier-scheme` |
| **Decision point** | Hierarchical under ADR ID | `parallelism-v1/no-global-pointer` |
| **Slice** | Hierarchical under feature ID | `identifier-scheme/adr-rename-sweep` |
| **Feature** | Flat semantic slug | `identifier-scheme`, `fleet-coordinator-harness` |

**Why hierarchy where used:** decisions belong to ADRs; slices belong to features. The parent is the namespace, the child's ID is locally unique. Self-identifying cross-refs — `parallelism-v1/no-global-pointer` tells you exactly where to look without index lookup.

**Why ADRs and features stay flat:** no natural parent. ADRs are global to the methodology. Features are the top of the work hierarchy — their "parent" is the corpus, not a grouping entity.

**Supersession vs amendment semantics:** both move types exist in cairn today (ADR-007 amended ADR-003 D4; dogfood is expected to supersede ADR-003 wholly). Decisions survive across ADR states via amendment; the hierarchical ID captures which ADR owns the decision at the time it was made. On supersession (`parallelism-v2` replaces `parallelism-v1`), new ADR re-states decisions under its own namespace; old IDs freeze with the superseded ADR and remain findable via its `superseded-by:` pointer.

**Slice branch naming:** `slice/<feature>/<slice>`, which equals `slice/<slice-id>`. Git handles nested refs natively (same mechanism as `origin/main`). Branch name derivation is trivial.

## 5. Feature metadata

Feature files add one optional frontmatter field:

```yaml
id: identifier-scheme
name: "Identifier scheme overhaul"
intent: "..."
shaped-from: docs/plans/2026-04-15-identifier-scheme-design.md
```

- **`shaped-from:`** — single string. Path or URL pointing to wherever the feature was shaped. Self-identifies by prefix: `docs/plans/...` for cairn design docs, `https://...` for external tickets (JIRA, Linear, Notion, GitHub). Cairn stays ticketing-system-agnostic.

**No `epic:` field, no `.claude/epics/` entity.** Epics drag Scrum baggage (tracked state, rollup, promotion). Cairn's shape is closer to Shape Up — design docs are shaped pitches, features are the work that lands the pitch, git history is the tracking. Grouping is a grep query ("which features reference this design doc?"), not a first-class concept. If you want tracked epics, that lives in JIRA.

## 6. Prompt rule (1b surface)

**Placement:** one-line rule in `CLAUDE.md` alongside the safety-critical rules; elaboration in `docs/operational-reference.md`; templates (handoff, intent, ADR) reinforce by example.

**CLAUDE.md line (sketch):**

> When referring to an ADR, decision, slice, or feature in prose, raise its `name:` — not its `id:`. IDs belong in cross-ref fields, filenames, branches, hook logic.

**operational-reference elaboration** covers: style guide for `name:` (short, sentence or title case by author judgment, no trailing punctuation), when ID citations are appropriate (commit messages, file paths, frontmatter references, hook audit logs), example rewrites of opaque-to-legible references.

**Why not templates-only:** the rule fires in ad-hoc prose too (mid-conversation responses, handoffs). `CLAUDE.md` is the only surface guaranteed loaded every session.

**Why not `CLAUDE.md`-only:** CLAUDE.md has a terseness budget; the rule's nuances (when is an ID citation OK?) need room to breathe.

## 7. Migration strategy

**Approach: three-phase, Phase 3 indefinitely deferred.**

### Phase 1 — Schema + support (no renames)

- New ADR `identifier-scheme` declares the full scheme. Supersedes ADR-005.
- Hooks updated to accept both legacy and new formats (`SLICE-NNN` alongside `<feature>/<slug>`, numeric ADR-NNN alongside flat slugs, `D1/D2` alongside hierarchical decision IDs).
- Templates updated (ADR template adds `name:`, slice template adds `name:`, feature template adds `name:` and `shaped-from:`, handoff template references names not IDs in the cross-feature index).
- `CLAUDE.md` gets the prompt rule.
- `docs/operational-reference.md` gets the elaboration.

After Phase 1, all *new* ADRs, slices, features, and decision points use the new scheme. Existing entities remain numeric.

### Phase 2 — One-shot rename sweep

- Rename all existing ADRs: `docs/adr/001-*.md` → `docs/adr/<flat-slug>.md`. Frontmatter gains `id:` and `name:` fields if missing.
- Rename decision points across all ADRs: `D1`/`D2`/… → `<adr-id>/<decision-slug>`. Update cross-references.
- Slices under `.claude/completed-slices/` get `name:` added. IDs stay `SLICE-NNN` for historical ones unless a feature home is inferable; otherwise retain raw slug. (Rename cost is high; legibility gain for historical slices is modest. Decision to rename or not made per-slice during the sweep.)
- Feature files under `.claude/features/` get `name:` and `shaped-from:` where applicable.
- Cross-reference sweep: `docs/`, `CLAUDE.md`, `commands/`, `scripts/`, `.claude/` — anywhere an entity is cited.
- Retire `.claude/sweep.yaml.current-slice-number`. Related: off-by-one flagged in handoff is moot after this slice.

Phase 2 is a single sweep slice — atomic, high blast radius, but contained. Integration sweep at close validates no broken cross-refs.

### Phase 3 — Drop legacy-format tolerance (deferred indefinitely)

Hooks continue to accept both formats. Cost of keeping legacy tolerance: ~5 regex lines across three files. Benefit of dropping: pure aesthetics. Historical artifacts (sweep notes, handoffs, this design doc itself) reference the old form. Not scheduled; revisit if the regex surface becomes a maintenance burden.

## 8. Illustrative slice breakdown

Slice boundaries are illustrative; each slice's Phase 1 Intent refines them.

| Slice | Purpose |
|---|---|
| `identifier-scheme/scheme-adr` | Write the governing ADR, supersede ADR-005. No code, no renames. |
| `identifier-scheme/hook-tolerance` | Update `scope-guard.sh`, `reversibility-guard.sh`, `reality-check.sh` to accept both formats. Add tests covering both. |
| `identifier-scheme/template-updates` | Update slice/ADR/feature/handoff templates; edit CLAUDE.md; elaborate in operational-reference. |
| `identifier-scheme/adr-rename-sweep` | Rename ADR files, add `id:`/`name:` fields, update all cross-refs. |
| `identifier-scheme/slice-and-feature-rename` | Rename/annotate slices and features with `name:`/`shaped-from:`. Retire `sweep.yaml.current-slice-number`. |
| `identifier-scheme/doc-sweep` | Final cross-ref pass across docs, commands, scripts, and any residual references. |

**Ordering:** scheme-adr → hook-tolerance → template-updates before any rename sweep. Rename sweeps serial, doc-sweep last. Each rename slice limited to one entity class to keep envelopes tight.

## 9. Open questions for Phase 1 Intent

Decisions left for the first slice's Intent phase to resolve:

- Exact `name:` style conventions (sentence case? title case? punctuation?). Captured in the ADR.
- Whether numeric ADR filenames keep a legacy symlink during transition (`docs/adr/001-pipeline-protocol.md → pipeline-protocol-v1.md`) or hard-rename with redirect comments. Lean: hard-rename, no symlinks.
- Whether slice frontmatter allows a `supersedes:` field to track renames during the sweep, or git mv is sufficient record.
- Handoff's cross-feature index format change — before/after example in the ADR.

## 10. Risks

- **Cross-reference sweep misses a reference.** Integration sweep at Phase 2 close catches broken grep-able refs, but subtle prose references ("D1 of the parallelism ADR") can slip. Mitigation: the sweep slice Phase 4 Auditor grep pass includes `D[0-9]`, `SLICE-[0-9]`, `ADR-[0-9]` patterns and flags any remaining matches outside archived history.
- **Hierarchical slice IDs break tooling that assumes flat IDs.** `.claude/current-slice/slice.yaml` ID field gains a `/`; filesystem paths under `.claude/completed-slices/<feature>/<slice>/` become nested. Hooks using slice IDs as literal path components need audit. Mitigation: `identifier-scheme/hook-tolerance` slice covers this; integration gate catches regressions.
- **Feature name collisions across design docs.** Two design docs each shape a `fleet-coordinator-harness` feature at different times. Mitigation: flat feature IDs are a single global namespace; first-come wins, authors check existing feature files before choosing. Rare enough in solo-dev to not need tooling.
- **Concurrent slice assumption in ADR-007 not actually exercised.** This feature doesn't fix that. Fleet-coordinator Feature 6 (harness) is the real validation.

## 11. Verification (feature-level)

- New ADR landed and supersedes ADR-005.
- All three hooks accept both legacy and new formats; test suite covers both.
- Templates updated; first post-migration slice uses new scheme end-to-end.
- Existing ADRs renamed; cross-references resolve.
- `.claude/sweep.yaml.current-slice-number` removed.
- Prompt rule visible in `CLAUDE.md`; elaboration in operational-reference.
- Integration sweep post-Phase 2 finds no broken cross-references.

## 12. Follow-on work (not in this feature)

- **State taxonomy (Feature 1c).** Slice states, transition model, autonomous-eligible vs human-gated classification. Needed by fleet-coordinator Feature 2.
- **Phase 3 of migration** (dropping legacy hook tolerance). Deferred indefinitely.
- **Concurrent slice execution validation.** Fleet-coordinator Features 6 (harness) and 7 (dogfood) handle this.
- **Epic-level tracking in external systems.** Out of cairn's scope by design.
