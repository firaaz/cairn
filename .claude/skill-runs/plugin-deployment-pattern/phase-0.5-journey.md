# Phase 0.5 — User-Journey Trace

Decision: "Plugin deployment pattern: how does `dist/` reach a ref consumers can resolve via `/plugin install`?"

Source: Phase 0.5 subagent run, 2026-05-09.

---

## Preface — what the trace must navigate

The decision is structurally about **how the curated `dist/` payload makes the cross-trust-boundary trip from a cairn maintainer's local checkout to a consumer's plugin cache**. F1 shipped the build pipeline (`scripts/build_dist.py` + `.github/workflows/dist-gate.yml`) but no publish step; F3's audit check 9 is PENDING precisely because the consumer's `/plugin install` cannot resolve `dist/` against any pushed ref.

The four roles below trace the same four-stage transit at different points:

```
[maintainer commits] → [CI/release builds dist/] → [pushed ref carries dist/] → [consumer resolves]
```

Each role hits a different subset of those four stages, and each approach (A/B/C) crosses each stage with a different mechanism. The boundary inventory at the end maps each crossing to clean / awkward / unmechanized per approach.

A separate-but-load-bearing finding while reading the Anthropic docs: **cairn's current `marketplace.json` schema is wrong regardless of approach.** It declares `source.type: "git"` (`.claude-plugin/marketplace.json:11`), but the docs do not list `"git"` as a valid `source.source` value — only `github`, `url`, `git-subdir`, and `npm`, plus a bare relative-path string (`code.claude.com/docs/en/plugin-marketplaces:231-238`). Also the discriminator field is `source.source`, not `source.type`. This means **today's manifest may not parse at all on a real `/plugin install` attempt** — i.e., audit check 9 may fail before it even gets to the missing-`dist/` symptom. The trace below proceeds as if today's manifest worked as the M5 ADR D3 implies (resolve subdirectory of the marketplace's git repo) so we can map the deployment pattern; the schema-correction overlap is flagged in Gap 8 below.

---

## Roles in scope

1. **First-time consumer** — runs `/plugin marketplace add` + `/plugin install cairn@cairn-marketplace` in a fresh project.
2. **Existing-symlink consumer** (`complex-rag-analysis`) — follows `docs/upgrading-from-symlink.md`, then runs the install.
3. **Cairn maintainer (release author)** — cuts a release that produces a deployable `dist/`.
4. **Cairn maintainer (post-merge to dev)** — what happens between dev-tip and the next release-tag? Is consumer-tracking broken in this window?

For each role, three parallel action sequences are traced — one per approach (**A**, **B**, **C**) — because the deployment pattern is exactly what differentiates the journey at the boundaries that matter.

---

## Role 1 — First-time consumer

Context: a developer with their own project (no prior cairn relationship) decides to consume cairn after reading `README.md`. They are sitting in a Claude Code session at their project root, with system deps installed (`brew install jq`, `uv tool install ruff` per `CLAUDE.md:13-15`).

### 1.A — Approach A (release-branch with `dist/` committed + sync CI)

1. **Operator runs slash command 1.** Inputs: `/plugin marketplace add https://github.com/firaaz/cairn` (`README.md:19`, `CONSUMER.md:14`). Outputs: Claude Code clones the cairn repo to `~/.claude/plugins/marketplaces/cairn-marketplace/` (`code.claude.com/docs/en/plugin-marketplaces:229`: "Once a plugin is cloned or copied into the local machine, it is copied into the local versioned plugin cache at `~/.claude/plugins/cache`"). The marketplace clone targets the **default branch** by default (`code.claude.com/docs/en/plugin-marketplaces:842-843`: "To pin to a branch or tag, append `@ref` to the GitHub shorthand or `#ref` to a git URL" — i.e., default branch is the implicit fallback when no ref is specified).
   - **Boundary**: marketplace fetch boundary. Mechanism: git clone (full repo).
2. **Claude Code parses `marketplace.json`.** Inputs: the file at `.claude-plugin/marketplace.json` of the cloned default branch (`dev` per `git status`). Outputs: registered `cairn-marketplace` entry with one plugin (`cairn`) whose source is a relative subdirectory `dist/` of the same repo (per `marketplace.json:13`). Under Approach A's assumed schema fix, this is `{ "source": "./dist" }` (a relative-path string per `code.claude.com/docs/en/plugin-marketplaces:233`).
   - **Boundary**: marketplace-schema-parse boundary. **GAP** today: `source.type: "git"` is not a documented value; see Gap 8.
