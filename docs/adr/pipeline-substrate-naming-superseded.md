---
id: pipeline-substrate-naming-superseded
name: "Pipeline substrate naming — superseded"
status: firm
contract:
  must-satisfy:
    - "commit-prefix registry mechanics survive via the inline fallback (carrier: scripts/validate_architecture.py _FALLBACK_REGISTRY INV-001)"
  evidence:
    - "tests/unit/test_inv_001_git_log_walk.py passes"
firmness: firm
supersedes: pipeline-substrate-naming
date: 2026-05-07
program: cairn-shrink-m4
---

# pipeline-substrate-naming-superseded: Pipeline Substrate Naming — Superseded

## Status
Firm

## Date
2026-05-07

## Context

M4 retires the pipeline machinery — `/integration-sweep`, `/refresh-architecture`,
and the associated registry mechanism introduced by `pipeline-substrate-naming`.
With the pipeline gone, the three-class commit taxonomy (slice-phase, decision,
pipeline-substrate) collapses back to two classes, and the registry that
authorized the third class becomes dead state.

## Decision

pipeline-substrate-naming is superseded. The substrate-commit-class
authorization mechanism (.claude/pipeline-substrate-registry.yaml + the
"three legitimate commit classes" extension to INV-001) retires with the
pipeline machinery (M4). INV-001's binding shrinks to the two legitimate
classes named in bootstrap-exception (decision and slice flows), with
"slice" reinterpreted as "any commit produced by the cairn-tdd-feature
dispatch skill."

The surviving behavior — if any — is captured in the carry-forward inventory at
docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md §2.

## Consequences

- .claude/pipeline-substrate-registry.yaml retired (Task E6).
- INV-001 binding-effective-from anchor unchanged (2fb83f6); the registry
  reference in the binding block is updated to point at the dispatch
  skill's commit convention or removed entirely (Task C5).
- The D4 follow-up tracked in the M3 handoff (design:/plan: registry
  bypass-of-ADR-path; refactor:/adr: M4 additions) is closed by this
  supersession (the registry no longer exists to drift from).
- Consumer projects continuing to reference the pipeline-substrate naming
  scheme must migrate per the M5 plugin packaging plan (out of M4 scope).
