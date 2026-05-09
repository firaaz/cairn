# Phase 2 — Approach B: npm publish

Author: Phase-2 sub-agent B (Plan), 2026-05-09. Persisted by lead.

## Synopsis

Approach B publishes cairn's curated `dist/` payload to the **npm registry** as a versioned package (e.g., `@firaaz/cairn`). `marketplace.json` lives on `dev` (default branch) and declares an `npm` source — the marketplace catalog is decoupled from the plugin payload's location. The catalog says "to install cairn, run `npm install @firaaz/cairn@0.x.y`"; the npm registry holds the canonical bytes.

Maintainer's release path: `git tag vX.Y.Z` → CI runs `build_dist.py` → CI synthesizes a `package.json` over the built tree → CI runs `npm publish --access public --provenance` → CI auto-bumps `marketplace.json` `source.version` on `dev` in the *same workflow* (S4 mechanization). Consumer's path: `/plugin marketplace add https://github.com/firaaz/cairn` (no `@ref` needed) → `/plugin install cairn@cairn-marketplace` → Claude Code shells out to `npm install @firaaz/cairn@0.x.y`.

The payload lives in three places that must agree on `0.x.y`: (1) `dist/.claude-plugin/plugin.json` `version` (which "wins silently" per Phase-0.5 Evidence 9), (2) `marketplace.json` `plugins[0].source.version`, (3) the npm-published version. CI mechanizes this 3-way alignment from a single source of truth (the git tag).

## Concrete shape

### marketplace.json (post-Approach-B rewrite)

```json
{
  "name": "cairn-marketplace",
  "owner": { "name": "firaaz" },
  "plugins": [
    {
      "name": "cairn",
      "description": "TDD-by-construction dispatch skill, hooks, and protocols for Claude Code.",
      "source": {
        "source": "npm",
        "package": "@firaaz/cairn",
        "version": "0.1.0"
      }
    }
  ]
}
```

Fields per Phase-0.5 Evidence 1 (`plugin-marketplaces:368-413`):
- `source.source: "npm"` discriminator (replaces invalid `"type": "git"`).
- `source.package: "@firaaz/cairn"` — scoped because cairn must own the namespace for supply-chain integrity.
- `source.version: "0.1.0"` — **explicit exact-pin**, NOT a semver range. Per Phase-0 constraint 16 npm.version accepts ranges; per cairn-D2, ranges are forbidden. We use exact version literally so npm's range semantics never fire.
- `source.registry` — omitted; defaults to public npm registry per Phase-0 constraint 16.

Lives on `dev` (default branch). README's literal `/plugin marketplace add https://github.com/firaaz/cairn` resolves at `dev`-tip and finds this manifest. **No `@ref` qualifier needed** — Phase 1 S2 (default-branch trap) does not apply to B.

### Synthesized package.json (published to npm)

CI generates this in the build directory before `npm publish`:

```json
{
  "name": "@firaaz/cairn",
  "version": "0.1.0",
  "description": "Cairn — TDD-by-construction dispatch for Claude Code.",
  "homepage": "https://github.com/firaaz/cairn",
  "repository": { "type": "git", "url": "https://github.com/firaaz/cairn.git" },
  "license": "MIT",
  "files": ["**/*"],
  "private": false
}
```

Notes:
- `name` matches `marketplace.json` `source.package` exactly.
- `version` matches the git tag (without `v` prefix).
- `files: ["**/*"]` ships **the entire build-output directory**. Curation happened upstream in `build_dist.py`'s allow-list (per ADR D3); package.json does NOT re-curate. Avoids L-019-class drift hazard.
- No `dependencies` / `devDependencies`. The package is a **distribution wrapper**, not a Node project. Claude Code's `npm install` fetches a leaf with zero dep tree (~1 round trip).
- No `scripts` field — no install/postinstall hook. `postinstall_validate.py` is consumer-invoked (per CONSUMER.md), not npm-invoked.

### dist/.claude-plugin/plugin.json (the 3-way alignment authority)

Per Phase-0.5 Evidence 9 (`plugin-marketplaces:715-718`), `plugin.json` `version` always wins silently over a marketplace entry's `version`. The 3-way alignment:

- `dist/.claude-plugin/plugin.json` `version` — authority for what consumers perceive as "current version."
- `marketplace.json` `source.version` — authority for which npm version is fetched.
- npm-registry version — authority for what bytes arrive.

CI mechanizes the alignment by deriving all three from one input: the git tag.

### CI workflow — `.github/workflows/release-publish.yml` (new)

