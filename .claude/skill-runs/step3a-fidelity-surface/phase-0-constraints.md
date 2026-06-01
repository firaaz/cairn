# Phase 0 — Constraint Envelope: Step 3a operator-gate redesign (defeat rubber-stamping)

`/decision` arc `step3a-fidelity-surface`, opened 2026-06-01. Read-only constraint harvest.
Companion: `_brief.md` (decision context). Every hard constraint this decision must honor is
listed below as `[ID/source:line] — what it requires or forbids`.

---

## A. The four mandated questions — resolved with evidence

### Q1 — Does INV-003 (four-phase topology lock) BIND cairn-intent's Step 3a? **NO.**

**Answer: INV-003 does NOT bind the `cairn-intent` loop or its Step 3a. Step 3a is NOT
structurally locked by a firm ADR. Changing it does NOT require a *superseding* ADR.** It is
governed by a *provisional* ADR (`intent-management-loop`), and the cost-model deferral
(`intent-contract-cost-model`, also provisional) is the thing a redesign must reckon with —
via supersession of *that* ADR's D3/D4, not INV-003.

Evidence:

- **[ARCHITECTURE.md:30] INV-003 scope** — "Every **cairn-tdd** feature runs through exactly
  four phases … Intent (Reader), Validation (Skeptic), Implementation (Builder), Integration
  (Auditor). … Phase count, names, and role assignments are locked; changes require a
  superseding ADR." The lock is explicitly scoped to **cairn-tdd-feature**, the *other* skill.
- **[scripts/validate_architecture.py:570 `validate_phase_topology`]** — INV-003's machine
  binding is a three-way cross-reference over exactly: (1) `.claude/agents/role-topology.yaml`
  (authoritative), (2) `docs/phase-skill-mapping.md` Phase Skill Guide, (3)
  `.claude/agents/phase-N-*.md` filenames. It checks `(phase_ordinal, role_slug)` agreement
  **only for the cairn-tdd four-phase roles**. It does **not** reference `cairn-intent`,
  `Step 3a`, `intent-challenge`, `intent-review`, `human_signoff_after`, or
  `workflows/cairn-intent.yaml`. Editing Step 3a cannot red this binding.
- **[ARCHITECTURE.md grep]** — `cairn-intent`, `intent-challenge`, `intent-review`, `Step 3a`
  appear in **zero** INV-001..012 invariant bodies. No invariant binds the cairn-intent loop.
- **[intent-management-loop frontmatter:6 `firmness: provisional`]** — the ADR that *does*
  govern cairn-intent is provisional, and (`:18-20`) "supersedes nothing and modifies no
  invariant, so Phase 5 independent verification is not required for it." Step 3a is created by
  this ADR's D2(a) front-challenge + the SKILL's `human_signoff_after: true`, not by INV-003.
- **[intent-management-loop:46-48]** — the loop ADR itself records that INV-003 (firm,
  machine-bound) **forbids retiring the four-phase pipeline** but is satisfied by *coexistence*;
  cairn-intent "builds the coexisting path." So INV-003 constrains cairn-intent only negatively:
  **a Step-3a redesign must not retire, rename, or re-topologize the cairn-tdd four phases**, and
  must keep cairn-tdd-feature as the working fallback (D1/D7).

**Net Q1:** The blocker is *not* a topology lock. It is the **deliberate deferral** of the exact
mechanism this arc proposes (Q2). The procedural cost is **superseding two provisional ADRs'
sections** (`intent-contract-cost-model` D3/D4, and `intent-management-loop` D2/D4 to the extent
the front-challenge slot is widened), not breaking a firm invariant. See Q4.

### Q2 — What EXACTLY did `intent-contract-cost-model` defer? (verbatim, with line cites)

**D3 (the deferral clause):**
- **[intent-contract-cost-model:49-54]** D3 — "Heavy-band *enforcement* — derived banding,
  promise↔clause traceability, agent-declared/challenger-attacked severity, and the front-loaded
  fidelity challenge — is **not shipped now**. It is a future ADR, gated on Trial E showing the
  formal proof adds value under the agent-owned model, and it ships as one bundle (the fields
  never precede the workflow that drafts them; the operator never reviews formal machinery). Its
  design constraints are recorded below so the follow-on does not re-derive them."
