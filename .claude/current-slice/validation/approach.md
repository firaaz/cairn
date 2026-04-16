# Phase 2 — SLICE-018 bypass-log-reclass, approach

## Test file

`tests/unit/test_d3_bypass_log_format.py`. Pytest + stdlib only, matching
`test_context_budget.py` convention. 10 tests total.

## Ambiguities enumerated

| # | Question | Resolution | Source |
|---|---|---|---|
| A1 | Test path with non-source envelope? | `EXPAND_ENVELOPE=1` via `.claude/settings.local.json` → logged to `envelope-expansions.log` | `scope-guard.sh:94-114` auto-mirror only fires on Python basename matches; a `.log` envelope never auto-includes a test mirror |
| A2 | `<class>:` — colon or colon-space? | Colon-space (`<class>: `) | intent L47 regex has `: .+`; Specification Detail L40 says `inserting the pre-existing: marker` |
| A3 | SLICE-017 fixture source? | Hardcoded literal captured at Phase-2 authoring from current log state | intent verification 5 |
| A4 | Log path from tests? | `Path(__file__).resolve().parent.parent.parent / ".claude" / "d3-bypasses.log"` | `test_context_budget.py:16` convention |
| A5 | "No other file touched" — pytest? | No: scope-guard at write time + Phase 4 sweep notes | intent verification 7 |
| A6 | Trailing-newline precision? | `endswith('\n') and not endswith('\n\n')` | intent verification 6 |
| A7 | Line-order representation? | Extract slice-id per line, assert `['SLICE-012','SLICE-014','SLICE-016','SLICE-017']` | intent Specification Detail L45 |
| A8 | SLICE-012 reason boundary? | Text after `pre-existing: `; pinned string from intent table | intent Specification Detail table |

No ambiguity required human escalation.

## RED state (pre-migration, captured 2026-04-16)

10 tests; 5 fail, 5 pass. Failures cite the expected root cause (legacy
lines missing the `<class>: ` marker):

- `test_every_line_matches_classified_regex` — line 1 ('... pre-existing ruff lint ...') fails regex (no colon)
- `test_all_lines_classified_pre_existing` — same root cause
- `test_slice_012_reason_preserved` — line lacks `pre-existing: ` prefix
- `test_slice_014_reason_preserved` — line lacks `pre-existing: ` prefix
- `test_slice_016_reason_preserved` — line lacks `pre-existing: ` prefix

Passing tests are regression guards on properties the migration must
preserve:

- `test_log_file_exists`
- `test_log_has_exactly_four_lines`
- `test_line_order_is_chronological`
- `test_slice_017_line_byte_identical`
- `test_trailing_newline_exactly_one`

## Signal to future intent-writing

Intent.md's envelope listed only `.claude/d3-bypasses.log`; scope-guard's
auto-test-mirror rule at `scope-guard.sh:94-114` keys on basename match
against envelope patterns and does not fire for non-Python envelopes.
Phase 2 therefore required `EXPAND_ENVELOPE=1` to land the test file.

Two non-exclusive forward paths (both out of scope for this slice):

- Phase-1 Reader: when envelope contains non-source artifacts, also list
  the test file path explicitly (e.g. `tests/unit/test_<name>.py`).
- Substrate: broaden `scope-guard.sh` auto-mirror to match test files
  against any envelope entry's stem, not only Python source basenames.

Logged as `pre-existing` substrate-refinement signal — not tracked
against D3's noise budget per ADR `d3-bypass-classification` Decision 1.
