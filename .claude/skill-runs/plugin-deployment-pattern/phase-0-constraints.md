# Phase 0 — Constraint Envelope

Decision: "Plugin deployment pattern: how does `dist/` reach a ref consumers can resolve via `/plugin install`?"

Source: Phase 0 subagent run, 2026-05-09. Categorisations: **HARD** = architectural invariant; **SOFT** = strong preference; **CONTEXT** = bounding background.

External-docs note: schema evidence is taken from the Anthropic plugins reference and plugin-marketplaces guide (`code.claude.com/docs/en/plugins-reference` and `code.claude.com/docs/en/plugin-marketplaces`, fetched 2026-05-09). Citations carry section anchors / line numbers from the fetched markdown rendition where available.

## DEPLOYMENT MECHANISM

1. **[HARD]** `dist/` does NOT currently exist in any committed ref of `firaaz/cairn`. Local checkout has no `dist/` directory; `git ls-tree -r HEAD` returns no `dist/...` paths; `git log --all --diff-filter=A -- 'dist/*'` is empty. F1 packaging shipped a build script + manifest pointing at `dist/`, but never committed the build output anywhere consumers can reach. Source: `git ls-tree -r HEAD` (run 2026-05-09); `git log --all --oneline -- 'dist/'` (empty). This is the named gap (handoff `bfef6e5`; brief lines 11–13).

2. **[HARD]** `dist/` is NOT in `.gitignore`. The reason `dist/` is missing from refs is "the build was never run + committed," not "git is excluding it." Any deployment mechanism that wants `dist/` ignored on the default branch must add an explicit ignore rule. Source: `.gitignore` (only `.venv/` is listed).

3. **[HARD]** `scripts/build_dist.py` produces the payload from a 14-row `ALLOW_LIST` with hard refusal to traverse `.slice-system → .` (CLAUDE.md symlink-recursion hazard). Build output goes wherever `--dist-root` points (default `<repo>/dist`); script does not commit, push, tag, or publish. Source: `scripts/build_dist.py:18-33,42-58,71-78`.

4. **[HARD]** `.github/workflows/dist-gate.yml` validates the build (`build_dist.py --dist-root /tmp/dist-ci` + allow-list assertions + post-install validator self-test) but has NO step that commits, pushes, tags, releases, or publishes the artifact. CI fires on `pull_request` and `push` to `dev`/`main`. Source: `.github/workflows/dist-gate.yml:3-32`.

5. **[HARD]** `.claude-plugin/marketplace.json` currently declares `{"type": "git", "url": "...", "path": "dist/"}` — the discriminator field used is `type`, but the documented schema uses `source` as the discriminator. The four documented `source.source` values are `github`, `url`, `git-subdir`, `npm`; relative-path strings are also accepted. **`type: git` does not appear in the documented marketplace schema.** Source: `.claude-plugin/marketplace.json:10-14`; `code.claude.com/docs/en/plugin-marketplaces` source-types table (lines 234–237 of fetched doc).

6. **[CONTEXT]** Whether cairn's current `type: git` is a working alias for `source: url`, an undocumented synonym, or actually-broken-but-no-one-tested is itself unknown. The schema docs show four `source.source` values (`github`, `url`, `git-subdir`, `npm`); none is `git`. Whatever the deployment pattern, the manifest will need to be reconciled with the documented schema or risk silent install failures. Source: `code.claude.com/docs/en/plugin-marketplaces:231-237` (Plugin sources table); `.claude-plugin/marketplace.json:10-14`.

## VERSIONING / STABILITY

7. **[HARD]** D2 (`m5-plugin-distribution-and-symlink-retire/D2`) commits to explicit semver-via-tags pre-v1: `dist/.claude-plugin/plugin.json` carries `"version": "0.x.y"`; tags follow `v0.x.y`; consumers pin via `marketplace.json` `source.ref` (tag) or `source.sha` (commit); cairn commits to bumping on every consumer-visible change. Source: `docs/adr/m5-plugin-distribution-and-symlink-retire.md:51-53`.

8. **[HARD]** Plugin template currently declares `"version": "0.1.0"`. Per the docs' version-resolution rules, when `version` is set in `plugin.json`, the version field is the cache key — pushing new commits without bumping it means consumers see "already at the latest version". Source: `.claude-plugin/plugin-template.json:3`; `code.claude.com/docs/en/plugins-reference:1004,1007-1009`.

