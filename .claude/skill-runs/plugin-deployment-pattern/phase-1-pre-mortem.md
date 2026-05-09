# Phase 1 — Pre-Mortem

Decision: "Plugin deployment pattern: how does `dist/` reach a ref consumers can resolve via `/plugin install`?"

Source: lead-session synthesis, 2026-05-09. Inputs: `phase-0-constraints.md` (37 numbered constraints, 5 conflicts, 4 docs ambiguities), `phase-0.5-journey.md` (13 boundaries, 11 gaps).

**Frame.** It is 2026-08-09 (3 months from now). The deployment pattern was chosen, M5+M6 closed, F3 audit check 9 went green. Then a failure surfaced. Walk back through the failure modes — these become the test cases each Phase 2 approach must defend against.

Severity: **Critical** = consumer install broken with no mechanical recovery; **High** = consumer install works but D-commitment violated or update channel broken; **Medium** = friction surfaces without breaking install/update.

## S1 — Schema-parse failure (CRITICAL, pre-existing, cross-approach)

**Trigger.** A consumer runs the README literal command `/plugin marketplace add https://github.com/firaaz/cairn`. Claude Code clones the repo, attempts to parse `.claude-plugin/marketplace.json`, encounters `"type": "git"`. The documented schema lists `source.source` with values `github | url | git-subdir | npm` (constraint 12; phase-0.5 Evidence 1). `"type"` is not the discriminator key; `"git"` is not a documented value.

**Mechanism of failure.** Either (a) `claude plugin validate` flags the manifest, the marketplace fails to register, and `/plugin install` returns "no such marketplace"; or (b) the validator silently passes on the unknown field, then `/plugin install` fails at source-resolution with an opaque error; or (c) a lenient parser tolerates it and accidentally works. None of (a)/(b)/(c) is documented (Phase 0 ambiguity A1).

**Who notices.** First-time consumer (Role 1) and existing-symlink consumer (Role 2) both. F3's audit check 9 is precisely the failure surface — until check 9 runs against a real install, this is unverified.

**Recovery cost.** None for the consumer (no install state to roll back), but **F3 is merge-eligible-but-not-merge-final** until check 9 passes. The cost is reputational: the F3 sweep-notes records a green migration runbook for a deployment that doesn't work.

**Defensive design implication.** Every Phase 2 approach MUST rewrite `marketplace.json` to a documented `source.source` shape. This is not optional and not differentiating — it's a structural prerequisite that lands with whichever approach. Phase 2 must show its specific schema rewrite (`source.source` value + which fields).

## S2 — Default-branch trap (CRITICAL, Approach A specifically)

**Trigger.** Approach A puts curated `dist/` on a long-lived `release` branch; default branch (`dev`) has `dist/` git-ignored. Consumer follows the README literal command — no `@release` qualifier. Marketplace add clones at `dev`-tip. Plugin source resolves against the marketplace's clone (Phase 0.5 Evidence 11) — `dist/` is absent on `dev`. Install fails with `Plugin directory not found at path: dist/` (Phase 0.5 Evidence 4).

**Mechanism of failure.** Marketplace.json's `source` field, if it uses a relative path or a `git-subdir` source omitting `ref`, resolves against the *cloned* ref — which is `dev`. The README's literal install command does not include `@release`. So either:

