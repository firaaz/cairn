---
slice: integration-gate/configurable-pytest-timeout
phase: 2-validation
date: 2026-04-17
---

# Validation Approach

## D-commitment tie (ARCHITECTURE.md:102 compliance)

Intent does not carry an explicit `d-contribution:` field, but the "What and
Why" section names the contribution unambiguously: this slice reduces
false-positive D3 bypasses logged to `.claude/d3-bypasses.log` (5 of the 10
most recent bypasses are traced to the pytest 120s ceiling being exceeded by
downstream consumers with larger suites). The slice therefore contributes to
**D3 signal-preservation** — the bypass log's `3-in-10 → design-review`
trigger counts only `false-positive` entries (ADR-003, as refined by
`d3-bypass-classification` 2026-04-16), so a configurable timeout that
removes infrastructure-class false positives directly strengthens the
mechanism D3 gates on.

Observation for integration-sweep: intent.md frontmatter does not currently
carry a structured D-contribution field. A future lint rule enforcing this
declaration — or a schema update to `intent.md`'s envelope — would convert
ARCHITECTURE.md:102's soft-spoken rule into mechanical enforcement.

## Mocking posture

Tests patch `integration_gate.subprocess.run` directly via
`unittest.mock.patch` (no `pytest-mock` dep is declared in `pyproject.toml`).
Env vars are controlled via pytest's built-in `monkeypatch` fixture. The
patch target is the full module-path string `"integration_gate.subprocess.run"`
(not `patch.object` on the module reference) to remain stable under the
existing `import subprocess` pattern at `scripts/integration_gate.py:17`.

**Rationale:** the intent declares the only behavior change is the `timeout=`
kwarg on `subprocess.run`. Patching `subprocess.run` and asserting on the
captured call kwargs is the most surgical realization — it exercises the
exact code path the spec describes without spawning real subprocesses, and
requires no refactor inside the envelope (an `_run_subprocess` helper seam
was considered and rejected as envelope creep).

## Check-to-test mapping

| Intent check | Test | Class |
|---|---|---|
| 1. `CAIRN_PYTEST_TIMEOUT=300` → `timeout=300` | `test_env_override_applies` | `TestPytestTimeoutOverride` |
| 2. `CAIRN_RUFF_TIMEOUT=10` → `timeout=10` | `test_env_override_applies` | `TestRuffTimeoutOverride` |
| 3. No env → pytest `timeout=120` | `test_default_when_unset` | `TestPytestTimeoutOverride` |
| 4. No env → ruff `timeout=60` | `test_default_when_unset` | `TestRuffTimeoutOverride` |
| 5. Empty string → default | `test_invalid_falls_back_to_default[empty]` | both |
| 6. Non-numeric → default | `test_invalid_falls_back_to_default[non_numeric]` | both |
| 7. `"0"` → default | `test_invalid_falls_back_to_default[zero]` | both |
| 8. `"-5"` → default | `test_invalid_falls_back_to_default[negative]` | both |
| 9. Invalid → no stdout/stderr pollution | `test_invalid_env_produces_no_new_output` (×6 param) | `TestSilentFallback` |
| 10. Existing exit-code assertions intact | (covered by existing `tests/unit/test_integration_gate.py`) | — |

Float (`"1.5"`) is added as an extra parametrize case alongside checks 5-8,
matching intent.md:30's enumeration of invalid forms. Check 10 is satisfied
by the existing suite continuing to pass — no duplication needed here.

## Bisected-TDD adaptation (verify-RED disclosure)

Per Phase Skill Guide: *"TDD's red-green cycle is structurally bisected by
cairn's session boundary: the Skeptic commits the failing tests (RED +
Verify RED) without ever touching production code."* Under this adaptation,
strict "watched it fail for the right reason" applies cleanly to tests
asserting **new behavior**; it applies in a weaker form to tests asserting
**invariants preserved through the change**.

Verify-RED run (`uv run pytest tests/unit/test_integration_gate_timeout.py`,
20 tests collected):

