"""Phase 2 RED — cost-discipline/track-0-telemetry (INV-009 introduction).

Spec:
 - .claude/current-slice/intent.md §Verification V11–V20
 - docs/plans/2026-04-23-cost-discipline-design.md §Track 0
 - docs/adr/cost-per-slice-budget.md (new, added by Phase 3)

Phase-3 contract asserted by this file:

 * `_state` dict gains six additive keys via `_init_state_dict`:
   `tokens_by_phase`, `cost_by_phase_usd`, `model_by_phase`,
   `tokens_total`, `cost_total_usd`, `pricing_snapshot`.
   `schema_version` stays `"1.0"` (additive-only per orchestrator-observability D4).

 * New module-level constant matching `^PRICING_TABLE_\\d{4}_\\d{2}_\\d{2}$`
   (a non-empty dict `{model_id: {input_per_1k, cache_creation_per_1k,
   cache_read_per_1k, output_per_1k}}`). `pricing_snapshot` is a deep-copy
   of this table at slice init (archive reinterpretability).

 * New helper `_record_phase_cost(phase, tokens, model)` — module-level,
   mutates `_state`, idempotent per-phase (overwrite on retry, not
   accumulate), recomputes `tokens_total` and `cost_total_usd` from the
   post-update dicts. Does NOT mutate `retries_by_phase`.

 * New helper `_parse_usage_envelope(raw_stdout)` — parses
   `claude -p --output-format json` stdout (JSON array shape observed in
   the P1 smoke-test at slice open) and returns the four-class tokens dict
   `{"input", "cache_creation", "cache_read", "output"}` — all non-negative
   ints.

 * `_generate_result_md(state)` extended with a `## Cost` section:
   a totals line (`$<X.XX> USD`, `<N>` tokens), one table row per populated
   phase (`phase | model | tokens | USD`), and a footer `pricing: <constant name>`.

 * INV-009 introduced-provisional. Module-level constants
   `INV_009_COST_THRESHOLD_USD` and `INV_009_TOKEN_THRESHOLD` default to
   None at introduction → the INV-009 check emits a `UserWarning`
   (advisory-only) rather than failing. When thresholds are later set to
   numeric values by a rebaseline slice, the check fails on breach.

Every test is expected to FAIL at Phase 2 — none of the helpers,
constants, or fields exist yet in `scripts/slice_orchestrator.py`.

Pytest + stdlib only. No Hypothesis (CLAUDE.md stdlib-only rule,
slice-rescope 2026-04-12). Property-style tests use `random.Random(seed)`
for determinism, precedent: tests/unit/test_context_discipline_protocol.py.
"""

from __future__ import annotations

import copy
import json
import random
import re
import warnings
from pathlib import Path

import pytest


PRICING_TABLE_NAME_RX = re.compile(r"^PRICING_TABLE_\d{4}_\d{2}_\d{2}$")

ROLES = (
    "phase-1-writer",
    "phase-2-skeptic",
    "phase-3-implementer",
    "phase-4-integrator",
)

TOKEN_CLASSES = ("input", "cache_creation", "cache_read", "output")


# --- Helpers ---------------------------------------------------------------


def _so(monkeypatch, tmp_path):
    """Import `slice_orchestrator` with a freshly-initialised module state
    rooted at an empty tmp worktree.

    Existing tests (test_state_schema.py, test_observability_writer.py) use
    the same recipe.
    """
    monkeypatch.chdir(tmp_path)
    import slice_orchestrator as so

    Path(".claude/orchestrator-debug").mkdir(parents=True, exist_ok=True)
    Path(".claude/current-slice").mkdir(parents=True, exist_ok=True)
    so._init_state_dict(slice_id="demo/slice-x")
    return so


def _pricing_constant(so):
    """Locate the single module attribute matching `PRICING_TABLE_<date>`.

    Returns `(name, table)`. Fails the calling test if zero or more than
    one candidate attribute is present (forces Phase 3 to land exactly
    one dated constant — the load-bearing dating convention).
    """
    hits = [n for n in dir(so) if PRICING_TABLE_NAME_RX.match(n)]
    assert len(hits) == 1, (
        "expect exactly one module attribute matching "
        "^PRICING_TABLE_\\d{4}_\\d{2}_\\d{2}$ in slice_orchestrator "
        f"(dating convention per intent §S4); found {hits!r}"
    )
    name = hits[0]
    table = getattr(so, name)
    assert isinstance(table, dict) and table, (
        f"{name} must be a non-empty dict; got {type(table).__name__}"
    )
    return name, table


