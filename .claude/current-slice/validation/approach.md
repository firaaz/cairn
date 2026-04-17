---
slice: v1-defense-d3/bypass-log-test-resilience
phase: 2-validation
date: 2026-04-17
---

# Phase 2 — Validation approach

## Ambiguity enumeration (resolved)

Three ambiguities surfaced from intent §1-6 during Phase 2 ambiguity-pass. All
three were escalated to the operator one-at-a-time per brainstorming skill;
decisions below.

### Q1 — qualifier letter set: `[A-D]` or `[A-Z]`?

- **Intent §1-2** state `<letter> ∈ {A, B, C, D}` and fix the regex to
  `(?: \([A-D]\))?`.
- **ADR `d3-bypass-classification.md`** is silent on the qualifier letter set.
  The ADR firms class tokens only.
- **Operator decision: `[A-Z]`** — widen to match ADR silence. No letter-set
  gate. Rationale: test should not invent constraints the ADR does not
  specify; if a letter-set contract is desired later, the ADR is the right
  place to firm it.

### Q2 — `test_line_order_is_chronological`: date check or suffix-only?

- **Intent §6** drops the date from the chronological assertion and asserts
  only id-suffix monotonicity, keeping the test named `..._is_chronological`.
- Id-suffix monotonicity is a *proxy* for chronological order, not a
  guarantee: a future entry with a higher suffix but an earlier date would
  pass suffix-monotonicity and silently violate chronology.
- **Operator decision: tighten to BOTH** — assert id-suffix AND date are each
  monotonically non-decreasing across the full sequence. Rationale: keeps the
  test name honest; date field is already parsed by the widened regex at no
  additional cost.

### Q3 — Verification §3's 5 regex property checks: tests or manual table?

- **Intent Verification §3** allows the 5 regex properties to be discharged
  "by hand or table in implementation notes."
- Slice's whole premise is schema-driven-not-human-maintained. Leaving regex
  correctness to a notes-table reintroduces the class of fragility this slice
  exists to remove.
- **Operator decision: (a) parametrized unit test** — encoded as
  `test_classified_line_regex_schema` with 5 named cases
  (`no-qualifier`, `with-qualifier`, `missing-space`, `multi-letter`,
  `bogus-class`).

### Scope deferral (confirmed during Q3)

An architectural alternative was explored (dataclass / `strptime` / pyparsing
parsers instead of regex). **Intent §2 out-of-scope bullet explicitly blocks
`CLASSIFIED_LINE_RE` rewrite into a generator/dataclass.** Operator confirmed
minimal-widening-only path for this slice and deferred the parser redesign to
a future slice (tentatively `parser-for-d3-log` — not scheduled, not
queued).

## Test-design rationale

`tests/unit/test_d3_bypass_log_format.py` patched in-place. Envelope honored
(single file). Test-count: 10 → 11 functions = 15 test items (parametrize
expands the new function to 5 cases).

### Kept unchanged (migration-anchor contract)

- `test_log_file_exists` — existence check.
- `test_slice_012_reason_preserved`, `test_slice_014_reason_preserved`,
  `test_slice_016_reason_preserved` — byte-identical reason pins.
- `test_slice_017_line_byte_identical` — full-line byte-identical pin.
- `test_trailing_newline_exactly_one` — newline hygiene.
- Module-level constants `SLICE_012_REASON`, `SLICE_014_REASON`,
  `SLICE_016_REASON`, `SLICE_017_LINE` — byte-identical.

### Reshaped (count-driven → schema-driven)

- `test_log_has_exactly_four_lines` → **renamed**
  `test_log_has_at_least_four_lines`; assertion `== 4` → `>= 4`. Honesty:
  the new predicate is different enough to justify the name change.
- `test_all_lines_classified_pre_existing` → **renamed**
  `test_first_four_lines_classified_pre_existing`; iterates only the first
  four lines (migration anchors) and asserts each is `pre-existing`. The
  original dict-equality assertion over the full log is dropped because it
  cannot coexist with append-only growth.
- `test_line_order_is_chronological` — **name preserved, body reshaped**
  per Q2(b). (a) first four ids exactly `["SLICE-012", "SLICE-014",
  "SLICE-016", "SLICE-017"]`; (b) id-suffix monotonic non-decreasing; (c)
  date monotonic non-decreasing (ISO-8601 lexicographic == chronological).

### Added (new mechanical gate)

- `test_classified_line_regex_schema` — `@pytest.mark.parametrize` with 5
  named cases covering Verification §3's regex contract: positive for
  plain-class and qualifier-class lines, negative for missing-space,
  multi-letter, and bogus-class variants.

