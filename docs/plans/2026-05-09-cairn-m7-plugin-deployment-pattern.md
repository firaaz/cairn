---
id: cairn-m7-plugin-deployment-pattern
name: Cairn M7 — Plugin Deployment Pattern (Release Branch + Sync CI)
firmness: provisional
status: spec — for cairn-tdd-feature dispatch
date: 2026-05-09
scope: Implement m5-plugin-deployment-pattern ADR D1–D9 — schema-rewrite marketplace.json to source.source:"github" + ref:"release"; ship .github/workflows/release-publish.yml as the publish step (force-with-lease syncs dist contents to release branch HEAD on workflow_dispatch with version cross-check); ship tests/unit/test_marketplace_schema.py as the schema-shape lint; close F3 audit check 9 (PENDING) by running a real /plugin install round-trip before merge.
invariants-touched:
  - INV-012
inputs:
  - docs/adr/m5-plugin-deployment-pattern.md
  - docs/adr/m5-plugin-distribution-and-symlink-retire.md
  - docs/ARCHITECTURE.md
  - .claude/skill-runs/plugin-deployment-pattern/phase-0-constraints.md
  - .claude/skill-runs/plugin-deployment-pattern/phase-0.5-journey.md
  - .claude/skill-runs/plugin-deployment-pattern/phase-1-pre-mortem.md
  - .claude/skill-runs/plugin-deployment-pattern/phase-3-adversarial.md
  - .claude/skill-runs/plugin-deployment-pattern/phase-5-independent-verification.md
  - .claude/skill-runs/cairn-m6-f3-migration-and-symlink-retire/integration/sweep-notes.md
envelope:
  - '^docs/plans/2026-05-09-cairn-m7-plugin-deployment-pattern\.md$'
  - '^\.claude-plugin/marketplace\.json$'
  - '^\.github/workflows/release-publish\.yml$'
  - '^tests/unit/test_marketplace_schema\.py$'
  - '^\.gitignore$'
  - '^CHANGELOG\.md$'
  - '^docs/roadmap\.md$'
  - '^docs/operational-reference\.md$'
---

# Cairn M7 — Plugin Deployment Pattern (Release Branch + Sync CI)

> **For agentic workers:** REQUIRED SUB-SKILL: `cairn-tdd-feature` is the dispatch shell; this plan is its input. The decision was made via `/decision` 2026-05-09 (full A/B/C/D enumeration, operator-selected A, Phase 5 independent verification convergent at HIGH confidence). The committed ADR is `docs/adr/m5-plugin-deployment-pattern.md` — read it first; this plan operationalizes its D1–D9 commitments. Within-feature parallel subagents are permitted; Section S (schema rewrite + lint) and Section W (workflow) are independent and may run in parallel agents during Phase 3.

**Goal.** Close the deployment gap surfaced at F3 audit check 9 (PENDING). After M7 lands, a fresh consumer running the literal commands `/plugin marketplace add https://github.com/firaaz/cairn` + `/plugin install cairn@cairn-marketplace` resolves the marketplace at `dev`-tip, follows `source.source: "github"` + `ref: "release"` to the `release` branch, and gets a working install. M5+M6 milestone closes structurally.

**Architecture.** Three threads. **Thread S (schema rewrite + lint)** edits `.claude-plugin/marketplace.json` to the documented `source.source: "github"` shape per ADR D2, and ships `tests/unit/test_marketplace_schema.py` per ADR D7 as the schema-shape lint that gates every PR via `dist-gate.yml`. **Thread W (release workflow)** ships `.github/workflows/release-publish.yml` per ADR D5/D6 — `workflow_dispatch`-triggered, builds `dist/` via `scripts/build_dist.py`, cross-checks the input version against the built `plugin.json:version`, force-with-leases the `release` branch tree to match `/tmp/dist-out`, optionally tags `v0.x.y`. **Thread V (verification)** runs F3 audit check 9 against the chosen-and-shipped manifest as the acceptance criterion per ADR D9 — the feature is not merge-final until check 9 records green.

**Tech Stack.** YAML for the GitHub Actions workflow. Python 3.11 + pytest for the schema lint. Bash within the workflow's release-sync step (`git worktree add`, `cp -a`, `git commit`, `git push --force-with-lease`). No new Python dependencies; lint uses stdlib `json` + pytest. CI uses first-party actions only (`actions/checkout@v4`, `astral-sh/setup-uv@v3`, `actions/github-script@v7` if needed for output) — no third-party Action dependencies per the Phase 3 adversarial finding that A wins on supply-chain surface vs Approach D's `peter-evans/create-pull-request@v6`.

