# Phase 4 sweep notes — cairn-m5-f1-packaging

- **Snapshot SHA:** `5dc03cf421198aa43394fb241cf6a17df1320f47`
- **HEAD audited:** `1428c79` (Phase 3 — implementation)
- **Audited at:** 2026-05-08
- **Verdict:** OK

## Tests

`uv run pytest -q --tb=no` (HEAD `1428c79`):

```
2 failed, 401 passed, 2 xfailed in 20.32s
FAILED tests/unit/test_invariant_assertions.py::TestSlice011AssertionCoverage::test_no_extra_assertion_blocks
FAILED tests/unit/test_invariant_assertions.py::TestSlice011AssertionCoverage::test_invariant_count_unchanged
```

Baseline at `5dc03cf` (`/tmp/cairn-m5-f1-packaging-baseline-failures.txt`):

```
3 failed, 359 passed, 2 xfailed in 21.52s
FAILED tests/unit/test_context_budget.py::test_inv004_turn1_token_budget
FAILED tests/unit/test_invariant_assertions.py::TestSlice011AssertionCoverage::test_no_extra_assertion_blocks
FAILED tests/unit/test_invariant_assertions.py::TestSlice011AssertionCoverage::test_invariant_count_unchanged
```

Delta vs baseline:

| Bucket | Baseline | HEAD | Δ |
| --- | --- | --- | --- |
| Passed | 359 | 401 | +42 |
| Failed | 3 | 2 | −1 |
| xfailed | 2 | 2 | 0 |

- **+42 passing** matches Phase 2's 41 RED tests + 1 ride-along (Phase-2 tests
  that now pass under Phase 3 GREEN). Approach.md declared 41 new tests; tally
  consistent.
- **No new failures** vs baseline. Both surviving failures
  (`test_no_extra_assertion_blocks`, `test_invariant_count_unchanged`) are
  byte-identical to baseline; `git diff 5dc03cf..HEAD --
  tests/unit/test_invariant_assertions.py` is empty, so the failures are
  pre-existing and untouched by F1 (out-of-scope per the snapshot baseline
  contract).
- **Flaky `test_inv004_turn1_token_budget`.** Did NOT fail this run; baseline
  shows it flickering. Per intent contract this flicker is not attributable
  to F1 (INV-004 re-baseline pending per `.claude/handoff.md`). Documented as
  expected drift.

`uv run python scripts/validate_architecture.py` (note: validator lives at
`scripts/`, not `checks/` — the brief's `checks/validate_architecture.py`
path is stale post-shrink): **ALL CHECKS PASSED** — 11 invariants, 28 ADRs.
One INV-002 token-budget warning on `.claude/handoff.md` (382 tokens vs
360-warn-at) — pre-existing, not F1 attribution.

`uv run pytest tests/unit/test_role_guard_envelope.py
tests/unit/test_role_guard_post_m4.py -v --tb=no` (A8 regression guard):
**22 passed in 0.35s.** Pre-D5-anchoring-fix policy semantics are
byte-identical post-fix.

`bash scripts/smoketest_hooks.sh` (Path-B self-symlink dogfood):
**`PASS role_guard.py`** — D5 anchoring fix did not break self-consumption.

## Validator

`uv run python scripts/validate_architecture.py` → ALL CHECKS PASSED. No
per-invariant block needs documenting beyond the table below.

## Invariants

| INV-NNN | Statement (abridged) | Status | Evidence |
| --- | --- | --- | --- |
| INV-011 | Cairn-the-repo retains a local self-consumption mechanism (`.slice-system → .` self-symlink, alternatives only via superseding ADR); maintainers can iterate on hooks/skills/agents without plugin republish. F1 lands plugin packaging without retiring the self-symlink. | PASS | `docs/ARCHITECTURE.md:91` (statement); `git diff 5dc03cf..HEAD -- .claude/settings.json` empty (Path B unchanged); `.slice-system` symlink intact (`scripts/smoketest_hooks.sh` exits PASS — confirms self-consumption still works); `.claude/active-envelope.yaml:1-52` unchanged in spirit; D8 routing in plan F1.8. |

