---
id: phase-lock-and-role-declaration
status: accepted
contract:
  must-satisfy:
    - "phase roles match the declared topology and write locks (carrier: checks/role_guard.py + scripts/validate_architecture.py INV-003 phase-topology)"
  evidence:
    - "uv run python scripts/validate_architecture.py"
firmness: firm
supersedes: []
supersedes-sections: []
superseded-by: null
topic: process
invariants-touched: [INV-003]
date: 2026-04-11
---

# phase-lock-and-role-declaration: Four-Phase Pipeline Lock and Role Declaration

## Status
Accepted

## Date
2026-04-11

## Context

`docs/vision.md` commitment #5 marks the four-phase pipeline (`Intent → Validation → Implementation → Integration`) as **plastic through v1**: "The phase rethink is a first-class work item that runs through `/decision` and may produce 3, 4, or 5 phases with different names or boundaries." Commitment #6 commits to explicit cognitive roles per phase with anti-behaviors, "exact names decided with the phase rethink." Neither commitment has been resolved.

cliff-failure-mode-and-v1-defenses D4 explicitly preserves the phase rethink on the v1 critical path ("Commitment #5 (plastic phases) is NOT in the time-box") and names it as load-bearing for D1/D2/D3: the phase shape determines where each defense hooks into the pipeline. `docs/plans/2026-04-11-adr-003-v1-execution-plan.md` §P0a makes this concrete — the phase rethink "runs as a standalone `/decision`, not a slice" and must land "before the `phase-lock-and-role-declaration` operationalization slice to avoid D1/D2/D3 churn cost."

The `/decision` session producing this ADR was framed by two prior exploratory sessions captured in `.claude/current-slice/exploration-notes.md` (2026-04-11), which produced a concrete 5-phase RIPER-inspired proposal (Intent→Design→Validation→Implementation→Integration with Reader/Architect/Skeptic/Builder/Auditor roles), and by `docs/reviews/2026-04-11-from-rag-session.md` Finding 3, which proposed a different 5-phase shape with a Pre-Decision gate making Decision→Intent immutability structural rather than prescriptive. Neither proposal had been committed; both were candidates for this decision.

Concurrent with this `/decision` session, `docs/lessons.md` L-002 was captured, formalizing the route-before-run pattern (triage → framing → analysis/execution) and observing that the current session ran as a clean 1-flow `/decision` because `exploration-notes.md` played the upstream brainstorming role, which the session boundary to today preserved as framing isolation.

This ADR resolves commitment #5 and commitment #6 together as a single firm decision and names a mechanical mitigation for the one load-bearing belief the decision rests on.

## Decision

Cairn commits to the following four claims.

### D1 — The slice pipeline has exactly four phases, locked in order and name

The pipeline is `Intent → Validation → Implementation → Integration`. No phase is added, removed, renamed, or reordered without a superseding ADR. The names are load-bearing: `/catchup`, `/start-slice`, `scope-guard.sh`, `checks/reality-check.sh`, `docs/operational-reference.md`, and the `slice.yaml status` field all string-match on these phase names. A rename is not a refactor; it is a supersession.

Two alternative proposals that emerged during the decision are explicitly rejected but preserved in the Alternatives section as first-class successor candidates in case the risk register's A2 tripwire (below) fires:

- **5-phase RIPER split** (Intent+Design separated) — rejected because the "Architect writes code prematurely" anti-behavior the proposal solves is already structurally prevented by the Phase 1→Phase 2 session boundary per context-discipline-protocol, and because the proposal's proposed `design.md` artifact carries an unmitigated Pre-Mortem F1 risk (too loose to gate on).
- **5-phase Pre-Decision gate** (Decision-as-phase-zero) — rejected because it duplicates the `/decision` protocol and risks collapsing the two mechanisms. Its structural gain (Decision→Intent immutability becomes a phase-gate property) is absorbed into this ADR by a one-line addition to `commands/claude-code/start-slice.md` Step 3 gate check (below).

