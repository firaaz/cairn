---
slice: cairn-m7-plugin-deployment-pattern
phase: planned (ADR + plan landed; ready for cairn-tdd-feature dispatch)
branch: dev
as-of: 2026-05-09 126ee60
---

## State

`/decision` ran on plugin deployment pattern (full A/B/C/D enumeration, teamed Phase 0/0.5 + Phase 2). Operator selected Approach A. Phase 5 independent blind verification converged HIGH-confidence on the same field-level shape. ADR `m5-plugin-deployment-pattern` (firm, accepted) landed at `69ef87a` with INV-012 added to ARCHITECTURE.md; verification trail at `93c1e75`. M7 implementing-feature plan, envelope expansion, and L-022 lesson all queued in working tree (next commit). Validator state: 1 pre-existing failure (INV-002 handoff budget), 1 new warning (INV-012 lacks invariant-check `test-ref` until M7 lands the schema lint).

## Next

Dispatch `cairn-tdd-feature` against `docs/plans/2026-05-09-cairn-m7-plugin-deployment-pattern.md`. M7 ships in three threads: S (schema rewrite + `tests/unit/test_marketplace_schema.py`), W (`.github/workflows/release-publish.yml`), V (manual end-to-end `/plugin install` round-trip — audit check 9 NON-SKIPPABLE per ADR D9). M7 close transitions F3 audit check 9 PENDING → PASS and closes M5+M6 structurally.

## Blocked / Pending

- F3 audit check 9 — gated on M7; ADR D9 makes it acceptance criterion.
- F1 dist/ deployment gap (original lead item) — closes on M7 merge.
- INV-012 invariant-check binding — M7 Phase 4 may extend with `test-ref` pointing at `tests/unit/test_marketplace_schema.py` (resolves Check E warning).
- `/handoff` skill — 4th manual refresh in a row.
- 2 pre-existing baseline test failures (`TestSlice011AssertionCoverage`); INV-002 re-baseline.
- 6 amendment ADRs + spec-v2 correction + pre-§9 audit (carry-overs from prior handoffs).

## Features

- `cairn-m5-f1-packaging`: shipped + on `origin/dev` — structural gap closes on M7 merge.
- `cairn-m5-f2-consumer-doc-surface`: closed.
- `cairn-m6-f3-migration-and-symlink-retire`: closed + merged + branch deleted; check 9 PENDING → resolves on M7.
- (next) **`cairn-m7-plugin-deployment-pattern`**: plan landed at `docs/plans/2026-05-09-cairn-m7-plugin-deployment-pattern.md`; ADR is `m5-plugin-deployment-pattern`.

## Pointers

- `docs/adr/m5-plugin-deployment-pattern.md` — governing ADR; D1–D9 testable commitments; Risk Register inherits S1–S10 from Phase 1.
- `docs/plans/2026-05-09-cairn-m7-plugin-deployment-pattern.md` — M7 dispatch input contract.
- `.claude/skill-runs/plugin-deployment-pattern/` — full /decision verification trail (brief, P0, P0.5, P1, P2{A,B,C}, P3, P5).
- `docs/ARCHITECTURE.md:99` — INV-012 prose (machine-check pending M7).
- `docs/lessons.md` L-022 — manifest-schema validity as load-bearing prerequisite; round-trip the install, don't just build the artifact.
- `.claude/active-envelope.yaml` — expanded with M7 plan + lessons.md paths.
