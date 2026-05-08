---
id: cairn-m5-f1-packaging
envelope:
  paths:
    - ^docs/plans/2026-05-08-cairn-m5-f1-packaging\.md$
    - ^\.claude-plugin/marketplace\.json$
    - ^dist/\.claude-plugin/plugin\.json$
    - ^dist/hooks/hooks\.json$
    - ^scripts/build_dist\.py$
    - ^scripts/postinstall_validate\.py$
    - ^checks/role_guard\.py$
    - ^tests/unit/test_role_guard_anchoring\.py$
    - ^tests/unit/test_build_dist\.py$
    - ^tests/unit/test_postinstall_validator\.py$
    - ^tests/unit/test_plugin_manifests\.py$
    - ^tests/unit/test_hooks_json\.py$
    - ^\.github/workflows/dist-gate\.yml$
firmness: provisional
status: draft
date: 2026-05-08
scope: F1 of M5 — author plugin manifests, dist build script, hook registration, post-install validator, and role_guard runtime-anchoring fix; CI gates dist payload allow-list. No consumer-doc surface (F2) or migration (F3).
inputs:
  - docs/adr/m5-plugin-distribution-and-symlink-retire.md
  - .claude/skill-runs/m5-plugin-decision/phase-0-constraints.md
  - .claude/skill-runs/m5-plugin-decision/phase-1-pre-mortem.md
  - .claude/skill-runs/m5-plugin-decision/phase-3-corrections-applied.md
  - .claude/skill-runs/m5-plugin-decision/phase-5-reconciliation.md
  - checks/role_guard.py
  - .claude/settings.json
  - docs/operational-reference.md
---

# Cairn M5 F1 — Plugin packaging

> **For agentic workers:** REQUIRED SUB-SKILL: `cairn-tdd-feature` is the dispatch shell — this plan is its input. Each section below maps to TDD-shaped Phase-2 reds + Phase-3 implementation. Within-feature parallelism via parallel Agent calls is permitted per CLAUDE.md "Within-slice parallel subagents are allowed" — Sections F1.1 (manifests) and F1.4 (hooks.json) have no shared state and may run concurrently from a single Phase-3 dispatch. Section F1.5 (`role_guard.py` anchoring fix) MUST land before Section F1.6 (post-install validator) — the validator's positive enforcement test calls the patched code path.

**Goal:** Make cairn installable as a Claude Code plugin via its own marketplace, with a curated `dist/` payload (no leak of `tests/`, `docs/adr/`, `.local/`, `.venv/`), plugin-internal hook registration that needs no consumer settings.json merge, a `role_guard.py` that anchors `CAIRN_ROOT` on `CLAUDE_PROJECT_DIR` so envelope enforcement survives plugin-cache invocation, and a post-install validator that exercises envelope enforcement end-to-end (dep-checks alone are theatre per Pre-mortem Scenario 1).

**Architecture:** Three artifact threads + one source-code fix + one CI gate. **Thread 1 (manifests, D1+D2):** `.claude-plugin/marketplace.json` declares cairn-as-its-own-marketplace; `dist/.claude-plugin/plugin.json` carries explicit `"version": "0.1.0"`; `marketplace.json source.path: "dist/"` points at the curated subdir. **Thread 2 (`dist/` build, D3):** `scripts/build_dist.py` copies + renames from canonical layout into `dist/{skills,agents,checks,templates,hooks}/` against an explicit allow-list. **Thread 3 (hooks, D4):** `dist/hooks/hooks.json` registers the three hooks using `${CLAUDE_PLUGIN_ROOT}` substitution, replacing the legacy `.slice-system/checks/...` consumer-settings.json merge. **Source-code fix (D5):** `checks/role_guard.py:28,121` swap `Path(__file__).resolve().parent.parent` for `Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))` so envelope file + audit log resolve against the consumer's project, not the plugin cache. **CI gate (D3 + Risk #5):** GitHub Actions runs `build_dist.py` then asserts the output matches the allow-list. **Post-install validator (D5):** `scripts/postinstall_validate.py` warns on missing `jq`/`ruff`, then runs a **positive enforcement self-test** — writes a sample `mode: operator` envelope under a tmp `CLAUDE_PROJECT_DIR`, invokes `role_guard.py` against an out-of-envelope path, asserts exit 1.