### D2 — Each phase has a named role with anti-behaviors, declared in protocol text

Roles are **instructed**, not hook-enforced. This is consistent with cliff-failure-mode-and-v1-defenses D4's v1 time-box ("Mechanized role assignment per phase — commitment #6 mechanization — remains deferred; roles stay instructed in protocol text, not hook-enforced. v2 re-opens mechanization.") and constraint C4 of this decision's envelope. Roles are surfaced at phase entry; see D4.

| Phase | Role | Primary anti-behavior | Secondary anti-behaviors |
|---|---|---|---|
| 1. Intent | **Reader** | Reader does not propose implementation | Does not read source code (greenfield slices) or reads only public interfaces (modification slices); does not write design-flavored content beyond `intent.md` Zone 2 "Specification Detail" |
| 2. Validation | **Skeptic** | Skeptic does not implement | Does not read Phase 3's implementation; enumerates ambiguities in `intent.md` and resolves them by reference to ARCHITECTURE.md/ADRs or escalates before writing any test |
| 3. Implementation | **Builder** | Builder does not re-litigate the spec or the tests | Does not expand the envelope beyond `slice.yaml`'s declared files; does not load Phase 2's `approach.md` or reasoning about why tests are shaped as they are |
| 4. Integration | **Auditor** | Auditor does not rewrite the implementation | Produces pass/fail verdict on declared invariants with `file:line` citation evidence; on implementation failure, fails the slice per `docs/spec-v1.md` §13 item 8 rather than patching |

### D3 — Pre-Decision structural immutability (absorbed from rejected Approach C)

`commands/claude-code/start-slice.md` Step 3 gate check gains one additional rule: advancing from Phase 1 (Intent) to Phase 2 (Validation) requires that every ADR named in `intent.md`'s `adrs-referenced` YAML field exists as a committed file in `docs/adr/`. Verified by: `git log --oneline -- docs/adr/<adr-slug>.md` returns at least one commit for each declared ADR. This structurally enforces `docs/spec-v1.md` §6's Decision→Intent Immutability rule without adding a new phase. It is the one-line absorption of the "5-phase Pre-Decision gate" proposal's structural gain.

If `intent.md`'s `adrs-referenced` field is empty, the gate passes trivially — this matches the existing low-consequence-slice semantics and does not add friction to cleanup or pure-implementation slices.

### D4 — Phase→skill mapping exists and is surfaced at phase entry

**Commitment.** A phase→skill mapping lives in `docs/operational-reference.md` § Phase Skill Guide (new section, landed by the follow-up slice named in Consequences below). The mapping is a living registry — updates to it do not require ADR supersession, analogous to how `docs/ARCHITECTURE.md` is a living derived view regenerated by `/refresh-architecture`. This ADR commits to the registry's existence, not to specific skill names.

**Surfacing mechanism.** `/catchup` and `/start-slice` read the registry at phase entry and print the target phase's role, anti-behaviors, and recommended skills to the operator. This is the direct mitigation for Risk F6 (role declarations becoming dead ADR text) in the risk register below. No hook-enforcement is introduced; surfacing is textual at phase entry, consistent with constraint C4.

**Initial mapping (evidence-backed first-cut).** Citations are to Superpowers plugin skill files at `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/`.

