---
id: m5-plugin-deployment-pattern
status: accepted
firmness: firm
supersedes: []
supersedes-sections: [m5-plugin-distribution-and-symlink-retire/D3]
superseded-by: null
topic: architecture
invariants-touched: []
date: 2026-05-09
---

# m5-plugin-deployment-pattern: M5 Plugin Deployment Pattern (Release Branch + Sync CI)

## Status

Accepted (post-`/decision` Phase 3 adversarial stress test, 2026-05-09; operator-selected A over runner-up D after full A/B/C/D enumeration). Phase 5 independent verification pending.

## Date

2026-05-09

## Context

`m5-plugin-distribution-and-symlink-retire` (firm, 2026-05-08) committed cairn to ship as a Claude Code plugin via its own marketplace. D3 of that ADR specified `marketplace.json` `source.path: "dist/"` and named CI as the populator of `dist/` "at release from a curated allow-list" (`docs/adr/m5-plugin-distribution-and-symlink-retire.md:55-68`). M5+M6 features F1, F2, F3 closed and merged onto `dev` at `6a6f430`.

Two operational gaps surfaced when F3 reached its audit:

1. **The `dist/` payload was never committed to any pushed ref.** `git ls-tree -r HEAD` and `git log --all --diff-filter=A -- 'dist/*'` are empty. F1 shipped the build pipeline (`scripts/build_dist.py` + `.github/workflows/dist-gate.yml`) but no publish step. `/plugin install cairn@cairn-marketplace` would resolve `path: "dist/"` against a missing directory.

2. **Today's `marketplace.json` schema does not match the documented Anthropic schema.** The current manifest declares `"type": "git"` (`.claude-plugin/marketplace.json:11`); the documented discriminator is `source.source` with values `github`, `url`, `git-subdir`, `npm`, plus a literal relative-path string (`code.claude.com/docs/en/plugin-marketplaces:231-238`). `"type": "git"` is not in the documented schema. The manifest may not parse at all on a real `/plugin install`.

F3's audit check 9 (manual end-to-end real install) was recorded as PENDING precisely on these gaps (`.claude/skill-runs/cairn-m6-f3-migration-and-symlink-retire/integration/sweep-notes.md`). M5+M6 is structurally incomplete from the consumer's perspective.

`/decision` ran 2026-05-09 (teamed pattern, parallel Phase 0/0.5 + Phase 2 across A/B/C):
- **Phase 0** surfaced 37 numbered constraints across deployment / versioning / schema / CI / consumer-resolution / dogfooding / migration / docs / other, with 5 explicit conflicts and 4 external-docs ambiguities (`.claude/skill-runs/plugin-deployment-pattern/phase-0-constraints.md`).
- **Phase 0.5** traced four role journeys (first-time consumer, existing-symlink consumer, release author, post-merge maintainer) and 13 boundaries B1–B13, with 11 numbered gaps; surfaced Approach D as a Gap 11 hybrid (`.claude/skill-runs/plugin-deployment-pattern/phase-0.5-journey.md`).
- **Phase 1** named 10 severity-tagged scenarios S1–S10 across technical / scale / integration / adoption (`.claude/skill-runs/plugin-deployment-pattern/phase-1-pre-mortem.md`).
- **Phase 2** forced-enumerated three approaches plus the surfaced Approach D: A=release-branch+sync-CI, B=npm-publish, C=git-subdir+tag (re-grounded; original "GitHub release archive" had no documented schema landing point), D=C-anchored hybrid (`.claude/skill-runs/plugin-deployment-pattern/phase-2-approach-{A,B,C}.md`).
- **Phase 3** stress-tested D and steel-manned A as runner-up; surfaced two real bugs in D's CI workflow (permission gap + version-assertion gap); ranked A and D as roughly tied with marginal lean toward A on simpler ceremony + structurally-absent S4 + first-party CI (`.claude/skill-runs/plugin-deployment-pattern/phase-3-adversarial.md`).
- **Operator selected Approach A** at the Phase 3 boundary.

## Decision

### D1 — Plugin payload deploys via a long-lived `release` branch with shape-(i)

