---
slice: v1-defense-d2/inv-002-binding-implementation
phase: complete
branch: feature/compression-followup
as-of: 2026-05-03 527a615
---

## State
INV-002 (a/b/c) and INV-008 ARCHITECTURE.md blocks flipped to `structural-parser` / `test-ref` per ADR `invariant-binding-strategy` D4–D7 at slice close `527a615`. Bindings remain on `<pending-slice-close-sha>` placeholder — **not effective in production**. Two known gaps surfaced post-close: (1) `parse_assertion_blocks` is a flat parser and cannot read INV-002's nested YAML; (2) `close_slice` bundled `sweep-notes.md` into `handoff.md`, blowing INV-002's 440-token budget (this handoff trimmed back to spec).

## Next
First-principles review pending per operator decision. Do not ship the SHA-substitution `docs:` follow-up until the parser gap and the close_slice bundling behavior are addressed. Sweep is due (`sweep-interval: 1`).

## Blocked / Pending
- INV-002 binding non-functional pending parser upgrade.
- `close_slice` bundles sweep-notes into handoff.md, blowing INV-002 budget.
- L-015 extractor disk-fallback — 2 XPASS(strict) reds remain (substrate Slice 4).
- INV-004 rebaseline for CC 2.1.126 (intermittent).
- `V1_ASSERTION_TYPES` allowlist hardcoded in tests; future cleanup slice.
- Phase-3-revert-under-RED-pressure prompt iteration.

## Pointers
- `docs/adr/invariant-binding-strategy.md` D4–D7 — design.
- `scripts/validate_architecture.py:151` (parser) and `:594` (`_run_structural_parser_assertion`).
- `tests/unit/test_inv_002_structural_parser.py:78` (Phase-2 deferral note) and `:353` (live-handoff test).
- `.claude/sweep-results/v1-defense-d2-inv-002-binding-implementation/artifacts/` — full slice artifacts incl. original sweep-notes.
