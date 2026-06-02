# Construct Evidence

Feature id: `trial-e-dp4-gh2-fail-closed`

## Intent Guards
- `uv run python checks/premise_guard.py .claude/skill-runs/trial-e-dp4-gh2-fail-closed/intent.md`
  - exit 0, silent
- `uv run python checks/atomicity_guard.py .claude/skill-runs/trial-e-dp4-gh2-fail-closed/intent.md`
  - exit 0
  - `atomicity_guard: all 7 clause(s) atomic-or-validly-tagged.`

## Fresh Challenge
- Worker `019e8862-bbc3-7e82-9850-c01e598033cc`
- Report: `.claude/skill-runs/trial-e-dp4-gh2-fail-closed/intent-challenge.md`
- Verdict: `challenge-pass`
- Escape hatch revision: not required. The reviewer classified strict fail-closed as a compatibility risk, not a blocker.

## Red
- `uv run pytest tests/unit/test_hook_missing_deps.py -v`
- Result: 6 failed, 3 passed
- Expected failures:
  - reality-check missing `jq` exited 0 with `WARNING: reality-check hook skipped — jq not found in PATH`
  - reality-check missing `ruff` exited 0 with `WARNING: reality-check hook skipped — ruff not found in PATH. Install with: uv tool install ruff`
  - reversibility-guard missing `jq` exited 0 with `WARNING: reversibility-guard hook skipped — jq not found in PATH`

## Green Focused
- `uv run pytest tests/unit/test_hook_missing_deps.py -v`
- Result: 9 passed in 1.36s

## Payload / Build Subset
- `uv run pytest tests/unit/test_hook_missing_deps.py tests/unit/test_hooks_json.py tests/unit/test_build_dist.py -q`
- Result: 27 passed in 1.73s

## Smoke Build
- `uv run python scripts/build_dist.py --repo-root . --dist-root /tmp/cairn-dp4-dist`
- Result: exit 0, no stdout/stderr

## Full Pytest
- `uv run pytest`
- Result: 673 passed, 2 skipped, 2 xfailed in 40.65s

## Architecture Validation
- `uv run python scripts/validate_architecture.py`
- Result:
  - `ALL CHECKS PASSED`
  - `Invariants verified: 12`
  - `ADR files checked: 45`

## Mirror Checks
- `cmp -s checks/reality-check.sh plugins/cairn/checks/reality-check.sh`
  - exit 0
- `cmp -s checks/reversibility-guard.sh plugins/cairn/checks/reversibility-guard.sh`
  - exit 0
