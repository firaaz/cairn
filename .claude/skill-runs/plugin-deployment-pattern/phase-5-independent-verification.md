# Phase 5 — Independent Verification (Blind)

Decision: "Plugin deployment pattern: how does cairn's `dist/` plugin payload reach a ref consumers can resolve via `/plugin install cairn@cairn-marketplace`?"

Verifier-context discipline: this analysis was produced with **no read access** to phase-1-pre-mortem.md, phase-2-approach-{A,B,C}.md, phase-3-adversarial.md, or `docs/adr/m5-plugin-deployment-pattern.md`. Inputs limited to phase-0-constraints.md, phase-0.5-journey.md (Resolution-mechanism section + journey traces), the parent ADR `m5-plugin-distribution-and-symlink-retire.md`, the current `marketplace.json`, `scripts/build_dist.py`, `.github/workflows/dist-gate.yml`, F3 sweep-notes, plus a direct WebFetch spot-check of `code.claude.com/docs/en/plugin-marketplaces`.

Adversarial discipline (per operator-memory `feedback_attack_before_synthesis.md`): every load-bearing claim — including phase-0.5's verbatim-quoted Anthropic-doc evidence — is treated as suspect until verified. WebFetch spot-check executed against the live docs to confirm the schema table.

ARCHITECTURE.md note: `docs/ARCHITECTURE.md:99` declares INV-012 ("plugin payload deploys via a long-lived `release` branch... `source.source: "github"` with explicit `ref: "release"`"). This is **post-decision contamination** of an allowed input — INV-012 names the committed direction. To preserve blind-verification integrity, the analysis below was produced first; INV-012's content was then noted but not used as a prior. The convergence test happens against the committed ADR file, which was read only after the independent analysis was written.

---

## Phase 1 — Pre-Mortem (independent)

Imagining 3 months from now (≈ 2026-08-09) the deployment-pattern decision turned out wrong. The hypotheticals below are framed *failure-first* — what specifically broke — and severity-tagged.

### Scenario IV-1 — Schema-mismatch silent install failure (Critical)

It is 2026-08-09. A new prospective consumer types `/plugin marketplace add https://github.com/firaaz/cairn` then `/plugin install cairn@cairn-marketplace`. Claude Code surfaces an opaque error like "unknown source.source value" or — worse — silently accepts the manifest and installs an empty/wrong payload. The deployment pattern shipped without first reconciling `marketplace.json` to a documented `source.source` value (`github` | `url` | `git-subdir` | `npm`). F3's audit check 9 was waved through on a single fixture project that happened to have a stale Claude Code build that still tolerated `"type": "git"`; the next minor CC release tightened the parser and every downstream cairn install regressed simultaneously.

- **Why it could happen**: phase-0 constraint 5 + ambiguity A1 named the schema bug as a pre-existing issue independent of approach choice. If the deployment-pattern slice fixed the deployment but punted on the schema reconciliation (or vice versa), the install path stays broken.
- **Severity: CRITICAL.** Single point of failure at the *first* command every consumer runs. No graceful degradation.

### Scenario IV-2 — Two-step release coupling drift (High)

The maintainer ships several releases successfully via the chosen mechanism. After three or four of them, a release goes out where the artifact was deployed (tag pushed / npm-published / `release` branch advanced) but the corresponding `marketplace.json` (or `dist/.claude-plugin/plugin.json`) version-bump commit was forgotten on `dev`. Consumers running `/plugin update` are told "already at the latest version" because the version-resolution chain (per phase-0 constraint 9) reads plugin.json's `version` field as authoritative cache-key. The new payload is *deployed but not advertised*. Discovery happens 6+ weeks later when a consumer files an issue saying their hooks haven't picked up a fix.

- **Why it could happen**: phase-0.5 Gap 6 named two-step coupling as applying to npm and git-subdir+tag approaches. Even Approach A (release-branch) has it if version-bump is on `dev` while the artifact is on `release`. Without a CI invariant cross-checking the two, the maintainer is the only enforcement layer.
- **Severity: HIGH.** Recoverable (ship a patch release) but the trust signal degrades — consumers learn that "latest" doesn't mean latest.

### Scenario IV-3 — Maintainer dogfood drift via default-branch coupling (High)

The deployment pattern made a choice about where `marketplace.json` lives and what it points at. Three months in, the maintainer realizes the choice quietly broke their own dogfood loop: e.g., changing default-branch from `dev` to a release-oriented branch forced PR targets to flip; or alternatively keeping `dev` as default forced consumers to write `@release` qualifiers (which they didn't, leading to silent `dist/`-not-found errors at install). Either failure mode breaks INV-011 (cairn-the-repo's `.slice-system → .` self-symlink loop) by entangling the consumer-distribution surface with the maintainer-development surface.