| Phase | Role | Primary skills | Supporting skills | Notes on adaptation |
|---|---|---|---|---|
| 1. Intent | Reader | — (`commands/claude-code/start-slice.md` Step 5 is the protocol guide) | — | No Superpowers skill is a primary fit for Phase 1 because `intent.md`'s Zone 1/2/3 schema is cairn-specific. `brainstorming` runs *upstream* of Phase 1 per L-002 (framing step), not inline. |
| 2. Validation | Skeptic | `superpowers:test-driven-development` (`test-driven-development/SKILL.md:31-38` Iron Law) — the **RED + Verify RED** half of the red-green cycle | `superpowers:brainstorming` for ambiguity enumeration (`brainstorming/SKILL.md:70-79` one-question-at-a-time style aligns with `start-slice.md:44-48` Phase 2 protocol) | TDD's red-green cycle is structurally bisected by cairn's session boundary: the Skeptic commits the failing tests (RED + Verify RED) without ever touching production code, and hands off to Phase 3 via commit. This is a non-obvious adaptation of the skill. |
| 3. Implementation | Builder | `superpowers:test-driven-development` (`test-driven-development/SKILL.md:130-196` GREEN + Verify GREEN + REFACTOR), `superpowers:verification-before-completion` (`verification-before-completion/SKILL.md:17-22` Iron Law) | `superpowers:subagent-driven-development` (`subagent-driven-development/SKILL.md:41-85` when envelope has multiple independent files), `superpowers:receiving-code-review` when review feedback arrives | Builder completes the TDD cycle that Phase 2 started. `verification-before-completion` is mandatory before ending Phase 3: tests must be run fresh, output cited, no "should pass" claims. |
| 4. Integration | Auditor | `superpowers:verification-before-completion` (same Iron Law, applied to full-suite + validator + invariant checks), `superpowers:requesting-code-review` (`requesting-code-review/SKILL.md:13-22` mandatory before merge) | `superpowers:systematic-debugging` (`systematic-debugging/SKILL.md:22-26` Iron Law) as escape route if an invariant check fails; `systematic-debugging/SKILL.md:199-213` "If 3+ Fixes Failed: Question Architecture" maps directly to spec-v1 §13 item 8's Phase 4 death spiral discipline and this ADR's D2 anti-behavior ("Auditor does not rewrite") | Auditor is the terminal phase — pass/fail judgment with evidence. Code-reviewer subagent dispatched via `requesting-code-review` is the external check for invariant verification. If invariants fail, systematic-debugging governs the response path (investigate, do not patch; escalate to fail-and-restart after 3 failed fixes). |

**Explicit exclusions and why**:

- `superpowers:dispatching-parallel-agents` — parallelism-native work violates v1 single-slice discipline per cliff-failure-mode-and-v1-defenses D4 ("Vision commitment #2 parallelism-native is time-boxed to v2+").
- `superpowers:executing-plans` — the parallel-session variant of `subagent-driven-development`; inside a Phase 3 session, same-session subagent dispatch is the right choice.
- `superpowers:finishing-a-development-branch` — cairn's slice-close protocol (`/start-slice complete`) supersedes it for slice work; applies to non-slice development only.
- `superpowers:using-git-worktrees` — worktrees are for parallelism or isolation from shared state; v1 single-slice work does not need them. Listed as conditional in Phase 3 only if a subagent-driven task explicitly requires it.
- `superpowers:writing-skills`, `superpowers:writing-plans` — meta-skills that sit outside any slice phase.

### Invariant declaration

**INV-003**: Every slice runs through exactly four phases in order — Intent (Reader), Validation (Skeptic), Implementation (Builder), Integration (Auditor). Each phase's role and anti-behaviors are surfaced at phase entry by `/catchup` and `/start-slice` by reading from `docs/operational-reference.md § Phase Skill Guide`. The phase count is locked at four; the names are locked as listed; the roles are locked as listed. Changes to any of these require a superseding ADR. (phase-lock-and-role-declaration)

## Consequences

- **Commitment #5 (plastic phases) is resolved.** The phase shape is no longer "plastic through v1" — it is locked by this ADR. `docs/vision.md` commitment #5 is targeted-superseded for v1 purposes in the same manner cliff-failure-mode-and-v1-defenses D4 targeted-superseded vision.md commitments #1/#2/#6 (mechanization): the vision.md text is not edited; this ADR is the authoritative record.