9. **[HARD]** Per-source version-resolution semantics differ. For `github`/`url`/`git-subdir` and relative-path sources in a git-hosted marketplace, omitting `version` from both `plugin.json` and the marketplace entry causes the git commit SHA to be used as the version string (every new commit = new version). For `npm` sources the resolver returns `unknown` if no version is set; effectively this means npm REQUIRES an explicit version. Source: `code.claude.com/docs/en/plugins-reference:993-998`.

10. **[CONTEXT]** "Release channels" are a documented pattern: two marketplaces (`stable` / `latest`) point at different refs (e.g. `ref: stable` vs `ref: latest`) of the same repo. This is the canonical Anthropic-blessed shape for branch-based versioning. Source: `code.claude.com/docs/en/plugin-marketplaces:720-786` (Set up release channels).

11. **[SOFT]** Six amendment ADRs (`cost-per-slice-budget`, `parallelism-v1`, `phase-pipeline-evaluation`, `feature-slice-model`, `context-tiers-integration`, `identifier-scheme`) gate v1; until they close, cairn ships as `v0.x.y`. Whatever deployment mechanism lands must survive the eventual `0.x.y → 1.0.0` cut without forcing consumer-side rework. Source: `docs/adr/m5-plugin-distribution-and-symlink-retire.md:53,132`.

## MARKETPLACE.JSON SCHEMA

12. **[HARD]** Documented `source.source` values, exhaustively, are: `github` (fields: `repo` required, `ref?`, `sha?`), `url` (fields: `url` required, `ref?`, `sha?`), `git-subdir` (fields: `url` required, `path` required, `ref?`, `sha?`), `npm` (fields: `package` required, `version?`, `registry?`). Relative-path strings (e.g. `"./plugins/foo"`) are also accepted as a literal-string `source` value. Source: `code.claude.com/docs/en/plugin-marketplaces:231-413`.

13. **[HARD]** `source.path` is meaningful only for `git-subdir` (and for relative-string sources, where it is the entire string). For `github` / `url`, the schema has no `path` field documented — the entire repo at the resolved ref IS the plugin root. Source: `code.claude.com/docs/en/plugin-marketplaces:231-327` (no `path` row in `github`/`url` field tables; `git-subdir` table at lines 361–366 lists `path` as required).

14. **[HARD]** `git-subdir` clones sparsely (partial clone) to fetch only the subdirectory, "minimizing bandwidth for large monorepos". This is the only documented `source.*` shape that natively combines "git repo + subdirectory" semantics. Source: `code.claude.com/docs/en/plugin-marketplaces:329-331`.

15. **[HARD]** `source.ref` accepts a git branch or tag (defaults to repository default branch when omitted); `source.sha` accepts a full 40-character commit SHA. Both are pinning fields; the schema does not document semver-range syntax for `ref`/`sha` (semver ranges only appear on `npm.version`). Source: `code.claude.com/docs/en/plugin-marketplaces:291-295,322-327,361-366`.

16. **[HARD]** `npm.version` accepts semver ranges (`2.1.0`, `^2.0.0`, `~1.5.0`); `npm.registry` is optional (defaults to system npm registry). Installation is via `npm install`. Source: `code.claude.com/docs/en/plugin-marketplaces:368-413`.

17. **[CONTEXT]** **Release-archive / GitHub-releases / tarball-download is NOT a documented source type.** A search across the marketplace docs returned zero hits for `tarball`, `release`, `archive` as schema field names. Approach C (operator-named "GitHub release + git-subdir") is therefore mechanism-ambiguous: `git-subdir` clones a git ref, it does not download a release tarball. The "GitHub release" and "git-subdir" parts of Approach C address different things; the schema does not natively support release-artifact downloads. Source: `code.claude.com/docs/en/plugin-marketplaces:225-413` (full sources section); absence of any `tarball`/`release` field in source-type tables.

18. **[CONTEXT]** Marketplace sources vs plugin sources are documented as different concepts. Marketplace source supports `ref` but **not** `sha`; plugin source supports both. So a user typing `/plugin marketplace add owner/repo@ref` is pinning the catalog, not the plugin; the catalog then resolves each plugin's `source` independently. Source: `code.claude.com/docs/en/plugin-marketplaces:239-246`.

19. **[CONTEXT]** Relative-path plugin sources only resolve correctly when users add the marketplace via Git (GitHub/GitLab/git URL). If the marketplace is added via a direct URL to `marketplace.json`, relative paths break — Anthropic explicitly recommends switching to `github`/`url`/`npm` for URL-based distribution. This affects whether `marketplace.json` should ever rely on a `path: "dist/"`-style relative-resolution shape. Source: `code.claude.com/docs/en/plugin-marketplaces:261-263` (Note callout).

