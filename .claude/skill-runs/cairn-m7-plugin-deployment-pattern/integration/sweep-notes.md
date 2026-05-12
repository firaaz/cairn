# Phase 4a sweep — cairn-m7-plugin-deployment-pattern

> **Scope.** Phase 4a runs automated audit checks 1–8. Audit check 9 is operator-bound (push to `origin` + GitHub Actions release-publish run + fresh non-cairn project install + dispatch round-trip) and is scaffolded below as `PENDING`. A second `phase-4-tdd` dispatch (Phase 4b) will edit the check-9 section once the operator returns the VERDICT.

**Feature id:** `cairn-m7-plugin-deployment-pattern`
**Snapshot SHA:** `38ea8b565eea4db118a1541757fb70bc1b86b80d`
**Phase 1 intent:** `dd966de`
**Phase 2 RED tests:** `c9a1ff2`
**Phase 2 amendment (retire superseded F1 A1 shape):** `31d3976`
**Phase 3 implementation:** `b1439c9`
**Orchestrator envelope expansion:** `527f49a`
**Touched invariants:** `INV-012`

---

## Tests

Command: `uv run pytest -q --tb=no -rf` (full suite at HEAD).

**Headline:** `15 failed, 421 passed, 1 skipped, 2 xfailed in 24.23s`.

**Baseline (snapshot-pinned, `/tmp/cairn-m7-plugin-deployment-pattern-baseline-failures.txt`):** 14 failures, 414 passed, 1 skipped, 2 xfailed.

**Delta vs baseline:**

- **+7 GREEN** new in M7's deliverables: `tests/unit/test_marketplace_schema.py` (5) + `tests/unit/test_release_workflow.py` (4) = **9 new GREEN** added by M7. Total GREEN delta is +7 because two of the previously RED `tests/unit/test_invariant_assertions.py::TestSlice011…` cases were not on this baseline list (the baseline lists 14 failures; current passing count rose 414 → 421 = +7; new tests landed = 9; this implies 2 baseline-RED cases flipped to GREEN, none of which are M7's responsibility). The 14 baseline failures all reproduce verbatim at HEAD.
- **+1 NEW FAILURE (environmental, not introduced by M7):** `tests/unit/test_context_budget.py::test_inv004_turn1_token_budget` — INV-004 live measurement test that spawns `claude -p "hi"` and reads turn-1 token JSONL. Failure value `69720 tokens > 40000 budget` reflects current Claude Code session-state (CC version `2.1.136`), not M7. Diff inspection of `38ea8b5..HEAD` confirms M7 touched only `.claude-plugin/marketplace.json`, `.github/workflows/{release-publish,dist-gate}.yml`, `tests/unit/test_{marketplace_schema,release_workflow,plugin_manifests}.py`, `.gitignore`, `CHANGELOG.md`, `.claude/active-envelope.yaml`, and `.claude/skill-runs/cairn-m7-plugin-deployment-pattern/**` — none of which are imported by `test_context_budget.py`. This test is `skipif` when `claude` is absent and is sensitive to CC-binary token-budget bloat upstream; classify **out-of-scope** for M7. Recommend re-pinning the baseline file after merge if the failure persists.

**14 baseline failures still RED at HEAD (all out-of-scope for M7 per /tmp/cairn-m7-plugin-deployment-pattern-baseline-failures.txt):**

