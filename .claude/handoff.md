---
slice: cairn-m6-f3-migration-and-symlink-retire
phase: complete
branch: dev
as-of: 2026-05-09 6a6f430
---

## State

F3 closed and fast-forwarded onto `dev` (`6a6f430`); M5+M6 milestone code (F1 + F2 + F3) is on `origin/dev` and the F3 feature branch is deleted (local + origin). F1's plugin-marketplace `source.path: "dist/"` is structurally not deployed — `dist/` was never committed to any pushed ref, no CI step publishes it, and Claude Code's `/plugin install` resolves `path:` statically against the cloned default branch (confirmed via Anthropic's plugin-marketplaces docs). `/plugin install cairn@cairn-marketplace` will fail today; F3's audit check 9 (manual end-to-end real install) is **PENDING — gated on a deployment-gap feature, not on F3's work**.

Schema dogfood #2 was positive (n=2 cumulative): F3's intent absorbed 6 operator-interview amendments through three Phase 1 commits, with all six amendments captured in writing under explicit operator approval before Phase 2 dispatched. P.1 RAISE_ISSUE branch (amendment 1) was readied but didn't fire — `reversibility-guard.sh`'s frontmatter-only gate scopes to `docs/adr/*.md`, not `docs/ARCHITECTURE.md`, so the body-prose append was permitted directly. Suite at `6a6f430`: 13 failed (vs 14 baseline at `c78f863`; one incidental pass on `test_inv004_turn1_token_budget` from F3 doc-churn), 413 passed, 1 skipped, 2 xfailed.

## Next

Run `/decision` (teamed pattern per operator memory `feedback_decision_with_agent_teams.md`: parallel Phase 0/0.5 + Phase 2 across 3 approaches, persist context to `.claude/skill-runs/<decision>/`) for the plugin deployment pattern — three documented options: **A. release branch with `dist/` committed + sync CI, B. npm publish (`source.source: "npm"`), C. GitHub release + git-subdir.** Dispatch the chosen-pattern feature next so check 9 unblocks; F3 sweep-notes records the gap as "merge-eligible but not merge-final until check 9 records green".

## Blocked / Pending

- Plugin deployment gap (NEW, top-priority) — F1's `dist/` not pushed; `/decision` then dispatch chosen-pattern feature → `.claude/skill-runs/cairn-m6-f3-migration-and-symlink-retire/integration/sweep-notes.md` "Pending manual verification — audit check 9"
- F1 audit-shape learning — Phase 4 verified build-time correctness but not post-deploy installability; Phase-4 checklist (or `templates/sweep-notes.md`) may want a "would `/plugin install` resolve this?" check for plugin-distribution features
- `/handoff` skill — still pending; this refresh was manual (third in a row)
- `.gitignore` cleanup — `dist/` (F1 follow-up flagged but unfixed) + untracked `.claude/envelope-grants.log`
- 2 baseline failures: `TestSlice011AssertionCoverage::{test_no_extra_assertion_blocks, test_invariant_count_unchanged}` → INV-002 re-baseline on `docs/handoff.md`
- 6 amendment ADRs (governance follow-up); spec-v2 correction; pre-§9 audit (5 recent intent.mds × "cited ADR shaped impl?")

## Features

- `cairn-m5-f1-packaging`: shipped + on origin/dev — **structurally incomplete** (dist/ deployment gap)
- `cairn-m5-f2-consumer-doc-surface`: closed
- `cairn-m6-f3-migration-and-symlink-retire`: closed + merged + branch deleted; check 9 PENDING on deployment-gap fix
- (next) plugin-deployment-gap feature — TBD post-`/decision`

## Pointers

- `docs/adr/m5-plugin-distribution-and-symlink-retire.md` — governing ADR for M5+M6; D3 (allow-list IS the contract) is the relevant decision the deployment-pattern choice may amend or extend
- `.claude/skill-runs/cairn-m6-f3-migration-and-symlink-retire/integration/sweep-notes.md` — F3 audit (check 9 PENDING), schema dogfood #2 evidence
- `.claude/skill-runs/m5-plugin-decision/` — prior `/decision` workspace for the M5+M6 program (Phase 0.5 journey, Phase 1 pre-mortem); reuse the structure for the deployment-pattern decision
- `.claude-plugin/marketplace.json:13` — the `"path": "dist/"` declaration that gates the install
- `scripts/build_dist.py` + `.github/workflows/dist-gate.yml` — build-time pipeline; CI validates but never publishes dist/
- `docs/roadmap.md` — `## Gated` section now carries the F1.1 validator-stdout-literal entry F3 added; the deployment-gap feature should land alongside or before that
- `templates/handoff.md`, `templates/sweep-notes.md`, `templates/intent.md`, `templates/feature-plan.md`, `templates/adr-frontmatter.yaml`, `templates/active-envelope.yaml` — F2-shipped phase-boundary contract templates
