---
id: trial-e-dp5-field-notes-sink
name: Trial-E dp5 field notes close sink
snapshot-sha: 8e115193670a7b5b5ba3aa95f71fd96c1b3a6373
invariants-touched: []
---

## Operator Prompt
> A previous agent produced the plan below to accomplish the user's task. Implement the plan in a fresh context. Treat the plan as the source of user intent, re-read files as needed, and carry the work through implementation and verification.
>
> # Trial-E dp5: Make Field Notes the `cairn-intent` Close Sink
>
> ## Summary
> Run one maintainer-only real dogfood slice through `cairn-intent` with feature id `trial-e-dp5-field-notes-sink`. The change fixes a live loop defect: Trial-E close observations currently point to `docs/dogfood-log.md`, whose schema is for older defense-catch entries, while all Trial-E observations are actually recorded in dated operator field notes.
>
> ## Key Changes
> - Form `.claude/skill-runs/trial-e-dp5-field-notes-sink/intent.md` and run the normal `cairn-intent` loop: front challenge, operator sign-off, test-first implementation, close-review, final close.
> - Update the close sink contract so Trial-E observations go to `docs/operator-field-notes-YYYY-MM-DD.md`.
> - Keep `docs/dogfood-log.md` unchanged; it remains the structured cliff-defense dogfood log, not the Trial-E felt-cost sink.
> - Update the Claude-side `cairn-intent` skill, canonical `workflows/cairn-intent.yaml`, plugin workflow mirror, and Codex `cairn-intent` skill text so both hosts agree on the close behavior.
> - In workflow close write envelopes, replace the dogfood-log path with a dated field-note regex such as `^docs/operator-field-notes-[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$`.
>
> ## Test Plan
> - Add a focused workflow test asserting the `close` node permits dated operator field notes and no longer permits `docs/dogfood-log.md`.
> - Add a skill conformance test asserting the Claude `cairn-intent` Step 6 names operator field notes, not `docs/dogfood-log.md`.
> - Add or extend plugin conformance coverage so the plugin workflow mirror has the same close sink path.
> - Run focused tests for cairn-intent workflow/skill/plugin conformance, then run `uv run pytest` and `uv run python scripts/validate_architecture.py`.
>
> ## Assumptions
> - Audience is maintainer-only; no consumer distribution, D7 retirement ADR, or dogfood-log schema migration in this slice.
> - The dated field notes are the canonical Trial-E observation sink.
> - The slice records dp5 felt cost, checkpoint catch/miss behavior, and any co-miss signal in `docs/operator-field-notes-2026-06-02.md` unless implementation occurs on a later date, in which case use that date.

## What
Change the `cairn-intent` close contract so Trial-E observations are recorded in dated operator field notes instead of `docs/dogfood-log.md`.

## Why
Trial-E dogfood already records observations in `docs/operator-field-notes-YYYY-MM-DD.md`; the current close envelope and skill prose point at a schema-mismatched dogfood log.

## Boundary
Do not migrate `docs/dogfood-log.md`, retire `cairn-tdd-feature`, create a D7 retirement ADR, or change consumer distribution behavior.

## Specification
- The canonical `close` node write envelope permits `^docs/operator-field-notes-[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$`.
- The canonical `close` node write envelope does not permit `^docs/dogfood-log\.md$`.
- The plugin workflow mirror uses the same close write envelope sink as the canonical workflow.
- Claude-side Step 6 records the Trial-E observation to `docs/operator-field-notes-YYYY-MM-DD.md`.
- The Codex `cairn-intent` skill names the same dated field-notes close sink.
- `docs/dogfood-log.md` remains unchanged.

## Verification
- `uv run pytest tests/unit/test_cairn_intent_workflow.py tests/unit/test_cairn_intent_skill_conformance.py tests/unit/test_codex_plugin_manifest.py -v`
- `uv run pytest -v`
- `uv run python scripts/validate_architecture.py`
- `git diff -- docs/dogfood-log.md` shows no diff.