- **Pure RED (2 tests):** `TestPytestTimeoutOverride::test_env_override_applies`
  fails with `AssertionError: 120 != 300`; `TestRuffTimeoutOverride::test_env_override_applies`
  fails with `60 != 10`. Each fails because `_run_step4b`/`_run_step4a` pass
  hardcoded timeouts and ignore the env var — the exact absence Phase 3 fills.
- **Contract-fixation (18 tests, green today):** the "default preserved",
  "invalid falls back", and "silent fallback" classes pass trivially because
  the current implementation does not read the env var at all, so setting it
  to `"abc"` / `"-5"` / `""` has zero effect and the hardcoded defaults (120
  / 60) coincide with the values the tests assert.

Each of the 18 green-today tests has a named Phase 3 failure mode it would
catch:

- `test_default_when_unset`: Phase 3 Builder removes the fallback and writes
  e.g. `timeout = int(os.environ["CAIRN_PYTEST_TIMEOUT"])` → `KeyError` under
  unset env, test captures no call (or wrong kwarg) and fails.
- `test_invalid_falls_back_to_default[non_numeric|float]`: Phase 3 Builder
  writes `timeout = int(os.environ.get(..., "120"))` without `try/except`
  → `ValueError` on `"abc"` / `"1.5"`, test fails.
- `test_invalid_falls_back_to_default[zero|negative]`: Phase 3 Builder
  accepts the env value without the `> 0` guard → `timeout=0` or `timeout=-5`
  passed to `subprocess.run`, test fails.
- `test_invalid_env_produces_no_new_output`: Phase 3 Builder adds a
  stderr warning on invalid parse (e.g. `print("warning: invalid timeout",
  file=sys.stderr)`) → stream differs from baseline, test fails.

This disclosure lives here rather than in the test file so that Phase 3 and
Phase 4 reviewers can see the Skeptic's RED posture without having to
re-derive it from coverage gaps.

**Observation for integration-sweep (lessons log candidate):** 2-of-20
pure-RED is a legitimate shape for spec-change-with-invariants slices, but
the imbalance is worth recording — if future slices follow this pattern,
the sweep should consider whether the Phase Skill Guide adaptation note
needs to surface "contract-fixation" as a first-class test category rather
than a textual footnote.

## Ambiguity resolutions (Skeptic pass)

Four candidates were enumerated during Phase 2 entry. Resolutions:

1. **No explicit D0/D1/D2/D3 tag in intent frontmatter** — *real but
   non-blocking.* Resolved here (§D-commitment tie) by documenting the D3
   tie in `approach.md`. No intent amendment. Surfaced to integration-sweep
   as a schema-improvement candidate.
2. **"No pollution" under-specified** — *dismissed.* intent.md:61 reads
   "gate output character-identical to current" — that IS a byte-identity
   contract, realized in `TestSilentFallback` by comparing baseline and
   invalid-env captures.
3. **Float coverage gap** — *dismissed as gap.* intent.md:30 enumerates
   float as an invalid form; check #6's semantics (ValueError branch) cover
   it under `int("1.5")`. Float is added explicitly as a parametrize id
   for belt-and-braces.
4. **Ruff-side enumeration gap** — *dismissed.* intent.md:25-26 applies
   identical parse semantics to both env vars. Resolved by mirroring the
   same test class structure (`TestPytestTimeoutOverride` ↔
   `TestRuffTimeoutOverride`) with full parametrize parity on invalid
   values. Check 9 covers both sides via `TestSilentFallback` parametrize.

## Skeptic anti-behavior attestation

- `scripts/integration_gate.py` **not modified** — Skeptic did not
  implement. The file was read to confirm existing function signatures
  (`_run_step4a(root: Path)`, `_run_step4b(root: Path)`), call sites of
  `subprocess.run`, and import pattern (`import subprocess`) for patch-path
  correctness.
- No Phase 3 artifacts were read — none exist yet.
- Ambiguities enumerated before any test was written; resolutions recorded
  here rather than deferred to Phase 3.

## Out-of-scope acknowledgements (preserved from intent)

Step 3 validator timeout (`scripts/integration_gate.py:65`, 60s hardcoded),
the pytest `-x` short-circuit flag, raising the default timeout values,
consumer-facing documentation, and any CLI/config-file surface all remain
out of scope per the intent envelope. No Phase 2 test touches these.