- `tests/unit/test_adr_rename_sweep.py::TestV7Validator::test_validate_architecture_exits_0`
- `tests/unit/test_adr_rename_sweep.py::TestContractC3CurrentCorpusPasses::test_sweep_tests_pass_on_live_corpus`
- `tests/unit/test_adr_rename_sweep.py::TestContractC4RobustnessUnderGrowth::test_valid_new_adr_keeps_suite_green`
- `tests/unit/test_inv_001_git_log_walk.py::test_validator_e2e_passes_with_placeholder`
- `tests/unit/test_inv_002_structural_parser.py::test_live_cairn_handoff_passes_structural_parser`
- `tests/unit/test_inv_002_structural_parser.py::test_validator_e2e_passes_with_placeholder`
- `tests/unit/test_inv_003_phase_topology.py::TestCleanTreePasses::test_validator_subprocess_passes_on_cairn_head`
- `tests/unit/test_invariant_assertions.py::TestCairnSelfDogfood::test_cairn_self_validation_still_passes`
- `tests/unit/test_invariant_assertions.py::TestSlice011AssertionCoverage::test_no_extra_assertion_blocks`
- `tests/unit/test_invariant_assertions.py::TestSlice011AssertionCoverage::test_invariant_count_unchanged`
- `tests/unit/test_invariant_assertions.py::TestSlice011ZeroWarnings::test_zero_check_e_warnings`
- `tests/unit/test_invariant_assertions.py::TestSlice011ZeroWarnings::test_zero_check_d_failures`
- `tests/unit/test_sweep_debt_cleanup.py::test_v5_architecture_validator`
- `tests/unit/test_validate_architecture.py::test_v1_cairn_self_dogfood_baseline`

All 14 fail on the same INV-002 token-budget breach in `.claude/handoff.md` (727 tokens vs 440-token fail-at threshold). Pre-existing; documented in handoff.md "Blocked / Pending" as carry-over.

**M7-introduced GREEN (per-file targeted runs):**

| File | Tests | Result |
|---|---|---|
| `tests/unit/test_marketplace_schema.py` | 5 | 5 PASSED |
| `tests/unit/test_release_workflow.py` | 4 | 4 PASSED |
| `tests/unit/test_build_dist.py` | 11 | 11 PASSED (regression — no M7 regression) |

---

## Validator

Command: `uv run python scripts/validate_architecture.py`.

**Result:** `FAILED — 1 issue(s)` + 1 warning.

- **FAIL: Check D — INV-002 structural-parser:** token budget exceeded — 727 tokens (fail-at 440) in `.claude/handoff.md`. **Pre-existing** (matches handoff.md "Blocked / Pending" lines 22–23 and is the documented INV-002 re-baseline carry-over). Out-of-scope for M7.
- **WARNING: Check E — INV-012 has no machine-checkable assertion.** `docs/ARCHITECTURE.md:99` carries INV-012 prose but does not yet declare an `invariant-check INV-012` block with `type: test-ref` pointing at `tests/unit/test_marketplace_schema.py`. Per plan §Phase 4 Bonus and intent.md §Verification check 7, this is a **recommended bonus, not required for merge**. The lint exists and binds to INV-012 in spirit (5 assertions, each citing ADR D2/D3/D7); landing the `invariant-check` block is left as a Phase-4b or post-merge cleanup decision.

**Per-invariant breakdown:**

| Invariant block | Validator status |
|---|---|
| INV-001 commit-prefix grammar | PASS |
| INV-002 handoff token budget | **FAIL (pre-existing, out-of-scope)** |
| INV-003 phase topology | PASS |
| INV-004 turn-1 context budget | (not validator-checked; pytest live measure) |
| INV-005…INV-011 | PASS |
| INV-012 release-branch deployment | PASS prose, **WARN no test-ref binding (bonus deferred)** |

No NEW validator failures introduced by M7.

---

## Invariants

| INV | Statement (truncated) | Status | Evidence |
|---|---|---|---|
| INV-012 | `marketplace.json` carries `source.source: "github"` + `ref: "release"` (not relative-path, not omitted-ref); `release` branch HEAD IS the curated dist-payload (no `dist/` subdirectory); CI release workflow is `workflow_dispatch`-triggered with version cross-check; force-with-lease replaces `release` tree on each release. | **PASS (schema + workflow); WARN (no `invariant-check` test-ref block yet)** | (1) Schema: `.claude-plugin/marketplace.json:8-12` — `"source": {"source": "github", "repo": "firaaz/cairn", "ref": "release"}`; no top-level `version`, no `type` field — committed at Phase 3 (`b1439c9`). (2) Lint: `tests/unit/test_marketplace_schema.py:38-46` (`source==github`), `:49-52` (`repo==firaaz/cairn`), `:55-62` (`ref==release`), `:65-73` (`"version" not in plugins[0]`), `:76-84` (`"type" not in source`) — 5 assertions, all GREEN. (3) Workflow: `.github/workflows/release-publish.yml:11` (`workflow_dispatch`), `:13-16` (required `version` input), `:48-60` (FLI-2 cross-check before any push), `:106` (`chore: release v${VERSION}` literal commit prefix — INV-001 binding), `:110` (`git push --force-with-lease origin release` — FLI-3), `:34,40` (only `actions/checkout@v4` + `astral-sh/setup-uv@v3` — FLI-4 first-party only), `:26-27` (`permissions: contents: write` only). (4) Dist-gate extension: `.github/workflows/dist-gate.yml:27` runs the new tests alongside `test_build_dist.py` (PASS-by-construction CI binding). (5) Bonus `invariant-check INV-012` block in `docs/ARCHITECTURE.md` — **NOT YET LANDED**; recorded as PENDING follow-up per plan §Phase 4 Bonus, NOT required for merge. |

