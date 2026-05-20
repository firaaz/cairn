# Phase 0.5 — User-Journey Trace

## Branch RETROFIT

### Trigger
Trial B's close verdict "works, but might be too strict" paired with deferred legacy-label retrofit scope in Trial B spec (14 ADRs missing `name:` field, 6 slices with id-shape violations). No new design required — apply identifier-scheme contract (already `firm`) to stale artifacts. Operator chooses RETROFIT if the contract shape is proven-sound and the mechanical cleanup is low-friction.

### Artifacts touched
- `docs/adr/*.md` — 14 ADRs missing `name:` or legacy `title:` field; 4 others with legacy `title:` only. Edit operation: add `name:` field to frontmatter (or rename legacy `title:` → `name:` where both exist).
- `.claude/features/*.yaml` — slices with uppercase/dotted id violations recorded during Trial B T2 discovery (6 slices total in `compression.yaml`, `housekeeping.yaml`, `orchestrator-paths.yaml`). Decision per violation: rename in-place (breaking id immutability rule D3) or accept as legacy-baseline advisory (D2 slice-id-shape baseline raised from 0 → 6).
- `tests/unit/test_identifier_scheme_contract.py` — update `LEGACY_LABEL_BASELINE` constant from trial value (10) downward as each ADR is retrofitted.

### Downstream readers
- **Human reviewers:** will consume the diffs showing the mechanical edits.
- **`test_identifier_scheme_contract.py`:** runs on every commit; must pass baseline assertions on the advisory ceiling.
- **Phase 1 (Reader) for future slices:** if Phase 1 ever reads `.claude/features/*.yaml` to construct intent input (not current), the normalized `name:` field becomes a guaranteed source; currently Phase 1 reads only plan-docs and ADRs.
- **ADR cross-reference resolution (D9 test):** if any retrofitted ADR carried dangling `adrs-referenced`, resolving those refs becomes part of the retrofit. Test enforces this on next run.

### State transitions
1. Operator selects RETROFIT branch → no new ADR, no new design decision.
2. Implementer audits Trial B's deferred list (14 ADRs + 6 slices) → pre-flight check.
3. For each of 14 ADRs: edit frontmatter to add or normalize `name:` field. Gate: `reversibility-guard.sh` allows frontmatter-only edits (old_string begins with `firmness:`, `status:`, `superseded-by:`). **Mechanism gap:** Rule allows editing `firmness:` but the retrofit adds a new `name:` field — this is a *new key*, not an amendment of existing frontmatter. **Check:** does reversibility-guard treat "add new frontmatter key" as allowed? If not, operator must invoke `ADR_EDITORIAL_FIX=1` escape hatch on every ADR edit, raising visibility (good) but procedural friction (cost).
4. For each of 6 slices: evaluate id-shape violation. Decision per violation: (a) rename slice (requires D3 immutable-id override, marks as unsustainable), (b) document as legacy exception, update `LEGACY_SLICE_ID_BASELINE` constant in test. Trial B spec chose (b); RETROFIT maintains that choice.
5. Run test suite: `test_identifier_scheme_contract.py` must pass; advisory baselines are fixtures of the test's constants.
6. Commit all edits under message `chore(identifier-scheme): retrofit legacy labels and slice-id baselines` (single commit per session is typical for this scope).

### Verification path
- `uv run pytest tests/unit/test_identifier_scheme_contract.py -v` — all 6 test functions pass; advisory baseline assertions confirm counts match the retrofit.
- `git diff HEAD~1` on the session's final commit shows exactly N frontmatter edits to `docs/adr/*.md` and M constant updates in the test file. No other files touched.
- Manual spot-check: one retrofitted ADR is read cold by a peer to confirm `name:` field is human-sensible and does not duplicate existing heading/title text.

### Exit criterion
- `test_identifier_scheme_contract.py` passes with updated baseline constants.
- All 14 ADRs carry a `name:` field in frontmatter.
- Commit is signed off by operator; no follow-up actions (the deferred retrofit is complete).

