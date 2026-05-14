# Feature schema D5 reconciliation — decision

**Question:** How should `identifier-scheme` D5 reconcile with the schema drift observed in `.claude/features/orchestrator-paths.yaml`?

**Context (surfaced by Trial B T5 on 2026-05-14):**

`identifier-scheme` D5 (firm, 2026-04-15) prescribes feature file frontmatter:
- `id:` — flat semantic slug (per D2)
- `name:` — human-facing label (per D1)
- `intent:` — short prose statement
- `shaped-from:` — single string path/URL to the design artifact

Empirically (2026-05-14 audit of `.claude/features/*.yaml` — 10 files):
- 9 conform to D5: compression, cost-discipline, efficiency-program-afternoon-wins, housekeeping, identifier-scheme, integration-gate, substrate, v1-defense-d2, v1-defense-d3
- 1 has structurally evolved: orchestrator-paths uses `charter:` (instead of `intent:`), no `shaped-from:`, plus 6 additional fields not in D5: `status`, `tracking` (GH issue ref), `predecessor` (slice id), `lesson` (L-id ref), `audit-findings` (F-id list), `out-of-scope` (list)

**Decision shape:** binary at the top, with downstream consequences either way.

- **Option NARROW:** D5 stays as-is. orchestrator-paths.yaml migrates back to D5: add `intent:` (derived from charter), add `shaped-from:` (find or create design doc), retain extra fields as advisory or move to slice metadata.
- **Option WIDEN:** D5 is amended to permit the richer schema. `charter:` becomes the canonical replacement for `intent:` OR an accepted alias. New fields (tracking, predecessor, lesson, audit-findings, out-of-scope) are recognised as optional. `shaped-from:` becomes optional or is folded into a more general "context" pointer.

**Why this is a firm-track decision:** amending or re-affirming D5 of `identifier-scheme` (status: firm) changes an architectural commitment. Both options have cross-cutting consequences — for the hook layer (does anything read these fields?), for the dispatch skill (does cairn-tdd-feature emit/expect these fields?), and for the broader question of "what is a cairn feature."

**Triggered by:** Trial B (ADR contract on identifier-scheme), T5 implementation.
