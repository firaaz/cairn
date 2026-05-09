# Phase 3 — Adversarial Stress Test

Author: lead-session synthesis, 2026-05-09. Inputs: Phase 0/0.5/1/2A/2B/2C.

**Frame.** Per the protocol: take the strongest approach and attack it. Per operator memory `feedback_attack_before_synthesis.md`: mount adversarial attacks on every load-bearing claim before synthesis; default-to-acceptance is the named failure mode.

**Strongest approach from Phase 2:** Approach D (C-anchored: `source.source: "git-subdir"` pinned to `source.ref: "v0.x.y"`, with the tagged commit anchored on a long-lived `release` branch).

**Runner-up:** Approach A (`source.source: "github"` with `ref: "release"`; release-branch shape-(i) where the branch tree IS the plugin root).

## Disconfirming search on Approach D

**Attack 1 — Does `git-subdir` decouple from marketplace clone ref?** D's S2 defense rests on the claim that `git-subdir` source resolution uses its own clone (independent of the marketplace's clone), so the marketplace can live on `dev` while the plugin is pinned to `v0.x.y`. Phase-0.5 Evidence 11 (`plugin-marketplaces:259`) explicitly addresses relative-path sources only — relative paths "resolve relative to the marketplace root." It does NOT directly state whether `git-subdir` source resolution clones independently or reuses the marketplace clone.

**Verification check.** Phase-0.5 Evidence 2 (`plugin-marketplaces:329-331`) reads: "Use `git-subdir` to point to a plugin that lives inside a subdirectory of a git repository. Claude Code uses a sparse, partial clone to fetch only the subdirectory, minimizing bandwidth for large monorepos." This implies an independent clone — sparse-clone of a specific URL+ref+path. Combined with Phase-0.5 Evidence 1 (the `git-subdir` field shape requires `url`), the source object IS its own resolution unit. **The decoupling claim is supported by mechanism evidence but never empirically verified.** Phase 2C honestly named this as "not empirically verified against Claude Code's actual git-subdir resolver."

**Verdict.** Believed-with-evidence, not directly verified. Risk if wrong: D's S2 defense degrades to A's S2 defense (must use `@release` qualifier or change default branch). Mitigation: F3 audit check 9, when run against the chosen-and-shipped manifest, IS the empirical verification. If D's manifest doesn't resolve, we discover before consumers do.

**Attack 2 — Does `git-subdir` work with `ref: "v0.x.y"` (a tag, not a branch)?** Phase-0.5 Evidence 3 confirms `ref` accepts "branch or tag" for `git-subdir`. Direct mechanism evidence. No serious attack.

**Attack 3 — The `release` branch's tree shape under D.** Phase 2C's workflow merges the source SHA into `release` then adds `dist/`. So `release` carries the full repo at the source SHA PLUS `dist/`. For consumers using `git-subdir` with `path: "dist"`, only `dist/` matters via sparse-clone. But the branch is ~the same size as `dev` plus `dist/`. **A's shape-(i) is leaner** (release tree IS dist contents, no extraneous files).

**Verdict.** Real trade-off. D's `release` is heavier than A's `release`. Not a correctness issue — sparse-clone serves consumers regardless. Maintenance impact: a maintainer browsing `release` in the GitHub web UI sees a full repo tree plus `dist/` — easier to recognize as "release branch of cairn" than A's "release branch is JUST a curated payload."

**Attack 4 — `peter-evans/create-pull-request@v6` permission gap.** Phase 2C's workflow declares `permissions: contents: write` but the auto-PR step needs `pull-requests: write`. This is a one-line bug: workflow needs both permissions. Phase 4 ADR/F-spec must include this.

**Verdict.** Real bug, low-severity, easily fixed. Doesn't undermine D structurally.

**Attack 5 — Two-step coupling residual under D.** D mechanizes S4 via auto-PR, but the auto-PR's merge step is human. If maintainer ignores the auto-PR for >1 commit on `dev`, divergence accumulates. Phase 2C names a "release-checklist gate" that asserts `marketplace.json:source.ref` matches most-recent tag. **The gate is described but not specified — no concrete CI shape given.** Phase 4 must spec this gate or accept that S4 residual is "maintainer must merge the auto-PR within N days."

**Verdict.** Specification gap, not structural flaw. Either spec the gate in Phase 4 or accept the residual.

