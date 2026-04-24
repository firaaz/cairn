# Phase 4 Handoff — cost-discipline/track-0-telemetry

**Status**: OK (slice close-ready)
**Date**: 2026-04-24 (post-rewind re-run)
**Auditor commits reviewed**: `438bd2c`, `f06a220`, `f693878`, `0bac248`
**Phase-3 handoff commit**: `d3e5baf`

## What this handoff is

This handoff terminates Phase 4 with `OK`. The orchestrator's `close_slice` is the sole commit source for the terminal `slice: complete` commit (INV-008 DC-4 / spec-v1.md §13). Phase 4 has not run `git commit` and will not.

## Resolution summary (vs prior RAISE_ISSUE handoff)

The previous Phase-4 handoff (commit history `438bd2c..d718c7e`) returned RAISE_ISSUE on two grounds:

1. **V3 dispatch-site gap** — `_record_phase_cost` / `_parse_usage_envelope` existed as helpers but had zero callers in `_dispatch_once`. Telemetry was dead code.
2. **INV-009 introduction broke `test_invariant_assertions.py`** — the test file's `EXPECTED_INVARIANT_IDS` constant hardcoded `{INV-001..INV-008}` and was not in any envelope.

Operator chose Option A from the prior handoff's recommendations: amend the envelope (`5223d53`), rewind to phase 3 (`0dca9e2`), re-dispatch the `orchestrator-cost-plumbing` cluster only (`0bac248`). The re-dispatch landed:

- `--output-format json` in the dispatch `cmd` list at `scripts/slice_orchestrator.py:1262–1263`.
- A `try`-wrapped `_record_phase_cost(role, _parse_usage_envelope(stdout), _extract_envelope_model(stdout))` call at `:1316–1320` inside `_dispatch_once`.
- A companion `_extract_agent_result_text` helper at `:390–416` so `_parse_structured_tail` continues to consume the agent's status tail through the new envelope.
- Widened `EXPECTED_INVARIANT_IDS = {f"INV-{n:03d}" for n in range(1, 10)}` at `tests/unit/test_invariant_assertions.py:1115`.

Result: 722 passed / 0 failed / 3 skipped (was 720 + 2 failed). Architecture validator GREEN with 9 invariants verified. All five declared invariants PASS with file:line evidence — full table in `integration/sweep-notes.md`.

## Verification artifacts

