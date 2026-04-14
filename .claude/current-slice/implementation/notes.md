# SLICE-008 Implementation Notes

## Decisions not pinned by intent

1. **D1 gate placement in Step 7.** Intent says "between Phase 4 PASS and status: complete transition." Placed the gate as a `### D1 Refresh Gate` subsection before a new `### Completion Sequence` subsection. The existing numbered sequence (1–6) is preserved under Completion Sequence, keeping the gate logically prior but structurally separate.

2. **V6 note placement.** Intent says refresh-architecture.md "and/or" .full.md gains a note. Added to refresh-architecture.md (the lite file) since it's loaded by default and the note is short. The .full.md was left unchanged — no behavioral change to document there.

## Pre-existing test failures

Three tests from prior slices fail when SLICE-008 files are uncommitted (envelope-compliance diffs against HEAD). These are expected during Phase 3 and will resolve on commit:
- `test_slice_005_design_decomposition::test_v7_envelope_compliance`
- `test_sweep_debt_cleanup::test_v3_measurement_artifact_committed` (pre-existing debt)
- `test_sweep_debt_cleanup::test_v4_envelope_compliance`
