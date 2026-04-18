# SLICE-018 D3 bypass — out-of-band record

This file exists because SLICE-018 (`bypass-log-reclass`) is the slice that
normalizes `.claude/d3-bypasses.log` to the classified format. Appending its
own D3 finding to that log at close would break SLICE-018's own Phase 2
contract (4-line count, `pre-existing:4 slice-caused:0` distribution,
chronological ID order).

Operator chose option (a) from `sweep-notes.md` line 74: log out-of-band for
this slice only. This file is the out-of-band record. It will become
removable once the follow-up slice implementing ADR `d3-bypass-classification`
Decision 2's envelope `exempt:` syntax lands — that slice can either migrate
this entry into the main log or delete this file as obsolete.

## Bypass record

The line that would normally have been appended to `.claude/d3-bypasses.log`:

```
SLICE-018 2026-04-16 slice-caused: tests/unit/test_d3_bypass_log_format.py added via EXPAND_ENVELOPE=1 but not covered by intent envelope; logging in-place would violate this slice's own Phase 2 post-state pins
```

## Full context

See `.claude/current-slice/integration/sweep-notes.md` at commit `306a1d1`
(Phase 4 integration commit) for complete finding rationale, Phase 2 contract
citations (line 64/80/85 of `tests/unit/test_d3_bypass_log_format.py`), and
the three follow-up paths enumerated. That file is wiped on slice close per
ADR-002, but the content persists in git history.

## Protocol note

This deviates from the D3 bypass protocol's letter (`start-slice.full.md`
§"D3 bypass escape hatch"). `D3_GATE_BYPASS=1` was not set; the log append
was skipped to preserve Phase 2 post-state. The deviation is structural, not
operational — no mechanism existed to both log-in-place and satisfy the
migration slice's own contract.
