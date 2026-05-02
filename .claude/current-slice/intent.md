# Intent — substrate/start-slice-pythonpath-paper-cut

## What

Replace every operator-facing occurrence of the bare dispatcher line
`python -m slice_orchestrator` with the canonical
`PYTHONPATH=scripts uv run python -m slice_orchestrator` across four
documentation surfaces, and lock the fix with a new RED test.

Envelope (5 files):

- `commands/claude-code/start-slice.md` (primary)
- `commands/claude-code/start-slice-legacy.md` (prose mirror)
- `CHANGELOG.md` (CLI ref)
- `docs/features/compression.md` (CLI ref)
- `tests/unit/test_start_slice_dispatcher_doc.py` (new)

## Why

`slice_orchestrator` lives under `scripts/` and is not installed into
the project venv. The bare line, copied verbatim from current docs,
fails with `ModuleNotFoundError`. Operators who copy-paste the
documented command get a broken command — a substrate paper-cut of the
same class as the prior `upgrade_doc` typos.

## Boundary

Pure documentation change plus one new test. No edits under
`scripts/slice_orchestrator/`. Skill-flow dispatch is unaffected — the
skill executes a tool call, not the literal prose.

Out of scope: `docs/lessons.md`, `docs/plans/**`, `docs/adr/**`,
`docs/operational-reference.md`, `.claude/sweep-results/**`,
`.claude/completed-slices/**`, any change to orchestrator CLI surface
or behavior, making `slice_orchestrator` pip-installable.

Invariants touched: none. ADRs referenced: none (empty adrs-referenced
satisfies D3 trivially per phase-lock-and-role-declaration D3).

## Specification

For each of the four documentation files, every line containing the
substring `python -m slice_orchestrator` must, after stripping leading
prose markers (backticks, list bullets, indentation), begin with the
literal prefix `PYTHONPATH=scripts uv run python -m slice_orchestrator`.

Equivalently: zero matches for the bare form
`(?<!uv run )python -m slice_orchestrator` across the four files.

The new test `tests/unit/test_start_slice_dispatcher_doc.py` enforces
this property as a parametrized check over the four envelope files.

## Verification

- Phase 2 RED: `tests/unit/test_start_slice_dispatcher_doc.py` fails on
  current `main` (bare form present in all four files) and passes after
  the doc edits land.
- Negative-lookbehind regex `(?<!uv run )python -m slice_orchestrator`
  yields zero matches in the four envelope files post-fix.
- Manual smoke: copying the dispatcher line from any of the four docs
  into a fresh shell at repo root no longer raises `ModuleNotFoundError`.
- No diff under `scripts/slice_orchestrator/`.
- Out-of-scope files (`lessons.md`, `plans/**`, `adr/**`,
  `sweep-results/**`, `completed-slices/**`) untouched in slice diff.
