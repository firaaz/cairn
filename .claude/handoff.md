---
slice: post-cairn-shrink
phase: doc-reconciliation-landed
branch: dev
as-of: 2026-05-08 f089c27
---

## State
Doc-reconciliation landed on dev (5 commits ahead of `9711616`): op-ref full rewrite + ARCH.md surgical (incl. L59 INV-005 audit-followup) + why-cairn.md (L47 envelope + 8 stale-claim fixes). Retired surfaces (`/start-slice`, `scope-guard.sh`, `.claude/current-slice/`, orchestrator-debug, retired CAIRN_* env vars) cleared from the three docs. Suite 359/1/2 — the one fail is the pre-existing INV-004 turn-1 budget regression under CC 2.1.132 system-prompt overhead. Validator + smoketest green.

## Next
1. Memory prune of 7 post-M4-stale entries (`m4_stale_memories_to_prune.md`).
2. M5 plugin packaging.
3. Branch/worktree cleanup: delete `design/cairn-shrink` + `worktree-stress-test+m4-shrink-dogfood`; `git worktree remove` stress-test worktree.
4. Push `dev` → `origin/dev` (awaiting go-ahead; 8 commits ahead).

## Blocked / Pending
- 6 amendment ADRs (cost-per-slice-budget, parallelism-v1, phase-pipeline-evaluation, feature-slice-model, context-tiers-integration, identifier-scheme).
- M6 consumer migration (`.slice-system → .` retire).
- INV-004 re-baseline once CC system-prompt overhead stabilises.

## Pointers
- docs/operational-reference.md (post-shrink rewrite; bindings preserved)
- .claude/skills/cairn-tdd-feature/SKILL.md
- .claude/active-envelope.yaml (mode: operator; set mode: off for ad-hoc)
- /Users/firaazfarook/.claude/plans/concurrent-chasing-river.md
