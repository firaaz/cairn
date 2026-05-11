# Phase 1 Pre-Mortem — plugin-payload-transport

Five failure scenarios for "we picked a transport and burned operator time." Each is a distinct failure axis, not a re-skin of "approach X fails."

---

## S1. Empirical resolver behavior — V-3 attempt 3 falsifies the sha/url hypothesis

**Trigger condition.** We adopt A1 (research-anthropic-marketplace.md:58: `source: "url"` + `sha:` + drop `ref:`) on the hypothesis that "82/82 Anthropic plugins use sha-pinning so the resolver must HTTP-fetch by SHA." V-3 attempt 3 install still fails with `git@github.com: Permission denied (publickey)`, or fails with a new mode (e.g. `sha not reachable from default branch`, `unable to resolve commit`, or silent fallback to ref-resolution clone).

**What gets wasted.** Hypothesis is "strongly suggested but not empirically verified" (research:44). Burn: ADR amendment #2 to m5-plugin-deployment-pattern D2/D7, INV-012 redefinition (sha replaces ref), `tests/unit/test_marketplace_schema.py` rewrite, release-publish.yml change to capture+inject post-push SHA, one more operator install-test cycle. ~3-4 operator hours minimum, plus a third falsified ADR amendment in the chain (`marketplace-source-url-amend` already falsified; this would be the second).

**Detection lag.** Fast (~5 min) — install either succeeds or returns Permission denied at `/plugin install` time. But: a *silent partial success* (clone succeeds, but resolver picks wrong tree state) could lurk until F3 check 9 manual end-to-end.

**Recoverability.** Revertible at the manifest level (sha field is additive); release-publish.yml change is revertible. The ADR churn is not free but is contained. We are not married to infrastructure.

**Mitigations.** (a) Run a throwaway empirical probe BEFORE writing the impl slice — hand-edit marketplace.json on a scratch branch, install in fresh consumer, observe. (b) Phase 2 must enumerate the *next* fallback (A2 git-subdir, A3/A4 self-marketplace, A6 tarball) so attempt 3's falsification doesn't strand us. (c) Define "success" criteria precisely: HTTPS-only clone path in the resolver's debug log, not just absence of error.

---

## S2. Consumer-environment heterogeneity — works on operator's mac, breaks for a consumer class

**Trigger condition.** Transport works on the operator's macOS + uv + jq + ruff floor (phase-0-constraints:32) but breaks for: (a) Windows consumer (issue #50725: Windows `url`-type also forces SSH), (b) corporate-proxy consumer where `*.github.com` is whitelisted but `*.amazonaws.com` / `*.r2.cloudflarestorage.com` is not (kills A2-self-host approaches), (c) consumer behind firewall blocking arbitrary HTTPS hosts, (d) consumer without `git` on PATH (kills any approach that triggers git-clone), (e) `git-subdir` source-type behaves differently on Windows than darwin.

**What gets wasted.** Full impl slice landed, F3 check 9 green on operator box, then first external consumer reports failure. Now: a CONSUMER.md prereq expansion (violates phase-0-constraints:32 "No expansion of consumer prereq floor"), or a second transport for the broken class, or scope-narrowing of who cairn supports. Possibly an ADR amendment declaring platform support matrix. 4-8 operator hours plus loss of "zero-friction install" premise from `delivery-mechanism-friction` (phase-0-constraints:25).

**Detection lag.** Long — could be weeks until a non-operator consumer tries to install. Without an external-consumer canary, this is invisible.

**Recoverability.** Partially. The transport mechanism is revertible but the *premise* (zero-friction) erodes with each escape hatch. Once we document "SSH key required on Windows," we've conceded the friction-zero ADR.

**Mitigations.** (a) Phase 2 must list, per approach, the *consumer prerequisite delta* vs. current floor `{jq, ruff, python3}`. (b) Prefer approaches whose transport is `git-clone-over-HTTPS to github.com` (the lowest-common-denominator network path) over self-hosted alternatives. (c) Defer "Windows support" explicitly if no candidate covers it — don't pretend.

---

## S3. Release-publish / dist-gate integration breakage

**Trigger condition.** Chosen transport requires release-publish.yml changes that violate one of: INV-001 conventional-commit prefix (constraints:7), INV-012 ref-immutability (constraints:9), `--force-with-lease`-only invariant (constraints:36, release-publish.yml:110), `tests/unit/test_marketplace_schema.py` assertions (constraints:21 — `source ∈ {github,url,git-subdir,npm}`, `ref == "release"`, no `version`), or dist-gate.yml PR-time gating semantics. Observable signal: CI red on next release-publish run, or schema lint failure on the marketplace.json edit PR.