## CI / RELEASE CADENCE

20. **[HARD]** CI today runs `dist-gate` on every PR and on push to `dev`/`main`; build is exercised but never persisted. Any chosen deployment pattern must add a *publish* step (commit-to-branch, push-tag, npm-publish, or release-attach) that fires on the right trigger (tag push? release event? merge to release branch?). Source: `.github/workflows/dist-gate.yml:1-32`.

21. **[HARD]** INV-001 binds: every commit since `2fb83f6` carries a Conventional Commits prefix recognised in `_FALLBACK_REGISTRY`. Any CI step that auto-commits `dist/` content (e.g., a sync action) MUST emit a registered prefix or have its prefix added to the registry via superseding ADR. Source: `docs/ARCHITECTURE.md:13-20`; `CLAUDE.md:5-7`.

22. **[HARD]** ADRs are append-only (CLAUDE.md safety-critical rule); `reversibility-guard.sh` permits `Write` on new ADRs and frontmatter-only `Edit` on existing ones. If the chosen deployment requires amending `m5-plugin-distribution-and-symlink-retire/D3` rather than writing a new ADR, the amendment lands as a frontmatter-only edit (`status:`/`firmness:`/`superseded-by:`) plus a co-landed superseding-or-amending ADR — not as a body-prose edit to the firm ADR. Source: `CLAUDE.md:18-22`.

23. **[SOFT]** `claude plugin tag` is a documented CLI for creating release git-tags; `--push` pushes the tag to remote. This is Anthropic's blessed manual-tag mechanism for the explicit-version pattern. Source: `code.claude.com/docs/en/plugins-reference:875-890`.

24. **[SOFT]** No hardcoded timeouts/sizes in consumer-facing scripts; every CI/build knob uses `int(os.environ.get("CAIRN_<KNOB>", default))` with the var documented in `docs/operational-reference.md`. Any new release-CI script inherits this rule. Source: `CLAUDE.md:30`.

## CONSUMER RESOLUTION SEMANTICS

25. **[HARD]** Marketplace plugins are copied to `~/.claude/plugins/cache` on install (separate directory per installed version); the in-place repo is not used. This means whatever the deployment pattern produces at the resolved ref/version becomes the *frozen* plugin payload until the next `/plugin update`. The 7-day grace-period for the previous version's directory and the orphan cleanup are mechanical, not user-configurable. Source: `code.claude.com/docs/en/plugins-reference:619-623`; `code.claude.com/docs/en/plugin-marketplaces:229`.

26. **[HARD]** Installed plugins cannot reference files outside their directory (path-traversal blocked); symlinks within the plugin directory are preserved (not dereferenced) and resolved at runtime. Whatever ref the deployment pattern produces, it must be self-contained — `dist/` cannot escape upward to `..` or sibling directories. Source: `code.claude.com/docs/en/plugins-reference:625-637`.

27. **[HARD]** `${CLAUDE_PLUGIN_ROOT}` resolves to the plugin's installation directory (cache path), which changes on every update. Hooks/MCP/LSP commands resolving plugin-internal scripts use this variable. The deployment pattern's chosen ref-resolution must produce a layout where `${CLAUDE_PLUGIN_ROOT}/checks/role_guard.py` (etc.) lands at the expected paths declared in `dist/hooks/hooks.json`. Source: `code.claude.com/docs/en/plugins-reference:540-546`; `m5-plugin-distribution-and-symlink-retire/D4` (`.../m5-plugin-distribution-and-symlink-retire.md:71-72`).

28. **[HARD]** D5 (`m5-plugin-distribution-and-symlink-retire/D5`) requires `role_guard.py` lines 28 and 121 to anchor `CAIRN_ROOT` via `Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))`, NOT `Path(__file__).resolve().parent.parent`. Under any chosen deployment, post-install validator must exercise positive end-to-end envelope enforcement (write sample envelope → attempt denied write → assert exit 1). The deployment mechanism must produce a `dist/checks/role_guard.py` carrying the D5 anchoring. Source: `docs/adr/m5-plugin-distribution-and-symlink-retire.md:74-86`; `scripts/postinstall_validate.py:57-109`.

## DOGFOODING / SELF-CONSUMPTION

