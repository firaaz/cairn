# Phase 2 — Approach B: Marketplace-Curated Plugin

Author: forced-enumeration teammate, plain subagent. Steel-manning the alternative the brainstorm did not pick. Brief: cairn ships as a publicly-listed Claude Code marketplace plugin with a **curated payload** (methodology core only — skill, agents, hooks, templates), **no slash-commands**, **no `docs/`**, **single audience-tagged `CLAUDE.md`**, after **closing the 6 amendment ADRs to v1**. Symlink retired.

---

## 1. Boundary coverage

The Phase 0.5 cross-role list (`phase-0.5-journey.md:64-78`) names twelve must-cover surfaces. Approach B's coverage:

- **Hook-script delivery + invocation path.** Marketplace install drops `checks/{reversibility-guard.sh, reality-check.sh, role_guard.py}` into `${CLAUDE_PLUGIN_ROOT}/checks/`. Manifest-declared hook entries reference `${CLAUDE_PLUGIN_ROOT}/checks/...` — version-stable across releases because Anthropic's marketplace contract pins `${CLAUDE_PLUGIN_ROOT}` semantics.
- **Agent-registry resolution.** Curated payload includes `.claude/agents/{phase-{1..4}-tdd, triager-tdd}.md` + `role-topology.yaml` — exactly the five `subagent_type` slugs Phase 0.5 §6 requires. Marketplace metadata declares them as plugin-provided agents; consumer's own `.claude/agents/` is not touched.
- **Skill discovery.** `.claude/skills/cairn-tdd-feature/SKILL.md` ships in payload; marketplace declares the skill name. Consumer's Skill tool resolves it without `.slice-system/` interposition.
- **Slash-command discovery.** **B intentionally drops `/catchup`, `/handoff`, `/decision`, `/new-adr`, `.full` variants.** These are operator-discipline aids, not methodology-core. Consumers either bring their own (the portfolio evaluator already has an `adr` skill — `2026-04-23-from-portfolio-evaluation.md:51`) or invoke the underlying primitives directly. The `.local/` leakage hazard (Scenario 5) is structurally impossible: `commands/` is not in the payload at all.
- **Python-runtime boundary.** `role_guard.py:90-92` lazy-imports pyyaml; B doubles down on this — the curated payload ships only `role_guard.py` (no pydantic/typer-dependent code), so the consumer-runtime contract collapses to "stdlib `python3` on PATH" plus `jq` and `ruff`. No `uv run` requirement on the consumer; uv is a maintainer tool.
- **System-dep contract.** Marketplace listing declares `jq` and `ruff` as prerequisites in the listing description; Anthropic's review (see §3) enforces an explicit prerequisites field. B can additionally ship a one-shot `cairn-postinstall` validator inside the payload that exits non-zero on missing deps — same defense as the brainstorm's #8 but discoverable from the marketplace page before install.
- **Consumer-owned `.claude/` state.** `handoff.md`, `active-envelope.yaml`, `skill-runs/<id>/`, `learning.md`, `adr-editorial-fixes.log` all stay consumer-side. Curated payload contains no top-level `.claude/` files that would clobber consumer state on install — only the namespaced `.claude/skills/cairn-tdd-feature/` and `.claude/agents/<five-named-files>` paths. Lower clobber risk than full-repo-minus-internals (Approach A) because the payload surface is auditable in one screen.
- **Plan-doc + envelope contract.** Comprehensive templates ship under `templates/` (Brainstorm decision #6, made non-negotiable in B because Finding 3 of `2026-04-23-from-portfolio-evaluation.md:81-85` flagged it as "what consumers most need"). `templates/{handoff.md, intent.md, plan.md, adr-frontmatter.md, active-envelope.yaml}` with worked examples (Scenario 4 defense).
- **Identifier-scheme contract.** `id:` vs `name:` documented in the audience-tagged `CLAUDE.md` `[both]` block. No file split needed.
- **Settings.json hook-string boundary.** Marketplace plugins declare hook registrations in the manifest; Claude Code merges them on install/upgrade. B's reduced surface (3 hooks, no slash-commands) means the merge is small and round-trips cleanly. Smoke-test (Scenario 2 defense) ships in the maintainer repo, not the consumer payload.
- **Symlink-stripping logic.** Symlink is retired — `reversibility-guard.sh:48,76` strip-prefix branch goes to dead code (a one-line ADR under `docs/adr/` retires it during the v1 cut). `role_guard.py` never needed strip logic; nothing to remove.
- **Cairn self-consumption circularity.** B explicitly picks **Path B** (cairn-the-repo keeps an in-repo registration; only consumers use the marketplace plugin). This resolves the Scenario 3 open question that Approach A leaves open. Maintainer dogfoods through the canonical checkout via a thin `.claude/settings.json` override committed to cairn (not shipped in payload).
- **Versioning + pinning.** Marketplace plugins carry semver tags as a first-class UX. `claude plugin install cairn@1.0.0` is the documented surface. SHA-pinning is still possible for power users but is not the consumer's primary path.

---

## 2. Pre-mortem responses

### Scenario 1 — Silent enforcement bypass (`role_guard.py` __file__ anchor)

**Defense.** B ships v1, which means Slice F1 includes the `role_guard.py:28` `CAIRN_ROOT` rewrite as a v1-blocking change (env-anchored: `Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))`). The marketplace-listing review surface (§3 below) requires a public README — Anthropic's listing review will ask "what happens if `$CLAUDE_PROJECT_DIR` is unset?" before the plugin goes live. **B addresses this scenario better than A** because the marketplace review is an external forcing function: a private git-URL install (Approach A) gets no second pair of eyes on the path-anchoring contract.

### Scenario 2 — Settings-merge drift across N consumers

**Defense.** Marketplace install uses Anthropic's manifest-merge contract, not bespoke shell-out semantics — manifest changes between versions are diff'd by the platform, and `claude plugin upgrade cairn` is the documented upgrade surface. B's curated payload (3 hooks, 0 slash-commands) makes the manifest small enough that human review of every release diff is feasible. **B addresses this scenario better than A** at N≥3 consumers because git-URL installs require each consumer to know they need to `git pull && claude plugin reinstall`, while marketplace pushes a notification.

### Scenario 3 — Self-consumption circularity (maintainer can't iterate on hooks)

**Defense.** B explicitly resolves the Path A / Path B open question (`brainstorm-decisions.md:25`) in favor of **Path B**: cairn-the-repo keeps a thin in-repo hook registration via canonical paths (`checks/role_guard.py` referenced directly from cairn's own `.claude/settings.json`); only consumers go through the marketplace. Maintainer iteration cost is unchanged from today (edit canonical → next tool call uses new code). The plugin-publish step is a release event, not a per-edit event. The Approach-A risk of "regression gated by previous version" never materialises.

### Scenario 4 — Adoption death by audience confusion

**Defense.** B's audience-tagged `CLAUDE.md` directly implements the portfolio review's *literal* suggestion at `2026-04-23-from-portfolio-evaluation.md:60-66` — "split into two files, **or add an explicit 'Audience' block at top**." The brainstorm picked the strawman (file split); B picks what the reviewer actually proposed. Single source of truth, section-tagged. **B addresses this scenario better than A** because file-split CONSUMER.md+CLAUDE.md doubles the surface where audience leakage can recur, while a tagged-block `CLAUDE.md` has one canonical location for every rule. Comprehensive templates with worked examples (Brainstorm #6) are in B too. The minimum-viable-cairn subset (`2026-04-23-from-portfolio-evaluation.md:103-105`) **is the curated payload itself** — B operationalises the open question.

### Scenario 5 — `.local/` leakage in plugin payload

**Defense.** `commands/` is not in B's payload. The leakage class is structurally impossible. Marketplace review is the second forcing function: Anthropic catches obvious internal-leakage on listing review even if the maintainer's deny-list regresses. **B addresses this scenario better than A** because A's "full-repo-minus-internals" model is an inverse-allowlist where every new internal directory is a regression candidate — the very pattern Scenario 5 calls brittle (`phase-1-pre-mortem.md:68`).

### Scenario 6 — Migration-orphan in flight

**Defense.** v1 stability means consumers migrate once, not repeatedly across pre-v1 churn. Curated payload means agent-registry slugs are the only cross-version contract, and v1 firms them. The marketplace `claude plugin install cairn@1.0.0` UX surfaces the version explicitly, so a consumer migrating from `.slice-system → .` knows what version they're landing on. The "finish or abandon, then migrate" workflow ships in the audience-tagged `CLAUDE.md`. Pre-migration `cairn migrate --dry-run` quiescence check (Scenario 6 defense) is in F3 either way.

---

## 3. Why this beats the alternatives

### Marketplace > git-URL on three axes

**Discoverability.** Git-URL install assumes the consumer already knows about cairn. Marketplace listing creates the funnel the portfolio evaluator's open-question 1 (`2026-04-23-from-portfolio-evaluation.md:103-105`) implicitly requires: a place where "minimum-viable-cairn consumer path" can be *named*. Curated payload IS that named answer.

**Version-pinning UX.** `claude plugin install cairn@1.0.0` is parseable by every consumer; `claude plugin install git+ssh://...@<sha>` is not. SHA-pinning the brainstorm picked (`brainstorm-decisions.md:8`) is power-user UX masquerading as consumer UX.

**Install reliability.** Marketplace install has retry semantics, signature verification, and rollback. Git-URL install fails on private-repo permissions, network blips, and SSH config — every one of which is a silent first-impression failure for a Role-1 consumer (`phase-0.5-journey.md:7-23`). The slower marketplace-review iteration is the *correct* trade because cairn iterates pre-v1 too fast for consumers anyway — slowing the public release cadence forces v1 stabilisation, which is the actual blocker per `2026-04-23-from-portfolio-evaluation.md:32,52,111`.

### Curated payload > full-repo-minus-internals

**Audit boundary.** Curated payload's allow-list is one paragraph and fits in the manifest. Approach A's deny-list is open-ended — every new `docs/<thing>/` directory is a potential leak (Scenario 5's exact failure mode at `phase-1-pre-mortem.md:65-71`). One-paragraph allow-list survives maintainer turnover; deny-list relies on memory.

**Smaller install + lower clobber risk.** Curated payload omits ~50% of the repo (no `docs/`, no `commands/`, no `scripts/` beyond hook deps). Less to download, less to namespace-collide with consumer's `.claude/`. Phase 0.5 §6 listed seven directories under "should ship" — B ships four.

### v1 first > pre-v1 ship

The portfolio review explicitly cited pre-v1 instability as the adoption blocker — three times (`2026-04-23-from-portfolio-evaluation.md:32,52,111`). Brainstorm decision #3 ("pre-v1; consumers pin SHAs and accept drift") **dares the same outcome the review predicts**. Closing the 6 amendment ADRs (cost-per-slice-budget, parallelism-v1, phase-pipeline-evaluation, feature-slice-model, context-tiers-integration, identifier-scheme) into firm:firm before ship is the single intervention with the highest expected adoption-ROI. Six ADRs of upfront work is finite; pre-v1 churn is unbounded.

### Audience block > file split

The portfolio reviewer's literal suggestion (`2026-04-23-from-portfolio-evaluation.md:66`): "split `CLAUDE.md` into two files, **or add an explicit 'Audience' block at top distinguishing `cairn-maintainer` rules from `cairn-consumer` rules**." File-split is the strawman. B picks the actually-endorsed option. Single source of truth means a rule like "Edit canonical paths only, never via `.slice-system/`" (`CLAUDE.md:11`) is tagged `[maintainer]` once, not duplicated and de-synced across two files. Constraint #6 (HARD) is the audience-ambiguity problem; tagged blocks solve it directly without doubling the maintenance surface.

---

## 4. Honest weaknesses

**Marketplace gatekeeping.** Anthropic's review pipeline introduces a publication-cadence dependency cairn doesn't control. If review takes three weeks and a security fix in `role_guard.py` needs to ship in two days, B has no fast-path. Mitigation: maintain the canonical-checkout install path as an emergency channel; document it as `[maintainer]`-tagged in `CLAUDE.md`. Still a real weakness.

**v1 cut adds 6 ADRs of upfront work.** Closing cost-per-slice-budget, parallelism-v1, phase-pipeline-evaluation, feature-slice-model, context-tiers-integration, identifier-scheme to `firmness:firm` is real work that delays the ship by weeks-to-months. The brainstorm picked pre-v1 ship precisely to avoid this cost. If any of those six is genuinely not yet ready to firm, B forces a hard stop until it is — which can stall indefinitely on a single unresolved ADR.

**Curated payload denies consumers the slash-commands cairn ships today.** `/catchup`, `/handoff`, `/decision`, `/new-adr` are real operator affordances. A consumer who adopts cairn and discovers they want `/decision` for their own ADR work has to either re-implement it or pull the canonical files out-of-band. This is genuine functionality loss, justified only if "methodology core vs operator-discipline aids" is a real boundary — and reasonable people can disagree. The portfolio evaluator's planned partial adoption (`2026-04-23-from-portfolio-evaluation.md:38-46`) actually wants several of these pieces, suggesting the boundary is contested.

---

## Synthesis

Approach B is **strongest on first-impression and audit-boundary axes**: marketplace listing creates the discoverability funnel cairn currently lacks, the curated payload makes Scenario 5's `.local/` leakage structurally impossible, and v1 stabilisation directly addresses the one adoption blocker the portfolio evaluator named three times. It is **weakest on iteration velocity**: marketplace gatekeeping plus a v1 cut means the ship date is bounded by Anthropic's review cadence and by closing six open amendment ADRs, neither under cairn's unilateral control. **A specific test that would falsify Approach B**: dispatch a fresh prospective consumer (not the portfolio evaluator, not complex-rag-analysis) at the curated payload + audience-tagged CLAUDE.md and ask them to onboard end-to-end without `/decision` or `/new-adr`; if they reach Phase-3 envelope denial and cannot recover within 30 minutes using only the shipped templates and tagged `CLAUDE.md`, the curated-payload boundary is wrong and Approach A's full-payload-minus-internals is the better answer.