def _first_known_model(table):
    """Pick a model-id whose entry carries all four *_per_1k keys."""
    for mid, prices in table.items():
        if all(f"{c}_per_1k" in prices for c in TOKEN_CLASSES):
            return mid
    pytest.fail(
        "no model entry in PRICING_TABLE carries all four *_per_1k keys; "
        f"table={table!r}"
    )


def _expected_cost(tokens, prices):
    """Reference formula (stdlib only, test-local, independent of prod code)."""
    return sum((tokens[c] / 1000.0) * prices[f"{c}_per_1k"] for c in TOKEN_CLASSES)


def _random_tokens(rng, cap=50_000):
    """Non-negative integer tokens dict with all four classes populated."""
    return {c: rng.randint(0, cap) for c in TOKEN_CLASSES}


# --- V11 — default-state defaults for the six additive fields -------------


def test_v11_six_cost_fields_present_with_empty_defaults(monkeypatch, tmp_path):
    """V11: freshly-initialized state carries all six cost fields at empty."""
    so = _so(monkeypatch, tmp_path)
    s = so._state
    assert s["tokens_by_phase"] == {}
    assert s["cost_by_phase_usd"] == {}
    assert s["model_by_phase"] == {}
    assert s["tokens_total"] == 0
    assert s["cost_total_usd"] == 0.0
    snap = s["pricing_snapshot"]
    assert isinstance(snap, dict) and snap, (
        "pricing_snapshot must be a non-empty dict at init (copied from the "
        "dated PRICING_TABLE constant)"
    )
    _, table = _pricing_constant(so)
    assert snap == table, (
        "pricing_snapshot at init must equal the module-level "
        "PRICING_TABLE_<date> constant verbatim (archive reinterpretability "
        "at cost-at-the-time, intent §S4)"
    )


def test_v11_schema_version_stays_at_1_0_after_additive_extension(
    monkeypatch, tmp_path
):
    """V1/V11 additive-only contract: schema_version MUST NOT bump."""
    so = _so(monkeypatch, tmp_path)
    assert so._state["schema_version"] == "1.0", (
        "cost fields are additive per orchestrator-observability D4 — "
        "never bump schema_version on additive extensions"
    )


def test_v11_pricing_snapshot_is_deep_copy_not_reference(monkeypatch, tmp_path):
    """Snapshot must survive mutation of PRICING_TABLE (and vice-versa)."""
    so = _so(monkeypatch, tmp_path)
    _, table = _pricing_constant(so)
    snap = so._state["pricing_snapshot"]
    mid = next(iter(snap))
    snap[mid]["input_per_1k"] = 999.999
    assert table[mid]["input_per_1k"] != 999.999, (
        "mutating state pricing_snapshot must not leak into PRICING_TABLE "
        "constant (archive reinterpretability at cost-at-the-time)"
    )


# --- V16 — PRICING_TABLE constant presence --------------------------------


def test_v16_pricing_table_constant_matches_regex_and_is_nonempty(
    monkeypatch, tmp_path
):
    """V16: dated module constant exists as a non-empty dict."""
    so = _so(monkeypatch, tmp_path)
    _, table = _pricing_constant(so)
    sample = next(iter(table.values()))
    assert "input_per_1k" in sample, (
        "at least one PRICING_TABLE entry must carry the `input_per_1k` "
        "key (intent §S1 field shape)"
    )


def test_v16_pricing_table_carries_four_per_1k_keys_per_model(monkeypatch, tmp_path):
    """Each priced model carries all four *_per_1k keys."""
    so = _so(monkeypatch, tmp_path)
    _, table = _pricing_constant(so)
    for mid, prices in table.items():
        for cls in TOKEN_CLASSES:
            key = f"{cls}_per_1k"
            assert key in prices, (
                f"PRICING_TABLE[{mid!r}] missing required key {key!r}; "
                f"all four of {TOKEN_CLASSES!r} must be priced"
            )
            assert isinstance(prices[key], (int, float))
            assert prices[key] >= 0.0


# --- V12 — JSON usage parsing ---------------------------------------------

# P1 smoke-test fixture captured 2026-04-24 via live
# `claude -p --output-format json` invocation. Top-level output is a JSON
# array; the terminal `type == "result"` element carries the authoritative
# usage block. Keys observed:
#   usage.input_tokens                    (new-session input tokens)
#   usage.cache_creation_input_tokens
#   usage.cache_read_input_tokens
#   usage.output_tokens
# Plus `modelUsage: {<model>: {inputTokens, outputTokens, cacheReadInputTokens,
#                             cacheCreationInputTokens, costUSD, ...}}`
# and a `result` field containing the agent's raw stdout.

