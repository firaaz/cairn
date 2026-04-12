# /start-slice

Begin or advance a slice through Intent → Validation → Implementation → Integration.

Usage: `/start-slice` (new) | `/start-slice phase 2|3|4` (advance) | `/start-slice complete` (finish) | `/start-slice failed` (archive)

## Rules

1. Read `.slice-system/docs/operational-reference.md` for target phase.
2. Read `.claude/current-slice/slice.yaml` for current state. Missing = new slice.
3. Phase 1: write intent.md (YAML envelope + what/why/spec + verification). No source reads (greenfield) or public interfaces only (modification).
4. Phase 2: enumerate ambiguities, write tests to `tests/`, approach.md to validation/.
5. Phase 3: input is intent.md + tests only. Pass the suite. Record decisions in implementation/notes.md.
6. Phase 4: full test suite + validator + invariant evidence table. Failure = fail the slice, not patch.

## Step 3

Gate before advancing: Phase 2 needs intent.md + adrs-referenced committed (empty adrs-referenced passes trivially). Phase 3 needs tests committed. Phase 4 needs source committed. On failure, name every missing ADR slug. On pass: update slice.yaml, print Phase Skill Guide role/skills.

## Step 7

Completion wipes `.claude/current-slice/` — `git rm -r` all files except slice.yaml (set `status: complete`). No archive for successful slices. Check sweep.yaml for due sweep.

## Step 8

Failed slice recovery: set `status: failed` in slice.yaml, commit, archive to `.claude/completed-slices/<ID>-failed/`, recreate empty current-slice. Fresh slice with failure as input context.

## Load full

- If initializing a new slice: read start-slice.full.md for directory structure, slice.yaml template, and intent-writing guide.
- If gate fails: read start-slice.full.md for D3 gate semantics and remediation commands.
- If running `/start-slice complete`: read start-slice.full.md for the completion sequence.
- If running `/start-slice failed`: read start-slice.full.md for the archive protocol.