- **Commitment #6 (explicit roles) is resolved.** Roles are named (Reader/Skeptic/Builder/Auditor), anti-behaviors are named, and the surfacing mechanism is committed. The mechanization portion of commitment #6 remains time-boxed to v2+ per cliff-failure-mode-and-v1-defenses D4 and is not addressed here.

- **the `phase-lock-and-role-declaration` operationalization slice (D1 design) is unblocked.** Per cliff-failure-mode-and-v1-defenses Consequences and `docs/plans/2026-04-11-adr-003-v1-execution-plan.md` §P0a ("the phase rethink ADR must land before the `phase-lock-and-role-declaration` operationalization slice to avoid D1/D2/D3 churn cost"), this ADR's land satisfies the prerequisite. the `phase-lock-and-role-declaration` operationalization slice can now be designed against a fixed phase shape.

- **INV-003 is added to `docs/ARCHITECTURE.md`** at the next `/refresh-architecture` run. The validator's Check B (every firm ADR has an invariant) is satisfied by INV-003's pairing with phase-lock-and-role-declaration.

- **A follow-up slice (the `phase-lock-and-role-declaration` operationalization slice-precursor) implements the D4 surfacing.** Scope: (a) add `§ Phase Skill Guide` section to `docs/operational-reference.md` carrying the initial mapping from this ADR's D4 table verbatim; (b) update `commands/claude-code/catchup.md` to read the guide and print role/anti-behaviors/skills on phase entry; (c) update `commands/claude-code/start-slice.md` to do the same and add the D3 `adrs-referenced` gate check to Step 3. This slice is explicitly **pre-D1** and does not fold into the `phase-lock-and-role-declaration` operationalization slice's D1 scope. It is a small commit-#6 follow-through slice whose entire purpose is to make this ADR's D2 and D4 commitments operationally visible.

- **the `context-discipline-protocol` operationalization slice (stopped at Phase 2) does not need migration.** the `context-discipline-protocol` operationalization slice's phase 2 artifacts in `.claude/current-slice/validation/approach.md` are design-flavored but remain in `validation/`; this ADR does not introduce a separate Design phase. the `context-discipline-protocol` operationalization slice resolves per `docs/plans/2026-04-11-adr-003-v1-execution-plan.md` §P0b (review-amend-or-supersede) without phase-shape migration cost.

- **cliff-failure-mode-and-v1-defenses and phase-lock-and-role-declaration have different firmnesses deliberately.** cliff-failure-mode-and-v1-defenses (target failure mode + D1/D2/D3/D4 scope) is `firmness: provisional` because the cliff framing and defense set are expected to be superseded after dogfood. phase-lock-and-role-declaration (phase shape) is `firmness: firm` because the phase shape is load-bearing for every downstream slice and supersession cost rises linearly with the number of slices built on it — making the firm commitment honest about the cost of revisiting. The two ADRs resolve different classes of uncertainty; the firmness asymmetry reflects that.

- **`docs/spec-v1.md` §5 and `docs/operational-reference.md` are consistent with this ADR as written.** No edits required to either at propagation time beyond adding the `§ Phase Skill Guide` section in the follow-up slice. The phase count, names, and order already match. `docs/spec-v1.md` §9 (three-track routing, marked `[DESIGN-ONLY]`) is **not** resurrected by this ADR; track-based phase counts remain deferred. Low-consequence slices use the four-phase shape with a trivially-passing D3 gate (empty `adrs-referenced` field).

- **L-002 (route-before-run triage pattern) is referenced but not superseded.** L-002 governs how units of work route to flows (triage → framing → analysis/execution). phase-lock-and-role-declaration governs the shape of the `/start-slice` flow itself. The two are orthogonal commitments.

- **Pipeline-substrate commit class is unchanged.** This ADR does not create a new commit class. The follow-up slice that implements D4 surfacing runs through the normal four-phase pipeline and produces slice-phase commits, not pipeline-substrate commits. Per L-001 and cliff-failure-mode-and-v1-defenses Consequences, `/refresh-architecture` and `/integration-sweep` commits remain the only named non-slice commit classes.

