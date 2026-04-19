---
slice: housekeeping/post-slice-a-tidy
phase: 2-validation
date: 2026-04-19
---

## Ambiguity enumeration

Forced enumeration over intent.md verification section; no unresolved ambiguities.

- **Item A wording** — "exits 0 with no F841 finding" vs "exits 0 period". Interpreted as the narrower guard: F841 specifically must not appear. A later unrelated ruff finding would not regress this slice's goal. Test asserts `"F841" not in combined_output`, not `returncode == 0`.
- **Item B** — intent lists this as "verify-only"; translates to a drift-detector pair (gitignore pattern present + file not in index). No write action expected from Phase 3.
- **Item D** — intent says "already resolved". Encoded as a guard test that fails if any of `validation/`, `implementation/`, `integration/` exists empty. This catches regressions where a future phase creates an empty dir and fails to populate it.
- **Item 8** — intent lists five finding keywords; encoded as a presence check on a `## Dogfooding findings` section in Phase 4's `sweep-notes.md`. Keyword set is the minimum Phase 4 must persist; extra findings are allowed.

## Test → verification mapping

| Verification item | Test(s) | RED/GREEN at Phase 2 commit |
|---|---|---|
| 1. ruff clean on state-machine test | `test_item_a_ruff_no_f841_in_state_machine_test` | RED |
| 2. state-machine target-function still passes | `test_item_a_state_machine_target_function_still_passes` (narrow — finding #6 in approach rationale) | GREEN guard |
| 3. platform-probe not tracked | `test_item_c_platform_probe_not_tracked` | RED |
| 3. platform-probe not in working tree | `test_item_c_platform_probe_not_in_working_tree` | RED |
| 4. .gitignore still lists handoff.md | `test_item_b_handoff_path_in_gitignore` | GREEN guard |
| 4. handoff.md untracked | `test_item_b_handoff_not_tracked` | GREEN guard |
| 5. no stray empty subdirs | `test_item_d_no_empty_current_slice_subdirs` | GREEN guard |
| 8. dogfooding findings section | `test_item_8_dogfooding_findings_section_in_sweep_notes` | RED |

Items 6 (full-suite pytest) and 7 (architecture validator) are Phase 4 whole-tree checks; they are not encoded as Phase 2 fixtures.

## Envelope expansion

Phase 1 envelope authorised only `tests/unit/test_slice_orchestrator_state_machine.py` for tests. That file's theme is orchestrator state-machine behaviour, and appending housekeeping-janitorial assertions there pollutes it. Phase 2 expands the envelope by one file — `tests/unit/test_housekeeping_post_slice_a_tidy.py` — with the rationale recorded here and in the Phase-2 commit message. Noted as dogfooding finding #5 (Phase-1 envelope schema lacks a slice-slug test slot by default).
