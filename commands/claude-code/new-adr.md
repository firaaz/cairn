# /new-adr

Create an Architecture Decision Record with proper YAML frontmatter.

Usage: `/new-adr` (new) or `/new-adr supersede ADR-NNN` (supersede existing)

## Rules

1. Read `docs/adr/index.md` for highest ADR number. New ADR = highest + 1.
2. Gather: decision statement, what prompted it, firmness (default provisional).
3. Create `docs/adr/<NNN>-<slug>.md` with YAML frontmatter: id, status, firmness, supersedes, topic, invariants-touched, date.
4. Body: Status, Date, Context, Decision (testable commitments), Consequences (easier AND harder), Alternatives Considered.
5. Superseding: update old ADR frontmatter ONLY — `superseded-by` and `status: superseded`. Never modify old body (append-only).
6. Update `docs/adr/index.md`, run `/refresh-architecture`, fix if validation fails.
7. Commit: `git add docs/adr/ docs/ARCHITECTURE.md && git commit`.
8. During a slice: update `slice.yaml` → `adrs-created`.
9. Editorial fixes only: `ADR_EDITORIAL_FIX=1`. Not for substantive changes.

## Load full

- If superseding an existing ADR: read new-adr.full.md for partial-supersession protocol and frontmatter update rules.
- If validation fails after `/refresh-architecture`: read new-adr.full.md for the complete YAML template and section guide.
