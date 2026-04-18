---
id: cliff-failure-mode-and-v1-defenses
status: accepted
firmness: provisional
supersedes: []
supersedes-sections: []
superseded-by: null
topic: scope
invariants-touched: []
date: 2026-04-11
---

# cliff-failure-mode-and-v1-defenses: Target Failure Mode and v1 Defense Commitments

## Status
Accepted

## Date
2026-04-11

## Context

Cairn exists to close gaps in Spec-Driven Development for AI-managed codebases. `docs/spec-v1.md` §13 enumerates nine failure modes cairn claims to defend against but does not name a *primary* target or rank the defenses. Without a named primary, MVP scoping degenerates into "implement everything" — which is what the current roadmap reflects (ten pre-v1 items, all plausibly necessary, none explicitly load-bearing).

This ADR names the primary target failure mode, commits to three candidate defenses expected to be load-bearing for v1, and time-boxes everything else to post-v1. The goal is a single legibility criterion for every subsequent pre-v1 slice: *does this contribute to D1, D2, or D3? If not, it is deferred to v2.*

### The primary target — the medium-scale AI-managed cliff

A discontinuous failure mode in codebases of roughly 50 files, 5k lines of code, and 6 months of AI-heavy development, where the project crosses a threshold after which further progress requires a mental model no human has — because no human read the code. Failure manifests as unpredictable breakage on further changes: each change is locally correct, but compound drift has silently eroded global properties that were never explicitly invariants.

**The 50-files / 5k-LOC / 6-months threshold is an intuition, not an empirical finding.** It is named here to make the target concrete enough to falsify, not because cairn has measured it. Dogfood may demonstrate the real threshold is different; that is an acceptable outcome and a supersession trigger.

"Cliff" is load-bearing terminology: the failure is discontinuous, not gradual. The project works, works, works, then crosses a threshold and stops working in ways that cannot be reasoned about from the current state alone. The threshold is the point at which the human-held mental model falls below the complexity the codebase actually has.

This failure mode is NOT named in spec-v1. It is the superordinate failure into which spec-v1 §13's nine enumerated failures compose:

- authorship contamination, interpretation drift, ceremony fatigue (§13 items 1–3) erode phase discipline, which erodes the quality of individual slices;
- routing mistakes (§13 item 4) and cross-slice integration failures (§13 item 5) erode global consistency across slices;
- ADR corpus semantic drift (§13 item 6) erodes the cached mind itself;
- hook bypass (§13 item 7), Phase 4 death spirals (§13 item 8), and AI-test blind spots (§13 item 9) erode the verification layer.

Any single §13 item is survivable in isolation. The cliff is what happens when several compound across many slices in a codebase whose authors are AI agents with correlated blind spots, and whose human maintainer cannot audit each slice closely enough to catch the compounding.

### Concrete mechanism

1. Slices 1..N each pass their 4-phase gate. Each change is locally correct.
2. `/refresh-architecture` is manual; it gets skipped under load. `docs/ARCHITECTURE.md` goes stale relative to the ADR corpus.
3. Integration-sweep Step 2 (adversarial enumeration of failure modes) is human-driven. It degrades to rubber-stamping when the human does not know the code — and the human does not know the code, because an AI wrote most of it.
4. A property that *should* be an invariant is never named, so no hook or validator check enforces it.
5. Slice K silently violates the unnamed property. Its tests pass, scope-guard passes, integration-sweep misses it (the property is not in the named invariant set).
6. Slices K+1..K+M compound the violation. Each is locally correct because the violated property was never a commitment.
7. Slice K+M+1 requires the violated property to hold. Breakage cascades.

Cairn's working hypothesis is that this failure mode is preventable by combining three properties no single SDD framework currently ships together: (a) enforced phase discipline, (b) live machine-readable architecture, (c) machine-checkable invariants as first-class artifacts. The 2026-04-11 framework review (see the session-1 framework matrix in `docs/plans/2026-04-11-substrate-and-framework-exploration-notes.md` once promoted) found no framework combining all three, but this is a point-in-time snapshot, not a standing claim.

### Honest limits

Cairn is currently two slices deep (the `validator-symlink-fix` slice shipped, the `context-discipline-protocol` operationalization slice stopped). The cliff has not been operationally observed in cairn itself. The target is theoretically grounded and derived from first-principles analysis of the failure mechanism above, but is not yet empirically validated in cairn. This ADR is therefore provisional and explicitly expects revalidation against the first dogfood cycle.

