---
id: <feature-id>
name: <human-facing label, mutable>
snapshot-sha: <git sha at Phase 1 dispatch>
invariants-touched: []
---

<!--
Phase 1 (Reader) intent template. Authoritative shape source:
`.claude/agents/phase-1-tdd.md`. Operational summary:
`docs/operational-reference.md` "Phase 1: Intent".

The eight body section headings below are required by the schema's
derive-don't-fabricate contract: Phase 1 must populate every section from
the plan-doc + cited ADRs + ARCHITECTURE.md, or RAISE_ISSUE if the inputs do
not support derivation. Omission-by-oversight is structurally prevented by
surfacing all eight headings in this template.
-->

## What
<!-- One paragraph: the behavior change. Lift verbatim from the plan-doc's
What/Why. ≤200 words combined with Why and Boundary. -->

## Why
<!-- Motivation. Cite the ADR(s) or review findings driving the work. Same
≤200-word combined budget. -->

## Boundary
<!-- What this feature does NOT do. Verbatim from the plan-doc's Boundary. -->

## Specification
<!-- Protocol-level commitments: wire formats, return shapes, error codes,
file paths, schema keys. Phase 2 writes tests against these literals. -->

## Verification
<!-- Concrete checks Phase 4 will run. Name the test files, validator
invocations, and any grep/wc evidence required. -->

## Risk Surface
<!-- ≤80 words. Required. Name the failure mode that would NOT show up as a
test failure — domain-level wrongness that passes CI. Derive from the
plan-doc's What/Why and the cited ADRs' consequences. If you can name only
generic risks, the plan-doc is under-specified — RAISE_ISSUE. -->

## Feature-Local Invariants
<!-- ≥1 entry. Required. Conditions specific to *this* slice that must hold
across all phases. Distinct from the corpus `invariants-touched` frontmatter
field. Derive from the plan-doc's What/Why/Boundary. If no FLI is derivable,
RAISE_ISSUE. -->

## Explicit Scope-Out
<!-- ≥1 entry. Required. What this slice deliberately does NOT do. Derive
from the plan-doc's Boundary plus the cited ADRs' explicit deferrals. If you
cannot name something out-of-scope, RAISE_ISSUE. -->

## Premise Grounding
<!-- OPTIONAL. NOT authored by phase-1-tdd — its Reader contract forbids
reading implementation source, so it cannot verify a verbatim span. The
operator adds this block at the Phase-1→Phase-2 approval gate (skill Step 5a),
where premise_guard.py diffs each quote against live source. Omit the section
entirely if the intent makes no claims about existing source behaviour. When
present, each premise pins a verbatim `quote:` from a repo-root-relative
`source:` and a one-line `label:` stating the current-behaviour claim the
intent depends on. -->

```yaml
premises:
  - source: scripts/_root.py            # repo-root-relative path
    quote: |                            # verbatim span; block scalar
      def project_root() -> Path:
    label: "one-line current-behaviour claim the intent depends on"
```
