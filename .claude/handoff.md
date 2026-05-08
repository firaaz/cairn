---
slice: m5-plugin-distribution
phase: f1-shipped-squashed
branch: dev
as-of: 2026-05-08 6e25777
---

## State
M5 F1 (plugin packaging) shipped via `cairn-tdd-feature` and squashed to a single commit (`6e25777`) on `dev`. The squash collapses Phase 1 (intent) → admin envelope-widening → Phase 2 (41 RED tests) → Phase 3 (GREEN impl) → Phase 4 (audit). Suite 401 passed / 2 failed (baseline) / 2 xfailed; validator green (11 invariants); A8 regression guard 22/22 green; INV-011 PASS. `.slice-system → .` self-symlink (Path B) intact. Local `dev` is 5 ahead of `origin/dev`; nothing pushed. Pre-squash chain (now garbage-collectable): `a20e7a7` (P1) → `a06a3c2` (admin) → `94c1990` (P2) → `ac796aa` (P3) → `b1d6362` (P4) — workspace files preserve the phase narrative.

## Next
1. Push `dev` → `origin/dev` (5 commits ahead) — operator-blessed when ready.
2. Dispatch F2 (`cairn-m5-f2-consumer-doc-surface`) via `cairn-tdd-feature` — pulls in F1 deliverables (marketplace URL, validator output, manifest paths, auto-postinstall decision).
3. F3 (`cairn-m6-f3-migration-and-symlink-retire`) after F2.

## Blocked / Pending
- F2-blocked: runbook home (CONSUMER.md vs new `docs/upgrading-from-symlink.md`) — F2 + F3 design call.
- F2-followup from F1: auto-postinstall hook decision (Phase 3 deferred — plugin spec field not confirmed; route to F2 CONSUMER.md as manual invocation if no auto-hook).
- F1 cleanup (one-line, out-of-envelope at P3): add `dist/` to `.gitignore`. Untracked `.claude/envelope-grants.log` (Phase-3 test side-effect) likely belongs there too.
- Pyright analyzer noise: `typer`/`yaml` flagged as unresolved imports in `build_dist.py`, `postinstall_validate.py`, `role_guard.py`. Runtime fine; pre-existing pattern across `scripts/`. Not actionable.
- 6 amendment ADRs (cost-per-slice-budget, parallelism-v1, phase-pipeline-evaluation, feature-slice-model, context-tiers-integration, identifier-scheme).
- M5.1: slash-command shipping (`dist/commands/`), multi-consumer rollout, doc-link validator.
- INV-004 re-baseline once CC system-prompt overhead stabilises (`test_inv004_turn1_token_budget` known-flaky; flickered PASS/FAIL across F1 dispatch).

## Pointers
- `docs/adr/m5-plugin-distribution-and-symlink-retire.md` (9 D-commitments + INV-011)
- `docs/plans/2026-05-08-cairn-m{5,6}-f{1,2,3}-*.md` (the trio; F1 envelope amended for canonical templates `.claude-plugin/{plugin,hooks}-template.json`)
- `.claude/skill-runs/cairn-m5-f1-packaging/` (intent.md, validation/approach.md, integration/sweep-notes.md — squashed out of git history but preserved as files)
- `.claude/skill-runs/m5-plugin-decision/` + `m5-feature-plans/brief.md`
- `.claude/active-envelope.yaml` (operator mode; widened to cover the M5/M6 trio plan docs — narrow scope before F2 dispatch if desired)