- **[:56] D4 (explicit non-commitment)** — "This decision introduces **none** of the following
  now: a `band: light` field; a default-HEAVY posture; or any `## Promise` / `pid` / `traces-to`
  / `severity` grammar. No new gate, no new template field ships under this ADR."
- **[:62] D5 (the gate)** — "Trial E measures whether the formal proof adds value **under the
  agent-owned model** … That measurement gates D3."
- **[:72] Honest interim posture** — "there is no *new automated* intent-fidelity backstop until
  D3 lands. The floor concern (below) is real and explicitly unaddressed by new machinery until
  then; we accept today's defenses in the interim."

**The "Deferred design constraints" list — enumerated VERBATIM [intent-contract-cost-model:75-98].**
Header [:78-79]: "The heavy-band enforcement follow-on **must** answer these; they are not solved
here:"

1. **[:80-84] Ceiling-not-floor.** "A promise bounds *scope*, never the *floor* (severity /
   must-fail). The m5 A10 'fail-loud / declare-unsafe' canary can be drafted as 'the validator
   shall report a result' — grounded, atomic, within-promise — and ship as log-and-exit-0. The
   bundle must declare and attack the floor (see `docs/lessons.md` L-028), or wrong-intent ships
   green."
2. **[:85-88] Band determination must be derived, not declared.** "Default-HEAVY is
   adoption-hostile; user self-classification is a burden; either way 'whoever picks the band
   picks whether the floor exists.' The band must be inferred from the work (cites sources /
   declares invariants / touches enforcement) and folded into the promise the operator already
   approves — never a separate knob."
3. **[:89-91] Quadratic at scale.** "Traceability is O(pids×clauses) and a single-pass fidelity
   challenge skims at 30+ clauses; 'one promise you approve' must not degrade into a
   pid-taxonomy."
4. **[:92-93] Distribution staleness.** "New gates/fields render as inert prose on a consumer
   running stale hook wiring (`.slice-system` lag, `intent-management-loop`/R1); enforcement must
   ship via the plugin-release path, and no global `*_FIX` bypass (becomes a universal silent
   disable, L-018)."
5. **[:94-96] Approval timing.** "Promise-approval upstream of the gates can force a re-approval
   when post-approval formalization reds `premise_guard`; ground premises on the prose promise at
   approval and defer only EARS-shaping."
6. **[:97-98] Same-family residual.** "A fresh-context fidelity challenger raises the floor but
   ~60% co-misses (`intent-management-loop`/D4, EXPOSED); cross-family escalation is the named
   fallback."

**Status of the deferred bundle [lessons.md L-028 concrete instance]** — these floor mechanisms
are recorded "as **deferred design constraints** … **not accepted for implementation**." Acting
now reverses that disposition.

### Q3 — What does L-028 REQUIRE of ANY compressed human-approval surface?

**[docs/lessons.md L-028 (pattern + corrective), watching-mark instance 1/3]** — "A compressed
human-approval object bounds the ceiling (scope), never the floor (severity) — declare the floor
or intent silently erodes within scope." The corrective is a four-part mandatory posture for any
agent-drafted artifact under a compressed human anchor (promise / sign-off card / charter):

1. **Mechanize the structural edge** — "a deterministic anchor↔clause traceability check (orphan
   clause = smuggled scope; unrealized anchor line = dropped behavior)."
2. **Declare the floor** — "a *mandatory* per-clause severity field (`mandatory|advisory`) so
   silent floor-erosion becomes a visible, objectable line." **Critically [L-028 + brief:16]:
   severity is the *challenger's* input, NEVER user review.** Re-loading severity onto the user is
   the anti-pattern.
3. **Attack the semantics** — "with a fresh-context fidelity challenger (is each edge honest /
   under-realized?)."
4. **Record the honest limit EXPOSED** — "same-family review ~60% co-misses; it raises the floor,
   it does not close the hole."

