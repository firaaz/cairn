---
id: trial-e-dp4-gh2-fail-closed
name: Trial-E dp4 gh#2 fail-closed hook dogfood
snapshot-sha: e1ae33f
invariants-touched:
  - hook-dependency-failure-is-visible
  - plugin-mirror-byte-identity
---

## Operator Prompt
> A previous agent produced the plan below to accomplish the user's task. Implement the plan in a fresh context. Treat the plan as the source of user intent, re-read files as needed, and carry the work through implementation and verification.
>
> # Trial-E dp4: gh#2 Fail-Closed Hook Dogfood
>
> ## Summary
>
> Run a real `cairn-intent` dogfood with feature id `trial-e-dp4-gh2-fail-closed`, ending in a local commit on `dev`. User-confirmed scope is the live hook surface: `checks/reality-check.sh`, `checks/reversibility-guard.sh`, their `plugins/cairn/checks/` mirrors, tests, `.claude/skill-runs/...`, `.claude/handoff.md`, and `docs/operator-field-notes-2026-06-02.md`.
>
> Use the shipped Codex cairn-intent flow: form intent, run premise/atomicity guards, dispatch fresh `worker` agents with `fork_context:false` for challenge and close-review, require both operator sign-offs, then close green.
>
> ## Key Changes
>
> - Form `.claude/skill-runs/trial-e-dp4-gh2-fail-closed/intent.md` with premise grounding for the live fail-open lines:
>   `reality-check.sh` jq lines 8-10, `reality-check.sh` ruff lines 26-28, and `reversibility-guard.sh` jq lines 9-11.
> - Initial contract is strict fail-closed: no escape hatch. Add `escalate-when` requiring revision if the front-challenge blocks strict behavior as a real consumer-compatibility risk.
> - If and only if challenge blocks strict behavior, revise to the exact escape hatch `CAIRN_ALLOW_MISSING_DEPS=1`, which emits a warning and exits 0; otherwise missing deps fail closed.
> - Add `tests/unit/test_hook_missing_deps.py`, parameterized over canonical and plugin mirror scripts.
> - Change `reality-check.sh` missing dep behavior:
>   `jq` missing -> exit 1, stderr `ERROR: reality-check hook dependency missing: jq not found in PATH; failing closed`.
>   `ruff` missing on a Python-file event -> exit 1, analogous stderr. Non-Python events still exit 0 after `jq` parses.
> - Change `reversibility-guard.sh` missing `jq` behavior:
>   exit 2, stderr `ERROR: reversibility-guard dependency missing: jq not found in PATH; failing closed`, and stdout deny JSON with reason `REVERSIBILITY GUARD: required dependency jq not found in PATH; failing closed`.
> - Keep `plugins/cairn/checks/reality-check.sh` and `plugins/cairn/checks/reversibility-guard.sh` byte-identical to canonical scripts; add a test assertion for this.
> - Append dp4 to `docs/operator-field-notes-2026-06-02.md` with felt-cost, checkpoint catch/miss table, co-miss result, and whether the D2 close-review charter gap surfaced.
> - Update `.claude/handoff.md` to remove or replace the active `gh#2` thread only after green close evidence exists; do not invent a `closed` state.
>
> ## Test Plan
>
> - RED: run `uv run pytest tests/unit/test_hook_missing_deps.py -v` before implementation and confirm the missing-dep tests fail because hooks exit 0.
> - GREEN focused: run `uv run pytest tests/unit/test_hook_missing_deps.py -v`.
> - Payload/build checks: run `uv run pytest tests/unit/test_hook_missing_deps.py tests/unit/test_hooks_json.py tests/unit/test_build_dist.py -q`.
> - Smoke build: `uv run python scripts/build_dist.py --repo-root . --dist-root /tmp/cairn-dp4-dist`.
> - Final acceptance: `uv run pytest` and `uv run python scripts/validate_architecture.py`.
> - Close-review receives the intent path, full diff, focused and full verification output, build evidence, and the field-notes draft.
>
> ## Assumptions
>
> - `scope-guard.sh` and `role-cheatsheet.sh` are stale prompt names deleted at `42ae8d9`; do not restore them.
> - Codex Python hook adapters and post-install validator warning semantics are out of scope unless the fresh challenge/review classifies that as a contract-fidelity blocker.
> - The final commit is local only, with message `fix(hooks): fail closed on missing hook deps`; no push or GitHub issue close is part of this run.
> - Pre-existing untracked `.claude/skill-runs/.../_check` artifacts are not staged.

## What
Change the live shell hook dependency behavior from warning-and-skip to fail-closed when required tools are missing, while dogfooding the shipped `cairn-intent` loop for gh#2.

## Why
The current hooks silently skip when `jq` or `ruff` is absent, so the operator can believe guard coverage is active while the hook surface is disabled. Trial-E dp4 measures whether the intent loop catches and closes that real hook-fidelity slice.

## Boundary
This does not restore deleted prompt files, change Codex Python hook adapters, alter post-install validator warning semantics, push to GitHub, or close the GitHub issue remotely.