A new long-lived branch named `release` carries the plugin payload. Its working-tree HEAD IS the curated dist-payload directly — there is no `dist/` subdirectory on `release`; the build output's contents land at branch root. Layout:

```
release/
├── .claude-plugin/plugin.json
├── agents/{phase-1-tdd.md, phase-2-tdd.md, phase-3-tdd.md, phase-4-tdd.md, triager-tdd.md, role-topology.yaml}
├── checks/{role_guard.py, reality-check.sh, reversibility-guard.sh}
├── hooks/hooks.json
├── skills/cairn-tdd-feature/
├── templates/handoff.md
└── postinstall_validate.py
```

This shape is forced by the `source.source: "github"` choice (D2 below): for `github` source, the entire repo at the resolved ref IS the plugin root; no `path` field is documented for that source-type (`code.claude.com/docs/en/plugin-marketplaces:280-288`).

The default branch stays `dev`; `dist/` is git-ignored on `dev`. The maintainer dogfood loop reads canonical paths through `.slice-system → .` (`m5-plugin-distribution-and-symlink-retire/D8` preserved).

### D2 — `marketplace.json` uses `source.source: "github"` with explicit `ref: "release"`

The manifest is rewritten from today's `{ "type": "git", "url": "...", "path": "dist/" }` (schema-invalid) to:

```json
{
  "source": "github",
  "repo": "firaaz/cairn",
  "ref": "release"
}
```

`source.source: "github"` is one of the four documented `source.source` values (`code.claude.com/docs/en/plugin-marketplaces:231-238`). `repo` is the `owner/repo` shorthand. `ref: "release"` decouples plugin-source resolution from the marketplace's clone ref — consumers' `/plugin marketplace add https://github.com/firaaz/cairn` clones the marketplace at default branch (`dev`), but the plugin source resolves a separate clone at `release`. This is the structural defense against the default-branch trap (Phase 1 S2).

The literal consumer commands at `README.md:19`, `CONSUMER.md:14`, and `docs/upgrading-from-symlink.md:49` remain UNCHANGED. No `@release` qualifier; no docs churn.

### D3 — `dist/.claude-plugin/plugin.json:version` is the canonical consumer-visible update signal

Per `code.claude.com/docs/en/plugin-marketplaces:715-718` ("the `plugin.json` value always wins silently" over marketplace entry's `version`), `marketplace.json`'s plugin entry omits the `version` field. The single source of truth for the consumer-visible version is `dist/.claude-plugin/plugin.json:version`, which is bumped per release per `m5-plugin-distribution-and-symlink-retire/D2` ("explicit semver-via-tags pre-v1, manual bumps").

The bump source is `.claude-plugin/plugin-template.json:version`; `scripts/build_dist.py:30` copies the template into `dist/`.

This operationalizes `m5-plugin-distribution-and-symlink-retire/D2`'s "consumers pin via SHAs/tags" intent without violating it: consumers track the `release` branch's HEAD, but updates only ship when plugin.json's `version` field is bumped (per the docs' explicit-version cache-key behavior at `code.claude.com/docs/en/plugins-reference:1004-1008`).

### D4 — Default branch stays `dev`

No default-branch change. Cairn maintainers cloning `firaaz/cairn` land on `dev`; the dogfood loop is unaffected. `m5-plugin-distribution-and-symlink-retire/D8` ("cairn-self stays on Path B self-symlink") is preserved structurally.

### D5 — Release CI workflow is `workflow_dispatch`-triggered with version cross-check

A new workflow `.github/workflows/release-publish.yml` runs on `workflow_dispatch` (manual button click) with two inputs: `version` (semver string, e.g. `0.2.0`) and optional `source_ref` (default: `dev`). The workflow:

1. Checks out the source ref.
2. Builds `dist/` via `scripts/build_dist.py` to `/tmp/dist-out`.
3. Reads `dist/.claude-plugin/plugin.json:version`.
4. **Asserts the input `version` equals the built `version`.** If they diverge, the workflow fails before any push — catching the "I meant to release 0.2.0 but plugin-template still says 0.1.0" failure mode.
5. Force-with-leases the `release` branch tree to match `/tmp/dist-out`.
6. Optionally tags the release commit as `v0.x.y` (D8 below).