**Hard prohibition [L-028 corrective last line]:** "**Never narrate the structural check as if it
caught semantics.**" Any design that markets a cardinality/traceability check as a fidelity check
violates L-028.

**Anti-pattern signals the design must avoid [L-028]:** "'The user approved the promise, so
anything consistent with it is fine.' 'Nothing exceeds the promise' stated as a *sufficient*
invariant. A sign-off / promise / charter treated as the floor when it only sets the ceiling.
Shipping an agent-drafted formal layer under a human anchor with no severity field and no fidelity
attacker. Narrating a cardinality/coverage check as if it verified meaning."

**Binding consequence for THIS arc:** the current Step 3a [SKILL.md:60] surfaces the full
`intent.md` + challenge verdict as one all-or-nothing approval with **no declared floor** — it is
exactly the L-028 ceiling-only anchor. Any redesign MUST (a) declare the floor, (b) keep severity
off the operator's plate (challenger input), (c) attack semantics with a fresh-context fidelity
challenger, (d) record the ~60% co-miss limit honestly, and (e) not narrate any structural check
as a semantic catch.

### Q4 — Procedurally, what does superseding cost-model D3/D4 REQUIRE?

This decision's "act now" branch supersedes a *deliberate deferral*. Requirements:

1. **Append-only ADR; land as a NEW ADR, not a body edit.**
   - [CLAUDE.md "ADRs are append-only"] — `reversibility-guard.sh` allows `Write` on new ADRs,
     blocks overwriting existing ones; `Edit` on an accepted ADR is allowed **only** if
     `old_string`'s first line begins with `status:`, `superseded-by:`, `superseded_by:`, or
     `firmness:` (frontmatter-only). Typo escape: `ADR_EDITORIAL_FIX=1`.
   - [intent-contract-model-decision/framing.md:61] "ADR append-only … any model change lands as
     a **new** ADR, not a body edit."
2. **Supersession frontmatter wiring (two ADRs in scope).**
   - [new-adr.full.md:38-48, identifier-scheme/D9] New ADR frontmatter: `supersedes:` and
     `supersedes-sections:` hold lists of target ADR **`id:` flat slugs** (NOT filenames, NOT
     NNN). Cost-model is a *partial* (D3/D4) supersession → `supersedes: [intent-contract-cost-model]`
     **plus** `supersedes-sections: [D3, D4]` (and likely `[D3, D4, D5]` since D5 is the gate). If
     the front-challenge slot is widened, also `supersedes-sections` against `intent-management-loop`
     D2/D4 — or record those as `adrs-referenced` if only extended, not invalidated.
   - [new-adr.full.md:81-84] On the superseded ADR(s): update **frontmatter ONLY** — set
     `status: superseded` (or keep `accepted` with section-level supersession per L-029) and
     `superseded-by: <new-id>`. **Never edit the old body.** Note: `intent-contract-cost-model`
     retains valid decisions (D1/D2) — per L-029 a parent that keeps valid decisions stays
     `accepted` and only its *sections* are superseded.
3. **Commit prefix: use `docs:` (or `design:`), NOT `adr:`.**
   - [validate_architecture.py:278-283 `_FALLBACK_REGISTRY`] INV-001's registered prefixes are
     exactly: `feat:`, `docs:`, `fix:`, `chore:`, `test:`, `design:`. **`adr:` is NOT registered**
     — an `adr:`-prefixed commit reds the INV-001 git-log-walk binding.
   - **[new-adr.full.md:95 is WRONG]** — it instructs `git commit -m "adr: …"`; this contradicts
     the registry and operator memory `project_adr_commit_prefix`. The last two ADR commits used
     `docs:` (git log: `docs: cairn-intent-git-lifecycle…`, `docs: git-workflow-v1…`). **Use
     `docs:`.**
   - [ARCHITECTURE.md:13 INV-001] direct commits with unregistered prefixes are not permitted
     except as recorded in a superseding ADR; the walk runs `--no-merges`.