---

## Self-review summary

This plan was self-reviewed at authoring against the m5-plugin-deployment-pattern ADR's D-commitments:

- **D1 — Long-lived `release` branch with shape-(i).** Thread W's release-sync step uses `git worktree add` to materialize a fresh `release`-checkout, wipes its tree, and `cp -a /tmp/dist-out/. /tmp/release-worktree/` to make the release-branch HEAD's working tree IDENTICAL to the dist-output. No `dist/` subdirectory on `release`; the build output's contents land at branch root. `git ls-tree release` after a release shows exactly what consumers get.
- **D2 — `source.source: "github"` + `ref: "release"`.** Thread S's marketplace.json rewrite uses the literal field shape committed in the ADR. Thread S's lint asserts these exact field/value pairs.
- **D3 — `dist/.claude-plugin/plugin.json:version` is the canonical update signal.** Thread W's CI step extracts `plugin.json:version` from the built tree (`/tmp/dist-out/.claude-plugin/plugin.json`) and asserts it equals the workflow's `version` input. If they diverge (maintainer typed `0.2.0` but plugin-template still says `0.1.0`), the workflow fails before any push. Thread S's lint asserts marketplace.json's plugin entry does NOT carry a `version` field (per ADR D3 + Phase-0.5 Evidence 9 — silent-mask trap).
- **D4 — Default branch stays `dev`.** Thread W never invokes anything that mutates the default branch; Thread S never edits `dev`'s file layout (only marketplace.json's content is changed). The feature explicitly does NOT change GitHub's `default_branch` setting.
- **D5 — `workflow_dispatch` trigger with version cross-check.** Thread W's workflow declares `workflow_dispatch` as primary (with `version` and optional `source_ref` inputs); secondary `push: tags: ['v*']` is included for `claude plugin tag` compatibility. The version cross-check happens between the workflow's input and the built `dist/.claude-plugin/plugin.json:version`.
- **D6 — Force-with-lease only.** The workflow's release-sync step uses `git push --force-with-lease origin release` — never `--force`. Cairn's force-push policy is honored.
- **D7 — Schema-shape lint.** Thread S ships `tests/unit/test_marketplace_schema.py`. The test gates via `dist-gate.yml`'s `pytest tests/unit/test_build_dist.py` step — extend dist-gate.yml to also run the new test. Section S Phase 2 names the literal assertions.
- **D8 — Optional release-tagging.** Thread W's workflow includes an `if: github.event_name == 'workflow_dispatch'` step that creates and pushes `v0.x.y` tag. The tag step is conditional and idempotent (assertion: tag-or-create).
- **D9 — F3 audit check 9 acceptance gate.** Thread V is non-skippable: Phase 4 sweep notes record the manual end-to-end install verification as a PASS — feature is not merge-final until this records green. The runbook (Phase 4 Section V below) names the literal commands the verifying operator types.

**Cross-feature dependencies:**

- **F1 (packaging) is required.** M7 reuses F1's `scripts/build_dist.py` + `dist-gate.yml` + `scripts/postinstall_validate.py` + `.claude-plugin/plugin-template.json` directly. If any of those are missing or regressed, **abort and surface to operator** — M7 is structurally blocked on F1.
- **F3 (migration + symlink retire) was structurally complete but check-9 PENDING.** M7's success transitions F3 from PENDING → PASS. The F3 sweep-notes (`.claude/skill-runs/cairn-m6-f3-migration-and-symlink-retire/integration/sweep-notes.md`) line "merge-eligible but not merge-final until check 9" closes when M7 ships.
- **No co-landed ADR amendment.** The ADR was committed with `supersedes-sections: [m5-plugin-distribution-and-symlink-retire/D3]`. Per cairn's append-only ADR policy, M5's body prose and frontmatter are NOT modified; the new ADR is the canonical pointer. M7 does not need to touch any ADR file.

---

## Phase-by-phase scope

### Phase 1 — Intent (Reader)

The Reader produces `intent.md` — the contract Phase 2 will write tests against. Intent must include:

**Specification** — what the feature delivers in literal-text form:
- The new `marketplace.json` field shape (literal JSON).
- The new workflow's trigger, jobs, steps, secrets (verbatim YAML acceptable, or a structured spec).
- The schema-shape lint's literal assertions.
- The release-sync mechanism (force-with-lease semantics; `git worktree add` step).

