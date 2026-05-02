---
slice: none
phase: between-slices
branch: feature/compression-followup
as-of: 2026-05-02 d6d742f
---

## State

`compression/papercut-bundle` (Slice 1) closed clean at `161fa56` — three
substrate paper-cuts landed (scope-guard d{1,3}-bypasses arm, verify_handoff
`sweep:` prefix, integration-sweep doc → `uv run python`). 13 regression tests
pass.

`substrate/phase-2-skeptic-stage-surface` (Slice 2, issue #26) failed twice
and was archived. The lifecycle.py fix at `ae9e6c8` remains on HEAD and
satisfies its R1–R4 unit tests (mocked git surface), but two distinct
substrate bugs surfaced under self-application:

1. **`ae9e6c8` untracked-file blind spot.** `commit_phase_handoff` uses `git
   diff --name-only <phase-1-sha> -- tests/unit/`, which excludes untracked
   files. First-time test files (the actual issue #26 scenario) never reach
   the staging set. Verified independently with a scratch repo — `git diff`
   returns empty for untracked paths.
2. **Phase-2-skeptic write timing.** On the redispatch, the skeptic agent
   did not write `tests/unit/test_phase_2_handoff_staging_surface.py` during
   Phase 2 (the file mtime is `14:11`, after the Phase-2 handoff commit at
   `14:10:21`). The file was instead written by phase-3-implementer and
   committed at `af0b5e0` between the two phase-3 handoffs. Cause unclear
   — possibly because the slice brief mentioned a reference file already
   existed; possibly because the skeptic's prompt makes a "validate, don't
   re-write" call when it sees evidence the artifact is already in tree.

Issue #26 is therefore partially resolved: the test surface
`tests/unit/test_phase_2_handoff_staging_surface.py` is in tree at `af0b5e0`,
unit tests pass, the lifecycle.py change covers the tracked-modified path —
but the actual S1 scenario (first-time test file written by phase-2-skeptic)
still leaks past the Phase-2 boundary.

## Next

A small follow-up slice should patch `scripts/slice_orchestrator/lifecycle.py`
to also enumerate untracked files via `git ls-files --others
--exclude-standard -- tests/unit/`, in addition to the existing diff. This is
a ~5-line change. Suggested slice id:
`substrate/phase-2-staging-untracked-enumeration`.

The phase-2-skeptic write-timing bug is a separate axis. Worth a one-paragraph
filing as a new issue before tackling — the lifecycle.py fix covers the
S1 hot path even if the skeptic happens to write tests during P2; the
sequencing bug only matters when the skeptic skips the write, which is a
behavioral question about the agent prompt.

## Pending / Blocked

- Issue #26 — partially fixed (`ae9e6c8`); needs untracked-enumeration
  follow-up before fully closed.
- New issue (file): phase-2-skeptic on redispatch did not write tests during
  Phase 2 — agent-prompt sequencing question.
- `test_d3_bypass_log_format` line-18 fail persists → `v1-defense-d3/bypass-log-test-resilience`.
- `test_extractor_slice::test_emits_parent_edge_to_feature` XPASS-strict on
  un-squashed feature-branch close commits → substrate Slice 4 (L-015) or
  relax `strict=True`.
- Integration sweep due — interval=1, +1 slice (Slice 1) since
  `compression/upgrade-doc-bug-fixes`. Run `/integration-sweep` in a fresh
  session before opening the next slice.
- Branch lifetime ceiling 2026-05-11 → six followup slices originally queued;
  three remain assignable here (Slice 1 closed; Slice 2 partially closed;
  three followups + this paper-cut close-out + the pending sweep).

## Pointers

- `.claude/completed-slices/substrate-phase-2-skeptic-stage-surface-failed-2/`
  — handoff-phase-4.md (integrator's RAISE_ISSUE summary, test-file-mtime
  analysis), intent.md (the redispatch's bisect-anchor commitment).
- `.claude/completed-slices/substrate-phase-2-skeptic-stage-surface-failed/`
  — first-attempt artifacts including the reference test file.
- `scripts/slice_orchestrator/lifecycle.py:228-243` — the diff-based staging
  block from `ae9e6c8`, target of the planned follow-up patch.
- `tests/unit/test_phase_2_handoff_staging_surface.py` — R1–R4 regression
  surface, in tree at `af0b5e0`.
- Issue #26 — the original spec; should NOT be closed until the
  untracked-enumeration follow-up lands.

## Memory entry to update

`slice_system_propagates_wrong_models.md` (auto-memory) is the existing entry
on Phase-2-skeptic behavior issues. The phase-2-skeptic write-timing finding
in this slice belongs under that thread or as a sibling memory.