**Attack 6 — Tag mutation via `git tag -f` after release.** D's CI tags during the release run. Choice 3a (manual workflow_dispatch after manual tag-push) means the tag is pre-pushed by the maintainer. The CI's "Tag the release commit (idempotent)" step asserts the tag points at HEAD; if the maintainer pushed the tag at a `dev`-tip commit and CI ran on a different `release`-branch commit, the assertion fails. Workflow stops cleanly. **But:** if the maintainer subsequently does `git tag -d v0.1.0 && git tag -a v0.1.0 <release-sha> && git push origin v0.1.0 --force`, they can re-point the tag. This is a maintainer-choice tag-mutation, not CI-driven.

**Verdict.** Honest acknowledgment: D's tag-immutability rests on cairn maintainer discipline, not on CI enforcement. Mitigation: protect tag refs via GitHub's tag protection rules (orthogonal to CI). Mention in Phase 4 ADR.

**Attack 7 — plugin.json:version vs tag-name divergence.** D requires plugin.json's `version` field equals the tag's `v`-stripped form. CI enforces via `bump_plugin_version.py` (which writes plugin-template.json from the workflow input). But the workflow's "Tag the release commit (idempotent)" step asserts the tag points at HEAD; doesn't directly assert plugin.json:version matches. **Add a CI step**: read `dist/.claude-plugin/plugin.json:version` post-build, assert equals workflow `inputs.version`. One-line fix.

**Verdict.** Spec gap, easily fixed in Phase 4.

