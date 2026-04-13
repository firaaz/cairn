# SLICE-007 Phase 2 — Validation Approach

## Ambiguity Resolutions

**A1 — Measurement values correctness.** The intent says "commit the corrected measurement values" produced by a hook recalculation (20074→19950, MISS→PASS). Resolution: the working-tree state is mechanically generated output. Commit as-is. No validation of the values themselves is in scope — the test checks only that the file has no uncommitted diff.

**A2 — Table cell content for using-git-worktrees.** The intent specifies wording: "when subagent-driven tasks require workspace isolation, or for cross-slice parallel work". ADR-007 D3 confirms: "returns as a conditional supporting skill for Phase 3 (Builder) when subagent-driven tasks require workspace isolation. Also available for cross-slice parallel work." The intent wording is consistent with ADR-007 D3. Resolution: test checks that `using-git-worktrees` appears in the Phase 3 row's Supporting skills column. Exact prose is a Phase 3 editorial choice within the ADR-007 D3 constraint.

**A3 — Notes column for new entry.** The intent does not specify Notes column text. The existing Phase 3 Notes column is about TDD cycle completion and verification-before-completion being mandatory — unrelated to worktrees. Resolution: no Notes column change required. The conditional wording in the Supporting skills column itself provides sufficient context, matching the pattern of existing entries (e.g., `dispatching-parallel-agents when...`).

**A4 — Exclusion removal scope.** Line 104 of operational-reference.md contains the full `using-git-worktrees` exclusion bullet. Resolution: remove exactly that bullet. Section heading, intro text, and other three bullets remain unchanged.

## Test Strategy

| Test | Verification | RED/GREEN at Phase 2 |
|------|-------------|---------------------|
| test_v1_worktrees_in_phase3_supporting | Intent #2 | RED — not yet in table |
| test_v2_worktrees_not_in_exclusions | Intent #3 | RED — still in exclusions |
| test_v3_measurement_artifact_committed | Intent #1, #4 | RED — file uncommitted |
| test_v4_envelope_compliance | Envelope discipline | GREEN canary — only the measurement file is outside envelope patterns, and it IS in the allowed list |
| test_v5_architecture_validator | Intent #5 | GREEN canary — no invariant changes |

V1-V3 flip GREEN when Phase 3 commits the two changes. V4-V5 are regression guards.
