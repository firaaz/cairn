---
id: intent-template-operator-prompt
name: Pin operator prompt verbatim in the intent template
snapshot-sha: 26d00c1
invariants-touched: []
---

## Operator Prompt
<!-- Verbatim initiating framing, pinned for cold-read recovery. Exempt from
derive-don't-fabricate (this is pinned input, not Phase-1 derivation). -->
> Vehicle: gh#28 — "Intent.md template tightening: pinned operator prompt +
> per-section length caps". First Trial-E felt-cost dry-run of the loop
> (activate-first dogfood). Form the intent from the gh#28 body, scope to
> in-session, surface for explicit confirmation before construction. Track
> felt-cost vs four-phase and watch for any semantic-grounding leak; record to
> docs/operator-field-notes-2026-06-01.md at close.

## What
Add a pinned, verbatim `## Operator Prompt` section to `templates/intent.md`
so the operator's original framing survives at the top of every intent
artifact. Under the cairn-intent loop the operator signs off twice — at intent
approval and at close-review, often hours apart — and a cold-read at the second
gate has no anchor to the first. The pinned prompt restores framing without
re-deriving it.

## Why
gh#28 failure 1: "Context broken at review — operator cold-reads the intent
without remembering original framing" (source: `docs/operator-field-notes-2026-05-10.md`).
The gap is structural to the loop's two-sign-off shape (`intent-management-loop`
D2). gh#28 mitigation 2 (pin operator prompt verbatim) is the direct fix.

## Boundary
Does NOT add per-section length caps (gh#28 mitigation 3). A validator-enforced
length cap is a separable, decision-weight choice: it introduces a mechanical
gate that cuts against D3's subagent-enforcement model. D3 bars only a
clause-count *cardinality* gate on contract depth — it is silent on a prose
length cap — so #3 is a new decision, not a D3-settled one, and belongs in its
own /decision. Does NOT change the four-phase Phase-1 dispatch prompt
(mitigation 1) or document a cheap-re-runs discipline (mitigation 4). Additive.

## Specification
- `templates/intent.md` gains a `## Operator Prompt` section placed before
  `## What`, holding the operator's initiating framing **verbatim** (block-quoted).
- Its guidance states the section is **exempt from the derive-don't-fabricate
  contract** (pinned input, not Phase-1 derivation) and is the cold-read anchor
  for both sign-off gates.
- `.claude/agents/phase-1-tdd.md` (the authoritative shape source) is amended:
  its "Intent shape" paragraph describes the verbatim-pinned, derive-exempt
  `## Operator Prompt` as the leading section before the eight, and its
  "derive, don't fabricate" contract is clarified to bind only the eight derived
  sections — reconciling the carve-out in the authoritative source, not only the
  template.
- The template's internal shape comment (`templates/intent.md` lines 8-18) names
  the new section's verbatim / derive-exempt status.
- The eight existing schema headings remain present and in order.

## Verification
- New assertion in `tests/unit/test_intent_template_graduated_contract.py`:
  `templates/intent.md` contains `## Operator Prompt` positioned before `## What`,
  with the verbatim + derive-exempt guidance prose.
- `uv run pytest tests/unit/test_template_extraction.py tests/unit/test_intent_template_graduated_contract.py -v` GREEN (existing eight-heading + contract assertions unchanged).
- Full `uv run pytest` + `uv run python scripts/validate_architecture.py` GREEN.

## Risk Surface
The pin section becomes a vibes-graded dumping ground (the exact failure 2 gh#28
names), or the derive-exempt carve-out leaks and Phase 1 stops deriving the eight
sections. Neither surfaces as a test failure — a wording/discipline risk the
close-review must smell-test.

## Feature-Local Invariants
The `## Operator Prompt` section is verbatim-input-only and derive-exempt; the
eight derived schema headings stay mandatory-and-derived. Adding the pin must
not soften the derive-don't-fabricate contract on the eight.

## Explicit Scope-Out
- Per-section length caps (gh#28 #3) — separable and decision-weight (a
  validator gate vs D3's subagent-enforcement model; D3's no-cardinality-gate is
  silent on prose length); needs its own /decision, not bundled here.
- `commands/claude-code/cairn-tdd-feature.md` Phase-1 prompt tightening (gh#28 #1).
- Cheap-re-runs-over-interactivity documentation (gh#28 #4).

## Premise Grounding
```yaml
premises:
  - source: docs/adr/intent-management-loop.md
    quote: |
      the close-review smell-testing contract-depth against diff size. No hard
      cardinality gate.
    label: "D3 enforces contract-depth via the close-review smell-test against diff size, with no clause-count cardinality gate (silent on per-section prose length caps)"
```

## Contract
```yaml
scope-statement: pin the operator's verbatim framing at the top of templates/intent.md so a cold-read at either sign-off gate restores original framing
must-satisfy:
  - the intent template shall carry a `## Operator Prompt` section positioned before the `## What` heading
  - the `## Operator Prompt` guidance shall state the section is verbatim-pinned and exempt from the derive-don't-fabricate contract
  - clause: the eight schema headings shall remain present and in order after the change
    except: "regression-meta: baseline is test_template_extraction.test_intent_template_shape_and_eight_headings, currently GREEN"
must-not-violate:
  - INV-003 four-phase contract — phase count, names, roles, and the eight derived headings' derive-don't-fabricate requirement are untouched
wrong-if:
  - the derive-exempt carve-out is worded so it could apply to any of the eight derived sections
  - the new section is added after `## What` or out of position
escalate-when:
  - clause: the front-challenge finds the intent-template schema addition requires ADR / schema-amendment governance before construction
    except: "operator-bound: operator decides whether to route to /decision or proceed"
evidence:
  - tests/unit/test_intent_template_graduated_contract.py new assertion GREEN
  - tests/unit/test_template_extraction.py eight-heading assertion still GREEN
  - full uv run pytest + scripts/validate_architecture.py GREEN
execution-scope:
  - templates/intent.md
  - .claude/agents/phase-1-tdd.md
  - tests/unit/test_intent_template_graduated_contract.py
```
