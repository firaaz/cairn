# close-review — graduated-contract (increment #3)

**Status: close-review-blocked.**

One must-not-violate clause is violated by a *silent cross-cutting commitment* the
constructor introduced and did not surface: the proposed `templates/intent.md` flips
the shared `## Contract` block's normative framing from "OPTIONAL / omit for trivial
work" to "**mandatory** for every repo-writing session / scope-statement **never
omitted**." That template is consumed by BOTH `cairn-intent` (correct per D3) AND the
live `cairn-tdd-feature` Phase 1, whose shipped contract (`.claude/agents/phase-1-tdd.md`
line 15, `SKILL.md` Step 5b) says the exact opposite — "light/trivial work **omits
`## Contract` entirely**" and "a *derived* band rule is **deferred to D3 (gated on
Trial E); do not try to systematize the call now**." The change makes the shared
template self-contradictory across the two consuming skills and pre-empts a documented
deferral. This is decision-weight (cross-cutting + externally-visible guidance change)
and was NOT recorded in `open_decisions`. It blocks until the operator chooses how to
scope the "mandatory" framing.

Everything else passes: the TDD shape is sound (verified RED-at-HEAD / GREEN-with-draft
in a throwaway tree), honest-minimal holds (no module), execution-scope matches, and the
prose is otherwise faithful to D3.

---

## Live-contract basis (judged on the contract, not the constructor's claims)

- Authoritative node: `workflows/cairn-intent.yaml` `load-or-form-intent` evidence
  `contract-floor` = "One-line scope statement plus must-satisfy floor" (line 47).
- ADR `docs/adr/intent-management-loop.md` D3 (lines 66–70).
- Tag source of truth: `scripts/lib/atomicity.EXCEPTION_TAGS` (lines 14–16).
- Live HEAD `templates/intent.md` `## Contract` header (lines 76–84): "OPTIONAL …
  Omit this entire block for light/trivial work (the cost-model m2 fix)."
- Live HEAD `.claude/agents/phase-1-tdd.md` line 15 + `.claude/skills/cairn-tdd-feature/SKILL.md`
  Step 5b: `## Contract` optional, omitted for light work, derived band deferred to D3.

I did NOT rely on the constructor's `intent-challenge.md` verdict; I re-derived
RED/GREEN and the tag/token facts independently.

## Per must-satisfy clause

1. **"where heavy intent work, the template shall document all four exception tags as
   the depth-graduation dial" (except universal-set)** — PASS. All four tags present
   in the proposed `## Contract` (verified `all(t in tmpl)` against `EXCEPTION_TAGS`);
   framed as the graduation dial (lines 91–98, 124–135). Caveat: this assertion is
   ALREADY green at HEAD (the live template documents all four tags), so the
   corresponding test function is not uniquely RED-at-HEAD — see Evidence note.

2. **"the template shall require a one-line scope-statement as the contract
   completeness floor"** — PASS on its face (lines 84–89: "Every contract carries a
   one-line `scope-statement:`"). BUT the *requirement* is realized via the contested
   "mandatory / never omitted" framing (see finding F1). The clause holds; its
   realization is what's blocked.

3. **"when contract depth changes, the template shall describe graduation from a
   one-line must-satisfy clause up to full EARS grammar plus premise grounding"
   (except regression-meta)** — PASS. Lines 91–98 describe TRIVIAL (scope-statement +
   one bare clause) → MEDIUM/HEAVY (full grammar + `## Premise Grounding`). The two
   worked YAML examples (trivial, heavy) instantiate it. Regression baseline (eight
   headings + Contract + Premise Grounding blocks) preserved — confirmed via the
   existing extraction tests staying green.

4. **"the new unit test shall assert templates/intent.md carries the scope-statement
   token"** — PASS. `test_scope_statement_completeness_floor_required` asserts
   `"scope-statement" in section` (and `"completeness floor"`). Verified GREEN with the
   draft, RED at HEAD (the token is absent from the live template).