- (a) Default branch must change from `dev` → `release` (impacts cairn-the-repo's PR-target conventions and every fresh clone — Phase 0.5 Gap 2);
- (b) README/CONSUMER.md must rewrite the literal command to `/plugin marketplace add firaaz/cairn@release` (consumer-facing copy update + every existing screenshot/doc/blog post breaks);
- (c) `marketplace.json` `source.source` must use `github` with explicit `ref: "release"` (so the source resolution decouples from the marketplace's own clone-ref).

**Who notices.** Every first-time consumer running the README command. Every existing-symlink consumer running the upgrading-from-symlink runbook (`docs/upgrading-from-symlink.md:49` carries the same literal).

**Recovery cost.** Each consumer must individually update their local invocation OR cairn must update README/CONSUMER.md (a one-time cost) AND propagate via `/plugin update`. If default branch changes: every cairn maintainer's local `git fetch` produces a different default-branch ref, dev workflow disruption.

**Defensive design implication.** Approach A MUST pick option (c) — `marketplace.json` uses `source.source: "github"` with explicit `ref: "release"` — to keep consumers resolving the right ref without README rewrite. Other options re-introduce friction the M5 ADR's D8 carve-out (cairn maintainers stay on Path B self-symlink, undisturbed) is meant to avoid.

## S3 — npm consumer-side dependency (HIGH, Approach B specifically)

**Trigger.** Approach B requires `npm install @firaaz/cairn@0.x.y` at consumer install time (Phase 0.5 Evidence 5). The docs say "installed using `npm install`" but are silent on whether Claude Code shells out to consumer-side npm or uses an embedded npm client (Phase 0 ambiguity, also Phase 0.5 Gap 4). The plausible-default reading is "consumer-side npm" (because `registry` defaults to "system npm registry" and version-fallback returns `unknown`).

**Mechanism of failure.** A consumer running cairn (e.g., `complex-rag-analysis`) is a Python uv project; npm is not on PATH; install fails with a binary-missing error. Cairn's stated system-dep contract names only `jq` and `ruff` (`CLAUDE.md:13-15`); adding `npm` extends the consumer-prerequisite floor.

**Who notices.** Any consumer in a non-JS / non-Node project. `complex-rag-analysis` is one such. The portfolio-evaluator in the M5 review (`docs/reviews/2026-04-23-from-portfolio-evaluation.md`) was a Next.js project — they would have npm. So the failure mode is consumer-segment-dependent.

**Recovery cost.** Consumer installs npm (one-time, ~5 min) but this is a hard friction the M5 ADR didn't budget for. CONSUMER.md prerequisites + post-install hook validates and warns on missing system deps (M5 ADR Brainstorm decision 8) — npm would be added to that list, increasing consumer onboarding cost.

**Defensive design implication.** Approach B must (a) update CONSUMER.md prerequisites to add npm explicitly, (b) extend `scripts/postinstall_validate.py` to check for npm, (c) accept that the prerequisite floor expands. The vision-commitment friction is not lethal, but it pushes cairn's install footprint outward.

## S4 — Two-step release coupling (HIGH, Approaches B and C)

**Trigger.** Maintainer cuts release v0.x.y. Step (i): publish artefact (npm publish for B; create+push tag for C). Step (ii): bump `marketplace.json`'s pinned version on `dev` (`source.version` for B; `source.ref` for C). Maintainer does (i), forgets (ii) — or vice versa.

**Mechanism of failure.** Consumers' `/plugin update` re-pulls the marketplace clone, parses `marketplace.json`, sees the unchanged `version` / `ref`, reports "already at the latest version" (Phase 0.5 Evidence 8). The new artefact is published but not surfaced to consumers. Worse: if step (ii) lands first (marketplace.json bumped before npm publish / tag push), consumers' install fails at source-resolution with "package not found" or "ref not found".

**Mechanism details per approach.**
- **B (npm)**: 3-way version alignment — `dist/.claude-plugin/plugin.json` `version` (Phase 0.5 Evidence 9: "plugin.json wins silently over marketplace entry"), `marketplace.json` plugin entry's `source.version`, and the npm-published version. All three must agree. Two of three live in cairn-the-repo (one in `dist/` after build, one in the marketplace.json on `dev`); one lives on the npm registry.
- **C (git-subdir + tag)**: 2-way alignment — `dist/.claude-plugin/plugin.json` `version` and `marketplace.json` `source.ref`. Both live in cairn-the-repo. The `version` lives on the tagged commit; the `ref` lives on `dev`'s `marketplace.json`.

**Who notices.** Consumers running `/plugin update` after a botched release. Maintainer notices on next release-cadence review.

**Recovery cost.** If (i) without (ii): publish a fix-up commit bumping marketplace.json. Consumers re-update. If (ii) without (i): immediately revert the marketplace.json bump or push the artefact. Each is recoverable, but each requires an explicit fix-up commit + a follow-up release-checklist update.

**Defensive design implication.** Approaches B and C MUST mechanize the two-step coupling — either via a single CI workflow that enforces both steps atomically (publish + commit-bump in the same job), or via a release-checklist gate + a CI assertion that catches the divergence. Approach A's release is one push (release-branch tree replacement + plugin.json version bump in one commit), avoiding this class of failure structurally.

## S5 — INV-001 commit-prefix binding under auto-commit CI (HIGH, all approaches)

**Trigger.** A release CI workflow auto-commits to `release` branch (A), to a release-only commit + tag (C), or runs `npm publish` plus an auto-commit bumping marketplace.json on `dev` (B). The auto-commit's message prefix must match a Conventional Commits prefix in `_FALLBACK_REGISTRY` (`docs/ARCHITECTURE.md:13-20`, INV-001). Common candidates: `chore:`, `chore(release):`, `release:`. The exact registry contents must be checked (Phase 0 constraint 21).

**Mechanism of failure.** CI emits a commit with an unregistered prefix — e.g., `release(v0.x.y): publish dist payload`. INV-001 hook flags the commit (or the validator flags it post-merge). The release breaks the cairn-the-repo's commit-prefix discipline; either the prefix gets registered via a superseding ADR (governance overhead) or CI is rewritten to use a registered prefix.

**Who notices.** Cairn maintainer on next `validate_architecture.py` run, OR `reality-check.sh`/INV-001 hook on the auto-commit itself.

**Recovery cost.** Low if the prefix is unregistered-but-fixable (rewrite CI). Higher if a new prefix is genuinely needed and requires an ADR amendment.

**Defensive design implication.** All three approaches must specify the exact commit prefix the release CI emits, AND verify it is in the current `_FALLBACK_REGISTRY`. If not, the release-CI plan includes a lever to register the prefix BEFORE the first release runs.

## S6 — Detached `dist/` ref under git-subdir + tag (MEDIUM, Approach C)

**Trigger.** Approach C tags `v0.x.y` against a release-only commit that contains `dist/`. This commit may not be reachable from any branch — it's a detached commit, reachable only via tag. Future maintainer doing `git log dev` doesn't see it. `git branch --contains v0.x.y` returns empty.

**Mechanism of failure.** Not a consumer-facing failure (consumers pin to the tag, sparse-clone resolves). It's a maintainer-ergonomics failure: future debugging asks "why is there a tag pointing at a commit not on any branch?" without ready answers. Or: a maintainer running `git gc` aggressively could prune the tag's target if the tag itself is removed (impossible by accident, but a footgun).

**Who notices.** Future cairn maintainer doing release-history archaeology. Or a consumer on a network with shallow-clone constraints (the tag is reachable only via explicit fetch; default `git fetch` may not pull it).

**Recovery cost.** Low if a `release` branch is maintained alongside (the tag points at the branch's HEAD at release time, branch keeps the commit reachable). High if the maintainer prunes the branch or runs `git gc --prune=now` between releases.

**Defensive design implication.** Approach C should keep a `release` branch as a reachability anchor for tagged commits — at which point Approach C becomes structurally similar to Approach A's release-branch shape, plus tags. This is the **Approach D hybrid** the journey trace surfaced.

## S7 — D2 stability stance violated by ref-omission footgun (HIGH, Approaches A and C)

**Trigger.** Maintainer or first-time documentation reader writes `marketplace.json` without `source.ref` (Approach A) or with `source.ref` omitted (Approach C). Per Phase 0.5 Evidence 3, `ref` defaults to repository default branch. `git-subdir` and `github` sources without `ref` track the moving HEAD of `dev`.

**Mechanism of failure.** Every commit on `dev` pulls consumers forward — directly violating M5-ADR-D2 (`m5-plugin-distribution-and-symlink-retire/D2`: "consumers pin via SHAs/tags"). Consumers lose pin-aware stability without realizing it; one accidentally-merged-to-`dev` regression cascades to every consumer immediately.

**Who notices.** Every consumer who ran `/plugin update` after the bad merge. Effect is N consumers × bad-commit-magnitude.

**Recovery cost.** High. The bad commit must be reverted on `dev`, AND a follow-up commit must mechanize ref-pinning. Some consumers may already have applied damage (if cairn's hooks now silently fail-open on the bad commit, downstream consumer sessions ran unprotected).

**Defensive design implication.** Approaches A and C must:
- (i) Make `source.ref` mandatory in the manifest (lint or build-time assertion that flags absence).
- (ii) Document the failure mode prominently (CONSUMER.md or operational-reference.md callout).
- (iii) Preferably automate the ref bump on every release (CI sets `source.ref` from the new tag/branch).

Approach B inherits a different but equivalent footgun: omitting `version` for npm sources falls back to `unknown` (Phase 0.5 Evidence 7), breaking update detection. Same defensive shape: mandatory explicit version.

## S8 — Schema breaking change upstream (MEDIUM, all approaches)

**Trigger.** Anthropic ships a marketplace.json schema change (e.g., renames `source.source` → `source.kind`, deprecates `git-subdir`, restructures field shapes). Cairn's frozen `marketplace.json` and pinned consumers don't auto-update.

**Mechanism of failure.** New consumers' Claude Code parses today's manifest as invalid; old consumers' pinned cache continues working until they `/plugin update` (which re-pulls marketplace.json, hitting the parse failure). The schema-validator that flagged S1 might also flag this.

**Who notices.** Anyone trying to install or update cairn after Anthropic's change.

**Recovery cost.** Cairn ships a follow-up commit updating `marketplace.json` to the new schema. Consumers run `/plugin update`. If a consumer's pin is on a SHA before the schema-fix, they have to re-pin.

**Defensive design implication.** This is unavoidable (cairn doesn't control the upstream schema). Mitigation: monitor `code.claude.com/docs/en/plugin-marketplaces` for schema changelog; subscribe to Anthropic plugin-API release notes if they exist. Phase 4 ADR's Risk Register must explicitly carry this as accepted residual risk.

## S9 — Cairn maintainer dogfood disrupted by deployment-pattern choice (MEDIUM, Approach A and any default-branch-mutating variant)

**Trigger.** Approach A's most-direct fix for S2 is changing default branch from `dev` → `release`. Cairn maintainers' `git clone https://github.com/firaaz/cairn.git` lands them on `release` (the deployment branch with `dist/` materialized) instead of `dev` (the dev-loop branch).

**Mechanism of failure.** Maintainer opens a fresh clone, runs `uv sync`, attempts to test a hook change. Because they're on `release`, they're seeing the *built* `dist/` payload, not the canonical sources. They edit `dist/checks/role_guard.py` instead of `checks/role_guard.py` — the change is overwritten by next CI build. Or: they get confused, push to `release` directly, breaking the deployment.

**Who notices.** Cairn maintainer (single role; small population — currently 1).

**Recovery cost.** Low individually, but compounds: every maintainer-onboarding step now starts with "make sure you `git checkout dev`". The M5 ADR's D8 ("cairn-self stays on Path B") was meant to avoid exactly this kind of friction.

**Defensive design implication.** Approach A's resolution of S2 must NOT change the default branch. It must use `marketplace.json` `source.source: "github"` with explicit `ref: "release"`, so the consumer resolves `release` while the default branch stays `dev`.

## S10 — Approach C release-branch absorption collapses C into A (low-stakes structural observation)

**Trigger.** Phase 2C is asked to defend against S6 (detached commits). The natural defense — keep a `release` branch as a reachability anchor — makes C and A converge on the same shape: a `release` branch carrying `dist/`, with C adding tag-pins on top.

**Mechanism of failure.** Not a failure per se; a structural observation that C's "tag-only" stance may be unstable under real maintenance pressures. Phase 2 must reckon with whether C is genuinely separable from A or whether it is a refinement of A. If the latter, the comparison table becomes A-flat vs A-with-tags vs B; the operator-named C as "GitHub release artifact" doesn't have a documented landing point regardless.

**Defensive design implication.** Phase 2 should explicitly test whether C-without-release-branch is workable (relying purely on tag reachability). If not, Phase 2 should propose **Approach D = A + tags** as the strongest synthesis: release branch (S6 reachability anchor, S2 default-branch decoupling via explicit `ref: "release"`) plus tags (cairn-D2 SHA/tag pinning).

## Cross-scenario observations

**Scenarios that apply across all approaches (S1, S5, S8).** These are baseline costs, not differentiators. Phase 2 must address them but should not weight them heavily in the comparison.

**Scenarios that decisively shape comparison (S2, S3, S4, S7, S9).** These split A/B/C cleanly:
- A bears S2 + S5 + S9 (default-branch trap, commit-prefix discipline, dogfood disruption).
- B bears S3 + S4 + S5 (npm prereq, two-step coupling, commit-prefix discipline).
- C bears S4 + S5 + S6 (two-step coupling, commit-prefix discipline, detached-commit ergonomics).

**The hybrid Approach D (A+C, release-branch + tags) bears S5 + S9 only** if it uses `source.source: "github"` with `ref: "release"` AND tags the release commits. This may be the strongest synthesis.

## What Phase 2 must explicitly do

Each Phase 2 sub-agent is instructed to score its approach against the 10 scenarios above, citing which scenarios apply and how the approach defends against each. Approaches that decline to address an applicable scenario must say so explicitly and accept the residual risk. Approaches that propose new defenses Phase 1 didn't anticipate must surface the defense.

Phase 2 is also explicitly authorized to propose **Approach D** as a fourth approach if its structural properties dominate A/C/B head-to-head on this severity-tagged scoring.

End of Phase 1.
