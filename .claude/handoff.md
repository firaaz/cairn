---
slice: design/cairn-shrink
phase: m4-stress-tested
branch: design/cairn-shrink
as-of: 2026-05-07 a29b9db
---

## State
M4 + review fixes landed. cairn-tdd-feature dispatch dogfooded e2e on `hook-bare-python3-smoketest` (squash `dc1b339`); phase isolation, RED-GREEN, audit, regression-plant all verified. Suite 360/0/2; validator green.

## Next
1. PR `design/cairn-shrink` → `dev`. `dc1b339` is the dogfood squash — single SHA revert if needed.
2. After merge: M5 plugin packaging.
3. Before M5: doc-reconciliation slice (op-ref + ARCHITECTURE.md drift).

## Blocked / Pending
- Doc-reconciliation: op-ref + ARCHITECTURE.md still cite retired `current-slice/`, `/start-slice`, `scope-guard`, `ADR_D{1,3}_BYPASS`. Out of scope for M4 PR.
- 6 amendment ADRs (cost-per-slice-budget, parallelism-v1, phase-pipeline-evaluation, feature-slice-model, context-tiers-integration, identifier-scheme).
- M6 consumer migration (.slice-system → . retire).
- Memory prune of 7 post-M4-stale entries (see `m4_stale_memories_to_prune.md`).
- Optional 2nd stress test: feature needing Phase-3 envelope-grant escapes.

## Pointers
- docs/plans/2026-05-08-hook-bare-python3-smoketest.md
- .claude/skills/cairn-tdd-feature/SKILL.md
- commands/claude-code/catchup.md
- .claude/active-envelope.yaml (clear or `mode: off` post-merge)