5. **"the new unit test shall assert the four exception-tag names are present in
   templates/intent.md" (except universal-set)** — PASS as written
   (`test_four_exception_tags_documented_match_live_tag_set`). Note: this asserts
   against the `## Contract` *section* (not whole file) and imports the live
   `EXCEPTION_TAGS`, so it stays parity-correct. It is the one test function that is
   GREEN at HEAD too (live Contract block already lists all four) — redundant with the
   existing `test_intent_template_contract_tags_match_exception_tags`. The intent
   discloses this honestly (Verification lines 82–84). Not a defect.

## Per must-not-violate clause

- **"the eight Phase-1 schema headings stay present and in order"** — PASS.
  `test_intent_template_shape_and_eight_headings` (existing) ran GREEN against the
  proposed template in the throwaway tree.
- **"no hard cardinality gate or mechanical contract-depth enforcement is introduced"**
  — PASS. The draft adds prose + a test only; no gate. The template explicitly states
  the mechanical gate does NOT enforce the floor or depth (lines 103–106).
- **"the four tag names in the template equal scripts/lib/atomicity.EXCEPTION_TAGS
  exactly"** — PASS. Confirmed equal; the existing parity test still green.
- **"no code, hook, or validator assertion is modified (template plus test only)"** —
  VIOLATED-IN-SPIRIT. No `.py` hook/validator is touched, so the literal clause holds.
  But the draft silently changes BEHAVIOURAL GUIDANCE that the live
  `cairn-tdd-feature` Phase 1 agent depends on (the "omit `## Contract` for light work"
  rule). The clause's intent — "don't change anything beyond additive template
  guidance for the cairn-intent loop" — is breached: this is a REPLACE (delete
  "OPTIONAL"/"omit") not an ADD, and it reaches a second consumer. This is the block.

## Per wrong-if clause

- "frames the scope-statement as optional rather than required" — the draft frames it as
  required (not the wrong-if). But it does so by also reframing the *whole Contract
  block* as mandatory, which is the over-reach in F1.
- "graduation prose implies/adds a cardinality or diff-size gate" — NOT triggered;
  prose explicitly says no gate.
- "redefines a tag name or declaration rule instead of citing atomicity.py" — NOT
  triggered; tags are cited, semantics unchanged.
- "the new test passes while the template guidance contradicts ADR D3" — NOT triggered
  against D3. The contradiction is with `phase-1-tdd` (a different ADR surface,
  `intent-contract-cost-model` D4 / the Trial-E deferral), which the wrong-if list does
  not anticipate.

## Per escalate-when clause (constructor's own triggers)

- **"the template needs a STRUCTURAL change … to carry the graduation guidance — that
  is decision-weight, surface to operator"** — FIRED, and the constructor wrongly
  judged it did not. The draft adds `scope-statement` as a SEVENTH contract clause-key
  (it appears in both worked YAML examples and the clause-list, while the prose still
  says "Six clause-lists" / "full six-clause grammar"). Adding a new contract grammar
  key to a shared, schema-shaped template is a structural change. Combined with the
  optional→mandatory flip, the escalate-when trigger should have fired.

## Honest-minimal

CONFIRMED. No Python module introduced. The only `.py` artifact is a grep/parse unit
test that imports the existing `lib.atomicity.EXCEPTION_TAGS`. No per-subagent module,
no new caller. Matches the brief.

## Evidence adequacy & TDD shape (independently verified)

Built a throwaway tree `_check/` mimicking repo layout (live `scripts/lib/atomicity.py`,
proposed template + test) and a `_check_red/` with the live HEAD template, ran pytest,
then deleted both trees.

- Proposed test vs proposed template: **5 passed**.
- Existing `test_template_extraction.py` intent.md tests vs proposed template
  (ADD-not-REPLACE): **3 passed** (eight-headings-in-order, parseable-Contract,
  tag-parity all green).
