# Phase 3 — Adversarial pass on `plugin-payload-transport`

Verdict (anchored up-front so you can stop reading early if you only need the call): **RESHAPE.** A1 should not be the load-bearing pick. A3a should. See §6.

## 1. Falsifying the A1 causal claim without running V-3 attempt 3

The convergence note (`phase-2-convergence-note.md:7,22`) leans on "82/82 of `url`-source plugins use `sha:`; 0 use `ref:`" as the strongest empirical prior. I attacked it three ways.

**1a. Re-inspection of the marketplace JSON.** The 82/82 number replicates exactly (jq filter on `~/.claude/plugins/marketplaces/claude-plugins-official/.claude-plugin/marketplace.json`). But the population is structurally narrower than the convergence note suggests: 82/82 of `url`-source plugins are also **on `github.com`** (100% — no GitLab, no self-hosted git, no `.tar.gz`), and 82/82 use 40-char SHAs (no short shas, no semver tags-as-sha). One plugin (`atomic-agents`) carries `path` alongside `sha:`, which is a `git-subdir` shape misclassified as `url`. That single edge case matters: it shows the resolver tolerates extra keys, and it suggests there isn't a strict `url`-vs-`git-subdir` branching gate — just a loose union.

By contrast, `git-subdir` (n=36) carries `ref:` AND `sha:` 35/36 times, with refs like `main`, `master`, `v1.0.1`. So **`ref:` is not a banned field in marketplaces** — it just isn't paired with `url:` alone. The convergence note frames "82/82 use sha" as if sha-pinning is the resolver's preferred branch; the equally valid reading is "Anthropic's CI emits sha-pinning for url-source as a stylistic convention because the schema generator captures the resolved sha at marketplace-build time." That's non-causal.

**1b. Counter-example hunt.** No `url`+`ref` plugin found in Anthropic's marketplace. No tarball URLs either. That's pattern, not mechanism. I cannot find a publicly-visible third-party marketplace using `url`+`ref` to falsify cleanly, but **cairn's own V-3 attempt 2 IS the counter-example we already have**: marketplace.json carried `source: "url"` + `https://...` + `ref: "release"` and the install force-routed to SSH (`framing.md:10-12`). The cached marketplace.json was confirmed to carry the `url` shape; the resolver host-coerced anyway.

**1c. Upstream-issue forensics (gh issue view).** Issue #50725 (0xbrainkid): *"If the marketplace entry declares `source: "url"` with an HTTPS Git URL, then switching to SSH during `/plugin install` is a source-of-truth violation. ... the installer silently upgrades itself to SSH."* This is the load-bearing finding. The bug operates at the URL/host-detection layer, not the pin-field layer. The bug-reporter explicitly named `source: "url"` as the failing shape and named host-based coercion as the mechanism.

Issue #26588 (heathdutton) goes further: he claims to have reverse-engineered `cli.js` and the patch he proposes is for `case 'github':` — meaning the bug exists in the `github` source-handler. **If `source: "url"` on a github.com host is internally rerouted into `case 'github'` (the simplest explanation for why V-3 attempt 2 failed identically to V-3 attempt 1), then `sha:` vs `ref:` is irrelevant to which branch fires** — both pin styles end up in the same SSH-fallback code path. ChrisTowles claims v2.1.72 "works with HTTPS-only," but operator runs 2.1.138 today and V-3 attempt 2 (2026-05-11) still fails — so whatever ChrisTowles tested either reverted or never covered cairn's manifest shape.

**Non-causal explanation that fits all observations:**

- Anthropic's marketplace-build tool computes the resolved sha at publish time and emits `url`+`sha`. Stylistic, not behavioral.
- The resolver, once it sees host=`github.com`, routes through a github-clone path that ignores both the declared `source` type AND the pin field, and tries HTTPS-then-SSH-fallback per heathdutton's reverse-engineering.
- A1 changes the pin field but not the host. If the host is the trigger, A1 still fails.

**A1's causal claim survives only if** the resolver has a fast-path that says "if url-source with `sha:` set, fetch-by-commit via libgit2/HTTPS directly, never touch the github-clone branch." That's a specific code shape with zero evidence in the upstream issues. Even research-anthropic-marketplace.md:44 admits the claim is "strongly suggested but not empirically verified."

## 2. Assumption audit