### Open mechanism gaps
1. **Reversibility-guard treat-new-keys rule:** unclear whether `Edit` on an existing ADR frontmatter that *adds* a new key (not amending existing key) is allowed by `reversibility-guard.sh:48,76` logic. If not, every ADR edit requires `ADR_EDITORIAL_FIX=1` overhead. **Verify before dispatch:** test one edit locally and report the gate.
2. **Slice-id immutability vs. advisory ceiling:** Trial B resolved the tension by choosing advisory baseline (accept legacy violations, test enforces ceiling). No new decision needed — but the mechanism is test-level constants only, no ADR amendment. If baseline drifts (new slices added with id violations), only the test changes; users won't be aware of the constraint. **Silent acceptance risk:** worth a handoff note flagging the advisory nature of slice-id enforcement.

---

## Branch TRIAL-C

### Trigger
Operator chooses Trial-C to validate contracts at the highest-friction surface: slice `intent.md` produced by Phase 1 (Reader). This is the most-LLM-authored, most-prone-to-rubber-stamping artifact. If the protocol defeats rubber-stamping on intent, the validation spans the narrowest artifact (most LLM control) to the widest impact (feeds all downstream phases). Operator selects TRIAL-C if Trial B's verdict "works" outweighs "too strict" — the contract shape is proven; now test it on the hardest case.

### Artifacts touched
- `.claude/agents/phase-1-tdd.md` — Phase 1 output spec (line 13–19) currently prescribes `intent.md` sections but does not bind a frontmatter `contract:` block. Add `contract:` section to the intent YAML frontmatter spec with must-satisfy / must-not-violate / wrong-if / evidence clauses. Parallel update: `.claude/agents/phase-2-tdd.md` must document what Phase 2 does with the contract (e.g., "enumerate ambiguities against contract clauses, not prose"; "test each `must-satisfy` invariant from the contract, not plan-doc intent").
- `tests/unit/test_slice_intent_contract.py` (new test file) — deterministic invariant tests mirroring Trial B's pattern. Scope: for a given `intent.md`, verify contract clauses are satisfiable (e.g., "Risk Surface names a domain-level failure mode, not generic risk"; "Feature-Local Invariants are citable by Phase 2 tests").
- `.claude/skill-runs/slice-intent-contract-trial-c/` (trial workspace) — Phase 1 writes an initial draft intent under the new contract shape to `.claude/skill-runs/slice-intent-contract-trial-c/intent.md`. Phase 2 writes validation tests that explicitly bind each test to a `must-satisfy` clause of the contract. Phase 4 audits the contract durability (did the contract catch semantic wrongness that code review might have missed?).

### Downstream readers
- **Phase 2 agent (`phase-2-tdd.md`):** receives intent.md as sole input (per operational-reference.md line 97). Today Phase 2 reads intent's prose Specification/Verification/Risk-Surface sections. Under TRIAL-C, Phase 2 also reads the frontmatter `contract:` block and **writes its tests against the contract's `must-satisfy` invariants, not the prose intent**. Mechanism: skill brief includes the contract block as a structured input; Phase 2's prompt (phase-2-tdd.md) is amended to reference the contract-invariant mapping. **Audience:** Phase 2 is a dispatch-skill subagent, not the operator. The contract blocks Phase 2's freedom to interpret prose — it must satisfy the contract, period.
- **Phase 1 review gate (human, operator-driven):** Today the operator reads `intent.md` prose before Phase 2 dispatch. Under TRIAL-C, the review points to the frontmatter `contract:` block explicitly: "Does this contract capture the boundary I intended?" If the prose intent and the contract conflict, the operator raises an issue before Phase 2 runs. The contract becomes the review surface, not the prose. **Mechanism:** Skill brief to operator before Phase 2 dispatch includes the contract block in JSON/YAML; operator confirms contract-as-written before Phase 2 is triggered.
- **Phase 4 (Auditor) sweep:** reads intent.md, implementation, and tests. Under TRIAL-C, Phase 4 audits whether the test suite *actually* enforces the contract's invariants or whether tests drifted to prose. If a `must-satisfy` invariant is not directly tested, Phase 4 escalates. **Mechanism:** Phase 4 prompt includes contract-to-test mapping verification; outputs sweep-notes.md with explicit contract-coverage report.

