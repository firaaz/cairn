# Phase 1 — Pre-Mortem: Step-3a fidelity-surface redesign

/decision arc `step3a-fidelity-surface`, opened 2026-06-01. Read-only phase. Premise: we SHIPPED a Step-3a redesign; it is 6 months later (≈2026-12); it FAILED. This is the failure landscape every approach (A predict-before-see / B cross-family challenger + declared-floor surface / C forcing-function on monolithic gate / D do-nothing/measure-first) must survive. No fixes here — Phase 2 owns those.

Grounding: L-028 (`docs/lessons.md:557`) ceiling-not-floor; `intent-contract-cost-model.md:97` ~60% same-family co-miss; `intent-management-loop.md` D2/D4/D7 (the loop, decorrelation residual, Trial-E gate); the three personas (`intent-challenge.md`, `intent-review.md`, `cairn-intent/SKILL.md:60` Step 3a).

Convention: each scenario gives **(1) title (2) narrative (3) mechanism (4) falsifiable observable (5) threatens which of A/B/C/D — and which it does NOT.** Lethality tag: APPROACH-KILLER / SEVERE / MODERATE.

---

## S1 — Relocation, not elimination: the rubber-stamp moves to the floor-elicitation prompt (deepens attack #1)

**Lethality: SEVERE (APPROACH-KILLER for A on its load-bearing claim).**

**Narrative.** Approach A elicits the operator's fidelity/floor criteria *before* revealing the contract ("what would make this wrong? what must this never do?"). For the first dozen intents the operator answers thoughtfully. By month 2 the latency driver that produced the original rubber-stamp is unchanged — the operator still has to wait for the fresh-context challenge round-trip *after* answering — so they learn to type a generic floor ("must not break existing tests; must match what I said") that satisfies the prompt's required fields without engaging the specific intent. Six months in, the pre-elicited floor is boilerplate; the challenger enforces the contract against a vacuous criterion and passes everything; intent-fidelity leaps ship green exactly as before, now with a "the operator pinned the floor" audit trail that *looks* stronger than the old monolithic gate.

**Mechanism.** A's whole thesis (brief :13, :31) is that predict-before-see "sidesteps the ~60% co-miss because the human supplies the floor." But eliciting a floor is itself a gate, and any gate the operator can satisfy without engagement gets satisfied without engagement under the same VOLUME+LATENCY pressure (`brief:10`) that the redesign was supposed to remove. The prompt moved the rubber-stamp from "approve the contract" to "type a floor"; the cheaper a generic answer is relative to a specific one, the faster it degrades. This is precisely L-005's pattern (prose-specified side-effects execute inconsistently under context pressure) applied to the operator instead of an agent.

**Observable.** Per-intent floor-criteria text: token entropy and edit-distance from a small set of stock phrasings trends toward boilerplate over the trial window; cross-intent cosine similarity of elicited floors rises toward 1.0. Defect-escape (post-close fidelity defects, `brief:21,40`) does NOT drop versus the pre-redesign baseline. Time-to-floor-answer collapses toward a few seconds.

**Threatens:** A (directly, kills its core claim). Partially B (its declared-floor *surface* can also be skimmed, but B's floor is the *challenger's* input per L-028, not the operator's, so the operator-side relocation does not apply — B's relocation risk is the surface-review skim, see S2). C is the explicit anti-relocation bet (forcing-function), so this scenario is the *test* C must pass, not a threat that assumes C failed. Does NOT threaten D (D ships no new operator prompt to relocate onto).

---

## S2 — Floor erosion survives because severity leaked back onto the user (deepens attack #2 / L-028)