## Specification
`checks/reality-check.sh` shall fail closed with exit 1 when `jq` is missing, emitting `ERROR: reality-check hook dependency missing: jq not found in PATH; failing closed` to stderr. For Python-file events, it shall fail closed with exit 1 when `ruff` is missing, emitting `ERROR: reality-check hook dependency missing: ruff not found in PATH; failing closed` to stderr; non-Python events still exit 0 after `jq` parses the payload. `checks/reversibility-guard.sh` shall fail closed with exit 2 when `jq` is missing, emit `ERROR: reversibility-guard dependency missing: jq not found in PATH; failing closed` to stderr, and write a deny JSON whose permission reason is `REVERSIBILITY GUARD: required dependency jq not found in PATH; failing closed`. The plugin mirror hook scripts shall remain byte-identical to the canonical scripts.

## Verification
Run the red missing-dependency test before implementation; then run focused, payload/build, smoke build, full pytest, and architecture validation checks named in the operator prompt. Close-review receives the intent path, implementation diff, focused/full verification output, build evidence, and the field-notes draft.

## Risk Surface
Consumer environments that lack `jq` or `ruff` may experience newly blocking hooks. If the fresh front-challenge classifies strict fail-closed as a real compatibility blocker, the contract must be revised before construction.

## Feature-Local Invariants
- Missing hook dependencies are visible failures by default, not silent skips.
- The plugin hook mirrors stay byte-identical to the canonical hook scripts.
- The dogfood evidence records both checkpoint behavior and the Trial-E felt cost.

## Explicit Scope-Out
- No changes to `scope-guard.sh` or `role-cheatsheet.sh`.
- No changes to Codex Python hook adapters or post-install validator warning semantics unless challenge or review blocks on contract fidelity.
- No remote push and no GitHub issue closure.
- No staging of pre-existing untracked `_check` artifacts.

## Premise Grounding

```yaml
premises:
  - source: checks/reality-check.sh
    quote: |
      if ! command -v jq &>/dev/null; then
        echo "WARNING: reality-check hook skipped — jq not found in PATH" >&2
        exit 0
    label: "reality-check currently fails open when jq is missing"
  - source: checks/reality-check.sh
    quote: |
      if ! command -v ruff &>/dev/null; then
        echo "WARNING: reality-check hook skipped — ruff not found in PATH. Install with: uv tool install ruff" >&2
        exit 0
    label: "reality-check currently fails open on Python-file events when ruff is missing"
  - source: checks/reversibility-guard.sh
    quote: |
      if ! command -v jq &>/dev/null; then
        echo "WARNING: reversibility-guard hook skipped — jq not found in PATH" >&2
        exit 0
    label: "reversibility-guard currently fails open when jq is missing"
```

## Contract

```yaml
scope-statement: make the live shell hook dependency checks fail closed by default and record the Trial-E dp4 dogfood evidence for gh#2
must-satisfy:
  - when jq is missing from PATH, the reality-check shell hook shall exit 1 and emit the specified fail-closed jq error to stderr
  - when ruff is missing from PATH during a Python-file event, the reality-check shell hook shall exit 1 and emit the specified fail-closed ruff error to stderr
  - when ruff is missing from PATH during a non-Python event, the reality-check shell hook shall exit 0 after parsing the payload with jq
  - when jq is missing from PATH, the reversibility-guard shell hook shall exit 2 and emit the specified fail-closed jq error to stderr
  - when jq is missing from PATH, the reversibility-guard shell hook shall write deny JSON with the specified fail-closed permission reason to stdout
  - clause: every plugin hook mirror shall be byte-identical to its canonical shell hook
    except: "universal-set: checks/reality-check.sh mirrored at plugins/cairn/checks/reality-check.sh; checks/reversibility-guard.sh mirrored at plugins/cairn/checks/reversibility-guard.sh"
  - the implementation shall record Trial-E dp4 field notes with felt cost, checkpoint catch/miss table, co-miss result, and D2 close-review charter-gap observation
must-not-violate:
  - the implementation shall preserve existing destructive-command deny behavior in reversibility-guard
  - the implementation shall preserve reality-check no-op behavior for non-Python files when jq is available
  - the implementation shall keep the local commit on dev without pushing or closing GitHub remotely
wrong-if:
  - a missing dependency silently exits 0 by default on a hook path that should be guarded
  - plugin mirror scripts diverge from their canonical hook scripts
  - the handoff records gh#2 with a non-contractual closed state
escalate-when:
  - if the fresh front-challenge blocks strict fail-closed behavior as a real consumer-compatibility risk, revise the contract before construction to add exactly the escape hatch CAIRN_ALLOW_MISSING_DEPS=1, which emits a warning and exits 0; otherwise do not add an escape hatch
evidence:
  - red missing-dependency test output before implementation
  - focused missing-dependency test output after implementation
  - payload/build focused pytest output
  - smoke build output
  - full pytest output
  - architecture validation output
  - fresh challenge and close-review signoffs
execution-scope:
  - checks/reality-check.sh
  - checks/reversibility-guard.sh
  - plugins/cairn/checks/reality-check.sh
  - plugins/cairn/checks/reversibility-guard.sh
  - tests/unit/test_hook_missing_deps.py
  - .claude/skill-runs/trial-e-dp4-gh2-fail-closed/
  - .claude/handoff.md
  - docs/operator-field-notes-2026-06-02.md
```
