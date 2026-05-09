---
slice: cairn-m7-plugin-deployment-pattern
phase: P1-P4b complete; V-3 + V-5 (fresh-project install round-trip) operator-bound
branch: dev
as-of: 2026-05-09 6cba452
---

## State

M7 dispatched via `cairn-tdd-feature` end-to-end. Commit chain: P1 `dd966de` → P2 `c9a1ff2` → envelope `527f49a` → P3 `b1439c9` → P2 amendment `31d3976` → P4a `26e9cf4` → INV-012 binding `1f4733e` → handoff `05b2de3` → P4b `6cba452`. Operator authorized push + workflow trigger; orchestrator executed V-thread machine-half autonomously: pushed `dev` to origin (`bfef6e5..05b2de3`), triggered release-publish workflow (run [25601897616](https://github.com/firaaz/cairn/actions/runs/25601897616) green in 10s), captured `release` SHA `779b013`, `v0.1.0` tag SHA `f8e2b70`, FLI-2 cross-check held end-to-end, and ran `postinstall_validate.py` against a clone of the published `release` payload (exit 0). Phase 4b recorded check-9 VERDICT: **PASS-with-pending-manual-round-trip** matching F3's verbatim precedent. Suite: 13 failed / 423 passed (was 14/422 baseline; INV-012 binding flipped one). All M7 tests GREEN.

## Next

**V-thread V-3 + V-5 — operator-bound, requires fresh non-cairn Claude Code session:**

3. Fresh project (any directory NOT inside cairn's tree). Run literally:
   ```
   /plugin marketplace add https://github.com/firaaz/cairn
   /plugin install cairn@cairn-marketplace
   ```
   Capture both transcripts. Confirm install completes; payload lands under consumer plugin cache.
4. (Already PASS via release-branch clone test — re-run from consumer cache for final verbatim record if desired.) `uv run python ${CLAUDE_PLUGIN_ROOT}/postinstall_validate.py` should report clean exit + envelope-enforcement self-test PASS.
5. Trivial `cairn-tdd-feature` dispatch in fresh project. Confirm `reversibility-guard.sh` / `role_guard.py` stderr OR `.claude/envelope-grants.log` landing consumer-side.

When V-3 + V-5 return: orchestrator amends sweep-notes (check-9 section gains "V-3 + V-5 closure" block; VERDICT PARTIAL-PASS → PASS), then lands the F3 PENDING → PASS follow-up commit and closes M5+M6 structurally.

## Blocked / Pending

- **V-3 + V-5 (audit check 9 closure)** — operator-bound, gates merge-final per ADR D9. Empirical M7.5 residual (Anthropic resolver behavior) verified by V-3 by construction.
- **F3 PENDING → PASS amendment** — gated on V-3 + V-5 green; lands as standalone follow-up commit per F3 sweep-notes recording protocol.
- **F1 dist/ deployment gap closure note** — same gate.
- **Operator envelope trim** — post-merge: revisit `.claude/active-envelope.yaml` M7 expansion at `527f49a` (M7 phase-3 paths) — keep or trim per next session's scope.
- **Node 20 deprecation** — workflow annotation: `actions/checkout@v4`, `astral-sh/setup-uv@v3` running on Node 20; default flips to Node 24 on 2026-06-02. Bump action versions before then. Out-of-scope for M7; new lever for the punch list.
- 2 baseline `TestSlice011AssertionCoverage` failures + INV-002 re-baseline (carry-overs).
- 6 amendment ADRs + spec-v2 correction + pre-§9 audit (carry-overs from prior handoffs).
- `/handoff` skill — 6th manual refresh in a row.

## Features

- `cairn-m5-f1-packaging`: shipped + on `origin/dev` — structural gap closure note pending V-3+V-5 green.
- `cairn-m5-f2-consumer-doc-surface`: closed.
- `cairn-m6-f3-migration-and-symlink-retire`: closed + merged + branch deleted; check 9 PENDING → resolves on V-3+V-5 green.
- `cairn-m7-plugin-deployment-pattern`: P1-P4b shipped + V-thread machine-half PASS (HEAD `6cba452`); merge-eligible, not merge-final until V-3+V-5 close. Marketplace shape on `dev` correct; release branch on origin populated; v0.1.0 tag pushed.

## Pointers

- `docs/adr/m5-plugin-deployment-pattern.md` — governing ADR; D1–D9 testable commitments.
- `docs/plans/2026-05-09-cairn-m7-plugin-deployment-pattern.md` — M7 dispatch input contract.
- `.claude/skill-runs/cairn-m7-plugin-deployment-pattern/intent.md` — Phase 1 contract (commit `dd966de`).
- `.claude/skill-runs/cairn-m7-plugin-deployment-pattern/validation/approach.md` — Phase 2 + amendment notes.
- `.claude/skill-runs/cairn-m7-plugin-deployment-pattern/integration/sweep-notes.md` — full audit; check-9 VERDICT block at lines 169-223 (machine-half PASS, V-3+V-5 PENDING).
- `.claude/skill-runs/plugin-deployment-pattern/` — /decision verification trail.
- `docs/ARCHITECTURE.md:99-105` — INV-012 prose + invariant-check `test-ref` binding.
- `docs/lessons.md` L-022 — manifest-schema validity as load-bearing prerequisite.
- `.claude/active-envelope.yaml` — M7 phase-3 expansion at commit `527f49a`; trim post-merge.
- Release branch on origin: SHA `779b013`; v0.1.0 tag SHA `f8e2b70`; workflow run https://github.com/firaaz/cairn/actions/runs/25601897616.