```yaml
name: release-publish

on:
  push:
    tags:
      - 'v*.*.*'

concurrency:
  group: release-publish
  cancel-in-progress: false

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      id-token: write          # for npm provenance (--provenance)
    steps:
      - name: Checkout (full history, the tagged ref)
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          ref: ${{ github.ref }}

      - name: Derive version from tag
        id: ver
        run: |
          tag="${GITHUB_REF_NAME}"
          ver="${tag#v}"
          echo "version=${ver}" >> "$GITHUB_OUTPUT"
          echo "tag=${tag}"     >> "$GITHUB_OUTPUT"

      - name: Install uv
        uses: astral-sh/setup-uv@v3
      - name: Sync project venv
        run: uv sync

      - name: Setup Node + npm
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          registry-url: 'https://registry.npmjs.org'

      - name: Verify version triangle pre-build
        run: uv run python scripts/release/verify_version_triangle.py
             --tag-version "${{ steps.ver.outputs.version }}"

      - name: Build dist payload
        run: uv run python scripts/build_dist.py
             --repo-root .
             --dist-root /tmp/dist-out

      - name: Run allow-list assertions on built tree
        run: uv run pytest tests/unit/test_build_dist.py -q
        env:
          CAIRN_DIST_ROOT: /tmp/dist-out

      - name: Run post-install validator self-test on built tree
        env:
          CLAUDE_PLUGIN_ROOT: /tmp/dist-out
        run: uv run python scripts/postinstall_validate.py

      - name: Synthesize package.json over built tree
        run: uv run python scripts/release/synth_package_json.py
             --dist-root /tmp/dist-out
             --version "${{ steps.ver.outputs.version }}"

      - name: npm publish
        working-directory: /tmp/dist-out
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
        run: npm publish --access public --provenance

      - name: Bump marketplace.json source.version on dev
        run: |
          git fetch origin dev
          git checkout dev
          uv run python scripts/release/bump_marketplace_version.py \
              --version "${{ steps.ver.outputs.version }}"
          git add .claude-plugin/marketplace.json
          git -c user.name='cairn-release-bot' \
              -c user.email='release-bot@users.noreply.github.com' \
              commit -m "chore(release): bump marketplace.json source.version to ${{ steps.ver.outputs.version }}"
          git push origin dev
```

Trigger: only `git push --tags` matching `vX.Y.Z`. PR-time / dev-tip pushes continue to run `dist-gate.yml` validate-only.

