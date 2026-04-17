---
slice: v1-defense-d3/bypass-log-test-resilience
date: 2026-04-17
phase: 1-intent
invariants-touched: []
adrs-referenced: [d3-bypass-classification]
envelope:
  - "tests/unit/test_d3_bypass_log_format.py"
out-of-scope:
  - ".claude/d3-bypasses.log"           # not touching actual log contents
  - "scripts/**"                         # no runtime/check changes
  - "docs/adr/**"                        # schema stays; test catches up to it
  - "checks/**"                          # hook behavior unchanged
  - "CLASSIFIED_LINE_RE rewrite into a generator/dataclass"  # minimal widening only
---

### What and Why

`tests/unit/test_d3_bypass_log_format.py` was written in SLICE-018 Phase 2 against a 4-line migrated `.claude/d3-bypasses.log`. The file is append-only and has since grown to 7 entries; four assertions in the suite hardcode the shape of the original 4-line migration and now fail on every sweep. Sweep #14 Finding #1 called for resilience; sweep #15 re-confirmed the failures are 100% carried-over (not regressions). This slice patches the tests so the gate is schema-driven rather than count-driven, keeping the invariant anchors (byte-identical SLICE-012/014/016/017 reasons + chronological ordering) while tolerating post-migration growth.

### Specification Detail

1. **Classified-line schema (source of truth: `docs/adr/d3-bypass-classification.md` Decision 1).** Each log line matches:
   ```
   SLICE-<digits> <YYYY-MM-DD> <class>[ (<letter>)]: <reason>
   ```
   where `<class> ∈ {slice-caused, pre-existing, false-positive}` and the `(<letter>)` qualifier is **optional**, with `<letter> ∈ {A, B, C, D}`. The qualifier is observed in the current log on `slice-caused` entries (SLICE-018 `(A)`, SLICE-018 `(C)`) as a per-slice sub-tag; the test does not enforce semantics on the letter, only that the qualifier — when present — matches the shape `(<single-uppercase-letter>)` and sits between class-token and the colon, separated by a single space.
2. **`CLASSIFIED_LINE_RE` widens** to:
   ```
   ^SLICE-\d+ \d{4}-\d{2}-\d{2} (slice-caused|pre-existing|false-positive)(?: \([A-D]\))?: .+$
   ```
   The capture group on the class token is preserved so `test_all_lines_classified_pre_existing` can still inspect per-line class via `m.group(1)`.
3. **Migration-anchor pins stay byte-identical** (`SLICE-012`, `SLICE-014`, `SLICE-016`, `SLICE-017` reasons / `SLICE-017` full line / trailing-newline-exactly-one). These tests remain unchanged.
4. **Count assertion drops the `== 4` hardcode.** Replace with `>= 4` — the four migration anchors are a permanent floor; additions append only.
5. **Class-distribution assertion changes shape.** `test_all_lines_classified_pre_existing` currently asserts `counts == {"slice-caused": 0, "pre-existing": 4, "false-positive": 0}`. New shape: assert the **first four lines** are each `pre-existing` (the migration-anchor class contract from SLICE-018); the rest of the log is unconstrained by this test. A separate per-line regex test covers every line's schema compliance.
6. **Chronological-order assertion changes shape.** `test_line_order_is_chronological` currently asserts the id-list equals `["SLICE-012", "SLICE-014", "SLICE-016", "SLICE-017"]`. New shape: assert (a) the first four ids are exactly `["SLICE-012", "SLICE-014", "SLICE-016", "SLICE-017"]`, and (b) the full sequence of numeric suffixes (`int(id.split("-")[1])`) is monotonically non-decreasing. Duplicate suffixes are permitted — SLICE-018 already has two entries with `(A)` / `(C)` sub-tags.

### Boundary

**Explicitly out of scope:**
- Touching `.claude/d3-bypasses.log` itself. The tests catch up to the existing log; the log is not edited.
- Changing the classified-line schema in `docs/adr/d3-bypass-classification.md` or any companion doc.
- Refactoring the test file's structure (e.g., extracting fixtures or table-driven tests). Minimal regex + assertion edits only.
- Tightening or loosening hook behavior in `checks/*.sh` or `scripts/integration_gate.py`.
- Touching any other test file, even adjacent D3 tests.

### Verification

1. `uv run pytest tests/unit/test_d3_bypass_log_format.py -v` — all 10 tests pass against the current 7-entry `.claude/d3-bypasses.log`.
2. `uv run python scripts/integration_gate.py` — exit 0 (previously exit 1 on these tests).
3. Property verification (by hand or table in implementation notes):
   - `CLASSIFIED_LINE_RE` matches `SLICE-020 2026-04-17 pre-existing: …` (plain class, no qualifier).
   - `CLASSIFIED_LINE_RE` matches `SLICE-018 2026-04-16 slice-caused (A): …` (class + qualifier).
   - `CLASSIFIED_LINE_RE` does not match `SLICE-018 2026-04-16 slice-caused(A): …` (missing space before qualifier).
   - `CLASSIFIED_LINE_RE` does not match `SLICE-018 2026-04-16 slice-caused (AC): …` (multi-letter qualifier).
   - `CLASSIFIED_LINE_RE` does not match `SLICE-018 2026-04-16 bogus-class: …` (invalid class token).
4. The SLICE-012/014/016/017 reason-preservation tests continue to pass byte-identically.
5. No changes outside `tests/unit/test_d3_bypass_log_format.py` appear in `git diff --stat` at phase-3 close.