3. **Operator runs slash command 2.** Inputs: `/plugin install cairn@cairn-marketplace`. Outputs: Claude Code resolves `dist/` against the **same cloned ref** the marketplace was added at (the default branch — Approach A keeps the default branch on `dev`, where `dist/` is `.gitignore`'d). With Approach A, the operator's `/plugin marketplace add` url must be qualified with the release-branch ref: `/plugin marketplace add firaaz/cairn@release` (the `@ref` syntax of `code.claude.com/docs/en/plugin-marketplaces:858-861`).
   - **GAP** vanilla A: if the user runs the README's literal command without `@release`, marketplace adds at `dev`-tip, where `dist/` is git-ignored. `/plugin install` fails.
   - **Mitigation in A**: README must instruct `/plugin marketplace add firaaz/cairn@release` (or push the marketplace.json onto a long-lived release branch, with `dev` carrying a placeholder marketplace.json). Either way, the literal install instructions in `README.md:19` and `CONSUMER.md:14` need a refactor.
4. **Claude Code copies plugin payload to cache.** Inputs: the `dist/` subdirectory from the cloned ref. Outputs: `~/.claude/plugins/cache/cairn-marketplace/cairn/<version>/` containing `dist/`-mirror tree (`skills/cairn-tdd-feature/`, `agents/phase-{1..4}-tdd.md`, `agents/triager-tdd.md`, `agents/role-topology.yaml`, `checks/{reversibility-guard.sh,reality-check.sh,role_guard.py}`, `templates/handoff.md`, `.claude-plugin/plugin.json`, `hooks/hooks.json`, `postinstall_validate.py`).
   - **Boundary**: payload-cache boundary. Mechanism: directory copy (`code.claude.com/docs/en/plugins-reference:619` "Claude Code copies *marketplace* plugins to the user's local **plugin cache**").
5. **Plugin manifest discovered.** Inputs: `.claude-plugin/plugin.json` at the cache root. Outputs: plugin metadata (name, version, hooks ref, agents dir, skills dir).
6. **Hooks register from plugin payload.** Inputs: `dist/hooks/hooks.json` (per `m5-plugin-distribution-and-symlink-retire/D4`). Outputs: `PreToolUse`, `PostToolUse`, etc. handlers wired to commands using `${CLAUDE_PLUGIN_ROOT}` substitution (`code.claude.com/docs/en/plugins-reference:542-544`).
   - **State transition**: consumer's hook registry changes from "no cairn hooks" to "three cairn hooks active".
7. **Skills + agents register.** Same flow, automatic discovery (`code.claude.com/docs/en/plugins-reference:41` "Skills and commands are automatically discovered when the plugin is installed"; `code.claude.com/docs/en/plugins-reference:73` for agents).
8. **Operator runs post-install validator.** Inputs: `uv run python scripts/validate_plugin_install.py` (`CONSUMER.md:22`). Outputs: clean exit (or actionable error).
9. **Operator authors first plan doc.** Inputs: `templates/feature-plan.md` (shipped under plugin cache; `CONSUMER.md:29`). Outputs: `docs/plans/<date>-<feature>.md` in consumer repo.
10. **Operator dispatches `cairn-tdd-feature` skill.** Inputs: plan path. Outputs: four-phase pipeline, four commits, `.claude/skill-runs/<feature-id>/` artefacts in consumer repo.

**Boundaries crossed by 1.A**:
- Marketplace fetch boundary (git clone of default branch).
- Marketplace-schema-parse boundary.
- Plugin-source ref resolution boundary (where does `dist/` live?).
- Payload-cache boundary.
- Hook/skill/agent registration boundary.
- Consumer-state ownership boundary (per-feature plan docs and skill-runs are consumer-owned).

### 1.B — Approach B (npm publish: `source.source: "npm"`)

1. **Operator runs `/plugin marketplace add https://github.com/firaaz/cairn`.** Same as 1.A step 1 — marketplace fetch is independent of plugin source-type.
2. **Claude Code parses `marketplace.json`.** Outputs: plugin entry with `source: { "source": "npm", "package": "@firaaz/cairn", "version": "0.x.y" }` (`code.claude.com/docs/en/plugin-marketplaces:374-394`).
3. **Operator runs `/plugin install cairn@cairn-marketplace`.** Inputs: above. Outputs: Claude Code invokes `npm install @firaaz/cairn@0.x.y` to fetch the package (`code.claude.com/docs/en/plugin-marketplaces:368-370` "Plugins distributed as npm packages are installed using `npm install`").
   - **Mechanism caveat**: the docs say "installed using `npm install`" but do not explicitly state whether Claude Code shells out to the consumer's npm binary or uses an embedded npm client. Most natural reading is "shells out to consumer's `npm`" because that is the only way private registry credential helpers work, and it matches the pattern of how `code.claude.com/docs/en/plugin-marketplaces:508-516` describes git-credential resolution (uses host system's helpers).
   - **Pre-mortem-relevant assumption (needs Phase 1 challenge)**: Approach B requires consumer-side `npm` on PATH. If absent, install fails with a missing-binary error (specific message ambiguous in docs).
4. **Plugin payload arrives in cache.** The `package.json`'s contents (post-`npm install`) become the plugin root. The `files:` array in `package.json` (or `.npmignore`) curates what ships — i.e., **npm's curation contract replaces `dist/`'s curation contract**.
   - **Implication for build pipeline**: `scripts/build_dist.py`'s allow-list either becomes the npm-publish content (e.g., set `package.json` `files:` from the same allow-list) or the build outputs to a directory that `npm publish` is run against. Either way, F1's `build_dist.py` is reusable; the publish step replaces "`git push` to release branch" with "`npm publish`".
5. **Steps 5–10 same as 1.A.** Manifest parse, hook/skill/agent registration, validator, plan doc, dispatch.

**Boundaries unique to 1.B**:
- npm-resolution boundary (consumer-side npm binary required, network reach to npm registry).
- npm-credential boundary for private registries (`.npmrc` or `NODE_AUTH_TOKEN`).
- Version-semantics boundary (npm semver-range, e.g., `^0.x.y` vs cairn-D2's "pin SHAs/tags" stance — pre-v1 npm conventions tolerate `0.x` ranges but the cairn ADR commits to manual bumps).

### 1.C — Approach C (GitHub release artifact / `git-subdir` against tag)

The brief lists "GH-release+subdir" but the Anthropic docs do not document a `source.source: "github-release"` value. The closest documented mechanism is `source.source: "git-subdir"` pointed at a tag (`code.claude.com/docs/en/plugin-marketplaces:329-366`), where the tag is created by the release workflow against a commit that has `dist/` populated.

1. **Operator runs `/plugin marketplace add ...`.** Same as 1.A step 1.
2. **Claude Code parses `marketplace.json`.** Outputs: plugin entry with `source: { "source": "git-subdir", "url": "https://github.com/firaaz/cairn.git", "path": "dist", "ref": "v0.x.y" }` (or omits `ref` to track the default branch — but Approach C's premise is pinning to a release).
3. **Operator runs `/plugin install`.** Outputs: Claude Code does a sparse partial clone of cairn at `v0.x.y`, fetching only `dist/` (`code.claude.com/docs/en/plugin-marketplaces:331` "Claude Code uses a sparse, partial clone to fetch only the subdirectory, minimizing bandwidth for large monorepos").
4. **Cache + register.** Same as 1.A steps 4–7, but the `dist/` payload comes from the tag, not from a branch.

**Boundaries unique to 1.C**:
- Tag-existence boundary: if `v0.x.y` does not exist or does not have `dist/` populated, install fails (specific error: `code.claude.com/docs/en/plugins-reference:929` "Plugin directory not found at path: ./plugins/my-plugin. Check that the marketplace entry has the correct path.").
- Tag-creation pre-condition: the tag must be created by the release workflow against a commit that materialised `dist/`. This means CI must commit `dist/` (or use a detached-tag mechanism — see Gap 5).

**Variant 1.C′ — true GitHub-release artifact** (i.e., a release-asset tarball, not a tagged commit). Not documented in `code.claude.com/docs/en/plugin-marketplaces`. **There is no `source.source` value for "GitHub release archive download"** in the documented schema. If the operator's "Approach C" envisions this, it is **structurally not supported** by the marketplace schema as documented. Approach C must be re-grounded onto `git-subdir` + tag (the closest documented mechanism) or reduce to a pre-v1 hybrid (release-branch tag plus `git-subdir` resolution, which collapses into Approach A semantically).

---

## Role 2 — Existing-symlink consumer (`complex-rag-analysis`)

Context: an existing consumer with `.slice-system → /abs/path/to/cairn` and `.claude/settings.json` hook entries pointing at `$CLAUDE_PROJECT_DIR/.slice-system/checks/...`. They follow `docs/upgrading-from-symlink.md`. The migration runbook is approach-agnostic up until the actual `/plugin install` step (`docs/upgrading-from-symlink.md:46-60`); the deployment pattern only diverges at that step.

### Pre-install steps (common to A/B/C)

1. **Quiescence preflight.** Inputs: `scripts/migrate_from_symlink.sh` (copied from cairn before the symlink unlink). Outputs: exit 0 (clean) or exit 2 (in-flight skill-run; halt) or exit 3 (cairn-self detected; abort) per `docs/upgrading-from-symlink.md:14-31`.
2. **Atomic swap step 1.** Inputs: `unlink .slice-system`. Outputs: symlink gone; `.slice-system` no longer resolves.
3. **Atomic swap step 2 (run `/plugin marketplace add`).** Inputs: `/plugin marketplace add https://github.com/firaaz/cairn`. Outputs: marketplace cloned; **same fetch boundary as Role 1**.

### Per-approach divergence

#### 2.A — Approach A
4.A. **`/plugin install`.** Same as 1.A step 3. **Same `@release` ref-pinning gap**: the runbook at `docs/upgrading-from-symlink.md:49` says `/plugin marketplace add https://github.com/firaaz/cairn` (no `@ref`). Under A, this resolves to default branch (`dev`), where `dist/` is git-ignored, install fails. Runbook needs `@release` qualifier.
5.A. **Step 2.4: filter `.claude/settings.json` hook entries** (`docs/upgrading-from-symlink.md:62-70`). Inputs: `migrate_from_symlink.sh`'s jq filter pass. Outputs: `.claude/settings.json` no longer references `$CLAUDE_PROJECT_DIR/.slice-system/checks/...`; plugin-internal `hooks.json` (per ADR D4) registers the hooks at the plugin-cache path.

#### 2.B — Approach B (npm)
4.B. **`/plugin install`.** Same as 1.B step 3 — npm-install boundary applies. **Concern**: `complex-rag-analysis` is a Python uv project; npm presence is not guaranteed. Runbook would need a "verify `npm --version`" preflight step.
5.B. Same as 5.A.

#### 2.C — Approach C (git-subdir + tag)
4.C. **`/plugin install`.** Same as 1.C step 3 — sparse clone at tag `v0.x.y`. **Tag must exist with `dist/` populated** at the moment of install.
5.C. Same as 5.A.

### Post-install steps (common again)
6. **Session restart.** Inputs: operator quits Claude Code, restarts it. Outputs: agent registry reloads, hooks reload from plugin cache (`docs/upgrading-from-symlink.md:74-77`).
7. **Smoke test.** Inputs: `uv run python scripts/validate_plugin_install.py`, then a trivial `cairn-tdd-feature` dispatch (`docs/upgrading-from-symlink.md:114-126`). Outputs: clean validator exit + four phase commits + `.claude/envelope-grants.log` lands consumer-side.

**Boundaries unique to Role 2**:
- Symlink-removal atomicity boundary: between `unlink .slice-system` and `/plugin install` completing successfully, there is a window where neither the symlink nor the plugin payload is present. Hooks 404 silently in this window. Under all approaches the runbook's session-restart step (6) closes this; the boundary is timing-of-restart.
- Settings.json filter boundary: `$CLAUDE_PROJECT_DIR/.slice-system/checks/...` references must be removed atomically with the install.
- Per-feature in-flight skill-runs boundary: `.claude/skill-runs/<id>/` survives if quiescence preflight passed; orphaned otherwise.

---

## Role 3 — Cairn maintainer (release author)

Context: a maintainer is sitting on `dev` with a tested change ready to ship. They want consumers to be able to update to this change via `/plugin update`. The deployment pattern fully differentiates this role's actions across A/B/C — the maintainer's release verbs are the most novel surface.

### 3.A — Approach A (release-branch with `dist/` committed + sync CI)

1. **Maintainer merges feature branch into `dev`.** Inputs: PR merge or direct push. Outputs: `dev` HEAD advances. `dist-gate.yml` runs and validates `build_dist.py` produces a valid `dist/` payload (`/.github/workflows/dist-gate.yml:23-32`), but **does not push `dist/` anywhere**.
   - **State transition**: cairn-the-repo internally consistent; consumer-visible state unchanged (consumers track the `release` branch, not `dev`).
2. **Maintainer decides to cut a release.** Inputs: operator decision based on roadmap / handoff cadence (`docs/roadmap.md`). Outputs: maintainer either runs a manual release script or triggers a CI workflow tagged "release".
3. **Release workflow runs (CI-side).** Inputs: a triggering event (e.g., `git tag v0.x.y && git push origin v0.x.y`, or a manual `workflow_dispatch`). Outputs:
   - CI runs `uv run python scripts/build_dist.py --repo-root . --dist-root /tmp/dist-out`.
   - CI checks out (or creates) the `release` branch.
   - CI replaces `release`'s tree with `/tmp/dist-out`'s contents (or `git rm -r dist/` followed by copying `/tmp/dist-out` into `dist/`, then `git add dist/`, then commit).
   - CI commits with a message like `chore(release): v0.x.y dist payload from <commit-sha>`.
   - CI bumps `dist/.claude-plugin/plugin.json`'s `version` field per `m5-plugin-distribution-and-symlink-retire/D2` (semver-via-tags pre-v1).
   - CI pushes `release` and (optionally) tags `release-v0.x.y`.
   - **Mechanism caveat**: `code.claude.com/docs/en/plugins-reference:1004-1011` warns that explicit `version` requires manual bumps — so step "bumps version" must be deliberate, not "always copy `version: 0.0.0-dev`".
4. **`marketplace.json` either lives on `release` only, OR lives on `dev` and points at `release`.**
   - **Option 3.A.i**: marketplace.json lives only on `release` branch. README's `/plugin marketplace add https://github.com/firaaz/cairn` resolves to default branch, which is `dev` — no marketplace.json there means add fails. **Default branch must change to `release`** OR README must qualify with `@release`. `dev` would no longer auto-resolve as marketplace; this changes the maintainer's own dogfood loop.
   - **Option 3.A.ii**: marketplace.json lives on both `dev` and `release`, with the source pointing at the same repo's `release` ref. But — checking the schema — relative paths (`./dist`) are resolved against the *marketplace's own clone*. If `/plugin marketplace add` clones `dev`, then `./dist` resolves against `dev`'s tree, where `dist/` is git-ignored. **Relative path source is structurally incompatible with "marketplace lives on `dev`, plugin lives on `release`".** Approach A must use `source.source: "github"` with `repo: "firaaz/cairn"` and `ref: "release"` (`code.claude.com/docs/en/plugin-marketplaces:280-288`) to point at the release branch from a `dev`-hosted marketplace.json.
   - **Decision implication**: under Approach A, `marketplace.json` cannot use the relative-path source string. It must use the `github` (or `git-subdir`) source object with explicit `ref`. This is a non-trivial schema change from today's manifest.
5. **Maintainer announces release.** Inputs: handoff edit, CHANGELOG.md update on `dev`. Outputs: consumers see the version bump on next `/plugin update`.
   - Consumer-side: `claude plugin update cairn@cairn-marketplace` resolves the new version of `release` branch (or new commit SHA per `code.claude.com/docs/en/plugin-marketplaces:706-712`).

**Boundaries unique to 3.A**:
- Release-branch existence boundary: must be created and kept alive across releases.
- `dist/`-on-`release`-branch atomicity boundary: each release must `git rm` old `dist/` and add new — partial replacement risks stale files.
- Marketplace.json source-ref boundary: must be a `github`-source object with `ref: "release"`, NOT a relative path.
- CI-credential boundary: GitHub Actions need a token with push permission to `release` (above default `GITHUB_TOKEN` permissions for protected branches).

### 3.B — Approach B (npm publish)

1. **Maintainer merges into `dev`.** Same as 3.A step 1 — `dist-gate.yml` validates build only.
2. **Maintainer cuts release.** Inputs: tag `v0.x.y` or `workflow_dispatch`.
3. **Release workflow runs.**
   - CI runs `build_dist.py` to populate `/tmp/dist-out`.
   - CI synthesizes a `package.json` in `/tmp/dist-out` with `name: "@firaaz/cairn"`, `version: "0.x.y"`, `files: [...]` (or pre-curate via `.npmignore` since `dist/` is fully curated already).
   - CI runs `cd /tmp/dist-out && npm publish --access public` (or `--access restricted` for a scoped private package).
   - **Credential**: needs `NPM_TOKEN` secret in GitHub Actions secrets, scoped to publish under `@firaaz/`.
4. **`marketplace.json` declares `source.source: "npm"`, `source.package: "@firaaz/cairn"`, `source.version: "0.x.y"`.**
   - If `version` is omitted, npm's default behavior fetches "latest" — but cairn-D2 is "pin SHAs/tags", so `version` should be explicit. The version is pinned in `marketplace.json`'s plugin entry rather than via a semver range.
   - **Marketplace-on-`dev` is fine here**: the marketplace.json's `source` doesn't reference any git ref of cairn-the-repo. The relative-path / cross-ref incompatibility from 3.A vanishes. `/plugin marketplace add` from `dev` works without `@release` qualifier.
5. **Maintainer pushes a `marketplace.json` update bumping `version: "0.x.y"` to the new release.** This is the consumer-visible signal.
   - **Concern**: every release requires both `npm publish` AND a commit-to-`dev` bumping `version`. If the maintainer publishes to npm but forgets to bump `marketplace.json`, consumers don't see the new version (`/plugin update` reports "already at the latest version"). This is a two-step coupling that A doesn't have (A's coupling is `dist/` push + version bump on the same `release` branch).
   - **Counter-mitigation**: omit `version` from marketplace.json and use the `npm` package's `latest` tag. But this loses the pin-explicitly stance and `code.claude.com/docs/en/plugin-marketplaces:998` warns of `unknown` version for npm sources without explicit version, which means update detection is brittle.

**Boundaries unique to 3.B**:
- npm-org-credential boundary: `@firaaz` scope must exist on npmjs.org (or private registry); maintainer must have publish permission.
- npm-publish-secret-in-CI boundary: `NPM_TOKEN` must be in GitHub secrets.
- Two-step release boundary: `npm publish` and `marketplace.json` version bump must both happen.
- Consumer-side npm-PATH boundary: every consumer needs `npm` on PATH (extends from Role 1.B).

### 3.C — Approach C (`git-subdir` against tag)

1. **Maintainer merges into `dev`.** Same as 3.A step 1.
2. **Maintainer cuts release.** Inputs: triggering action.
3. **Release workflow runs.**
   - CI runs `build_dist.py` to populate `dist/` in the working tree.
   - CI commits `dist/` to a temporary branch or to a release-only commit (this commit has `dist/` materialised, while `dev` does not).
   - CI tags this commit as `v0.x.y`.
   - CI pushes the tag to origin.
   - **Decision point**: does CI delete the temporary branch, leaving only the tag? Or keep a `release` branch where the latest tag's commit is `release`'s HEAD? Either works — the tag is the consumer-resolvable handle.
   - Tags do not move; consumers pinning to `v0.x.y` get a stable payload.
4. **`marketplace.json` declares `source.source: "git-subdir"`, `source.url: "https://github.com/firaaz/cairn.git"`, `source.path: "dist"`, `source.ref: "v0.x.y"`** (or no `ref`, tracking default branch — but C's premise is pin-to-tag).
   - `marketplace.json` lives on `dev` and is consumer-resolvable from `dev`'s clone. The `git-subdir` source independently resolves against `cairn.git`'s tag space.
5. **Maintainer pushes a `marketplace.json` update bumping `source.ref`** from `v0.x.(y-1)` to `v0.x.y`. This is the consumer-visible signal — same two-step coupling as 3.B (publish-tag + bump-marketplace-json).
   - **Counter-mitigation**: omit `source.ref`, track default branch's `dist/` (which doesn't exist under C's premise). Or use a moving tag like `release` (anti-pattern; SHA pinning is the cairn-D2 stance).

**Boundaries unique to 3.C**:
- Tag-creation atomicity boundary: tag commit must include `dist/`; partial-tagging (tag pointing at a `dist/`-less commit) breaks all consumers.
- Two-step release boundary: tag push + marketplace.json `ref` bump.
- Tag-naming convention boundary: `v0.x.y` per cairn-D2; CI must enforce.
- Detached-`dist/`-commit boundary: if `dist/` is only in the tagged commit and never on a branch, it's reachable only via the tag, not via any `git pull` in normal operation. This is fine for consumers (they pin) but unusual for git ergonomics.

---

## Role 4 — Cairn maintainer (post-merge to dev, between releases)

Context: a maintainer has just merged a PR into `dev`. The PR contains a substantive change (e.g., a new behavioural assertion in `role_guard.py`). They have NOT yet cut a release. What does a consumer who runs `/plugin update` experience? What does the next pin-aware consumer experience?

### 4.A — Approach A

1. **Merge into `dev`.** Outputs: `dev` HEAD advances; `dist-gate.yml` validates; **no consumer-visible change**.
2. **Consumer runs `/plugin update cairn@cairn-marketplace`.** Inputs: command. Outputs: Claude Code refreshes the marketplace clone (re-clones / pulls) — this picks up `dev`-tip's `marketplace.json`. Then it resolves the plugin source.
   - With Option 3.A.ii (marketplace.json points at `github` source `ref: "release"`), the plugin source is `release` branch. `release` did not advance; `/plugin update` reports "already at latest version" (`code.claude.com/docs/en/plugins-reference:1004-1008`).
   - With Option 3.A.i (default branch is `release`, marketplace lives only on `release`), `dev`-merge has no effect on consumers; same outcome.
3. **Consumer onboards fresh.** Inputs: `/plugin marketplace add firaaz/cairn`. If default branch is `dev`, marketplace adds at `dev`-tip. If marketplace.json is on both `dev` and `release` (Option 3.A.ii), this works — fresh consumer gets `dev`-tip's marketplace.json which points at `release`'s plugin payload. Consumer pins forward to whatever `release` is.
   - **Result**: consumer is held back at the last release. Gap to `dev`-tip is the difference between most-recent-merge and most-recent-release.
4. **Maintainer's own dogfood is unaffected.** Cairn-the-repo retains `.slice-system → .` self-symlink (M5 ADR D8), so the maintainer is not running plugin-cached cairn. Their dev-loop sees `dev`-tip immediately.

**State transition unique to 4.A**: between merge and release, `dev` advances but consumer-resolvable state does not. Consumer is consistently behind the bleeding edge by some bounded delta.

### 4.B — Approach B (npm)

1. **Merge into `dev`.** Same as 4.A step 1.
2. **Consumer runs `/plugin update`.** Outputs: Claude Code refreshes marketplace, parses `marketplace.json`, sees `source.version: "0.x.y"`. If unchanged, npm sees same version, install skipped. Same "held at last release" semantics as 4.A.
3. **Variant**: if `marketplace.json` declares a semver range like `^0.x.y` on npm-source, then `/plugin update` resolves the latest matching published version. Pre-v1 (`0.x.y`), `^0.x.y` collapses to exactly `0.x.y` per npm semver semantics — but `~0.x.y` allows patch updates. The cairn ADR's "pin SHAs/tags" stance argues for explicit `version`, not range — same outcome as A.
4. **Maintainer's own dogfood**: same as 4.A — Path B self-symlink unaffected.

**State transition unique to 4.B**: same shape as 4.A. The intermediate state lives on npm registry instead of git refs, but the "consumer held at last published version" outcome is identical.

### 4.C — Approach C (`git-subdir` + tag)

1. **Merge into `dev`.** Same as 4.A step 1.
2. **Consumer runs `/plugin update`.** Outputs: Claude Code refreshes marketplace, parses `marketplace.json`, sees `source.ref: "v0.x.y"`. The `git-subdir` resolution targets the tag — tag did not move; install skipped.
3. **Variant**: if `marketplace.json` omits `source.ref`, default branch tracking applies. Default branch is `dev` (assumed unchanged for cairn-internal-dogfood reasons under D8). On `dev`, `dist/` is git-ignored — `git-subdir` would fail to find the `path: "dist"` subdirectory (`code.claude.com/docs/en/plugins-reference:929`). Consumers would get an install error, not a held-back version.
   - **Conclusion**: 4.C is only consistent if `source.ref` is set to a tag.
4. **Maintainer's own dogfood**: same as 4.A.

**State transition unique to 4.C**: same shape as 4.A/B given pinned `ref`. If `ref` is not pinned, consumer is in a broken state (can't install / update) on default branch.

### Common observation across 4.A/B/C

All three approaches **hold the consumer back** at the most-recent release between releases, by design — this is exactly what `m5-plugin-distribution-and-symlink-retire/D2` ("explicit semver-via-tags pre-v1") commits to. None of A/B/C creates a "consumer pulled forward by every dev-merge" failure mode.

The dev-tip-vs-release window is a release-cadence question, not a deployment-pattern question. Per `code.claude.com/docs/en/plugins-reference:1004-1008`, **as long as the version string doesn't change, consumers don't get updates**. All three approaches honor this.

The novel-to-Approach-B concern is the *coupling* between npm-publish and marketplace.json bump — i.e., a maintainer can publish to npm without bumping `marketplace.json`'s pinned version, leaving a published-but-unreferenced version. Approach A's coupling is cleaner (one push to `release` materialises `dist/` and bumps `version`); Approach C has the same two-step coupling as B (tag push + marketplace.json `ref` bump).

---

## Boundary inventory

For each distinct boundary surfaced above, classified by type, with per-approach scoring (clean / awkward / unmechanized).

### Session boundaries

#### B1 — Marketplace fetch (consumer's `/plugin marketplace add` clones cairn's repo)

- **Next session needs to know**: location of `marketplace.json` in the cloned tree (`.claude-plugin/marketplace.json`).
- **Information transit**: git clone of cairn at default branch (or `@ref` if specified), into `~/.claude/plugins/marketplaces/cairn-marketplace/`.
- **A**: awkward — needs `@release` qualifier in the marketplace-add URL, or a default-branch change. Today's `README.md:19` lacks this qualifier.
- **B**: clean — marketplace.json lives on `dev` (default branch), no `@ref` needed.
- **C**: clean — marketplace.json lives on `dev` (default branch), no `@ref` needed.

#### B2 — Plugin install (consumer's `/plugin install` resolves payload)

- **Next session needs to know**: where the plugin payload lives — relative path in marketplace clone, github repo+ref+(optional)path, or npm package+version.
- **Information transit**: parsed `source` object in `marketplace.json`.
- **A**: clean if `source.source: "github"` with `ref: "release"`. Awkward if `source` is the relative-path string `./dist` (incompatible with marketplace-on-`dev` if `dist/` is git-ignored). Unmechanized if today's `source.type: "git"` schema is kept (not a documented value).
- **B**: clean — `source.source: "npm"` is documented; consumer-side `npm` is the only friction.
- **C**: clean — `source.source: "git-subdir"` is documented and explicitly designed for "subdirectory of a git repo at a tag".

#### B3 — Hook/skill/agent registration

- **Next session needs to know**: hooks.json path, skills/agents directories.
- **Information transit**: `dist/.claude-plugin/plugin.json` + plugin-cache layout. Hooks fire via `${CLAUDE_PLUGIN_ROOT}` substitution.
- **A/B/C all clean**: this boundary is downstream of the deployment pattern; once the payload arrives in the cache, registration is identical.

#### B4 — Session restart for hook/agent reload

- **Next session needs to know**: that a restart is required after install.
- **Information transit**: documented in `docs/upgrading-from-symlink.md:74-77`; not enforced mechanically.
- **A/B/C all clean** (same mechanism for all).

### Artifact boundaries

#### B5 — `dist/` build (canonical sources → curated payload)

- **Producer**: `scripts/build_dist.py` (`scripts/build_dist.py:18-33` allow-list).
- **Consumer**: deployment step (push to release branch / npm publish / git-subdir tag commit).
- **What if missing/malformed**: `dist-gate.yml` already validates the build (`.github/workflows/dist-gate.yml:23-27`); if `build_dist.py` raises `FileNotFoundError`, CI fails. **This boundary is mechanized for all three approaches** — it's the same build script.
- **A/B/C all clean** — F1's existing CI suffices.

#### B6 — Deployment (pushed `dist/` → consumer-resolvable ref)

- **Producer**: release workflow (CI or human).
- **Consumer**: `/plugin install` resolution (B2).
- **What if missing/malformed**: today this boundary has no producer at all (audit check 9 PENDING gap). The producer is what each approach proposes.
- **A**: awkward — requires `release` branch creation, force-push or replace-tree mechanics, GitHub Actions write-perm to `release`. Each release commits `dist/` to `release` branch. Mechanism is built (custom GitHub Action workflow), but composition is novel — every release modifies file-tracked state in a separate branch.
- **B**: clean for ergonomics — `npm publish` is well-known; `NPM_TOKEN` in CI is a one-time setup. Awkward for cairn's identity — adds an external dependency (npm registry) beyond what cairn's standing dep set permits per `CLAUDE.md` "post-M4 standing dep set as the only allowed dependencies".
- **C**: clean — git-tag with `dist/` materialised at the tagged commit; `git-subdir` resolution is the documented mechanism.

#### B7 — `marketplace.json` (catalog + plugin source pointer)

- **Producer**: cairn maintainer (committed to `dev`).
- **Consumer**: Claude Code's `/plugin marketplace add` and `/plugin install` resolution.
- **What if missing/malformed**: `code.claude.com/docs/en/plugin-marketplaces:947` "Ensure JSON syntax is valid... using `claude plugin validate`". Today's `source.type: "git"` is not in the documented schema; the validator may or may not surface this — see Gap 8.
- **A**: awkward — must use `source.source: "github"` with `ref: "release"`, not relative-path; schema change from today.
- **B**: awkward — `source.source: "npm"` requires npm-publish workflow; schema change from today.
- **C**: awkward — `source.source: "git-subdir"` with `ref: "v0.x.y"`; schema change from today, but most-natural fit for cairn-D2 ("explicit semver-via-tags").

#### B8 — `dist/.claude-plugin/plugin.json` `version` field

- **Producer**: cairn maintainer / CI on release.
- **Consumer**: Claude Code's update-detection logic (`code.claude.com/docs/en/plugins-reference:991-1011`).
- **What if missing/malformed**: per `code.claude.com/docs/en/plugins-reference:993-1008`, fall-back order is plugin.json > marketplace entry > git SHA > "unknown". Setting `version` in plugin.json silently overrides marketplace entry.
- **A**: clean — every push to `release` includes a bumped `dist/.claude-plugin/plugin.json` version.
- **B**: awkward — `version` in plugin.json (inside `dist/`) AND `marketplace.json` plugin entry's `version` AND the npm-published version must all agree. Three places to bump. `code.claude.com/docs/en/plugin-marketplaces:715-718` warns about plugin.json silently overriding marketplace.json.
- **C**: clean — `marketplace.json`'s `source.ref` is the consumer-facing version handle; plugin.json's `version` is the secondary handle. Two places to keep aligned, but they live in the same commit (the tagged commit).

### State transitions

#### B9 — Symlink → plugin install (Role 2 atomic swap)

- **From**: consumer with `.slice-system` symlink and `$CLAUDE_PROJECT_DIR/.slice-system/checks/...` settings.json hooks.
- **To**: consumer with no `.slice-system`, plugin-cache hooks via `${CLAUDE_PLUGIN_ROOT}/...`.
- **Mechanism**: `scripts/migrate_from_symlink.sh` (lines 39-52 banner; lines 132+ jq filter pass) plus operator-run `/plugin install`.
- **A/B/C all clean** at the migration mechanics — the runbook is approach-agnostic. Approach-specific frictions in the install step itself surface in B1/B2.

#### B10 — Release-branch state advance (Approach A only)

- **From**: `release` branch at version `v0.x.(y-1)`.
- **To**: `release` branch at version `v0.x.y`.
- **Mechanism**: CI workflow that builds `dist/`, replaces `release` tree, commits, pushes, optionally tags.
- **A**: unmechanized today — must be built. Composition: actions/checkout to `release`, run `build_dist.py --dist-root .` after `git rm -r dist/` (or maintain `release` as `dist/` content directly), commit, push. Race conditions if two releases overlap (mitigate via concurrency: 1 in workflow). Force-push to `release` is governed by cairn's force-push policy (`CLAUDE.md` "Force-push policy: blocked unless --force-with-lease").
- **B/C**: not applicable.

#### B11 — npm-publish state advance (Approach B only)

- **From**: npm registry has `@firaaz/cairn@0.x.(y-1)` as latest.
- **To**: npm registry has `@firaaz/cairn@0.x.y` as latest.
- **Mechanism**: CI workflow runs `npm publish` against curated payload.
- **A/C**: not applicable.
- **B**: clean for ergonomics; adds external system (npm registry) outside cairn's control. Tags don't move (npm publishes are immutable per-version), which honors cairn-D2.

#### B12 — Tag creation state advance (Approach C only)

- **From**: cairn.git has tags up to `v0.x.(y-1)`.
- **To**: cairn.git has tags up to `v0.x.y`, the new tag pointing at a commit with `dist/` materialised.
- **Mechanism**: CI workflow builds `dist/`, commits to a release-only commit (or temp branch), tags, pushes tag.
- **A/B**: not applicable.
- **C**: unmechanized today — must be built. The tag must point at a commit that has `dist/` (a `dev` commit doesn't have `dist/`). Conceptually clean but requires deciding: does the release commit live on a branch (and which?) or is it a detached commit only reachable via tag?

#### B13 — Marketplace.json schema validity transition

- **From**: today's `source.type: "git", url: ..., path: "dist/"` (not in documented schema).
- **To**: a documented `source.source: <github|url|git-subdir|npm>` shape.
- **A**: must transition to `source.source: "github", repo: "firaaz/cairn", ref: "release"`.
- **B**: must transition to `source.source: "npm", package: "@firaaz/cairn", version: "0.x.y"`.
- **C**: must transition to `source.source: "git-subdir", url: "...", path: "dist", ref: "v0.x.y"`.

This is a pre-existing schema bug in today's manifest, **independent of approach choice**. All three approaches require fixing it. See Gap 8.

---

## Gaps

Gaps are steps where the answer in current docs/code is "the user will figure it out" — surfaced numerically for Phase 1 to address.

1. **Default-branch ambiguity for marketplace fetch (Approach A only).** Today's `README.md:19` and `CONSUMER.md:14` literal command is `/plugin marketplace add https://github.com/firaaz/cairn` — no `@ref`. Under Approach A with marketplace.json on `release` only, this fails because `dev` (default branch) has no marketplace.json. The user must guess to add `@release`, OR cairn must change the default branch from `dev` to `release`. Neither is currently documented.

2. **Maintainer dogfood under default-branch change (Approach A only).** If Approach A solves Gap 1 by changing default branch to `release`, cairn-the-repo's own dogfood loop is affected. Maintainers cloning cairn for dev work expect `dev` as default. Forcing default-branch to `release` for plugin-discovery friendliness is a non-trivial repo-management decision (impacts every PR target, every fresh clone). Today's `m5-plugin-distribution-and-symlink-retire/D8` does not address this.

3. **`@ref` qualifier vs `extraKnownMarketplaces` (cross-approach).** An alternative to default-branch change is documenting that consumers always use `@ref`. But the literal consumer-facing instruction in `README.md:19` does not. If A is chosen, this is a docs-update boundary — must rewrite README + CONSUMER.md + upgrading-from-symlink.md install instructions.

4. **npm-binary presence on consumer side (Approach B only).** Approach B requires consumers to have `npm` on PATH. cairn's existing system-dep contract names only `jq` and `ruff` (`CLAUDE.md:13-15`). No documented preflight check for `npm`. Phase 1 must address: do all current/expected consumers have npm? `complex-rag-analysis` is a Python uv project — npm presence is not guaranteed.

5. **Detached-commit reachability under git-subdir + tag (Approach C only).** If the release-only commit (with `dist/` materialised) lives only as a tagged orphan and never on a branch, normal `git pull` doesn't surface it. This is fine for `/plugin install` (it resolves the tag explicitly) but unusual for git-tooling ergonomics — `git log --all` shows it, `git branch --contains <tag>` returns empty. This may surface as a "what is this commit doing?" friction for future maintainers. Decision: keep a `release` branch (collapses with A's release-branch shape) or accept detached tags?

6. **Two-step release coupling (Approaches B and C only).** Both require: (i) deploy the artefact (npm publish / push tag), AND (ii) update `marketplace.json`'s pinned version on `dev`. If a maintainer does (i) but forgets (ii), consumers don't see the new version. Approach A's release is one push (to `release` branch, which mutates both `dist/` and `dist/.claude-plugin/plugin.json` `version` in one commit). Phase 1 must address: how is the two-step coupling enforced?

7. **CI-credential decision unmechanized (cross-approach).** Each approach needs different CI secrets:
   - A: write access to `release` branch (above default `GITHUB_TOKEN` for protected branches; needs a PAT or app-token if `release` is protected).
   - B: `NPM_TOKEN` scoped to `@firaaz/`.
   - C: write access to push tags (default `GITHUB_TOKEN` typically suffices, but tag-protection rules vary).
   None of these are mentioned in current cairn docs/CI.

8. **Today's `marketplace.json` schema is not documented (cross-approach pre-existing bug).** `.claude-plugin/marketplace.json:11` declares `"type": "git"`, but `code.claude.com/docs/en/plugin-marketplaces:231-238` does not list `"git"` as a valid `source.source` value, AND the discriminator field is `source.source` not `source.type`. The current manifest may not parse at all on a real `/plugin install` attempt — F3's audit check 9 may fail before even getting to the missing-`dist/` symptom. **All three approaches must fix this.** Phase 1 should treat the schema correction as a structural necessity independent of A/B/C selection.

9. **`source.ref` vs `source.sha` semantics (Approach C only).** `code.claude.com/docs/en/plugin-marketplaces:285-288, 311-321, 360-366` show `ref` and `sha` are independent fields. cairn-D2's "consumers pin SHAs/tags" is satisfied by either, but the maintainer cannot pin both — `marketplace.json` carries one or the other. Tag-pin (`ref: "v0.x.y"`) is more readable; SHA-pin is more immutable (tags can theoretically be force-moved). Approach C must pick.

10. **`/plugin update` cache-key behaviour with omitted `version` (Approaches B and C variant).** `code.claude.com/docs/en/plugins-reference:993-998` says without explicit `version`, git-based sources fall back to git commit SHA, but npm sources fall back to "unknown". Under Approach C with omitted `source.ref`, default-branch tracking applies and git SHA changes pull consumers forward on every `dev` commit — which **violates cairn-D2's "pin SHAs/tags"** stance. Approach C must require `source.ref` to be set; an omit-`ref` failure mode where consumers track `dev` is a footgun.

11. **Cross-cutting Approach D: combination/hybrid not enumerated.** The brief says "Phase 2 is allowed to propose a fourth approach". The most-natural hybrid is **A + C**: a `release` branch tracks the latest release's `dist/` (for marketplace.json `source.source: "github" ref: "release"` resolution) AND tagged commits on that branch carry `v0.x.y` for SHA-pinning. This satisfies both "consumers can pin to a tag" (cairn-D2) and "default-branch consumers get a stable cut" (4.A's structural property). Not enumerated by the operator; surfaced here for Phase 2 to consider.

---

## Resolution mechanism evidence

Verbatim citations from `code.claude.com/docs/en/plugins-reference` (line numbers refer to the persisted fetched copy at `/Users/firaazfarook/.claude/projects/-Users-firaazfarook-Developer-github-com-firaaz-cairn/27b02b3d-d03a-472e-b488-47fe405faa17/tool-results/toolu_01TRvmZpjBBe2s78MEBoPFoi.txt`) and `code.claude.com/docs/en/plugin-marketplaces` (line numbers refer to the persisted fetched copy at `.../toolu_01DBYceYL9sVYhgZvdV6NmRE.txt`).

### Evidence 1 — Documented `source.source` values

`code.claude.com/docs/en/plugin-marketplaces:231-238`:

> | Source        | Type                            | Fields                             | Notes                                                                                                                                             |
> | ------------- | ------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
> | Relative path | `string` (e.g. `"./my-plugin"`) | none                               | Local directory within the marketplace repo. Must start with `./`. Resolved relative to the marketplace root, not the `.claude-plugin/` directory |
> | `github`      | object                          | `repo`, `ref?`, `sha?`             |                                                                                                                                                   |
> | `url`         | object                          | `url`, `ref?`, `sha?`              | Git URL source                                                                                                                                    |
> | `git-subdir`  | object                          | `url`, `path`, `ref?`, `sha?`      | Subdirectory within a git repo. Clones sparsely to minimize bandwidth for monorepos                                                               |
> | `npm`         | object                          | `package`, `version?`, `registry?` | Installed via `npm install`                                                                                                                       |

**Implication**: there is no `"git"` value documented. cairn's current `marketplace.json:11` `"type": "git"` is structurally not in the documented schema. Discriminator field is `source.source` (not `source.type`).

### Evidence 2 — `source.path` resolution under `git-subdir`

`code.claude.com/docs/en/plugin-marketplaces:331`:

> Use `git-subdir` to point to a plugin that lives inside a subdirectory of a git repository. Claude Code uses a sparse, partial clone to fetch only the subdirectory, minimizing bandwidth for large monorepos.

`code.claude.com/docs/en/plugin-marketplaces:361-366`:

> | Field  | Type   | Description                                                                                              |
> | :----- | :----- | :------------------------------------------------------------------------------------------------------- |
> | `url`  | string | Required. Git repository URL, GitHub `owner/repo` shorthand, or SSH URL                                  |
> | `path` | string | Required. Subdirectory path within the repo containing the plugin (for example, `"tools/claude-plugin"`) |
> | `ref`  | string | Optional. Git branch or tag (defaults to repository default branch)                                      |
> | `sha`  | string | Optional. Full 40-character git commit SHA to pin to an exact version                                    |

**Implication**: under `git-subdir`, `path` is required. `ref` defaults to **repository default branch**. `path` is resolved against the cloned/fetched ref's tree.

### Evidence 3 — `source.ref` defaults across types

`code.claude.com/docs/en/plugin-marketplaces:294`:

> | `ref`  | string | Optional. Git branch or tag (defaults to repository default branch)                              |

(For `github` source.) Same default-to-default-branch language at lines 326, 365 for `url` and `git-subdir` types.

**Implication**: omitting `ref` does NOT pin to a tag. It tracks the moving HEAD of the default branch, pulling consumers forward on every commit — incompatible with `m5-plugin-distribution-and-symlink-retire/D2`'s "pin SHAs/tags" stance.

### Evidence 4 — error message when `path` doesn't exist on the resolved ref

`code.claude.com/docs/en/plugins-reference:929`:

> `Plugin directory not found at path: ./plugins/my-plugin. Check that the marketplace entry has the correct path.`

**Implication**: missing `dist/` on the resolved ref produces a specific error message. Today, with `marketplace.json` `path: "dist/"` and `dist/` git-ignored on `dev`, this is the error consumers would see (modulo Gap 8's parse-time issue).

### Evidence 5 — npm source mechanics and consumer-side `npm` requirement

`code.claude.com/docs/en/plugin-marketplaces:368-370`:

> ### npm packages
>
> Plugins distributed as npm packages are installed using `npm install`. This works with any package on the public npm registry or a private registry your team hosts.

`code.claude.com/docs/en/plugin-marketplaces:409-413`:

> | Field      | Type   | Description                                                                                  |
> | :--------- | :----- | :------------------------------------------------------------------------------------------- |
> | `package`  | string | Required. Package name or scoped package (for example, `@org/plugin`)                        |
> | `version`  | string | Optional. Version or version range (for example, `2.1.0`, `^2.0.0`, `~1.5.0`)                |
> | `registry` | string | Optional. Custom npm registry URL. Defaults to the system npm registry (typically npmjs.org) |

**Implication**: "installed using `npm install`" — the docs do not specify whether Claude Code shells out to consumer-side `npm` or uses an embedded npm. Most natural reading is consumer-side npm, because (a) `registry` field defaults to the **system** npm registry, suggesting npm-config is read from the host, and (b) `code.claude.com/docs/en/plugin-marketplaces:998` reports "unknown" version for npm sources without explicit version, suggesting Claude Code reads npm's resolution output rather than enforcing its own. **Phase 1 should challenge this assumption** if Approach B is selected — the docs are ambiguous here.

### Evidence 6 — `/plugin marketplace add` ref qualifier

`code.claude.com/docs/en/plugin-marketplaces:842`:

> * `<source>`: GitHub `owner/repo` shorthand, git URL, remote URL to a `marketplace.json` file, or local directory path. To pin to a branch or tag, append `@ref` to the GitHub shorthand or `#ref` to a git URL

`code.claude.com/docs/en/plugin-marketplaces:858-861`:

> Pin to a specific branch or tag with `@ref`:
>
> ```bash theme={null}
> claude plugin marketplace add acme-corp/claude-plugins@v2.0
> ```

**Implication**: `/plugin marketplace add` defaults to repository's default branch when no `@ref` is appended. Approach A's "marketplace.json on `release` branch only" requires consumers to write `@release` — `README.md:19`'s literal command does not include this.

### Evidence 7 — version resolution and update detection

`code.claude.com/docs/en/plugin-marketplaces:706-712`:

> Claude Code resolves a plugin's version from the first of these that is set:
>
> 1. `version` in the plugin's `plugin.json`
> 2. `version` in the plugin's marketplace entry
> 3. The git commit SHA of the plugin's source
>
> For the git-based source types `github`, `url`, `git-subdir`, and relative paths inside a git-hosted marketplace, you can omit `version` entirely and every new commit is treated as a new version. This is the simplest setup for internal or actively-developed plugins.

`code.claude.com/docs/en/plugins-reference:993-998`:

> The version is resolved from the first of these that is set:
>
> 1. The `version` field in the plugin's `plugin.json`
> 2. The `version` field in the plugin's marketplace entry in `marketplace.json`
> 3. The git commit SHA of the plugin's source, for `github`, `url`, `git-subdir`, and relative-path sources in a git-hosted marketplace
> 4. `unknown`, for `npm` sources or local directories not inside a git repository

**Implication for Approach B (npm)**: omitting `version` on npm sources falls back to `"unknown"`, which breaks update detection. For B, an explicit `version` (matching the npm-published version) is mandatory.

**Implication for Approaches A and C (git-based)**: omitting `version` falls back to git SHA — which means **every commit on the source ref pulls consumers forward**. Under A with `ref: "release"`, that's once-per-release (acceptable). Under C with `ref: "v0.x.y"`, tags don't move so SHA is stable (acceptable). Under either approach with omitted `ref`, consumers track default branch — every `dev` commit pulls consumers forward, **violating cairn-D2**.

### Evidence 8 — explicit-version pin behaviour

`code.claude.com/docs/en/plugins-reference:1004-1008`:

> | **Explicit version**   | Set `"version": "2.1.0"` in `plugin.json`                        | Users get updates only when you bump this field. Pushing new commits without bumping it has no effect, and `/plugin update` reports "already at the latest version". | Published plugins with stable release cycles      |

`code.claude.com/docs/en/plugins-reference:1007`:

> | **Commit-SHA version** | Omit `version` from both `plugin.json` and the marketplace entry | Users get updates on every new commit to the plugin's git source                                                                                                     | Internal or team plugins under active development |

**Implication**: cairn's stated stance per `m5-plugin-distribution-and-symlink-retire/D2` ("explicit semver-via-tags") aligns with the **explicit version** row. Setting `dist/.claude-plugin/plugin.json` `version` to `"0.x.y"` and bumping it on every release is the documented path. Approaches A and C support this naturally; Approach B requires alignment between npm-published version, marketplace.json entry version, and plugin.json version.

### Evidence 9 — plugin.json wins over marketplace entry silently

`code.claude.com/docs/en/plugin-marketplaces:715-718`:

> Avoid setting `version` in both `plugin.json` and the marketplace entry. The `plugin.json` value always wins silently, so a stale manifest version can mask a version you set in `marketplace.json`.

**Implication**: in cairn's case, `dist/.claude-plugin/plugin.json` is the authority for `version`, not `marketplace.json`. The CI release workflow (under any approach) must bump `dist/.claude-plugin/plugin.json` `version` — not just `marketplace.json`. F1's `build_dist.py` copies `.claude-plugin/plugin-template.json` → `dist/.claude-plugin/plugin.json` (`scripts/build_dist.py:30`), so the version-bump source is the template file.

### Evidence 10 — plugin caching mechanics (downstream of all approaches)

`code.claude.com/docs/en/plugins-reference:619`:

> For security and verification purposes, Claude Code copies *marketplace* plugins to the user's local **plugin cache** (`~/.claude/plugins/cache`) rather than using them in-place.

`code.claude.com/docs/en/plugins-reference:621`:

> Each installed version is a separate directory in the cache. When you update or uninstall a plugin, the previous version directory is marked as orphaned and removed automatically 7 days later. The grace period lets concurrent Claude Code sessions that already loaded the old version keep running without errors.

**Implication**: post-fetch, all three approaches converge on identical cache mechanics. The deployment-pattern decision is upstream of plugin-cache handling.

### Evidence 11 — relative path resolution

`code.claude.com/docs/en/plugin-marketplaces:259`:

> Paths resolve relative to the marketplace root, which is the directory containing `.claude-plugin/`. In the example above, `./plugins/my-plugin` points to `<repo>/plugins/my-plugin`, even though `marketplace.json` lives at `<repo>/.claude-plugin/marketplace.json`. Do not use `../` to reference paths outside the marketplace root.

**Implication for Approach A with relative-path source**: `./dist` resolves against the marketplace's clone (i.e., the marketplace repo at the marketplace's `@ref` — which is the **same repo and same ref** as the marketplace clone). This is what makes Option 3.A.ii structurally inconsistent: if the marketplace lives on `dev` (default branch) and uses `./dist`, then `./dist` resolves on `dev`, where `dist/` is git-ignored. **Approach A cannot use a relative-path source if `dist/` is not on the marketplace's resolved ref.** Must use `github` source object with explicit `ref: "release"`.

### Evidence 12 — update-fetch trigger

`code.claude.com/docs/en/plugin-marketplaces:925`:

> Refresh marketplaces from their sources to retrieve new plugins and version changes.

`code.claude.com/docs/en/plugin-marketplaces:1004-1006`:

> By default, when a `git pull` fails, Claude Code removes the stale clone and attempts to re-clone. In offline or airgapped environments, re-cloning fails the same way, leaving the marketplace directory empty.

**Implication**: `/plugin update` re-pulls the marketplace, then re-resolves the plugin source. Under all three approaches, the consumer's update path is:

```
/plugin update cairn@cairn-marketplace
  → re-pull cairn-marketplace clone (on default branch + @ref if any)
  → re-parse marketplace.json
  → re-resolve plugin source per source.* fields
  → install if version changed
```

The consumer-side mechanics are identical; the maintainer-side mechanics differ.

---

## Summary tables

### Per-approach boundary scoring

| Boundary | A (release-branch) | B (npm) | C (git-subdir + tag) |
|---|---|---|---|
| B1 marketplace fetch | awkward (needs @release qualifier or default-branch change) | clean | clean |
| B2 plugin install | clean if `github` source w/ `ref: release`; awkward if relative-path | clean (npm requires consumer-side npm) | clean |
| B3 hook/skill/agent registration | clean | clean | clean |
| B4 session restart | clean | clean | clean |
| B5 `dist/` build | clean (F1 already shipped) | clean | clean |
| B6 deployment | awkward (custom CI to push to `release`) | clean for ergonomics, awkward for cairn identity (external dep) | clean |
| B7 marketplace.json | awkward (schema change to `github`+`ref`) | awkward (schema change to `npm`) | awkward (schema change to `git-subdir`) |
| B8 plugin.json version | clean | awkward (3-way version alignment) | clean (2-way alignment, same commit) |
| B9 symlink → plugin install transition | clean (runbook agnostic) | clean | clean |
| B10 release-branch state advance | unmechanized (must build CI) | n/a | n/a |
| B11 npm-publish state advance | n/a | clean (well-known mechanism) | n/a |
| B12 tag-creation state advance | n/a | n/a | unmechanized (must build CI) |
| B13 marketplace.json schema validity | required transition | required transition | required transition |

### Per-approach gap incidence

| Gap | A | B | C |
|---|---|---|---|
| 1. Default-branch ambiguity for marketplace fetch | applies | does not apply | does not apply |
| 2. Maintainer dogfood under default-branch change | applies | does not apply | does not apply |
| 3. `@ref` qualifier vs `extraKnownMarketplaces` | applies | does not apply | does not apply |
| 4. npm-binary on consumer side | does not apply | applies | does not apply |
| 5. Detached-commit reachability | does not apply | does not apply | applies |
| 6. Two-step release coupling | does not apply | applies | applies |
| 7. CI-credential decision unmechanized | applies | applies | applies |
| 8. Today's marketplace.json schema not documented | applies | applies | applies |
| 9. `source.ref` vs `source.sha` semantics | applies | does not apply | applies |
| 10. `/plugin update` cache-key behaviour | does not apply | applies | applies |
| 11. Cross-cutting Approach D hybrid | n/a (informational) | n/a (informational) | n/a (informational) |

---

## Closing observation

The deployment pattern is decoupled from the four-stage transit's downstream stages (cache, registration, restart, dispatch). All three approaches produce identical consumer-experience post-install. The choice is upstream — at the maintainer's release-author surface and at the marketplace.json schema's `source.source` field.

The most novel role's journey (Role 3) reveals the deepest divergence: A demands a long-lived `release` branch with custom CI to push curated payloads; B demands an external registry relationship and a 3-way version-alignment discipline; C demands a tag-creation CI workflow with a release-only commit but reuses the existing repo without an additional branch.

The deceptively-stable common boundary across all three (B5 `dist/` build) is already mechanized — F1's `scripts/build_dist.py` and `dist-gate.yml` are reusable as the "build" half of any approach. The unmechanized work is uniformly the "deploy" half — B6 — which is exactly where audit check 9 PENDING surfaces.

End of trace.