### CLASSIFIED_LINE_RE — deliberately NOT widened in Phase 2

The regex stays at its current narrow shape
(`(slice-caused|pre-existing|false-positive): `) for the Phase 2 commit.
Reason: Phase 2's TDD role is Skeptic (RED + Verify RED). The regex is the
"production code" of this test-only slice; widening it is Phase 3's job.
Phase 2 commits tests that *demand* the widening → tests fail RED → Phase 3
widens → tests pass GREEN.

**Phase 3 change (to be made): single-line edit at `CLASSIFIED_LINE_RE`:**
```python
r"^SLICE-\d+ \d{4}-\d{2}-\d{2} (slice-caused|pre-existing|false-positive)(?: \([A-Z]\))?: .+$"
```
Note: `[A-Z]` per Q1, NOT the intent-as-written `[A-D]`.

## RED evidence

`uv run pytest tests/unit/test_d3_bypass_log_format.py -v` → **2 failed, 13
passed**. Exactly the expected RED signal.

### Failure 1 — `test_every_line_matches_classified_regex`
```
AssertionError: line 5 does not match classified format:
'SLICE-018 2026-04-16 slice-caused (A): user-approved Phase 3 envelope
expansion deleted two legacy live-diff envelope-compliance fixtures ...'
```
Cause: narrow regex rejects the ` (A)` qualifier between class token and
colon. Live-log line 5 (and 6, first failing assertion halts iteration)
are the `SLICE-018` qualified entries. Phase 3's widening will accept them.

### Failure 2 — `test_classified_line_regex_schema[with-qualifier]`
```
AssertionError: regex match=False for line
'SLICE-018 2026-04-16 slice-caused (A): reason text', expected True
```
Cause: same — narrow regex rejects qualifier. Fixture line, not live-log.
Phase 3 widening fixes this.

### Passing cases (sanity)

- `test_classified_line_regex_schema[no-qualifier]` passes under narrow regex
  because `SLICE-020` lines have no qualifier — verifies the widened regex
  will not regress plain-class matching.
- `test_classified_line_regex_schema[missing-space|multi-letter|bogus-class]`
  all pass under narrow regex because the narrow regex correctly rejects all
  three. They will **continue** to pass under the widened regex because
  `\([A-Z]\)` is single-letter-only and the class alternation is unchanged.
- `test_first_four_lines_classified_pre_existing` passes because migration
  anchors have no qualifiers — narrow regex matches them.
- `test_line_order_is_chronological` passes because the current 7-line log
  is both suffix-monotonic (12,14,16,17,18,18,20) and date-monotonic
  (2026-04-14 ≤ ... ≤ 2026-04-17).

## Property verification table

(From intent Verification §3, encoded mechanically by
`test_classified_line_regex_schema`; table reproduced here for Phase 3
reviewer cross-check.)

| Case | Line | Narrow regex | Widened regex | Expected |
|---|---|---|---|---|
| no-qualifier | `SLICE-020 2026-04-17 pre-existing: reason text` | match | match | match |
| with-qualifier | `SLICE-018 2026-04-16 slice-caused (A): reason text` | reject | match | match |
| missing-space | `SLICE-018 2026-04-16 slice-caused(A): reason text` | reject | reject | reject |
| multi-letter | `SLICE-018 2026-04-16 slice-caused (AC): reason text` | reject | reject | reject |
| bogus-class | `SLICE-018 2026-04-16 bogus-class: reason text` | reject | reject | reject |

## Phase 3 guidance

1. Widen `CLASSIFIED_LINE_RE` exactly as shown above. Single-line edit.
2. Run `uv run pytest tests/unit/test_d3_bypass_log_format.py -v` → expect
   **15 passed**.
3. Run `uv run python scripts/integration_gate.py` → expect exit 0.
4. Record the one-line regex change + RED→GREEN evidence in
   `.claude/current-slice/implementation/notes.md`.

## Follow-ups (out of scope for this slice)

- **`parser-for-d3-log` slice** — replace regex-based validation with a
  dataclass parser (or `strptime` + structural tokenization). Requires
  amending intent §2 out-of-scope bullet; not queued. Decision deferred per
  operator.
- **Letter-set ADR amendment** — if the `{A, B, C, D}` set is load-bearing,
  firm it in `d3-bypass-classification.md` Decision 1 and tighten the regex
  back to `[A-D]`. Not queued; operator chose ADR-silence-first path.