- **Team-rollout legibility.** When cairn is introduced to teammates during the personal-to-team transition (`docs/vision.md` § "What cairn is"), the phase shape + role declarations provide the operational vocabulary. Without this ADR, cairn documents four phases but has no durable role names; with it, Reader/Skeptic/Builder/Auditor become the shared language for phase conversations.

- **Phase 5 Independent Verification was run on the draft.** After the draft commit (`49e45e9`), a fresh general-purpose subagent received only the constraint envelope, `docs/ARCHITECTURE.md`, ADRs 001–003, `docs/vision.md`, `docs/spec-v1.md`, `docs/lessons.md`, `docs/plans/2026-04-11-adr-003-v1-execution-plan.md`, `.claude/current-slice/exploration-notes.md`, `docs/reviews/2026-04-11-from-rag-session.md`, and the current protocol skill files — with explicit instruction to NOT read this ADR's body. The subagent independently harvested constraints, ran a user-journey trace, generated a pre-mortem, enumerated four phase-shape approaches (including genuinely derived variations), and stress-tested the strongest. It converged on the same 4-phase lock with the same Reader/Skeptic/Builder/Auditor role set, the same `firmness: firm` choice, and the same load-bearing belief — Intent-conflation risk addressable by a written Reader anti-behavior rather than by a dedicated Design phase. Minor protocol bug observed during the verification: the subagent's instruction to read `docs/adr/index.md` leaked the title "Four-Phase Pipeline Lock and Role Declaration" via the new phase-lock-and-role-declaration row, partially pre-anchoring phase count = 4. This is captured as a follow-up protocol improvement — future `/decision` runs should defer the index update from the draft commit to Phase 6 propagation to preserve Phase 5's isolation cleanly.

## Alternatives Considered

This ADR enumerated five approaches during `/decision` Phase 2 and stress-tested Approach A (the accepted one) in Phase 3. The four rejected approaches are preserved here in full detail because Approach B and Approach C are first-class successor candidates if the risk register's A2 tripwire (below) fires. The `/decision` session's full enumeration and stress test are in the git history via this commit's message and the decision protocol's session artifacts.

### Approach B — 5-phase RIPER split (rejected)

