# Intent challenge — intent-template-operator-prompt

Front-loaded skeptic, fresh context. One premise; `premise_guard` exit 0 (quote
verbatim-grounded). Challenge is the semantic gap the guard cannot see.

## premise-source-checks

**Premise (label):** "D3 keeps depth/size enforcement subagent-side … no
mechanical cardinality gate — so gh#28 #3 (validator rejects oversize) is
out-of-scope here." Source `docs/adr/intent-management-loop.md`.

Read lines 66-70 (D3). Verbatim: *"The completeness floor = a one-line
scope-statement … + the close-review smell-testing contract-**depth** against
diff size. No hard **cardinality** gate."* Cross-read the test gloss
`tests/unit/test_intent_template_graduated_contract.py:7` — *"NO hard
cardinality gate — enforcement lives in the subagents, not in a mechanical
**clause-count** check."* So in-repo, "cardinality gate" = a clause-count check
on **contract depth**.

gh#28 #3, `docs/operator-field-notes-2026-05-10.md:56`: *"Hard length caps with
per-section caps in the intent template."* Target = **byte/line length of
artifact prose**, not contract clause-count.

Eight-heading coupling: `test_template_extraction.py:110-130` cursor-walks the
body for eight headings in order; an inserted `## Operator Prompt` before
`## What` is skipped, stays GREEN. No script/validator counts headings (grep of
`scripts/`, `checks/` — only the two tests parse the template). Additive
heading is test-safe.

## semantic-counterfactual-search

**CF-1 (the decisive one): "no cardinality gate" → "#3 out-of-scope" is an
over-read.** Counterfactual: the grounded quote is true (D3 bars a *cardinality*
gate on contract depth) AND a per-section *length* cap is still reconcilable
with D3 — because length ≠ cardinality and artifact-prose ≠ contract-depth.
This reading **holds against source**: D3's span governs contract clause-depth
via subagent smell-test; it says nothing barring a byte/line cap on prose. The
intent's `label:` and Boundary silently widen "no **cardinality** gate" to "no
mechanical gate on **depth/size**," folding gh#28 #3's domain (size) into a
prohibition the quote only states for cardinality.

*Mitigating read:* the intent does not claim D3 *forbids* #3 — it scopes #3 OUT
as "needs its own consideration." Scoping-out for separate governance is the
conservative direction and does not block construction of *this* additive
section. The defect is in the *justification* (claims a D3 conflict that the
source does not establish), not in the *exclusion* itself. The fix is a one-line
re-word, not a scope change.

**CF-2 (governance / escalate-when): does the addition need ADR/schema-amend
first?** Counterfactual attempted: the section is a schema amendment requiring
governance. Held? **No.** The authoritative shape source
(`.claude/agents/phase-1-tdd.md:13`) frames intent shape as frontmatter → eight
sections → two optional *trailing* blocks; a *pre-What verbatim-input* section
is new shape. BUT D3 explicitly carves the cairn-intent-loop template as
in-scope build surface, the change is additive and test-pinned, and
`escalate-when` already routes the call to the operator (operator-bound). No
hard block. **Finding, not block:** the intent must also touch
`.claude/agents/phase-1-tdd.md` and the template's own comment (lines 8-18,
"the eight body section headings … required by the derive-don't-fabricate
contract") or the derive-exempt carve-out the intent's own FLI fears will leak —
the authoritative shape source and template comment still say "eight … derived,"
unaware of a ninth exempt section. `execution-scope` lists only
`templates/intent.md` + one test, omitting the shape source. This is a real
under-scope.

**CF-3 (scope honesty):** one section + one new assertion matches the additive
contract depth; not padded. Adequate.

## verdict

**challenge-blocked** (sustainable, narrow). Two source-grounded defects:
(1) the premise `label:`/Boundary over-read D3's "no **cardinality** gate" into
"no mechanical depth/**size** gate," asserting a D3↔gh#28-#3 conflict the quoted
span does not support; (2) `execution-scope` omits the authoritative shape
source `.claude/agents/phase-1-tdd.md` and the template's own "eight … derived"
comment, so the derive-exempt carve-out the intent's FLI fears would leak is left
contradicting the very contract it claims to preserve. Both are cheap revisions,
not a redesign.

Challenged premise: the single D3 premise.

## verification note (re-challenge)

Revised intent re-read. **CF-1 resolved:** premise `label:` (line 89) now reads
"no clause-count cardinality gate (silent on per-section prose length caps)" —
faithful to the source span; Boundary (35-37) + Scope-Out (76-78) scope gh#28 #3
out as separable, decision-weight, routed to its own /decision. Manufactured
D3-conflict gone. **CF-2 resolved:** `.claude/agents/phase-1-tdd.md` added to
`execution-scope` (114); Specification (47-54) requires amending its "Intent
shape" paragraph + binding derive-don't-fabricate to the eight + naming the
section in the template comment — carve-out reconciled in the authoritative
source. Residual (note, not block): `wrong-if` still references only "the eight"
derived sections; once phase-1-tdd.md is amended the carve-out lives in two
places the close-review must check stay in sync. **Verdict: challenge-pass.**