### State transitions
1. Operator selects TRIAL-C → decision-weight commitment to refactor Phase 1 output shape (intent.md now carries structured contract).
2. Trial plan amended: `.claude/plans/2026-05-20-slice-intent-contract-trial-c.md` (single-page spec, author via superpowers:writing-plans or sketch inline). Plan spec includes: what makes intent-contract success (Phase 2 tests bind to contract; Phase 4 coverage is ≥95%), what makes it fail (contract grows past 15 lines; Phase 2 reports contract ambiguity; Phase 4 finds untested must-satisfy).
3. Phase 1 executed on a greenfield or modification feature (scope: one slice, likely the simplest in the backlog). Phase 1 agent writes intent.md with frontmatter `contract:` block (5–10 lines, modeled on Trial A handoff contract). Example contract for intent:
   ```yaml
   contract:
     must-satisfy:
       - Specification names the observable behavior, not the implementation
       - Verification section lists the test invariants to be checked
       - Risk Surface names domain-level failure mode, not generic risk
       - Feature-Local Invariants are tied to ARCHITECTURE.md INV-* or slice-specific conditions
     must-not-violate:
       - Prose uses first-person ("I will", "we should") — use imperative instead
       - Risk Surface exceeds 80 words or is generic ("tests might fail")
     wrong-if:
       - Phase 2 reports ambiguities in the contract that prose doesn't resolve
       - test_slice_intent_contract.py finds a must-satisfy clause unverifiable
     evidence:
       - test_slice_intent_contract.py passes
       - Phase 2 agents report zero ambiguities in contract
   ```
4. Operator reviews `intent.md` + contract block. Gate: operator confirms contract captures the intended boundary **before Phase 2 is dispatched**. Mechanism: skill loops back to operator with the intent + contract in rendered form; operator approves or amends the contract.
5. Phase 2 is dispatched with the contract block included in the Phase 2 brief (not just the intent prose). Phase 2 writes tests where each test explicitly documents which contract-clause it enforces. Example:
   ```python
   def test_intent_specification_is_observable():
       # Enforces contract.must-satisfy[0]: "Specification names the observable behavior"
       intent = yaml.safe_load(open(".claude/skill-runs/slice-intent-contract-trial-c/intent.md"))
       spec = intent["Specification"]
       # ... assertions that spec uses observable terms ...
   ```
6. Phase 4 audits contract durability: for each `must-satisfy` clause, Phase 4 checks if at least one test in the validation suite enforces it. Phase 4 output includes coverage map: `{ must-satisfy[0]: [test_intent_specification_is_observable], ... }`. If any clause is uncovered, Phase 4 escalates.

### Verification path
- `test_slice_intent_contract.py` passes — intent.md contract is well-formed and satisfiable.
- `uv run pytest tests/` on the trial slice: all tests pass; Phase 2's tests explicitly reference contract clauses in comments or test-discovery metadata.
- Phase 4's sweep-notes.md includes a table: contract-clause → test-that-enforces-it. Coverage must be ≥95% (one clause may be implicit in multiple tests, acceptable).
- Operator's one-line verdict: "contract surfaced an ambiguity Phase 2 would have asked about" (success signal) vs. "prose-and-contract said the same thing; contract added no clarity" (failure signal) vs. "contract is still too strict for Phase 2 to work with" (iteration signal).

### Exit criterion
- Trial slice (one feature, full P1→P4 run) completes under new contract shape.
- Operator verdict on contract usability is recorded in skill-run close-out.
- If verdict is "works": TRIAL-C becomes the new shape for Phase 1; operational-reference.md is amended; future slices use the contract shape.
- If verdict is "too strict" or "not useful": TIGHTEN-FIRST analysis is queued; TRIAL-C is archived as "shape works, but needs refinement."

