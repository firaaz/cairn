---
slice: cairn-m7-plugin-deployment-pattern
phase: P1-P4a complete; V-thread (audit check 9) operator-bound
branch: dev
as-of: 2026-05-09 1f4733e
---

## State

M7 dispatched via `cairn-tdd-feature`. P1 intent (`dd966de`), P2 RED tests (`c9a1ff2`), P3 implementation (`b1439c9`), P2 amendment retiring superseded F1 A1 shape (`31d3976`), P4a sweep (`26e9cf4`) all committed. INV-012 invariant-check `test-ref` binding landed as orchestrator follow-up at `1f4733e` — Check E warning resolved, `test_zero_check_e_warnings` flipped from baseline-fail to GREEN. Operator-envelope expansion at `527f49a` (covers M7 phase-3 surface; trim post-merge). Suite: 13 failed / 423 passed / 1 skipped / 2 xfailed (was 14/422 baseline; one positive flip from INV-012 binding). All 9 M7 tests GREEN; 8 of 9 audit checks PASS; check 9 PENDING — operator-bound, NON-SKIPPABLE per ADR D9.

## Next

**V-thread runbook (operator)** — execute the cross-machine half:

1. `git push origin dev` (tip = `1f4733e`).
2. GitHub Actions UI → `release-publish` workflow → inputs: `version: 0.1.0`, `source_ref: dev`. Capture run-link, `release` SHA, `v0.1.0` tag SHA.
3. Fresh non-cairn project: `/plugin marketplace add https://github.com/firaaz/cairn` then `/plugin install cairn@cairn-marketplace`. Capture transcripts.
4. `uv run python scripts/validate_plugin_install.py` — clean exit.
5. Trivial `cairn-tdd-feature` dispatch — confirm hooks fire (stderr or `.claude/envelope-grants.log` consumer-side).
6. Report VERDICT block back to orchestrator.

Then orchestrator dispatches **Phase 4b** (records VERDICT into sweep-notes), followed by post-merge cleanup: F3 PENDING → PASS amendment, F1 deployment-gap closure, optional envelope retract.

## Blocked / Pending

- **Audit check 9 (V-thread)** — operator-bound; merge-final gate per ADR D9. Highest-leverage residual is M7.5 (Anthropic resolver behavior on `source.source:"github"` + `ref:"release"`); audit check 9 IS the empirical verification.
- **Phase 4b** — gated on operator's VERDICT block.
- **F3 audit check 9 PENDING → PASS** — closes on Phase 4b green.
- **F1 dist/ deployment gap** — closes on M7 merge.
- **Operator envelope trim** — post-merge: revisit `.claude/active-envelope.yaml` M7 expansion at `527f49a`.
- 2 baseline `TestSlice011AssertionCoverage` failures + INV-002 re-baseline (carry-overs).
- 6 amendment ADRs + spec-v2 correction + pre-§9 audit (carry-overs from prior handoffs).
- `/handoff` skill — 5th manual refresh in a row.

## Features

- `cairn-m5-f1-packaging`: shipped + on `origin/dev` — structural gap closes on M7 merge.
- `cairn-m5-f2-consumer-doc-surface`: closed.
- `cairn-m6-f3-migration-and-symlink-retire`: closed + merged + branch deleted; check 9 PENDING → resolves on M7 Phase 4b.
- `cairn-m7-plugin-deployment-pattern`: P1-P4a + INV-012 binding shipped (HEAD `1f4733e`); V-thread operator-bound; Phase 4b queued.

## Pointers

- `docs/adr/m5-plugin-deployment-pattern.md` — governing ADR; D1–D9 testable commitments.
- `docs/plans/2026-05-09-cairn-m7-plugin-deployment-pattern.md` — M7 dispatch input contract.
- `.claude/skill-runs/cairn-m7-plugin-deployment-pattern/intent.md` — Phase 1 contract (commit `dd966de`).
- `.claude/skill-runs/cairn-m7-plugin-deployment-pattern/validation/approach.md` — Phase 2 + amendment notes.
- `.claude/skill-runs/cairn-m7-plugin-deployment-pattern/integration/sweep-notes.md` — Phase 4a sweep with check-9 runbook scaffolded; Phase 4b will edit the VERDICT section.
- `.claude/skill-runs/plugin-deployment-pattern/` — /decision verification trail (P0, P0.5, P1, P2{A,B,C}, P3, P5).
- `docs/ARCHITECTURE.md:99-105` — INV-012 prose + invariant-check test-ref binding (machine-checked via `tests/unit/test_marketplace_schema.py`).
- `docs/lessons.md` L-022 — manifest-schema validity as load-bearing prerequisite.
- `.claude/active-envelope.yaml` — expanded with M7 phase-3 surface (`527f49a`); trim post-merge.
