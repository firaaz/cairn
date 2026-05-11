# Phase 3 — Adversarial Stress Test

## Attacks on C

### A1. "No auto-routing this slice" is false on the artifacts C ships
**Claim under attack:** Phase 2-C §Concrete shape clause (c): "auto-routing of agents is **out of scope** for this slice (S3, S10 deferred to diagnostics slice)" — reinforced in §Pre-mortem S3 HANDLED and S10 HANDLED ("no auto-routing this slice").
**Disconfirming evidence:** All four nav agents on `origin/feature/workflow-subagents` declare auto-routing trigger phrases in their `description:` frontmatter, which Claude Code uses as the dispatch-trigger surface:
- `agents/slice-status.md:3`: `Auto-fires when user asks for slice/orchestrator status — phrases like "status?", "updates?", "is it still going?", "what phase are we in", "resume phase N".`
- `agents/worktree-map.md:3`: `Auto-fires when user asks "what shipped where", "status across worktrees", references multiple .worktrees/ paths in one message, or asks "what worktrees do I have".`
- `agents/adr-context.md:3`: `Auto-fires when user asks "what are the relevant invariants for X", "ADRs for this", "look up ADR on Y", or is about to make an architectural decision.`
- `agents/handoff-closer.md:3`: `Auto-fires when user says "handoff", "handoff and commit", "wrap up", "close out the session", or "commit the current fixes".`
**Verdict:** **breaks** — the agents are literally auto-routing agents. C's S3/S10 mitigations were predicated on "no auto-routing"; the artifacts shipped contradict it.
**Required correction:** Either (a) C must explicitly strip the `description:` trigger phrases (or scope them to literal slash invocation) before shipping, and the ADR must encode this as a normative rule, or (b) C must accept S3 and S10 as PARTIAL/EXPOSED — same posture as A — and ship a cairn-substrate pre-flight on every nav agent (mirroring the A-reshape for diagnostics). Option (a) is cheaper but loses the "auto-fires on phrase trigger" UX that motivates the branch.

### A2. `adr-context` carries a soft tooling-dep that C claims it doesn't
**Claim under attack:** Phase 2-C: nav agents are "zero-new-dep". Convergence note row "New consumer deps: 0 (this slice)".
**Disconfirming evidence:** `agents/adr-context.md` Step 2: `"Use ast-grep or grep to find ADRs naming the topic in title or body"` and Step 2 tool-preference block names `sg --pattern '...' --lang markdown` as the structural search option. The agent does not *require* ast-grep, but it cites it. Shipping the agent prompt into consumer payload means the prose ships too; operators who read the prompt will reach for ast-grep, reproducing S6 (PREREQS-shifts-friction) at a smaller scale.
**Verdict:** **cracks** — not a hard dep, but the prompt is a quiet recruiting vector for the same tooling C claims it isn't shipping.
**Required correction:** Strip the ast-grep cite from `adr-context` before merge (or replace with `Grep`-only path). Same edit for any other nav agent that name-drops ast-grep/Pyright/LSP.

