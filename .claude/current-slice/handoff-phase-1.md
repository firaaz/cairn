# SLICE-002 Phase 1 Handoff — handoff-catchup-protocol-rewrite

## What Phase 1 Produced

- `.claude/current-slice/intent.md` — three zones per template. YAML envelope lists 7 paths. Six contractual commitments in §Specification Detail (§1 handoff format, §2 banned sections, §3 catchup tiers, §4 slice closure wipe, §5 learning staging ground, §6 operational reference update). V1–V7 verification items.
- `.claude/current-slice/slice.yaml` — `id: SLICE-002`, `invariants-touched: [INV-002]`, `adrs-referenced: [ADR-002]`, `adrs-created: [ADR-002]`.
- `docs/adr/002-context-discipline-protocol.md` — pre-slice ADR formalizing the context-discipline protocol. `firmness: firm`. Authored ahead of slice init because the protocol is load-bearing for SLICE-003 and warranted architectural commitment rather than operational-reference convention.
- `docs/ARCHITECTURE.md` — refreshed with INV-002. Validator green: 2 invariants, 2 ADRs, ALL CHECKS PASSED.

Commits on `dev`: `2fc1931` (ADR + ARCHITECTURE refresh), `e10e305` (slice Phase 1 intent + SLICE-001 cleanup + sweep bump).

## Phase Gate

**Met.** `git log --oneline -- .claude/current-slice/intent.md` returns `e10e305`.

## What Phase 2 Should Load

- `.claude/current-slice/intent.md` — the test contract. Primary input.
- `docs/ARCHITECTURE.md` — INV-002 only. Everything else is scenery for Phase 2.
- `docs/adr/002-context-discipline-protocol.md` — listed in `adrs-referenced`; load if a borderline test-design call needs the ADR's reasoning.

## What Phase 2 Must NOT Load

- `docs/plans/2026-04-11-context-discipline-design.md` — the design document. Phase 2 builds from `intent.md` alone. The design doc has the full exploration (baselines, alternatives, measurement plan) that `intent.md` deliberately compressed into commitments. Loading it would leak the solution-space reasoning into test design — exactly what the soft-agent-split is supposed to prevent.
- `docs/reviews/2026-04-11-from-rag-session.md` — unrelated cross-project review.
- Any of this session's chat transcript or reasoning. Intent.md stands alone.

## Ambiguities Flagged for Phase 2

Nothing load-bearing. Two minor notes:

1. **V2 token-budget check** — intent.md says "the literal substring `150` and `400` both appear within 100 characters of the word `token`". This is a loose proxy for "documents the budget". Phase 2 may tighten (e.g. regex `150.*400.*token` or `150.*400 tokens`) or keep loose. Record the choice in `validation/approach.md`.

2. **V4 wipe-keyword list** — V4 accepts any of `wipe`, `rm -r`, `git rm`, `remove`, `delete` near `.claude/current-slice`. Deliberately inclusive because Phase 3 picks the mechanism. Phase 2 should NOT narrow to one verb.

## Test Target

New file: `tests/unit/test_context_discipline_protocol.py`. Structural/file-content assertions, not runtime. Check `checks/scope-guard.sh` lines 84–113 — the envelope lists the test file explicitly, so the write should be permitted without `EXPAND_ENVELOPE=1`.

## Envelope Reminder

Declared envelope from `intent.md`:

- `commands/claude-code/handoff.md`
- `commands/claude-code/catchup.md`
- `commands/claude-code/start-slice.md`
- `templates/handoff.md` (does not yet exist — Phase 3 creates it)
- `.claude/learning.md` (does not yet exist — Phase 3 creates it)
- `docs/operational-reference.md`
- `tests/unit/test_context_discipline_protocol.py` (Phase 2 creates)

Phase 2 touches only the last one. Phase 3 touches the rest. Do not expand without `EXPAND_ENVELOPE=1`.

## Context Isolation — What Phase 3 Will Not See

Phase 3 receives `intent.md` + the test file Phase 2 writes. It will NOT receive `.claude/current-slice/validation/approach.md` — the reasoning trace Phase 2 produces. That exclusion preserves the external-check property: Phase 3 sees the tests as a bare contract without the test-design rationale that might bias implementation toward "what the tests were thinking of" rather than "what the tests check".