FIXTURE_ENVELOPE_RAW = json.dumps(
    [
        {"type": "system", "subtype": "init", "session_id": "s1"},
        {
            "type": "assistant",
            "message": {
                "model": "claude-opus-4-7",
                "usage": {"input_tokens": 6, "output_tokens": 1},
            },
        },
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "duration_ms": 3173,
            "num_turns": 1,
            "result": '{"status":"OK","commit_hash":"abc","summary":"demo"}',
            "session_id": "s1",
            "total_cost_usd": 0.09977974999999999,
            "usage": {
                "input_tokens": 123,
                "cache_creation_input_tokens": 456,
                "cache_read_input_tokens": 789,
                "output_tokens": 321,
            },
            "modelUsage": {
                "claude-opus-4-7": {
                    "inputTokens": 123,
                    "outputTokens": 321,
                    "cacheReadInputTokens": 789,
                    "cacheCreationInputTokens": 456,
                    "costUSD": 0.09977974999999999,
                }
            },
        },
    ]
)


def test_v12_parse_usage_envelope_returns_exactly_four_token_classes(
    monkeypatch, tmp_path
):
    """V12: parser normalizes the claude envelope to a 4-key tokens dict."""
    so = _so(monkeypatch, tmp_path)
    parser = getattr(so, "_parse_usage_envelope", None)
    assert parser is not None, (
        "_parse_usage_envelope helper must exist — it extracts the 4-class "
        "tokens dict from `claude -p --output-format json` stdout. "
        "Name chosen in Phase 2; Phase 3 may rename but must update both sides."
    )
    tokens = parser(FIXTURE_ENVELOPE_RAW)
    assert set(tokens.keys()) == set(TOKEN_CLASSES), (
        f"parsed tokens dict must carry exactly {sorted(TOKEN_CLASSES)!r}; "
        f"got {sorted(tokens.keys())!r}"
    )
    for c in TOKEN_CLASSES:
        assert isinstance(tokens[c], int) and tokens[c] >= 0, (
            f"tokens[{c!r}] must be a non-negative int; got {tokens[c]!r} "
            f"(type {type(tokens[c]).__name__})"
        )


def test_v12_parse_usage_envelope_exact_values_from_fixture(monkeypatch, tmp_path):
    """V12: exact-value round-trip against the P1 smoke-test fixture."""
    so = _so(monkeypatch, tmp_path)
    parser = so._parse_usage_envelope
    tokens = parser(FIXTURE_ENVELOPE_RAW)
    assert tokens["input"] == 123
    assert tokens["cache_creation"] == 456
    assert tokens["cache_read"] == 789
    assert tokens["output"] == 321


# --- V13 — pricing attribution --------------------------------------------


def test_v13_record_phase_cost_uses_exact_pricing_arithmetic(monkeypatch, tmp_path):
    """V13: cost = sum_c (tokens[c]/1000) * snapshot[model][c_per_1k] — exact."""
    so = _so(monkeypatch, tmp_path)
    _, table = _pricing_constant(so)
    model = _first_known_model(table)
    rec = getattr(so, "_record_phase_cost", None)
    assert rec is not None, (
        "_record_phase_cost helper must exist (intent §S3); signature "
        "`_record_phase_cost(phase, tokens, model)` operating on `_state`"
    )
    tokens = {"input": 1000, "cache_creation": 0, "cache_read": 0, "output": 1000}
    rec("phase-1-writer", tokens, model)
    expected = _expected_cost(tokens, so._state["pricing_snapshot"][model])
    got = so._state["cost_by_phase_usd"]["phase-1-writer"]
    assert got == expected, (
        f"cost must be exact sum over 4 classes via pricing_snapshot; "
        f"expected {expected!r}, got {got!r}"
    )


