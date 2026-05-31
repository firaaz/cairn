# Trial-D measurement scratch — MEDIUM (cairn-m7-plugin-deployment-pattern)

ASSISTANT INSTRUMENTATION ONLY. The `## Contract` -> `must-satisfy` list at the bottom
is AUTHORED BY THE OPERATOR. If the assistant fills it, metrics #1 (authoring-time) and
#2 (rubber-stamp reduction) are VOID (plan Step 2).

Source intent: .claude/skill-runs/cairn-m7-plugin-deployment-pattern/intent.md
  (completed-run record; copied below for derivation — do NOT edit the original).
Behaviors to derive from: `## Specification` S1-S6 and `## Feature-Local Invariants`
  FLI-1..7. (FLI-4 "first-party Actions only" and FLI-7 "audit check 9 is a merge gate"
  are the universal-/operator-bound-flavoured clauses the measurement specifically eyes.)

Operator procedure (do LIGHT first, then MEDIUM, then HEAVY):
  1. Start a stopwatch.
  2. In the `## Contract` block at the BOTTOM of this file, author one atomic EARS
     clause per behavior in the derivation source. Split, or tag with one of
     {universal-set, regression-meta, operator-bound, trivial-existence}, any clause
     that isn't a single tool-call or single file-check. Tagging is the one-line
     escape from a flagged clause.
  3. Stop the stopwatch. Record elapsed + your felt-prose-baseline estimate -> metric #1.
  4. Note any clause where deciding "split vs tag vs leave atomic" surfaced a call you
     would otherwise have waved through -> metric #2 (binary per intent).
  5. Say "<size> ready". The assistant runs
     `uv run python checks/atomicity_guard.py <this-file>` and proposes false-positive
     labels for the flagged clauses; you adjudicate -> metric #3.

EARS shapes (write each must-satisfy item as ONE of these):
  Ubiquitous : the <system> shall <response>
  Event      : when <trigger>, the <system> shall <response>
  State      : while <state>, the <system> shall <response>
  Option     : where <feature>, the <system> shall <response>
  Unwanted   : if <condition>, then the <system> shall <response>

Atomicity (ADR D3): a clause is atomic iff verifiable by a single tool call or single
file check. Untagged clauses must pass atomicity. A non-atomic clause must be split into
atomic clauses OR carry one tag (mapping form {clause: "<EARS>", except: "<tag>: <decl>"}):
  universal-set     - quantifies over a set; declaration enumerates the set
  regression-meta   - "unchanged"/"no regression"; declaration names the baseline
  operator-bound    - needs human action/judgement; declaration names the operator step
  trivial-existence - a file/output simply exists; NO declaration required
The first three tags require a non-empty declaration; an unknown tag always fails.

----- derivation source (verbatim copy of the read-only original) -----


## What

Operationalize ADR `m5-plugin-deployment-pattern` D1–D9. Three threads land together:
- **S (schema rewrite + lint).** Rewrite `.claude-plugin/marketplace.json` to the documented `source.source:"github"` + `repo:"firaaz/cairn"` + `ref:"release"` shape and ship `tests/unit/test_marketplace_schema.py` as the per-PR shape lint.
- **W (release workflow).** Ship `.github/workflows/release-publish.yml` — `workflow_dispatch`-triggered (with secondary `push: tags: ['v*']`), builds `dist/` via `scripts/build_dist.py`, cross-checks input `version` against built `plugin.json:version`, force-with-leases the `release` branch tree to match `/tmp/dist-out`, and conditionally tags `v0.x.y`.
- **V (verification).** Run F3 audit check 9 (manual end-to-end install) against the chosen-and-shipped manifest as a NON-SKIPPABLE acceptance gate.

## Why

F3 closed structurally but its audit check 9 is PENDING because (a) the `dist/` payload was never committed to a pushed ref and (b) today's `marketplace.json` carries the schema-invalid `"type": "git"` discriminator. M5+M6 is consumer-broken: `/plugin install cairn@cairn-marketplace` resolves no payload. After M7, the literal commands at `README.md:19` / `CONSUMER.md:14` work end-to-end against a fresh consumer; F3 transitions PENDING → PASS; M5+M6 closes; INV-012 acquires its first machine-checked binding.

## Boundary