Concrete cases: A1 (sha-pinning) needs release-publish to capture HEAD SHA post-push and rewrite marketplace.json on `dev` — that's a two-step coupling (rejected in m5-plugin-deployment-pattern Phase 3 stress test, constraints:45). A3 self-marketplace via release branch root inverts the dist/ curation model (constraints:38). A6 GitHub Releases tarball requires `gh release create` step + asset upload + URL-with-tag in marketplace.json (drift between marketplace.json and release-branch HEAD).

**What gets wasted.** Workflow rewrite + INV redefinition + test rewrite + ADR amendment to D5/D7/D8 of m5-plugin-deployment-pattern. The test_marketplace_schema rewrite is load-bearing — these are the 5 currently-green assertions that prove the manifest hasn't drifted. ~6-10 hours and a second-order increase in maintenance surface.

**Detection lag.** Short for CI breakage (next release run); medium for invariant drift (next schema-lint PR); long for two-step-coupling regret (felt months later as release ceremony complexity).

**Recoverability.** Workflow code is revertible; ADR amendments compound. The big risk is *invariant erosion* — once INV-012 stops binding `ref: "release"`, the deterministic-release property is harder to restore.

**Mitigations.** (a) Phase 2 must explicitly state, per approach, which INV/ADR clauses it amends and which stay intact. (b) Prefer approaches that preserve the test_marketplace_schema assertion set as-is (additive fields only, not redefinition). (c) Reject approaches requiring two-step CI coupling (cross-ref the rejection rationale from m5-plugin-deployment-pattern Phase 3).

---

## S4. Update / drift — installs work, updates don't

**Trigger condition.** Stage 3 install succeeds at v0.1.0; release-publish ships v0.1.1; consumer runs `/plugin update cairn@cairn-marketplace` and gets stale payload, or no update mechanism, or a manual `remove + re-add` requirement. Observable signal: phase-0.5-journey:88-96 Stage 6 is `UNKNOWN` (journey:109); we have not verified update semantics under *any* transport.

Concrete failure cases: (a) A1 sha-pinned manifest — consumer is locked to the sha that was current at their last marketplace-add; until *marketplace.json itself* changes on dev and they re-run marketplace-add, they never see v0.1.1. This is the worst case: install works, update silently never happens. (b) A3 self-marketplace on release branch — marketplace.json and payload are co-versioned, but consumer's marketplace cache at `~/.claude/plugins/marketplaces/cairn-marketplace/` doesn't auto-refresh from origin. (c) A6 tarball with version-pinned URL — same lock-in issue.

**What gets wasted.** The worst kind: invisible to operator dogfood (operator re-adds marketplace constantly), visible to long-tail consumers months in. Each blocked consumer = manual support, a CONSUMER.md "to update, run X first" note, and erosion of plugin-system promises. The fix is a second slice (update-mechanism slice) that wasn't in the v1 budget.

**Detection lag.** Very long — only triggers on the second release. By the time we ship v0.1.1, the wrong-shape decision is months old.

**Recoverability.** Depends. If we're sha-pinned and the resolver caches by sha forever, we're stuck with a "manual re-add per release" UX — embarrassing but revertible by switching back to ref-based pinning IF the resolver bug is fixed by then. Self-marketplace structure is harder to undo.

**Mitigations.** (a) Phase 2 must explicitly answer "how does v0.1.1 reach an already-installed consumer?" per approach, not handwave. (b) Empirical probe at impl time: install v0.1.0, ship v0.1.1, run update, observe. Don't ship without this. (c) Prefer approaches where marketplace.json itself is *ref-pointed* even if payload is sha-pinned, so a release-publish that updates marketplace.json on dev propagates naturally.

---

## S5. Maintainer cost / second-order infrastructure debt

**Trigger condition.** Approach pulls in a new always-on infra dep that cairn now owns: S3/R2 bucket (A2 self-hosted), separate `cairn-marketplace` repo (A4), GitLab/Codeberg mirror (A5), or a GitHub Releases workflow with auth tokens + asset uploads (A6). Observable signal: Phase 2 design lists a new credential, a new external service contract, or a new repo to maintain.

