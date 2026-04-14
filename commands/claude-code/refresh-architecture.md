# /refresh-architecture

Regenerate `docs/ARCHITECTURE.md` from the ADR corpus and validate consistency.

Usage: `/refresh-architecture`

**Note:** This command is also invoked automatically by the D1 refresh gate during `/start-slice complete` (see start-slice.full.md Step 7). The manual command behavior is unchanged.

## Rules

1. Read every `.md` in `docs/adr/` (skip `index.md`). Parse YAML frontmatter. Skip `status: superseded` or `retired`.
2. Extract `## Decision` content from each active ADR — these source invariant commitments.
3. Rewrite `docs/ARCHITECTURE.md`: `## Invariants`, `## Boundaries`, `## Data Ownership`, `## Current Phase Constraints`.
4. Each invariant: specific, testable, references ≥1 active ADR. Firm ADRs MUST have core commitments as invariants.
5. Update `docs/adr/index.md` table (include superseded, marked as such).
6. Run validator: `uv run python .slice-system/scripts/validate_architecture.py`.
7. Report: Check A (invariant→ADR), Check B (firm ADR→invariant), Check C (superseded refs).
8. If clean: `git add docs/ARCHITECTURE.md docs/adr/index.md && git commit -m "docs: refresh ARCHITECTURE.md from ADRs"`.

## Load full

- If validator fails: read refresh-architecture.full.md for check-type remediation steps and the ARCHITECTURE.md structure template.
