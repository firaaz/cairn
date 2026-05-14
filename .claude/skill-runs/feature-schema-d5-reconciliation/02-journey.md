# Phase 0.5 — User-journey trace

## Stage 1: Feature creation

**Mechanism:** `commands/claude-code/start-slice.full.md:130-149` — operator creates the feature file. Prescribed shape: `id, name, intent, shaped-from, created, slices: [{id, added}]`.

**Fields written:** `id`, `name`, `intent`, `shaped-from`, `created`, `slices`.

**NARROW impact:** orchestrator-paths.yaml must add `intent:` + `shaped-from:`, rename `charter:` → `intent:`. One rename + one new field. No tooling breaks.

**WIDEN impact:** D5 must enumerate `charter:`, `status:`, `tracking:`, `predecessor:`, `lesson:`, `audit-findings:`, `out-of-scope:` as permitted. Template needs update.

## Stage 2: Slice planning

**Mechanism:** `start-slice.full.md:94-128` reads `slice.yaml`, not the feature file. `cairn-tdd-feature` reads plan docs (`docs/plans/<feature>.md`), not feature file.

**Fields read:** none from `.claude/features/*.yaml`.

**NARROW impact:** none. **WIDEN impact:** none.

## Stage 3: Slice execution (Phases 1-4)

**Mechanism:** Phase agents read `intent.md` (skill-runs artifact), not feature files.

**Fields read:** none. **NARROW impact:** none. **WIDEN impact:** none.

## Stage 4: Slice close

**Mechanism:** `start-slice.full.md:244-255`. Slice entry `{id, added}` appended to `slices:` when new slice starts.

`test_feature_file_schema.py:73-76` enforces slice `status:` may only be `"dropped"`. **orchestrator-paths.yaml uses `status: phase-1` in its slice entry — violates this rule** (synthetic-test-only currently, but a real bug if extended to live files).

**NARROW impact:** orchestrator-paths.yaml's `status: phase-1` slice entry is independently a violation; needs removal or `test_feature_file_schema.py` extension.

**WIDEN impact:** would need to permit `status: phase-1` in slice entries — contradicts existing schema rule.

## Stage 5: Handoff and catchup

**Mechanism:** `commands/claude-code/catchup.md` reads `.claude/handoff.md`, `git log`, etc. — does **not** read `.claude/features/*.yaml`.

**Fields read:** none. **NARROW impact:** none. **WIDEN impact:** none.

## Stage 6: ADR and lesson capture

**Mechanism:** No post-M4 mechanism reads `intent:` / `shaped-from:` from feature file → ADR / lesson.

**NARROW impact:** none in current state; future automation that reads `intent:` would catch missing intent on orchestrator-paths.

**WIDEN impact:** must define whether `charter:` semantically satisfies the intent role.

## Boundary mechanism summary

| Boundary | Field read | NARROW breaks? | WIDEN breaks? |
|---|---|---|---|
| Stage 1: feature file creation template | id, name, intent, shaped-from prescribed | Yes — orchestrator-paths must add intent + shaped-from, rename charter | No — existing fields preserved |
| Stage 2: slice planning | none (reads plan doc) | No | No |
| Stage 3: phase execution | none (reads intent.md) | No | No |
| Stage 4: slice close / append | id, added per entry; status: dropped only | Partial — orchestrator-paths has status: phase-1 (independent violation) | Same violation unless schema widened |
| Stage 5: handoff/catchup | none | No | No |
| Stage 6: ADR/lesson capture | none | No | No |
| test_identifier_scheme_contract.py | id, name (live files) | No — orchestrator-paths has both; intent NOT checked here | No |
| test_feature_file_schema.py | id, intent, created, slices[] (synthetic only) | Would fail if extended (missing intent) | Would need widening for slice status |

## Stages where orchestrator-paths.yaml's extra fields ARE used

All operator-readable prose only — **no programmatic reader found**.

- `tracking:` → human pointer to GH #24
- `predecessor:` → narrative provenance
- `lesson:` → L-017 cross-reference
- `audit-findings:` → F-03x list
- `out-of-scope:` → scoping prose
- top-level `status: in-progress` → lifecycle indicator

## Stages where extra fields are UNUSED

All six extra fields are unused at every automated stage. Only live automated enforcement: `test_identifier_scheme_contract.py` (passes for orchestrator-paths) and `test_feature_file_schema.py` (synthetic only; would fail on missing `intent:` and slice-entry `status: phase-1`).

## Decision data

**Under NARROW:** rename `charter:` → `intent:`, add `shaped-from: null`, fix or relocate `status: phase-1` from slice entry. 6 extra fields have no tooling dependents — keep as unvalidated prose, move to comment, or relocate.

**Under WIDEN:** D5 must permit `charter:` as alias and canonize top-level `status:`. Slice-entry `status: phase-1` is an independent violation regardless of top-level policy.
