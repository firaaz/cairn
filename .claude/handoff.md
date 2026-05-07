---
slice: post-cairn-shrink
phase: shrink-merged
branch: dev
as-of: 2026-05-07 42ae8d9
---

## State
cairn-shrink merged to dev as single squash `42ae8d9` (~29k LOC net removal; 76 commits collapsed). cairn-tdd-feature dispatch + F3 operator envelope are live; smoketest catches M4-class regressions. Suite 360/0/2; validator green.

## Next
1. Doc-reconciliation: op-ref + ARCHITECTURE.md still cite retired `current-slice/`, `/start-slice`, `scope-guard`, `ADR_D{1,3}_BYPASS`.
2. Memory prune of 7 post-M4-stale entries (`m4_stale_memories_to_prune.md`).
3. M5 plugin packaging.
4. Cleanup: delete branches `design/cairn-shrink` + `worktree-stress-test+m4-shrink-dogfood`; `git worktree remove` the stress-test worktree.
5. Push `dev` → `origin/dev` (awaiting user go-ahead).

## Blocked / Pending
- 6 amendment ADRs (cost-per-slice-budget, parallelism-v1, phase-pipeline-evaluation, feature-slice-model, context-tiers-integration, identifier-scheme).
- M6 consumer migration (`.slice-system → .` retire).
- Optional 2nd stress test for envelope-grant escapes.

## Pointers
- docs/plans/2026-05-08-hook-bare-python3-smoketest.md
- .claude/skills/cairn-tdd-feature/SKILL.md
- commands/claude-code/catchup.md
- .claude/active-envelope.yaml (mode: operator with M4 paths; set mode: off for ad-hoc work)