## Risk Surface
The tests can prove path/prose conformance while missing an operator-experience defect where close records still fail to collect useful Trial-E felt-cost and co-miss observations.

## Feature-Local Invariants
- Trial-E observation writes target dated operator field notes.
- The canonical workflow and plugin workflow mirror agree on the close sink.
- The old dogfood log remains untouched by this slice.

## Explicit Scope-Out
- No `docs/dogfood-log.md` schema migration.
- No four-phase retirement or D7 supersession ADR.
- No changes outside the named close-sink surfaces and dp5 records.

## Premise Grounding

```yaml
premises:
  - source: workflows/cairn-intent.yaml
    quote: |
      - ^docs/dogfood-log\.md$
    label: "canonical close write envelope currently permits docs/dogfood-log.md"
  - source: plugins/cairn/workflows/cairn-intent.yaml
    quote: |
      - ^docs/dogfood-log\.md$
    label: "plugin workflow mirror currently permits docs/dogfood-log.md"
  - source: .claude/skills/cairn-intent/SKILL.md
    quote: |
      6. **Close (`close` node, current conversation).** Record the close: write `<workspace>/close.md` (intent pointer, final verification, residual risk if accepted), append a handoff pointer to `.claude/handoff.md`, and record the Trial-E observation (felt cost vs four-phase; any correlated-miss signal) to `docs/dogfood-log.md`. Run the final verification command and confirm GREEN before recording.
    label: "Claude Step 6 currently sends Trial-E observations to docs/dogfood-log.md"
  - source: docs/operator-field-notes-2026-06-02.md
    quote: |
      - **Sink unchanged.** dp3 recorded here, not `docs/dogfood-log.md`; `cairn-intent` `SKILL.md:72`
        Step 6 still points Trial-E observations at the envelope-denied, schema-mismatched dogfood-log.
    label: "operator field notes record the live sink mismatch"
```

## Contract

```yaml
scope-statement: switch the cairn-intent close observation sink from dogfood-log to dated operator field notes across canonical, Claude, and plugin surfaces
must-satisfy:
  - when the close node write envelope is checked, the workflow shall permit dated operator field notes
  - when the close node write envelope is checked, the workflow shall reject docs/dogfood-log.md
  - when Claude Step 6 is checked, the skill shall name dated operator field notes as the Trial-E observation sink
  - when the plugin mirror is checked, the mirror shall match the canonical close sink
  - when Codex cairn-intent guidance is checked, the skill shall name dated operator field notes as the Trial-E observation sink
must-not-violate:
  - docs/dogfood-log.md remains unchanged
  - cairn-tdd-feature remains the retained fallback
wrong-if:
  - docs/dogfood-log.md remains in either close node write envelope
  - Trial-E observation sink guidance is absent from either cairn-intent skill surface
escalate-when:
  - changing the sink requires a dogfood-log schema migration
  - changing the sink requires a D7 retirement decision
evidence:
  - focused workflow, skill, and plugin conformance tests pass
  - full pytest passes
  - architecture validation passes
  - dp5 is recorded in docs/operator-field-notes-2026-06-02.md
execution-scope:
  - .claude/skill-runs/trial-e-dp5-field-notes-sink/intent.md
  - .claude/skill-runs/trial-e-dp5-field-notes-sink/intent-challenge.md
  - .claude/skill-runs/trial-e-dp5-field-notes-sink/close-review.md
  - .claude/skill-runs/trial-e-dp5-field-notes-sink/close.md
  - .claude/handoff.md
  - .claude/skills/cairn-intent/SKILL.md
  - workflows/cairn-intent.yaml
  - plugins/cairn/workflows/cairn-intent.yaml
  - plugins/cairn/skills/cairn-intent/SKILL.md
  - tests/unit/test_cairn_intent_workflow.py
  - tests/unit/test_cairn_intent_skill_conformance.py
  - tests/unit/test_codex_plugin_manifest.py
  - docs/operator-field-notes-2026-06-02.md
```