- Proposed test vs LIVE HEAD template: **4 failed, 1 passed** — genuine RED. The 4
  RED functions (`scope_statement_floor`, `graduation_rule`,
  `floor_is_subagent_enforced`, `trivial_worked_example`) prove the increment delivers
  real new coverage. The 1 GREEN-at-HEAD function is the tag-name assertion (redundant,
  disclosed).
- Intent's OWN `## Contract` `must-satisfy` runs clean through
  `lib.atomicity.check_clauses` (no offences) — the intent itself is gate-valid.

Evidence is adequate for a template-guidance + regression-test increment. The grep-based
test cannot catch semantic wrongness — which is exactly where F1 lives.

## Scope check

execution-scope = `templates/intent.md` + `tests/unit/test_intent_template_graduated_contract.py`
— matches the brief's canonical landing targets and the intent's declared scope. The
dist mirror `plugins/cairn/templates/intent.md` is correctly out of scope (regen is a
separate step). No scope creep on the file list. The OVER-REACH is within
`templates/intent.md` content, not the file set.

## Open decisions

The constructor surfaced NONE (intent + intent-challenge both say "None"). I re-flag one
the constructor missed:

**OD-1 (cross-cutting, blocking): the shared `templates/intent.md` "mandatory / never
omitted" reframing collides with `cairn-tdd-feature`.** One template file feeds two
skills. D3's "contract mandatory" is a `cairn-intent` rule; `cairn-tdd-feature`'s live
contract keeps `## Contract` optional and explicitly DEFERS the derived band rule to "D3
(gated on Trial E)." Flipping the shared template to "mandatory for every repo-writing
session / never omitted" applies D3 to `cairn-tdd-feature` before its retirement and
contradicts `phase-1-tdd.md` line 15 + `SKILL.md` Step 5b.
- **Proposed default:** keep the additive D3 guidance, but SCOPE the "mandatory" wording
  to the `cairn-intent` loop (e.g. "Under the `cairn-intent` loop, a contract is
  mandatory … ; `cairn-tdd-feature` keeps the light/heavy band call — `## Contract`
  remains omittable for light work, fail-open"). Retain HEAD's "OPTIONAL" /
  "omit for light work" sentence for the four-phase reader. The mechanical default
  (fail-open + `CAIRN_CONTRACT_REQUIRED=1`) is already unchanged and should stay.
- **Tradeoff:** the per-loop hedge makes the shared template wordier and slightly
  two-voiced; the alternative (one unconditional "mandatory") is cleaner prose but
  silently changes four-phase behaviour and pre-empts a deferral the operator owns. The
  intent's own Explicit Scope-Out names "making `## Contract` mandatory by default … a
  separate `/decision`" — so this is operator territory by the constructor's own line.

**OD-2 (minor, non-blocking): `scope-statement` as a new contract key + the stale "Six
clause-lists" count.** The draft adds `scope-statement:` as a contract key (now seven
keys) but the header still reads "Six clause-lists" and GRADUATION says "full six-clause
grammar." Either renumber to seven, or document `scope-statement` as the floor that sits
above the six lists. Fix in the same edit once OD-1 is resolved.

## Required rework before close

1. Resolve OD-1: per-loop-scope the "mandatory / never omitted" wording so the shared
   template does not contradict `phase-1-tdd.md`/`SKILL.md` or pre-empt the Trial-E
   deferral. (Operator decision.)
2. Fix OD-2: reconcile the "Six clause-lists" count with the added `scope-statement`
   key.
3. Re-run the proposed test (must stay GREEN) and the existing `test_template_extraction`
   intent.md tests (must stay GREEN) after the rewording.

## Residual risk if shipped as-is

A `cairn-tdd-feature` Phase 1 reader, reading the same template, would believe a
`## Contract` block is mandatory and the scope-statement is never omitted — directly
against its own agent contract and the recorded Trial-E deferral. Silent
guidance-divergence across two skills sharing one file is exactly the "passes CI,
semantically wrong" failure the intent's own Risk Surface names; the grep test goes
green on it.
