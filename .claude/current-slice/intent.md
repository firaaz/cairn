---
slice: d1-dogfood-instrumentation
date: 2026-04-12
phase: 1-intent
invariants-touched: []
adrs-referenced: [ADR-003]
envelope:
  - "docs/dogfood-log.md"
  - "scripts/dogfood_evaluate.py"
  - "tests/unit/test_dogfood_*.py"
out-of-scope:
  - "D1/D2/D3 automation themselves (separate slices)"
  - "Modifying existing validator or refresh-architecture command"
  - "Retroactive population of dogfood-log.md with pre-SLICE-004 entries"
  - "Automated hook integration (D1 automation writes to the log; this slice builds the log)"
---

### What and Why

ADR-003 commits to a dogfood gate: 10 completed slices post-ADR-003 OR 2026-10-11, whichever comes first. The gate evaluates whether D1/D2/D3 together catch ≥1 class of drift that manual integration-sweep Step 3 would have missed, and whether any defense has a false-positive rate high enough to force muting. No tracking substrate exists to record these signals. Without it, the dogfood evaluation at gate time becomes a memory exercise — exactly the failure mode cairn exists to prevent.

This slice builds the measurement substrate: a structured log (`docs/dogfood-log.md`) and an evaluation script (`scripts/dogfood_evaluate.py`) that reads the log and produces a pass/fail verdict against the ADR-003 dogfood criteria.

ADR-003 v1 contribution: D1 (instrumentation responsibility) + D0 (measuring the primary target failure mode).

### Specification Detail

**Log format** (`docs/dogfood-log.md`): YAML-frontmattered markdown. Each entry is a fenced YAML block with:
- `slice`: slice ID (e.g. SLICE-005)
- `date`: ISO 8601 date
- `defense`: which defense flagged (D1 | D2 | D3 | manual)
- `type`: catch | false-positive | friction
- `description`: one-line summary
- `would-manual-have-caught`: yes | no | unclear
- `disposition`: confirmed | muted | disputed

Entries are append-only. The file header carries a YAML frontmatter block with `schema-version: 1` for forward compatibility.

**Evaluation script** (`scripts/dogfood_evaluate.py`): stdlib-only Python. Reads `docs/dogfood-log.md`, parses all entry blocks, and evaluates:
1. **Catch-rate criterion**: ≥1 entry where `defense` ∈ {D1, D2, D3} AND `type` = catch AND `would-manual-have-caught` = no AND `disposition` = confirmed. Pass if ≥1 such entry exists.
2. **False-positive criterion**: for each defense, count entries where `type` = false-positive AND `disposition` = confirmed. Fail if any defense has ≥3 confirmed false positives (muting threshold). The threshold of 3 is a starting point; it can be adjusted by ADR supersession.
3. **Gate status**: report slice count since ADR-003 (from `sweep.yaml` current-slice-number minus 2, since ADR-003 landed between SLICE-001 and SLICE-002), whether 10-slice or date threshold is closer, and overall pass/fail/insufficient-data.

Exit codes: 0 = pass, 1 = fail, 2 = insufficient data (fewer than 10 post-ADR-003 slices and before deadline).

**Project-root resolution**: same pattern as `validate_architecture.py` — `$CLAUDE_PROJECT_DIR`, then `git rev-parse --show-toplevel`, then exit 2.

### Boundary

- This slice does NOT build D1/D2/D3 automation. It builds what they write to.
- This slice does NOT modify `scripts/validate_architecture.py` or any hook.
- This slice does NOT retroactively populate the log with pre-SLICE-004 entries. Prior slices had no instrumentation; fabricating entries would defeat the measurement.
- The false-positive threshold (3) is a provisional starting value, not an invariant commitment.

### Verification

1. `scripts/dogfood_evaluate.py` exits 2 when `docs/dogfood-log.md` has zero entries and slice count < 10.
2. `scripts/dogfood_evaluate.py` exits 0 when the log contains ≥1 confirmed catch entry with `would-manual-have-caught: no` and no defense exceeds the false-positive threshold.
3. `scripts/dogfood_evaluate.py` exits 1 when any defense has ≥3 confirmed false positives.
4. `scripts/dogfood_evaluate.py` exits 1 when 10+ post-ADR-003 slices exist but no confirmed automated catch.
5. Malformed entries (missing required fields) produce a stderr warning and are skipped, not a crash.
6. Project-root resolution follows the same three-step pattern as `validate_architecture.py`.
