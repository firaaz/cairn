# Phase 2 — Approach A: release branch with `dist/` committed + sync CI

Author: Phase-2 sub-agent A (Plan), 2026-05-09. Persisted by lead.

**Charter.** Cairn keeps `dev` as default branch and `dist/` git-ignored on `dev`. A long-lived `release` branch carries the curated `dist/` payload. CI builds `dist/` on a release trigger and force-with-leases the `release` branch tree to match. `marketplace.json` lives on `dev` (so consumers' `/plugin marketplace add https://github.com/firaaz/cairn` works without an `@ref` qualifier) and uses `source.source: "github"` with explicit `ref: "release"` to decouple plugin-source resolution from the marketplace clone's ref.

## Synopsis

Approach A pins the cairn plugin payload to a long-lived `release` branch on the same repository, keeps `dev` as the maintainer dogfood branch (`dist/` git-ignored there), and uses `source.source: "github"` + `ref: "release"` in `marketplace.json` so the plugin-source resolution is decoupled from whatever ref the consumer's marketplace clone landed at. A new GitHub Actions workflow (manually triggered or tag-driven) builds `dist/` from `dev`-tip via `scripts/build_dist.py`, force-syncs the `release` branch tree to that build, and bumps `dist/.claude-plugin/plugin.json` `version` in the same commit. One push, one consumer-visible signal.

## Concrete shape

### Marketplace manifest (lives on `dev`, all branches that consumers might add)

`.claude-plugin/marketplace.json` after rewrite:

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

Key fields (each cited against the verbatim Phase-0.5 docs evidence):

- `source.source: "github"` is one of the four documented values (`code.claude.com/docs/en/plugin-marketplaces:231-238`, Phase-0.5 Evidence 1). It replaces today's invalid `"type": "git"` (`.claude-plugin/marketplace.json:11`, Phase-0 constraint 5).
- `repo: "firaaz/cairn"` is the `owner/repo` shorthand documented for the `github` source object (`code.claude.com/docs/en/plugin-marketplaces:280-288`, Phase-0 constraint 12).
- `ref: "release"` is the long-lived release branch (Phase-0.5 Evidence 3 names branch-or-tag as accepted values; defaulting to default branch is the failure mode S2 disarms).
- No `path` field — for `github` source, the entire repo at the resolved ref is the plugin root (Phase-0 constraint 13). The `release` branch is structured to be the plugin root directly; see "release-branch tree shape" below.
- No `sha` — `ref: "release"` follows the moving HEAD of the release branch, but updates are gated by `version` in `plugin.json` (Phase-0.5 Evidence 8). Consumers who want SHA pinning can override `ref` with `sha` themselves.

### `dist/.claude-plugin/plugin.json` (the version authority)

```json
{
  "name": "cairn",
  "version": "0.1.0",
  "description": "Cairn — TDD-by-construction dispatch for Claude Code.",
  "homepage": "https://github.com/firaaz/cairn"
}
```

CI bumps `version` per release per cairn-D2 (`m5-plugin-distribution-and-symlink-retire/D2`). Per Phase-0.5 Evidence 9 (`code.claude.com/docs/en/plugin-marketplaces:715-718`), `plugin.json` `version` always wins silently over a marketplace entry's `version`; therefore Approach A keeps `version` in `plugin.json` only and omits it from the marketplace entry to avoid the silent-mask trap. The version-resolution chain (Phase-0.5 Evidence 7, `code.claude.com/docs/en/plugins-reference:993-998`) collapses to:

1. `dist/.claude-plugin/plugin.json` `version` → `"0.x.y"` (always wins).

That is the consumer-visible update signal. Cairn-D2 is satisfied with one bump in one file in one commit.

### Release-branch tree shape (the load-bearing decision)

**Shape (i): `release` HEAD tree IS the plugin root.** The `release` branch's working tree contents are the contents of `dist/` after build. So the layout at `release` HEAD is:

```
release/
├── .claude-plugin/
│   └── plugin.json          (the version-bearing manifest)
├── agents/
│   ├── phase-1-tdd.md
│   ├── phase-2-tdd.md
│   ├── phase-3-tdd.md
│   ├── phase-4-tdd.md
│   ├── triager-tdd.md
│   └── role-topology.yaml
├── checks/
│   ├── role_guard.py        (with D5 anchoring fix)
│   ├── reality-check.sh
│   └── reversibility-guard.sh
├── hooks/
│   └── hooks.json
├── skills/
│   └── cairn-tdd-feature/
├── templates/
│   └── handoff.md
└── postinstall_validate.py
```

This shape is forced by Phase-0 constraint 13: for `github` source, the entire repo at the resolved ref is the plugin root. The release branch carries no `dist/` subdirectory; the `dist/` build output IS the branch tree.

**Shape (ii) (rejected):** keep `release` as a parallel layout where the plugin payload lives under `dist/` and the rest of the branch is empty. Rejected: requires a `git-subdir` source instead of `github`, which is an extra schema-shape change. Shape (i) is the simplest manifest fit. (Note: this rejection is what produces convergence with Approach D — see Phase 2C.)

This means the `release` branch has a substantively different file layout from `dev`. Force-with-lease is mandatory each release because the build is deterministic (replace, don't merge).

### GitHub Actions workflow — `release-publish.yml`

New file `.github/workflows/release-publish.yml`. Triggered by `workflow_dispatch` (manual button) plus optionally by `push` of tags matching `v*`.

```yaml
name: release-publish

on:
  workflow_dispatch:
    inputs:
      version:
        description: "Version to publish (e.g. 0.2.0). Must match dist/.claude-plugin/plugin.json once bumped."
        required: true
        type: string
      source_ref:
        description: "Source ref to build dist from (default: dev)."
        required: false
        default: "dev"
        type: string
  push:
    tags:
      - "v*"

concurrency:
  group: release-publish
  cancel-in-progress: false

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    permissions:
      contents: write   # required to push to release branch
    steps:
      - name: Checkout source ref
        uses: actions/checkout@v4
        with:
          ref: ${{ github.event.inputs.source_ref || github.ref }}
          fetch-depth: 0

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Sync project venv
        run: uv sync

      - name: Build dist payload
        run: uv run python scripts/build_dist.py --repo-root . --dist-root /tmp/dist-out

      - name: Run allow-list assertions
        run: uv run pytest tests/unit/test_build_dist.py -q

      - name: Determine version
        id: version
        run: |
          VERSION=$(uv run python -c "import json,sys; print(json.load(open('/tmp/dist-out/.claude-plugin/plugin.json'))['version'])")
          echo "version=${VERSION}" >> "$GITHUB_OUTPUT"

      - name: Verify version was bumped
        env:
          INPUT_VERSION: ${{ github.event.inputs.version }}
          BUILT_VERSION: ${{ steps.version.outputs.version }}
        run: |
          if [ -n "$INPUT_VERSION" ] && [ "$INPUT_VERSION" != "$BUILT_VERSION" ]; then
            echo "Input version $INPUT_VERSION does not match dist/.claude-plugin/plugin.json version $BUILT_VERSION"
            exit 1
          fi

      - name: Sync release branch
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          VERSION: ${{ steps.version.outputs.version }}
          SOURCE_SHA: ${{ github.sha }}
        run: |
          set -euo pipefail
          git config user.name  "cairn-release-bot"
          git config user.email "cairn-release-bot@users.noreply.github.com"
          mkdir -p /tmp/release-worktree
          if git ls-remote --exit-code --heads origin release >/dev/null 2>&1; then
            git fetch origin release:release
            git worktree add /tmp/release-worktree release
          else
            git worktree add --orphan -b release /tmp/release-worktree
          fi
          rm -rf /tmp/release-worktree/* /tmp/release-worktree/.[!.]* || true
          cp -a /tmp/dist-out/. /tmp/release-worktree/
          cd /tmp/release-worktree
          git add -A
          git commit -m "chore: release v${VERSION} from ${SOURCE_SHA::7}"
          git push --force-with-lease origin release

      - name: Tag release commit (optional, future-D2-tag-pinning hook)
        if: github.event_name == 'workflow_dispatch'
        env:
          VERSION: ${{ steps.version.outputs.version }}
        run: |
          git -C /tmp/release-worktree tag "v${VERSION}"
          git -C /tmp/release-worktree push origin "v${VERSION}"
```

Workflow design notes:

- **Trigger**: primary trigger is `workflow_dispatch` (manual button). The maintainer types the new version explicitly into the form; CI cross-checks it matches the `dist/.claude-plugin/plugin.json` value to defend against the silent-no-bump failure mode (Phase-0.5 Evidence 8).
- **Concurrency**: `cancel-in-progress: false` because we never want to abort a release mid-push; that risks half-synced `release` branch.
- **Permissions**: `contents: write` on the default `GITHUB_TOKEN` is sufficient if `release` is not branch-protected. If the maintainer eventually protects `release`, a fine-grained PAT is needed (Phase-0.5 Gap 7). Phase 4 ADR's deployment section names this trade-off.
- **Force-with-lease**: required because each release replaces `release`'s entire tree; merge would carry stale files. `--force-with-lease` (not `--force`) honors cairn's force-push policy (`CLAUDE.md` "Force-push policy: blocked unless --force-with-lease"; Phase-0.5 boundary B10).
- **Symlink hazard defense**: `scripts/build_dist.py` already refuses to traverse `.slice-system` (Phase-0 constraint 31). The workflow runs `build_dist.py`, not a generic recursive copy, so the symlink-recursion footgun does not surface.
- **Secrets**: only the default `GITHUB_TOKEN`. No npm token, no PAT (until release-branch protection is added).

### Maintainer release flow (the verbs the maintainer types)

```
# 1. Land all dev changes destined for the release.
git checkout dev && git pull --ff-only

# 2. Bump version in the source-of-truth template.
$EDITOR .claude-plugin/plugin-template.json   # change "version": "0.x.y" to "0.x.(y+1)"
git add .claude-plugin/plugin-template.json
git commit -m "chore: bump plugin version to 0.x.(y+1)"
git push origin dev

# 3. Trigger release-publish workflow from the GitHub Actions UI:
#    Actions → release-publish → "Run workflow" → version: 0.x.(y+1), source_ref: dev
```

That is one human action (a `workflow_dispatch` button click after the version-bump commit). The CI does the rest.

### Consumer install flow (literal slash commands)

```
# README.md:19 / CONSUMER.md:14 — UNCHANGED literal:
/plugin marketplace add https://github.com/firaaz/cairn
/plugin install cairn@cairn-marketplace
```

Resolution chain (per Phase-0.5 Evidence 1, 6, 11):

1. `/plugin marketplace add https://github.com/firaaz/cairn` — clones cairn at default branch (`dev`); reads `.claude-plugin/marketplace.json`; registers the `cairn-marketplace` entry.
2. `/plugin install cairn@cairn-marketplace` — parses the plugin's `source` object: `{ source: "github", repo: "firaaz/cairn", ref: "release" }`. Claude Code clones `firaaz/cairn` at `ref: release` (separate from the marketplace clone); the entire repo's tree at `release` HEAD becomes the plugin root.
3. Reads `release/.claude-plugin/plugin.json` for the plugin name + version.
4. Copies the cloned `release` tree into `~/.claude/plugins/cache/cairn-marketplace/cairn/<version>/` (Phase-0 constraint 25, Phase-0.5 Evidence 10).
5. Reads `hooks/hooks.json`, `agents/`, `skills/`, registers per the plugin manifest contract (Phase-0 constraint 27).

Consumers do not need to know the `release` branch exists. They never type `@release`. The literal README command works.

## Constraint fit

### HARD constraints honored

- **Constraint 1** (`dist/` not in any committed ref today). After A lands and the first release runs, `dist/`'s contents (under shape-(i) layout) live on the `release` branch. Closes the gap.
- **Constraint 2** (`dist/` not in `.gitignore`). A adds `dist/` to `.gitignore` on `dev` (and only on `dev`); on `release`, the build output lives at branch root, so no `dist/` directory exists.
- **Constraint 3** (`build_dist.py` produces from allow-list). Reused unchanged.
- **Constraint 4** (today's `dist-gate.yml` validates only). A adds a sibling workflow (`release-publish.yml`).
- **Constraint 5 + 12 + 13** (current `type: git` is not documented; `source.source` is the discriminator; `path` is meaningful only for `git-subdir`). A rewrites to `source.source: "github"` + `repo` + `ref`; no `path` field.
- **Constraint 7 + 8** (D2 explicit-version-via-tags; `plugin-template.json` carries `version`). A keeps explicit-version stance.
- **Constraint 15** (`source.ref` accepts branch or tag, defaults to default branch when omitted). A makes `ref` mandatory in the manifest.
- **Constraint 20** (CI must add publish step). New `release-publish.yml`.
- **Constraint 21** (INV-001 commit-prefix). CI commits with `chore:` prefix; verified in `_FALLBACK_REGISTRY` at `scripts/validate_architecture.py:279`.
- **Constraint 22** (firm M5 ADR amendment path). A's resolution: new ADR co-landed with M5-ADR frontmatter flip OR amendment ADR with `amends-section: D3`.
- **Constraint 25–28** (cache mechanics, `${CLAUDE_PLUGIN_ROOT}`, D5 anchoring). All downstream of deployment pattern; A ships same `dist/` payload.
- **Constraint 29 + 30** (INV-011, D8 Path B, bootstrap circularity). A keeps `dev` as default; `.slice-system → .` self-symlink intact. **Load-bearing S9 defense.**
- **Constraint 32, 33** (F3 audit check 9, D9 atomic ship). After A's first release, check 9 mechanically runnable.

### Conflict resolution

- **C1 (manifest schema)**: rewrite to `source.source: "github"` with `repo` + `ref: "release"`. Mandatory regardless of approach (S1).
- **C4 (D2 explicit-version vs SHA-fallback)**: A explicitly chooses explicit-version; consumers don't track `dev`-tip.
- **C5 (firm M5 ADR vs decision-weight)**: A's chosen path: amend `m5-plugin-distribution-and-symlink-retire/D3` via co-landed amendment ADR.

C2 and C3 do not apply to A.

## Pre-mortem scenario defense

### S1 — Schema-parse failure (CRITICAL, cross-approach)

**Defense.** Rewrite `marketplace.json` to `{ "source": "github", "repo": "firaaz/cairn", "ref": "release" }`. The new shape is documented (Phase-0.5 Evidence 1). Decision cost is the manifest text-edit, zero new mechanism.

**Residual.** Add `claude plugin validate` invocation to `dist-gate.yml` to catch field-name typos pre-merge.

### S2 — Default-branch trap (CRITICAL, A-specific)

**Defense.** Use `source.source: "github"` with explicit `ref: "release"` — NOT relative-path string and NOT `git-subdir` source omitting `ref`. Per Phase-0.5 Evidence 11 (`plugin-marketplaces:259`), relative paths resolve against the marketplace clone's ref (`dev`, where `dist/` is git-ignored). The `github` source object resolves the plugin from a separate clone at the explicitly-named `ref`, decoupling plugin-source resolution from the marketplace's clone ref entirely. Phase-0 constraint 13 confirms no `path` field for `github` — the entire repo at the resolved ref IS the plugin root, forcing shape-(i).

**Residual.** Zero from the `@ref` trap itself. Consumers never type `@release`.

### S5 — INV-001 commit-prefix binding (HIGH, all approaches)

**Defense.** Workflow's `git commit` uses `chore: release v${VERSION} from ${SOURCE_SHA::7}`. `chore:` is in `_FALLBACK_REGISTRY` at line 279 with `_verify_pass_through` verifier (line 348).

**Residual.** Add a unit test asserting the workflow's commit-message format.

### S7 — D2 stability stance violated by ref-omission (HIGH, A and C)

**Defense.** `source.ref: "release"` hardcoded in the manifest. Add `tests/unit/test_marketplace_schema.py` assertion that loads `.claude-plugin/marketplace.json` and asserts `plugins[0].source.ref` exists and equals `"release"`. CI gates the assertion every PR.

### S8 — Schema breaking change upstream (MEDIUM, all approaches)

**Defense.** Unavoidable; cairn doesn't control Anthropic's schema. Mitigation: monitor changelog. Phase 4 ADR Risk Register carries this as accepted residual.

### S9 — Cairn maintainer dogfood disrupted (MEDIUM, A-specific)

**Load-bearing defense.** A explicitly does NOT change default branch. `dev` stays default; `.slice-system → .` self-symlink intact (INV-011 / D8); maintainer's `git clone` lands on `dev`. The maintainer's `release-publish.yml` interaction is purely via the GitHub Actions UI (button click) plus a one-line version-bump commit on `dev`. Neither requires the maintainer to checkout `release` locally.

**Residual.** A maintainer could `git checkout release` and find a different file layout. Mitigation: documentation in M5-amendment ADR + CHANGELOG.md note. Honest concession: a maintainer determined to push directly to `release` will overwrite the next CI sync. This is the same risk shape as any CI-managed branch (deploy-target, gh-pages); cairn inherits the standard mitigation (branch protection on `release`).

### S10 — Approach C release-branch absorption

A's release-branch shape vindicates the primitive both A and C need. A could optionally tag every release commit on `release` as `v0.x.y` (workflow's `if: workflow_dispatch` step). This gives D2-strict consumers a SHA-pinning mechanism (override `ref` → `sha`) without changing the default consumer experience.

### Cross-scenario coverage summary

| Scenario | Severity | Applies to A? | A defends? | Residual |
|---|---|---|---|---|
| S1 schema-parse | CRITICAL | yes | yes | low |
| S2 default-branch trap | CRITICAL | yes (A-specific) | yes | zero |
| S3 npm consumer dep | HIGH | no | n/a | n/a |
| S4 two-step coupling | HIGH | no (one-push) | n/a | n/a |
| S5 commit-prefix | HIGH | yes | yes | low |
| S6 detached commits | MEDIUM | no | n/a | n/a |
| S7 ref-omission | HIGH | yes | yes | low |
| S8 upstream schema | MEDIUM | yes | accepted | medium |
| S9 maintainer dogfood | MEDIUM | yes (A-specific) | yes | low |
| S10 absorption | low | n/a | favors A | n/a |

**A defends: S1, S2, S5, S7, S9. A carries: S8, accidental release-push under S9.**

## Downstream impact

### Consumer onboarding

- **README.md** UNCHANGED. Line 19's literal `/plugin marketplace add https://github.com/firaaz/cairn` works because marketplace.json carries the `github`-source-with-`ref: "release"` indirection. **Strongest A property: zero docs churn for consumer copy.**
- **CONSUMER.md** UNCHANGED at lines 13–15.
- **`docs/upgrading-from-symlink.md`** UNCHANGED at line 49.
- New M5-amendment ADR (Phase 4 deliverable, not consumer-facing).

### F3 audit check 9

After A's first release lands `release` branch with `dist/`-build contents:
```
/plugin marketplace add https://github.com/firaaz/cairn
/plugin install cairn@cairn-marketplace
uv run python scripts/validate_plugin_install.py
```
Check 9 transitions PENDING → PASS in one push. F3 becomes merge-final.

### M5+M6 milestone closure

D9 (atomic) closes when check 9 passes. A is the shortest path.

### Vision commitment #1 (Windsurf as second runtime)

A's `release` branch is a plain git branch on a public GitHub repo with the plugin payload at branch root. Any agent runtime that can `git clone` and read the file tree can consume it. A is **vision-neutral, not vision-blocking**.

### Maintenance load

Per release: one `workflow_dispatch` + one `dev`-side version-bump commit (~30 seconds). Initial: write `release-publish.yml` (~1 hour) + set up `release` branch (~5 min). **A has the lowest per-release ceremony among the three approaches.**

## Honest negative consequences

(a) **`release` branch is a CI-only deploy target with non-obvious purpose.** A maintainer who hasn't read the M5-amendment ADR sees `release` in `git branch -a` and may not understand why it exists. Documentation responsibility.

(b) **Force-with-lease pushes from CI are a permission escalation.** Today's CI is read-only; `release-publish.yml` requires `contents: write`. If `release` is later protected, a fine-grained PAT is needed (Phase-0.5 Gap 7).

(c) **Two file-layout shapes for one repo.** `dev` has cairn's full layout; `release` has the curated `dist/`-output layout. Confusing for first-time contributors. Mitigation: README banner + branch description.

(d) **`release` branch's history is rewritten every release.** Force-with-lease replaces previous release's HEAD; archaeology requires looking at tags (which Approach A optionally creates). Mitigation: keep optional tag step always-on.

(e) **The default `GITHUB_TOKEN` `contents: write` permission applies workflow-wide.** Token has write scope over the whole repo for the run's duration. Mitigation: keep workflow minimal; all used actions first-party.

(f) **`dist/`-on-`release` is git-tracked content; diff between releases is one big commit.** Reviewer wanting "what changed between v0.1.0 and v0.2.0 in payload" must `git diff v0.1.0..v0.2.0`. Mitigation: release commit message includes source SHA.

## Cross-approach comparison hooks

| Axis | A (release branch + sync CI) | B (npm publish) | C (git-subdir + tag) |
|---|---|---|---|
| Maintainer release-flow ceremony | one push + workflow click | npm publish + `dev` bump (S4) | tag creation + `dev` bump (S4) |
| Consumer-side prereqs beyond cairn's standing deps | none | npm on PATH (Gap 4, S3) | none |
| Two-step release coupling (S4) | avoided | applies | applies |
| D2 fit (manual semver-via-tags) | clean | awkward (3-way alignment) | clean (2-way alignment) |
| External-dep footprint | zero | npm registry | zero |
| Maintainer dogfood (S9) | risk-bearing (mitigated) | n/a | n/a |
| CI credential floor | default `GITHUB_TOKEN` | `NPM_TOKEN` secret | default `GITHUB_TOKEN` |
| Vision-1 fit (Windsurf) | runtime-portable | runtime-portable | runtime-portable |

## What A proposes Phase 0/0.5/1 didn't anticipate

**Novel defense — "release branch IS the plugin root" (shape-(i)).** Phase 0.5 considered both shapes implicitly. A makes the choice explicit: shape-(i) eliminates schema ambiguity (`github` source has no `path` field), simplifies the manifest, makes the release-branch tree directly readable as the plugin payload.

**Novel defense — workflow-input version-cross-check.** `release-publish.yml` accepts `version` as manual input, then verifies it matches `dist/.claude-plugin/plugin.json` value. Catches "I meant 0.2.0 but plugin-template still says 0.1.0" failure mode.

**Novel risk — branch-protection escalation post-launch.** Once `release` is established, branch protection requires upgrading from `GITHUB_TOKEN` to fine-grained PAT. Deferred decision: ship Approach A unprotected initially.

**Novel risk — `release` branch's "rewritten history" interacts with consumer-side git caching.** Brief window between force-push and consumer's re-clone could see inconsistency. Phase-0.5 Evidence 12 confirms Claude Code's `git pull` failure handler removes-and-re-clones, mostly absorbing this.

End of Phase 2A.