(F1 owns D1, D2, D3, D4, D5 per intent. INV-011 is the only invariant in the
intent's `invariants-touched` list — D-commitments are tracked per the
acceptance-criteria walk below.)

## Acceptance criteria audit (A1–A12)

| Criterion | Status | Test | Source / artefact |
| --- | --- | --- | --- |
| A1 — Marketplace manifest (D1) | PASS | `tests/unit/test_plugin_manifests.py` | `.claude-plugin/marketplace.json:1-17` (cairn-marketplace, single plugin entry, `source.type:"git"`, `source.path:"dist/"`) |
| A2 — Plugin manifest with explicit version (D1, D2) | PASS | `tests/unit/test_plugin_manifests.py` | `.claude-plugin/plugin-template.json:1-6` (canonical: `name:"cairn"`, `version:"0.1.0"`, non-empty `description`); built into `dist/.claude-plugin/plugin.json` by `scripts/build_dist.py:30` |
| A3 — Build allow-list populates expected paths (D3) | PASS | `tests/unit/test_build_dist.py` | `scripts/build_dist.py:18-33` (14-row ALLOW_LIST); manual smoke build (see below) lists 14 expected files |
| A4 — Build never leaks excluded surfaces (D3) | PASS | `tests/unit/test_build_dist.py` | `scripts/build_dist.py:18-33` (allow-list IS the contract); manual smoke confirms no `tests/`, `docs/`, `.venv/`, `commands/`, `slice_orchestrator/`, `skill-runs/`, `adr/`, `plans/`, `reviews/` |
| A5 — Build idempotent + symlink-safe (D3) | PASS | `tests/unit/test_build_dist.py` | `scripts/build_dist.py:36-39,55,66-68` (`_clean()` rmtree, `ignore_patterns(".slice-system","__pycache__")`, explicit `startswith(".slice-system")` skip) |
| A6 — Hooks manifest with `${CLAUDE_PLUGIN_ROOT}` (D4) | PASS | `tests/unit/test_hooks_json.py` | `.claude-plugin/hooks-template.json:1-33` — PreToolUse `Bash\|Edit\|Write`→`reversibility-guard.sh`, PreToolUse `Write\|Edit\|MultiEdit\|NotebookEdit`→`role_guard.py`, PostToolUse `Edit\|Write`→`reality-check.sh`. All commands prefixed with `${CLAUDE_PLUGIN_ROOT}/`. No `.slice-system/` references. |
| A7 — `role_guard.py` anchors on `CLAUDE_PROJECT_DIR` (D5) | PASS | `tests/unit/test_role_guard_anchoring.py` | `checks/role_guard.py:28` — `CAIRN_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())`. `_log_grant()` at `:121` reads the same constant. No `Path(__file__).resolve().parent.parent` remains. Diff vs baseline at `5dc03cf` confirms one-line change at `:28`. |
| A8 — Regression guard | PASS | `tests/unit/test_role_guard_envelope.py` + `tests/unit/test_role_guard_post_m4.py` | 22/22 PASS post-fix; identical to pre-fix (path-source-only change). |
| A9 — Validator dep checks are warnings (D5) | PASS | `tests/unit/test_postinstall_validator.py` | `scripts/postinstall_validate.py:35-43` (`check_dep` prints WARN to stderr, returns False, never exits non-zero); `main()` at `:112-128` only fails on enforcement failure. |
| A10 — Validator positive enforcement is fatal (D5) | PASS | `tests/unit/test_postinstall_validator.py` (incl. plugin-cache simulation per approach.md amendment) | `scripts/postinstall_validate.py:57-109` writes operator envelope, invokes role_guard via subprocess, requires `rc==1 AND non-empty stderr`; `:120-127` exits 1 with "envelope enforcement self-test failed — installation is not safe" on silent-pass. |
| A11 — CI gate (deferred runtime verification) | PASS-by-shape | `tests/unit/test_build_dist.py` workflow shape assertions | `.github/workflows/dist-gate.yml:1-32` declares `pull_request` + `push: dev,main` triggers, runs build_dist, runs allow-list assertions (`test_build_dist.py`), runs `postinstall_validate.py` with `CLAUDE_PLUGIN_ROOT=/tmp/dist-ci`. **Runtime-CI verification deferred to first PR open.** |
| A12 — `.claude/settings.json` untouched (D8) | PASS | n/a | `git diff 5dc03cf421198aa43394fb241cf6a17df1320f47 -- .claude/settings.json` produces empty output. |