4. **L-029 orphan-sweep (transitive supersession).**
   - [lessons.md L-029, watching-mark 1/3] "Treat subsystem retirement as a transitive
     supersession sweep. When retiring machinery, enumerate every firm ADR whose decisions
     reference it and supersede the affected *sections* in the same milestone
     (`supersedes-sections`…). A retirement ADR should carry an explicit 'orphans' list … If the
     sweep is deferred, record the orphan set as a roadmap item." For THIS arc: enumerate every
     ADR/skill/doc that asserts "no new automated intent-fidelity backstop / heavy-band deferred"
     and update it. **Known dependents:** `intent-contract-cost-model` D3/D4/D5 + its "Deferred
     design constraints" list; `intent-management-loop` D2(a)/D4 (the front-challenge slot +
     EXPOSED 60% residual); `.claude/skills/cairn-intent/SKILL.md` Step 3a + Step 3; `docs/lessons.md`
     L-028 (its "deferred, not accepted" disposition flips → add a follow-on note);
     `workflows/cairn-intent.yaml` nodes (`intent-challenge` / `human_signoff_after`); the two
     fresh-context agent prompts `.claude/agents/intent-challenge.md`, `.claude/agents/intent-review.md`.
5. **Index + validation.**
   - [new-adr.full.md:87-90] Add the new ADR row to `docs/adr/index.md` (columns: id | name |
     status | firmness | topic | date). No `/refresh-architecture` step exists post-M4
     [ARCHITECTURE.md:9] — manual `ARCHITECTURE.md` edits are permitted as part of an
     ADR-supersession-justified commit. Run `uv run pytest` + `scripts/validate_architecture.py`
     (INV-001 walk, INV-003 topology) to confirm green.
   - [new-adr.full.md:13 vs disk reality] Docs describe a `<NNN>-<slug>.md` filename; **current
     practice is flat-slug filenames** (`intent-management-loop.md`, `git-workflow-v1.md`, etc.).
     Match the live convention: `docs/adr/<new-flat-slug>.md`. Successor of a `-vN` ADR uses the
     `-v2` pattern; cost-model has no version suffix, so pick a descriptive slug.
6. **Evidence discipline for the "act now" decision itself.**
   - [operator memory `feedback_decision_commit_only_evidence_supports`; brief:17] cost-model
     deferral was made on "commit only what evidence supports." Trial E is n=1; D3 is *gated on*
     Trial E. Superseding it now must either (a) carry new evidence, or (b) commit only the
     invariant + a cost-removing/timing move and defer unmeasured machinery — "cost confirmed" ≠
     "enforcement value confirmed."
   - [lessons.md L-027] do not let adversarial completeness select the null action; if acting,
     name the one mechanism that survives the attacks AND is buildable now, and prove it.

---

## B. Binding constraint envelope (the full set)

### Topology / phase
- **[ARCHITECTURE.md:30 INV-003]** — FORBIDS retiring, renaming, or re-topologizing the cairn-tdd
  four phases / four roles; does NOT bind cairn-intent Step 3a (Q1). A redesign must keep
  cairn-tdd-feature intact as fallback.
- **[intent-management-loop D1/D7]** — REQUIRES coexistence: four-phase pipeline retained
  unmodified; cairn-tdd-feature stays the fallback; four-phase retirement is a *separate future
  firm supersession*, not this arc.
- **[intent-management-loop D2]** — the loop keeps construction fluid (one conversation, test-first,
  no phase resets) bracketed by two decorrelation checkpoints; approval is **delta-triggered** (re-
  fires only on premise / `must-satisfy` clause edit, never on diff size). A Step-3a redesign must
  not reintroduce per-session approval ceremony or diff-size triggers.
- **[framing.md:57 / context.md:59]** — keep any gate at the **Phase-1→2-equivalent boundary**
  (pre-construction); no new phase transitions.

### Context budget
- **[ARCHITECTURE.md:39 INV-004]** — session-start context ≤40,000 tokens; slash commands use
  progressive disclosure (lite ≤500 tokens + optional `.full.md`). Binds ONLY if the redesign adds
  session-start or new command/dispatch context. Machine-checked by `tests/unit/test_context_budget.py`.