def test_v13_record_phase_cost_populates_all_three_per_phase_dicts(
    monkeypatch, tmp_path
):
    """_record_phase_cost updates tokens_by_phase, cost_by_phase_usd,
    model_by_phase and recomputes totals in one call."""
    so = _so(monkeypatch, tmp_path)
    _, table = _pricing_constant(so)
    model = _first_known_model(table)
    rec = so._record_phase_cost
    tokens = {"input": 10, "cache_creation": 20, "cache_read": 30, "output": 40}
    rec("phase-2-skeptic", tokens, model)
    s = so._state
    assert s["tokens_by_phase"]["phase-2-skeptic"] == tokens
    assert s["model_by_phase"]["phase-2-skeptic"] == model
    assert "phase-2-skeptic" in s["cost_by_phase_usd"]
    assert s["tokens_total"] == sum(tokens.values()), (
        "tokens_total must be recomputed from the updated tokens_by_phase"
    )
    assert s["cost_total_usd"] == s["cost_by_phase_usd"]["phase-2-skeptic"], (
        "cost_total_usd must be recomputed from the updated cost_by_phase_usd"
    )


# --- V14 — idempotent retry (overwrite, not accumulate) -------------------


def test_v14_record_phase_cost_overwrites_tokens_on_redispatch(monkeypatch, tmp_path):
    """V14: redispatch of same phase overwrites (risk-register L166)."""
    so = _so(monkeypatch, tmp_path)
    _, table = _pricing_constant(so)
    model = _first_known_model(table)
    rec = so._record_phase_cost
    first = {"input": 100, "cache_creation": 200, "cache_read": 300, "output": 400}
    second = {"input": 7, "cache_creation": 11, "cache_read": 13, "output": 17}
    rec("phase-3-implementer", first, model)
    rec("phase-3-implementer", second, model)
    assert so._state["tokens_by_phase"]["phase-3-implementer"] == second, (
        "second dispatch must overwrite, not accumulate "
        "(design plan risk register L166: retries already counted in "
        "retries_by_phase)"
    )
    expected = _expected_cost(second, so._state["pricing_snapshot"][model])
    assert so._state["cost_by_phase_usd"]["phase-3-implementer"] == expected


def test_v14_record_phase_cost_does_not_touch_retries_by_phase(monkeypatch, tmp_path):
    """_record_phase_cost is orthogonal to retry accounting."""
    so = _so(monkeypatch, tmp_path)
    _, table = _pricing_constant(so)
    model = _first_known_model(table)
    rec = so._record_phase_cost
    before = copy.deepcopy(so._state.get("retries_by_phase", {}))
    rec(
        "phase-4-integrator",
        {"input": 1, "cache_creation": 1, "cache_read": 1, "output": 1},
        model,
    )
    rec(
        "phase-4-integrator",
        {"input": 2, "cache_creation": 2, "cache_read": 2, "output": 2},
        model,
    )
    after = so._state.get("retries_by_phase", {})
    assert after == before, (
        "_record_phase_cost must not mutate retries_by_phase — cost "
        "attribution is orthogonal to retry accounting"
    )


# --- V15 — JSON → MD Cost section -----------------------------------------


def _populate_two_phases(so):
    """Return the model id used; seeds two cost-populated phases."""
    _, table = _pricing_constant(so)
    model = _first_known_model(table)
    so._record_phase_cost(
        "phase-1-writer",
        {"input": 1000, "cache_creation": 500, "cache_read": 200, "output": 400},
        model,
    )
    so._record_phase_cost(
        "phase-3-implementer",
        {"input": 3000, "cache_creation": 800, "cache_read": 1200, "output": 600},
        model,
    )
    return model


def test_v15_result_md_has_cost_section_heading_and_pricing_footer(
    monkeypatch, tmp_path
):
    """V15: `## Cost` + `pricing: <PRICING_TABLE_<date>>` present in rendered MD."""
    so = _so(monkeypatch, tmp_path)
    pricing_name, _ = _pricing_constant(so)
    _populate_two_phases(so)
    so._state["status"] = "OK"
    so._state["phases_completed"] = ["phase-1-writer", "phase-3-implementer"]
    md = so._generate_result_md(so._state)
    assert "## Cost" in md, "Cost section heading missing from result MD"
    assert "pricing:" in md, "footer `pricing:` token missing from Cost section"
    assert pricing_name in md, (
        f"footer must reference the dated constant name {pricing_name!r}"
    )


def test_v15_result_md_cost_table_has_row_per_populated_phase(monkeypatch, tmp_path):
    """Each populated phase surfaces as a row in the Cost table."""
    so = _so(monkeypatch, tmp_path)
    model = _populate_two_phases(so)
    so._state["status"] = "OK"
    so._state["phases_completed"] = ["phase-1-writer", "phase-3-implementer"]
    md = so._generate_result_md(so._state)
    assert "## Cost" in md
    cost_section = md.split("## Cost", 1)[1]
    assert "phase-1-writer" in cost_section
    assert "phase-3-implementer" in cost_section
    assert model in cost_section, "model column must populate for each row"