**Verification surface** — the audit checks Phase 4 will run:
1. `tests/unit/test_marketplace_schema.py` passes (the new lint).
2. `dist-gate.yml` (existing) still passes after lint integration.
3. `marketplace.json` content matches the documented schema shape per ADR D2.
4. `.github/workflows/release-publish.yml` exists and parses as valid YAML.
5. Workflow's commit-message format matches a registered INV-001 prefix (asserted by a unit test).
6. **Audit check 9 (manual end-to-end install verification)** — a fresh consumer in a non-cairn project runs:
   ```
   /plugin marketplace add https://github.com/firaaz/cairn
   /plugin install cairn@cairn-marketplace
   uv run python scripts/validate_plugin_install.py
   ```
   and reports: install completes; validator green; hooks fire on a trivial dispatch. **This check is NON-SKIPPABLE — feature is not merge-final until it records green.**

**Risk Surface** — anticipate how each scenario from the ADR's Risk Register manifests in M7 specifically. Each risk gets a defense or accepted-residual classification.

**Feature-Local Invariants (FLI)** — schema-rewrite atomicity, workflow-input/built-version cross-check, force-with-lease (not force), no third-party Actions in workflow, etc.

The Reader MUST cite `m5-plugin-deployment-pattern` D1–D9 in `adrs-referenced` so Phase 1's structural-immutability gate (`phase-lock-and-role-declaration` D3) verifies the ADR exists before Phase 2 dispatches.

### Phase 2 — Failing tests (Skeptic)

The Skeptic writes failing tests for every specification element in Phase 1's intent.md. Tests live under `tests/unit/`. Two test files:

**`tests/unit/test_marketplace_schema.py`** (new) — schema-shape lint. Failing assertions per ADR D7:

```python
def test_marketplace_source_source_is_github():
    """ADR m5-plugin-deployment-pattern/D2: source.source must be 'github'."""
    manifest = json.loads(Path(".claude-plugin/marketplace.json").read_text())
    assert manifest["plugins"][0]["source"]["source"] == "github"

def test_marketplace_source_repo_is_firaaz_cairn():
    """ADR m5-plugin-deployment-pattern/D2: source.repo == 'firaaz/cairn'."""
    manifest = json.loads(Path(".claude-plugin/marketplace.json").read_text())
    assert manifest["plugins"][0]["source"]["repo"] == "firaaz/cairn"

def test_marketplace_source_ref_is_release():
    """ADR m5-plugin-deployment-pattern/D2 + D7: source.ref must equal 'release'.
    Defends Phase 1 S7 (D2 stability stance violated by ref-omission)."""
    manifest = json.loads(Path(".claude-plugin/marketplace.json").read_text())
    assert manifest["plugins"][0]["source"]["ref"] == "release"

def test_marketplace_plugin_entry_omits_version():
    """ADR m5-plugin-deployment-pattern/D3: marketplace entry must NOT carry version
    (silent-mask trap per Phase 0.5 Evidence 9 — plugin.json wins silently)."""
    manifest = json.loads(Path(".claude-plugin/marketplace.json").read_text())
    assert "version" not in manifest["plugins"][0]

def test_marketplace_no_legacy_type_field():
    """Regression: today's broken 'type: git' shape must not return."""
    manifest = json.loads(Path(".claude-plugin/marketplace.json").read_text())
    assert "type" not in manifest["plugins"][0]["source"]
```

**`tests/unit/test_release_workflow.py`** (new) — workflow-shape lint. Failing assertions:

```python
def test_release_workflow_exists():
    assert Path(".github/workflows/release-publish.yml").exists()

def test_release_workflow_has_workflow_dispatch_trigger():
    """ADR D5: workflow_dispatch is the primary trigger."""
    wf = yaml.safe_load(Path(".github/workflows/release-publish.yml").read_text())
    assert "workflow_dispatch" in wf["on"]
    assert "version" in wf["on"]["workflow_dispatch"]["inputs"]

def test_release_workflow_uses_force_with_lease():
    """ADR D6: only --force-with-lease is permitted, never --force."""
    text = Path(".github/workflows/release-publish.yml").read_text()
    assert "--force-with-lease" in text
    # Match the exact `git push --force ` token (with trailing space) so the
    # `--force-with-lease` literal does not produce a false positive.
    assert "git push --force " not in text and "git push --force\n" not in text

def test_release_workflow_commit_prefix_is_chore():
    """ADR D5 + Phase 1 S5: workflow's git commit must use `chore:` (in INV-001 _FALLBACK_REGISTRY)."""
    text = Path(".github/workflows/release-publish.yml").read_text()
    assert "chore: release" in text  # the literal commit message format
```