**Lethality: APPROACH-KILLER (for any approach that puts a severity/floor field on the operator's review surface).**

**Narrative.** The redesign ships a "declared-floor surface": each clause carries a `severity: mandatory|advisory` line, rendered to the operator at Step 3a so floor-erosion becomes "a visible, objectable line" (L-028 corrective 2). In practice the operator now faces N severity tags to adjudicate on top of the contract. They do what humans do with a checklist of N booleans they can't independently verify: pattern-accept (everything that says `mandatory` looks right; everything `advisory` is "probably fine"). An agent that drafts a fidelity-eroding clause simply tags it `advisory` (or `mandatory` on a vacuous restatement), and the operator — who cannot tell a real floor from a drafted one — waves it through. The wrong-intent ships green with a severity field that *documents* the erosion rather than catching it.

**Mechanism.** L-028's load-bearing rule (`docs/lessons.md:561`, restated in `intent-contract-cost-model.md:84` and brief:16,38) is explicit: severity must be **the challenger's input, NEVER user review.** The instant severity renders on the operator's plate it inherits the original disease — a compressed object the human can't validate, now with more fields. "Declare the floor" was never "show the floor to the human"; it was "make the floor a machine/challenger-checkable artifact." Any design that surfaces severity to the operator has re-loaded the floor onto the party L-028 says can't carry it.

**Observable.** The Step-3a render contains per-clause severity tags. Operator severity-edit rate at the gate is near-zero (they accept the agent's tags). A planted fidelity-eroding clause tagged `advisory` is approved in a dogfood probe. Post-close, ≥1 shipped clause is found to have honored scope but under-delivered the floor (the L-028 "validator shall report a result" → log-and-exit-0 shape, `docs/lessons.md:563`).

**Threatens:** B if its "severity-tagged surface" is rendered to the operator (the brief's B description says "severity = challenger's input per L-028" — so a *correct* B is NOT threatened, but a B that drifts the tags onto the operator's screen is killed). C's "mandatory per-clause severity acknowledgment" variant (brief:33) is the **direct kill** — it explicitly asks the operator to acknowledge severity, which is exactly the prohibited move. Does NOT threaten A *if* A keeps the elicited floor as challenger input and never shows the agent's severity back. Does NOT threaten D.

---

## S3 — The single same-family challenger remains the sole floor guard and co-misses the class it exists to catch (deepens attack #3 / the ~60%)

**Lethality: APPROACH-KILLER (for A and any single-same-family design).**

**Narrative.** Both A and C lean on "challenger + a structural check enforce it" (brief:13,31) using the *existing* `intent-challenge` agent — a fresh-context but same-model-family subagent (`intent-management-loop.md` D4, `cairn-intent/SKILL.md:78`). Over 6 months the redesign's fidelity guarantee rests on this one agent. The Kim-et-al ~60% co-miss (`intent-contract-cost-model.md:97`) is not a tail risk — it is the *expected* behavior: on roughly six of ten genuine fidelity leaps, the same-family challenger reasons its way to the same wrong conclusion the drafting model did, because they share the blind spot. The operator, having delegated the floor to "the challenger will catch it," disengages further. The net system catches *fewer* fidelity leaps than the old monolithic gate, where at least an un-anchored human occasionally noticed something felt off.

**Mechanism.** A fresh *context* decorrelates context-bound errors (Song et al., `intent-management-loop.md` D4); it does NOT decorrelate *family*-bound semantic blind spots (Kim et al.). Fidelity leaps are exactly the family-bound class — the drafting model's misreading of the operator's intent is a semantic error the same family tends to reproduce. The brief's own steelman (`brief:13`) concedes "the only decorrelation-preserving compression is to elicit the operator's floor before revealing the contract" *because of* this co-miss — which means any approach still routing the floor through the same-family challenger has not escaped it; it has renamed it. `intent-challenge.md` is additionally **scoped to premise-truth**, not fidelity (`intent-challenge.md:13-19`, brief:20): a fidelity leap that isn't a source-citing `## Premise Grounding` claim is *out of its charter entirely* — so the co-miss number is optimistic; the real catch rate on non-premise fidelity leaps is near zero.

**Observable.** Run the Trial-E acceptance probe (`intent-management-loop.md` D9 — slice-#25 counterfactual + a fidelity-leap counterfactual that is NOT phrased as a premise). The same-family challenger passes the fidelity-leap counterfactual. Logged challenger verdicts show it rarely BLOCKs on anything outside `## Premise Grounding`. A cross-family re-run of the same intents catches leaps the same-family run missed (the decorrelation-gap signal `intent-management-loop.md` R2 names as the cross-family `/decision` trigger).

**Threatens:** A and C (both rely on the existing same-family challenger as the floor enforcer behind the operator's pinned/acknowledged criteria). B is the **named fallback** for exactly this (brief:32, `intent-contract-cost-model.md:98`) — so this scenario is the argument *for* B, not against it; it threatens B only if cross-family turns out to ALSO co-miss (see S7). Does NOT threaten D (D measures the co-miss rather than relying on a guard).

---

## S4 — Wrong-target metric: the redesign optimizes review-time and declares victory while defect-escape is flat or worse (deepens attack #4)

**Lethality: SEVERE (cross-cutting; it is how ALL of A/B/C ship a *failure* believing it a success).**

**Narrative.** The redesign is instrumented against the `slice-intent-contract.md:20` ">15min review = failure" metric (brief:21). After shipping, median Step-3a review time drops from (say) 8min to 90s — the surface is smaller / the floor-elicitation is quick. The team reads this as success: "rubber-stamping defeated, review is fast and engaged." Six months of slices later, a downstream consumer (the brief names complex-rag-analysis as a real consumer; CLAUDE.md cites its ~917s pytest) hits a cascade traceable to a fidelity leap that shipped green in month 2. The fast review time was not engagement — it was disengagement, which is *observationally identical* (brief:21). The metric rewarded the exact behavior it was meant to kill.

**Mechanism.** Fast approval and rubber-stamping produce the same telemetry (`brief:21`: "fast approval is observationally identical to disengagement"). `slice-intent-contract.md:20` declared >15min a *failure ceiling*; the redesign mistook the ceiling for a *success target* and drove toward it. The only signal that distinguishes engaged-fast from disengaged-fast is post-close fidelity-defect-escape (brief:21,40) — which has a long latency (the cliff mechanism, `cliff-failure-mode-and-v1-defenses.md:46-52`: violations compound silently across slices K..K+M before slice K+M+1 cascades). By the time defect-escape data exists, six months of slices are built on the eroded floor.

**Observable.** The redesign's success criteria reference review-time-under-threshold. Defect-escape is NOT tracked, or is tracked but flat/rising while review-time falls. The gap between "declared success" (month 1, on review-time) and "observed cascade" (month 6, on defect-escape) is the falsifier. `docs/dogfood-log.md` (currently 11 lines) records felt-cost/speed but no fidelity-defect-escape column.

**Threatens:** A, B, C (all three can be mis-validated on review-time; the danger scales with how aggressively each compresses — A and B compress, so they are most exposed; C explicitly does NOT compress (brief:33) and so is *less* exposed to "small surface = fast = good," but C can still be validated on its forcing-function's completion-time and mistake compliance-speed for engagement). D is the *defense* against this scenario (it is measure-first, `brief:34`) — but see S6: D fails a different way. Does NOT threaten D's design; D's risk is that it never produces an actionable result.

---

## S5 — Job mis-scoping strips the operator's irreducible externalities (deepens attack #5)

**Lethality: APPROACH-KILLER (for A specifically; SEVERE for B).**

**Narrative.** The operator's chosen frame (brief:12-13) defines the irreducible job as fidelity + value/scope and *excludes correctness* ("the human can't validate it; an AI wrote the code," `cliff-failure-mode-and-v1-defenses.md:48`). Approach A operationalizes this by eliciting fidelity/floor criteria and deriving the review surface from *that job only*. But the operator holds a class of knowledge neither the drafting model nor the context-blind challenger ever saw: domain facts, regulatory constraints, an externality from a meeting, "we promised customer X we'd never log Y." The redesigned surface, derived from the *enumerated* fidelity job, has no slot for "the thing the operator knows that nobody wrote down." Six months in, a slice ships a clause that is faithful-to-the-contract, passes the challenger, satisfies the pre-elicited floor — and violates a regulatory constraint the operator would have caught in the *old* full-contract read because seeing the whole thing jogged the externality. The compression that defeated rubber-stamping also amputated the operator's highest-value, least-formalizable contribution.

**Mechanism.** Premise-truth ≠ correctness ≠ domain-externality (brief:41). The challenger attacks premises-vs-cited-source (`intent-challenge.md:13`); it is *context-blind by construction* (`intent-challenge.md:7` "you have seen only the intent and the source it cites") so it can never hold an un-cited externality. The back-review is charter-blind to fidelity (`intent-review.md:15-22`, brief:19). If the operator-facing surface is *derived* from a pre-enumerated job, it structurally cannot surface the un-enumerated externality — and externalities are by definition un-enumerated. Predict-before-see makes this worse: pinning criteria *before* seeing the contract means the operator commits to a floor without the contract's content triggering the externality recall. The full-contract read was inefficient but had one virtue — breadth of trigger surface — that the redesign optimizes away.

**Observable.** A dogfood probe seeds an intent with a clause that violates an externality stated only verbally to the operator (never in any cited source). The redesigned surface does not surface it; the operator approves; the old full-read would have caught it (run both on the same seeded intent and compare). Post-ship, ≥1 fidelity defect is of the "operator knew, surface never asked" class.

**Threatens:** A (predict-before-see is the worst case — commits the operator before content can trigger recall). B (a challenger-assembled compressed surface also drops un-cited externalities; cross-family does not add externality-knowledge). C is the *least* threatened — it does NOT compress (brief:33), so the full contract is still in front of the operator; the forcing-function adds engagement *on top of* the breadth-of-trigger the full read preserves. Does NOT threaten C's design on this axis; does NOT threaten D (D keeps the current full-surface gate while measuring).

---

## S6 — NEW: Measure-first never converges; the deferral becomes permanent and the gate rots un-redesigned (the do-nothing trap)

**Lethality: APPROACH-KILLER (for D).**

**Narrative.** Approach D honors the deferral (brief:34, `intent-contract-cost-model.md` D3/D5 — heavy-band bundle gated on Trial E) and instruments the gap: operator pre-verdict vs gate/challenger catches, to *get* the Trial-E data redesign is gated on. Six months later the instrumentation has logged n=4 intents (the operator works on cairn intermittently; `MEMORY.md` and the dogfood-log's 11 lines show low throughput). Fidelity defects are rare *per intent* and have long latency (the cliff compounds silently, `cliff-failure-mode-and-v1-defenses.md:51`), so n=4 yields zero observed escapes — not because the gate is safe but because the sample is too small and too young. D's own honoring of "commit only what evidence supports" (brief:17,34) now *blocks* action indefinitely: there is never enough evidence, because the evidence-generating mechanism (real fidelity defects surfacing) is exactly what slow throughput + long latency suppresses. This is L-027 (`docs/lessons.md:545`) made real: adversarial rigor / evidentiary caution rationalizes the null action until deferral wins by default. The rubber-stamp problem the arc opened to fix is still live, now with a "we're measuring" fig leaf.

**Mechanism.** D's gate (Trial-E pass, `intent-management-loop.md` D7,D9) requires a *positive* fidelity-defect signal to justify redesign, but the failure mode is **silent and slow by construction** (the entire cliff thesis, `cliff-failure-mode-and-v1-defenses.md:42` — "several compound across many slices … human cannot audit each closely enough to catch the compounding"). You cannot measure-first your way to detecting a failure whose defining property is that it doesn't show up until many slices later. Low single-operator throughput (`MEMORY.md` feedback_shared_worktree_concurrency notes parallel sessions but still one operator) starves the sample. The deferral was gated on Trial E (n=1 at decision time, brief:17); D's promise to "get the data" runs into the fact that the data accrues slower than the decision-relevance window.

**Observable.** 6-month instrumentation sample size is in the single digits. Zero fidelity-escapes observed AND zero confidence the gate is safe (the two are confused). No redesign has shipped; the original rubber-stamp telemetry (fast approvals, `brief:10`) is unchanged. The Trial-E "pass/fail" verdict (`intent-management-loop.md` D7) remains unreached at month 6 — neither passed nor failed, just un-adjudicated.

**Threatens:** D (directly and uniquely — this is D's characteristic death). Does NOT threaten A/B/C (they act; their failures are S1-S5/S7, not paralysis). Note the pairing with S4: A/B/C risk *false-positive* success on review-time; D risks *never reaching a verdict at all*. The arc cannot escape both by picking one — it must answer both.

---

## S7 — NEW: Cross-family decorrelation degrades to a single point of failure (family-collapse + the unmeasured-second-family assumption)

**Lethality: APPROACH-KILLER (for B).**

**Narrative.** Approach B adds a cross-family challenger as the named fallback for the ~60% co-miss (brief:32, `intent-contract-cost-model.md:98`). It ships using model-family-2 as the decorrelating second opinion. Three failure paths converge over 6 months: **(a) Operational collapse** — family-2's API has an outage / gets deprecated / the org standardizes on family-1 for cost; the cross-family check silently falls back to same-family (or no-ops), and B is now S3 with extra machinery. **(b) Unmeasured decorrelation** — the ~60% number is a *family-1-vs-family-1* measurement (Kim et al., via `intent-contract-cost-model.md:97`); B *assumes* family-1-vs-family-2 co-misses *less*, but that delta is **unmeasured for cairn's fidelity-leap class**. If the two families share training-corpus blind spots on the specific semantic patterns cairn intents exercise, cross-family co-miss could be 50%+ too — B paid cross-family machinery cost (which the brief and `intent-contract-cost-model.md:93` warn must ship via the plugin-release path, no stale-`.slice-system` gaps) for an unverified decorrelation gain. **(c) Distribution rot** — a consumer on stale `.slice-system` wiring (`intent-management-loop.md` R1) runs B's surface as inert prose with the cross-family hook missing; enforcement is silently disabled (CLAUDE.md "Missing deps cause the hook to no-op … enforcement silently disabled").

**Mechanism.** B's value rests on an empirical claim it does not establish: that cross-family error-agreement is materially below same-family's ~60% *on cairn's fidelity-leap distribution specifically*. The repo names cross-family as the fallback but has never measured its co-miss rate (the ~60% is the same-family number; the cross-family rate is asserted-better, not shown). Meanwhile cross-family adds a hard runtime dependency on a second provider — a new availability/cost/distribution surface that the "cut before adding" ethos (brief:27) flags as a liability, and that L-018 (cited `intent-contract-cost-model.md:93`) warns becomes a silent-disable vector. B commits machinery against an unmeasured value — the exact failure `intent-contract-cost-model.md` Context (`:34`) and the Alternatives "Ship the full model now" rejection (`:104`) were written to avoid.

**Observable.** B's spec assumes family-2 availability with no same-family degradation path documented (or a degradation path that silently no-ops). No cairn-specific cross-family co-miss measurement exists in the repo (search the dogfood-log / skill-runs: the number cited is always the same-family ~60%). A seeded fidelity-leap probe run cross-family still co-misses at a rate not statistically distinguishable from same-family. A stale-`.slice-system` consumer shows the cross-family check absent at runtime.

**Threatens:** B (directly and uniquely — its core mechanism). Does NOT threaten A (A's decorrelation is the *operator*, not a second family — though A inherits S3 if it leans on the same-family challenger behind the operator). Does NOT threaten C (no second family). Does NOT threaten D (no new family). This is the mirror of S3: S3 kills the *single-same-family* approaches; S7 kills the *cross-family* approach — together they squeeze the design toward "the operator is the decorrelating source," i.e., toward A — which S1/S5 then attack. There is no free decorrelation.

---

## S8 — NEW: INV-003 / governance failure — the redesign needed a firm supersession it didn't get, and the Step-3a change is an orphan (integration with the ADR corpus)

**Lethality: SEVERE (procedural; can retroactively invalidate the whole redesign regardless of mechanism).**

**Narrative.** The redesign ships as a provisional ADR (or a skill edit) that modifies cairn-intent Step 3a. The brief's open question (brief:25) — does INV-003's four-phase lock bind the *cairn-intent* loop? — was resolved as "no, INV-003 only binds cairn-tdd-feature" and the team proceeded on that reading. Six months later an integration sweep (or a downstream `/decision`) discovers that the Step-3a change *did* interact with a firm commitment: it altered the `human_signoff_after: true` contract (`workflows/cairn-intent.yaml:115`) and the `intent-management-loop` D2 "approval is delta-triggered" / D7 "retirement is a future firm supersession" decisions in a way that needed a *firm* superseding ADR with Phase-5 verification — not a provisional one. The redesign is now an L-029 orphan (`docs/lessons.md:569`): a firm ADR's section describes a Step-3a gate that no longer exists, the validator passes (it checks reference-existence, not body-vs-reality, `docs/lessons.md:571`), and a reader reconstructs the wrong model. Worse, because `intent-contract-cost-model` D3/D5 deferred the heavy-band bundle *gated on Trial E*, shipping the redesign *before* Trial E adjudicates is a supersession-by-stealth of that deferral (brief:17 "acting now = superseding this deferral on n=1 Trial-E data") that was never recorded as a supersession.

**Mechanism.** Provisional ADRs skip Phase-5 independent verification (`decision.full` / `intent-management-loop.md:18-20`). If the Step-3a change is decision-weight (it alters a human-approval contract that firm ADRs reference), the missing Phase-5 means the inherited-error class (L-007, `docs/lessons.md:120`) and the orphan class (L-029) both go uncaught. The four ADRs/decisions in tension — `intent-management-loop` D2/D7, `intent-contract-cost-model` D3/D5, `slice-intent-contract`, and the `human_signoff_after` workflow contract — form a web; touching Step 3a without sweeping the web is the partial-retirement pattern L-029 names (`docs/lessons.md:575`). MEMORY.md `feedback_designs_through_decision` is explicit: decision-weight architectural changes (supersession/cross-cutting) invoke /decision, not a skill edit — and this *is* the /decision, but if it lands provisional it dodges the firm-supersession discipline the change actually needs.

**Observable.** The shipped ADR is `firmness: provisional` (no Phase-5) while touching a `human_signoff_after` contract that firm ADRs reference. A later sweep finds a firm ADR section describing the old monolithic Step-3a gate. The `intent-contract-cost-model` D3 deferral is neither superseded nor satisfied-via-Trial-E in the corpus, yet the heavy-band-adjacent machinery shipped. `validate_architecture` passes while the ADR bodies contradict the live skill.

**Threatens:** A, B (both add machinery/fields = larger ADR surface = more firm-decision interactions = more orphan risk; both are heavy-band-bundle-adjacent, so both most directly collide with the `intent-contract-cost-model` D3 deferral). C if its forcing-function alters the `human_signoff_after` contract semantics. Does NOT threaten D *on this axis* — D ships no Step-3a mechanism change, so it creates no orphan and triggers no firm-supersession need (D's failure is S6, not S8). This is the one scenario where D is structurally safest.

---

## S9 — NEW: Scale — the surface degrades into a pid-taxonomy / per-clause grind across many clauses and many slices (deepens the brief's quadratic constraint)

**Lethality: MODERATE→SEVERE (scales with adoption; APPROACH-KILLER for C's per-clause variants at the high end).**

**Narrative.** The redesign works on the light/medium intents used during the trial (the cost-model m2 one-liner, `templates/intent.md:158`). Six months and many slices later, a genuinely heavy intent arrives — 30+ clauses (`intent-contract-cost-model.md:90` "single-pass fidelity challenge skims at 30+ clauses"). Approach C's per-clause active recall / per-clause severity acknowledgment now demands the operator perform a recall ritual or severity tap *per clause*, 30+ times. The operator's engagement budget is finite; by clause 8 they are pattern-tapping, and the forcing-function has become the new rubber-stamp at scale (S1 reborn under volume). For A, the pre-elicited floor cannot anticipate 30 clauses' worth of failure modes, so the elicited criteria under-cover the contract and the challenger enforces a floor that is sparse relative to the surface. The traceability check (L-028 corrective 1) is O(criteria × clauses) and the same-family challenger skims — both degrade exactly where the contract is heaviest and the stakes are highest. This is `intent-contract-cost-model.md:89-90` constraint 3 (quadratic-at-scale) plus constraint 2 (band-must-be-derived) coming due: "one promise you approve must not degrade into a pid-taxonomy."

**Mechanism.** Every per-clause operator action is O(clauses); human engagement per item decays as item-count rises (the volume driver, brief:10, is *worse* at 30 clauses than at the 3-clause intents the design was tuned on). A single-pass same-family challenger's catch rate degrades with clause count (`intent-contract-cost-model.md:90`). The redesign was validated on light intents (Trial-E throughput is low, S6) so the heavy-intent failure mode is *structurally under-sampled at design time* — it only appears once a heavy real intent runs, which by month 6 it finally does. The deferred-constraint warning (`intent-contract-cost-model.md:89`) was recorded but, being deferred, was not built against.

**Observable.** On the first 30+-clause intent: operator per-clause action time decays monotonically across the clause list (engagement curve); challenger BLOCK-rate per clause drops past ~clause 10; defect-escape concentrates in the back half of long contracts. Elicited-floor coverage (A) — fraction of shipped clauses whose failure mode the pre-elicited criteria actually named — is low on heavy intents.

**Threatens:** C (per-clause variants — directly; the forcing-function's cost is linear in clauses and so is its decay). A (pre-elicited floor under-covers a large contract). B less so for the *operator* (B's surface is challenger-assembled, not per-clause-operator-driven) but B's single-pass challenger still skims at 30+ clauses (`intent-contract-cost-model.md:90`). Does NOT threaten D (D adds no per-clause operator burden; it keeps the current gate).

---

## S10 — NEW: Amendment / re-challenge interaction — mid-construction intent drift bypasses the new fidelity surface entirely (integration with the loop)

**Lethality: SEVERE (it is a hole the redesign doesn't cover, regardless of how good the front gate is).**

**Narrative.** The redesign hardens Step 3a — the *front* sign-off. But the cairn-intent loop is delta-triggered (`intent-management-loop.md` D2, `cairn-intent/SKILL.md:53,62`): mid-construction, a `must-satisfy` clause changes materially and the loop is *supposed* to re-fire the front intent-challenge. Six months in, the operator approves a clean intent at the hardened Step 3a, construction begins, and three hours later the intent drifts (a clause is edited to accommodate a discovered constraint). The re-challenge *should* re-run the new fidelity surface — but (a) the operator, deep in fluid construction (`SKILL.md:62`), edits the clause inline and keeps going without re-triggering, because the delta-trigger is prose-specified ("return to Step 3 and re-challenge," `SKILL.md:62`) and prose-specified side-effects skip under context pressure (L-005, `docs/lessons.md:96`); or (b) the re-fire runs but the operator, mid-flow and hours past the original framing, rubber-stamps the *re*-approval even harder than the first (the `## Operator Prompt` verbatim-pin, `templates/intent.md:24-31`, was the gh#28 mitigation for exactly this cold-read-anchor problem — and it addresses framing recall, not engagement). Either way the fidelity leap enters *via the amendment path*, downstream of the redesigned front gate, and the back close-review is charter-blind to fidelity (`intent-review.md:15-22`). The redesign hardened the front door; the leak came through the window.

**Mechanism.** The redesign's scope is Step 3a (the *initial* approval). The loop has *two* approval moments (initial + delta-re-fire, `SKILL.md:53,62`) and the delta-re-fire is the weaker one — it fires mid-flow, prose-triggered, hours past peak framing context. Predict-before-see (A) is *especially* vulnerable: the pre-elicited floor was pinned against the *original* intent at *original* peak context; a mid-construction clause edit invalidates the pinned floor, but A has no defined re-elicitation ritual (the brief's A description, brief:31, is silent on amendment). The close-review (`intent-review.md`) cannot recover it (it checks diff-against-contract, and the *contract itself* drifted, so a faithful diff of the drifted contract passes — brief:19). Handoff across sessions (`SKILL.md:72`, `.claude/handoff.md`) compounds it: an intent amended in session 1 is resumed in session 2 as a "plain resume" that *skips the challenge entirely* (`SKILL.md:29,53`).

**Observable.** Dogfood probe: approve a clean intent through the new surface, then materially edit a `must-satisfy` clause mid-construction. Measure whether the new fidelity surface re-fires AND whether the operator engages the re-fire as hard as the initial. Re-fire skip-rate > 0; re-fire engagement < initial engagement. A's pinned floor is not re-elicited after the clause edit. A resumed-in-next-session amended intent shows the challenge was skipped (`delta_kind: resume`).

**Threatens:** A (no re-elicitation ritual for the pinned floor — the predict-before-see anchor goes stale on amendment, the most acute case). B and C (their hardened surface is initial-scoped; the delta-re-fire is the prose-triggered weak path for both). Does NOT threaten D (D changes nothing about the loop's amendment handling — it inherits the *existing* re-challenge behavior rather than adding a front-gate the amendment can bypass; D's problem is S6, not this).

---

## Lethality ranking (most → least lethal)

| # | Title | Lethality | APPROACH-KILLER for |
|---|---|---|---|
| S2 | Severity leaked back onto the user | APPROACH-KILLER | C (severity-ack variant) + any A/B that renders severity to operator |
| S3 | Single same-family challenger co-misses its own class | APPROACH-KILLER | A, C |
| S7 | Cross-family decorrelation collapses / is unmeasured | APPROACH-KILLER | B |
| S5 | Job mis-scoping strips operator externalities | APPROACH-KILLER | A (SEVERE for B) |
| S6 | Measure-first never converges (do-nothing trap) | APPROACH-KILLER | D |
| S1 | Rubber-stamp relocates to floor-elicitation | SEVERE (kills A's core claim) | A |
| S8 | Missing firm supersession → ADR orphan | SEVERE | (procedural; threatens A/B/C, not D) |
| S10 | Amendment/re-challenge bypasses the front surface | SEVERE | (hole in A/B/C; A most acute) |
| S4 | Wrong-target metric (review-time vs defect-escape) | SEVERE | (mis-validates A/B/C as success) |
| S9 | Scale: per-clause grind / pid-taxonomy at 30+ clauses | MODERATE→SEVERE | C (high end), A (coverage) |

## Cross-cutting structural finding (the squeeze)

The decorrelation scenarios form a **trilemma no single mechanism escapes**:
- **S3 kills single-same-family** (A, C behind the same-family challenger).
- **S7 kills cross-family** (B).
- → both squeeze the design toward "**the operator is the decorrelating source**" (A's predict-before-see).
- **But S1 (operator-floor relocates the rubber-stamp), S5 (operator surface strips externalities), and S10 (operator floor goes stale on amendment) attack exactly that.**

There is no free decorrelation source. Any approach that names a *single* decorrelation guard — operator OR same-family OR cross-family — has a named scenario that kills it alone. The surviving design space is either (i) layered/redundant decorrelation (operator AND a family-decorrelated challenger, accepting cost) or (ii) D's honest "measure the co-miss before betting" — which S6 shows rots into permanent deferral. **Phase 2's hardest job is not picking a mechanism; it is escaping this squeeze without either betting on one unverified decorrelation source (S1/S3/S5/S7) or deferring forever (S6).**

Two metric/governance scenarios sit underneath all of the above and would let a *failed* redesign masquerade as a success or an orphan: **S4** (review-time is observationally identical to disengagement — any approach validated on it ships a failure believing it a win) and **S8** (a provisional ADR touching a `human_signoff_after` contract that firm ADRs reference is an orphan-in-waiting). Both must be answered by *every* approach, including D.
