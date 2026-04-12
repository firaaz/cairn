# Refresh Architecture — Full Reference

Regenerate `docs/ARCHITECTURE.md` from the current ADR corpus and validate consistency.

Usage: `/refresh-architecture`

## Why This Exists

ARCHITECTURE.md is a derived view — synthesized from ADRs, not hand-maintained. Every statement traces to a decision, and every firm decision is reflected in the doc. This keeps the architecture honest: if it drifts from the ADRs, the validator catches it. Generation is creative (AI synthesis), validation is mechanical (script) — they should not be confused.

## Step 1: Gather ADRs

Read every `.md` file in `docs/adr/` (skip `index.md`). For each ADR:
- Parse the YAML frontmatter (between `---` delimiters)
- Extract: `id`, `status`, `firmness`, `topic`, `invariants-touched`
- Skip any ADR where `status` is `superseded` or `retired`
- If frontmatter is missing or malformed, warn the user and skip that ADR

Collect the `## Decision` section content from each active ADR — these are the source of invariant commitments.

## Step 2: Synthesize ARCHITECTURE.md

Rewrite `docs/ARCHITECTURE.md` preserving this structure:

```markdown
# Architecture

System: Multi-tenant RAG for structured visa/border configuration data
Phase: <derive from ADR-002 or current state>

## Invariants

**INV-NNN** <Specific, testable commitment.> (ADR-NNN, ADR-NNN)

## Boundaries

<Module boundaries and ownership. Derived from ADR decisions about separation.>

## Data Ownership

<Which module owns which data. Derived from ADR storage/access decisions.>

## Current Phase Constraints

<What is deferred. Derived from ADR phasing decisions.>
```

Invariant rules:
- Each must be a specific, testable statement — vague invariants are worse than none because they pass every check vacuously
- Each must reference at least one active ADR
- Firm ADRs must have their core commitments reflected as invariants (the validator checks this — if a firm ADR has no invariant, Check B fails)
- Provisional ADRs should generally be reflected, but with softer language appropriate to their provisional status

## Step 3: Regenerate Index

Update `docs/adr/index.md` with all ADRs in table format (include superseded ones, marked as such). Table columns: ID, Title, Status, Firmness, Topic, Date.

## Step 4: Run Validator

Execute: `uv run python .slice-system/scripts/validate_architecture.py`

Report results:
- **ALL CHECKS PASSED**: Confirm counts (invariants verified, ADRs checked)
- **FAILED**: List each failure with its check type and remediation:
  - Check A (forward): invariant references missing/invalid ADR → fix the ADR reference
  - Check B (backward): firm ADR missing from invariants → add an invariant for it
  - Check C (staleness): invariant references superseded ADR → update to the superseding ADR

## Step 5: Commit if Clean

If validation passes:
```
git add docs/ARCHITECTURE.md docs/adr/index.md && git commit -m "docs: refresh ARCHITECTURE.md from ADRs"
```
