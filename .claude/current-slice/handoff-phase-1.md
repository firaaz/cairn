---
slice: identifier-scheme/slice-and-feature-rename
phase: 1-intent
branch: feature/identifier-scheme
as-of: 2026-04-17 af660a5
---

## State
Phase 1 intent committed at `af660a5`. `adrs-referenced: [identifier-scheme, feature-slice-model]` — both exist in `docs/adr/`. D3 gate passes: no new ADRs required, intent references only landed ones.

## Next
Run `/start-slice phase 2` in a fresh session. Phase 2 Skeptic writes tests under `tests/unit/` covering the 10 verification items in `intent.md § Verification`.

## Blocked / Pending
- §9 ambiguity: `scripts/dogfood_evaluate.py` baseline. Options — (a) repurpose `dogfood-log.md adr-003-landed-at-slice` as commit-sha or slice-id, (b) drop field and read baseline from `docs/adr/cliff-failure-mode-and-v1-defenses.md` first-commit sha. Either is intent-compliant; record choice in `validation/approach.md` and `implementation/notes.md`.
- §8 sweep-due fallback on missing/unresolvable `last-sweep-at-slice-id` = "sweep due" + stderr diagnostic. Assert this behavior in tests.
- Slug renames in §3 are normative literal strings — tests assert `v1-defense-d2/code-invariant-binding`, `v1-defense-d2/assertion-block-migration`, `v1-defense-d3/automated-backstop`, `v1-defense-d3/ruff-cleanup`.

## Pointers
- `.claude/current-slice/intent.md` — only input for Phase 2 beyond ARCHITECTURE.md + cited ADRs. Do not read envelope source internals.
- `docs/adr/identifier-scheme.md` — §D2 (id shapes), D5 (feature metadata), D6 (name style), D7 (migration phases) authoritative.
- `docs/adr/feature-slice-model.md` — feature and slice entry schema.