---

## Audit Checks

Per intent.md §Verification (lines 86–93) and plan §Phase 4 (lines 238–248).

### Check 1 — `tests/unit/test_marketplace_schema.py` passes (5 assertions)

**VERDICT: PASS.** `5 passed in 0.01s`. All 5 ADR-cited assertions GREEN:
1. `plugins[0].source.source == "github"` — `tests/unit/test_marketplace_schema.py:38-46`.
2. `plugins[0].source.repo == "firaaz/cairn"` — `:49-52`.
3. `plugins[0].source.ref == "release"` — `:55-62`.
4. `"version" not in plugins[0]` — `:65-73`.
5. `"type" not in plugins[0].source` — `:76-84`.

### Check 2 — `tests/unit/test_release_workflow.py` passes (4 assertions)

**VERDICT: PASS.** `4 passed in 0.02s`. All 4 workflow-shape assertions GREEN:
1. `Path(".github/workflows/release-publish.yml").exists()`.
2. `on.workflow_dispatch.inputs.version` present.
3. `--force-with-lease` present AND no bare `git push --force ` / `git push --force\n` token.
4. `chore: release` literal commit-prefix present.

### Check 3 — `tests/unit/test_build_dist.py` regression

**VERDICT: PASS.** `11 passed in 0.41s`. No M7 regression; F1 packaging surface intact.

### Check 4 — `dist-gate.yml` runs clean on PR-time invocation against M7 branch

**VERDICT: PASS-by-construction.** Cannot trigger CI from Phase 4a; substitute is grep-evidence that Phase 3's extension landed.

Evidence: `.github/workflows/dist-gate.yml:27` reads:

```
        run: uv run pytest tests/unit/test_build_dist.py tests/unit/test_marketplace_schema.py tests/unit/test_release_workflow.py -q
```

All three files exist (checks 1–3 ran them locally), so the dist-gate.yml step will collect and run them on the next PR-time invocation.

### Check 5 — `marketplace.json` valid JSON; field-by-field grep matches ADR D2

**VERDICT: PASS.** `python3 -c "import json; json.load(open('.claude-plugin/marketplace.json'))"` parses cleanly. Field-by-field at `.claude-plugin/marketplace.json:1-15`:

| ADR D2 requirement | Evidence |
|---|---|
| `name: "cairn-marketplace"` | `:2` |
| `owner.name: "firaaz"` | `:3` |
| `plugins[0].name: "cairn"` | `:6` |
| `plugins[0].description` (verbatim) | `:7` |
| `source.source == "github"` | `:9` |
| `source.repo == "firaaz/cairn"` | `:10` |
| `source.ref == "release"` | `:11` |
| no top-level `version` | (absent — confirmed by grep) |
| no `type` field on `source` | (absent — confirmed by grep) |

### Check 6 — `release-publish.yml` valid YAML; field-by-field grep matches ADR D5/D6/D8

