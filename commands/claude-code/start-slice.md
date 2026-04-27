# /start-slice

Thin dispatcher → `python -m slice_orchestrator` (package at `scripts/slice_orchestrator/`). Drives a slice through Intent → Validation → Implementation → Integration via per-phase `claude -p --agent <role>` agents.

Usage: `/start-slice <brief>` (new), `/start-slice --resume` (continue current), `/start-slice --legacy` (prose fallback).

## Step 3

Gate before advancing. Phase 2 needs `intent.md` + `adrs-referenced` committed (empty `adrs-referenced` passes trivially). Phase 3 needs the validation suite committed. Phase 4 needs the source committed. On failure, name every missing ADR slug and stop. On pass, advance the slice and print the Phase Skill Guide row for the next role.

## Step 7

Completion wipes `.claude/current-slice/`. The orchestrator removes every file under that directory in the close commit (`slice.yaml` is overwritten by the next slice). No archive directory — git history covers the post-mortem case.

## Step 8

Failed slice recovery: orchestrator sets `status: failed` in `slice.yaml`, archives the directory to `.claude/completed-slices/<id>-failed/`, and exits non-zero. The next slice can use the failed slice as input context.

## Legacy escape hatch

`/start-slice --legacy` (or env `CAIRN_LEGACY_START_SLICE=1`) bypasses the orchestrator and follows `start-slice-legacy.md`, which points at the canonical prose protocol in `start-slice.full.md`. Retained until ≥5 clean compressed slices have landed (compression design §10).

## Load full

- Always: read start-slice.full.md for the full prose protocol — phase-by-phase rules, gate semantics, slice.yaml schema, completion sequence, and failed-slice archive protocol.
