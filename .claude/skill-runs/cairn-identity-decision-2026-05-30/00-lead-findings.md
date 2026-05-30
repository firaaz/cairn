# Lead findings — Phase 0/0.5 synthesis (cairn identity decision)

Consolidated by the lead after Phase 0 (`01-constraint-envelope.md`) + Phase 0.5 (`02-journey-trace.md`) + direct reads of phase-lock-and-role-declaration, phase-pipeline-evaluation, slice-intent-contract, identity-and-scope-deferral, and `.claude/settings.json`. Read this + 01 + 02 before acting.

## F1 — Supersession scope is 5 ADRs + INV-003, not 2
Direction doc §5 lists only `[slice-intent-contract, identity-and-scope-deferral]` (both provisional). TRUE scope adds three FIRM ADRs: `phase-lock-and-role-declaration` (owns INV-003), `phase-pipeline-evaluation` (reaffirmed INV-003), `feature-slice-model` D0 (couples slice→4-phase; partial `supersedes-sections` amendment — agent-asserted, verify before ADR). Plus INV-003 retirement/amendment + ≥1 new invariant. Heavier blast radius than the direction doc frames.

## F2 — phase-pipeline-evaluation is the heaviest counter-evidence (and it backs comparator B)
FIRM ADR (2026-04-13), evaluated the 4 phases on 5-slice evidence. Findings: 4 cognitive modes "resist compression"; roles non-vacuous across code/non-code; **"no phase should be skippable — the fix for heavy ceremony is LIGHTER ceremony WITHIN phases, not fewer phases"** (= comparator B, with empirical backing); A2 isolation canary NOT FIRED (0/5 slices leaked) — the session boundary IS isolating.
Honest charter-cycle rebuttal: it confirms the cognitive modes are valuable, NOT that they must be SESSION boundaries vs subagent dispatches, and it predates arc A's native-subagent landscape. The charter cycle does NOT actually drop the cleaves (charter-formation=Intent; skeptic-worker=Validation/test-first; build-worker=Implementation; verify-worker=Integration/Auditor with build≠check) — it replaces the heavy MACHINERY (session-boundary ceremony, AGENT_ROLE, per-phase commit gates, fixed SKILL.md) with subagent dispatch + charter. "Phases-out" oversells; "machinery-out, cleaves-preserved-via-subagents" is the honest claim. → A and B may CONVERGE.

## F3 — The headline value is currently unmechanized (Gap 1, FATAL-as-designed/fixable)
The §6 re-injection hook (goal+amendments re-injected per turn — "the one lever that holds") DOES NOT EXIST: settings.json wires only PreToolUse+PostToolUse; no SessionStart/UserPromptSubmit. The charter isn't CLAUDE.md, so nothing re-injects it post-compaction. The "complement" identity (goal-commitment-vs-reactivity) rests on prose discipline today. ADR must commit the hook as a BUILD DELIVERABLE, not narrate it as mechanical.

## F4 — In-cycle /decision re-introduces a rejected collapse (Gap 6, FATAL unless re-scoped)
§7's decision-touching route nests a full /decision pipeline BETWEEN charter-commit and build. phase-lock rejected exactly this (its Approach C "Pre-Decision phase") on the upstream-asymmetry principle: decisions belong UPSTREAM of slices, not inside. ADR must route decision-goals as a separate upstream cycle OR explicitly supersede the principle (and own pulling decision-adversariality into the same lead window that builds against it).

## F5 — Blind workers have no per-worker write scope (Gap 2, fixable-in-ADR = open-question #2)
AGENT_ROLE is dead code (role_guard reads it; dispatch never injects). Blind workers gated only by the worktree-global operator envelope → no write-confinement beyond a normal session. ADR must decide: native per-subagent tools/permissionMode frontmatter vs a SubagentStart hook vs both.

## F6 — Return-channel accumulation (C3 residual, Gap 3, accept-and-document/hardenable)
C3 ("subagents can't re-pollute the parent") holds per-dispatch but degrades as ONE lead accumulates harvest→build→verify(+decision) returns across a pipeline. Arc A's four provisos (committed-artifact channel / capped returns / foreground+named / fork-hostile) are disciplined PROSE in a SKILL.md the design rewrites — enforced by no hook. Harden proviso (a).

## F7 — Mechanism-deferral (§3) is constrained-anyway, not just a bet
invariant-binding-strategy validator-type whitelist is CLOSED: 5 implemented (grep/file-exists/test-ref/git-log-walk/structural-parser); ast+custom v2-deferred. Semantic intent↔ADR alignment is architecturally unmechanizable under the whitelist without a new validator-type ADR. → §3's "never mechanize semantic alignment" is a near-constraint, not merely a preference. Strengthens the deferral.

## F8 — R2 is the surviving steelman of "defer again" (Phase-3 runner-up to steelman)
identity-and-scope-deferral (2026-05-20) rejected ~this direction (its Approach 3). Its "rebranding not redesign / doc-only cheaper" ground is now DEAD (the charter cycle is a real redesign). But its R2 (option value: M4-pivot precedent + single-operator + no external pull) SURVIVED and got HEAVIER: the cycle commits MORE firm state on evidence no more settled (C1 cliff unmeasured in cairn; C5-C8 never skeptic-verified), re-opened by operator fiat (its D3.4 trigger) not matured evidence. If synthesis can't answer R2, the supersession is re-litigation with a bigger blast radius.

## Anchors that hold
Append-only ADR guard + validator gate are real and survive. The cross-slice substrate (C5–C8) IS the claimed durable identity — but C5–C8 were never skeptic-verified (Phase-3 attack target), and C1 (the cliff) is unmeasured in cairn.
