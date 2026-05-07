---
id: slice-close-contract-superseded
name: "Slice close contract — superseded"
status: firm
firmness: firm
supersedes: slice-close-contract
date: 2026-05-07
program: cairn-shrink-m4
---

# Slice close contract — Superseded

## Context

The slice-close-contract ADR governed the idempotent close precondition,
the sole-producer-of-slice:complete-commit rule, the cross-slice slug-collision
tripwire, and the 13-row resume reconciliation matrix — all load-bearing for
cairn's pre-shrink slice orchestrator.

Per docs/plans/2026-05-06-cairn-shrink-design.md §3.2 / §7, that subsystem retires
in M4 (2026-05-07). This ADR records the supersession.

## Decision

slice-close-contract is superseded. The close_slice ceremony — its four-signal
idempotence precondition, its sole-producer-of-slice:complete-commit role, its
cross-slice slug-collision tripwire, and its 13-row resume reconciliation
matrix — all retire with the slice unit-of-work (M4). The dispatch skill
(.claude/skills/cairn-tdd-feature/SKILL.md) commits each phase's writes
natively; there is no slice to close.

The surviving behavior — if any — is captured in the carry-forward inventory at
docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md §2.

## Consequences

- close_slice and commit_phase_handoff functions deleted (E1, E5).
- INV-008 retires (slice-close lifecycle invariant — Task C1).
- INV-002(c) sub-clause retires (was bound to close_slice idempotence
  via test_close_slice_hardened.py — Task C4).
- 13-row resume matrix deleted; manual re-run is the dispatch-path
  equivalent.
- Consumer projects continuing to reference close_slice must migrate per
  the M5 plugin packaging plan (out of M4 scope).

## References

- docs/plans/2026-05-06-cairn-shrink-design.md §3.2, §7
- docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md