**Attack 8 — Today's marketplace.json schema bug (S1) is independent of approach.** Verified by both Phase 0 and Phase 0.5 agents independently. The bug exists today regardless of which approach lands. **Concern**: if Phase 4 ships D's manifest rewrite without verifying empirically (i.e., F3 audit check 9 doesn't run against the rewritten manifest before merge), we may ship another invalid manifest. Mitigation: the Phase 4 deliverable feature MUST run check 9 as part of its acceptance, before merge to `dev`.

**Verdict.** Real risk; mitigation is feature-acceptance criterion, not approach-side.

**Attack 9 — Approach D's claim that `release` branch keeps tagged commit reachable.** D dissolves S6 (detached commits) by maintaining a `release` branch where each release commit is HEAD at tag time. But: cairn's branch-protection policies are not yet in place on `release`. A future force-push to `release` (or branch deletion) could orphan tagged commits. **Mitigation**: protect `release` branch in GitHub settings (no force-push, no delete) once it exists. This is operator action, not CI mechanism.

**Verdict.** Operator-action mitigation; not a structural flaw.

## Steel-man Approach A

Take the second-best approach (A) and argue its case as strongly as possible. What does A handle that D doesn't?

**A's strongest case, point by point:**

1. **One push per release. Period.** A's release ceremony is `git checkout dev; bump plugin-template.json; git push; click workflow_dispatch button.` That's it. No tag-creation, no auto-PR, no auto-PR-merge step. **The S4 two-step coupling is structurally absent in A** — the release branch's force-with-lease push carries both `dist/` payload AND the new plugin.json:version in one commit. D mechanizes S4; A doesn't have S4 at all.

2. **No `peter-evans/create-pull-request` third-party dependency.** A's CI uses only first-party `actions/checkout` + `astral-sh/setup-uv` + bash. D's auto-PR step pulls in a community-maintained action. Smaller supply-chain surface.

3. **Force-with-lease is honest about deploy semantics.** A's `release` branch is a CI-managed deploy target. Force-with-lease + the M5-amendment ADR's documentation makes this explicit: "release is CI-only, do not push manually, force-with-lease will overwrite on next release." Future maintainers reading the workflow understand the deploy semantics. D's `release` looks like a normal branch (merge commits), making it ambiguous whether manual pushes are OK.

4. **Shape-(i) is leaner for archaeology.** A's `release` HEAD tree IS the plugin payload — `git ls-tree release` shows exactly what the consumer gets. D's `release` carries the full `dev` tree at source-SHA plus `dist/` — `git ls-tree release` shows extraneous files.

5. **Branch HEAD pin under cairn-D2 is honest if documented.** D2 says "consumers pin via SHAs/tags." A's `ref: "release"` is a branch pin (not a SHA, not a tag) — but combined with plugin.json:version-as-cache-key (Phase-0.5 Evidence 8), updates only ship on version bump. D2's INTENT (no surprise updates) is preserved by the plugin.json:version mechanism. The `ref: "release"` is a pointer-handle, not a stability handle.

6. **A's archaeology via optional tagging.** A's workflow optionally tags every release commit on `release` as `v0.x.y`. D2-strict consumers can override `ref` → `sha` (or hand-edit to `ref: "v0.x.y"`) for SHA-pin stability. **A's optional tagging gives the same affordance as D's mandatory tagging, without making the manifest depend on it.**

7. **A is closer to the M5 ADR D3's literal posture.** D3 says `marketplace.json` `source.path: "dist/"` (which is now schema-invalid). The closest documented schema shape is `git-subdir` with `path: "dist"` (D's choice) OR `github` (A's choice with shape-(i) inverting `dist/` from "subdirectory" to "branch root"). A's interpretation requires the inversion claim to be explicit in the M5-amendment ADR; D's interpretation is closer to D3's literal text.

   **Counter-counter:** the S1 schema bug means D3's literal `path: "dist/"` was never going to work. A redefines D3's intent ("the dist allow-list shapes the consumer-visible payload") to a different schema shape. D preserves D3's `path: "dist"` text.

   **Verdict on this point:** D is more textually faithful to D3; A is structurally cleaner.

**A's weak spots vs D:**

- A's S2 defense (use `github` source with explicit `ref: "release"`) is conceptually identical to D's S2 defense (use `git-subdir` source with explicit `ref: "v0.x.y"`) — both decouple plugin-source resolution from marketplace clone ref. The difference is in the pin handle (branch vs tag).
- A's pin handle (`ref: "release"`) reads cosmetically like a moving target; D's (`ref: "v0.x.y"`) reads as a pin. Both are equally stable in practice (updates only ship on version bump).
- A's force-with-lease history rewriting requires optional tagging for archaeology; D's normal-merge history doesn't.

## Assumption audit on Approach D

| Assumption | Verified or believed? | Evidence | If wrong, severity |
|---|---|---|---|
| `source.source: "git-subdir"` is documented | **Verified** | Phase-0.5 Evidence 1, 2 (`plugin-marketplaces:329-366`) | n/a |
| `git-subdir` clones independently of marketplace clone | **Believed (mechanism-supported)** | Phase-0.5 Evidence 2 ("uses a sparse, partial clone") implies independent fetch with own URL+ref+path | High — collapses S2 defense to A's level |
| `git-subdir` resolves `ref: "v0.x.y"` (tag) cleanly | **Verified** | Phase-0.5 Evidence 3 (`ref` accepts "branch or tag") | n/a |
| Sparse-clone fetches only `path/` not full tree | **Believed (claimed by docs)** | Phase-0.5 Evidence 2 ("minimizing bandwidth") | Low — bandwidth concern only |
| plugin.json:version wins silently over marketplace entry | **Verified** | Phase-0.5 Evidence 9 (`plugin-marketplaces:715-718`) | n/a |
| `chore:` is INV-001-compliant | **Verified directly** | `scripts/validate_architecture.py:279,348` | n/a |
| `peter-evans/create-pull-request@v6` works as documented | **Believed** | Third-party action; not audited | Low — workflow-spec failure caught in CI |
| Tags don't move accidentally; cairn maintainer discipline holds | **Believed** | Cairn convention; not enforced | Medium — orphans tagged commit if `release` deleted |
| F3 audit check 9 will surface manifest bugs before they reach consumers | **Believed (process)** | Operator commitment + dispatch-skill discipline | High — if check 9 is skipped, S1 reaches consumers |

**Pattern:** D's verified assumptions are mechanism-side (schema documented, version-resolution chain). D's believed assumptions are process-side (maintainer discipline, third-party action stability, audit-check execution). This is the same pattern A bears — A's "force-with-lease honors cairn's policy" is also a maintainer-discipline assumption.

**Conclusion of audit.** No load-bearing assumption fails catastrophically. The single highest-leverage assumption is the git-subdir-decoupling claim (Attack 1) — if wrong, D collapses to A's posture. The right mitigation is: F3 audit check 9 against the chosen approach's manifest BEFORE merging to `dev`. This applies to A and D both.

## Two real bugs found in Phase 2C's workflow

Neither is structural; both must land in Phase 4's ADR / feature spec:

1. **`peter-evans/create-pull-request` permission gap.** Add `pull-requests: write` to the workflow's `permissions` block.
2. **Plugin.json:version vs workflow inputs.version assertion gap.** Add a CI step post-build asserting `dist/.claude-plugin/plugin.json:version` equals workflow `inputs.version`.

A's workflow (Phase 2A) has analogous risks but Phase 2A's plan does include the version cross-check ("Verify version was bumped" step at line 119–127). A is one bug ahead of D on workflow-spec completeness.

## Comparison synthesis

| Axis | A (release-branch + sync CI) | D (git-subdir + tag + release-branch anchor) |
|---|---|---|
| S1 schema-rewrite | yes (`source.source: "github"`) | yes (`source.source: "git-subdir"`) |
| S2 default-branch trap | defended (explicit `ref: "release"`) | defended (explicit `ref: "v0.x.y"` + git-subdir decoupling) |
| S4 two-step coupling | structurally absent | mechanically defended (auto-PR + checklist gate) |
| S5 commit-prefix | `chore:` ✓ verified | `chore:` ✓ verified |
| S6 detached commits | n/a (release branch) | dissolved (release branch anchor) |
| S7 ref-omission footgun | defended (mandatory `ref: "release"` lint) | defended (mandatory `ref: "v0.x.y"` lint + 3-layer) |
| S8 schema breaking change | accepted residual | accepted residual |
| S9 dogfood | defended (default branch unchanged) | defended (default branch unchanged) |
| Maintainer release ceremony | one push + workflow click | tag push + workflow_dispatch + auto-PR merge (3 steps) |
| CI complexity | medium | medium-high |
| Third-party CI deps | first-party only | + `peter-evans/create-pull-request@v6` |
| `release` branch shape | shape-(i) (release IS plugin root; force-with-lease) | shape-(ii)-merge (release carries dev + dist/; merge commits) |
| `release` branch archaeology | requires optional tagging | normal merge history |
| D2 textual fit (D2 says "tags follow `v0.x.y`") | indirect (branch HEAD pin + plugin.json version) | direct (tag pin literal) |
| Workflow-spec bugs found in Phase 3 | 0 | 2 (permission gap, version-assertion gap) |
| Manifest fidelity to today's `path: "dist/"` | inverted (no path field) | preserved (`path: "dist"`) |

**A wins on:** simpler ceremony, no third-party deps, no S4 (structural absence), workflow-spec maturity in Phase 2.

**D wins on:** D2 textual fit, normal merge history, manifest fidelity to D3.

**Roughly tied on:** S1, S2, S5, S7, S8, S9, ceiling on consumer prereqs (both stay at jq+ruff+git).

## Recommendation

**The choice between A and D is genuinely close.** Either is shippable. The decision is aesthetic-and-process, not mechanism:

- **Choose A if:** simpler maintainer flow + first-party-only CI + workflow-spec maturity + structurally-absent S4 outweigh D's more direct D2 fit.
- **Choose D if:** D2 textual fit (`v0.x.y` tag pin) + normal merge history + manifest fidelity to D3's `path: "dist"` outweigh A's simpler ceremony.

**Lead's lean:** marginally toward **Approach A**. Reasoning:
1. **S4 structurally absent** is stronger than S4 mechanized. Mechanized defenses can be undone by maintainer discipline lapses (auto-PR sits unmerged); structurally-absent S4 has nowhere to lapse.
2. **First-party CI deps** matter for cairn's identity (pre-v1, small consumer base). Adding `peter-evans/create-pull-request@v6` extends the supply-chain trust boundary.
3. **D's two real Phase-3-found bugs** (permission gap, version-assertion gap) are easily fixed but signal that D's CI shape is less battle-tested than A's at this point in the design.

But this is marginal. **Operator should choose.** The lean above is documented; not load-bearing. If the operator prefers D for the D2 textual fit, the choice is honestly made.

## What Phase 4 needs regardless of A or D

1. **Schema rewrite** (S1) — mandatory, structural prerequisite.
2. **`tests/unit/test_marketplace_schema.py`** — schema-shape lint asserting `source.source` is one of the documented values, ref is non-empty (matching the chosen approach's expected pattern).
3. **Risk Register entry for S8** — accepted residual.
4. **M5-ADR amendment** (Phase-0 conflict C5) — co-landed amendment ADR with `amends-section: D3` (and possibly `D2-extended-by` if Approach B's npm path were chosen, which it isn't here).
5. **F3 audit check 9 acceptance criterion** — the chosen feature includes a manual end-to-end install verification before merge.
6. **plugin.json:version is the consumer-visible update signal**, NOT marketplace.json's source.version (per Phase-0.5 Evidence 9). Both A and D inherit this.

## Phase 5 trigger

The eventual ADR will likely be `firmness: firm` (deployment pattern is a long-lived structural commitment, not provisional). **Phase 5 (independent verification) applies.** Per the protocol, after Phase 4 commits the ADR draft, a fresh subagent runs Phases 1-3 again on the constraint envelope only (no lead reasoning). If the fresh agent reaches the same approach, high confidence; if different, surface the trade-off.

## Decision-question for operator

The lead recommends Approach A with the marginal lean above. Approach D is competitive and would be honestly chosen.

**Operator: A or D?** Or any other override (e.g., Approach B if the npm path is genuinely preferred for portability reasons; or escalate the decision and amend the brief).

Phase 4 (ADR drafting) waits on this answer.