Phase 2 commits these test files; all assertions RED. The Skeptic does NOT write the implementation — only the failing tests.

### Phase 3 — Implementation (Builder)

Two parallel agent dispatches permitted (Sections S and W are independent):

**Section S — Schema rewrite + lint.** Replace `.claude-plugin/marketplace.json` body with the ADR D2 shape:

```json
{
  "name": "cairn-marketplace",
  "owner": { "name": "firaaz" },
  "plugins": [
    {
      "name": "cairn",
      "description": "TDD-by-construction dispatch skill, hooks, and protocols for Claude Code.",
      "source": {
        "source": "github",
        "repo": "firaaz/cairn",
        "ref": "release"
      }
    }
  ]
}
```

Extend `.github/workflows/dist-gate.yml` to run `pytest tests/unit/test_marketplace_schema.py tests/unit/test_release_workflow.py` alongside `tests/unit/test_build_dist.py`.

**Section W — Release workflow.** Create `.github/workflows/release-publish.yml` per the ADR D5/D6 spec. Verbatim shape from the ADR's example (with the workflow-input version cross-check step and the force-with-lease release-sync step). The workflow must:

1. Trigger on `workflow_dispatch` (primary) with `version` (required) and `source_ref` (default `dev`) inputs; secondary `push: tags: ['v*']` for `claude plugin tag` compat.
2. Use `actions/checkout@v4` + `astral-sh/setup-uv@v3` only — first-party Actions per Phase 3 adversarial finding.
3. Build dist via `uv run python scripts/build_dist.py --repo-root . --dist-root /tmp/dist-out`.
4. Cross-check `inputs.version` against `dist/.claude-plugin/plugin.json:version`; fail before push if they differ.
5. `git worktree add` to materialize `release` (or create-orphan if first run); wipe its tree; `cp -a /tmp/dist-out/. /tmp/release-worktree/`; `git commit -m "chore: release v${VERSION} from ${SOURCE_SHA::7}"`; `git push --force-with-lease origin release`.
6. Conditional `if: github.event_name == 'workflow_dispatch'` step that creates and pushes `v${VERSION}` tag idempotently.
7. `permissions: contents: write` (only) — no `pull-requests:` (no auto-PR machinery; A-strongest doesn't need one).

**Section S' — Optional but recommended.** Add `dist/` to `.gitignore` on `dev`. Add a CHANGELOG.md note under "M7 — plugin deployment" explaining the `release` branch's character (CI-only; force-with-leased on each release; do not push manually). The CHANGELOG note is the canonical reference for any future contributor seeing `release` in `git branch -a`.

Phase 3 commits the implementation; all Phase 2 RED tests now GREEN.

### Phase 4 — Audit (Auditor)

The Auditor runs all eight automated audit checks from intent §Verification, plus dispatches Section V (manual end-to-end install verification — audit check 9) per ADR D9.

**Section V — Manual end-to-end verification (audit check 9).** Per ADR D9, this is a NON-SKIPPABLE acceptance criterion. The verifying operator (lead or designated reviewer):

1. Pushes the M7 branch to `origin` (or relies on dev-tip after Phase 3 merges).
2. Runs the release-publish workflow once via GitHub Actions UI (`Actions → release-publish → Run workflow → version: 0.1.0, source_ref: dev`). Confirms:
   - Workflow completes green.
   - `release` branch exists on `origin` and carries the dist-output tree at root.
   - `v0.1.0` tag exists.
3. Opens a fresh project (any non-cairn directory) in Claude Code.
4. Verifies system prereqs: `jq --version`, `ruff --version` (already documented in CONSUMER.md/CLAUDE.md). NO `npm` required (Phase 1 S3 not applicable to A).
5. Runs the literal install commands:
   ```
   /plugin marketplace add https://github.com/firaaz/cairn
   /plugin install cairn@cairn-marketplace
   ```
6. Confirms install completes without "directory not found" or schema-parse errors.
7. Runs `uv run python scripts/validate_plugin_install.py` (or the equivalent `${CLAUDE_PLUGIN_ROOT}/postinstall_validate.py`). Confirms green exit.
8. Runs a trivial `cairn-tdd-feature` dispatch on a throwaway plan (e.g., a one-line "hello world" feature) to confirm hooks fire and skills register correctly under the plugin-cache layout.
9. Records the audit-check-9 result in Phase 4 sweep-notes verbatim:

```markdown
**Audit check 9 (manual end-to-end install).**
- Workflow run: <link to GitHub Actions run>
- Release branch SHA: <40-char>
- Tag: v0.1.0
- Fresh project: <path or description>
- /plugin marketplace add output: <success message>
- /plugin install output: <success message>
- validate_plugin_install.py: clean exit, no warnings
- Trivial dispatch: 4 phase commits landed; .claude/envelope-grants.log lands consumer-side; hooks fired
- VERDICT: PASS
```

If audit check 9 fails, the Auditor RAISE_ISSUE per the dispatch protocol — the feature is not merge-final.

**Other audit checks** (1–8 per intent.md):
1. `tests/unit/test_marketplace_schema.py` passes (new).
2. `tests/unit/test_release_workflow.py` passes (new).
3. Existing `tests/unit/test_build_dist.py` still passes (regression).
4. `dist-gate.yml` runs clean on a PR-time invocation (CI must be green on the M7 branch).
5. `marketplace.json` parses as valid JSON; field-by-field grep confirms ADR D2 shape.
6. `.github/workflows/release-publish.yml` parses as valid YAML; field-by-field grep confirms ADR D5/D6 shape.
7. `validate_architecture.py` runs without NEW failures vs baseline (pre-existing INV-002 handoff token-budget breach is the only known failure; M7 must not introduce others; INV-012's Check E warning resolves once `tests/unit/test_marketplace_schema.py` is referenced as the invariant-check `test-ref`).
8. The full pytest suite passes (matching the F3-baseline; M7's 5+4 new tests should add to GREEN count, no new RED).

**Bonus — INV-012 invariant-check binding.** Phase 4 may extend `docs/ARCHITECTURE.md`'s INV-012 to add an `invariant-check` block referencing `tests/unit/test_marketplace_schema.py::test_marketplace_source_ref_is_release` (or similar). This converts the Check E warning to a proper machine-checked invariant. Recommended; not strictly required for merge.

---

## Risk Register inheritance

The ADR's Risk Register (S1–S10 with defenses) inherits to M7. M7's specific risk additions:

| # | Risk | M7 defense |
|---|---|---|
| M7.1 | Schema rewrite breaks existing dist-gate.yml CI | Phase 2 RED tests gate the rewrite; Phase 3 dispatcher runs `dist-gate.yml` locally before commit. |
| M7.2 | release-publish.yml syntax error blocks first release | Phase 2 includes `test_release_workflow_exists` + YAML-parse assertion. Phase 3 lints the YAML pre-commit. |
| M7.3 | First force-with-lease push fails because `release` branch doesn't exist | Workflow's release-sync step uses `git ls-remote --exit-code --heads origin release` to detect first-run, falls back to `git worktree add --orphan -b release`. |
| M7.4 | Workflow's `${{ secrets.GITHUB_TOKEN }}` lacks `contents: write` on default branch protection | M7 ships unprotected `release` initially per ADR's "branch-protection escalation post-launch" deferred decision. |
| M7.5 | Audit check 9 reveals an unanticipated failure mode (e.g., Anthropic's resolver behaves differently than the docs imply) | RAISE_ISSUE escalates to operator; M7 not merge-final until resolved. The /decision Phase 5 verifier flagged this as the highest-leverage residual ("git-subdir-decoupling claim" — the analog for A is the `github`-source-decoupling claim per Phase 0.5 Evidence 11; F3 audit check 9 IS the empirical verification per Phase 3 Attack 1). |

---

## Out of scope (explicit)

- **Branch protection on `release`.** Deferred per ADR's "branch-protection escalation post-launch" — added in a follow-up if abuse surfaces.
- **`claude plugin validate` integration in dist-gate.yml.** Recommended in ADR Risk Register but deferred — only if the CLI is stable in CI environments.
- **Windsurf-port story.** Vision commitment #1 is preserved (release branch is plain git; consumable by any agent runtime), but M7 ships only the Claude Code marketplace shape. Windsurf-specific manifest is a future feature.
- **Cross-cutting lessons.md update.** L-022 candidate (manifest-schema validity as load-bearing prerequisite) lands in lessons.md as part of the parent /decision propagation, not M7.
- **Handoff.md refresh.** Standard session hygiene; not an M7 deliverable.

---

## Operator-facing acceptance summary

When M7 closes:
- `/plugin marketplace add https://github.com/firaaz/cairn` + `/plugin install cairn@cairn-marketplace` works end-to-end against a fresh consumer project.
- F3 audit check 9 transitions PENDING → PASS in the M7 sweep-notes.
- F3 sweep-notes references the M7 commit chain (or vice versa) so the cross-feature dependency is explicit.
- M5+M6 milestone closes structurally.

End of M7 plan.