`workflow_dispatch` is the primary trigger to keep releases explicit operator actions. A secondary `push: tags: ['v*']` trigger is permitted for `claude plugin tag`-driven releases.

### D6 — Force-with-lease, not force, on `release`

Each release replaces the `release` branch tree deterministically. Merges are not used; `--force` is blocked by cairn's force-push policy (`CLAUDE.md` "Force-push policy"); `--force-with-lease` is the only permitted form and is the workflow's push verb.

### D7 — Schema-shape lint asserts manifest validity

A new test `tests/unit/test_marketplace_schema.py` loads `.claude-plugin/marketplace.json` and asserts:
- `plugins[0].source.source` is one of `{github, url, git-subdir, npm}`.
- `plugins[0].source.repo` matches `^firaaz/cairn$`.
- `plugins[0].source.ref` equals `"release"`.

The test is gated by `dist-gate.yml` so every PR catches an accidentally-omitted `ref` or a regression to the broken `type: git` shape. Phase 1 S7 (D2 stability stance violated by ref-omission) and S1 (schema-parse failure) are mechanically defended.

### D8 — Optional release-tagging step in CI

Each `workflow_dispatch` run also creates and pushes a `v0.x.y` tag pointing at the `release`-branch HEAD post-sync. The tag step is conditional on `github.event_name == 'workflow_dispatch'`. This provides:
- A SHA-pinning escape hatch for D2-strict consumers (they can override `ref: "release"` with `ref: "v0.x.y"` or `sha: "<40-char>"` in their own marketplace.json fork or in a private overlay).
- An archaeology anchor: `git tag -l 'v*'` lists all releases; `git log v0.1.0..v0.1.1 -- :^.claude-plugin/plugin.json` shows what changed in the payload between releases (excluding the version bump).

### D9 — F3 audit check 9 acceptance criterion for the implementing feature

The follow-up feature that implements this ADR (the M7 plugin-deployment-pattern feature) MUST include F3's audit check 9 as a verification step in its intent.md. The check is the manual end-to-end install verification: a fresh consumer in a non-cairn project runs the literal README commands, the install completes, the post-install validator passes, hooks fire. The feature is not merge-final until check 9 records green.

This couples the deployment-mechanism feature's acceptance to the resolution of F3's PENDING manual verification (`.claude/skill-runs/cairn-m6-f3-migration-and-symlink-retire/integration/sweep-notes.md` "Pending manual verification — audit check 9").

## Consequences

### Easier (positive)

- **F3 audit check 9 unblocks.** A fresh consumer running `/plugin marketplace add https://github.com/firaaz/cairn` + `/plugin install cairn@cairn-marketplace` resolves the manifest at `dev`-tip, follows `source.source: "github" ref: "release"` to the `release` branch, and gets a working install. F3 becomes merge-final.
- **M5+M6 milestone closes.** `m5-plugin-distribution-and-symlink-retire/D9` (atomic ship) was structurally incomplete; this ADR's implementation closes it.
- **The schema-bug is fixed.** Today's `"type": "git"` (not in documented schema) is replaced with the documented `source.source: "github"` shape. `claude plugin validate` will accept the new manifest.
- **The literal consumer commands DO NOT change.** `README.md:19`, `CONSUMER.md:14`, and `docs/upgrading-from-symlink.md:49` are unchanged. Zero docs churn for consumer-facing copy.
- **No two-step release coupling.** One push to `release` (force-with-lease) carries both the new `dist/` payload and the bumped `plugin.json:version`. Phase 1 S4 ("two-step release coupling") is structurally absent under A.
- **No expansion of consumer prereq floor.** Cairn's prereq floor remains `{jq, ruff, python3}` (`CLAUDE.md:13-15`). No npm dependency vs Approach B.
- **First-party CI only.** No third-party GitHub Actions like `peter-evans/create-pull-request@v6` (which D would have required). Smaller supply-chain trust boundary.
- **Maintainer dogfood unaffected.** `m5-plugin-distribution-and-symlink-retire/D8` (Path B self-symlink) is preserved structurally; default branch stays `dev`.
- **Version cross-check catches a real failure mode.** D5's workflow input vs built `plugin.json:version` assertion catches the "I meant 0.2.0 but plugin-template still says 0.1.0" footgun before any push.