### Open mechanism gaps
1. **Phase 1 → operator review → Phase 2 dispatch loop:** Current flow is Phase 1 commits intent.md, then Phase 2 is triggered from handoff. Under TRIAL-C, operator must review the *contract block specifically* before Phase 2 runs. Mechanism: skill brief to operator should surface the contract block JSON for approval. **Unclear:** does the existing cairn-tdd-feature skill have a built-in operator-review gate before Phase 2? If not, that is a workflow addition requiring skill SKILL.md amendment. **Verify:** check cairn-tdd-feature SKILL.md for pause/approval points.
2. **Contract-to-test binding in Phase 2 output:** Phase 2 writes tests; tests must document which contract-clause they enforce. Mechanism is test-file comments/metadata, but there is no validator enforcing the binding. If Phase 2 drifts (writes tests against prose, not contract), Phase 4 catches it (contract-coverage audit), but the drift is late. **Early enforcement unclear:** no mechanism prevents Phase 2 from ignoring the contract. Phase-2-tdd.md prompt amendment is the only enforcement; discipline only. **Recommend:** Phase 2 brief should include explicit instruction that tests must cite contract clauses in comment headers; Phase 4 audits this.
3. **Contract versioning and amendments:** If Phase 1 writes a contract, then Phase 2 finds the contract ambiguous (e.g., a `must-satisfy` clause is unprovable), who amends the contract? Current identifer-scheme ADR contract can be amended via frontmatter-only edit (reversibility-guard allows `firmness:` edits). Intent.md is not an ADR — it's a skill-run artifact. **Unclear:** what is the amendment authority and process for intent.md contracts? If operator amends the contract after Phase 1 commits, does the amendment go into the committed intent.md (rewrite the artifact) or into a separate contract-revision document? If rewrite, that's not append-only. **Mechanism unclear:** needs explicit policy for contract amendments on non-ADR artifacts.

---

## Branch TIGHTEN-FIRST

### Trigger
Operator treats Trial B's verdict "might be too strict" as a signal that the contract shape itself needs refinement before extending to a third surface (Trial C / intent). Examples of tightenings: relax mandatory keys, introduce contract-block versioning, separate `must-satisfy` / `must-not-violate` granularity (e.g., move some `must-not-violate` to `escalate-when`), or narrow the `wrong-if` conditions to avoid false positives on legitimate edge cases. TIGHTEN-FIRST defers both RETROFIT and TRIAL-C; the branch picks "iterate on the mechanism itself" over "apply proven mechanism."

