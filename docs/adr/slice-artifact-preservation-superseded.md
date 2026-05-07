---
id: slice-artifact-preservation-superseded
name: "Slice artifact preservation — superseded"
status: firm
firmness: firm
supersedes: slice-artifact-preservation
date: 2026-05-07
program: cairn-shrink-m4
---

# Slice artifact preservation — Superseded

## Context

The slice-artifact-preservation ADR governed the pre-wipe copy of phase
ephemerals to `.claude/sweep-results/<slug>/artifacts/` inside `close_slice`,
the F5-tolerance contract for missing source files, the two-tier copy-failure
handling (D6 silent-skip vs D7 loud-abort), and the INV-008 fourth-property
prose amendment — all load-bearing for cairn's pre-shrink artifact preservation
layer.

Per docs/plans/2026-05-06-cairn-shrink-design.md §3.2 / §7, that subsystem retires
in M4 (2026-05-07). This ADR records the supersession.

## Decision

slice-artifact-preservation is superseded. The _copy_artifacts_to_sweep_results
function, the .claude/sweep-results/<slug>/artifacts/ output shape, and the
F5-tolerance copy-before-wipe contract all retire with close_slice (M4).
Git history of merged feature branches preserves the equivalent forensic
surface.

The surviving behavior — if any — is captured in the carry-forward inventory at
docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md §2.

## Consequences

- .claude/sweep-results/ machinery deleted (Task E6).
- _copy_artifacts_to_sweep_results function deleted with scripts/slice_orchestrator/ (Task E1).
- INV-008 sub-clause (d) retires in lockstep — INV-008 fully retired (Task C1).
- Consumer projects continuing to reference sweep-results must migrate per
  the M5 plugin packaging plan (out of M4 scope).