def test_v15_result_md_cost_section_contains_totals_line(monkeypatch, tmp_path):
    """Totals line carries `tokens_total` integer and a `$...USD` marker."""
    so = _so(monkeypatch, tmp_path)
    _populate_two_phases(so)
    so._state["status"] = "OK"
    so._state["phases_completed"] = ["phase-1-writer", "phase-3-implementer"]
    md = so._generate_result_md(so._state)
    cost_section = md.split("## Cost", 1)[1]
    total_tokens = so._state["tokens_total"]
    assert str(total_tokens) in cost_section, (
        f"totals line must display tokens_total={total_tokens}"
    )
    assert "$" in cost_section and "USD" in cost_section, (
        "totals line must carry `$` and `USD` markers "
        "(intent §S5 format `Total: <N> tokens, $<X.XX> USD`)"
    )


# --- V17 — INV-009 introduced-provisional, advisory-only at introduction --


def _check_inv_009(state, cost_threshold, token_threshold):
    """Mirror the INV-009 machine check semantics (warn when None, assert otherwise).

    This function is the test-file assertion referenced by the ARCHITECTURE.md
    `invariant-check INV-009` block landing in Phase 3. At introduction both
    thresholds default to None → every check is advisory. When a rebaseline
    slice later substitutes numeric values in slice_orchestrator, the same
    check body fails loudly on breach.
    """
    tokens_total = state.get("tokens_total", 0)
    cost_total = state.get("cost_total_usd", 0.0)
    if cost_threshold is None or token_threshold is None:
        warnings.warn(
            "INV-009 advisory: thresholds TBD at introduction "
            f"(cost={cost_total!r}, tokens={tokens_total!r})",
            UserWarning,
            stacklevel=2,
        )
        return "advisory"
    assert cost_total <= cost_threshold, (
        f"INV-009: cost_total_usd={cost_total!r} exceeds threshold={cost_threshold!r}"
    )
    assert tokens_total <= token_threshold, (
        f"INV-009: tokens_total={tokens_total!r} exceeds threshold={token_threshold!r}"
    )
    return "pass"


def test_v17_inv_009_thresholds_default_to_none_at_introduction(monkeypatch, tmp_path):
    """INV-009 provisional: both threshold constants are None at intro."""
    so = _so(monkeypatch, tmp_path)
    cost_t = getattr(so, "INV_009_COST_THRESHOLD_USD", "MISSING")
    tok_t = getattr(so, "INV_009_TOKEN_THRESHOLD", "MISSING")
    assert cost_t is None, (
        "INV-009 introduced-provisional: module constant "
        "INV_009_COST_THRESHOLD_USD must default to None (advisory-only at "
        f"introduction, design OQ#1 recommendation). Got {cost_t!r}."
    )
    assert tok_t is None, (
        "INV-009 introduced-provisional: module constant "
        f"INV_009_TOKEN_THRESHOLD must default to None. Got {tok_t!r}."
    )


def test_v17_inv_009_check_warns_when_thresholds_tbd(monkeypatch, tmp_path):
    """V17: while thresholds are None, the check WARNS and does not raise."""
    so = _so(monkeypatch, tmp_path)
    state = {"tokens_total": 1_000_000, "cost_total_usd": 999.99}
    cost_t = getattr(so, "INV_009_COST_THRESHOLD_USD", None)
    tok_t = getattr(so, "INV_009_TOKEN_THRESHOLD", None)
    with pytest.warns(UserWarning, match="INV-009"):
        outcome = _check_inv_009(state, cost_threshold=cost_t, token_threshold=tok_t)
    assert outcome == "advisory"


def test_v17_inv_009_check_fails_when_numeric_threshold_exceeded(monkeypatch, tmp_path):
    """V17 contrapositive: once thresholds go numeric, breach must fail."""
    _so(monkeypatch, tmp_path)  # ensure module imports cleanly in tmp worktree
    state = {"tokens_total": 1_000_000, "cost_total_usd": 999.99}
    with pytest.raises(AssertionError, match="INV-009"):
        _check_inv_009(state, cost_threshold=1.0, token_threshold=100)


def test_v17_inv_009_check_passes_under_numeric_threshold(monkeypatch, tmp_path):
    """Sanity complement to the fail-on-breach case."""
    _so(monkeypatch, tmp_path)
    state = {"tokens_total": 10, "cost_total_usd": 0.01}
    outcome = _check_inv_009(state, cost_threshold=10.0, token_threshold=1_000)
    assert outcome == "pass"