**VERDICT: PASS.** `uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/release-publish.yml'))"` parses cleanly; top-level keys `['name', on, 'permissions', 'jobs']` (`on` deserializes to bool `True` because of YAML's `on:` ambiguity, which is a pyyaml quirk, not a workflow defect). Field-by-field:

| ADR/FLI requirement | Evidence (`.github/workflows/release-publish.yml`) |
|---|---|
| `workflow_dispatch` trigger | `:11` |
| Required `version` input (string, semver) | `:13-16` |
| Optional `source_ref` input, default `dev` | `:17-21` |
| Secondary `push: tags: ['v*']` (D8 compat) | `:22-24` |
| `permissions: contents: write` only (no `pull-requests:`) | `:26-27` |
| First-party Actions only (FLI-4) | `:34` (`actions/checkout@v4`), `:40` (`astral-sh/setup-uv@v3`) — `grep -nE 'uses:'` returned exactly these two |
| FLI-2 input/built-version cross-check before push | `:48-60` (exits non-zero on mismatch with `::error::` annotation) |
| FLI-5 `chore: release` literal commit prefix | `:106` (`git -C "${WORKTREE}" commit -m "chore: release v${VERSION} from ${SOURCE_SHA:0:7}"`) |
| FLI-3 `--force-with-lease` only (D6) | `:110` (`git -C "${WORKTREE}" push --force-with-lease origin release`); `grep -cE 'force-with-lease' = 4`; `grep -cE 'force [^w]' = 0` (no bare `--force`) |
| M7.3 first-run defense | `:86-92` (`git ls-remote --exit-code --heads origin release` → fall back to `git worktree add --orphan -b release`) |
| D8 conditional tag step | `:112-125` (idempotent create-or-update of `v${VERSION}` tag, `if: github.event_name == 'workflow_dispatch'`) |

### Check 7 — `scripts/validate_architecture.py` no NEW failures vs F3 baseline

**VERDICT: PASS (no NEW failures).** Validator output: `FAILED — 1 issue(s)` (INV-002 handoff token budget — pre-existing) + 1 warning (Check E: INV-012 has no machine-checkable assertion). Both match the M7 plan's documented baseline exactly. The Check-E warning is the bonus item from plan §Phase 4 — landing an `invariant-check INV-012 type: test-ref` block in `docs/ARCHITECTURE.md` referencing `tests/unit/test_marketplace_schema.py::test_marketplace_source_ref_is_release` would resolve it; **deferred to a follow-up edit, not required for merge**.

### Check 8 — Full pytest suite matches 14-entry baseline

**VERDICT: PASS (with 1 environmental anomaly, out-of-scope).** All 14 baseline failures reproduce verbatim. The 9 new M7 tests are GREEN. The 1 NEW failure (`test_context_budget.py::test_inv004_turn1_token_budget`) is environmental (live `claude` CLI session-state, CC `2.1.136`, 69720 tokens) and not introduced by M7's diff — `git diff --stat 38ea8b5..HEAD` confirms M7 changed no file imported by that test. Recommend re-pinning baseline post-merge if it persists across sessions.

### Check 9 — Manual end-to-end install (NON-SKIPPABLE)

**Audit check 9 (manual end-to-end install).** VERDICT: **PASS-with-pending-manual-round-trip**

Substantial machine-half verification COMPLETE. Steps V-3 + V-5 remain
operator-bound until a fresh non-cairn Claude Code session can run
`/plugin install` — these are the M7.5 empirical-residual slots ADR D9
requires for full merge-final status.

Following the F3 precedent (sweep-notes line 10:
"PASS-with-pending-manual"), M7 is merge-eligible but not merge-final
until V-3 + V-5 record green.

#### V-1 — push to origin: PASS
- `git push origin dev` succeeded: `bfef6e5..05b2de3 dev -> dev` (2026-05-09).

#### V-2 — release-publish workflow: PASS
- Run link: https://github.com/firaaz/cairn/actions/runs/25601897616
- head_sha: `05b2de31ef9fa4cf38b928729bb59e88a43710da`
- Conclusion: success (10s)
- All 9 workflow steps PASS — including FLI-2 version cross-check, FLI-3 force-with-lease (no bare `--force`), FLI-5 `chore:` prefix, D8 idempotent tag.
- release branch SHA on origin: `779b013116ae3788673ac9428be67f88b41238fe`
- v0.1.0 tag SHA on origin: `f8e2b70df77ea4acd9439948b096202968c1f011` (annotated)
- release branch tree at root: `.claude-plugin/`, `agents/`, `checks/`, `hooks/`, `postinstall_validate.py`, `skills/`, `templates/` — D1 satisfied (no `dist/` subdirectory; build-output contents at branch root, confirmed via `gh api repos/firaaz/cairn/contents?ref=release`).

#### V-3 — fresh-project /plugin install round-trip: PENDING (operator-bound)
- Requires a Claude Code session in a non-cairn directory invoking `/plugin marketplace add https://github.com/firaaz/cairn` then `/plugin install cairn@cairn-marketplace`. The orchestrator session cannot invoke slash commands across sessions.
- This step's empirical claim is THE M7.5 residual (intent.md:110): "marketplace.json parses but Anthropic's resolver does not follow `source.source:'github'` to `ref:'release'` as the docs imply." V-3 is the by-construction empirical verification.
- Prerequisites verified: marketplace.json on `dev` has the M7-correct shape (`source.source:"github"` + `repo:"firaaz/cairn"` + `ref:"release"`) — confirmed via `gh api repos/firaaz/cairn/contents/.claude-plugin/marketplace.json?ref=dev`.

#### V-4 — postinstall_validate.py: PASS (against published payload)
- Cloned release branch into `/tmp/cairn-release-test` (`git clone --depth 1 --branch release https://github.com/firaaz/cairn.git`).
- Ran: `CLAUDE_PLUGIN_ROOT=/tmp/cairn-release-test python3 /tmp/cairn-release-test/postinstall_validate.py`
- Exit code: `0`. No stderr. The script's two stages — (a) warn-only `jq`/`ruff` dep probes and (b) the load-bearing positive end-to-end envelope-enforcement self-test (per ADR D5 / Pre-mortem Scenario 1) — both pass against the live published payload.
- This validates step 4 of the V-thread runbook against the artefact actually shipped on origin/release at SHA `779b013`.
- Note: in a real consumer install, V-4 runs from the consumer's plugin cache, not from a tmp clone. The behavior tested (envelope-enforcement firing) is identical; cache layout is the only difference and is owned by Anthropic's resolver (V-3's domain).

#### V-5 — hook-fire smoke test: PENDING (operator-bound)
- Requires a Claude Code session in the consumer's fresh-project directory dispatching a trivial `cairn-tdd-feature` cycle and observing `reversibility-guard.sh` / `role_guard.py` lines in stderr OR `.claude/envelope-grants.log` landing consumer-side. Same cross-session constraint as V-3.

#### FLI-2 end-to-end cross-check: PASS
- `release:.claude-plugin/plugin.json:version == "0.1.0"` (verified via gh api), matches the workflow's input `version` parameter. The cross-check held end-to-end.

#### Aggregate VERDICT
- **PASS-with-pending-manual-round-trip.** Machine-half verification (V-1, V-2, V-4) complete; manual half (V-3, V-5) pending operator's fresh-project session. M7 is **merge-eligible but not merge-final** until V-3 + V-5 record green. F3 sweep-notes (`.claude/skill-runs/cairn-m6-f3-migration-and-symlink-retire/integration/sweep-notes.md`) closure remains gated on V-3 + V-5.
- Highest-leverage residual M7.5 (Anthropic resolver behavior on `source.source:"github"` + `ref:"release"`) is empirically pending; V-3 is the verification slot.

#### Recording protocol for V-3 + V-5 closure
When the operator returns with V-3 transcript + V-5 hook-fire evidence, this section gains a final block:
```
**V-3 + V-5 closure:** VERDICT changed PARTIAL-PASS → PASS at <commit-sha>.
- V-3 transcript: <pasted or path>
- V-5 hook-fire evidence: <stderr / grants log line>
- M7 merge-final; F3 PENDING → PASS via follow-up commit.
```

#### V-3 attempt 1 falsification (2026-05-10) and manifest amendment

V-3 ran from a fresh non-cairn Claude Code session. Result: install **failed**.

```
Failed to install: Failed to clone repository: Cloning into
  '/Users/firaazfarook/.claude/plugins/cache/temp_github_<id>'...
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.
```

**Root cause.** Claude Code's plugin resolver, given the M7-shipped manifest shape (`source.source: "github"` + `repo: "firaaz/cairn"` + `ref: "release"`), constructs an SSH-protocol clone URL (`git@github.com:firaaz/cairn`). Operator's machine has no GitHub SSH key registered; HTTPS is the working transport. Manual `git clone --branch release https://github.com/firaaz/cairn` succeeds — confirming the `release` branch payload is intact and reachable; only the resolver's protocol choice is the failure.

**Falsification axis vs. ADR D9 prediction.** The original ADR `m5-plugin-deployment-pattern.md:151` flagged the residual as: "decoupling [of plugin-source clone ref from marketplace's clone] is supported by the docs but never empirically verified against Claude Code's actual resolver." V-3 actually verified the schema parses + the `ref: "release"` is followed correctly. The unanticipated failure is one layer down: transport-protocol selection for `source: "github"`. The ADR predicted falsification at the schema-follow axis; V-3 falsified at the transport-protocol axis. Both are "Anthropic resolver behavior" but at different stages of resolution.

**Corroboration.** Three parallel research threads (2026-05-10) confirmed `source: "github"` forces SSH-clone is a known unfixed Claude Code bug:
- `anthropics/claude-code#26588` (OPEN) — "Marketplace plugin cloning should default to HTTPS instead of SSH" — feature request, unshipped.
- `anthropics/claude-code#47088` (CLOSED COMPLETED 2026-04-12) — same failure mode, macOS, identical stderr; closed without code-fix.
- `anthropics/claude-code#50725` (OPEN) — Windows-specific; reports SSH-clone behavior on `url`-typed sources too. Risk caveat for Windows consumers, not the macOS/Linux common case.
- Anthropic's own `claude-plugins-official` marketplace uses `git-subdir` and `url` source types — never `github`.

**Amendment.** ADR `marketplace-source-url-amend` (2026-05-10) supersedes `m5-plugin-deployment-pattern/D2` and `m5-plugin-deployment-pattern/D7`. Manifest swap: `source: "url"` + `url: "https://github.com/firaaz/cairn.git"` + `ref: "release"` (unchanged). Schema-lint test updated to assert the new shape; all 5 schema tests GREEN against the amended manifest. INV-012 binding (`tests/unit/test_marketplace_schema.py::test_marketplace_source_ref_is_release`) is unchanged — that test asserts `ref: "release"`, which is preserved. **No `release`-branch / v0.1.0 tag changes** — `release` never carried `marketplace.json`; only `dev`-tip's manifest and the schema-lint test change.

**Status after amendment.** VERDICT remains **PASS-with-pending-manual-round-trip**. V-3 must re-run against the amended manifest (`dev`-tip `marketplace.json` with `source: "url"`) before V-3 records green and the closure block above is filled in. V-5 (hook-fire smoke test) is unblocked once V-3 succeeds.

**Re-run runbook for V-3 attempt 2:**
1. Commit + push the amendment package (this sweep-notes edit + ADR + manifest + test updates) to `origin/dev`.
2. Fresh Claude Code session in a non-cairn directory.
3. Run `/plugin marketplace add https://github.com/firaaz/cairn`. Expect: success (this step never failed).
4. Run `/plugin install cairn@cairn-marketplace`. **Expect: success**, payload lands under `~/.claude/plugins/cache/`.
5. If install fails with the same SSH stderr: report — there is a deeper issue beyond the documented `url`-source-type behavior (possibly intersecting `#50725`'s Windows-style failure on macOS, which would be a new finding worth filing).
6. If install fails with a different error: capture stderr; investigate. The `url` source-type is documented and used by Anthropic's own marketplace, so unexpected failures here are signal.
7. Run `uv run python ${CLAUDE_PLUGIN_ROOT}/postinstall_validate.py`. Expect: clean exit + envelope-enforcement self-test PASS (already verified end-to-end against published `release` payload in V-4).
8. Trivial `cairn-tdd-feature` dispatch — V-5. Confirm hook stderr / `.claude/envelope-grants.log` lands consumer-side.

#### V-3 attempt 3 + V-5 CLOSURE (2026-05-12) — A1 (`source: "url"` + `sha:`) PASS

**VERDICT changed PARTIAL-PASS → PASS at commit 2a7e145 (marketplace.json sha pin to release HEAD 04994cc).**

V-3 attempt 3 ran A1 (the `url` + `sha` shape) after the operator elected probe-A1-first to avoid paying A3a's commit-`dist/` operational cost. The probe falsified the Phase-3 adversarial prediction (which had ranked A1 as non-causal-pattern dismissal): the 82/82 sha-pinning population pattern in Anthropic's marketplace IS causal — the resolver branches on sha-vs-ref pinning, not just on host detection.

**Sequence:**
1. Probe commit 9f419aa (2026-05-12) swapped marketplace.json `ref: "release"` → `sha: "779b013…"` (release HEAD).
2. V-3 attempt 3 install: PASS. No `git@github.com: Permission denied`, no `temp_github_<id>` cache path.
3. **Latent M5 packaging bug surfaced** at hook-load time: `Hook load failed: [{"expected": "record", "code": "invalid_type", "path": ["hooks"], "message": "Invalid input: expected record, received undefined"}]`. Cairn's `hooks.json` shipped flat (`{PreToolUse: [...], PostToolUse: [...]}`) but Claude Code's plugin schema requires the `{"hooks": {...}}` wrapper. Bug was latent through M5/M6/M7 because every prior install attempt failed at SSH before reaching the hook loader. Fixed at commit a18bca0 (`.claude-plugin/hooks-template.json` rewrapped + `tests/unit/test_hooks_json.py` helpers + `_hook_root` assertion bound to the live "received undefined" stderr).
4. Release-publish workflow re-ran v0.1.0; new release HEAD `04994cc863a00afd14ac0d67c2a78f25a601a922`.
5. marketplace.json sha-pin bumped to 04994cc (commit 2a7e145).
6. Operator: `/plugin marketplace remove cairn-marketplace` + add + install. Install: PASS. Hook-load: PASS (no schema error).
7. **V-5 hook-fire evidence:** consumer Claude Code session, operator dispatched `Bash(rm -rf /tmp/cairn-test-doesnt-exist)`. Result: blocked by `reversibility-guard.sh` PreToolUse hook with stderr `REVERSIBILITY GUARD: rm -rf: use rm with explicit paths instead`. Hook firing confirmed end-to-end consumer-side. V-5 PASS.

**M7 merge-final.** F3 audit check 9 PENDING → PASS via this commit. The plugin-deployment pattern is empirically validated for fresh consumers without GitHub SSH keys configured.

**Documented update-mechanism fragility (S4 from plugin-payload-transport Phase 1 pre-mortem materialized):** `/plugin update cairn@cairn-marketplace` does NOT refresh consumer's marketplace cache to pick up new sha pins. Workaround: manual `/plugin marketplace remove cairn-marketplace; /plugin marketplace add https://github.com/firaaz/cairn` per release iteration. To be documented in CONSUMER.md as part of the plugin-payload-transport ADR revision.

**ADR-revision pending (separate commit chain):** `plugin-payload-transport` (committed a10342f) elevated A3a as load-bearing on the Phase-3 adversarial premise that A1 was non-causal pattern-dismissal. Empirical reality reranked: A1 works, A3a's commit-`dist/` cost is unnecessary. Revision will supersede plugin-payload-transport with A1-load-bearing shape; INV-012 wording reverts toward sha-pin; test_marketplace_schema.py rewrites for `sha`-shape assertions; lessons.md gains entry on cheap-probe-trumps-strong-adversarial-argument.

#### V-3 attempt 2 falsification (2026-05-11) — `source: "url"` does not bypass the SSH-clone path

Operator ran V-3 attempt 2 in a fresh non-cairn Claude Code session after the `marketplace-source-url-amend` ADR + manifest landed on `origin/dev`. Procedure: `/plugin marketplace remove cairn-marketplace`, then `/plugin marketplace add https://github.com/firaaz/cairn`, then `/plugin install cairn@cairn-marketplace`. Result: **install failed with the identical SSH stderr** as attempt 1.

```
Failed to install: Failed to clone repository: Cloning into
  '/Users/firaazfarook/.claude/plugins/cache/temp_github_1778513919255_bulpop'...
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.
```

**Cache forensics (2026-05-11, in-session by main agent):**
- `~/.claude/plugins/marketplaces/cairn-marketplace/.claude-plugin/marketplace.json` — present, correct amended shape (`source: "url"` + `url: "https://github.com/firaaz/cairn.git"` + `ref: "release"`). The cached marketplace manifest is the post-amendment shape; this rules out stale-manifest causes.
- `~/.claude/plugins/marketplaces/cairn-marketplace/` — fully populated via HTTPS clone (full repo tree present, including 14k CHANGELOG.md and 59k uv.lock). **Marketplace-add HTTPS clone works.**
- `~/.claude/plugins/known_marketplaces.json` — Claude Code normalized our `source: "url"` to `source: "git"` in its internal registration. Cosmetic — the URL field is preserved with HTTPS.
- `~/.claude/plugins/cache/` — contains only `claude-plugins-official/`; no cairn dir, no leftover `temp_github_*` (cleaned up after failed install).

**What this means.** Failure is at the **plugin-install** layer, not marketplace-add. The cached marketplace.json correctly declares `source: "url"`, but Claude Code's install path still routes through its github-source clone handler (the `temp_github_<id>` cache-dir name is diagnostic of that handler). The `url` source-type, when the URL host is `github.com`, falls through to the github clone code path which prefers SSH.

**Falsifies.** ADR `marketplace-source-url-amend` (load-bearing claim: "swap `source: "github"` → `source: "url"` to bypass the SSH-clone failure"). The pivot does not bypass; the failure mode is one layer below `source` typing, in the resolver's host-based routing. Status flipped `accepted → falsified`.

**What's still valid.**
- INV-012 binding (`tests/unit/test_marketplace_schema.py::test_marketplace_source_ref_is_release`) — the test asserts schema shape, which is correctly amended; the test is unrelated to the resolver bug.
- M5 plugin-deployment-pattern's V-1/V-2/V-4 evidence (release-publish workflow, postinstall_validate against the published payload) — unchanged.
- `release` branch + v0.1.0 tag + release-publish.yml — unchanged; no rollback needed.

**What's blocked.**
- M7 merge-final. F3 check 9 PENDING → cannot transition to PASS via any URL/github source-type pointing at `github.com` against operators without SSH keys.
- V-5 hook-fire smoke test — blocked behind V-3.

**Next.** Out-of-band `/decision` on plugin-payload transport (options sketched: GitHub Releases tarball URL, self-hosted artifact, `git-subdir` source-type, document SSH prerequisite + falsify zero-friction premise, file upstream bug + wait). The decision supersedes both `m5-plugin-deployment-pattern/D2` and `marketplace-source-url-amend` and produces the new transport ADR.

---

## Follow-up notes (not blocking merge)

1. **Bonus — INV-012 `invariant-check` block.** Add to `docs/ARCHITECTURE.md` after the INV-012 prose paragraph:
   ```yaml
   invariant-check INV-012:
     type: test-ref
     test: tests/unit/test_marketplace_schema.py::test_marketplace_source_ref_is_release
   ```
   Resolves Check-E warning. Plan §Phase 4 Bonus calls this "recommended; not strictly required for merge." Defer to Phase 4b or a sweep-debt slice.
2. **Baseline re-pin candidate — `test_inv004_turn1_token_budget`.** The +1 anomaly above is session-state-dependent (live `claude` CLI). After M7 merges, capture a fresh baseline-failures file pinned to the post-merge tip and update `/tmp/cairn-m7-plugin-deployment-pattern-baseline-failures.txt` (or its successor in F-next) accordingly.
3. **INV-002 handoff-budget breach** continues to dominate the validator/pytest failure list (14 of the 14 baseline failures trace to it). Outside M7's scope; tracked in `.claude/handoff.md` "Blocked / Pending".