### A3. `slice-status` and `worktree-map` hard-code cairn-shape assumptions and will misfire in non-cairn worktrees if the agents land at user scope
**Claim under attack:** C §Pre-mortem S3 HANDLED — "the four substrate-aware agents inherently no-op in non-cairn repos" (lifted from A's framing; C's own §Concrete shape relies on the same logic).
**Disconfirming evidence:** `slice-status` reads `.claude/handoff.md`, `.claude/current-slice/`, `.claude/orchestrator-debug/`, `/private/tmp/claude-*/` — cairn-specific paths. In a non-cairn repo the agent's "Degenerate cases" branch fires (`slice: none / phase: none`) and *still emits a 6-line card*, which is a noisy, confusing surface, not a clean no-op. `worktree-map` unconditionally runs `git worktree list --porcelain`; in a non-git directory this errors but the agent still emits a "no worktrees" line per its spec.
The fix-as-claimed ("inherently no-op") is incorrect: the agents produce *something* on every fire, and they fire on phrases as generic as `"status?"` and `"what worktrees do I have"` — phrases an operator will type in any project. If cairn is installed at user scope (which superpowers-style installs encourage, per PREREQS.md's recommendation that C inherits via SessionStart pointer), false-fire is the steady state, not the edge case.
**Verdict:** **cracks** — "inherently no-op" overstates the safety. The agents will fire and produce output in non-cairn repos.
**Required correction:** Add a one-line cairn-substrate guard at the top of each nav agent (`Refuse if .claude/active-envelope.yaml and docs/ARCHITECTURE.md absent`). Identical mechanism A applies to the diagnostics; deferring it for nav was unjustified.

### A4. CI token-budget enforcement has no precedent in the repo; S9 mitigation is more speculative than C admits
**Claim under attack:** C §Concrete shape: "CI token-budget check on the injected payload (mitigates S9)." Convergence: S9 PARTIAL "budget + CI" — treated as a known, available mitigation.
**Disconfirming evidence:** `.github/workflows/` contains exactly two files: `dist-gate.yml` and `release-publish.yml`. Neither enforces token budgets on shipped artifacts; dist-gate runs `build_dist.py`, allow-list pytest assertions, and `postinstall_validate.py` — all path/schema checks, no token counting. There is no existing token-counting tool, no tokenizer pinned in the project deps, and no precedent for budget enforcement on a SessionStart payload. The check is *implementable* but it is *unbuilt*, and the build/run/maintain cost is non-trivial (which tokenizer? what definition of "injected"? does it include lazy-loaded `.full.md` siblings or not?).
**Verdict:** **cracks** — the mitigation is real-in-principle but the convergence note's "PARTIAL (budget + CI)" reads as "we have CI" when in fact "we'd have to build CI for it." S9 is closer to EXPOSED than PARTIAL until the check is committed.
**Required correction:** Either (a) demote S9 to EXPOSED until the CI check lands, and treat the CI check as a load-bearing line item in this slice (not a follow-up), or (b) accept a prose-only budget invariant with no enforcement and acknowledge L-005 drift exposure in the ADR consequences.

### A5. Surface count understates audit cost vs. B
**Claim under attack:** C §Why this approach beats §"the 4 navigational agents + SessionStart share one ADR, one F3 audit, one release." Implicit claim: marginal audit cost over B is small.
**Disconfirming evidence:** B ships 1 artifact (SessionStart skill) + 1 ADR. C ships 5 artifacts (SessionStart + 4 agents) + 1 ADR + `dist/agents/` curation updates + plugin.json version bump + release-branch refresh. F3 audit check 9 (manual end-to-end install per m5-plugin-deployment-pattern D9) must verify each new agent loads on the consumer side and does not false-fire — that's 4 acceptance subchecks C ships and B does not. If even one nav agent needs the A1/A3 corrections above, C's audit re-runs.
**Verdict:** **cracks** — not a break, but C's audit surface is materially larger than the convergence framing suggests. "Same F3 audit" is technically true (one workflow run) but the *content* of the audit is 4× the inspected surface.
**Required correction:** Convergence note should state the F3 audit-surface ratio honestly (B: 1 SessionStart payload to verify; C: SessionStart + 4 agent prompts + their auto-route triggers + their pre-flight guards), so the operator can weigh the velocity claim.

### A6. Deferral of `pytest-triage`/`root-cause-hunter` leaves the branch in limbo with stale code
**Claim under attack:** C §Concrete shape: "defer to provisional slice `diagnostics-with-detection`." Convergence: C is "the only sequence that gives the 4 zero-new-dep agents a clean home with no contested decisions attached."
**Disconfirming evidence:** Branch is at `8b680cb`, +334 LOC, 1 commit. If C lands, 4 of 6 agents ship and 2 sit on an unmerged branch with no scheduled landing — the diagnostics slice is "deferred" with no date, no trigger condition beyond "evidence". By default, that is indistinguishable from "indefinitely". If postponed indefinitely, the branch author's contested hypothesis ("capability gain is worth setup-surface cost") goes untested — which is functionally **B**, plus more shipped agent-prompt surface and more ADR clauses to honor. The convergence note frames this as a virtue ("forces contested part through its own /decision"), but it is also a deferred-forever risk: there is no commitment to actually run the diagnostics decision.
**Verdict:** **cracks** — the deferral logic only holds if there's a concrete trigger for the follow-on slice; without it, C is B-plus-overhead.
**Required correction:** Slice ADR should name the *trigger condition* that opens the diagnostics slice (e.g., "next time J5 pytest-debug pain shows up in operator-field-notes-*, or by 2026-09-01, whichever comes first"). Without it, the deferral is rhetorical, not operational.

## Steel-man for B

B is the disciplined answer to a measured problem. Phase 0.5 verified exactly one thing about the current friction: J1 step 3–5 costs ~20 min of prose-reading because no SessionStart is wired. That is the *only* friction whose magnitude is verified. Every other claim — that `slice-status` is needed (vs. just running `git log` + reading `.claude/handoff.md`), that `adr-context` is needed (vs. running `/decision`'s Phase 0 by hand as the operator has done successfully for every prior decision in `.claude/skill-runs/`), that `worktree-map` is needed (vs. `git worktree list`), that `handoff-closer` is needed (vs. the operator's existing commit discipline already encoded in CLAUDE.md prose) — is asserted by the branch author, not measured against onboarding traces. C accepts those assertions and ships against them. B refuses, and ships only the SessionStart skill that the verified friction demands.

B's other virtue is that it leaves the contested commitments uncontested. The slice ADR in B contains three decisions; in C it contains four (the fourth being "navigational agents auto-fire on phrase triggers and ship in main payload"), and as A1/A3 demonstrate, that fourth decision is more contested than C admits. B's ADR is cheaper to write, cheaper to audit, cheaper to supersede if SessionStart turns out to need a different shape under evidence. The handoff-closer cherry-pick path B leaves open is the *correct* way to absorb branch work that genuinely reinforces substrate — narrow, named, evidenced — rather than C's broader posture of "if it's zero-new-dep, ship it."

The strongest claim for B: C is scope-creep dressed as synergy. The synergy story ("same ADR, same audit, same release") is real in cost-of-shipping terms but obscures the cost-of-being-wrong: when the 4 nav agents need post-merge corrections (A1, A2, A3), every one of those corrections re-runs the F3 audit, re-bumps the plugin version, and re-pushes the release branch. B's clean-stop position is more recoverable: if SessionStart turns out wrong, supersede one ADR and rewrite one skill. C's "ship 4 things that seemed safe today" multiplies the rollback surface 5×.

## Verified-vs-believed re-audit

| Claim | Phase 2 status | Re-audited status | Evidence |
|---|---|---|---|
| 1. "`using-cairn` is highest-leverage" | VERIFIED | **PARTIALLY VERIFIED** | Phase 0.5 verified J1#1 is the friction (~20 min prose, no SessionStart wired). It did *not* verify that SessionStart is the *highest-leverage* response — only that it's *a* response. If SessionStart pointer is 2k tokens and operators still need Tier-2 reads of CONSUMER.md / operational-reference / spec-v1, the friction may be displaced to mid-session rather than collapsed. No measurement on time-to-first-dispatch under SessionStart exists. |
| 2. "Friction is paid per-machine, every session" | VERIFIED | VERIFIED | Holds — no SessionStart hook in `.claude/settings.json` confirmed Phase 0.5. |
| 3. "Auto-routed > slash-command discovery" | NOT VERIFIED | NOT VERIFIED — and **C inherits this claim despite denying it** | C ships 4 auto-routing agents (A1); the convergence framing that "C is the only approach that doesn't paper over S3/S10 with prose" is contradicted by the artifact text. |
| 4. "Pyright/ast-grep/superpowers worth setup cost" | NOT VERIFIED | NOT VERIFIED | Still unmeasured. C doesn't ship them but `adr-context` cites ast-grep (A2). |
| 5. "Plugin-layout split is merge-blocker" | NOT YET VERIFIED | NOT YET VERIFIED | Out of scope for this attack pass. |
| C: "Nav agents have no contested decisions" | (implicit VERIFIED) | **FALSIFIED** | A1 + A3 surface contested decisions: auto-route trigger semantics, cairn-substrate pre-flight scope, false-fire posture in non-cairn worktrees. |
| C: "S3 HANDLED, S10 HANDLED" | HANDLED | **PARTIAL at best** | A1 shows the agents auto-route; mitigations Phase 1 required (substrate pre-flight, discoverable-trace announcement) are not in the artifacts. |
| C: "S9 PARTIAL via CI" | PARTIAL | **EXPOSED until CI is built** | A4: no precedent CI for token budgets; the check is unbuilt. |

## New scenarios surfaced (S11+)

### S11 — Auto-routing trigger phrases collide with operator's natural English in non-cairn worktrees
**Class:** integration / human
**Threatens most:** C (and A, but A has the diagnostics-only pre-flight)
**How it manifests:** Operator working in a non-cairn project types "status?" or "what worktrees do I have" (phrases verified in `slice-status.md:3` and `worktree-map.md:3`). Cairn-at-user-scope auto-fires the agent; the agent runs through its "Degenerate cases" branch and emits a 6-line card or table referencing cairn concepts (slice/phase/handoff) that mean nothing in the host project. Operator concludes cairn is leaking; methodology credibility takes the hit.
**Why it's plausible:** Phrase triggers are the most ordinary status-query English in the language. Cairn at user scope is the model B's SessionStart already implies (the skill loads from user-scope plugin install).
**Mitigations:** Substrate pre-flight on every agent (not just diagnostics); refuse-with-silent-exit when cairn-shape absent.

### S12 — Agent-name collision with future Claude Code / superpowers additions
**Class:** integration / reversibility
**Threatens most:** C (4 new agent names enter the namespace)
**How it manifests:** Names `slice-status`, `worktree-map`, `adr-context`, `handoff-closer` are generic enough that superpowers, another methodology plugin, or Claude Code itself could ship an overlapping name later. Claude Code's agent-dispatch resolution rules across plugin scopes are not specified in any cairn doc; collision is silent — wrong agent fires, or neither fires.
**Why it's plausible:** No namespace prefix on cairn agents today (`phase-1-tdd`, `triager-tdd` are cairn-flavored; `slice-status`/`worktree-map`/`adr-context`/`handoff-closer` are not). Superpowers ecosystem is active and could plausibly want any of these names.
**Mitigations:** Rename to `cairn-slice-status` etc., or document a namespace convention in the slice ADR. Cheap if done before merge; expensive after consumer adoption.

### S13 — Deferral of diagnostics slice has no trigger; functionally B + overhead
**Class:** governance / adoption
**Threatens most:** C
**How it manifests:** See A6. The "future diagnostics-with-detection slice" has no scheduled date, no operator-field-notes trigger, no quantitative criterion (e.g., "open after N pytest-debug pain reports"). It sits as an indefinite TODO. Without a trigger, C is operationally B-plus-4-agents — the contested-decision unbundling claim is unfalsifiable.
**Why it's plausible:** Cairn's own roadmap (per memory: "Gated" section of `docs/roadmap.md`) is the established pattern for indefinitely-deferred work.
**Mitigations:** Slice ADR names the trigger condition for diagnostics-slice; otherwise demote the deferral to "rejected" honestly.

## Corrections required

C must adopt these to remain the leader (in priority order):

1. **A1 fix (load-bearing).** Either strip auto-routing `description:` triggers from the 4 nav agents, or accept S3/S10 as PARTIAL and ship a cairn-substrate pre-flight guard on each. The convergence note's "no auto-routing this slice" must be retracted; the ADR must encode the actual posture.
2. **A3 fix (load-bearing).** Add a one-line substrate pre-flight to every nav agent (`refuse cleanly if .claude/active-envelope.yaml + docs/ARCHITECTURE.md absent`). Without it, S11 fires.
3. **A2 fix (cheap).** Strip the ast-grep cite from `adr-context`; replace with `Grep`-only. Apply same audit to the other 3 nav agents.
4. **S12 fix (cheap, before-merge).** Rename agents to `cairn-*` prefix, or commit to a namespace convention in the slice ADR.
5. **A4 / S9 honesty.** Either build the CI token-budget check in this slice (and treat it as load-bearing), or accept S9 as EXPOSED and name it in the ADR consequences.
6. **A6 / S13 fix.** Slice ADR names the trigger condition for the deferred `diagnostics-with-detection` slice (date, evidence-criterion, or both). Otherwise demote the deferral honestly.

If corrections 1+2+5 land, C survives. If 1+2 are rejected, C collapses to A's posture without A's capability gain — at which point **B is the better choice** (simpler, fewer auditable surfaces, same SessionStart benefit).

## Confidence after stress test

**MEDIUM** that C-with-corrections is the right choice. C-as-written has two breaks (A1, A4) and four cracks (A2, A3, A5, A6). The breaks are correctable in-slice; the cracks are mostly honesty-of-framing issues that the ADR can absorb. But if the operator rejects corrections 1 or 2 (the auto-routing rework and substrate pre-flight), C should not lead — B should.

The single load-bearing question for Phase 4: **does the slice ADR require substrate pre-flight + non-auto-routing on the 4 nav agents, or accept them as-is?** If yes → C leads with corrections. If no → switch to B.