29. **[HARD]** INV-011 is firm: cairn-the-repo retains `.slice-system → .` self-symlink for maintainer dogfooding; `scripts/migrate_from_symlink.sh` aborts exit 3 on self-symlink detection. Plugin-installs-itself (Path A) is rejected per D8. The chosen deployment mechanism MUST NOT change what cairn-the-repo consumes locally; it changes only how *external* consumers reach the payload. Source: `docs/ARCHITECTURE.md:91-97` (INV-011); `docs/adr/m5-plugin-distribution-and-symlink-retire.md:103-105` (D8).

30. **[HARD]** The maintainer self-symlink is the bootstrap-circularity defense (Pre-mortem Scenario 3): editing `checks/role_guard.py` while cairn's hooks run from the plugin cache requires republish-reinstall-restart per iteration. Whichever deployment pattern is chosen, cairn-internal development continues to read from canonical paths via `.slice-system → .`, not from the plugin cache. Source: `docs/adr/m5-plugin-distribution-and-symlink-retire.md:155-160` (Risk Register #3); `docs/ARCHITECTURE.md:91`.

31. **[SOFT]** Symlink-recursion hazard: any tool walking from cairn-the-repo's root that follows symlinks recursively will infinite-loop on `.slice-system → .`. `build_dist.py` already explicitly skips it; any new deployment-CI script (sync-action, publish-script, etc.) that walks the repo MUST explicitly exclude `.slice-system`. Source: `CLAUDE.md:14`; `scripts/build_dist.py:50-56,66-67`.

## MIGRATION / BACKWARDS-COMPAT

32. **[HARD]** F3 (M6) shipped on `dev` at `6a6f430`; `complex-rag-analysis` migration helper + `docs/upgrading-from-symlink.md` are in place, audit checks 1–8 PASS, audit check 9 (manual end-to-end real install) is PENDING precisely on the deployment-mechanism gap. Whichever deployment pattern lands must let check 9 actually run (consumer types `/plugin marketplace add` + `/plugin install` and gets a working install). Source: `.claude/skill-runs/cairn-m6-f3-migration-and-symlink-retire/integration/sweep-notes.md` (Status block + Pending manual verification section).

33. **[HARD]** D9 (`m5-plugin-distribution-and-symlink-retire/D9`) ships M5+M6 atomically as one milestone. F3 closed, but the deployment-mechanism gap means the M5+M6 milestone is functionally incomplete from the consumer's perspective — F3's consumer-facing migration runbook points at install commands that fail. Whichever deployment pattern lands closes the milestone. Source: `docs/adr/m5-plugin-distribution-and-symlink-retire.md:107-113` (D9); F3 sweep-notes Status block.

34. **[SOFT]** README and CONSUMER.md instruct consumers to run `/plugin marketplace add https://github.com/firaaz/cairn` then `/plugin install cairn@cairn-marketplace`. These literal URLs are committed and consumer-facing; whatever deployment pattern lands either preserves these strings or requires a coordinated doc update. Source: `README.md:19` (per F3 sweep-notes audit check 8); `CONSUMER.md:13-15` (per F3 sweep-notes adjacent-code regression check).

35. **[CONTEXT]** Lessons L-017 / L-018 / L-019 (consumer-bridge breakage class): cwd-coupling + `__file__`-resolution drift through `.slice-system` historically silent-broke consumer dogfood sessions. The chosen deployment pattern's path-resolution behavior under the plugin-cache model must be exercised under a real consumer install — dispatch-time tests on the build script alone are necessary but not sufficient. Source: `docs/lessons.md:327-396` (L-017/018/019 entries).

## OTHER

36. **[HARD]** Vision commitment #1 (agent-portable substrate, Windsurf as second runtime) survives the deployment choice. `.claude/skills/` ports to Windsurf "for free" (cross-agent skill discovery); `.claude/agents/` does not. Whichever deployment pattern is chosen, it must not lock cairn into Claude-Code-only distribution at the protocol level. Source: `docs/operational-reference.md:409`; `docs/plans/2026-05-06-cairn-shrink-design.md:125,160,294`.

37. **[CONTEXT]** Operator memory `feedback_designs_through_decision.md` records that decision-weight architectural changes (distribution / migration / supersession / cross-cutting) invoke `/decision`, not just `superpowers:brainstorming → writing-plans`. This /decision run is the sanctioned process for the choice. Source: brief.md:34-35; operator-memory pointer in system reminder.

## CONFLICTS SURFACED