Three new helper scripts under `scripts/release/` (within cairn's standing-dep envelope: stdlib + typer + pyyaml — no new deps):
1. `verify_version_triangle.py` — asserts `plugin-template.json` `version` equals tag-version-without-v, AND that `marketplace.json` `source.version` will be bumped to the same. Fails build before npm publish if anyone forgot to bump plugin-template before tagging.
2. `synth_package_json.py` — writes synthesized `package.json` into built tree.
3. `bump_marketplace_version.py` — reads `marketplace.json`, sets `plugins[0].source.version` to arg, writes back. Idempotent.

Secrets / org setup:
- **`NPM_TOKEN`** — automation token from npmjs.com, scoped to publish under `@firaaz/`. GitHub Actions secret.
- **`@firaaz` npm org** — must be created on npmjs.com.
- **`--provenance`** — npm's supply-chain feature; signs published tarball with GitHub Actions OIDC token. Free, recommended hard.

### Maintainer-side release flow

1. On `dev`: edit `.claude-plugin/plugin-template.json` to bump `version`. Commit: `chore(release): bump plugin-template.json version to 0.1.1`. (`chore:` prefix is in `_FALLBACK_REGISTRY`; scope-suffix `(release)` permitted per `validate_architecture.py:412-419` strip-scope-before-lookup logic.)
2. Update CHANGELOG.md.
3. `git tag v0.1.1 && git push origin v0.1.1`.
4. Workflow runs: verifies version triangle → builds dist → synthesizes package.json → publishes to npm → bumps `marketplace.json` `source.version` on `dev`.
5. Observe auto-bump commit on `dev`.
6. Consumers see new version on next `/plugin update`.

Maintainer-visible work is **one tag push**. Two-step coupling (S4) is wholly mechanized inside the single CI job.

### Consumer-side install flow

```
/plugin marketplace add https://github.com/firaaz/cairn
/plugin install cairn@cairn-marketplace
```

What Claude Code does:
1. Clones cairn's default branch (`dev`) — no `@ref` needed.
2. Parses `marketplace.json`, reads `source: { source: "npm", package: "@firaaz/cairn", version: "0.1.1" }`.
3. Shells out (most-natural reading per Phase-0.5 Evidence 5) to `npm install @firaaz/cairn@0.1.1` against an isolated cache dir.
4. Copies resulting `node_modules/@firaaz/cairn/` tree into `~/.claude/plugins/cache/cairn-marketplace/cairn/0.1.1/`.
5. Discovers `.claude-plugin/plugin.json` at cache root; loads plugin.

**Consumer prerequisite floor (new):** `npm` must be on `PATH`. Cairn's existing prereq floor is `jq` and `ruff`. B adds `npm`.

## Constraint fit

### Phase 0 constraint 7 — D2 manual semver pre-v1

**Does B violate?** Surface-level. D2 says "consumers pin via SHAs/tags"; npm-version is not enumerated. But underlying intent ("consumers get explicit, manually-bumped versions; no surprise updates") is fully preserved by B with `source.version: "0.1.1"` exact pin.

**Mitigation:** D2 must be amended (per Phase-0 constraint 22 ADR-amend protocol) to add npm-version to enumerated pinning fields. Co-landed with M5-ADR frontmatter-flip.

### Phase 0 constraint 9 — npm fallback to "unknown"

**B's avoidance:** explicit `source.version` always set; never trigger unknown-fallback. CI's `verify_version_triangle.py` catches drops/empties.

### Phase 0 constraint 16 — npm.version accepts ranges

**B's choice:** **exact pins only** (no `^`, `~`, `>=`, `<`, `*`, ` `, `||`). Non-negotiable per cairn-D2. Lint in `bump_marketplace_version.py` rejects range-bearing values. Converts Phase-0 conflict C3 into non-conflict at runtime.

### Phase 0 constraint 36 — Vision commitment #1 (Windsurf as 2nd runtime)

**Partial Claude-Code-coupling.** The npm-source mechanism is documented in Anthropic's marketplace docs — Claude-Code-specific. But **payload is portable**: Windsurf consumers can `npm install @firaaz/cairn` and point Windsurf at `node_modules/@firaaz/cairn/`. Or publish a Windsurf-flavored manifest alongside marketplace.json. **B's npm channel may be marginally MORE portable than git-subdir** (every editor with Node ecosystem can `npm install`).

## Pre-mortem scenario defense

### S1 — Schema-parse failure (CRITICAL, cross-approach)

**Defense.** Rewrite to `source.source: "npm"`; documented value (Phase-0.5 Evidence 1). F3 audit check 9 finally runs.

### S3 — npm consumer-side dependency (HIGH, B-specific) — **B carries this**

Load-bearing weakness B accepts.

**Defense stack:**
1. **CONSUMER.md prereqs update** — add `npm` to system-deps list with install instructions per platform.
2. **Extend `postinstall_validate.py`** — add `"npm"` to `DEP_OWNERS` dict; warn-only check.
3. **Pre-install preflight** — CONSUMER.md callout: "Verify `npm --version` before continuing."
4. **Risk Register entry** in new ADR.

**Phase-0.5 Gap 4 docs-ambiguity:** docs ambiguous on consumer-side npm vs Claude-Code-embedded. **B's planning assumption: consumer-side npm.** Evidence supporting: (a) `registry` field "Defaults to the **system** npm registry"; (b) version-fallback returns `unknown` for npm sources (suggests Claude Code reads npm's resolution output).

**Residual if wrong:** if Claude Code bundles its own npm, B's CONSUMER.md update is over-cautious — strictly better than under-prereq.

### S4 — Two-step release coupling (HIGH, B and C) — **B mechanically defends**

CI workflow does both steps in **one job**. If step (1) `npm publish` succeeds and step (2) `git push` fails (e.g., `dev` protected), workflow fails loudly. `bump_marketplace_version.py` is idempotent — re-run safe.

3-way version triangle: git tag is single input; CI derives all three. `verify_version_triangle.py` asserts pre-publish.

### S5 — INV-001 commit-prefix binding (HIGH, all approaches)

**Defense.** Auto-commit prefix `chore(release):`. Verified `chore:` is in `_FALLBACK_REGISTRY` (`validate_architecture.py:279`); prefix-match strips scope (lines 412-419).

### S8 — Schema breaking change upstream (MEDIUM)

**B-specific resilience:** even if Anthropic deprecates `source.source: "npm"`, the underlying npm package `@firaaz/cairn@0.1.1` exists on registry forever (npm immutability). Consumers can fall back to manual `npm install` + cache-dir wire-up. A and C don't have this property as cleanly. **Small advantage for B Phase 1 didn't surface.**

## Downstream impact

### CONSUMER.md update

Add "System dependencies" section near top with `jq` + `ruff` + `npm` install commands per platform.

### `scripts/postinstall_validate.py` extension

