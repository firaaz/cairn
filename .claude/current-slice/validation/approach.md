---
slice: SLICE-014
phase: 2-validation
framing: C (documented baseline + frozen pre-slice evidence)
precedent: SLICE-013 (same framing, different edit mechanism)
---

# Validation Approach — SLICE-014 (ruff-cleanup v2)

## Framing decision

SLICE-014 is a behavior-preserving lint cleanup, same shape as SLICE-013. It reuses SLICE-013's **framing C**: no new test code, pre-slice evidence transcripts frozen as the literal RED artifact, verification via existing ruff + pytest runs at Phase 4.

The difference from SLICE-013 is mechanism, not framing. SLICE-013 attempted to clear E402 by relocating the import *and* retaining the runtime `sys.path.insert` — a placement that could not satisfy E402 by construction, which is why Phase 3 aborted. SLICE-014 instead introduces a new file (`pyproject.toml`) whose `[tool.pytest.ini_options] pythonpath = ["scripts"]` config puts `scripts/` on `sys.path` before test collection, enabling the validator import to sit at module top as an ordinary import with no accompanying sys.path statement.

## Validation surface

Three properties must hold at Phase 4:

1. **Lint property (primary target of the slice).** `ruff check tests/unit/test_feature_cross_index.py tests/unit/test_invariant_assertions.py` exits 0 with zero errors. The pre-slice state (frozen in `pre-slice-ruff.txt`) exits 1 with exactly three errors: two `E741` at `test_feature_cross_index.py:88,95` and one `E402` at `test_invariant_assertions.py:1114`.

2. **Behavioral invariant (must NOT change).** `python3 -m pytest tests/unit/test_feature_cross_index.py tests/unit/test_invariant_assertions.py` exits 0 with 58 passed, 0 failed, 0 skipped — identical to pre-slice (frozen in `pre-slice-pytest.txt`). The validator import must resolve via pytest's `pythonpath` config, not via runtime `sys.path.insert`.

3. **Pytest config property (new to SLICE-014).** `pyproject.toml` exists at repo root and contains exactly `[tool.pytest.ini_options]` with `pythonpath = ["scripts"]`. No other sections, no ruff config, no project metadata — per intent §2 and the out-of-scope clause.

Phase 4 re-runs the two commands plus inspects `pyproject.toml`. Lint exit flipping from 1→0 is the GREEN transition. Behavioral invariant holding unchanged (58/58) is the preservation check. Pytest config presence is the config check.

## RED evidence

- `pre-slice-ruff.txt` — verbatim transcript of `ruff check` against the two envelope test files showing exit 1 and the three enumerated errors (2×E741, 1×E402). This is the RED state for the lint property. Phase 3 makes this transcript no longer reproducible.
- `pre-slice-pytest.txt` — verbatim transcript of `pytest` showing exit 0, 58 passed. This is the invariant baseline. Phase 3 must reproduce this exactly (modulo runtime seconds).

No new test code is added. Authoring a test that asserts `ruff check ... exits 0` would merely duplicate what `integration_gate.py` Step 4a already enforces repo-wide; a test asserting `pyproject.toml` contains `[tool.pytest.ini_options]` would be a tautology against a 2-line file. Redundancy buys no additional coverage.

## Ambiguity enumeration (Skeptic pass)

Seven ambiguities surfaced; all resolve via intent.md or repo state. None required escalation.

1. **`pyproject.toml` scope.** Could include `[build-system]`, `[project]`, `[tool.ruff]`, etc. `intent.md` §2 and the out-of-scope clause pin contents to `[tool.pytest.ini_options]` with a single `pythonpath = ["scripts"]` key — no other sections. Resolved.

2. **`import sys` retention.** If `sys.path.insert` is removed, `sys` could become unused and trigger `F401`. Grep (`\bsys\.`) shows `sys.executable` in use at lines 44, 1093, 1203, 1221 of `test_invariant_assertions.py`. `import sys` remains live. No F401 risk. Resolved.

3. **Pytest rootdir / config discovery.** Adding `pyproject.toml` changes pytest's rootdir determination (it becomes the dir containing `pyproject.toml`). Existing tests resolve `CAIRN_ROOT` via `Path(__file__).resolve().parent.parent.parent` — file-relative, not pytest-rootdir-dependent. No test should break from rootdir shift. Resolved.

4. **Edit ordering at line 29 vs 1112.** Inserting an import at line 29 shifts line 1112 to 1113. Intent describes both edits relative to the **pre-slice** baseline. Phase 3 applies them in either order on the pre-slice file — the net result is the same. Builder handles independently; not an ambiguity, a sequencing note. Resolved.

5. **Blank-line placement around new import.** `intent.md` §3 says "add a blank line" after the VALIDATOR assignment, then the import. The existing blank line at line 30 (before `# --- Fixtures ---` at line 32) is preserved. Phase 3 ensures exactly one blank line separates VALIDATOR from the import and at least one blank line separates the import from `# --- Fixtures ---`. Resolved.

6. **Section comment at line 1105.** `intent.md` §3 states `# === SLICE-011: Assertion block coverage ...` stays in place — only the three-line import block (lines 1112-1114, including the comment) is removed. Resolved.

7. **`.claude/d3-bypasses.log`.** Out-of-scope (`intent.md` out-of-scope clause). The 1/10 rolling-window entry consumed by SLICE-012 decays naturally as slices age out; no edit to the log. Resolved.

## Phase 3 entry contract

Phase 3 (Implementer) receives exactly two inputs: `intent.md` (specification) and the two frozen transcripts in this directory (validation surface). Phase 3 does NOT read this `approach.md` beyond this contract section — the framing rationale is Skeptic's work and must not influence Implementer's choices beyond what intent.md already binds.

**Phase 3 success criterion:** after creating `pyproject.toml` and applying the three enumerated test-file edits, re-running:

```
ruff check tests/unit/test_feature_cross_index.py tests/unit/test_invariant_assertions.py
python3 -m pytest tests/unit/test_feature_cross_index.py tests/unit/test_invariant_assertions.py
```

produces (1) ruff exit 0 with zero errors, and (2) pytest exit 0 with 58 passed, 0 failed, 0 skipped. The pytest run succeeding is itself confirmation that the new top-of-file validator import resolves via the `pyproject.toml` `pythonpath` config — without it, collection would fail with `ModuleNotFoundError: No module named 'validate_architecture'`.

## Phase 4 evidence requirements

- `ruff check` transcript: exit 0, zero errors (contrast with `pre-slice-ruff.txt`).
- `pytest` transcript: exit 0, 58 passed, 0 failed, 0 skipped (match `pre-slice-pytest.txt` outcome counts).
- `pyproject.toml` content: exactly one `[tool.pytest.ini_options]` section with `pythonpath = ["scripts"]`.
- `integration_gate.py` run: exit 0, Steps 3, 4a, 4b all PASS, no new D3 bypass log entry.
- `snapshot_diff.py --diff`: changes confined to three envelope files plus `.claude/current-slice/` artifacts.
