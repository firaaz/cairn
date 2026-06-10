---
id: d3-bypass-classification-superseded
name: "D3 bypass classification — superseded"
status: firm
carrier: rationale-only
firmness: firm
supersedes: d3-bypass-classification
date: 2026-05-07
program: cairn-shrink-m4
---

# D3 bypass classification — superseded

## Status
Firm.

## Date
2026-05-07

## Context

d3-bypass-classification refined D3's bypass log schema and introduced
intent-time envelope exemptions. Both mechanisms depended on the slice
machinery's structural-immutability gate (D3) being in the active dispatch
path.

With M3 retiring the slice pipeline and associated dispatch hooks, the D3 gate
no longer fires. There is no enforcement target for the bypass log schema or the
ADR_D3_BYPASS=1 escape hatch.

## Decision

d3-bypass-classification is superseded. With the slice machinery retired and
no D3 structural-immutability gate in the dispatch path, the bypass log shape
and ADR_D3_BYPASS=1 escape have no enforcement target. Operator judgment + the
pre-commit validator subsume the gate.

The surviving behavior — if any — is captured in the carry-forward inventory at
docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md §2.

## Consequences

- .claude/d3-bypasses.log retired (Task E6).
- .claude/d1-bypasses.log retired in tandem (D1 gate dies with
  /refresh-architecture; Task E5).
- ADR_D3_BYPASS env-var no-op'd (no consumer remains).
- Consumer projects continuing to reference D3 bypass classification must
  migrate per the M5 plugin packaging plan (out of M4 scope).