- **[intent-management-loop D4 / context.md:59]** — no costly new subagent/dispatch pathway
  without a budget justification; reuse the existing front-challenge dispatch slot. Both
  decorrelation agents run fresh-context **same-family** (fits INV-004).

### Floor / fidelity (L-028 — the governing lesson)
- **[lessons.md L-028]** — any compressed approval surface MUST: declare the floor (per-clause
  severity, `mandatory|advisory`); keep severity as the **challenger's input, NEVER user review**;
  attack semantics with a fresh-context fidelity challenger; record the ~60% co-miss limit EXPOSED;
  and NEVER narrate a structural check as a semantic catch.
- **[intent-contract-cost-model:80-84 deferred-constraint-1]** — the floor must be *declared and
  attacked*, or wrong-intent ships green (ceiling-not-floor).
- **[brief:13,16]** — because of the ~60% co-miss, the only decorrelation-preserving compression is
  predict-before-see: elicit the operator's fidelity/floor criteria BEFORE revealing the committed
  contract; severity stays off the user's plate.

### Decorrelation
- **[intent-management-loop D4 / cost-model:97-98 / brief:18]** — a single same-family fresh-context
  agent ~60% co-misses; it cannot be the sole floor/fidelity guard. Cross-family escalation is the
  **named fallback** (recorded EXPOSED). A correlated miss in Trial E is the trigger to open a
  cross-family `/decision`.
- **[intent-challenge.md:13-19 (per brief)]** — the front-challenger is scoped to *premise-truth*
  (`## Premise Grounding` claims vs cited source), and that section is OPTIONAL; a fidelity leap
  that isn't a source-citing premise is OUT of scope today. A redesign relying on the front-slot
  must widen this scope explicitly.
- **[intent-review.md:15-22 (per brief)]** — the back-gate checks diff-against-CONTRACT
  (clause-check / evidence-adequacy / scope-check); a faithful diff of a leaked clause passes
  clean. The back-gate cannot recover an intent-fidelity leap.

