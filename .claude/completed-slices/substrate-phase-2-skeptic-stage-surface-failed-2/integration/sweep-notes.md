---
slice: substrate/phase-2-skeptic-stage-surface
phase: 4-integration
date: 2026-05-02
outcome: RAISE_ISSUE
---

# Integration sweep — substrate/phase-2-skeptic-stage-surface (re-dispatch)

Phase: 4 Integration · Date: 2026-05-02 · Auditor

## Scope

Re-dispatch of issue #26 self-application validation. Fix already on HEAD at
`ae9e6c8`. Slice contribution: regression surface
`tests/unit/test_phase_2_handoff_staging_surface.py` (R1–R4) + bisect-anchor
demonstration that the Phase-2 boundary commit on this slice naturally
captures the new test file.

## Invariants

| Invariant | Statement | Status | Evidence |
|-----------|-----------|--------|----------|
| INV-008 | close_slice produces exactly one terminal `slice: <id> — complete` commit; phase handoffs are content-widening on a single per-phase commit (DC-3 idempotent, DC-4 commit-count preserved). | PASS (code-level) | `scripts/slice_orchestrator/lifecycle.py:226-242` (ae9e6c8) — diff-discovery branch is `path.exists()`-guarded (DC-3) and stages additively into the same `commit --allow-empty -m "handoff: phase 2 complete"` (DC-4). `validate_architecture.py` PASS (10 invariants, 18 ADRs). |

## Test suite

`uv run pytest` → **1173 passed, 3 skipped, 3 xfailed, 6 failed** in 140.88s.

Slice-scoped surface (all PASS):
- `tests/unit/test_phase_2_handoff_staging_surface.py::test_phase_2_stages_single_slug_named_test_file` (R1)
- `tests/unit/test_phase_2_handoff_staging_surface.py::test_phase_2_stages_three_mixed_naming_test_files` (R2)
- `tests/unit/test_phase_2_handoff_staging_surface.py::test_phase_2_zero_test_files_preserves_commit_shape` (R3)
- `tests/unit/test_phase_2_handoff_staging_surface.py::test_phase_2_stages_test_file_and_handoff_md_together` (R4)

Pre-existing failures (out-of-scope, untouched in slice diff `2dad9db..HEAD`):

| Test | Disposition |
|------|-------------|
| `tests/unit/test_d3_bypass_log_format.py::test_every_line_matches_classified_regex` | pre-existing — tracked at `v1-defense-d3/bypass-log-test-resilience` |
| `tests/unit/test_extractor_slice.py::test_emits_parent_edge_to_feature` | pre-existing — substrate Slice 4 (L-015) |
| `tests/unit/test_mcp_cairn_knowledge_tools.py::test_v3_lookup_returns_invariant` | pre-existing — substrate MCP v3 thread |
| `tests/unit/test_mcp_cairn_knowledge_tools.py::test_v3_search_returns_typed_list` | pre-existing — substrate MCP v3 thread |
| `tests/unit/test_mcp_cairn_knowledge_tools.py::test_v3_path_bindings_returns_entities` | pre-existing — substrate MCP v3 thread |
| `tests/unit/test_mcp_cairn_knowledge_tools.py::test_v3_cypher_returns_row_dicts` | pre-existing — substrate MCP v3 thread |

All six predate slice init (`2dad9db`); no slice commit touches these files. Out
of scope per `intent.md` boundary.

## Diff surface (slice scope)

Slice commits (`2dad9db..3f79259`):

```
3f79259 handoff: phase 3 complete
52d92be handoff: phase 3 complete
af0b5e0 test: add regression surface for phase-2 test-file staging (issue #26)
f61a50e handoff: phase 2 complete
d5a9cb4 handoff: phase 1 complete
2dad9db slice: substrate/phase-2-skeptic-stage-surface — init
```

Test file shipped (291 LOC, additive). No source changes (fix already in tree at
ae9e6c8 from prior dispatch).

## Bisect-anchor contract — UNMET

`intent.md` makes the slice's substantive contribution conditional on:

> "the demonstration that, under the fixed orchestrator, that test file is itself
> naturally captured by the Phase-2 boundary commit on this very slice — the
> bisect-anchor contract the prior dispatch attempt could not satisfy."

Observed: Phase-2 boundary commit `f61a50e` is **empty** (`git show --stat f61a50e`
lists no paths). The test file `tests/unit/test_phase_2_handoff_staging_surface.py`
appears in `af0b5e0`, a separate commit between Phase-2 and Phase-3 handoffs,
with subject `test: add regression surface ...` — not produced by
`commit_phase_handoff`.

Interpretation: Phase-2-skeptic did not write the test file to disk *before*
its handoff commit fired; the file was materialised between Phase-2 and Phase-3
handoffs and committed via a non-orchestrator path. The R1–R4 unit tests
themselves confirm the `lifecycle.py` diff-discovery branch is logically correct
(all green against HEAD), but self-application as a bisect anchor failed for the
same root cause as the prior dispatch (cb45e7b archive): the orchestration
sequence does not currently guarantee that Phase-2 agent writes are flushed to
worktree before `commit_phase_handoff(phase=2)` runs.

This is a process/orchestration gap, **not** a code defect in the ae9e6c8 fix.

## Outcome

**RAISE_ISSUE.** Code surface is correct and verified by R1–R4. Pre-existing
reds out of scope. The bisect-anchor self-application contract from `intent.md`
is unmet — the Phase-2 boundary commit `f61a50e` does not contain the test
file. Recommend triager open a follow-up on Phase-2 agent → orchestrator
write-flush sequencing rather than a third re-dispatch of this same slice
(the test surface is now in the tree; further re-dispatch cannot retroactively
re-stage `f61a50e`).

## Learnings observed (optional)

- L: Self-application as a bisect-anchor strategy presumes the Phase-2 agent
  reliably writes-then-yields before the orchestrator's phase handoff fires.
  Two consecutive dispatches of this slice failed to land the RED test inside
  the Phase-2 boundary commit despite the in-tree fix being correct, suggesting
  the failure mode lives in the agent/orchestrator handoff sequencing rather
  than in `commit_phase_handoff` itself.
