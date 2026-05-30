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

## Contract

<!-- OPTIONAL. The scope-split (atomicity) machine-readable contract.
atomicity_guard.py runs the atomicity check on `must-satisfy` at the
Phase-1→Phase-2 boundary; the `scope-split` validator assertion runs the same
check. Absent block = fail-open with a visible stderr notice, unless
CAIRN_CONTRACT_REQUIRED=1.

Six clause-lists:
  must-satisfy      — atomicity-checked behavioural clauses (the gate's input)
  must-not-violate  — invariants this feature must preserve
  wrong-if          — observations that mean the implementation is wrong
  escalate-when     — conditions that require operator escalation
  evidence          — what proves each clause holds
  execution-scope   — files/dirs the work may touch

Write each `must-satisfy` item as a single EARS clause. The five EARS shapes:
  Ubiquitous : "the <system> shall <response>"
  Event      : "when <trigger>, the <system> shall <response>"
  State      : "while <state>, the <system> shall <response>"
  Option     : "where <feature>, the <system> shall <response>"
  Unwanted   : "if <condition>, then the <system> shall <response>"

Atomicity (ADR D3): a clause is atomic iff verifiable by a single tool call or
single file check. Clauses without a tag must pass atomicity. A non-atomic
clause must be split into atomic clauses OR carry one of the four named
exception tags — tagging is the cheap one-line escape from a flagged clause:

  universal-set      — quantifies over a set; declaration enumerates the set
  regression-meta    — "unchanged"/"no regression" meta-clause; declaration names the baseline
  operator-bound     — needs human action/judgement; declaration names the operator step
  trivial-existence  — a file/output simply exists; NO declaration required

The first three tags require a non-empty declaration after the colon; an unknown
tag always fails. Mapping form: {clause: "<EARS>", except: "<tag>: <declaration>"}.

Worked example (one bare atomic clause + one tagged universal-set clause): -->

```yaml
must-satisfy:
  - the validator reports the offending line number on a malformed id
  - clause: every consumer repository receives the regenerated dist mirror
    except: "universal-set: the consumer set is the 3 repos listed in roadmap.md"
must-not-violate:
  - <invariant this feature must preserve>
wrong-if:
  - <observation that means the implementation is wrong>
escalate-when:
  - <condition that requires operator escalation>
evidence:
  - <what proves a clause holds>
execution-scope:
  - <file or directory the work may touch>
```