Add `"npm"` to `DEP_OWNERS` dict; warn-only check.

### Cairn's standing-dep contract

CLAUDE.md `:30` rule applies to cairn's *Python* code (`pip install`-able deps). B does NOT add a Python dep. Introduces a new **consumer-side system tool** (npm). Standing-dep rule silent on system tools — `jq` and `ruff` are already non-Python system tools. Honest framing: "B expands consumer-prereq floor from {jq, ruff, python3} to {jq, ruff, python3, npm}."

### `complex-rag-analysis` migration

`complex-rag-analysis` is Python uv. npm not guaranteed. Three cases:
1. Already has npm — no friction.
2. Doesn't have npm — `brew install node` (~30 sec).
3. Air-gapped — escape hatch via direct `curl` from registry tarball URL + manual cache wire-up.

### F3 audit check 9

Today PENDING. Under B: PENDING resolves the moment first `release-publish` completes. Verification: ensure `npm --version` works, `/plugin marketplace add`, `/plugin install`, validator green, smoke-test dispatch.

### Future Windsurf-port story

B's payload distribution layer (npm) is *more* runtime-portable than A/C's git-based. Marketplace.json is Claude-Code-specific in all approaches.

## Honest negative consequences

1. **npm-org credentialing** — ~30 min one-time. Token rotation requires re-credentialing. Second auth boundary beyond GitHub.
2. **Two-step release coupling exists structurally — mechanized but not invisible.** A's "one push to release branch" has no analogous failure.
3. **Consumer prereq floor expands by one.** Real onboarding cost for non-Node consumers.
4. **External-system dependency at install time.** Every `/plugin install` requires npmjs.org reachable. npm has had multi-hour outages historically. Mitigation: existing pinned consumers continue working.
5. **Docs-ambiguity bet** (Phase-0.5 Gap 4 + S3). Conservative posture stands; WebFetch fresh docs at landing time to confirm.
6. **npm's range semantics are a permanent footgun for downstream forkers.** Cairn-side lint catches; downstream consumers reusing the pattern could write range-pinned manifests that violate D2 stability.
7. **`package.json` synthesis layer is an additional artifact to maintain.** Documentation explains.
8. **npm's per-version immutability is a constraint.** Botched `0.1.0` cannot be fixed in-place after 72-hour unpublish window — requires `0.1.1`. A's release-branch can be force-pushed; B's published version cannot.

## Cross-approach comparison hooks

### npm vs git-based: install bandwidth and registry uptime

- **Bandwidth.** npm package = curated tree only (~tens of KB). Git clone or git-subdir = repo metadata + history (~MB-scale). **B wins on bandwidth.**
- **Uptime.** npm registry has its own uptime; both ~99.9%. A and C bottleneck on GitHub; B bottlenecks on npmjs.org. B adds **one** registry, not zero.

### Maintainer ceremony

- **A**: build → `git rm` → replace tree → commit → push. Mid-step abort recoverable.
- **B**: build → synthesize → `npm publish` (immutable) → marketplace bump. Mid-step abort: npm publish immutable, idempotent re-run safe.
- **C**: build → commit → tag → push (+ marketplace bump). Two-step coupling.

### Versioning: npm immutability vs git-tag immutability

**Underrated B advantage:** **npm versions are stronger pins than git tags.** A force-push could in principle move a tag. An npm version cannot be republished (after 72-hour unpublish). Phase 1 didn't surface this.

## What B proposes Phase 0/0.5/1 didn't anticipate

1. **3-way version triangle as `verify_version_triangle.py` precondition.** Phase 1 S4 named the problem; B's defense converts 3-way drift into workflow-failure-before-side-effect.

2. **`--provenance` on `npm publish` for supply-chain attestation.** B is the only approach with a free GitHub-Actions-OIDC-based attestation. A and C ship via git push; git's signing layer requires GPG key management cairn doesn't have.

3. **npm immutability as stability invariant stronger than git-tag immutability.** Phase 1 didn't mention; marginally strengthens B's cairn-D2 honesty.

4. **`@firaaz/cairn` namespace ownership as anti-typosquat defense.** Owning the npm scope `@firaaz` prevents anyone publishing `@firaaz/<anything-else>`. Small but real supply-chain hygiene win.

5. **Synthesized package.json keeps build-script curation as the single allow-list.** `files: ["**/*"]` rejects re-curation in package.json. Avoids drift hazard.

6. **Consumer-prereq honesty improves cairn's installation reliability.** B's required prereq-section update creates a focused "system dependencies" callout listing all three (jq, ruff, npm) — docs improvement that benefits all approaches but B is the forcing function.

End of Phase 2B.