The `firmness: provisional` choice is load-bearing. It keeps the door open to reframing if dogfood evidence disagrees with the theoretical analysis, while still committing enough to give v1 a narrow, legible scope. spec-v1 §17 names this calibration gap explicitly; this ADR inherits that honesty.

Provisional firmness is cheap ceremonially but not cheap downstream: every slice that lands depending on D1/D2/D3 becomes churn cost if the defenses are superseded. The dogfood cycle is therefore gated to complete *before* any slice beyond D1/D2/D3's own design slices takes a hard dependency on the defenses. See the risk register and the supersession path below.

## Decision

Cairn commits to the following six claims.

### D0 — Naming the target

The medium-scale AI-managed cliff is cairn's primary target failure mode. spec-v1 §13's nine enumerated failure modes remain; they are not re-ranked as parallel targets but recognized as *components* of the cliff. Any future failure-mode amendment to spec-v1 §13 must state its relationship to the cliff (aggravator, component, or orthogonal).

### D1 — Automated architecture refresh

`docs/ARCHITECTURE.md` must not drift from the ADR corpus. Specifically:

- A post-slice hook fires `/refresh-architecture` automatically on slice-close.
- Slice-close gates on `scripts/validate_architecture.py` passing — a slice cannot be marked `complete` if the refresh produces a validation failure.
- The drift window between ADR write and architecture sync is zero.

**D1 session-boundary contract.** `/refresh-architecture` reads the full ADR corpus into main context and therefore cannot run inside any phase session without violating context-discipline-protocol's session-isolation guarantee (Phase 4's auditor role would pollute with design-context reads, Phase 1's reader role would see downstream consequences, etc.). D1's post-slice hook therefore runs in a **dedicated refresh session** spawned after Phase 4 commits land and the slice is about to transition to `status: complete`. This session has no phase role and loads only the ADR corpus plus the prior `ARCHITECTURE.md`; it does not load slice artifacts. The commit it produces is a **pipeline-substrate commit** in the same class as integration-sweep commits per `docs/lessons.md` L-001 — a deliberate, named scar that is not a slice-phase commit and not a decision commit, but is authorized as pipeline substrate. INV-001 is honored by naming this class explicitly rather than via a quiet exception.

**D1 escape hatch.** If a validator failure is a known false positive (typically: a semantic equivalence the parser cannot see, or a transient failure in the check script itself), the developer may close the slice with an `ADR_D1_BYPASS=1` environment variable on the slice-close command, following the `ADR_EDITORIAL_FIX=1` precedent in `checks/reversibility-guard.sh`. Each bypass is logged to `.claude/d1-bypasses.log` with the bypassing slice ID and a one-line reason; a third bypass in a rolling 10-slice window is itself a trigger to revisit D1's design (the check is producing more noise than signal).

D1 closes the stale-cached-mind gap identified in step 2 of the cliff mechanism.

### D2 — Code↔invariant binding

Invariants must have machine-checkable assertions, not just markdown cross-references to ADRs. Specifically:

- Every firm invariant in `docs/ARCHITECTURE.md` carries an assertion mechanism: AST-level check, schema-level check, or strict-grep with explicit anchoring rules. Purely descriptive invariants are not permitted at firm status.
- `scripts/validate_architecture.py` (or a successor) runs the assertions as part of each refresh, flagging code that violates a declared invariant.
- Invariants that cannot be machine-checked at introduction time are marked `firmness: advisory` and do NOT count toward v1 defense commitment satisfaction. Advisory invariants are preserved as future-intent signals; they do not provide cliff-prevention.

D2's design-slice scope includes specifying the assertion-storage location (ADR frontmatter, separate registry, or validator code), the assertion language, and the migration path for INV-001 and INV-002 (which currently have no machine-checkable form). These are deliberately deferred out of this ADR.

D2 closes the "invariants as commentary" gap identified in step 4 of the cliff mechanism.

### D3 — Automated unknown-unknown backstop

At least one automated check must exist beyond integration-sweep Step 2's human adversarial enumeration. The starting substrate already exists: `commands/claude-code/integration-sweep.md` Step 3 (check each invariant against source with file:line evidence, currently manual) and Step 4 (import integrity, lint, type, test, schema, currently manual-triggered). D3 is therefore not "invent a new backstop" but "promote the existing Step 3 and Step 4 checks from manual to mechanically-gating and extend them with at least one structural-diff check."

Specifically:

- Step 3's manual invariant check becomes D2's assertion runner — D2 and D3 partially overlap here by design.
- Step 4's cross-module checks become mandatory gates, not optional invocations.
- A new structural-snapshot-diff check: per-file imports/type shapes/schema dependencies are snapshotted at slice-land; the next sweep diffs against the prior snapshot; files whose shape changed without being listed in the slice envelope are flagged. Minimum acceptable form; design-slice refines it.

**D3 falsification test.** D3's design slice must define a known case the check MUST catch — a concrete planted violation that, if the check does not flag, causes D3 to be rejected at design-slice Phase 4. The falsification test is the mitigation for S6 (disarmed defense) in the risk register: a defense that exists but catches nothing is worse than an absent defense because it produces false confidence, so D3 is not accepted without a pre-specified calibration case.

D3 closes the "human Step 2 degrades on AI-written code" gap identified in step 3 of the cliff mechanism.

### D4 — Time-boxed v1 scope

v1 ships with D0/D1/D2/D3 dogfood-validated. The following vision.md commitments and their corresponding v1 success criteria are **time-boxed to v2**, not deferred indefinitely:

- **Vision commitment #1 (full agent portability — Windsurf)** including the success criteria "At least one slice has run end-to-end on Windsurf alone" and "At least one slice has run split mid-flight across both agents." v1 ships on Claude Code only. v2 re-opens the Windsurf port.
- **Vision commitment #2 (parallelism-native)** including the success criterion "Two concurrent slices have completed on separate worktrees without interference." v1 ships with single-slice discipline. v2 re-opens parallelism.
- **Spec-v1 §9 (three-track routing)** remains deferred; work-type routing is a v2+ concern.
- **Mechanized role assignment per phase (commitment #6 mechanization)** remains deferred; roles stay instructed in protocol text, not hook-enforced. v2 re-opens mechanization.
- **Retroactive invariant enforcement against existing code** — v2+.
- **Slice pause/resume as a built-in command** — v2+.
- **Cached-mind size management / `ARCHITECTURE.md` chunking** — v2+.

**Commitment #5 (plastic phases) is NOT in the time-box.** The phase rethink is orthogonal to the cliff framing and lands on its own timeline as a standalone ADR (see exploration-notes 5-phase proposal). It remains on the v1 critical path because the phase shape determines where D1/D2/D3 hook into the pipeline.

Vision commitments are preserved as v2+ goals. This ADR does not renounce them; it time-boxes them. Any pre-v1 slice that touches a time-boxed area must declare in `intent.md` that it is doing so under explicit non-v1-scope waiver, or be rejected.

This ADR functions as a targeted supersession of the listed vision.md §Success criteria lines for v1 scope purposes only. The vision.md lines themselves are not edited — the supersession is recorded here and will be propagated at the next `/refresh-architecture`.

### Supersession path and dogfood commitment

This ADR is `firmness: provisional`. It will be reassessed after the first dogfood cycle of v1 cairn.

**Dogfood target.** The dogfood is cairn dogfooding itself against its own development: the target is **cairn reaching 10 completed slices post-cliff-failure-mode-and-v1-defenses land, OR by 2026-10-11 (six months after this ADR), whichever comes first.** Ten slices is the minimum sample size that can exhibit compound-drift behavior; six months is the hard deadline. If neither threshold is reachable by the deadline, that itself is the dogfood signal — the process is too heavy to operate at the intended scale, and the ADR is superseded by a lighter reframing.

**Dogfood evidence shape.** Dogfood passes if D1/D2/D3 together catch **at least one class of drift** that integration-sweep Step 3's manual check would have missed in the same 10-slice window, AND no D1/D2/D3 false-positive rate is high enough that a check is muted by disabling it. Dogfood fails if either condition is violated. The D1 design slice is responsible for instrumenting the dogfood measurement; cliff-failure-mode-and-v1-defenses commits to the criterion, not the instrumentation.

Three supersession outcomes are permitted:

- **Promote.** D1/D2/D3 demonstrably catch cliff-shape failures and the false-positive rate is acceptable. A successor ADR promotes this ADR to firm.
- **Amend.** D1/D2/D3 prove individually insufficient or individually correct; a successor ADR adds, removes, or replaces specific defenses based on dogfood evidence.
- **Reframe.** The cliff framing itself fails to match observed failures; a successor ADR names a different primary target.

All three paths are acceptable. None is failure. Supersession is the plan.

## Consequences

- **v1 scope shrinks from ~10 open roadmap items to three load-bearing ones.** Each of D1/D2/D3 is dogfoodable in a single slice pipeline. Every pre-v1 slice after this ADR lands must declare in `intent.md` which of D0/D1/D2/D3 it implements, or mark itself as non-v1-scope waiver.

- **Every subsequent pre-v1 slice has a legibility criterion.** The question "does this contribute to D1, D2, or D3?" must be answered before work begins. Non-contributing work is time-boxed to v2 without apology.

- **spec-v1 §13 is amended at the next refresh.** The nine enumerated failure modes remain, with a new preamble identifying the cliff as the superordinate failure they compose into. The amendment is editorial — no existing failure mode is removed or re-ranked.

- **vision.md §Success criteria is targeted-superseded for v1 scope.** The specific lines listed in D4 are superseded for v1 purposes; they return as v2 scope. The vision document itself is not edited; this ADR is the authoritative record of the supersession.

- **The stopped the `context-discipline-protocol` operationalization slice must be reviewed against this ADR before resuming.** the `context-discipline-protocol` operationalization slice's envelope is currently tied to the rewrite of `handoff.md` and `catchup.md` for INV-002 compliance. The review question is: does the `context-discipline-protocol` operationalization slice's envelope contribute to D1/D2/D3, or does the envelope need amendment? The review outcome is recorded either in a successor ADR or in an amendment to the `context-discipline-protocol` operationalization slice's `stopped-reason` field in `slice.yaml`.

- **D1 interacts with context-discipline-protocol's session-isolation guarantee.** D1 is constrained to not pollute any phase session. The dedicated-refresh-session mechanism named in D1 above honors context-discipline-protocol; D1's design slice inherits this constraint and must verify the refresh session is spawned as specified.

- **D1 commits are pipeline-substrate.** Per L-001, integration-sweep commits are not slice-phase commits and not decision commits, but are named as pipeline substrate. D1 auto-commits inherit the same class. INV-001 is honored by naming the class, not by creating a quiet exception.

- **Team-rollout legibility is secured.** When cairn is introduced to teammates during the personal-to-team transition, the cliff framing provides the problem statement that makes cairn legible. Without this ADR, cairn is a set of disciplines without a named target; with it, the target is explicit, the scope is narrow, and the vision's missing items are explicitly time-boxed (not quietly dropped).

- **Provisional firmness means this ADR is expected to be superseded.** The supersession is part of the plan, not a failure mode. After dogfood cycle 1, one of promote / amend / reframe lands; all three are planned outcomes and all three are acceptable.

## Alternatives Considered

**Name a different target failure mode.** Candidates considered: "SDD phase discipline decay" (too narrow — ignores invariant rot), "AI-code review degradation" (too narrow — ignores architecture drift), "general software entropy" (too broad — already addressed by conventional architecture tools at scales cairn does not target). The medium-scale AI-managed cliff is the narrowest target that covers the observed combinatorial failure while remaining specific enough to rule out solutions. Rejected alternatives are either too narrow to justify cairn's three-way defense combination or too broad to provide scoping criteria.

**Split target-naming and defense commitments into two ADRs.** Considered during `/decision` stress test. cliff-failure-mode-and-v1-defenses would name only the cliff (D0); a separate phase-lock-and-role-declaration would carry D1/D2/D3/D4. Clean supersession isolation and independent firmness (target firm, defenses provisional) are the upsides. Rejected because the cliff framing's durability is ultimately dogfood-dependent — independent firmness on D0 would overstate confidence. Single-ADR provisional firmness is more honest and halves the `/decision` cost.

**Target-only, no defense commitments yet.** Considered during `/decision` stress test. cliff-failure-mode-and-v1-defenses would name only the cliff; D1/D2/D3 would be held as candidate defenses in working documents, committed only after dogfood. Safer epistemically — honors spec-v1 §17 calibration gap more strictly — and eliminates premature-defense-commitment failure scenarios. Rejected because the scoping problem this ADR exists to solve remains unsolved: pre-v1 slices still need a legibility criterion, and "we'll figure it out after dogfood" offers none. Indefinite delay is itself a failure mode.

**Commit to more than three defenses.** Adding D5 (parallel slices), D6 (work-type routing), D7 (role mechanization), etc. was considered. Rejected because each additional defense roughly doubles the v1 scope without closing the three specific gaps in the cliff mechanism. Parallel slices, work-type routing, and role mechanization all address *velocity* and *usability*, not *cliff prevention*. They are time-boxed to v2+ via D4 and preserved in the roadmap.

**Commit to firm ADR with immediate v1 release.** Rejected because cairn has not been operated at medium scale and the target failure mode has not been empirically observed in cairn itself. A firm commitment without empirical grounding would mask the "theoretical until validated" gap and remove the expected-supersession hedge. The provisional framing is honest about the calibration gap spec-v1 §17 names; a firm framing would not be.

**Defer the target-naming until after the `context-discipline-protocol` operationalization slice resumes and more slices land.** Rejected because the absence of a named primary target is precisely what prevents MVP scoping. the `context-discipline-protocol` operationalization slice itself is currently stopped pending substrate decisions, and the substrate question is downstream of "what is v1 actually committed to building." Naming the target first unblocks everything downstream; deferring it extends the stopped state indefinitely.

**Treat the cliff framing as working notes, not an ADR.** Rejected because the cliff framing is the load-bearing justification for every Tier 1 MVP item. If the framing lives only in working notes, it is a convention — any future slice that touches the working notes can silently revise it. ADR firmness forces supersession for any change, which is the exact property needed for a target-naming commitment.

## Risk Register

- **Risk:** The cliff framing fails to match the failure modes observed in dogfood. The theoretical analysis may be wrong. **Mitigation:** `firmness: provisional` keeps the reframing path open. The supersession clause names "reframe" as an acceptable outcome. If dogfood reveals a different failure mode, the ADR is superseded rather than silently ignored.

- **Risk:** D1 gates on *file shape* rather than *mental-model update*. ARCHITECTURE.md refreshes automatically; the human rubber-stamps the diff; drift moves from disk to cognition and the cliff forms anyway, slightly later. **Mitigation:** named but not closed at the ADR level — the D1 design slice must address cognitive-update surfacing (e.g., a diff summary the human is forced to acknowledge). This risk is the reason D1 is provisional, not firm.

- **Risk:** D2 degrades at scale. At ~18 firm invariants the validation cost becomes noticeable; false positives accumulate when code is refactored; the developer adds exceptions; D2 decays into an advisory-tier dumping ground. **Mitigation:** D2's design slice must specify a per-invariant runtime budget and an exception-count ceiling; exceeding either triggers a D2 review rather than silent decay.

- **Risk:** D3 ships without calibration and gets muted (S6 in `/decision` pre-mortem). A disarmed defense is worse than an absent one because it produces false confidence. **Mitigation:** D3's design slice must define a falsification test (one known case D3 must catch) as a Phase 4 gate. Unchecked-by-planted-violation D3 is rejected at design-slice acceptance.

- **Risk:** Provisional firmness is cheap ceremonially but expensive in downstream-slice churn. If a defense is superseded after 5 slices build on it, the real cost is those 5 slices, not the ADR rewrite. **Mitigation:** the dogfood cycle must complete before any slice beyond D1/D2/D3's own design slices takes a hard dependency on the defenses. Slices between dogfood start and dogfood completion are either D1/D2/D3 design slices themselves or non-v1-scope waiver slices.

- **Risk:** The explicit deferral list produces resistance from teammates during rollout because it reads as abandoning vision commitments. **Mitigation:** D4 time-boxes rather than deferring indefinitely; team-rollout documentation leads with the target (cliff) before the deferrals, so the time-box lands as scoping discipline rather than retreat.

- **Risk:** Dogfood is inconclusive — neither clearly catching nor clearly missing cliff failures, or the 10-slice / 6-month target is not reached on time. **Mitigation:** the dogfood evidence shape in the supersession path is deliberately binary (catch ≥1 class, false-positive rate not mute-triggering). The "threshold not reached" case is explicitly named as a dogfood signal (the process is too heavy).

- **Risk:** The cliff framing gets read as "cairn's one true problem," flattening the space of legitimate adjacent problems cairn could address later. **Mitigation:** the failure-mode enumeration in spec-v1 §13 is preserved — this ADR amends the preamble, not the list. Other cairn applications remain legitimate post-v1; this ADR only governs v1 scoping.

- **Risk:** The 50-files / 5k-LOC / 6-months threshold is wrong and cairn targets a non-problem or misses the real problem. **Mitigation:** the threshold is explicitly marked as intuition, not empirical. Dogfood against cairn itself will surface whether the threshold is roughly right; a significant miss is a reframe trigger.

- **Risk:** D1's dedicated-refresh-session mechanism violates context-discipline-protocol in some subtle way not caught at design time (e.g., the hook inherits environment variables that leak phase context). **Mitigation:** the D1 design slice must explicitly verify context-discipline-protocol compliance at Phase 4, with a named test that checks refresh-session isolation.