# --- V18 — property: overwrite, not accumulate (Random(42), 50 triples) ---


def test_v18_property_last_write_wins_per_phase(monkeypatch, tmp_path):
    """V18: replayed final values match the LAST triple's tokens per phase."""
    so = _so(monkeypatch, tmp_path)
    _, table = _pricing_constant(so)
    model = _first_known_model(table)
    rec = so._record_phase_cost
    rng = random.Random(42)
    # Model is constant for this property; no need to thread it through the
    # triple. Store (phase, tokens) pairs for last-write-wins replay.
    applied: list[tuple[str, dict]] = []
    for _ in range(50):
        phase = rng.choice(ROLES)
        tokens = _random_tokens(rng)
        applied.append((phase, tokens))
        rec(phase, tokens, model)
    last: dict[str, dict] = {}
    for phase, tokens in applied:
        last[phase] = tokens
    for phase, tokens in last.items():
        assert so._state["tokens_by_phase"][phase] == tokens, (
            f"phase {phase!r} must reflect LAST triple's tokens, not an "
            f"accumulated sum; got "
            f"{so._state['tokens_by_phase'][phase]!r}, expected {tokens!r}"
        )
        expected = _expected_cost(tokens, so._state["pricing_snapshot"][model])
        assert so._state["cost_by_phase_usd"][phase] == expected, (
            f"phase {phase!r}: cost must be computed from LAST triple's tokens"
        )


# --- V19 — property: totals == sum-of-parts (Random(43), 10 trials) -------


def test_v19_property_totals_equal_sum_of_parts(monkeypatch, tmp_path):
    """V19: tokens_total and cost_total_usd recomputed from per-phase parts."""
    so = _so(monkeypatch, tmp_path)
    _, table = _pricing_constant(so)
    model = _first_known_model(table)
    rng = random.Random(43)
    for trial in range(10):
        so._init_state_dict(slice_id=f"demo/trial-{trial}")
        roles_subset = rng.sample(ROLES, k=rng.randint(1, 4))
        for phase in roles_subset:
            so._record_phase_cost(phase, _random_tokens(rng), model)
        expected_tokens = sum(
            v
            for phase_tokens in so._state["tokens_by_phase"].values()
            for v in phase_tokens.values()
        )
        assert so._state["tokens_total"] == expected_tokens, (
            f"trial {trial}: tokens_total must equal sum of all per-class "
            f"tokens across all phases; got "
            f"{so._state['tokens_total']!r}, expected {expected_tokens!r}"
        )
        expected_cost = sum(so._state["cost_by_phase_usd"].values())
        assert abs(so._state["cost_total_usd"] - expected_cost) < 1e-9, (
            f"trial {trial}: cost_total_usd must equal sum of per-phase "
            f"costs within 1e-9 float tolerance; got "
            f"{so._state['cost_total_usd']!r}, expected {expected_cost!r}"
        )


# --- V20 — property: non-negativity + zero-invariant ----------------------


def test_v20_property_cost_is_non_negative_for_100_random_inputs(monkeypatch, tmp_path):
    """V20: random non-negative tokens always yield non-negative cost."""
    so = _so(monkeypatch, tmp_path)
    _, table = _pricing_constant(so)
    model = _first_known_model(table)
    rec = so._record_phase_cost
    rng = random.Random(44)
    for i in range(100):
        so._init_state_dict(slice_id=f"demo/n-{i}")
        rec("phase-1-writer", _random_tokens(rng), model)
        got = so._state["cost_by_phase_usd"]["phase-1-writer"]
        assert got >= 0.0, f"iter {i}: cost must be non-negative; got {got!r}"


def test_v20_zero_tokens_yield_exactly_zero_cost_not_approximately(
    monkeypatch, tmp_path
):
    """V20: zero-tokens → 0.0 exactly (not within-tolerance)."""
    so = _so(monkeypatch, tmp_path)
    _, table = _pricing_constant(so)
    model = _first_known_model(table)
    zero = {"input": 0, "cache_creation": 0, "cache_read": 0, "output": 0}
    so._record_phase_cost("phase-1-writer", zero, model)
    assert so._state["cost_by_phase_usd"]["phase-1-writer"] == 0.0, (
        "zero tokens must yield exactly 0.0 cost, not approximately"
    )
    assert so._state["tokens_total"] == 0
    assert so._state["cost_total_usd"] == 0.0