In: `.claude-plugin/marketplace.json`, `.github/workflows/release-publish.yml`, `tests/unit/test_marketplace_schema.py`, `tests/unit/test_release_workflow.py`, dist-gate.yml extension to run the new tests, optional `.gitignore`/`CHANGELOG.md`/`docs/roadmap.md`/`docs/operational-reference.md` edits per envelope. Out: README/CONSUMER/upgrading-from-symlink prose (D2 keeps consumer commands literal-unchanged); ADR amendments (append-only; M5 prose untouched); branch protection on `release`; `claude plugin validate` integration; Windsurf-port manifest; lessons.md L-022 update; handoff.md refresh.

## Specification

### S1 — `.claude-plugin/marketplace.json` literal shape (ADR D2 + D3)

The plugin entry's `source` block MUST be exactly:

```json
{
  "source": "github",
  "repo": "firaaz/cairn",
  "ref": "release"
}
```

The plugin entry MUST NOT carry a top-level `version` field (ADR D3 + Phase 0.5 Evidence 9 — `plugin.json:version` wins silently). The legacy `"type": "git"` field MUST be absent from `source`. Surrounding manifest carries `name: "cairn-marketplace"`, `owner.name: "firaaz"`, `plugins[0].name: "cairn"`, `plugins[0].description: "TDD-by-construction dispatch skill, hooks, and protocols for Claude Code."` (verbatim per plan §Phase 3 Section S).

### S2 — `tests/unit/test_marketplace_schema.py` literal assertions (ADR D7)

Five assertions, each citing the originating ADR clause:

1. `plugins[0].source.source == "github"` (ADR D2).
2. `plugins[0].source.repo == "firaaz/cairn"` (ADR D2).
3. `plugins[0].source.ref == "release"` (ADR D2 + D7; defends Phase 1 S7 — D2 stability stance violated by ref-omission).
4. `"version" not in plugins[0]` (ADR D3; defends silent-mask trap).
5. `"type" not in plugins[0].source` (regression — broken `type: git` shape must not return).

### S3 — `.github/workflows/release-publish.yml` shape (ADR D5/D6/D8)

Triggers: `workflow_dispatch` (primary) with required `version` (semver string) and optional `source_ref` (default `dev`) inputs; secondary `push: tags: ['v*']` for `claude plugin tag` compat. `permissions: contents: write` only — no `pull-requests:` (A wins on supply-chain surface; no auto-PR machinery). Steps, in order:

1. `actions/checkout@v4` of the source ref.
2. `astral-sh/setup-uv@v3`.
3. `uv run python scripts/build_dist.py --repo-root . --dist-root /tmp/dist-out`.
4. Read `/tmp/dist-out/.claude-plugin/plugin.json:version`; assert it equals `inputs.version`. On mismatch, the workflow MUST exit non-zero before any push (D5 cross-check).
5. Detect `release` branch existence via `git ls-remote --exit-code --heads origin release`; on first run, fall back to `git worktree add --orphan -b release` (M7.3 defense).
6. Materialize `release` via `git worktree add`, wipe its tree, `cp -a /tmp/dist-out/. <worktree>/`, `git commit -m "chore: release v${VERSION} from ${SOURCE_SHA::7}"`, `git push --force-with-lease origin release`. The literal commit prefix `chore:` MUST be present (S5 / INV-001 binding via `_FALLBACK_REGISTRY`).
7. Conditional `if: github.event_name == 'workflow_dispatch'`: idempotent create-or-update of `v${VERSION}` tag and `git push --tags` (D8).

Only first-party Actions (`actions/checkout@v4`, `astral-sh/setup-uv@v3`, optionally `actions/github-script@v7`) — no third-party Actions per Phase 3 adversarial finding.

### S4 — `tests/unit/test_release_workflow.py` literal assertions

1. `Path(".github/workflows/release-publish.yml").exists()`.
2. Parsed YAML's `on` mapping contains `workflow_dispatch`, and `on.workflow_dispatch.inputs` contains `version`.
3. File text contains `--force-with-lease` AND does NOT contain the bare token `git push --force ` (trailing space) or `git push --force\n` — the `--force-with-lease` literal must not produce a false positive (D6).
4. File text contains `chore: release` (literal commit-message prefix; INV-001 / S5 binding).

### S5 — dist-gate.yml extension

`.github/workflows/dist-gate.yml`'s pytest step is extended to run `tests/unit/test_marketplace_schema.py` and `tests/unit/test_release_workflow.py` alongside `tests/unit/test_build_dist.py`. No other dist-gate.yml semantics change.

### S6 — Optional artefacts (Section S' from plan)