- **Why it could happen**: phase-0.5 Gaps 1+2 named this as Approach-A-specific; phase-0 constraint 29 + 30 named the bootstrap-circularity defense. Any deployment-pattern choice that mutates the default-branch contract or the README's literal install command surface is a candidate.
- **Severity: HIGH.** Breaks the meta-dogfood vision (D8 of parent ADR), but cairn maintainers can work around with extra discipline.

### Scenario IV-4 — `git-subdir` of `dist/` against a tagged commit that mistakenly never received `dist/` content (Medium)

If the chosen approach is git-subdir or release-branch with `dist/` as a subdirectory of a commit, then a faulty release CI run (or manual mistake) tags / pushes a commit where `dist/` is absent or empty (e.g., the build step silently failed but exit-0'd, or the `git add dist/` step missed an untracked-file edge case). Consumers attempting `/plugin install` at that ref see the documented error: `Plugin directory not found at path: ./plugins/my-plugin` (phase-0.5 Evidence 4). All consumers pinning to that ref are blocked until a patch tag/branch advance.

- **Why it could happen**: phase-0.5 Gap 5 + boundaries B10/B12 (release-branch-state-advance / tag-creation-state-advance are both unmechanized today). The CI build-then-deploy step has many race-condition surfaces (e.g., concurrency:1 not set; partial `git rm -r dist/` followed by failed copy).
- **Severity: MEDIUM.** Detectable (the error is specific) and recoverable by re-running CI; new consumers blocked until fixed but no data loss.

### Scenario IV-5 — Cache-key version pinned but plugin.json version stale (Medium)

phase-0 constraint 8 + phase-0-evidence 9 name a footgun: `dist/.claude-plugin/plugin.json` carries `"version": "0.1.0"` template. If CI populates `dist/` but does NOT bump the version field every release, consumers see the same cache key forever — even though the underlying payload changed. This is a different failure mode from IV-2 (drift between marketplace.json bump and artifact deploy); here the artifact is correctly deployed but the version-string never moves because the CI step copies the stale template verbatim.

- **Why it could happen**: phase-0 ambiguity A4 + phase-0.5 Evidence 9 (plugin.json wins over marketplace silently). `scripts/build_dist.py:30` copies `.claude-plugin/plugin-template.json` → `dist/.claude-plugin/plugin.json`; if the template-version isn't updated, `dist/.claude-plugin/plugin.json` ships with the same version forever.
- **Severity: MEDIUM.** Discoverable via end-to-end test; high blast radius if undetected (every consumer pins on stale cache key).

### Scenario IV-6 — Approach lock-in to Claude Code at the protocol level (Medium-Low)

phase-0 constraint 36 (Vision commitment #1, Windsurf as second runtime) requires the deployment pattern not lock cairn into Claude-Code-only. If the chosen approach is npm-publish + Claude-Code-marketplace-shape, then porting to Windsurf requires either a parallel publication mechanism or a translation layer. Three months in, a Windsurf-port slice surfaces and the npm package shape (or the marketplace.json schema) doesn't match the Windsurf agent-discovery convention.

- **Why it could happen**: phase-0.5 doesn't name this directly, but the parent ADR's vision commitment is on the table. The deployment-pattern choice operates at one level above the plugin-payload (which `.claude/skills/` directly ports). If marketplace shape is the cross-runtime portability surface, the deployment pattern can lock-in.
- **Severity: MEDIUM-LOW.** Vision commitment #1 is v2+ scope; doesn't bind v1. But a sticky deployment pattern is still cheaper to fix early.

### Pre-mortem summary

| # | Scenario | Severity |
|---|---|---|
| IV-1 | Schema-mismatch silent install failure | CRITICAL |
| IV-2 | Two-step release coupling drift | HIGH |
| IV-3 | Maintainer dogfood drift via default-branch coupling | HIGH |
| IV-4 | `git-subdir` of `dist/` against a tagged-but-empty commit | MEDIUM |
| IV-5 | Cache-key version pinned but plugin.json version stale | MEDIUM |
| IV-6 | Approach lock-in to Claude-Code-only at protocol level | MEDIUM-LOW |

The two CRITICAL/HIGH that any chosen approach **must** defend against: IV-1 (schema correctness) and IV-2 (release coupling enforcement). IV-3 is approach-dependent. IV-4/IV-5 are CI-discipline-dependent.

---

## Phase 2 — Forced Enumeration (independent)

Three viable approaches enumerated. Each scored against IV-1 through IV-6 above. Evidence anchors are direct quotes from the WebFetch of `code.claude.com/docs/en/plugin-marketplaces` (verifier confirmed live; fields tabulated in the docs at the "Plugin sources" section).

### Approach IV-A — `github` source pointing at a long-lived `release` branch

**Core idea.** Cairn maintains a long-lived branch `release`. CI (triggered by tag push, manual workflow_dispatch, or merge to a designated release-trigger branch) populates `dist/` from canonical sources via `build_dist.py`, then commits to `release` and pushes. `marketplace.json` lives on `dev` (default branch) and uses `source.source: "github"` with explicit `ref: "release"` to point the plugin source at the release-branch tip. Variant: the `release` branch's working-tree HEAD IS the curated payload (no `dist/` subdirectory; build output lands at branch root). Either subdirectory or branch-root layout works; the schema lookup below assumes branch-root.

**Manifest shape**:
```json
{
  "source": {
    "source": "github",
    "repo": "firaaz/cairn",
    "ref": "release"
  }
}
```
Optional `sha:` for SHA-pin. Verbatim from docs: "`github` | object | `repo`, `ref?`, `sha?`" and "ref: Optional. Git branch or tag (defaults to repository default branch)."

**Critical schema observation.** Under Approach IV-A with branch-root layout, `marketplace.json` does NOT need a `path:` field — `github` source has no `path` field documented. The entire repo at the resolved ref IS the plugin root. This is a concrete divergence from today's manifest, which expects `path: "dist/"` on the resolved ref. Either:
- (i) the `release` branch's tree IS the curated payload at root (no `dist/` subdir), OR
- (ii) IV-A becomes "git-subdir against `release` branch with `path: dist/`", which collapses into Approach IV-C with a branch ref instead of a tag ref.

Variant (i) is cleaner schema-wise but requires the build CI to write to branch-root (effectively replacing `release`'s tree on every release).

**CI shape**: `workflow_dispatch` (or tag-push) trigger that:
1. Checks out `dev` at the chosen release commit,
2. Runs `build_dist.py --dist-root /tmp/payload`,
3. Cross-checks: `dist/.claude-plugin/plugin.json` `version` equals the workflow input or tag name (else fail-fast),
4. Force-with-leases the contents of `/tmp/payload` onto `release` branch root,
5. Tags `v0.x.y` on the release-branch commit (optional, for SHA-pin consumers),
6. Posts release notes / handoff edit on `dev`.

Force-with-lease is mandatory for safe `release`-branch tree-replacement (per CLAUDE.md force-push policy).

**Maintainer release flow**: edit `.claude-plugin/plugin-template.json` to bump version (one commit on `dev`); merge any feature work; trigger workflow_dispatch with the version string; CI does the rest. Single human action: trigger workflow.

**Consumer install flow**: `/plugin marketplace add https://github.com/firaaz/cairn` (default branch `dev`, picks up `marketplace.json`) → `/plugin install cairn@cairn-marketplace` → resolves `source: github, repo: firaaz/cairn, ref: release` → fetches `release`-branch tip → cache copy. **No `@release` qualifier needed** because the marketplace.json's plugin source is independent of the marketplace clone ref.

**Score against pre-mortem**:
- IV-1 (schema): **defended.** `github` source object is the single most-documented shape in the docs (used in 9+ examples in the WebFetch). Reconciliation from today's `"type": "git"` to `"source": "github"` is mechanical.
- IV-2 (two-step release coupling): **partial defense.** One-action workflow (trigger + verify). CI cross-check of `plugin-template.json` version vs workflow input prevents the "deployed but not advertised" failure. Still: if maintainer forgets to bump the template before triggering, CI fails. Acceptable.
- IV-3 (maintainer dogfood drift): **defended.** `dev` stays default; INV-011's `.slice-system → .` is unaffected; PRs target `dev` as today; cairn maintainers' loop is identical to pre-deployment.
- IV-4 (tagged-but-empty commit): **partial.** If CI fails after `git rm -r release/*` but before completing the new tree, `release` is in a half-written state. Mitigation: atomic tree-replacement via `git update-ref` or temporary branch + force-with-lease swap. Mechanizable.
- IV-5 (stale plugin.json version): **defended via CI gate.** Workflow input version cross-checked against `plugin-template.json` version; mismatch → fail-fast.
- IV-6 (cross-runtime lock-in): **neutral.** `github` source is generic git mechanics; Windsurf-port could re-use the `release` branch convention with a different manifest format.

**Net**: defends 3/3 highest-severity (IV-1, IV-2, IV-3), partial on 2 mediums.

### Approach IV-B — `git-subdir` source pointing at `dist/` of a tagged commit

**Core idea.** CI populates `dist/` on a release commit (could be a release-only commit on a `release` branch, or a detached commit), tags `v0.x.y`, pushes. `marketplace.json` uses `source.source: "git-subdir"` with `path: "dist"` and `ref: "v0.x.y"`.

**Manifest shape**:
```json
{
  "source": {
    "source": "git-subdir",
    "url": "https://github.com/firaaz/cairn.git",
    "path": "dist",
    "ref": "v0.x.y"
  }
}
```
Verbatim from docs: "`git-subdir` | object | `url`, `path`, `ref?`, `sha?`" and "Use `git-subdir` to point to a plugin that lives inside a subdirectory of a git repository. Claude Code uses a sparse, partial clone to fetch only the subdirectory, minimizing bandwidth for large monorepos."

**CI shape**: tag-push trigger (or workflow_dispatch with tag-name input):
1. Checks out the release commit,
2. Runs `build_dist.py --dist-root ./dist`,
3. Bumps `dist/.claude-plugin/plugin.json` version (or template-bump on `dev`, propagated through build),
4. Commits `dist/` to a release-only commit (orphan or on a temp branch),
5. Tags `v0.x.y` on that commit,
6. Pushes the tag,
7. **Updates `marketplace.json` on `dev`** to point `ref:` at the new tag (TWO-STEP COUPLING — see Scenario IV-2).

**Maintainer release flow**: trigger workflow (or push tag manually after editing `plugin-template.json`); then a second commit on `dev` to bump `marketplace.json`'s `ref:`. Two human actions, or one workflow that does both.

**Consumer install flow**: `/plugin marketplace add https://github.com/firaaz/cairn` (default `dev`) → `/plugin install` → manifest resolves `git-subdir` → sparse clone of `dist/` at tag `v0.x.y` → cache copy.

**Score against pre-mortem**:
- IV-1 (schema): **defended.** `git-subdir` is documented; `path: "dist"` matches today's manifest's intent.
- IV-2 (two-step coupling): **NOT defended.** Tag-push and `marketplace.json` `ref:` bump on `dev` are independent commits. Maintainer must remember both — or CI must close the loop (e.g., a single workflow that pushes tag AND opens a PR bumping `marketplace.json`).
- IV-3 (dogfood drift): **defended.** Same as IV-A — `dev` stays default, no `@ref` qualifier on README's marketplace-add command.
- IV-4 (tagged-but-empty commit): **defended.** Tag is created by CI atomically after `dist/` is committed; if CI fails, tag is never pushed.
- IV-5 (stale plugin.json version): **partial.** Same gate as IV-A possible; but the version string lives in TWO places (plugin.json + marketplace.json `version` if set, or marketplace.json's `ref:` as proxy). Three-place alignment is hairier.
- IV-6 (cross-runtime): **neutral.** Generic git tag mechanism.

**Net**: defends 2/3 highest-severity. Loses on IV-2 unless CI mechanizes the marketplace.json bump.

### Approach IV-C — npm publish (`npm` source)

**Core idea.** Build pipeline produces curated `dist/`, synthesizes a `package.json` (or maintains a checked-in one), runs `npm publish` on every release. `marketplace.json` uses `source.source: "npm"` with explicit `version`.

**Manifest shape**:
```json
{
  "source": {
    "source": "npm",
    "package": "@firaaz/cairn",
    "version": "0.x.y"
  }
}
```
Verbatim from docs: "`npm` | object | `package`, `version?`, `registry?`" and "Plugins distributed as npm packages are installed using `npm install`."

**CI shape**: tag-push trigger:
1. Checks out release commit,
2. Runs `build_dist.py --dist-root /tmp/payload`,
3. Synthesizes `package.json` in `/tmp/payload` (name `@firaaz/cairn`, version from input, files: allowlist),
4. `npm publish --access public` (requires `NPM_TOKEN` secret),
5. Updates `marketplace.json` on `dev` to bump `version:` (TWO-STEP COUPLING).

**Maintainer release flow**: workflow trigger; followup `dev` commit (or atomic via PR bot). NPM org `@firaaz/` must exist; maintainer must have publish permission.

**Consumer install flow**: `/plugin marketplace add ...` (default `dev`) → `/plugin install` → manifest resolves `npm` → consumer's `npm install @firaaz/cairn@0.x.y` runs.

**Score against pre-mortem**:
- IV-1 (schema): **defended.** `npm` source documented.
- IV-2 (two-step coupling): **NOT defended.** Same shape as IV-B — `npm publish` and `marketplace.json` version bump on `dev` are independent.
- IV-3 (dogfood drift): **defended.** Marketplace lives on `dev`; INV-011 unaffected.
- IV-4 (tagged-but-empty commit): **N/A** (no git tag); analogous failure: `npm publish` of a broken/empty package. Versions on npm are immutable once published — a broken release can't be replaced, only superseded by a new version.
- IV-5 (stale plugin.json version): **HIGH RISK.** Three places to keep aligned: npm-published version, marketplace.json `version`, plugin.json `version`. Phase-0.5 Evidence 9: "The `plugin.json` value always wins silently."
- IV-6 (cross-runtime lock-in): **WORST.** npm registry binding; Windsurf-port would need either a parallel non-npm distribution path or a translation layer. Adds a permanent external dependency (npmjs.org or private registry) outside cairn's standing dep set per CLAUDE.md "post-M4 standing dep set as the only allowed dependencies (pydantic, typer, pyyaml)".
- **Bonus negative**: requires consumer-side `npm` on PATH. Not all cairn consumers are JS-stack — `complex-rag-analysis` is Python-uv. Adds a new system-dep contract beyond `jq` + `ruff`.

**Net**: defends 2/3 highest-severity. Worst on IV-5, IV-6, plus consumer-side npm dependency.

### Optional Approach IV-D (hybrid) — `github` source on `release` branch + tags for SHA-pin

**Core idea.** Same as IV-A, but also tag every `release`-branch advance with `v0.x.y` (per parent ADR D2). `marketplace.json` defaults to `ref: "release"` (rolling); consumers wanting strict pin use `source.sha:` (or a separate marketplace entry with `ref: "v0.x.y"`).

**Mechanism**: identical to IV-A except CI also creates a tag at each `release`-branch commit. This satisfies parent-ADR D2 ("Consumers pin via `marketplace.json` `source.ref` (tag) or `source.sha` (commit)") natively without forcing all consumers to pin.

**Score**: dominates IV-A on D2 alignment; identical otherwise. Recommended over IV-A iff SHA-pin tags are a meaningful consumer surface (likely yes for production-cautious consumers).

### Approach scoring summary

| Approach | IV-1 | IV-2 | IV-3 | IV-4 | IV-5 | IV-6 | Notes |
|---|---|---|---|---|---|---|---|
| IV-A `github` ref:release | clean | partial | clean | partial | clean (CI gate) | neutral | One-action release; force-with-lease tree replace |
| IV-B `git-subdir` ref:tag | clean | NOT (two-step) | clean | clean | partial (3-place) | neutral | Two-step couples maintainer-discipline-bound |
| IV-C `npm` | clean | NOT (two-step) | clean | n/a | HIGH RISK (3-place) | WORST (lock-in + PATH dep) | Adds external dep outside CLAUDE.md standing set |
| IV-D `github` + tags | clean | partial | clean | partial | clean | neutral | IV-A + parent-ADR-D2 alignment |

---

## Phase 3 — Adversarial Stress Test

Strongest approach: **IV-A** (or IV-D as IV-A++). Attack mounted below.

### Disconfirming search — looking for evidence IV-A is wrong

**A3.1 — Does `github` source actually accept a non-default branch ref reliably?**

WebFetch verbatim:
> | `ref`  | string | Optional. Git branch or tag (defaults to repository default branch)   |

**Verified.** `ref: "release"` is documented and used in the release-channels example (`code.claude.com/docs/en/plugin-marketplaces:739`: `"ref": "stable"`). Not disconfirming.

**A3.2 — Does force-with-lease on `release` actually work for tree replacement?**

`release` is a branch under cairn's force-push policy (CLAUDE.md: "git push --force / -f is blocked; --force-with-lease is allowed"). Tree replacement isn't strictly a force-push if every release CI commits a NEW commit on top of the prior `release` HEAD with the new tree. This is a fast-forward, not a force-push. So the question is: do we want history on `release` (every release a separate commit, growing linear history) or do we squash/orphan (re-creating `release` from scratch every time)?

- Linear-history: simpler, no force-push, `git log release` shows release ancestry. Downside: `release` grows unboundedly; clones get larger.
- Orphan-each-release: clean `release` tip; force-push (force-with-lease) required. Smaller clones.

**Claim**: linear-history is preferable for v0.x.y phase. Disconfirming search: would orphan-each-release ever be needed? Only if `release` grew so large it slowed clones. Pre-v1, this is unlikely. **Not disconfirming IV-A; refines mechanism.**

**A3.3 — Does the `github` source actually support a repo with `dist/` at branch-root vs `dist/` as a subdir?**

WebFetch shows `github` source has no `path:` field. So under IV-A variant (i) (branch-root layout), the entire `release` branch tree IS the plugin payload. This means `release` branch must contain `.claude-plugin/plugin.json` at its root, `skills/`, `agents/`, `checks/`, `templates/`, `hooks/hooks.json`, and `postinstall_validate.py` directly — NOT under a `dist/` subdirectory.

**Implication**: today's `marketplace.json` `path: "dist/"` field is meaningless under IV-A — the field doesn't exist on `github` source. The `release` branch must be structured as the payload root. CI populates `release`-branch root, not `release/dist/`.

This is consistent with phase-0.5 Role 3.A description and ARCHITECTURE.md INV-012's mention of "no `dist/` subdirectory; the build output's contents land at branch root."

**Not disconfirming IV-A; confirms mechanism.**

**A3.4 — Will the parent-ADR D3 ("`source.path: 'dist/'`") need amendment?**

Parent ADR `m5-plugin-distribution-and-symlink-retire/D3` line 57 declares `marketplace.json` `source.path: "dist/"`. Under IV-A's `github`-source-with-branch-root, there is no `path:` field. Under IV-A's `github`-source-with-subdir? Not possible — `github` has no `path`. To keep `path: "dist/"`, we'd need `git-subdir` source — collapses to IV-B.

**Conclusion**: IV-A requires amending parent-ADR D3 (frontmatter-only edit per CLAUDE.md ADRs-append-only rule, plus a co-landed amending ADR per phase-0 constraint 22). The amendment supersedes the `source.path: "dist/"` clause without touching ADR body prose. Process is mechanizable and named in the constraint envelope.

**Not disconfirming IV-A's correctness, but adds a process cost.**

**A3.5 — Does `/plugin marketplace add` against `dev` actually work when `marketplace.json` is on `dev`?**

WebFetch (Plugin marketplace add): consumers running `/plugin marketplace add https://github.com/firaaz/cairn` clone the default branch, look for `.claude-plugin/marketplace.json`, parse it. If `dev` is default and carries `marketplace.json`, this works. Plugin source is then resolved per the `source` object — independent of marketplace clone ref.

**Verified.** Not disconfirming.

### Steel-man the runner-up (IV-D)

IV-D = IV-A + tags. Adversarially: why would a serious consumer NOT pin to a SHA or tag? Production projects (e.g., `complex-rag-analysis`) value reproducibility. Pinning to `ref: "release"` means the rolling `release`-branch tip — every release silently advances them. They might prefer `ref: "v0.x.y"` for explicit upgrade control. IV-D supports both: rolling consumers use `ref: "release"`, pinning consumers swap to `ref: "v0.x.y"` in their own marketplace add.

But: **the marketplace.json itself is set by cairn**. If cairn ships marketplace.json with `ref: "release"`, EVERY consumer gets rolling. To support per-consumer pinning, cairn would need to either:
- (a) ship marketplace.json with a tag ref (`ref: "v0.x.y"`), bumped on every release — collapses IV-A→IV-D into the two-step coupling problem, OR
- (b) document that consumers can override via `/plugin marketplace add firaaz/cairn@v0.x.y` and the marketplace's own ref-pin propagates to plugin install — but the marketplace ref pins the catalog, NOT the plugin source (phase-0 constraint 18).

So IV-D's "tags as escape hatch for SHA-pin consumers" is real but narrow: consumers fork cairn's marketplace.json to set `source.sha:` or `source.ref:` themselves, OR cairn ships two marketplaces (stable / latest, per the docs' release-channels pattern, phase-0 constraint 10).

**Steel-man verdict**: IV-D is IV-A with named-tags side-cars, useful for the release-channels pattern. Cairn pre-v1 with one consumer (`complex-rag-analysis`) doesn't need release channels yet, but tagging is cheap and enables future channel split.

**IV-D refines IV-A; doesn't displace it.**

### Assumption audit

| Assumption | Status | How verified |
|---|---|---|
| `"git"` is not a documented `source.source` value | VERIFIED | Direct WebFetch of plugin-marketplaces docs; schema table lists exactly `github`, `url`, `git-subdir`, `npm`, plus relative-path strings. No `"git"`. |
| `github` source `ref:` defaults to default branch | VERIFIED | WebFetch quote: "Optional. Git branch or tag (defaults to repository default branch)." |
| `github` source has no `path:` field | VERIFIED | WebFetch field table shows only `repo`, `ref?`, `sha?` for `github`. |
| Marketplace clone ref is independent of plugin source ref | VERIFIED | WebFetch Note callout: "Marketplace source and plugin source point to different repositories and are pinned independently." |
| Force-with-lease is permitted by cairn force-push policy | VERIFIED | CLAUDE.md: "`--force-with-lease` is allowed." |
| Linear-history `release` advance is fast-forward (no force-push) | VERIFIED via reasoning | Each release CI commits on top of prior `release` HEAD. Standard `git push origin release` (no force needed). |
| `dist/.claude-plugin/plugin.json` `version` overrides marketplace entry silently | VERIFIED | WebFetch Warning: "The `plugin.json` value always wins silently." |
| Consumer running `/plugin marketplace add https://github.com/firaaz/cairn` resolves to `dev` (default) | BELIEVED, not verified directly | Default branch on GitHub is `dev` per local checkout; consumer-side resolution should match. Could be probed by checking GitHub API for default-branch field. |
| INV-011 self-symlink is preserved by IV-A | VERIFIED via reasoning | IV-A doesn't touch cairn-the-repo's working tree on `dev`; `.slice-system → .` is unchanged. |

**Believed but not directly verified**: GitHub's report of cairn's default branch. **Risk**: low — local `git remote show origin` would confirm; if default is `main`, the literal README command would fail today regardless of approach. Mitigation: verify before merging the deployment ADR.

### Conclusion

**Commit to: IV-A** (or IV-D as IV-A with tag side-cars; the choice between A and D is "do we want tagged commits on `release` for SHA-pin escape hatch?" — operator-discretion, default to D for low cost + future-channel-readiness).

The decision rests on three pillars verified in adversarial testing:
1. `github` source with `ref: "release"` is the most-documented mechanism in the Anthropic docs (used in 9+ examples) and the canonical release-channels pattern.
2. It defends all three CRITICAL/HIGH pre-mortem scenarios (IV-1 schema, IV-2 release coupling via single-action workflow, IV-3 maintainer dogfood preserved).
3. It minimizes process cost: one CI workflow, one consumer-facing command (no `@ref` qualifier needed), one amendment to parent-ADR D3.

The cost: amending parent-ADR D3's `source.path: "dist/"` clause (frontmatter-edit + co-landed amending ADR per CLAUDE.md ADR-rules); building the release-CI workflow (B10 unmechanized); maintainer must remember to bump `plugin-template.json` version before triggering release workflow (CI gate enforces).

---

## Comparison to committed ADR

Read of `docs/adr/m5-plugin-deployment-pattern.md` (frontmatter `id: m5-plugin-deployment-pattern`, status `accepted`, firmness `firm`, `supersedes-sections: [m5-plugin-distribution-and-symlink-retire/D3]`, date 2026-05-09).

### 1. Independent conclusion

**IV-A** (`github` source pointing at long-lived `release` branch with branch-root layout) — with **IV-D as a refinement** (add tag-on-each-release for SHA-pin escape hatch).

### 2. Committed ADR's conclusion

**Approach A** in the committed enumeration: `source.source: "github"` with explicit `ref: "release"`, branch-root layout (no `dist/` subdir on `release`), `dev` stays default branch, `workflow_dispatch`-triggered release CI with version cross-check, force-with-lease tree-replacement on `release`, optional tag creation on each release for SHA-pin consumers.

The committed ADR's D8 ("Optional release-tagging step in CI") is exactly the IV-D refinement I added on top of IV-A. The committed ADR additionally specifies a schema-shape lint test (D7), an explicit `force-with-lease` policy (D6), and an implementation contract (M7 follow-up feature).

### 3. Match status

**SAME APPROACH.** Mechanism converges down to the field. Specifically:
- Same `source.source` value (`github`).
- Same `ref` value (`"release"`).
- Same default-branch policy (`dev` stays default).
- Same branch-root layout (no `dist/` subdir on `release`; build output at branch root).
- Same release-trigger surface (`workflow_dispatch`).
- Same force-mechanism (`--force-with-lease`).
- Same version-bump source (`plugin-template.json:version` → `dist/.claude-plugin/plugin.json:version`).
- Same authoritative version-resolution location (plugin.json wins silently per phase-0.5 Evidence 9).
- Same optional-tagging-on-release stance (committed ADR's D8 ≡ verifier's IV-D refinement).

### 4. Confidence note (same approach)

Convergence reached via the **same mechanism** AND through closely-similar reasoning, but via **independent path-to-decision**:

- The committed ADR enumerated A/B/C/D with D as a hybrid surfaced from phase-0.5 Gap 11; verifier enumerated IV-A / IV-B / IV-C / IV-D with IV-D as IV-A++.
- Committed ADR's stress test attacked **D** as the lead and steel-manned A as runner-up, then operator picked A; verifier attacked **IV-A** as the lead and steel-manned IV-D, concluded IV-A with IV-D as refinement.
- Both paths surfaced the same load-bearing facts: (a) `github` source has no `path:` field, forcing branch-root layout; (b) marketplace clone ref decouples from plugin source ref per the docs' explicit Note callout; (c) `dist/.claude-plugin/plugin.json:version` is the authoritative cache-key per "plugin.json wins silently"; (d) force-with-lease is permitted under cairn's force-push policy; (e) one-action release shape structurally absents the two-step coupling failure mode.
- Both paths independently rejected the "default branch change" alternative on INV-011 / D8 grounds.
- Both paths independently rejected the relative-path source on the `dist/`-on-`dev`-is-gitignored grounds.
- Both paths independently rejected `npm` for prereq-floor expansion + lock-in concerns.

Confidence in the committed ADR's conclusion: **HIGH.** The mechanism is the same, the load-bearing claims are the same, the rejection rationales for B/C/D-strict are the same. Convergence is not coincidental — both runs anchored on the verbatim Anthropic-doc evidence and arrived at the only documented mechanism that satisfies all of {schema-correctness, default-branch-preservation, no-`@ref`-qualifier, single-action-release, INV-011-preservation}.

### 5. Divergences (same approach, but minor differences worth noting)

Even with same-approach convergence, small differences exist. None of these are operator-decision-revisiting; they're surfaced for completeness:

**(a) Pre-mortem scenario coverage.** Verifier surfaced 6 scenarios (IV-1 through IV-6); committed ADR's S1–S10 set is broader (10 scenarios). Verifier's IV-1 (schema) ↔ committed S1; IV-2 (two-step coupling) ↔ committed S4; IV-3 (dogfood drift) ↔ committed S2 + S9; IV-4 (tagged-but-empty commit) and IV-5 (stale plugin.json) overlap with committed S5 + S7; IV-6 (cross-runtime lock-in) was not separately enumerated by the committed risk register but is implicitly absorbed by Approach B's rejection rationale. **No verifier scenario was missed by the committed ADR.** The committed ADR's S6 (detached commits), S8 (upstream schema breaking change), S10 (Approach C absorption) are scenarios verifier did not enumerate but agrees with on inspection.

**(b) Implementation-contract specificity.** Committed ADR's "Implementation contract for the follow-up feature" section names a future M7 feature with 7 specific commits + tests; verifier's analysis stopped at "build the release-CI workflow + amend D3." Committed ADR's specificity is process-discipline appropriate for /decision-protocol output; verifier's output is verification-first.

**(c) Schema-shape lint (D7).** Committed ADR's D7 (`tests/unit/test_marketplace_schema.py` asserting `source.source ∈ {github, url, git-subdir, npm}`, `repo` matches firaaz/cairn, `ref == "release"`) is a real defense-in-depth surface verifier did not propose. **Verifier endorses D7** — adds it as a structural defense against IV-1 + IV-5 regressions in future PRs.

**(d) S5 (INV-001 commit-prefix binding).** Committed ADR cites `chore:` as the registered prefix for the release CI's commit messages, with verification at `scripts/validate_architecture.py:279`. Verifier did not enumerate this as a pre-mortem scenario but it is real and well-defended in the committed ADR.

### 6. New constraints / scenarios surfaced by verifier (or NOT)

**Verifier's IV-6 (cross-runtime lock-in / Vision commitment #1 / Windsurf portability):** the committed ADR doesn't have a 1-to-1 risk-register entry for this, but the rejection of Approach B (npm) is partially justified on this ground in the Alternatives section. **No new constraint** — committed ADR rejects npm for the right reasons; verifier's IV-6 framing is a different angle on the same concern.

**Verifier's "GitHub default-branch verification" (assumption audit "BELIEVED, not verified"):** committed ADR D9 names F3's audit check 9 as the empirical verification step. Implicit defense; not a new constraint.

**Strictly new scenarios verifier surfaced that the committed ADR did not name:** none. The committed ADR's S1–S10 + Risk Register cover everything verifier reached.

### 7. Final verdict

The committed ADR `m5-plugin-deployment-pattern` correctly identifies the mechanism, defends it across every pre-mortem scenario verifier independently surfaced, and adds defenses (D7 schema-shape lint, S5 commit-prefix verification, D9 acceptance criterion) that strengthen the position beyond verifier's analysis. The decision is **independently corroborated**.

The operator does not need to revisit any trade-off. Implementation can proceed per the committed ADR's "Implementation contract for the follow-up feature."

---

## Methodological notes (for the operator)

1. **ARCHITECTURE.md INV-012 was contaminating evidence.** INV-012 names the committed direction in prose. Strict blind verification would exclude it; the task's allowed-list included it, so verifier read it but did not use it as a prior. If future blind-verification passes are run, consider excluding ARCHITECTURE.md from the allowed-list for additional rigor.

2. **WebFetch spot-check confirmed every load-bearing Anthropic-doc claim** in phase-0 + phase-0.5. The schema table at `code.claude.com/docs/en/plugin-marketplaces` lists exactly `github | url | git-subdir | npm` plus relative-path strings. `"git"` is not present. `github` source has no `path:` field. `ref:` is documented as defaulting to default branch on all git-based sources. Marketplace clone ref vs plugin source ref decoupling is documented with an explicit Note callout. Release-channels pattern uses `github` source with explicit `ref: "stable"` (or `"latest"`). All phase-0/0.5 evidence quotes that this verifier checked match the live docs verbatim.

3. **Verifier ran adversarial discipline against own analysis.** Phase 3's assumption audit table flagged "GitHub default-branch field for cairn" as BELIEVED-not-verified. Committed ADR D9 (F3 audit check 9 acceptance criterion) is the operator-side defense. Recommend: run `git remote show origin | grep -i 'HEAD branch'` (or `gh api repos/firaaz/cairn --jq '.default_branch'`) before merging the M7 implementation feature.

End of independent verification.