**C1 (manifest-shape vs documented schema).** Constraint 5 (current `marketplace.json` uses `"type": "git"` discriminator) vs constraint 12 (documented schema uses `"source": "<github|url|git-subdir|npm>"`). The current manifest does not match any documented `source.source` shape. Whichever Phase-2 approach is chosen, this conflict must be resolved (the manifest needs rewriting to a documented shape, OR an undocumented compatibility-alias must be confirmed by direct test or with Anthropic).

**C2 (Approach C vs schema absence).** Constraint 17 (no release-archive / tarball / GitHub-release source type is documented) vs the operator-named Approach C ("GitHub release + git-subdir"). `git-subdir` is documented as "sparse clone of a subdirectory of a git repo" — it does NOT download release artifacts. Approach C's "GitHub release" component has no documented marketplace-schema landing point. Phase 2C will need to either reinterpret C as "release-tag pin via `git-subdir` with `ref: vX.Y.Z`" (which collapses C into A-with-tags) or surface this as a structural blocker.

**C3 (D2 manual semver vs Approach B's npm semver-range semantics).** Constraint 7 (D2 commits to manual `v0.x.y` tag bumps; consumers pin SHAs/tags) vs constraint 16 (`npm.version` accepts semver ranges `^2.0.0`, `~1.5.0`). If Approach B (npm publish) is chosen, the npm registry's range-semantics arrive whether cairn invites them or not — D2's "consumers pin SHAs/tags" stance must either be re-stated as "consumers pin exact npm versions" (which is achievable via `npm.version: "0.1.0"` exact pin) or D2 amended.

**C4 (D2 explicit-version vs commit-SHA-as-version).** Constraint 8 (`plugin-template.json` carries `"version": "0.1.0"`; explicit-version mode) vs constraint 9 (commit-SHA-as-version mode is the docs' "actively-developed plugins" preset). D2 chose explicit version. Approach A (release-branch with `dist/` committed + sync CI) at the simplest implementation is "consumers pin `ref: dev` and re-pull on every `dev` commit"; that sidesteps the manual-bump requirement only by abandoning the explicit-version stance. The D2 commitment binds against the lazy implementation of A.

**C5 (firm M5 ADR vs decision-weight choice).** Constraint 22 (ADRs are append-only; firm ADRs only frontmatter-edit) vs the decision question itself, which by brief lines 27–35 names this a /decision-weight architectural-distribution change. Whichever Phase 2 approach lands, the resolution path is either (a) a new ADR amending `m5-plugin-distribution-and-symlink-retire/D3` via co-landed amendment ADR, or (b) frontmatter-flip of M5 to `superseded-by:` plus a fresh successor ADR. Phase 1+ must pick the path; Phase 0 surfaces only that the path is constrained.

## EXTERNAL-DOCS AMBIGUITIES FLAGGED

**A1.** The plugin-marketplaces docs do not document `"type": "git"` as a source.type value, but cairn's current `marketplace.json` uses it. Whether this is (a) an undocumented alias for `source: url`, (b) a legacy schema shape, (c) outright invalid, or (d) interpreted leniently by the resolver is not visible from the docs. Direct empirical test against a real `/plugin marketplace add` is the only resolution path — the docs are unambiguous about what IS supported but silent about what is rejected vs accepted-with-warning.

**A2.** The phrase "git-subdir … clones sparsely" (constraint 14) is documented at a high level but the docs do not specify whether `path: "dist/"` requires `dist/` to actually exist at the resolved ref/sha (presumably yes — sparse-clone of a non-existent path likely fails). This affects whether Approach A (release branch with `dist/` committed) can be implemented as `source: git-subdir, url: ..., path: dist/, ref: <release-branch-or-tag>` without the default branch ever carrying `dist/`. Empirical test or a docs supplement (the "Plugin directory not found at path" error in `code.claude.com/docs/en/plugins-reference:929` suggests fail-fast on missing path, which is consistent with sparse-clone semantics).

**A3.** `code.claude.com/docs/en/plugins-reference:993-998` lists which source-types use commit-SHA-as-version when `version` is omitted: "`github`, `url`, `git-subdir`, and relative-path sources in a git-hosted marketplace." This list is authoritative for which deployment patterns can use the commit-SHA-as-version escape; `npm` is explicitly excluded (`unknown` is the fallback). Phase 1+ should treat this list as exhaustive when reasoning about no-explicit-version variants of A and C.

**A4.** Whether `claude plugin tag` (constraint 23) interacts with `dist/`-population CI in any documented way is not stated. The CLI creates a release git-tag in the current plugin directory; it does not document any pre-tag build hook. Any deployment pattern using `claude plugin tag` as the trigger must therefore co-design the build/sync step separately.