## Plan-vs-implementation diff (F1.1–F1.7)

- **F1.1 (Manifests).** `.claude-plugin/marketplace.json:1-17` matches plan
  shape exactly; `source.url` is the plan-templated
  `https://github.com/firaaz/cairn.git` (plan F1.1 Step 2 + Open
  Question #4 — owner-confirmable at PR open).
- **F1.2 (Build script).** `scripts/build_dist.py` matches plan F1.2
  function shape: explicit ALLOW_LIST tuples (14 rows), `build()` cleans
  first, `main()` is typer-driven. `_root.py`/`lib/` deliberately omitted
  per plan Step 3 + self-review summary. Manual smoke (below) confirms.
- **F1.3 (`plugin.json` placement).** `plugin-template.json` is at
  `.claude-plugin/plugin-template.json` (canonical, source-controlled);
  build copies to `dist/.claude-plugin/plugin.json` via `build_dist.py:30`.
  `dist/` is NOT committed (verified by `git ls-files dist` empty).
- **F1.4 (hooks.json).** `hooks-template.json` is at
  `.claude-plugin/hooks-template.json`; built into `dist/hooks/hooks.json`
  by `build_dist.py:31`. Step 3: `role_guard.py` invoked via `python3`
  (NOT `uv run python`) per `hooks-template.json:17` — confirmed.
- **F1.5 (anchoring fix).** Single-line change at `checks/role_guard.py:28`
  per plan; `:121` automatically inherits via the module-level constant
  (no second mutation needed, per plan Step 3). Diff confirms.
- **F1.6 (Validator).** Function shape matches plan. **Step 5 decision —
  auto-postinstall hook deferred.** Phase 3 did NOT wire a
  `postinstall:` field into `plugin-template.json`
  (`.claude-plugin/plugin-template.json:1-6` shows only `name`,
  `version`, `description`, `homepage` — no `postinstall:` key). Per
  plan Open Question #2 + Section F1.6 Step 5, this routes to **F2's
  CONSUMER.md docket** as a manual-invocation documentation item.
- **F1.7 (CI gate).** Workflow shape per plan Step 1 (5 steps:
  checkout/uv-setup/sync, build, allow-list, validator). Workflow runs
  `pytest tests/unit/test_build_dist.py` for allow-list, and the
  validator with `CLAUDE_PLUGIN_ROOT=/tmp/dist-ci`. **Step 2 deferred:**
  see Findings below — `.gitignore` does NOT contain a `dist/` entry.

## Manual smoke evidence

### Build smoke

`uv run python scripts/build_dist.py --dist-root /tmp/cairn-dist-smoke`:

```
/tmp/cairn-dist-smoke/.claude-plugin/plugin.json
/tmp/cairn-dist-smoke/agents/phase-1-tdd.md
/tmp/cairn-dist-smoke/agents/phase-2-tdd.md
/tmp/cairn-dist-smoke/agents/phase-3-tdd.md
/tmp/cairn-dist-smoke/agents/phase-4-tdd.md
/tmp/cairn-dist-smoke/agents/role-topology.yaml
/tmp/cairn-dist-smoke/agents/triager-tdd.md
/tmp/cairn-dist-smoke/checks/reality-check.sh
/tmp/cairn-dist-smoke/checks/reversibility-guard.sh
/tmp/cairn-dist-smoke/checks/role_guard.py
/tmp/cairn-dist-smoke/hooks/hooks.json
/tmp/cairn-dist-smoke/postinstall_validate.py
/tmp/cairn-dist-smoke/skills/cairn-tdd-feature/SKILL.md
/tmp/cairn-dist-smoke/templates/handoff.md
```

14 files, no leakage. Allow-list contract holds.

### Validator smoke

`CLAUDE_PLUGIN_ROOT=/tmp/cairn-dist-smoke python3
/tmp/cairn-dist-smoke/postinstall_validate.py`:

```
exit=0
```

(stdout/stderr empty — `jq`/`ruff` resolve locally so no warnings; positive
enforcement self-test passed.) End-to-end deny landed against an
out-of-envelope `scripts/foo.py` write.

### Hook smoketest

`bash scripts/smoketest_hooks.sh`:

```
PASS role_guard.py
```

Path-B self-symlink dogfood unbroken by D5 anchoring change.

## Findings (operator follow-ups, NOT in this commit)

These are surfaced for operator review per the brief; Phase 4 does not
self-author fixups for items outside its envelope.

- **`dist/` not in `.gitignore`.** Phase 3's envelope did not include
  `.gitignore`, so plan F1.7 Step 2 was deferred. `git ls-files dist`
  is currently empty (no leak), but a one-line follow-up commit
  (`echo "dist/" >> .gitignore`) is the correct close. Recommend
  operator-blessed micro-commit, not Phase-4-authored.
- **Auto-postinstall hook deferred to F2 (plan F1.6 Step 5).**
  `plugin-template.json` does NOT declare a `postinstall:` field. F2's
  CONSUMER.md must document manual invocation
  (`python3 ${CLAUDE_PLUGIN_ROOT}/postinstall_validate.py`). Routed to
  F2's open-questions docket.
- **Pyright lint noise on `typer`/`yaml`.** Pyright reports unresolved
  imports for `typer` (in `build_dist.py`, `postinstall_validate.py`)
  and `yaml` (in `role_guard.py`). These are runtime deps in `.venv`
  per CLAUDE.md "post-M4 standing dep set: pydantic, typer, pyyaml".
  Pre-existing pattern — `scripts/validate_architecture.py` uses the
  same pattern. Analyzer-config noise, not an F1 regression.
- **Unused `typer` import in `postinstall_validate.py:28`?** **NOT a
  finding.** `grep -n typer scripts/postinstall_validate.py` returns
  zero hits — there is no `import typer` in this file. The brief's
  pre-emptive concern does not apply post-Phase-3.
- **`build_dist.py:76` unreachable-code warning?** Inspected — line 76
  is `dist_root = repo_root / "dist"` inside the `if dist_root is
  None:` branch of `main()`, which IS reachable when
  `--dist-root` is omitted (typer leaves the option `None`). This is a
  pyright false-positive caused by typer's decorator-flavoured option
  defaulting; not actually unreachable.
- **`test_inv004_turn1_token_budget` known-flaky.** Did not fail this
  run (suite tally says 401/2/2 vs baseline 359/3/2). The contract is
  "no NEW failures vs baseline" — the −1 failure delta is the flaky
  test passing this time; not attributable to F1. Re-baseline is
  blocked on INV-004 stabilisation per `.claude/handoff.md:21`.
- **`validate_architecture.py` location.** Brief listed
  `checks/validate_architecture.py`; canonical post-shrink location is
  `scripts/validate_architecture.py` (per
  `docs/operational-reference.md` and brief's "or `uv run python
  checks/validate_architecture.py` per project convention"). Used the
  canonical path.

## Audit verdict

OK. All twelve acceptance criteria pass; full suite green vs baseline
(no new failures, +42 passing); validator green; smoke tests green;
INV-011 PASS; D5 regression guard 22/22 green; no envelope violations.
Findings above are non-blocking operator follow-ups.