| Claim | Status | Cheapest convert/falsify |
|---|---|---|
| Marketplace-add HTTPS clone works | VERIFIED (framing.md:11, V-3 attempt 2 cache forensics) | — |
| Plugin-install with `url`+`ref` against github.com forces SSH | VERIFIED (V-3 attempts 1 + 2, framing.md:9-10) | — |
| Plugin-install with `url`+`sha` against github.com does NOT force SSH | **BELIEVED.** Inferred from population pattern only. | A1's own probe (`phase-2-approach-A1.md:70-79`). 5-min cost. Upstream #50725 evidence makes the prior weaker than convergence-note rank suggests. |
| Plugin-install with `"source": "./dist"` resolves filesystem-relative to marketplace cache | **BELIEVED**, but with a stronger structural argument: 49 Anthropic plugins use string-relative-path (jq verified) and there is no URL/host for the resolver to route on, so the only sensible interpretation is filesystem-relative. | A3a probe (`phase-2-approach-A3.md:87-111`). 30-min cost. |
| Plugin-install with `url` ending in `.tar.gz` takes HTTP-fetch path | **BELIEVED, weak.** Zero Anthropic plugins use this; no upstream signal it's supported. | A6 probe (`phase-2-approach-A6.md:62`). 30-min cost. Reject-on-falsify. |
| Update cycle refreshes marketplace.json from `dev` for sha-bumped manifest | **BELIEVED.** No empirical observation in any V-3 attempt. The 82/82 prior is install-only; we have no Anthropic-marketplace update-cycle evidence either. | Two-cycle probe: install v0.1.0-probe, bump sha on `dev`, run `/plugin update`, observe payload version. ~10 min on top of install probe. |
| Anthropic's 49 self-marketplace plugins use marketplace-cache refresh for updates | **BELIEVED.** Strong structural inference (no URL→nothing else to fetch), but no direct evidence. Anthropic could be doing nightly cron `marketplace remove + re-add`. | Same two-cycle probe under A3a. |

Note that two of A1's three load-bearing claims (sha-bypass and update-via-marketplace-refresh) are both BELIEVED. A3a has two BELIEVED claims but one (relative-path-resolution) is structurally far stronger.

## 3. Steel-man A3a as the winner

A3a is structurally stronger than A1 for four reasons.

**3a. Hypothesis shape.** A1's hypothesis is "the resolver has a sha-vs-ref behavioral branch inside the `url` handler that gates host-coercion." A3a's hypothesis is "when source is a relative-path string, there is no URL to coerce." A3a's hypothesis is **independent of any resolver branch** — it relies only on the absence of a URL, not on the presence of a specific code path. A1 bets the resolver has a particular if-statement; A3a bets the resolver knows how to read a filesystem path.

**3b. The two-step CI coupling rejection was structural, not Action-specific.** I re-read the rejection rationale: `phase-0-constraints.md:45` quotes m5's Phase 3 verdict as "simpler ceremony + structurally-absent S4 (two-step coupling) + first-party CI." S4 ("two-step coupling") is listed as a separate axis from "first-party CI." Approach A was selected because two-step was *structurally absent*, not because it used first-party Actions. Same file at the m5 ADR excerpt around line 138: *"No two-step release coupling."* listed as a standalone strength. A1 reintroduces exactly this rejected shape — push `release`, then capture HEAD-sha, then rewrite `marketplace.json` on `dev`, then push `dev`. A1's `phase-2-approach-A1.md:83` acknowledges this. A3a, in its preferred form (`phase-2-approach-A3.md:39` — "require `dist/` committed-current at workflow start"), has zero new CI pushes.

**3c. Blast radius if probe falsifies after impl.** A1's exit ramp (manifest revert + workflow-step revert) looks cheap on paper, but it is exit-ramp #2 in a chain: marketplace-source-url-amend was already amended and falsified once. Each amendment costs "operator plan-credibility" per Phase 2 A1 §5 R-A1-c (`phase-2-approach-A1.md:85`). A3a's exit ramp is more work in commits (~1-2h vs ~30 min) but it doesn't compound the falsification chain — A3a is a fundamentally different shape, not "amendment #2 of the url-source bet."

**3d. Update story.** A3a's update story has 49 Anthropic plugins as inferential evidence (`phase-2-approach-A3.md:79`). A1's update story has zero — every Anthropic url-plugin updates via marketplace.json sha-bumps, but we don't know if their marketplace cache actually re-fetches marketplace.json without a manual `remove+add`. Worst-case-A1 = consumer locked to install-time sha. Worst-case-A3a = consumer locked to install-time dist tree, *but at least the marketplace.json is structurally identical post-update* (still `"source": "./dist"`) so the failure mode is "stale dist", not "stale sha pin", which is easier to detect (postinstall_validate.py version check).

**Did the convergence note rank A1 first on probe-cost alone?** Yes — `phase-2-convergence-note.md:22` cites "highest empirical prior + lowest cost" and ranks 1st. But the empirical prior is for the *population pattern*, not the *causal mechanism*; and the cost is for the probe, not the wrong-pick fallout. Probe-cost ordering is a sensible execution heuristic (run cheap probe first), but it's not the same as **load-bearing-decision** ordering. Convergence-note conflates them.

## 4. Steel-man A7 (document SSH prereq)

A7 deserves serious weight:

- **Cost** is trivial: one CONSUMER.md note ("If you don't have a github SSH key configured, run `git config --global url.https://github.com/.insteadOf git@github.com:` before `/plugin install cairn@cairn-marketplace`") plus amending `delivery-mechanism-friction` to mark "zero-friction install" as conditional pending upstream fix.
- **Cost of a wrong A1/A3a/A6** is amendment #2 (or #3) to the ADR chain, falsification cycle #3, more operator hours, and more credibility erosion.
- **Upstream pressure is real**: three open issues (#26588, #47088, #50725) plus referenced #18001, #9719. heathdutton reverse-engineered the patch — once an Anthropic eng picks it up, fix-rollout is likely days, not months. ChrisTowles's v2.1.72 datapoint suggests Anthropic *has* tweaked behavior recently, even if it didn't cover cairn's shape.
- **Exit ramp is free**: when Anthropic ships the fix, A7's "delete the CONSUMER.md note" is a one-line revert. A1's exit is 1 PR + ADR un-amend. A3a's exit is 1-2h + ADR un-amend.

**Why A7 isn't the auto-winner**: it concedes the `delivery-mechanism-friction` "zero-friction" property, which was itself a load-bearing premise. A7 is *correct* if and only if the operator accepts that zero-friction was over-claimed in v1. That's a real concession — but it's also more honest than betting another ADR amendment on an unverified resolver branch.

The convergence note does name A7 (`phase-2-convergence-note.md:32`) but as a "fallback if all three probes falsify." That's backwards-prioritized. A7 should be the **floor** of the decision, with A3a as the upside bet — not a last-resort.

## 5. Independent re-derivation

My ranking, ignoring the convergence-note conclusion:

**1st — A3a, with A7 as the time-boxed escape hatch.** The hypothesis ("relative-path resolves filesystem-local because there's nothing to coerce") is the structurally strongest. 49/82 prior. Zero new CI steps. Update mechanism rides the same marketplace-cache refresh that Anthropic's 49 plugins use.

**For A3a to be wrong** for cairn's priorities, the following would have to hold: (a) the marketplace-cache walker recurses through `.slice-system` and infinite-loops at install time (R-A3a-4, `phase-2-approach-A3.md:121`), or (b) `dev`-branch instability bleeds to consumers materially (R-A3a-3). Both are mitigable: (a) by verifying once empirically (cheap), (b) by keeping `dist/` writes gated to release-publish workflow commits only.

**2nd — A7 as v1, A3a deferred.** If the operator's risk tolerance for an *unverified resolver hypothesis* is zero (and given V-3 has falsified twice already, this is a defensible posture), ship A7 in v1: amend `delivery-mechanism-friction` to "consumer must have github HTTPS-rewrite OR SSH key OR wait for upstream fix"; document; move on. Triggered re-decision when Anthropic ships the fix.

**For A7 to be wrong**: cairn's adoption curve depends *materially* on zero-friction install (i.e., a non-trivial population of consumers would bounce off "you need to configure git insteadOf"). I think that population is small for cairn's target audience (Claude Code power-users with `uv`/`jq`/`ruff` installed already have git configured), but the operator owns that call.

**3rd — A1.** Acceptable only if A3a is also rejected on grounds I haven't surfaced. If A1 must be the pick, harden it: (a) probe MUST include the update cycle, not just install; (b) probe MUST run on a machine where `~/.ssh/id_*` is moved aside, not just "no key configured" — V-3 attempt 2 showed `temp_github_<id>` triggers even with HTTPS declared, so we need to confirm `sha:` route does NOT enter `temp_github_<id>`; (c) probe MUST run with `CLAUDE_CODE_DEBUG=1` or equivalent and capture which resolver branch fires (filename in cache path is the discriminator).

**4th — A6.** Reject without probe. Zero empirical prior, worst update story, asset-URL forever-contract risk.

## 6. Phase-3 verdict

**RESHAPE.** A1 should not be the load-bearing pick.

Recommended new shape for Phase 4's ADR:

- **Load-bearing decision: A3a** (`source: "./dist"`, self-marketplace via `dev` carrying `dist/` committed-current).
- **Probe sequence inverted**: A3a probe first (~30 min). If A3a probe passes install + update, ship A3a. If it falsifies, fall to A7.
- **A7 as named v1 fallback** (not "last resort") — CONSUMER.md note + `delivery-mechanism-friction` amendment to soft-spec "zero-friction conditional on upstream fix #26588."
- **A1 demoted to "if A3a probe surfaces an unforeseen `dist/`-discipline blocker, retry with A1."** Not first.
- **A6 dropped from the ADR's named fallbacks.** Zero prior, asset-URL lock-in.

Rationale anchors: §1 (the sha-vs-ref claim is not causal under any model that fits the upstream evidence); §3b (two-step CI coupling was rejected structurally, not Action-specifically, and A1 reintroduces it); §3a (A3a's hypothesis is independent of any resolver branch existing); §4 (A7's exit ramp is strictly cheaper than A1's amendment-chain cost).

Firmness: still **provisional** until the A3a probe runs install + update cycles. But the load-bearing pick should reflect the strongest hypothesis, not the cheapest probe.

If the operator disagrees and wants A1 to remain load-bearing: the minimum acceptable hardening is the three probe-design tweaks in §5 third-place — debug-flag capture, ssh-keys-moved-aside, mandatory update-cycle. Without all three, A1 reaches Phase 4 as hypothesis-grade, which is the cliff Phase 3 is supposed to prevent.
