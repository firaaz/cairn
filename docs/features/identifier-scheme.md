---
id: identifier-scheme
name: "Identifier scheme"
status: merged
opened: 2026-04-15
merged: 2026-04-18
archive-branch: archive/identifier-scheme
---

# Identifier scheme

## What shipped

Every ADR, slice, feature, and decision point now carries both `id:` (immutable mechanical identifier) and `name:` (mutable human/LLM-facing label). Prose uses `name:`; cross-references, filenames, and hook inputs use `id:`. Full protocol in `docs/adr/identifier-scheme.md` and `docs/operational-reference.md`.

## Slices

- **identifier-scheme/adr-rename-sweep** — 2026-04-15 → 2026-04-16 — complete. ADRs renamed from numeric IDs (`adr-NNN`) to semantic slugs.
- **identifier-scheme/slice-and-feature-rename** — 2026-04-17 — complete. Slice and feature namespace migrated to feature-scoped slugs.
- **identifier-scheme/doc-sweep** — 2026-04-18 — complete. Residual prose references cleaned up.

## ADRs

- Created: [`docs/adr/identifier-scheme.md`](../adr/identifier-scheme.md)
- Touched via rename propagation: the full ADR corpus (see archive branch for exact touch list per slice)

## User-visible changes

- ADR files moved from `adr-NNN-<slug>.md` to `<semantic-slug>.md`
- Slice directories under `.claude/completed-slices/` use feature-scoped slugs
- Feature registry at `.claude/features/*.yaml` adopts the id/name pattern
- Hook input paths handle the new identifier shape (`scope-guard.sh`, `reality-check.sh`, `reversibility-guard.sh`)
- Commit-message phase templates at `.gitmessage-phase-{1..4}` use the new convention
- CLAUDE.md gained the identifier-scheme summary

## Carry-over debt at close

- **v1-defense-d3/bypass-log-hierarchical-slug** — queued slice. Narrow-patched ahead of this merge (regex alternation widen + chronology helper + log line 8 class-token reshape, commit `6c2e8f1` on archive branch). Remaining slice work: canonicalize hierarchical-id grammar in the D3 ADR, extract `CLASSIFIED_LINE_RE` from the test file to a shared definition, enforce shape at hook-append time.
- **F1 ADR prose cleanup in 7 ADRs** — folded into the planned `compression` Slice A.
- **F2 `test_phase_rethink.py:30-36` key rekey** — same (compression Slice A).
- **Part 0 ADR (P1–P6 + D1/D2/D3) consolidation** — planned as `compression` Slice B.

## Design & research docs

- [`docs/plans/2026-04-15-identifier-scheme-design.md`](../plans/2026-04-15-identifier-scheme-design.md) — original design
- [`docs/plans/2026-04-16-dogfood-observations.md`](../plans/2026-04-16-dogfood-observations.md) — parallel-execution dogfood findings (migrated from `.claude/plans/` at merge)
- [`docs/plans/2026-04-16-manual-parallel-dogfood.md`](../plans/2026-04-16-manual-parallel-dogfood.md) — dogfood run notes (migrated)
- [`docs/plans/2026-04-16-manual-dogfood-tmux-topology-design.md`](../plans/2026-04-16-manual-dogfood-tmux-topology-design.md) — tmux topology for dogfood
- [`docs/plans/2026-04-18-feature-to-dev-merge-protocol-design.md`](../plans/2026-04-18-feature-to-dev-merge-protocol-design.md) — merge protocol this feature instantiates
- [`docs/plans/2026-04-18-feature-to-dev-merge-protocol-plan.md`](../plans/2026-04-18-feature-to-dev-merge-protocol-plan.md) — this merge's execution plan

## Archaeology

```
git log archive/identifier-scheme
```

170+ pre-squash commits preserved on the archive branch (created at merge time from the feature branch rename). See `docs/plans/2026-04-18-feature-to-dev-merge-protocol-design.md` for the archaeology-preservation rationale.
