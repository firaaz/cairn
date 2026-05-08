# Phase 2 Approach — cairn-m6-f3-migration-and-symlink-retire

Snapshot SHA: `caa7599`. Baseline failures: 14 (`/tmp/cairn-m6-f3-migration-and-symlink-retire-baseline-failures.txt`).

## Cases mapped (intent §Verification "Phase 2 RED test cases" -> pytest)

`tests/unit/test_migrate_from_symlink.py`:

| Intent case | Pytest test |
|---|---|
| (a) Happy-path | `test_a_happy_path_exit_0_symlink_unlinked_settings_filtered` |
| (b) In-flight skill-run | `test_b_in_flight_skill_run_exit_2_no_state_change` |
| (c1) Cairn-self, no env vars | `test_c1_cairn_self_no_env_exit_3_with_required_stderr_tokens` |
| (c2) Cairn-self + `CAIRN_MIGRATE_FORCE=1` | `test_c2_cairn_self_with_FORCE_still_exits_3` |
| (c3) Cairn-self + `CAIRN_MIGRATE_BREAK_INV011=1` | `test_c3_cairn_self_with_BREAK_INV011_proceeds_with_multiline_stderr` |
| (d) Force-mode quiescence override | `test_d_force_mode_quiescence_override` |
| (e) shellcheck POSIX-strict | `test_e_shellcheck_zero_warnings` (graceful skip if not on PATH) |
| (f) Dash runtime over (a)/(b)/(c1)/(d) | `test_f_dash_runtime_a_happy_path`, `..._b_in_flight`, `..._c1_cairn_self`, `..._d_force_quiescence_override` |

## Risk-Surface-as-test-category (intent §Risk Surface, 8 items)

| Risk item | Coverage |
|---|---|
| 1. INV-011 silent erosion | Covered by (c1)+(c2) — every cairn-self refusal path asserts INV-011/D8/`docs/ARCHITECTURE.md:91` literals in stderr. |
| 2. Settings.json shape drift (complex-rag-analysis) | **Uncovered-by-design, backstopped by audit check 9** (manual end-to-end). Fixture is grounded against cairn's own `.claude/settings.json` per intent (verified directly: hooks-as-array shape, three symlink-anchored commands). (a) asserts an unrelated hook survives the filter; over-removal would surface here. |
| 3. Build-time drift between F1 smoke build and real plugin install | **Uncovered-by-design, backstopped by audit check 9.** No F3 unit-test surface for plugin-install-tree variance. |
| 4. Replace-branch dual-doc state | Out-of-scope for this test file (intent §Verification audit check 3 covers via `git ls-files` grep). |
| 5. INV-011 ARCHITECTURE.md edit denied | Out-of-scope for this test file (Phase 3 RAISE_ISSUE on hook denial; audit check 4 enforces). |
| 6. Quiescence preflight false-negative (Phase-4-orphan slice with sweep-notes present) | Acknowledged residual per intent; (b) covers the in-flight-without-sweep-notes path; deeper orphan detection is non-scope. |
| 7. Dual-placeholder confusion at `CONSUMER.md:21-22` | Out-of-scope for this test file (audit check 8 enforces grep-level breadcrumbs). |
| 8. Force-override env-var-name typo | Covered by (c1)+(c2) — both assert the literal `CAIRN_MIGRATE_BREAK_INV011` substring is in stderr so a typo is greppable. |

## (c3) safety hazard — fixture isolation

Case (c3) destroys the fixture's `.slice-system` self-symlink under `CAIRN_MIGRATE_BREAK_INV011=1`. Isolation:

1. The test uses pytest's `tmp_path` (`/private/var/folders/.../pytest-of-.../...`) — never `os.chdir` into the real repo.
2. A defensive guard rejects running if `tmp_path` is inside `REPO_ROOT`: `assert REPO_ROOT not in tmp_path.parents and tmp_path != REPO_ROOT`.
3. The script runs with `cwd=fixture` (the `tmp_path`), so `readlink .slice-system` resolves to the fixture's symlink, not cairn's.
4. The override is restricted to that one test method via `env_overrides={"CAIRN_MIGRATE_BREAK_INV011": "1"}` — it is never set in the parent process env.

## Ambiguities resolved

- **shellcheck invocation form (e).** Intent allows `-s sh` OR `--shell=bash`+directive, "Phase 2 picks the form most likely to match the script's actual shebang". Picked plain `shellcheck scripts/migrate_from_symlink.sh` (matches a `#!/bin/bash` + `# shellcheck shell=bash` directive shape, intent's "most likely shape"). Skipped on this dispatch host (shellcheck not on PATH).
- **dash binary path (f).** `which dash` returns nothing on this host but `/bin/dash` exists. Resolver tries `/usr/bin/dash`, `/bin/dash`, then `shutil.which("dash")`.
- **Session-restart prompt token (a).** Intent says "a session-restart prompt"; accepted either `restart` or `session` substring (case-insensitive) in stdout.
- **Pre-mortem Scenario 6 warning string (d).** Intent says "stderr contains the Pre-mortem Scenario 6 warning string" without pinning exact wording. Asserted on `scenario 6` substring (case-insensitive) AND an `orphan`/`in-flight` token. Cite: intent line 94 + `m5-plugin-distribution-and-symlink-retire` Pre-mortem Scenario 6.
- **INV-011 location for assertion strings (c1/c2/c3).** `docs/ARCHITECTURE.md:91` directly verified (cairn-the-repo `.slice-system → .` self-symlink as bootstrap-circularity defense; `m5-plugin-distribution-and-symlink-retire` cited).
- **Filter no-over-removal (a).** Intent does not explicitly require the filter preserve unrelated hooks; the fixture includes a non-`.slice-system` hook and asserts survival, since "filter every hook entry" would silently break consumer hook surfaces — over-removal is a defect class worth pinning.

## Pre-flight tooling check

```
$ which shellcheck   # not on PATH
$ which dash          # not on PATH (but /bin/dash exists)
$ ls /bin/dash        # /bin/dash
```

(e) skips, (f) runs against `/bin/dash`.

## Verify-RED output

```
$ uv run pytest tests/unit/test_migrate_from_symlink.py -v
...
10 failed, 1 skipped in 0.06s
```

Per-case state:

- (a) `test_a_happy_path_...` — FAIL (script missing)
- (b) `test_b_in_flight_skill_run_...` — FAIL
- (c1) `test_c1_cairn_self_no_env_...` — FAIL
- (c2) `test_c2_cairn_self_with_FORCE_...` — FAIL
- (c3) `test_c3_cairn_self_with_BREAK_INV011_...` — FAIL
- (d) `test_d_force_mode_quiescence_override` — FAIL
- (e) `test_e_shellcheck_zero_warnings` — SKIP (shellcheck not on PATH)
- (f) `test_f_dash_runtime_{a_happy_path, b_in_flight, c1_cairn_self, d_force_quiescence_override}` — 4 x FAIL (dash present at `/bin/dash`)

Full-suite regression attribution (`uv run pytest -q --tb=no -rf`): **24 failed, 402 passed, 1 skipped, 2 xfailed**. Baseline 14 + 10 new RED = 24. No baseline test newly regressed; no new failures outside this file.
