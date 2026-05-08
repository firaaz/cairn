---
id: <feature-id>
name: <human-facing label, mutable>
firmness: provisional
status: draft
date: <YYYY-MM-DD>
scope: <one-line scope statement>
inputs:
  - docs/adr/<adr-id>.md
  - docs/ARCHITECTURE.md
envelope:
  - "^scripts/path/to/.+\\.py$"
  - "^tests/unit/test_.+\\.py$"
  - "^docs/plans/<YYYY-MM-DD>-<feature-id>\\.md$"
---

<!--
Per-feature plan-doc template. Cross-reference:
`docs/operational-reference.md` "Per-feature plan-doc shape". Drop this file
at `docs/plans/<YYYY-MM-DD>-<feature-id>.md`, fill the frontmatter and the
four body sections, then dispatch via the `cairn-tdd-feature` skill.

The frontmatter `id:` field becomes the feature id used throughout the
dispatch run; the `envelope:` regex array is the source-write set Phase 3's
`role_guard.py` enforces.
-->

# <Feature name>

## What / Why

<One paragraph naming the behavior change and its motivation. Cite the ADR(s)
or review findings that motivate the work. Keep ≤200 words combined with
Boundary below.>

## Boundary

<Out-of-scope items, explicit. What this feature deliberately does NOT do.
At least one bullet — Phase 1 RAISE_ISSUEs if no scope-out is derivable.>

## Specification

<Protocol-level commitments — wire formats, return shapes, error codes,
file paths, schema keys. Phase 2 writes tests against these literals.>

## Verification

<Concrete checks Phase 4 will run. Name the test files, the validator
invocations, and any `wc`/grep evidence required for invariant verification.>