`dist/` added to `.gitignore` on `dev`. CHANGELOG.md gains an "M7 — plugin deployment" note explaining the `release` branch is CI-only / force-with-leased / do-not-push-manually.

## Verification

Nine audit checks. Checks 1–8 are automated (Phase 4 runs them); check 9 is manual and **NON-SKIPPABLE** (ADR D9).

1. `tests/unit/test_marketplace_schema.py` passes (the new lint).
2. `tests/unit/test_release_workflow.py` passes (the new workflow-shape lint).
3. Existing `tests/unit/test_build_dist.py` still passes (regression).
4. `dist-gate.yml` runs clean on a PR-time invocation against the M7 branch.
5. `.claude-plugin/marketplace.json` parses as valid JSON; field-by-field grep confirms ADR D2 shape (S1 above).
6. `.github/workflows/release-publish.yml` parses as valid YAML; field-by-field grep confirms ADR D5/D6/D8 shape (S3 above).
7. `scripts/validate_architecture.py` runs without NEW failures vs F3 baseline (the pre-existing INV-002 handoff token-budget breach is the only acceptable carry-over). INV-012 Check E warning resolves once `tests/unit/test_marketplace_schema.py` is referenced as the invariant `test-ref` (recommended bonus per plan §Phase 4 Bonus).
8. Full `uv run pytest` suite is GREEN (matching F3 baseline plus the 5+4 new tests).
9. **Audit check 9 — manual end-to-end install (NON-SKIPPABLE).** Verifying operator runs the release-publish workflow once via the GitHub Actions UI (`version: 0.1.0, source_ref: dev`); confirms workflow green, `release` branch present on origin with dist-output tree at root, `v0.1.0` tag pushed; opens a fresh non-cairn project in Claude Code; runs the literal commands `/plugin marketplace add https://github.com/firaaz/cairn` then `/plugin install cairn@cairn-marketplace`; confirms install completes (no "directory not found", no schema-parse error); runs `uv run python scripts/validate_plugin_install.py` (or `${CLAUDE_PLUGIN_ROOT}/postinstall_validate.py`) and confirms green exit; runs a trivial `cairn-tdd-feature` dispatch on a throwaway plan to confirm hooks fire under the plugin-cache layout. Records VERDICT: PASS in Phase 4 sweep-notes verbatim per plan §Phase 4 Section V. **Feature is not merge-final until check 9 records green; failure → RAISE_ISSUE.**

## Risk Surface

Inherits ADR `m5-plugin-deployment-pattern`'s S1–S10 Risk Register and adds plan §Risk Register M7.1–M7.5.

- **S1 (schema-parse failure, CRITICAL).** Defended by ADR D2 + D7 (lint) + D9 (audit check 9). Residual: low; `claude plugin validate` integration deferred until CLI is CI-stable.
- **S2 (default-branch trap, CRITICAL, A-specific).** Defended by D2's explicit `ref: "release"` decoupling + D4 (default branch stays `dev`) + D7 lint asserting `ref` non-empty. Residual: zero from the trap itself.
- **S5 (INV-001 commit-prefix binding, HIGH).** Workflow's `git commit` uses literal `chore:` prefix; `chore` is in `_FALLBACK_REGISTRY` at `scripts/validate_architecture.py:279`. Defended by `test_release_workflow_commit_prefix_is_chore`.
- **S7 (D2 stability stance violated by ref-omission).** Defended by `test_marketplace_source_ref_is_release` lint + D5 version cross-check.
- **S8 (schema breaking change upstream).** Accepted residual; cairn does not control Anthropic's schema. Mitigation: monitor `code.claude.com/docs/en/plugin-marketplaces` changelog.
- **S9 (maintainer dogfood disrupted).** Defended by D4 + D2 ref-decoupling. Residual: a maintainer `git checkout release` sees a different file layout (mitigated by CHANGELOG note + ADR prose).
- **M7.1 — schema rewrite breaks dist-gate.yml.** Defended by Phase 2 RED tests landing before the rewrite; Phase 3 runs dist-gate.yml locally before commit.
- **M7.2 — release-publish.yml syntax error blocks first release.** Defended by `test_release_workflow_exists` + YAML-parse assertion in Phase 2.
- **M7.3 — first force-with-lease push fails because `release` doesn't exist.** Defended by S3 step 5 (`git ls-remote --exit-code --heads origin release` → fall back to `git worktree add --orphan -b release`).
- **M7.4 — `${{ secrets.GITHUB_TOKEN }}` lacks `contents: write` on a protected `release`.** Accepted residual; M7 ships `release` unprotected per ADR's "branch-protection escalation post-launch" deferred decision.
- **M7.5 (HIGHEST-LEVERAGE RESIDUAL) — `marketplace.json` parses but Anthropic's resolver does not follow `source.source:"github"` to `ref:"release"` as the docs imply.** This is the `github`-source-decoupling claim per Phase 0.5 Evidence 11, flagged by /decision Phase 5 verifier as the highest-leverage residual. Audit check 9 is the empirical verification by construction; failure here means RAISE_ISSUE → operator → no merge.