**Core idea**: Split Intent into Intent(Reader) and Design(Architect). Intent becomes research-only; Design is new and produces `.claude/current-slice/design.md` with module boundaries, interface sketch, and data shapes. Validation reads design.md + intent.md. Implementation reads tests + design.md + intent.md (not Validation's approach.md). Integration unchanged.

**Source**: `.claude/current-slice/exploration-notes.md:157-175` (two exploratory sessions on 2026-04-11 authored this proposal in detail, including the full 5-role table with anti-behaviors).

**Proposed roles**: Reader (does not propose), Architect (does not run tests), Skeptic (does not implement), Builder (does not re-litigate), Auditor (does not rewrite).

**Why rejected**:

1. **The problem is already solved.** `docs/spec-v1.md:88` and `docs/operational-reference.md:24` both textually commit Intent to research-only semantics ("don't read source code, greenfield" / "only public interfaces, modification"). The *structural* mechanism preventing Phase 1 reasoning from contaminating Phase 2 is the **session boundary** between them, backed by context-discipline-protocol Layer 3 (slice-closure wipes `.claude/current-slice/`) and Layer 1 (handoff as pointer, not narrative). Adding a Design phase introduces a session boundary to solve a problem that is already solved by a different session boundary.

2. **Pre-Mortem F1 is unmitigated.** Design phase's artifact (`design.md`) is structurally the "too loose to gate on" failure mode. Unless it carries a strict schema — interfaces, wire formats, call shapes, data contracts — Validation(Skeptic) silently re-reads `intent.md` instead and Design becomes narrative residue, which is exactly the anti-pattern context-discipline-protocol Layer 1 was written to prevent. The 5th phase exists but context isolation at its boundary is fake.

3. **Pre-Mortem F3 — friction multiplier against dogfood pace.** +1 phase ≈ +25% session boundaries. cliff-failure-mode-and-v1-defenses commits to 10 slices by 2026-10-11 as the dogfood gate for D1/D2/D3. 5 phases × 10 slices adds ~12 session transitions over 6 months before any D1/D2/D3 evidence is generated. The friction tax begins competing with the cliff-prevention benefit, and operators start collapsing phases in practice, restoring the correlated-error path.

4. **The RIPER critique is a schema problem, not a phase-count problem.** `commands/claude-code/start-slice.md:148-166` defines `intent.md` Zone 2 "Specification Detail" as "Protocol-level commitments: wire formats, key patterns, return shapes, error codes." That is already design content with a clean schema. The cheap fix for "Architect writes code in Intent" is tightening Zone 2 into a required "Interface sketch" subsection — absorbed into this ADR's D2 "Reader anti-behaviors" row — not a new phase.

**Preserved for**: if A2 tripwire fires, Approach B is the first-class successor candidate. Its proposed role set (5 roles with anti-behaviors) is the labeled input for the superseder.

### Approach C — 5-phase Pre-Decision gate (rejected)

**Core idea**: Formalize "the decision that precedes this slice" as a first-class phase. Pre-Decision's artifact is the ADR (or pointer to the ADR) that the slice implements. Its gate checks `git log --oneline -- docs/adr/` for the referenced ADR. If no upstream ADR exists, the slice is low-consequence and the phase passes trivially.

**Source**: `docs/reviews/2026-04-11-from-rag-session.md:141-183` (Finding 3); `docs/spec-v1.md` §9 (the 5-phase track proposal it rehabilitates from `[DESIGN-ONLY]` status).

**Why rejected**:

1. **Pre-Mortem F2 — duplicates `/decision` and violates the upstream asymmetry principle.** Pre-Decision inside a slice risks collapsing with the existing 8-sub-phase `/decision` protocol. The subtle distinction between "Pre-Decision is a gate that an ADR exists" and "Pre-Decision is a mini-`/decision`" will be lost in practice under operational pressure unless the ADR makes the distinction airtight. Beyond duplication, the proposal violates the structural asymmetry `docs/reviews/2026-04-11-from-rag-session.md` Finding 4 (lines 185–245) names: *"slice phases are method-agnostic; decisions are method-prescribed. The asymmetry is the whole trick."* Absorbing `/decision` into a slice phase collapses that asymmetry — slice phases would gain prescribed sub-phases, re-creating the within-session role-switching problem `docs/spec-v1.md` §2 explicitly rejects. Both the duplication risk and the asymmetry violation point at the same conclusion: decisions belong **upstream** of slices (per `docs/lessons.md` L-002's Step 2 routing), not **inside** them. Either outcome violates constraint C7 (distinct `/decision` protocol from slice phases).

2. **Friction is structurally unchanged.** +1 phase = +1 session boundary, same F3 exposure as Approach B.

3. **The structural gain is absorbable.** Approach C's main upside — Decision→Intent immutability becomes a phase-gate property rather than a prescriptive rule — is captured by this ADR's **D3** (one-line `adrs-referenced` gate check in `start-slice.md` Step 3). The phase-count cost is avoided while the structural gain is preserved.

**Preserved for**: if the dogfood reveals that low-consequence slices routinely skip needed `/decision`s, Approach C's explicit Pre-Decision phase becomes a stronger candidate than this ADR's gate check. The gate check catches the case where the intent declares a referenced ADR but the ADR doesn't exist; it does NOT catch the case where the intent should have referenced an ADR but didn't. Approach C's stronger semantics address the second case at higher friction.

### Approach D — 6-phase combination (rejected)

**Core idea**: Combine Approaches B and C. Pre-Decision → Intent → Design → Validation → Implementation → Integration.

**Source**: synthesis of the two candidate proposals above. No primary source in the cairn corpus.

**Why rejected**: inherits both B's F1 exposure and C's F2 exposure. F3 friction is maximal (+2 phases = ~50% session multiplier against dogfood pace). The composition's only merit is "lose no structural gain from either proposal," which is outweighed by the friction catastrophe against cliff-failure-mode-and-v1-defenses's dogfood deadline.

### Approach E — 3-phase collapse (rejected)

**Core idea**: Collapse Validation and Implementation into a single "Build" phase using TDD-by-default. The slice loses the strict separation between test author and implementer within a session. Trade: ~25% fewer sessions per slice.

**Source**: `docs/spec-v1.md:167` (the 3-phase low-consequence track from §9 "Three-Track Routing", marked `[DESIGN-ONLY]`).

**Why rejected**: fundamentally incompatible with `docs/spec-v1.md` §2 Core Thesis ("A single agent in a single session cannot both author and consume the spec faithfully. The slice protocol exists because within-session role switching cannot be trusted."). Phase 2 and Phase 3 must not share a session — this is the central correlated-error defense. Approach E denies the thesis. Listed only to honor `/decision` Phase 2's genuine-enumeration rule.

## Risk Register

The pre-mortem generated six failure scenarios. Each is addressed below with the chosen approach's mitigation.

- **Risk F1 — Design phase's committed artifact is too loose to gate on (Approach B scenario).** `docs/spec-v1.md` §2's session-isolation thesis requires each phase's artifact to be specific enough to drive the next phase as a black-box input. Approach B's `design.md` risked being too vague. **Mitigation by approach choice**: not building a Design phase. The existing `intent.md` Zone 2 "Specification Detail" schema at `commands/claude-code/start-slice.md:148-166` is adequate as the Reader's structured artifact; if it proves too loose in practice, it can be tightened as a living-registry update to `operational-reference.md` without ADR supersession.

- **Risk F2 — Pre-Decision phase duplicates or collapses with `/decision` (Approach C scenario).** **Mitigation by approach choice**: not building a Pre-Decision phase. The structural gain is absorbed by the D3 `adrs-referenced` gate check, which enforces existence-of-upstream-ADR without running the 8-sub-phase `/decision` protocol a second time.

- **Risk F3 — Friction multiplier against cliff-failure-mode-and-v1-defenses dogfood pace.** **Mitigation by approach choice**: 4 phases at the current count, no session-boundary increase, baseline friction unchanged. The cliff-failure-mode-and-v1-defenses dogfood window (10 slices by 2026-10-11) is not delayed by this ADR.

- **Risk F4 — D1/D2/D3 design slices start against a phase shape that turns out unstable.** **Mitigation**: firmness is firm. Supersession requires a new ADR; drift cannot occur silently. If supersession is triggered (see A2 tripwire below), the `phase-lock-and-role-declaration` operationalization slice (D1) is the first slice affected; its phase shape is migrated explicitly in the superseding ADR's Consequences section.

- **Risk F5 — Failed-slice recovery's "integration" string match breaks on rename.** `commands/claude-code/start-slice.md:198` Step 8 checks `status == integration` as the failed-state trigger. **Mitigation by approach choice**: no rename happens. The terminal phase remains "integration."

- **Risk F6 — Roles named textually but become dead text that nothing surfaces.** This is the single largest risk to D2's legitimacy. **Mitigation**: D4 is a structural mitigation, not a textual one. The phase→skill registry must exist in `docs/operational-reference.md § Phase Skill Guide`, and `/catchup` and `/start-slice` must read from it and print it at phase entry. The follow-up slice named in Consequences is what makes this mitigation mechanical rather than aspirational. **If the follow-up slice does not land within two slices of phase-lock-and-role-declaration, F6 is materially unmitigated and phase-lock-and-role-declaration is on a trajectory to supersession.** This is a load-bearing follow-through commitment, not a nice-to-have.

### Assumption audit — A2 (the load-bearing belief)

The accepted approach (four-phase lock) rests on seven assumptions. Six are verified or degrade gracefully. One — **A2** — is a belief with no operational evidence and degrades catastrophically if wrong. Because this ADR is `firmness: firm`, A2 requires a concrete mechanical tripwire rather than human attestation.

**A2 — belief**: The Phase 1→Phase 2 session boundary already provides sufficient isolation to prevent the "Architect writes code prematurely" anti-pattern that Approach B was designed to address. That is: an `intent.md` committed by a Phase 1 (Reader) session, loaded fresh into a Phase 2 (Skeptic) session, will not contain smuggled implementation reasoning that contaminates the test design.

**A2 — evidence status**: `docs/spec-v1.md:86-96` names the session boundary as the mechanism; context-discipline-protocol Layer 3 (wipe-on-close) backs it structurally. Cairn is 2 slices deep (the `validator-symlink-fix` slice shipped; the `context-discipline-protocol` operationalization slice stopped). No slice has operationally demonstrated or refuted A2.

**A2 — degradation mode**: if A2 is wrong, `intent.md` silently accumulates design-flavored content that contaminates Phase 2's test design. The failure is invisible within a single slice because Phase 2's tests are still "derived from intent.md" — they just happen to be derived from intent.md's design reasoning rather than its specification. The failure surfaces only at dogfood scale when compound drift produces tests that verify implementation assumptions rather than specification properties.

**A2 — mechanical tripwire**: `/integration-sweep` (and in v1, a manually-run equivalent until D3 lands) compares each slice's `.claude/current-slice/validation/approach.md` (or its git-history equivalent) against the committed `intent.md` for that slice's Phase 2 transition. Specifically: identify design tokens (interface names, function signatures, wire format identifiers, schema names) present in `approach.md` but absent from `intent.md`. If more than **1 slice in any rolling 10-slice window** has novel design tokens in `approach.md`, the tripwire fires and this ADR enters supersession review with Approach B as the first-class successor candidate.

This is NOT a full D2 assertion (D2 is scoped separately under cliff-failure-mode-and-v1-defenses). It is a **named canary** specific to this ADR's load-bearing belief. The canary is human-runnable during sweep until D2 promotes it to machine-checkable; when D2 lands, the canary migrates to D2's assertion runner.

**A2 — alternative framing**: if the tripwire never fires over 10 slices, A2 is operationally validated and this ADR's firmness is retroactively justified. If it fires early, the supersession is triggered before further downstream slice cost accumulates; the firm commitment made supersession visible rather than cheap.

- **Additional risk — the phase→skill mapping goes stale.** Superpowers skills evolve; skill files get renamed, deprecated, or restructured upstream. **Mitigation**: the mapping lives in `docs/operational-reference.md`, not in this ADR. Updates to the mapping are normal documentation commits and do not require ADR supersession. The ADR commits only to the registry's existence and to the surfacing mechanism, not to specific skill names.

- **Additional risk — the follow-up slice for D4 surfacing gets deprioritized.** F6 depends on the follow-up slice landing within two slices of phase-lock-and-role-declaration. **Mitigation**: the follow-up slice is named in Consequences as a pre-D1 slice and is a hard dependency for the `phase-lock-and-role-declaration` operationalization slice (D1) to inherit a surfacing mechanism. Delaying the follow-up slice delays the `phase-lock-and-role-declaration` operationalization slice and therefore delays D1 — a concrete operational cost that makes deprioritization visible.

- **Additional risk — the D3 `adrs-referenced` gate check surfaces as friction for cleanup slices.** Pure-implementation slices (refactors, cleanups, doc fixes) may have empty `adrs-referenced` fields; the gate must pass trivially. **Mitigation**: the D3 rule explicitly says "If `adrs-referenced` is empty, the gate passes trivially." The pre-D1 follow-up slice implements the gate with this semantics; its Phase 2 tests must cover both the non-empty and empty cases.
