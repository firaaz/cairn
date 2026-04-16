# Phase 2 Approach — SLICE-017 housekeeping/inv004-rebaseline

## Ambiguity enumeration

1. **Provenance sentence exact wording.** Intent §Specification-Detail says "Append provenance sentence naming SLICE-017 and CC 2.1.110". Literal phrasing is not pinned. **Resolution:** Builder latitude on wording; Skeptic asserts both identifiers (`SLICE-017`, `2.1.110`) appear in the INV-004 paragraph. That constrains meaning without over-specifying form.

2. **`22k` literal in invariant-check description stays stale after re-baseline.** Intent §Specification-Detail line 40 declares the invariant-check fenced block (including `description`) "unchanged" — but its description string reads `"Points to the test suite that machine-checks the 22k token budget"`. Leaving it unchanged produces an internal mismatch between the invariant paragraph (`≤30,000`) and the description (`22k`). **Resolution:** Intent-as-stated wins; the description stays literally as-is. Flagged here so Phase 4 Auditor does not treat the mismatch as a regression — it is intentional per intent envelope scoping. If a future slice wants to clean this up, it is a separate edit under a different invariant-touched declaration.

3. **`uv.lock` diff is more than `requires-python`.** Intent §Specification-Detail line 48-49 mentions `requires-python = ">=3.11"` as the driving change, but `git diff uv.lock` shows the full dependency graph being populated (cairn, colorama, iniconfig, packaging, pluggy, pygments, pytest, pyyaml) — the prior file was effectively a header stub. **Resolution:** Intent line 50 says "the current file is the target state", which is an explicit commit-as-is directive regardless of diff size. No ambiguity after re-reading; the `requires-python` comment is just motivational prose, not a scope constraint.

4. **Aspirational `PASS|MISS` under new budget.** With current measurement `tokens=28511` and new `BUDGET_ASPIRATIONAL=25_000`, the post-regeneration measurement file line 6 will be `Aspirational (25000): MISS`. Intent item 2 line 6 allows either `PASS` or `MISS` but forbids stale `(20000)`/`(22000)`. **Resolution:** The `_record_measurement` f-string formats this automatically from the updated constants; no Builder decision required.

5. **`scripts/integration_gate.py` existence.** Verification item 7 relies on `python3 scripts/integration_gate.py`. **Resolution:** Verified present at repo root; not a phantom artifact.

## Test shape decision

Existing test `test_inv004_turn1_token_budget` is already RED under current state (28511 tokens > BUDGET_HARD=22000). Phase 3's constant bump to `BUDGET_HARD=30_000` flips it GREEN. No new pytest is needed to cover verification item 1.

Verification items 2, 4, 5, 6, 7 are stated by intent as Phase 4 Auditor grep/command evidence. Converting all of them to pytest assertions would exceed Skeptic scope. One gap is worth closing programmatically: the **documentation-contract** check for `docs/ARCHITECTURE.md` INV-004 paragraph (item 5). It is currently plain prose, it will be edited by the Builder, and a machine-checkable assertion reduces Auditor guesswork.

**New test added:** `test_inv004_architecture_rebaselined` in `tests/unit/test_context_budget.py` (co-located with the existing INV-004 test; file is in envelope, no envelope expansion needed).

Assertions:
- INV-004 paragraph contains `"≤30,000 total tokens"`
- INV-004 paragraph does NOT contain `"≤22,000"`
- INV-004 paragraph contains `"SLICE-017"` (provenance)
- INV-004 paragraph contains `"2.1.110"` (provenance)

Paragraph isolation: lines from `**INV-004**` marker to first subsequent blank line. No `claude` CLI dependency → runs unconditionally, not `skipif`-gated.

## Verify RED

Before handoff to Phase 3:
- `uv run pytest tests/unit/test_context_budget.py::test_inv004_architecture_rebaselined -v` must FAIL on the stale `≤22,000` text.
- `uv run pytest tests/unit/test_context_budget.py::test_inv004_turn1_token_budget -v` must FAIL on `28511 > 22000` (already known-RED, re-verified).

Both failures are recorded as Phase 2 exit evidence.

## Out of scope for Phase 2

- Running `claude -p hi` (measurement regeneration is Phase 3's work through the existing test).
- Editing `docs/ARCHITECTURE.md`, `uv.lock`, or the measurement file (all Phase 3 writes).
- Asserting measurement-file line-level content in pytest (the file is an output of the existing test; asserting its format statically is redundant with the constants it interpolates).
- Asserting `uv.lock` diff shape or `integration_gate.py` exit behavior (both are Phase 4 Auditor evidence per intent, not Skeptic territory).