## Feature-Local Invariants

- **FLI-1 — Schema-rewrite atomicity.** The marketplace.json rewrite must land in a single commit; a partial rewrite leaving both old `"type": "git"` and new `source.source: "github"` keys is undefined behavior and forbidden.
- **FLI-2 — Workflow-input/built-version cross-check is mandatory.** `release-publish.yml` MUST exit non-zero when `inputs.version != /tmp/dist-out/.claude-plugin/plugin.json:version`, BEFORE any `git push`. Removing this check requires an ADR amendment trail.
- **FLI-3 — `--force-with-lease` only.** Bare `git push --force` (with trailing space or newline) MUST NOT appear anywhere in `release-publish.yml`. Cairn's force-push policy applies to CI as well as humans.
- **FLI-4 — First-party Actions only.** Only `actions/*` and `astral-sh/setup-uv@v3` may appear in `uses:` directives in `release-publish.yml`. No third-party Actions (no `peter-evans/create-pull-request@v6`, no `softprops/action-gh-release`, etc.).
- **FLI-5 — `chore:` commit-prefix on release commits.** The release-sync step's commit message MUST begin with `chore: release ` to satisfy INV-001's `_FALLBACK_REGISTRY` binding (S5 mitigation).
- **FLI-6 — Marketplace plugin entry omits `version`.** Per ADR D3, the plugin entry in `marketplace.json` MUST NOT carry a top-level `version` field; `plugin.json:version` is the single source of truth.
- **FLI-7 — Audit check 9 green is a merge gate.** No merge to `dev` without a verbatim VERDICT: PASS recorded in Phase 4 sweep-notes for audit check 9 (ADR D9).

## Explicit Scope-Out

- **Branch protection on `release`.** Deferred per ADR's "branch-protection escalation post-launch" — added in a follow-up if abuse surfaces.
- **`claude plugin validate` integration in dist-gate.yml.** Recommended in ADR Risk Register but deferred — only if the CLI is stable in CI.
- **Windsurf-port manifest.** Vision commitment preserved (release branch is plain git; consumable by any agent runtime); M7 ships only the Claude Code marketplace shape.
- **Cross-cutting `lessons.md` update (L-022).** Manifest-schema-validity-as-load-bearing-prerequisite lands in lessons.md as part of the parent /decision propagation, not M7.
- **`handoff.md` refresh.** Standard session hygiene; not an M7 deliverable.
- **README / CONSUMER / upgrading-from-symlink prose.** Per ADR D2, the literal consumer commands stay UNCHANGED; zero docs churn for consumer-facing copy.
- **ADR amendments.** Append-only policy; `m5-plugin-distribution-and-symlink-retire` body prose and frontmatter are NOT modified — the new ADR's `supersedes-sections: [m5-plugin-distribution-and-symlink-retire/D3]` is the canonical pointer.
- **Default-branch change (`dev` → `release`).** Rejected in ADR Alternatives — incompatible with maintainer dogfood under D8 of the predecessor.
- **Relative-path source (`./dist`).** Rejected in ADR Alternatives — structurally incompatible with "marketplace lives on `dev`, plugin lives on `release`."

## Contract

```yaml
# OPERATOR AUTHORS must-satisfy — one atomic EARS clause per behavior in the derivation source.
# Bare string  -> atomicity-checked.
# Mapping form -> {clause: "<EARS>", except: "<tag>: <declaration>"}  (atomicity-waived).
# The assistant intentionally left this empty; filling it voids metrics #1/#2.
must-satisfy: []

# The five lists below are NOT measured (the gate checks only must-satisfy).
# Leave empty, or fill if you want a complete block.
must-not-violate: []
wrong-if: []
escalate-when: []
evidence: []
execution-scope: []
```
