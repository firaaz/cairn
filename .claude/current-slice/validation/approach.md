# Phase 2 — Skeptic Approach

## Intent recap

Backfill `.claude/d3-bypasses.log` lines 18 and 19 (both authored by `substrate/orchestrator-paths`) with the `pre-existing:` classification token mandated by ADR `d3-bypass-classification` Decision 1. No regex change, no test relaxation, no new substrate.

## Existing RED today

`test_every_line_matches_classified_regex` already halts on line 18 — the recurring sweep-noise failure. It goes GREEN once substrate is well-formed; no edit needed.

## New Skeptic pins (S5 of intent — promoted from optional)

Three additions in `tests/unit/test_d3_bypass_log_format.py`:

1. `test_line_18_substrate_orchestrator_paths_pre_existing_pin` — full-line equality against the canonical post-backfill string per S1. Catches reason-text drift, punctuation edits, wrong-line backfill.
2. `test_line_19_substrate_orchestrator_paths_pre_existing_pin` — full-line equality per S2.
3. `test_lines_18_and_19_classified_pre_existing_via_regex` — parallel to the SLICE-012/014/016/017 migration-anchor `pre-existing` pin. Names the class explicitly so a class-only regression (e.g. `slice-caused` swap) diagnoses as "wrong class" not "reason mismatch", protecting V8 (rolling-window noise count stays at zero).

## Out of Skeptic scope

- No pytest assertion that lines 1–17 are byte-identical to pre-slice HEAD; V3 is a Phase-4 `git diff` check. Lines 1–4 are already pinned by migration-anchor tests; lines 5–17 are guarded by the schema regex plus chronological-order test.
- No new trailing-newline test (existing one suffices).
- No write-time hook — out-of-scope per S6 (provisional ADR + v0 reset).

## Drift note

Log now has 21 lines (entries 20–21 added since intent on 2026-05-02; both already classified `pre-existing`). The intent's "no lines after 19" claim is stale but harmless — backfill still targets the malformed rows at indices 17/18. Pins key on the `substrate/orchestrator-paths 2026-04-30 ` prefix, so a reorder fails loudly rather than passing on the wrong row.

## Run

```
uv run pytest tests/unit/test_d3_bypass_log_format.py
```

Today: 4 failed, 14 passed. After Phase 3 backfill: 18 passed.