**Tech Stack:** Python 3.11 (cairn standing dep set: pyyaml, pydantic, typer; per CLAUDE.md "New code is Python, function-based"). JSON for plugin manifests + `hooks.json`. Bash unchanged (existing `.sh` hooks ride along verbatim). YAML for sample envelopes in tests. GitHub Actions for the CI gate. uv-managed venv (`uv run pytest`, `uv run python scripts/build_dist.py`). No new third-party deps introduced.

---

## Self-review summary

This plan covers all D-commitments routed to F1 by the ADR's D9 split:

- **D1** — `.claude-plugin/marketplace.json` + `dist/.claude-plugin/plugin.json` authored in Section F1.1.
- **D2** — Explicit `"version": "0.1.0"` in `dist/.claude-plugin/plugin.json`; tag protocol `v0.1.0` documented in Section F1.1 Step 4 (release-note shape, not git operation).
- **D3** — `scripts/build_dist.py` + allow-list in Section F1.2; CI gate in Section F1.7.
- **D4** — `dist/hooks/hooks.json` with `${CLAUDE_PLUGIN_ROOT}` substitution in Section F1.4.
- **D5** — `role_guard.py:28,121` runtime-anchoring fix in Section F1.5; **positive end-to-end enforcement test** in the post-install validator in Section F1.6 (NOT a green dep-check).
- **D9** (partial) — F1 ships first; nothing in this plan touches F2's CONSUMER.md surface or F3's migration steps.

Coverage gaps and routing decisions:

- The phase-skill-mapping promotion (Finding 4) and adoptable-disciplines list (Finding 5) are F2 surface — not in scope here.
- The `complex-rag-analysis` migration and downstream `.slice-system → .` retire are F3 — not in scope here.
- `commands/claude-code/.local/` slash-command payload is **deferred to M5.1** per ADR D3 — `dist/commands/` is intentionally absent from the F1 build script. The build script's allow-list is structured so adding `dist/commands/` later is a one-line change.
- `dist/` build script intentionally does NOT copy `pyproject.toml`, `uv.lock`, `.venv/`, `tests/`, `docs/adr/`, `docs/plans/`, `docs/reviews/`, `commands/claude-code/.local/`, or `scripts/slice_orchestrator/` (the latter is being retired; see operational-reference). These omissions are asserted by Section F1.2's allow-list test, not by deny-list — Risk #5 in the ADR explicitly warns against deny-list audits.
- `scripts/_root.py` and `scripts/lib/` carry-forward to `dist/` is flagged for F1.2 Step 3 verification — the ADR D3 notes "scripts/ (other than `_root.py` + `lib/` if hooks need them — confirm in F1)". Decision pinned to "do not include" unless a hook actually imports from them; current `role_guard.py` is stdlib + lazy `pyyaml`, no `lib/` dependency. Documented in Section F1.2.

---

## Section F1.1 — Plugin manifests (D1, D2)

**Files:**
- Create: `.claude-plugin/marketplace.json`
- Create: `dist/.claude-plugin/plugin.json`
- Create: `tests/unit/test_plugin_manifests.py`

**Why:** Per ADR D1, cairn becomes its own marketplace. Per `code.claude.com/docs/en/plugins-reference:1004-1008`, plugin version is an explicit string field — manual bumps required, no inferred semver. Per ADR D2, version `0.1.0` is the F1 ship version; tag is `v0.1.0`.

- [ ] **Step 1: Write failing tests for manifest shape.**

In `tests/unit/test_plugin_manifests.py`, assert:
- `.claude-plugin/marketplace.json` exists and parses as JSON.
- It contains a `plugins` array with exactly one entry whose `name` is `cairn`.
- That entry's `source.type` is `"git"`, `source.path` is `"dist/"`, and either `source.ref` (tag) or `source.sha` is settable (the field is allowed but may be unset at HEAD).
- `dist/.claude-plugin/plugin.json` exists and parses as JSON.
- `plugin.json.name` is `"cairn"`, `plugin.json.version` is exactly the string `"0.1.0"` (D2: explicit, not derived).
- `plugin.json.description` is non-empty.
- The two manifests' `name` fields agree.

