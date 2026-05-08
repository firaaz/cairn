# Phase 2 approach — cairn-m5-f1-packaging

## Tests written (all RED at HEAD `5dc03cf`)

| File | Failures | Criteria pinned |
| --- | --- | --- |
| `tests/unit/test_plugin_manifests.py` | 11 | A1, A2 (canonical + post-build artefact) |
| `tests/unit/test_build_dist.py` | 11 | A3, A4, A5, A11 (workflow shape) |
| `tests/unit/test_hooks_json.py` | 7 | A6 (canonical + post-build artefact) |
| `tests/unit/test_role_guard_anchoring.py` | 6 | A7 |
| `tests/unit/test_postinstall_validator.py` | 6 | A9, A10 (basic + plugin-cache canary + silent-pass canary) |

Total: 41 new failures, all distinct from the 3 baseline failures listed in
`/tmp/cairn-m5-f1-packaging-baseline-failures.txt` (`test_context_budget`,
two `TestSlice011AssertionCoverage::*`).

## Coverage routing for non-test acceptance criteria

- **A8** (regression guard for existing role_guard policy behaviour) — verified
  by Phase 4 re-running the existing `tests/unit/test_role_guard_envelope.py`
  and `tests/unit/test_role_guard_post_m4.py` and finding them green. No new
  assertions added; A7 changes only the path source per intent.md A8 wording.
- **A11** (CI gate workflow) — three thin shape-assertions live in
  `test_build_dist.py` (file presence; references to `build_dist.py`,
  `test_build_dist.py`, `postinstall_validate.py`; `pull_request` + `dev`/
  `main` triggers). Deeper CI behaviour is exercised when the workflow
  actually runs against a PR — out of scope for unit tests.
- **A12** (`.claude/settings.json` untouched) — verified by Phase 4 via
  `git diff 5dc03cf -- .claude/settings.json` returning empty. No test.

## Spec resolutions

- **Envelope amendment (SHA `e18dfd7`).** Asserted both surfaces (canonical
  `.claude-plugin/plugin-template.json` + `.claude-plugin/hooks-template.json`,
  AND built `dist/.claude-plugin/plugin.json` + `dist/hooks/hooks.json`) per
  the operator-confirmed plan amendment.
- **A10 hardened with plugin-cache simulation.** Per amendment, added
  `test_a10_plugin_cache_simulation_role_guard_anchors_via_env` which copies
  `checks/role_guard.py` to a tmp directory DIFFERENT from
  `CLAUDE_PROJECT_DIR` and invokes the copy via subprocess. The basic A10
  case (`test_a10_basic_positive_enforcement_passes`) and the silent-pass
  canary (`test_a10_validator_fails_loud_on_silent_pass`) are kept
  separately — they exercise different layers (validator API vs raw
  role_guard anchoring vs validator's response to a broken hook).
- **Import convention.** `pyproject.toml [tool.pytest.ini_options]
  pythonpath = ["scripts"]` → `from postinstall_validate import ...` (bare).
  `checks/` is NOT on the pythonpath; role_guard loaded via
  `importlib.util.spec_from_file_location`, matching
  `tests/unit/test_role_guard_envelope.py:73-77` and
  `tests/unit/test_role_guard_post_m4.py:193-196`.

## Items flagged for human (none blocking)

None — the open questions in intent.md §"Open questions and risks" (auto-postinstall
hook field, `pyyaml` consumer audit, marketplace `source.url`) are explicitly
out-of-scope per the plan and do not affect Phase 2 RED design.