### Severity / band determination
- **[cost-model:85-88 deferred-constraint-2]** — band/weight must be **derived** from the work
  (cites sources / declares invariants / touches enforcement), folded into the promise the operator
  already approves — NEVER a separate operator-set knob ("whoever picks the band picks whether the
  floor exists").
- **[cost-model:89-91 deferred-constraint-3]** — must not degrade into an O(pids×clauses)
  pid-taxonomy; a single-pass challenge skims at 30+ clauses.

### Distribution / hooks / deps
- **[cost-model:92-93 deferred-constraint-4 / CLAUDE.md / intent-management-loop R1]** — new
  gates/fields are inert prose on a consumer with stale `.slice-system` wiring; enforcement must
  ship via the plugin-release path; **no global `*_FIX` bypass** (universal silent disable, L-018).
- **[CLAUDE.md "New-code guidance" / framing.md:62]** — new code is **Python, function-based,
  pydantic/typer/pyyaml only, no decorators/metaprogramming**. AI-driven/semantic analysis **cannot
  live in a provider-agnostic hook** — it must be a skill step or a subagent. Surviving bash hooks
  stay until their own migration slices.
- **[CLAUDE.md "Edit canonical paths only"]** — never edit via `.slice-system/`; target
  `checks/…`, `commands/claude-code/…`, `scripts/…`, `.claude/skills/…` directly (role_guard.py
  does not strip the `.slice-system/` prefix → denial).
- **[CLAUDE.md "No hardcoded timeouts/sizes"]** — consumer-facing scripts use
  `int(os.environ.get("CAIRN_<KNOB>", <default>))` and document the var in operational-reference.

### Grounding / existing gates (reuse unchanged)
- **[cost-model:94-96 deferred-constraint-5 / context.md:50]** — ground premises on the prose
  promise AT approval; defer only EARS-shaping. Order: `premise_guard` → (any new
  traceability/severity) → fidelity challenge → construction. Promise-approval upstream of the
  gates must not force a re-approval when later formalization reds `premise_guard`.
- **[intent-management-loop D6 / framing.md:60]** — reuse the three shipped hooks unchanged
  (`premise_guard`, `role_guard`, `atomicity_guard`); D6 says "no new hooks." A new *deterministic*
  check would be a sibling guard at the same gate, but adding a hook needs supersession of D6's
  "ambient enforcement, no new hooks" stance (or it must be a skill-step, not a PreToolUse hook).

### Metric
- **[slice-intent-contract:20 wrong-if / brief:21]** — ">15 min/slice operator review = failure
  (contract too dense; defeats rubber-stamping defeat)." **ATTACK (carry forward):** this is a
  failure-*ceiling* possibly mislabeled as a success *target*; fast approval is observationally
  identical to disengagement. Prefer correlating against **post-close defect-escape**, not
  review-time-under-15-min. (slice-intent-contract is `status: superseded` by
  cairn-thin-substrate-direction — the 15-min metric is inherited lore, not a live binding, but the
  rubber-stamping concern persists.)

### Scope / ethos
- **[intent-management-loop D8 / framing.md:64]** — single-operator-per-branch (intent lives in
  git); multi-operator/multi-branch reconciliation is EXPOSED + deferred. Read-only/Q&A sessions
  exempt. New write paths must be envelope-declared (`role_guard`).
- **[CLAUDE.md "Cut before adding" / brief:27]** — prefer widening the existing front-challenge
  slot over new phases/dispatch/machinery. New tools/plugins/abstractions are liabilities; default
  no.
- **[operator memory `feedback_substrate_context_separation`]** — agent-facing surfaces must not
  expose operator memory; canonical sources only.

### Procedure (supersession)
- **[CLAUDE.md / reversibility-guard.sh]** — ADRs append-only; new ADR for any model change;
  frontmatter-only edits on the superseded ADR; `ADR_EDITORIAL_FIX=1` for typos only.
- **[validate_architecture.py:278-283]** — commit prefix MUST be `docs:`/`design:` etc.; **`adr:`
  reds INV-001** (the `/new-adr` docs are stale on this point).
- **[lessons.md L-029]** — transitive orphan-sweep: enumerate + supersede-sections (or roadmap-
  record) every dependent ADR/skill/doc in the same milestone; carry an explicit "orphans" list.
- **[identifier-scheme D9 / new-adr.full.md]** — `supersedes` / `supersedes-sections` /
  `adrs-referenced` hold flat-slug `id:` values; filenames are flat slugs in live practice.

---

## C. Decision-shaping implications (carried to later phases)

1. **The blocker is the deferral, not a lock.** No firm ADR or invariant prevents a Step-3a
   redesign. The cost is superseding two *provisional* ADRs' sections + an L-029 sweep + an
   evidence argument for acting ahead of the Trial-E gate. This makes Approach D
   (measure-first/deferral-honoring) the *cheapest* and the steelman baseline, and lowers the
   procedural bar for A/B/C versus what the brief's "Open question" feared.
2. **Any "act now" design is forced by L-028 to carry: a declared floor (severity = challenger
   input, off the user), a fidelity attacker (fresh-context), an honest ~60% co-miss record, and a
   structural-check honesty caveat.** A design lacking any of these is non-conformant on its face.
3. **The predict-before-see move (Approach A)** is the only compression the brief identifies that
   sidesteps the ~60% co-miss by having the *human* supply the floor at peak context — but it must
   still keep severity-as-challenger-input for the *contract's* clauses (L-028) and not re-load
   formal severity onto the operator (cost-model D3 "operator never reviews formal machinery").
4. **Cross-family (Approach B)** is the repo's *named* fallback for the co-miss, already EXPOSED in
   two ADRs — choosing it is honoring a pre-recorded escalation, not inventing machinery, but it
   adds cross-family dispatch (INV-004 budget check) and is heavier than D6's "no new hooks / same-
   family" stance.
5. **Band-derivation (cost-model deferred-constraint-2)** forbids any operator-set severity/band
   knob; if a design asks the operator to tag severity, it violates both L-028 (severity off the
   user) and the derived-band constraint.