- `integration/sweep-notes.md` (mandatory per Phase-4 spec) — contains the per-invariant PASS/FAIL table + V1–V22 structural-check matrix + V11–V20 behavioral-check matrix + regression notes.
- `slice.yaml` — `current_phase: 4`, `status: in-progress` (the orchestrator's `close_slice` flips status to `complete`).
- `.claude/handoff.md` — rotated to reflect Track-0 close + queued next slice.
- `.claude/sweep.yaml` — `last-sweep-at-slice-id` advanced to `cost-discipline/track-0-telemetry`; interval unchanged.

## Runnable-check gate

```
uv run pytest                              → 722 passed, 3 skipped, 0 failed
uv run python scripts/validate_architecture.py → ALL CHECKS PASSED (9 invariants, 15 ADRs)
```

## Invariants

| Invariant | Status |
|---|---|
| INV-009 (introduced, provisional, advisory-only) | PASS |
| INV-003 (phase contracts unchanged) | PASS |
| INV-004 (`/status` output bounded) | PASS |
| INV-006 (feature file always-create) | PASS |
| INV-008 (`close_slice` lifecycle untouched) | PASS |

Detailed file:line evidence per row in `integration/sweep-notes.md`.

## What Phase 4 did NOT do (per DC-4)

- Did NOT run `git commit`. Sole `slice: complete` commit comes from `close_slice`.
- Did NOT edit source or tests. All Phase-3 work was already committed by the re-dispatch on the amended envelope.
- Did NOT touch ADR frontmatter (no `ADR_EDITORIAL_FIX=1` invocation needed).

## Pointers

- Sweep notes (authoritative evidence): `.claude/current-slice/integration/sweep-notes.md`
- Intent (post-amendment envelope): `.claude/current-slice/intent.md`
- Phase-3 re-dispatch commit closing the V3/V21/V22 gaps: `0bac248`
- Architecture validator output: all-green; INV-009 wiring consistent.

---
# cost-discipline/track-0-telemetry — Phase 4 Integration Sweep Notes

**Slice**: `cost-discipline/track-0-telemetry`
**Phase**: 4 (Integration)
**Role**: Auditor
**Date**: 2026-04-24 (re-run after operator-adjudicated rewind)
**Builder commits under audit (post-rewind)**:
- `0bac248` — `phase-3: cost-discipline/track-0-telemetry — orchestrator-cost-plumbing (re-dispatch)` (lands V3 dispatch-site wiring + V21 callers + V22 test-guard widen)
- `f06a220` — `phase-3: cost-discipline/track-0-telemetry — invariant-codification` (carries forward: ADR + ARCHITECTURE.md INV-009)
- `f693878` — `phase 3 (docs-and-status-surface): cost surfacing + INV-009 docs` (carries forward: operational-reference + status surfaces + feature file)
- `438bd2c` — `phase-3: cost-discipline/track-0-telemetry — orchestrator-cost-plumbing` (carries forward: helpers + state fields + PRICING_TABLE + Cost section)

**Phase-3 handoff commit**: `d3e5baf` (`handoff: phase 3 complete`)
**Re-dispatch trigger**: `5223d53` (envelope amendment) → `0dca9e2` (rewind to phase 3)

**Verdict**: **PASS** — slice is close-ready. All structural checks (V1–V22), all behavioral checks (V11–V20), all five declared invariants (INV-003 / INV-004 / INV-006 / INV-008 / INV-009) hold with file:line evidence. Both prior-Phase-4 RAISE_ISSUE grounds (V3 dispatch-site gap; INV-009 trips `test_invariant_assertions.py` via hardcoded `EXPECTED_INVARIANT_IDS`) were addressed by the re-dispatch on the amended envelope.

---

## Runnable-check summary

### `uv run pytest`

```
722 passed, 3 skipped in 51.85s
```

Zero failures. The two prior `tests/unit/test_invariant_assertions.py` regressions documented in the previous Phase-4 sweep (`test_no_extra_assertion_blocks`, `test_invariant_count_unchanged`) are resolved by `tests/unit/test_invariant_assertions.py:1115` widening to `range(1, 10)` (V22 satisfied). Cost-telemetry suite unchanged at 22/22 GREEN (`tests/unit/test_slice_orchestrator_cost.py`); confirmed via targeted re-run with `tests/unit/test_context_budget.py` + `tests/unit/test_invariant_assertions.py` → `71 passed`.

### `uv run python scripts/validate_architecture.py`

```
ALL CHECKS PASSED
  Invariants verified: 9
  ADR files checked: 15
```

INV-009 recognised by validator. ADR/ARCHITECTURE wiring consistent.

---

## Invariants table (mandatory per Phase 4 spec)

One row per declared invariant with PASS/FAIL and `file:line` evidence.

| Invariant | Status | Evidence |
|---|---|---|
| **INV-009** (introduced, provisional, advisory-only) | **PASS** | ADR: `docs/adr/cost-per-slice-budget.md:5` (`firmness: provisional`) + `:1–13` frontmatter; body contains 17 occurrences of `X TBD` / `Y TBD` / `rebaseline` (V6 satisfied). ARCHITECTURE: `docs/ARCHITECTURE.md:85` (`**INV-009**` entry with `(cost-per-slice-budget)` citation) + `:87–91` (`invariant-check INV-009` block pointing to `tests/unit/test_slice_orchestrator_cost.py`) (V7 satisfied). Module constants: `scripts/slice_orchestrator.py:101–102` (`INV_009_COST_THRESHOLD_USD = None`, `INV_009_TOKEN_THRESHOLD = None`) — advisory-only at introduction per OQ#1. Machine-check: `tests/unit/test_slice_orchestrator_cost.py::_check_inv_009` (V17 GREEN — warns rather than raises while thresholds are `None`). Validator green: `validate_architecture.py` reports `Invariants verified: 9`. |
| **INV-003** (phase contracts unchanged) | **PASS** | `git diff HEAD~4 HEAD -- commands/claude-code/start-slice.md .claude/agents/` returns empty. Phase-Skill-Guide section of `docs/operational-reference.md` (`:74–106`) unchanged; the three Track-0 additions land in a new section at `:337–369`. Dispatch-plumbing edits in `scripts/slice_orchestrator.py` are orchestrator-internal and do not alter the phase-contract surface. |
| **INV-004** (`/status` output bounded) | **PASS** | `commands/claude-code/status.md:14` (one literal cost line: `Cost: <N> tokens · $<X.XX> USD (this slice)`) + `:24` (per-slice-only contract: "this line never totals prior slices"). `commands/claude-code/status.full.md:26` (one cost line; "Prior slices' totals are not summed in"). `grep -i 'cumulative\|across slices\|multi-slice' commands/claude-code/` returns no matches. `tests/unit/test_context_budget.py` GREEN in the targeted re-run. |
| **INV-006** (feature file always-create) | **PASS** | `.claude/features/cost-discipline.yaml:7` (`id: cost-discipline/track-0-telemetry`) + `:10–12` (`cost-discipline/lever-1-per-phase-model` with `after: [cost-discipline/track-0-telemetry]`). YAML structurally valid (loaded by feature loader; no validator errors). |
| **INV-008** (`close_slice` lifecycle untouched) | **PASS** | `git diff HEAD~5 HEAD -- scripts/slice_orchestrator.py` over `close_slice` / `_is_slice_already_closed` / `_wipe_current_slice` / `_bundle_handoff_md` / resume-matrix function bodies returns empty (verified via line-targeted regex grep against the diff). Existing state-persist atexit writer captures the new additive cost fields at close — no new commit site introduced. |

---

## Verification-check pass/fail (intent.md §V1–V22)

Structural (Phase 4 Auditor, file/grep evidence):

| Check | Status | Evidence |
|---|---|---|
| V1 — six additive fields in `_init_state_dict`, zero/empty defaults; `schema_version == "1.0"` | **PASS** | `scripts/slice_orchestrator.py:329–334` lists all six keys (`tokens_by_phase`, `cost_by_phase_usd`, `model_by_phase`, `tokens_total`, `cost_total_usd`, `pricing_snapshot`) with `{}` / `0` / `0.0` / `copy.deepcopy(_active_pricing_table())`. `schema_version` literal unchanged at `"1.0"`. |
| V2 — Module-level `PRICING_TABLE_<YYYY_MM_DD>` dict; entries contain `input_per_1k` | **PASS** | `scripts/slice_orchestrator.py:70` (`PRICING_TABLE_2026_04_24 = {`); `:71–89` enumerate `claude-opus-4-7`, `claude-sonnet-4-5`, `claude-haiku-4-5` each with `input_per_1k` / `cache_creation_per_1k` / `cache_read_per_1k` / `output_per_1k`. `_PRICING_TABLE_NAME_RX` at `:91` enforces dating convention. |
| V3 — Dispatch-site `cmd` list contains `"--output-format", "json"` | **PASS** | `scripts/slice_orchestrator.py:1262–1263` inside `_dispatch_once` (`cmd = [...]` at `:1255`), the literal pair appears between `PERMISSION_MODE` and the `json.dumps(inputs)` payload. (Was the V3 FAIL ground in the prior sweep; resolved by `0bac248`.) |
| V4 — `_record_phase_cost(phase, tokens, model)` helper exists with matching signature | **PASS** | `scripts/slice_orchestrator.py:472` (`def _record_phase_cost(phase, tokens, model):`). |
| V5 — `_generate_result_md` produces `## Cost` + `pricing:` when any phase has tokens | **PASS** | `scripts/slice_orchestrator.py:662` (gate: `if tokens_by_phase:`), `:668` (`lines.append("## Cost")`), `:683` (`lines.append(f"pricing: {pricing_name}")`). V15 (cost-test) green-covers the projection. |
| V6 — ADR exists, `firmness: provisional`, body contains `INV-009`, `X TBD`, `Y TBD`, rebaseline prose | **PASS** | `docs/adr/cost-per-slice-budget.md:5` (`firmness: provisional`); 17 occurrences of `X TBD` / `Y TBD` / `rebaseline` tokens across the body (per grep). |
| V7 — ARCHITECTURE.md has `**INV-009**` entry + sibling `invariant-check INV-009` block, with `(cost-per-slice-budget)` citation | **PASS** | `docs/ARCHITECTURE.md:85` (entry with citation) + `:87–91` (block, `pattern: "tests/unit/test_slice_orchestrator_cost.py"`). |
| V8 — operational-reference.md documents PRICING_TABLE convention, INV-009 advisory semantics, Cost section | **PASS** | `docs/operational-reference.md:337` (PRICING_TABLE convention) + `:343–354` (INV-009 advisory semantics with warn-vs-fail switch) + `:356–364` (Cost section + `/status` one-line surfacing). |
| V9 — status.md + status.full.md each have one cost-surfacing line; neither uses `cumulative` / `across slices` on cost | **PASS** | `commands/claude-code/status.md:14,24` + `commands/claude-code/status.full.md:26`. `grep -i 'cumulative\|across slices\|multi-slice' commands/claude-code/` returned no matches. |
| V10 — feature file exists, lists both slices with `after:` edge | **PASS** | `.claude/features/cost-discipline.yaml:7,10–12` (see INV-006 row). |
| **V21** (Amendment 2026-04-24) — `_dispatch_once` calls `_record_phase_cost(` and `_parse_usage_envelope(` outside their `def` lines | **PASS** | `scripts/slice_orchestrator.py:1316` (`_record_phase_cost(`), `:1318` (`_parse_usage_envelope(stdout)`), wrapped in a defensive `try/except` at `:1315–1325` per intent §S2.d. Calls are inside `_dispatch_once` (function header at `:1172`). (Was the V21 root-cause ground in the prior sweep; resolved by `0bac248`.) |
| **V22** (Amendment 2026-04-24) — `EXPECTED_INVARIANT_IDS` widened to include `INV-009`; `pytest` exits zero | **PASS** | `tests/unit/test_invariant_assertions.py:1115` (`EXPECTED_INVARIANT_IDS = {f"INV-{n:03d}" for n in range(1, 10)}` — note the `range(1, 10)` upper bound). `uv run pytest tests/unit/test_invariant_assertions.py` GREEN inside the 71-test targeted run (`71 passed in 8.22s`). |

Behavioral (Phase 2 Skeptic test file, Phase 4 Auditor verifies green):

| Check | Status | Evidence |
|---|---|---|
| V11 — defaults: empty dicts, zero ints, non-empty `pricing_snapshot` | **PASS** | `tests/unit/test_slice_orchestrator_cost.py` — 22/22 pass (full-suite + targeted run). |
| V12 — JSON-envelope usage parser yields four-key tokens dict, non-negative ints | **PASS** | same. `_parse_usage_envelope` at `scripts/slice_orchestrator.py:340` enforces `_nn(...)` non-negative coercion. |
| V13 — pricing attribution matches exact arithmetic | **PASS** | same. `_cost_for_tokens` at `scripts/slice_orchestrator.py:455` uses identical generator-expression shape to the test reference (intent §V13). |
| V14 — idempotent retry: second call overwrites, does not sum | **PASS** | same. `_record_phase_cost` at `:472` recomputes totals from per-phase dicts post-update. |
| V15 — JSON→MD Cost section round-trips two populated phases | **PASS** | same. `_generate_result_md` Cost section at `scripts/slice_orchestrator.py:658–684`. |
| V16 — module exposes attribute matching `^PRICING_TABLE_\d{4}_\d{2}_\d{2}$`, non-empty dict | **PASS** | same. `_active_pricing_table_name` at `:105–116` walks globals. |
| V17 — INV-009 advisory check warns (not raises) when thresholds are `None` | **PASS** | same. Module constants at `:101–102` hold `None`. |
| V18 — idempotency property (50 triples, overwrite-not-sum) | **PASS** | same (seeded `random.Random(42)`, stdlib-only per CLAUDE.md). |
| V19 — additivity property (totals = sum-of-parts across 10 random states) | **PASS** | same (seeded `random.Random(43)`, float tolerance `1e-9` for cost). |
| V20 — non-negativity + zero-invariant property | **PASS** | same (seeded `random.Random(44)`, exact zero on zero-tokens). |

---

## Regression check — adjacent modules

- `scripts/slice_orchestrator.py`: All Track-0 additions (cost telemetry block at `:62–102`, helpers at `:340–525`, dispatch-site wiring at `:1262–1325`, MD Cost section at `:658–684`) sit in clearly-bounded sections. `_dispatch_once` retained byte-identical timeout/error handling at `:1266–1300`; `_run_with_live_stderr`, `close_slice` (`:2032–2120+`), `_wipe_current_slice`, `_bundle_handoff_md`, and the resume matrix are unchanged. Confirmed via `git diff HEAD~5 HEAD -- scripts/slice_orchestrator.py | grep '^[-+] *def '` returning only the new helper `def` lines (no removals).
- `docs/ARCHITECTURE.md`: INV-009 entry + invariant-check block appended cleanly after INV-008 (`:85–91`); INV-001..INV-008 untouched.
- `docs/operational-reference.md`: three new sub-sections at `:337–364` appended cleanly; Phase Skill Guide (`:74–106`) untouched (preserves INV-003).
- `commands/claude-code/status.md`: one cost line + prose at `:14,24`; existing six-line, ≤1500-char dashboard (line 3) preserved (INV-004).
- `commands/claude-code/status.full.md`: one cost line at `:26`; existing contract preserved.
- `.claude/features/cost-discipline.yaml`: created this slice per INV-006 always-create; lists two slices with `after:` edge for sequencing.
- `tests/unit/test_invariant_assertions.py`: single one-line widening at `:1115` per envelope amendment 2026-04-24; no other edits.
- `tests/unit/test_slice_orchestrator_cost.py`: new test file (22 tests) per envelope §S2.

**Regression verdict**: NONE. Full suite 722 passed / 0 failed / 3 skipped (vs the 720 + 2 failed at the prior Phase-4 verdict — net +2 PASS, -2 FAIL).

---

## How both prior RAISE_ISSUE grounds were resolved

**Ground 1 (V3 dispatch-site integration)** → resolved by `0bac248` re-dispatch, which (a) inserted `"--output-format", "json"` into the `cmd` list at `scripts/slice_orchestrator.py:1262–1263`, (b) wired a defensive call `_record_phase_cost(role, _parse_usage_envelope(stdout), _extract_envelope_model(stdout))` at `:1316–1320` inside `_dispatch_once`, (c) introduced a companion `_extract_agent_result_text` helper at `:390–416` so the existing `_parse_structured_tail` can keep consuming the agent's status tail through the new envelope. The error-tolerance contract from intent §S2.d is honoured by the `try/except` at `:1315–1325`: a malformed envelope yields zero tokens and an empty model id, never crashes the dispatcher.

**Ground 2 (INV-009 introduction breaks `test_invariant_assertions.py`)** → resolved by `0bac248` widening `EXPECTED_INVARIANT_IDS = {f"INV-{n:03d}" for n in range(1, 10)}` at `tests/unit/test_invariant_assertions.py:1115`. The envelope amendment landed at commit `5223d53` added `tests/unit/test_invariant_assertions.py` to the in-scope list (`intent.md:20`) so the edit was within Phase-3's permitted surface.

**Ground 3 (combined envelope-scoping bug in Phase 1)** → resolved structurally by the envelope amendment + V21/V22 verification additions in `intent.md:162–163`. Future invariant-introducing slices now have a ready precedent for naming the test-guard constant in their envelope.

---

## Slice-close readiness

- Phase 4 gate (envelope committed): GREEN — Phase 3 commits present (`f693878`, `438bd2c`, `f06a220`, `0bac248`); V3 + V21 + V22 satisfied; no test regressions caused by this slice.
- INV-009: PASS (advisory introduction per design intent; thresholds `None` → warn-only).
- INV-003 / INV-004 / INV-006 / INV-008: PASS.
- Runnable-check gate: 722 pass / 0 fail / 3 skipped.
- Slice **IS** close-ready. Returning OK to the orchestrator; `close_slice` is the sole commit source for the terminal `slice: complete` commit per INV-008 DC-4.