**What gets wasted.** Compounds forever. Standing dep floor expands beyond `{pydantic, typer, pyyaml}` (CLAUDE.md). New failure modes: bucket bill, token rotation, mirror sync drift, second-repo ADR-sync overhead. Burns remaining v1 milestone budget on infra-plumbing rather than methodology. Also: violates the "first-party CI only" preference (constraints:45) if we onboard non-Anthropic services into the release path.

**Detection lag.** Short on cost-awareness (immediately obvious in Phase 2), but long on the *true* cost — drag accumulates over months as operator context-switches into infra-ops instead of cairn-methodology work.

**Recoverability.** Asymmetric. Easy to add infra; hard to remove without breaking installed consumers. Self-hosted artifact at `https://cairn.example.com/v0.1.0.tar.gz` becomes a URL contract that consumers' marketplace caches depend on; killing the host bricks installs.

**Mitigations.** (a) Phase 2 must compute a "new-infra delta" line per approach: zero new services, zero new credentials is the preferred shape. (b) Hard-reject any approach that adds a credentialed external dep without an explicit /decision on infrastructure ownership (per MEMORY: setup-task framing hides decision weight). (c) If self-hosted is the only working path, prefer GitHub Releases (free, already-trusted, no new credential) over arbitrary CDN.

---

## S6 (optional). Anthropic ships resolver fix — we're stuck with a workaround shape

**Trigger condition.** Anthropic merges a fix for #26588 / #47088 / #50725 within weeks of cairn picking a workaround. Observable signal: a Claude Code release with "plugin resolver: honor HTTPS scheme on `url` source-type" in changelog. Our chosen non-standard shape (e.g. self-marketplace, tarball-URL, sha-pinning) is now strictly worse than the simple `source: "url"` + `ref:` shape we had before V-3 falsifications — but we've already amended ADRs, rewritten release-publish.yml, and shipped to consumers.

**What gets wasted.** ADR un-amend (or supersession), workflow revert, manifest re-rewrite, consumer migration message. The further from `{source: url, ref}` we drift, the more work to come back.

**Detection lag.** Medium — depends on whether we watch upstream changelogs. Could be weeks-to-months.

**Recoverability.** Inversely proportional to how exotic our workaround is. A1 (sha-pinning) reverts trivially. A3/A4 (self-marketplace restructure) is a multi-day migration. A2 (self-hosted) leaves us with infra to decommission.

**Mitigations.** (a) Prefer approaches whose "exit ramp back to simple `source: url + ref`" is one-PR-cheap. (b) Phase 2 must score each approach on supersession-friendliness, not just present-day cost. (c) Subscribe to / poll the upstream issues; if a fix lands in a release-candidate, pause our migration.

---

## Phase 2 must address — non-negotiable design requirements

For EVERY candidate approach, Phase 2 must produce:

- [ ] **Empirical probe plan** — what scratch-branch test confirms the resolver behaves as hypothesized BEFORE we write the impl slice (S1).
- [ ] **Consumer prerequisite delta** — explicit list of consumer-side requirements vs. current floor `{jq, ruff, python3}`. Any expansion is a hard NO without /decision (S2, constraints:32).
- [ ] **Platform support claim** — does this work on macOS / Linux / Windows / corporate-proxy / no-git-on-PATH? Mark explicitly; don't pretend (S2).
- [ ] **INV/ADR amendment list** — which clauses of m5-plugin-deployment-pattern, marketplace-source-url-amend, INV-001, INV-012 this amends; which stay intact (S3).
- [ ] **test_marketplace_schema.py impact** — does this preserve the 5 green assertions as-is, redefine them, or rewrite (S3, constraints:21).
- [ ] **release-publish.yml diff sketch** — concrete workflow change; must preserve `--force-with-lease` invariant and first-party-CI-only preference (S3, constraints:36 + :45).
- [ ] **Update path** — exact answer to "how does v0.1.1 reach an installed v0.1.0 consumer?" Not "presumably the resolver handles it." Empirical probe required (S4).
- [ ] **New-infra delta** — zero new services, zero new credentials, zero new repos is the target. Any deviation requires explicit cost line (S5).
- [ ] **Exit-ramp cost** — if Anthropic fixes the resolver next month, how many hours/PRs to revert to canonical `source: url + ref:` shape (S6).
- [ ] **F3 audit check 9 plan** — concrete manual install steps in a fresh consumer project; must include both install and update cycles (S2 + S4, constraints:23).

Approaches that cannot answer all ten must be rejected before they reach synthesis.
