# New ADR — Full Reference

Create a new ADR with proper YAML frontmatter, or supersede an existing one.

Usage: `/new-adr` (new decision) or `/new-adr supersede ADR-NNN` (supersede existing)

## Why This Exists

ADRs are the system's memory of decisions. Every invariant in ARCHITECTURE.md traces back to an ADR. The append-only property is what makes ARCHITECTURE.md trustworthy as a derived view — if old ADRs could be silently edited, the synthesis would be unreliable. This skill enforces the creation protocol: proper frontmatter, append-only discipline, and automatic index/architecture refresh.

## Step 1: Determine the ADR Number

Read `docs/adr/index.md` to find the highest existing ADR number. The new ADR is that number + 1.

## Step 2: Gather Decision Context

If `$ARGUMENTS` contains "supersede ADR-NNN":
- Read the target ADR to understand what's being superseded
- Ask the user: is this a full supersession or partial? If partial, which sections are being superseded?

For any new ADR, gather from the user:
- **What decision is being made?** (one sentence)
- **What prompted this?** (slice conflict, new requirement, discovered limitation)
- **What firmness level?** Start provisional unless there's strong reason for firm — it's cheaper to promote later than to demote

## Step 3: Guide ADR Writing

Create the file at `docs/adr/<NNN>-<slug>.md` using this structure:

```yaml
---
id: ADR-<NNN>
status: accepted
firmness: provisional
supersedes: []           # or [ADR-NNN] if superseding
supersedes-sections: []  # for partial supersession, e.g. [A1-A3]
superseded-by: null
topic: <topic>
invariants-touched: [INV-NNN]
date: <today YYYY-MM-DD>
---
```

```markdown
# ADR-<NNN>: <Title>

## Status
Accepted (or Proposed, if needs review)

## Date
<today>

## Context
<What situation prompted this decision? Reference the slice or conflict that surfaced it.>

## Decision
<What is the decision? Be specific about commitments.
Each commitment should be testable — the validator and integration sweep need to verify these.>

## Consequences
<What changes as a result? What becomes easier, harder, or impossible?
Reference which invariants are affected.>

## Alternatives Considered
<What other approaches were evaluated? Why were they rejected?
This section is the disconfirming search — actively state what was considered and why it lost.>
```

## Step 4: If Superseding, Update the Old ADR

If this ADR supersedes another:
1. Read the old ADR
2. Update ONLY the YAML frontmatter of the old ADR:
   - Add `superseded-by: ADR-<NNN>` (pointing to the new ADR)
   - Change `status: superseded`
3. Do NOT modify the old ADR's body text — the append-only property is what keeps the history trustworthy

## Step 5: Update Index and Validate

1. Update `docs/adr/index.md` to include the new ADR row
2. Run `/refresh-architecture` to re-synthesize ARCHITECTURE.md and validate consistency
3. If validation fails, the new ADR needs adjustment (usually a missing invariant reference)

## Step 6: Commit

```
git add docs/adr/ docs/ARCHITECTURE.md && git commit -m "adr: ADR-<NNN> — <short title>"
```

If this was done during a slice, also update `.claude/current-slice/slice.yaml` → `adrs-created` field.

## Editorial Fixes to Accepted ADRs

For typo fixes, formatting corrections, and broken links in accepted ADRs, set `ADR_EDITORIAL_FIX=1` before editing. This logs the edit to `.claude/adr-editorial-fixes.log` but permits it. Do not use this for substantive content changes — if the meaning of a commitment changes, write a superseding ADR.
