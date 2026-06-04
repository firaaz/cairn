# Intent Challenge: trial-e-dp5-field-notes-sink

## Verdict

challenge-pass.

The intent survives the front challenge. `premise_guard` exited 0 for
`.claude/skill-runs/trial-e-dp5-field-notes-sink/intent.md`, and the cited
quotes are live. The semantic attack found a stale close-sink contract, not an
intentional requirement that Trial-E felt-cost observations continue going to
`docs/dogfood-log.md`.

No construction should start until operator sign-off, but there is no premise
blocker.

## Premise Source Checks

- P1 canonical close envelope: PASS. `workflows/cairn-intent.yaml:235-240`
  lists the `close` node operator write envelope and permits
  `^docs/dogfood-log\.md$`.
- P2 plugin workflow mirror: PASS. `plugins/cairn/workflows/cairn-intent.yaml:235-240`
  lists the same close write-envelope sink.
- P3 Claude Step 6: PASS. `.claude/skills/cairn-intent/SKILL.md:72` says to
  record the Trial-E observation to `docs/dogfood-log.md`.
- P4 operator field notes: PASS. `docs/operator-field-notes-2026-06-02.md:131-134`
  says dp3 was recorded in dated field notes and calls the current Step 6
  dogfood-log target envelope-denied and schema-mismatched. The same file at
  `:154-160` records dp4 felt cost and again says the observation sink is still
  these field notes rather than the workflow dogfood-log close sink.
- Additional support: `docs/operator-field-notes-2026-06-01.md:54-61` says
  dogfood-log has a rigid defense-catch schema and does not fit Trial-E
  felt-cost narrative; `docs/operator-field-notes-2026-06-01.md:140-142` says
  the sink mismatch persisted after dp2.
- Dogfood-log schema check: `docs/dogfood-log.md:8-9` requires fenced YAML
  entries with `slice`, `date`, `defense`, `type`, `description`,
  `would-manual-have-caught`, and `disposition`, supporting the schema-mismatch
  premise.
- ADR grounding: `docs/adr/intent-management-loop.md:87-93` makes D7 retirement
  a future firm supersession and `:110-116` says coexistence has no forced
  migration. The ADR does not name `docs/dogfood-log.md` as the Trial-E sink.

## Semantic Counterfactual Search

1. Counterfactual: `docs/dogfood-log.md` is intentionally the Trial-E sink
   despite field-note usage.

   Blocked. The only live sources found that send Trial-E observations to
   dogfood-log are the current close envelope and Claude Step 6, which are the
   exact surfaces under challenge. The dated field notes contain all live
   Trial-E data points found by search and repeatedly call the dogfood-log
   target a sink mismatch. The dogfood log itself contains only the older
   defense-catch schema, not Trial-E felt-cost/co-miss entries.

2. Counterfactual: the plugin workflow mirror should diverge from the canonical
   workflow.

   Blocked. The plugin workflow currently matches the canonical close envelope
   exactly. The Claude skill says the Claude and Codex surfaces drive the same
   workflow nodes and must agree on node ids, verdict statuses, and evidence ids
   (`.claude/skills/cairn-intent/SKILL.md:8`). The Codex skill points at
   `workflows/cairn-intent.yaml` but is currently silent on the observation
   sink, so adding explicit dated-field-note close prose is a construction
   requirement, not a divergence blocker.

3. Counterfactual: changing the close envelope implies a dogfood-log migration
   or D7 retirement ADR.

   Blocked. `intent-management-loop` D7 says retirement is separate and future;
   its consequences say there is no forced migration and `cairn-tdd-feature`
   remains the fallback. Switching the close observation sink leaves
   `docs/dogfood-log.md` unchanged as the older structured log. A D7 ADR would
   be required only for retiring `cairn-tdd-feature`; a migration decision would
   be required only if this slice tried to repurpose or rewrite dogfood-log.

## Blockers

None.

Notes:
- `uv run python checks/premise_guard.py ...` needed sandbox escalation for uv
  cache access, then passed.
- `git status --short` reported an fsmonitor IPC warning and pre-existing
  untracked skill-run paths. No implementation files or tests were edited by
  this challenge.

## Final JSON

{"status":"challenge-pass","challenged_premises":["canonical close envelope currently permits docs/dogfood-log.md","plugin workflow mirror currently permits docs/dogfood-log.md","Claude Step 6 currently sends Trial-E observations to docs/dogfood-log.md","operator field notes record the live sink mismatch"],"cited_evidence":["premise_guard exit 0","workflows/cairn-intent.yaml:235-240","plugins/cairn/workflows/cairn-intent.yaml:235-240",".claude/skills/cairn-intent/SKILL.md:72","docs/operator-field-notes-2026-06-01.md:54-61","docs/operator-field-notes-2026-06-01.md:140-142","docs/operator-field-notes-2026-06-02.md:131-134","docs/operator-field-notes-2026-06-02.md:154-160","docs/dogfood-log.md:8-9","docs/adr/intent-management-loop.md:87-93","docs/adr/intent-management-loop.md:110-116"],"blocked_counterfactuals":["docs/dogfood-log.md is intentionally the Trial-E felt-cost sink despite all live Trial-E observations being in dated field notes","the plugin workflow mirror should diverge from the canonical close sink","changing the close observation envelope requires a dogfood-log migration or D7 retirement ADR"]}