Run: `uv run pytest tests/unit/test_plugin_manifests.py -q`. Expect 5+ failures (files don't exist).

- [ ] **Step 2: Author `.claude-plugin/marketplace.json`.**

Shape per `code.claude.com/docs/en/plugin-marketplaces`:

```json
{
  "name": "cairn-marketplace",
  "owner": { "name": "firaaz" },
  "plugins": [
    {
      "name": "cairn",
      "description": "TDD-by-construction dispatch skill, hooks, and protocols for Claude Code.",
      "source": {
        "type": "git",
        "url": "https://github.com/firaaz/cairn.git",
        "path": "dist/"
      }
    }
  ]
}
```

(Concrete `url` to be confirmed at install — `marketplace.json` is repo-resident, so the consumer who runs `/plugin marketplace add <git-url>` supplies the URL. Field present per spec.)

- [ ] **Step 3: Author `dist/.claude-plugin/plugin.json`.**

```json
{
  "name": "cairn",
  "version": "0.1.0",
  "description": "Cairn — TDD-by-construction dispatch for Claude Code.",
  "homepage": "https://github.com/firaaz/cairn"
}
```

- [ ] **Step 4: Document tag protocol in plan-adjacent release notes.**

Add a brief paragraph to the release-tagging section of `docs/operational-reference.md` (under "Routing" or a new "Release tagging" subsection) noting: "Plugin version tags follow `v0.x.y`. F1 lands `v0.1.0`. Major version stays at `0` until the 6 amendment ADRs close per ADR D2." This is documentation-only — no `git tag` command runs in F1; tagging is a release-time operator action after the F1 PR merges.

- [ ] **Step 5: Re-run tests.** Expect green.

---

## Section F1.2 — `dist/` build script (D3)

**Files:**
- Create: `scripts/build_dist.py`
- Create: `tests/unit/test_build_dist.py`

**Why:** Plugin manifests have no `include`/`exclude` glob fields per ADR D3; curation is by physical separation. The build script is the authoritative allow-list. CI runs it every release; any drift between source layout and plugin payload is caught before consumers see it.

- [ ] **Step 1: Write failing tests for build_dist behaviour.**

In `tests/unit/test_build_dist.py`, run `build_dist.py` against tmp output and assert:

1. **Allow-list coverage** — these paths exist post-build: `dist/.claude-plugin/plugin.json`; `dist/skills/cairn-tdd-feature/SKILL.md`; `dist/agents/{phase-1,phase-2,phase-3,phase-4,triager}-tdd.md`; `dist/agents/role-topology.yaml`; `dist/checks/{reversibility-guard.sh,reality-check.sh,role_guard.py}`; `dist/templates/handoff.md` (only template at F1; F2 expands); `dist/hooks/hooks.json`; `dist/postinstall_validate.py`.
2. **Deny-list (negative)** — none of these appear: `dist/tests/`, `dist/docs/`, `dist/.venv/`, `dist/uv.lock`, `dist/pyproject.toml`, `dist/commands/` (slash-commands deferred to M5.1), `dist/scripts/slice_orchestrator/`, `dist/.claude/skill-runs/`, `dist/docs/{adr,plans,reviews}/`.
3. **Idempotence** — two consecutive runs produce byte-identical output (build script cleans output before populating).
4. **Symlink hazard guard** — never traverses `.slice-system → .` (CLAUDE.md "Symlink recursion hazard").

- [ ] **Step 2: Author `scripts/build_dist.py`.**

Shape (function-based, no decorators/metaprogramming):

- `ALLOW_LIST: list[tuple[str, str]]` — explicit `(canonical_src, dist_dest)` rename pairs:
  - `(".claude/skills/cairn-tdd-feature", "dist/skills/cairn-tdd-feature")`
  - `(".claude/agents/{phase-1,phase-2,phase-3,phase-4,triager}-tdd.md", "dist/agents/<same>")` (5 rows, listed individually per CLAUDE.md "three similar lines beats one abstraction")
  - `(".claude/agents/role-topology.yaml", "dist/agents/role-topology.yaml")`
  - `("checks/{reversibility-guard.sh,reality-check.sh,role_guard.py}", "dist/checks/<same>")` (3 rows)
  - `("templates/handoff.md", "dist/templates/handoff.md")`
  - `(".claude-plugin/plugin-template.json", "dist/.claude-plugin/plugin.json")` (per F1.3)
  - `(".claude-plugin/hooks-template.json", "dist/hooks/hooks.json")` (per F1.4)
  - `("scripts/postinstall_validate.py", "dist/postinstall_validate.py")` (per F1.6)
- `def build(repo_root: Path, dist_root: Path) -> None` — cleans `dist_root` first; walks ONLY canonical paths (never `.slice-system/`).
- `def main() -> int` — typer entrypoint; default `repo_root = CLAUDE_ROOT or cwd`, `dist_root = repo_root / "dist"`.

Do NOT generalise rename pairs into a glob engine — list explicitly.

- [ ] **Step 3: Confirm `scripts/_root.py` + `scripts/lib/` are NOT needed by `dist/checks/role_guard.py`.**

Read `checks/role_guard.py` after Section F1.5's anchoring fix — it imports only stdlib + lazy `yaml`. No `lib.*` dependency. Decision: do NOT include `scripts/_root.py` or `scripts/lib/` in `dist/`. Document this in a header comment in `build_dist.py` so future hook additions know to revisit.

- [ ] **Step 4: Re-run tests. Expect green.**

- [ ] **Step 5: Run a manual smoke build.** `uv run python scripts/build_dist.py --repo-root . --dist-root /tmp/cairn-dist-smoke && find /tmp/cairn-dist-smoke -type f | sort`. Eyeball: file list matches allow-list. No `.venv/`, no `tests/`, no `docs/`.

---

## Section F1.3 — `plugin.json` placement coordination

**Why:** `dist/` is build output, not source. Author `plugin.json` at canonical `.claude-plugin/plugin-template.json` (sibling of `marketplace.json`); `build_dist.py` copies it to `dist/.claude-plugin/plugin.json` at build time. This decouples version control from build artifacts and means consumers fetching a tagged commit's `dist/` subtree always see a clean rebuild.

- [ ] **Step 1: Author `plugin.json` at `.claude-plugin/plugin-template.json` (NOT `dist/.claude-plugin/plugin.json`).** Update Section F1.1's tests to read from the canonical source path.

- [ ] **Step 2: Add allow-list row** to `scripts/build_dist.py`: `(".claude-plugin/plugin-template.json", "dist/.claude-plugin/plugin.json")`. Section F1.2's allow-list test asserts the post-build location.

---

## Section F1.4 — Hook registration via `dist/hooks/hooks.json` (D4)

**Files:**
- Create: `.claude-plugin/hooks-template.json` (canonical source)
- Create: `tests/unit/test_hooks_json.py`
- Modify: `scripts/build_dist.py` (add allow-list row `(".claude-plugin/hooks-template.json", "dist/hooks/hooks.json")`)

**Why:** Per ADR D4, hooks register via `dist/hooks/hooks.json` per `code.claude.com/docs/en/plugins-reference:85,671`; `${CLAUDE_PLUGIN_ROOT}` substitutes to the plugin's installation directory per `code.claude.com/docs/en/plugins-reference:542`. NO consumer settings.json merge — Pre-mortem Scenario 2 (settings-merge drift) becomes mostly moot.

- [ ] **Step 1: Write failing tests for `hooks.json` shape.**

In `tests/unit/test_hooks_json.py`, assert against the canonical source `.claude-plugin/hooks-template.json`:

- File parses as JSON.
- `PreToolUse` contains entry matching `Bash|Edit|Write` whose command ends with `checks/reversibility-guard.sh` and contains `${CLAUDE_PLUGIN_ROOT}`.
- `PreToolUse` contains entry matching `Write|Edit|MultiEdit|NotebookEdit` whose command includes `checks/role_guard.py` and `${CLAUDE_PLUGIN_ROOT}`.
- `PostToolUse` contains entry matching `Edit|Write` whose command ends with `checks/reality-check.sh` and contains `${CLAUDE_PLUGIN_ROOT}`.
- No command string contains `$CLAUDE_PROJECT_DIR/.slice-system/` (legacy symlink-anchored path being retired).

- [ ] **Step 2: Author `.claude-plugin/hooks-template.json`.**

Shape:

```json
{
  "PreToolUse": [
    {
      "matcher": "Bash|Edit|Write",
      "hooks": [
        { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/checks/reversibility-guard.sh" }
      ]
    },
    {
      "matcher": "Write|Edit|MultiEdit|NotebookEdit",
      "hooks": [
        { "type": "command", "command": "python3 ${CLAUDE_PLUGIN_ROOT}/checks/role_guard.py" }
      ]
    }
  ],
  "PostToolUse": [
    {
      "matcher": "Edit|Write",
      "hooks": [
        { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/checks/reality-check.sh" }
      ]
    }
  ]
}
```

- [ ] **Step 3: Decision — invoke role_guard via `python3`, not `uv run python`.** Consumer environments may not have `uv` on PATH; `role_guard.py` is stdlib + lazy `pyyaml`. The lazy-yaml import is the stdlib-only happy path (per role_guard docstring); if `pyyaml` is absent under operator-envelope mode the check fails closed. Future consumer reports add `pyyaml` to the validator's warn-set — out of scope for F1.

- [ ] **Step 4: Re-run tests. Expect green.**

---

## Section F1.5 — `role_guard.py` runtime anchoring fix (D5)

**Files:**
- Modify: `checks/role_guard.py:28` (`CAIRN_ROOT` definition)
- Modify: `checks/role_guard.py:121` (`_log_grant()` writes via `CAIRN_ROOT`)
- Create: `tests/unit/test_role_guard_anchoring.py`

**Why:** Per ADR D5 + Pre-mortem Scenario 1: under plugin-cache invocation `__file__` resolves to the plugin cache dir. The current `Path(__file__).resolve().parent.parent` makes `CAIRN_ROOT` point at the cache, so `OPERATOR_ENVELOPE_PATH = CAIRN_ROOT / ".claude" / "active-envelope.yaml"` looks for the envelope inside the plugin cache (which has none), silently fail-opening enforcement. The audit trail at `_log_grant()` (line 121) writes to plugin-cache `envelope-grants.log`, which is ephemeral.

Replacement, both sites:

```python
CAIRN_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
```

- [ ] **Step 1: Write failing tests in `tests/unit/test_role_guard_anchoring.py`.**

Three cases (`importlib.reload` required — `CAIRN_ROOT` is a module-level constant captured at import; document in a header comment):

1. `test_cairn_root_uses_claude_project_dir` — set `CLAUDE_PROJECT_DIR=/tmp/some-consumer`, reload, assert `CAIRN_ROOT == Path("/tmp/some-consumer")` and `OPERATOR_ENVELOPE_PATH` resolves under it.
2. `test_cairn_root_falls_back_to_cwd_when_unset` — `delenv("CLAUDE_PROJECT_DIR")`, `chdir(tmp_path)`, reload, assert `CAIRN_ROOT == tmp_path`.
3. `test_log_grant_writes_under_claude_project_dir` — set `CLAUDE_PROJECT_DIR` to tmp; call `_log_grant("foo/bar.py", "phase-3-tdd")`; assert line lands at `<tmp>/.claude/envelope-grants.log`.

Run: `uv run pytest tests/unit/test_role_guard_anchoring.py -q`. Expect 3 failures.

- [ ] **Step 2: Apply the fix to `checks/role_guard.py:28`.**

Replace `CAIRN_ROOT = Path(__file__).resolve().parent.parent` with `CAIRN_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))`. `os` is already imported at line 20.

- [ ] **Step 3: Verify `:121` already references the corrected `CAIRN_ROOT`.**

Inspect: `_log_grant()` reads `CAIRN_ROOT` at line 121 (`grant_log = CAIRN_ROOT / ".claude" / "envelope-grants.log"`). With the module-level constant fixed, line 121 inherits the fix automatically. Confirm by reading the function body — no second mutation needed.

- [ ] **Step 4: Re-run tests. Expect green.**

- [ ] **Step 5: Run the existing role_guard test suite to confirm no regression.**

`uv run pytest tests/unit/test_role_guard*.py -q` (or whatever the existing role_guard tests are named). The fix is path-source-only; existing matchers and policy-table behavior is unchanged.

- [ ] **Step 6: Run `bash scripts/smoketest_hooks.sh`.** Confirm the role_guard smoke pass is still green under cairn-the-repo (Path B self-symlink — `CLAUDE_PROJECT_DIR` is set by the harness to repo root).

---

## Section F1.6 — Post-install validator with positive enforcement test (D5)

**Files:**
- Create: `scripts/postinstall_validate.py`
- Create: `tests/unit/test_postinstall_validator.py`
- Modify: `scripts/build_dist.py` (allow-list row `("scripts/postinstall_validate.py", "dist/postinstall_validate.py")`)
- Modify: `.claude-plugin/plugin-template.json` (declare validator entrypoint per `code.claude.com/docs/en/plugins-reference` postinstall hook field, if supported — otherwise document manual invocation in CONSUMER.md, deferred to F2)

**Why:** Per ADR D5 / Risk #1 / Pre-mortem Scenario 1: a green dep-check that doesn't exercise enforcement is theatre. The validator must (a) check system deps with warnings, AND (b) run a **positive end-to-end enforcement test** that proves envelope enforcement is wired correctly under plugin-cache invocation.

- [ ] **Step 1: Write failing tests in `tests/unit/test_postinstall_validator.py`.**

1. `test_validator_warns_on_missing_jq` — `setenv("PATH", "/nonexistent")`; run validator; assert exit 0 (warnings non-fatal); stderr contains `jq` + "warn".
2. `test_validator_warns_on_missing_ruff` — same pattern; stderr contains `ruff`.
3. `test_validator_passes_dep_check_when_present` — `jq`/`ruff` resolve via `shutil.which`; no warnings.
4. **`test_validator_positive_enforcement` (load-bearing)** — tmp `CLAUDE_PROJECT_DIR`, sample `mode: operator` envelope `paths: ["^docs/"]`. Validator forks `role_guard.py` against tool-input JSON with `file_path: "scripts/foo.py"` (out-of-envelope). Assert forked process exits 1; validator returns success (deny was expected).
5. `test_validator_fails_loud_when_enforcement_silently_passes` — patch/mock `role_guard.py` to return 0 (simulates pre-D5 `__file__`-anchored break). Validator MUST exit 1 with stderr "envelope enforcement did not deny out-of-envelope write — installation is not safe". This is the canary against future D5 regression.

- [ ] **Step 2: Author `scripts/postinstall_validate.py`.**

Function shape (typer-driven, function-based per CLAUDE.md):

- `def check_dep(name: str) -> bool` — `shutil.which(name)`; on miss print stderr `WARN: <name> not found on PATH; <hook-name> hooks will no-op`. Returns False; does NOT exit.
- `def check_envelope_enforcement(project_dir: Path) -> bool` — load-bearing:
  1. Write `<project_dir>/.claude/active-envelope.yaml` with `mode: operator`, `paths: ["^docs/"]` (auto-generated header comment).
  2. Tool-input JSON: `{"tool_name": "Edit", "tool_input": {"file_path": "scripts/foo.py", "old_string": "x", "new_string": "y"}}`.
  3. Subprocess `python3 <plugin-root>/checks/role_guard.py`, env `CLAUDE_PROJECT_DIR=<project_dir>`, `AGENT_ROLE` unset, stdin=JSON.
  4. Assert returncode==1 AND stderr non-empty; clean up envelope; return True iff deny landed.
- `def main() -> int` — `check_dep("jq")` + `check_dep("ruff")` warn-only; then `check_envelope_enforcement(...)` FATAL on failure (exit 1 + "envelope enforcement self-test failed — installation is not safe").

Plugin-root resolves via `os.environ.get("CLAUDE_PLUGIN_ROOT")` falling back to the script's own directory (cairn-the-repo dogfood invocation works). `project_dir` is a fresh `TemporaryDirectory()` — never the consumer's actual project.

- [ ] **Step 3: Re-run tests. Expect green.**

- [ ] **Step 4: Manual end-to-end smoke** — run `python3 scripts/postinstall_validate.py` from the repo root. Expect deps green (locally installed) AND positive enforcement test passing.

- [ ] **Step 5: Determine plugin auto-invocation hook.**

Read `code.claude.com/docs/en/plugins-reference` for the post-install hook entrypoint field name. If supported (likely a top-level `postinstall:` in `plugin.json` or an entry in `hooks.json`), wire it up. If NOT supported in current plugin spec, document the manual invocation in F2's CONSUMER.md (flag for F2 — out-of-scope for F1 plan-doc but the validator's existence is F1's responsibility).

---

## Section F1.7 — CI gate for `dist/` payload (D3, Risk #5)

**Files:**
- Create: `.github/workflows/dist-gate.yml`

**Why:** Per ADR D3 / Risk #5: payload curation is an allow-list, not a deny-list. CI must populate `dist/` and refuse to merge if anything not on the allow-list appears. Without this gate, accidental file additions leak (e.g., `tests/` accidentally copied during a future build_dist.py edit).

- [ ] **Step 1: Author `.github/workflows/dist-gate.yml`.**

Job shape:
- Trigger: `pull_request` on any branch + `push` to `dev`/`main`.
- Steps:
  1. Checkout.
  2. `uv sync`.
  3. `uv run python scripts/build_dist.py --dist-root /tmp/dist-ci`.
  4. `uv run pytest tests/unit/test_build_dist.py -q` (re-runs the allow-list assertions against the freshly-built tree).
  5. `uv run python scripts/postinstall_validate.py --plugin-root /tmp/dist-ci` (validator self-test against the actual built artifact).

The CI job intentionally runs `build_dist.py` against a tmp dir, not the in-repo `dist/`. F1 does NOT commit a `dist/` tree to the repo — `dist/` is build output, regenerated per release tag. Add `dist/` to `.gitignore` if not already present (verify in Step 2).

- [ ] **Step 2: Verify `.gitignore` excludes build artifacts.**

Read `.gitignore`. If `dist/` is absent, append it. (NOTE: `.claude-plugin/marketplace.json` and `.claude-plugin/plugin-template.json` and `.claude-plugin/hooks-template.json` are SOURCE files and MUST be committed — only the `dist/` build output is gitignored.)

- [ ] **Step 3: Smoke the CI job locally.**

`act` (or manual reproduction): run all five steps in sequence. Expect green.

---

## Section F1.8 — Cairn-the-repo settings.json (verification only)

ADR D8 keeps cairn-the-repo on `.slice-system → .` self-symlink. Current `.claude/settings.json` uses `$CLAUDE_PROJECT_DIR/.slice-system/checks/...` — correct for Path B. F1's `dist/hooks/hooks.json` (using `${CLAUDE_PLUGIN_ROOT}`) is an independent surface; cairn-the-repo's settings.json is NOT consumed by plugin-installed instances.

- [ ] **Step 1: Confirm `.claude/settings.json` is unchanged after F1.** No edits needed for F1. **Flag for F3:** downstream consumers DELETE the `.slice-system`-anchored hook entries after `/plugin install cairn@cairn-marketplace` — that deletion is F3's migration step.

---

## Out-of-scope follow-ups

- **F2 (Consumer-doc surface).** `CONSUMER.md`, README reading order, template expansion (D7), `[both]` tags in CLAUDE.md (D6), phase-skill-mapping promotion (Finding 4), `docs/adoptable-disciplines.md` (Finding 5). F2 also documents manual validator invocation in CONSUMER.md if the plugin spec lacks an auto postinstall hook (see F1.6 Step 5).
- **F3 (Migration + symlink retire).** `complex-rag-analysis` migration, downstream `.slice-system → .` retire, in-flight skill-run quiescence checklist. F3 also handles `.slice-system`-anchored hook-entry deletion in consumer `settings.json` (see F1.8 Step 1).
- **M5.1 follow-up payload bump.** Slash-commands (`/catchup`, `/handoff`, `/decision`, `/decision.full`, `/new-adr`, `/new-adr.full`) ship after stability audit. F1's allow-list is structured for one-line `dist/commands/` addition then.
- **`pyyaml` consumer-env audit.** Add a `pyyaml` warning to the validator's dep-check set if consumer reports `ImportError: yaml` under operator-envelope mode. Defer until first report.
- **Marketplace URL confirm.** `.claude-plugin/marketplace.json source.url` templated to `https://github.com/firaaz/cairn.git`; verify at PR-open time.
- **Auto-install postinstall hook.** If `plugin.json` supports a `postinstall:` field per the plugin reference, wire it (F1.6 Step 5). Otherwise validator runs by manual operator invocation; F2's CONSUMER.md documents.
- **CI release-tag automation.** Tag protocol `v0.x.y` is operator-driven (F1.1 Step 4). A future M5.1 workflow may run `build_dist.py`, commit to a release branch, and tag automatically. Out-of-scope for F1.