### Artifacts touched
- `docs/adr/contract-and-protocol-v2.md` (new ADR) — amends identifier-scheme ADR's contract section. Supersedes or supplements identifier-scheme D1–D9 with refined contract-block shape. Scope is explicitly the template/shape (must-satisfy/must-not-violate/wrong-if structure), not a new entity type or new identifier scheme. Firmness: likely `exploratory` or `draft` until the tightening is validated in code (e.g., the new shape is tested against the identifier-scheme ADR itself, Trial A handoff contract, and a simulation of Trial B/Trial C to confirm the shape works for all three).
- `tests/unit/test_contract_shape.py` (new test file) — property tests or deterministic schema tests on the contract shape itself. Validates that the refined shape is sound (e.g., "no contract exceeds 20 lines"; "every contract has ≥1 must-satisfy clause"; "must-not-violate and must-satisfy are orthogonal — no clause appears in both"). Test runs against actual contract blocks in the codebase (identifier-scheme ADR's contract, Trial A handoff contract) as test fixtures.
- `docs/plans/2026-05-20-tighten-contract-shape.md` — single-page plan doc naming the specific tightenings and their motivation. Scope: design + test, no implementation of other trials yet. Likely a 1–2 session effort (one session per tightening + one for unified test).

### Downstream readers
- **Future RETROFIT or TRIAL-C runs:** whichever branch is chosen after tightening will use the refined shape. The new ADR becomes the canonical reference instead of (or alongside) identifier-scheme's contract section.
- **Any new contract surfaces added post-tightening:** (e.g., ADR contracts, plan contracts, decision-point contracts) will cite the refined shape as their template.
- **Trial A handoff contract and Trial B identifier-scheme contract:** if the tightening changes the shape significantly, the existing contracts may require amendment to comply with the new shape. This is a consistency audit, not a new trial — verify the new shape retrofits to past contracts without loss of clause coverage.

### State transitions
1. Operator selects TIGHTEN-FIRST → no immediate artifact implementation, but a decision-weight design commitment (new ADR).
2. Brainstorm phase (superpowers:brainstorming) identifies candidate tightenings. Examples:
   - **Relax mandatory keys:** `must-satisfy` could be optional (some contracts may have no must-satisfy, e.g., a contract that is purely negative — "don't do X"). Trial A and Trial B both have 1+ must-satisfy; is that universal?
   - **Introduce contract-block versioning:** add `contract-version: 1` field; future shapes become `contract-version: 2`. Allows gradual adoption and backwards-compat. Trial B caught its own rule violation and chose to bend — versioning would allow explicit tolerance.
   - **Separate escalation from wrong-if:** `wrong-if` is a "stop and audit" condition; `escalate-when` in Trial A plan was a "stop and ask operator" condition. Merge them or keep distinct? Current shape conflates both.
   - **Enumerate the audience per clause:** each must-satisfy / must-not-violate is authored for one audience (operator? phase agent? validator? human reviewer?). Trial A contract was agent-to-agent (handoff readers). Trial B was validator-facing (test-property interpretation). Trial C will be human-review-facing (operator confirms contract before Phase 2). Audience mismatch may explain "too strict" — a clause written for a validator is unnatural for an operator to review.
3. Plan doc (`2026-05-20-tighten-contract-shape.md`) is written with the brainstorm outputs and a decision on which tightenings to prototype.
4. New ADR (`contract-and-protocol-v2.md`) is drafted with the refined shape. Frontmatter: `status: exploratory` (not `accepted` — waiting for validation).
5. Test file (`test_contract_shape.py`) is written to validate the refined shape against existing contracts (fixture: parse identifier-scheme contract and Trial A handoff contract; assert they pass under the new shape). If existing contracts don't fit the new shape, iteration on the shape.
6. Operator reviews the new shape + test results. **Gate:** before committing the new ADR, operator confirms the tightening does not break Trial A/B contracts (backward-compat) or makes them simpler (success signal).

### Verification path
- `uv run pytest tests/unit/test_contract_shape.py -v` — all shape-validation tests pass.
- Existing contracts (identifier-scheme D1–D9, Trial A handoff) are loaded by the test as fixtures and validated against the new shape. **Backward-compat verified:** existing contracts satisfy the new schema.
- Manual review: one tightening is applied to an existing contract in-repo (e.g., identifier-scheme's contract block is re-formatted to the new shape) and reviewed by operator for readability improvement.
- Operator verdict: "tightening makes the shape clearer for [audience A]" (success) vs. "tightening moves the problem elsewhere" (rework signal).

### Exit criterion
- New ADR `contract-and-protocol-v2.md` is committed with `status: exploratory` and the refined shape documented.
- `test_contract_shape.py` passes.
- Plan doc is committed.
- Operator decision (next action): retry RETROFIT with new shape, start TRIAL-C with new shape, or do another tightening round.

### Open mechanism gaps
1. **Audience-specificity in contract clauses:** Trial A (handoff) is agent-to-agent. Trial B (identifier-scheme) is validator-facing. Trial C (intent) is human-operator-facing. The same contract shape cannot serve all three audiences equally well without annotation. **Unresolved:** should the contract-shape include an audience field per clause (e.g., `must-satisfy: [{clause: "...", audience: "validator"}, ...]`) or should each artifact-type define its own instantiation of the generic shape? Current shape is generic; adding audience field is a tightening. **Recommend:** TIGHTEN-FIRST should enumerate audience per trial and decide.
2. **Backward-compat of amendments:** if contract-v2 shape introduces `contract-version:` or new optional fields, how do existing commits with contract-v1 shape behave? Do validators/tests accept both versions indefinitely? When does v1 deprecate? **Policy missing:** TIGHTEN-FIRST must define the sunsetting or coexistence story. This is not a mechanism gap (code can handle both) but a governance gap (when do we stop accepting v1?).

---

## Cross-branch comparison

### Convergence and divergence

**Convergence:** All three branches begin by treating Trial B's verdict as input. All three land on a mechanism in the identifier-scheme ADR (the most-crossed boundary artifact in cairn). RETROFIT applies the mechanism to stale artifacts; TRIAL-C extends the mechanism to a new artifact surface; TIGHTEN-FIRST refines the mechanism itself.

**Divergence:**
- **RETROFIT is mechanical, zero-decision:** applies proven identifier-scheme contract to 14 ADRs + 6 slices. No new ADR, no new shape, no design risk. Lowest decision weight; pure cleanup.
- **TRIAL-C is high-friction validation:** bind the proven contract to the artifact most-prone-to-rubber-stamping (intent.md). Highest expected learning (if intent contracts work here, the protocol scales). Highest implementation cost (Phase 1 + Phase 2 prompt rewrites, operator review loop amendment).
- **TIGHTEN-FIRST is design-weight iteration:** amend the contract shape itself before scaling to Trial C. Lowest friction (no new artifact surface), highest upstream impact (changes the shape used by RETROFIT and Trial C). Defers both scaling paths.

### Dependency chains and viability

**RETROFIT → (TRIAL-C or TIGHTEN-FIRST):** Completing RETROFIT does not enable or disable either. The 14 ADR edits are orthogonal to the contract shape. **Viability:** RETROFIT + TRIAL-C can happen in sequence (complete legacy cleanup, then test intent contract under existing shape). RETROFIT + TIGHTEN-FIRST also independent (cleanup can proceed while shape is refined).

**TRIAL-C → (RETROFIT or TIGHTEN-FIRST):** If TRIAL-C succeeds ("contract caught rubber-stamping at intent level"), the protocol has proven scaled from handoff (Trial A) to identifiers (Trial B) to intent (Trial C). At that point:
- RETROFIT becomes obviously valuable (apply proven protocol to 14 stale artifacts before deprecating them).
- TIGHTEN-FIRST becomes optional (the shape worked without amendment; refinement is nice-to-have, not mandatory).

If TRIAL-C fails ("contract is too strict for Phase 2 to use," or "operator found the review loop unnatural"), then:
- TIGHTEN-FIRST is the recovery path (amend the shape before trying TRIAL-C again).
- RETROFIT is still viable but lower-priority (mechanical, deferred until the protocol shape is stable).

**TIGHTEN-FIRST → (RETROFIT or TRIAL-C):** Whichever branch is chosen afterward must use the new shape. If tightening introduces backward-compat breaks (e.g., makes `must-satisfy` optional), then Trial A/B contracts may need re-formatting as part of the adoption. This is not decision-weight but operational friction.

### Mechanism gaps and risk surface across branches

| Mechanism | RETROFIT risk | TRIAL-C risk | TIGHTEN-FIRST risk |
|-----------|---|---|---|
| **Reversibility-guard new-key edit gate** | Required; unclear if allowed; may force `ADR_EDITORIAL_FIX=1` overhead | Not applicable | Not applicable |
| **Contract amendment authority (non-ADR)** | Not applicable | Critical; intent.md contract must be amenable if Phase 2 finds it ambiguous; no policy defined | Not applicable |
| **Operator review loop (before Phase 2)** | Not applicable | Critical; skill must gate Phase 2 on operator approval of contract; flow unclear | Not applicable |
| **Audience-specificity of clauses** | Not applicable | High friction (intent contracts are human-readable; maybe too strict for Phase 2 agents to use) | Critical; TIGHTEN-FIRST must decide if audience field is needed |
| **Backward-compat of shape refinements** | Not applicable | Not applicable | Critical; how long do v1 contracts coexist with v2? |

### Recommended sequence (if all three are to land)

1. **RETROFIT first** (1 session, low risk, unblocks other branches). Cleans up legacy drift and validates that reversibility-guard allows frontmatter-new-key edits (or surfaces that gap early).
2. **TIGHTEN-FIRST second** (1–2 sessions, design-weight, no new artifact surface). Refines the shape based on Trial B's "too strict" feedback *before* extending to intent (highest-friction surface). Ensures TRIAL-C starts with a ready-made shape, not a shape-that-may-need-amendment.
3. **TRIAL-C third** (1 session, uses the tightened shape from step 2, validation of intent-as-contract). Highest-friction test happens last; has the benefit of iterations from steps 1 + 2.

This sequence limits rework (step 1 de-risks reversibility-guard, step 2 de-risks shape brittleness) and sequences decision-weight in ascending order (mechanical → design → validation).

