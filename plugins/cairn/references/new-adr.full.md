# New ADR — Full Reference

Create a new ADR with proper YAML frontmatter, or supersede an existing one.

Usage: `/new-adr` (new decision) or `/new-adr supersede ADR-NNN` (supersede existing)

## Why This Exists

ADRs are the system's memory of decisions. Every invariant in ARCHITECTURE.md traces back to an ADR. The append-only property is what makes ARCHITECTURE.md trustworthy as a derived view — if old ADRs could be silently edited, the synthesis would be unreliable. This skill enforces the creation protocol: proper frontmatter, append-only discipline, and automatic index/architecture refresh.

## Step 1: Determine the ADR Id

Read `docs/adr/index.md` and pick a new `id:` for the ADR. Per ADR `identifier-scheme` D2, an ADR `id:` is a **flat semantic slug** — lowercase, hyphen-separated, no numeric prefix. Examples: `identifier-scheme`, `parallelism-v1`, `phase-lock-and-role-declaration`. The filename on disk takes the shape `docs/adr/<NNN>-<slug>.md` where `<NNN>` is a monotonically increasing numeric prefix used purely for filesystem ordering; the `<slug>` tail is the ADR `id:` and is what hooks, cross-references, and the validator consume.

When superseding a prior decision, the successor ADR's `id:` follows the `-v1` → `-v2` versioning pattern (ADR `identifier-scheme` D3), e.g., `parallelism-v1` superseded by `parallelism-v2`.

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
id: <flat-semantic-slug>
name: "<human label>"
status: accepted
firmness: provisional
supersedes: []           # list of ADR id values (e.g., [feature-slice-model]), not filenames
supersedes-sections: []  # for partial supersession, e.g. [A1-A3]
superseded-by: null
topic: <topic>
adrs-referenced: []      # list of ADR id values (e.g., [identifier-scheme]), not filenames
invariants-touched: [INV-NNN]
date: <today YYYY-MM-DD>
---
```

Per ADR `identifier-scheme` D9, `supersedes:` and `adrs-referenced:` each hold a list of target ADR `id:` values — the flat slugs from Step 1, **not** filenames and **not** numeric prefixes like `parallelism-v1`. Example: an ADR that supersedes `feature-slice-model` writes `supersedes: [feature-slice-model]`. The validator and `/refresh-architecture` resolve these slugs against `docs/adr/index.md` at load time.

Within an ADR body, decision points are numbered `D1`, `D2`, `D3`, … and are freely cited bare from the same ADR. When citing a decision point from a *different* ADR, use the hierarchical form `<adr-id>/<decision-slug>` (e.g., `identifier-scheme/flat-slug-id`) — the `<decision-slug>` identifies the decision within its owning ADR and is stable across supersession only if the successor explicitly preserves it.

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
