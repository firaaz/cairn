---
id: orchestrator-observability-superseded
name: "Orchestrator observability — superseded"
status: firm
firmness: firm
supersedes: orchestrator-observability
date: 2026-05-07
program: cairn-shrink-m4
---

# Orchestrator observability — Superseded

## Context

The orchestrator-observability ADR governed the canonical observability-artifact
shape under cairn's pre-shrink architecture (B2/B3-hybrid schema, .claude/orchestrator-debug/
JSON+MD sidecar, append-only index.jsonl, .heartbeat liveness file, retention
tripwires).

Per docs/plans/2026-05-06-cairn-shrink-design.md §3.2 / §7, that subsystem retires
in M4 (2026-05-07). This ADR records the supersession.

## Decision

orchestrator-observability is superseded. The B2/B3-hybrid schema, the
canonical .claude/orchestrator-debug/ output shape, the heartbeat liveness
file, and the retention tripwires all retire with the orchestrator (M4).
Cost data remains observable via Anthropic primitives natively; no cairn-
specific writer is required.

The surviving behavior — if any — is captured in the carry-forward inventory at
docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md §2.

## Consequences

- .claude/orchestrator-debug/ machinery deleted.
- index.jsonl + <slug>-result.{json,md} writers deleted with
  scripts/slice_orchestrator/.
- INV-009's cost-threshold mechanization retires (advisory-only at M3
  drop; see Task C3 for INV-009 retirement and a follow-up amendment ADR
  for cost-per-slice-budget).
- Consumer projects continuing to reference the observability shape must
  migrate per the M5 plugin packaging plan (out of M4 scope).

## References

- docs/plans/2026-05-06-cairn-shrink-design.md §3.2, §7
- docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md