### Harder (negative)

- **`release` branch is a CI-only deploy target with non-obvious purpose.** A contributor seeing `release` in `git branch -a` may not understand it's CI-managed and force-with-leased on every release. Documentation responsibility (CHANGELOG.md note + this ADR's "release-branch character" section serve as the canonical reference).
- **Force-with-lease pushes from CI are a permission escalation.** Today's CI is read-only (`dist-gate.yml`); `release-publish.yml` requires `contents: write`. The default `GITHUB_TOKEN` covers this on unprotected branches; if `release` is later protected, a fine-grained PAT scoped to `release` is needed.
- **Two file-layout shapes for one repo.** `dev` carries cairn's full layout (`scripts/`, `docs/`, `tests/`, `.claude/`, etc.); `release` carries only the curated dist-output layout. Visually confusing for first-time contributors. Mitigation: README banner + GitHub branch description.
- **`release` history is rewritten on each release.** Force-with-lease replaces the previous release's HEAD; archaeology requires looking at tags (which D8 ensures always exist). Without tags, `git reflog` is the only path back.
- **`dist/`-on-`release` is git-tracked content.** The diff between releases is one big commit per release; reviewers asking "what changed in the payload between v0.1.0 and v0.2.0" must `git diff v0.1.0..v0.2.0` (excluding plugin.json's version bump). The release commit message includes the source SHA to enable trace-back.
- **`source.source: "github"` is documented to clone at `ref: "release"` separately from the marketplace's clone.** This decoupling is supported by the docs (`plugin-marketplaces:280-288` describes `github` source with its own `ref` field) but never empirically verified against Claude Code's actual resolver. F3 audit check 9, run against this ADR's manifest before merge per D9, is the empirical verification.

## Alternatives Considered

### Approach D — `git-subdir` + tag + release-branch anchor (close runner-up)

Rejected after Phase 3 adversarial stress test. D's strengths: tag-pin (verbatim `m5-plugin-distribution-and-symlink-retire/D2` text fit), normal merge history on `release` (no force-with-lease), manifest fidelity to D3's `path: "dist"` text. D's weaknesses: 3-step ceremony (tag + dispatch + auto-PR merge); third-party dep on `peter-evans/create-pull-request@v6` for the auto-PR; two real spec gaps surfaced in Phase 3 (workflow `permissions` block missed `pull-requests: write`; plugin.json:version vs workflow inputs.version assertion not specified). Operator chose A for simpler ceremony + structurally-absent S4 + first-party CI. (`.claude/skill-runs/plugin-deployment-pattern/phase-2-approach-C.md`, `.../phase-3-adversarial.md`)

### Approach B — npm publish (`source.source: "npm"`)

Rejected. B adds `npm` to cairn's consumer prereq floor — `complex-rag-analysis` is a Python uv project; the M5 portfolio review's evaluator was a Next.js project. B's friction is consumer-segment-dependent. B also introduces a 3-way version triangle (plugin.json + marketplace.json + npm registry) and an external trust boundary (npm-org credentialing under `@firaaz/`). B's structural advantages (npm immutability ≥ git-tag immutability; `--provenance` supply-chain attestation; bandwidth efficiency) do not outweigh the prereq-floor expansion for cairn's consumer profile. (`.claude/skill-runs/plugin-deployment-pattern/phase-2-approach-B.md`)

### Default-branch change (`dev` → `release`)

Rejected. The simplest-but-naive A would change default branch from `dev` to `release`, eliminating the `@ref` qualifier requirement. But this disrupts cairn maintainer dogfood: `git clone firaaz/cairn` lands on `release` (the curated dist-output tree), not `dev` (the canonical sources). Maintainer would edit `dist/checks/role_guard.py` and have it overwritten by next CI sync. `m5-plugin-distribution-and-symlink-retire/D8` ("cairn-self stays on Path B") is incompatible with default-branch change. The strongest A explicitly preserves `dev` as default and uses `source.source: "github"` with `ref: "release"` to decouple consumer-resolution from default-branch convention.

### Relative-path source (`./dist`)

Rejected. Per `code.claude.com/docs/en/plugin-marketplaces:259`, relative paths "resolve relative to the marketplace root" — the marketplace's cloned ref. If marketplace.json lives on `dev` (default branch), `./dist` resolves on `dev`, where `dist/` is git-ignored. Install fails with `Plugin directory not found at path: ./dist` (`code.claude.com/docs/en/plugins-reference:929`). Relative-path source is structurally incompatible with "marketplace lives on `dev`, plugin lives on `release`."

### Approach C-detached (no release branch, tag-only commits)

Rejected. Tagged commits would live as orphans not reachable from any branch. `git branch --contains v0.1.0` empty; future maintainer doing `git log dev` doesn't see release commits. Aggressive `git gc --prune` could prune the orphan if a tag is later removed. Network-shallow-clone consumers may fetch defaults that don't include the tag. C-anchored (≡ Approach D) dissolves S6 by maintaining the release branch as a reachability anchor; the cost is one long-lived branch. C-detached has no unique advantage over D.

### Operator-named "GitHub release artifact" source

Rejected as mechanism-ambiguous. The Anthropic plugin-marketplaces docs do not document a `source.source: "github-release"` value, nor any tarball/archive download mechanism. A search across `code.claude.com/docs/en/plugin-marketplaces:225-413` for `tarball`, `release`, `archive` as schema field names returned zero hits. The closest documented mechanism is `git-subdir` against a tag (Approach D's foundation); a true GitHub-release-artifact path is structurally not supported by the marketplace schema.

## Risk Register

| # | Phase 1 scenario | Defense under D1–D9 | Residual risk |
|---|---|---|---|
| 1 | S1 — Schema-parse failure (CRITICAL, cross-approach) | D2: rewrite `marketplace.json` to documented `source.source: "github"` shape. D7: `tests/unit/test_marketplace_schema.py` lints schema-shape every PR. D9: F3 audit check 9 empirically verifies the rewritten manifest before merge. | Low. Add `claude plugin validate` invocation to `dist-gate.yml` if/when the CLI is stable. |
| 2 | S2 — Default-branch trap (CRITICAL, A-specific) | D2: explicit `ref: "release"` decouples plugin-source resolution from marketplace clone ref. D4: default branch stays `dev`. D7: lint asserts `ref` non-empty. | Zero from the `@ref` trap itself. Consumers never type `@release`. |
| 3 | S3 — npm consumer-side dependency | n/a — A does not use npm. | n/a |
| 4 | S4 — Two-step release coupling | Structurally absent under A. One push to `release` carries both `dist/` payload and `plugin.json:version` bump. | n/a |
| 5 | S5 — INV-001 commit-prefix binding (HIGH, all approaches) | CI workflow's `git commit` uses `chore:` prefix. Verified `chore:` is in `_FALLBACK_REGISTRY` at `scripts/validate_architecture.py:279` with `_verify_pass_through` verifier (line 348). | Low. Implementing-feature ships a unit test asserting the workflow's commit-message format matches a registered prefix. |
| 6 | S6 — Detached commits | n/a — A's `release` is a long-lived branch; commits are reachable via the branch. D8 optional tagging adds a parallel anchor. | n/a |
| 7 | S7 — D2 stability stance violated by ref-omission | D7: `tests/unit/test_marketplace_schema.py` asserts `source.ref == "release"`. D5: workflow's `version` input cross-checked against built `plugin.json:version`; mismatch fails before push. | Low. A future maintainer could remove the lint, but doing so requires an ADR amendment trail. |
| 8 | S8 — Schema breaking change upstream | Accepted residual; cairn doesn't control Anthropic's schema. Mitigation: monitor `code.claude.com/docs/en/plugin-marketplaces` changelog. | Medium. If Anthropic deprecates `source.source: "github"`, cairn ships a follow-up ADR + manifest rewrite. Existing pinned consumers continue working until they `/plugin update`. |
| 9 | S9 — Cairn maintainer dogfood disrupted | D4: default branch stays `dev`. D2: explicit `ref: "release"` keeps consumers on `release` while maintainers operate on `dev`. The `release-publish.yml` workflow is invoked via the GitHub Actions UI (button click), not local checkout. | Low. A maintainer could `git checkout release` out of curiosity and find a different file layout. Mitigation: README banner + branch description + this ADR's "release-branch character" prose. |
| 10 | S10 — Approach C absorption | n/a — A's release-branch shape vindicates the primitive both A and C-anchored need. D8 optional tagging gives D2-strict consumers SHA-pin affordance without making the manifest depend on it. | n/a |

Additional residuals not in the Phase 1 scenario set:

- **Force-with-lease history loss without tagging.** Mitigated by D8 making the optional tagging step always-on for `workflow_dispatch` runs.
- **`release` branch protection escalation.** Deferred decision: ship A unprotected initially; add branch protection in a follow-up if abuse surfaces (e.g., maintainer accidentally pushes manually).
- **Brief inconsistency window during force-with-lease.** A consumer running `/plugin update` exactly during the workflow's force-with-lease push may see a transient git-pull failure. Phase-0.5 Evidence 12 (`code.claude.com/docs/en/plugin-marketplaces:1004-1006`) confirms Claude Code's failure handler removes-and-re-clones, mostly absorbing this. Residual: vanishingly small.

## Verification Trail

All artefacts under `.claude/skill-runs/plugin-deployment-pattern/`:

- `brief.md` — operator-specified question, three operator-named approaches, citation rules, adversarial discipline.
- `phase-0-constraints.md` — 37 numbered constraints, 5 conflicts, 4 docs ambiguities (subagent: general-purpose).
- `phase-0.5-journey.md` — 13 boundaries B1–B13, 11 gaps, 12 verbatim Anthropic-doc evidence quotes (subagent: general-purpose).
- `phase-1-pre-mortem.md` — 10 severity-tagged scenarios S1–S10 (lead synthesis).
- `phase-2-approach-A.md`, `phase-2-approach-B.md`, `phase-2-approach-C.md` — three steel-mans (subagents: Plan; outputs persisted by lead due to read-only mode).
- `phase-3-adversarial.md` — disconfirming search on Approach D, steel-man of A, assumption audit, two real bugs in D's CI workflow surfaced (lead synthesis).

Mechanism evidence: `code.claude.com/docs/en/plugin-marketplaces` and `code.claude.com/docs/en/plugins-reference` (fetched 2026-05-09 by Phase 0 + Phase 0.5 subagents). Direct code verification of `.claude-plugin/marketplace.json:10-14`, `scripts/build_dist.py:18-33`, `.github/workflows/dist-gate.yml`, `scripts/validate_architecture.py:264-284,348`.

## Implementation contract for the follow-up feature

This ADR's commitments require a new feature (per `feature-slice-model`) whose plan doc lives at `docs/plans/<date>-cairn-m7-plugin-deployment.md` (or similar). The feature MUST:

1. Rewrite `.claude-plugin/marketplace.json` to the D2 shape.
2. Create `.github/workflows/release-publish.yml` per D5/D6.
3. Create `tests/unit/test_marketplace_schema.py` per D7.
4. Add the `release-publish.yml` workflow's commit-prefix to a unit-test assertion (S5 mitigation).
5. Run F3 audit check 9 against the new manifest as part of its acceptance, before merge to `dev` (D9).
6. Update CHANGELOG.md with a note explaining the `release` branch's character (CI-only deploy target; force-with-leased on each release; do not push manually).
7. Optionally: add `dist/` to `.gitignore` on `dev` (it already isn't tracked, but explicit gitignore prevents accidental commits).

The feature does NOT need to:
- Update `README.md`, `CONSUMER.md`, or `docs/upgrading-from-symlink.md` install commands (they remain unchanged per D2).
- Amend `m5-plugin-distribution-and-symlink-retire`'s body prose (this ADR's `supersedes-sections: [m5-plugin-distribution-and-symlink-retire/D3]` is the canonical pointer; M5's frontmatter remains as-is per cairn's append-only ADR policy).
