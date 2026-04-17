---
slice: identifier-scheme/adr-rename-sweep
phase: 2-validation
date: 2026-04-17
---

# Phase 2 Skeptic approach — adr-rename-sweep

## Inputs read
- `.claude/current-slice/intent.md`
- `docs/adr/identifier-scheme.md` (sole `adrs-referenced` entry)
- `.claude/current-slice/handoff-phase-1.md` (Phase 1 flagged ambiguities)
- Reference scans: `docs/adr/`, `tests/unit/*.py`, `docs/lessons.md`, `CHANGELOG.md`, `checks/reversibility-guard.sh`, `scripts/validate_architecture.py`, `.claude/features/identifier-scheme.yaml`, `docs/ARCHITECTURE.md` (INV-005 block)

No implementation source was read except hook bodies (needed to confirm Phase-1 widening already landed — reversibility-guard now matches `docs/adr/*.md`, not `[0-9]*.md`).

## Ambiguities — enumeration and resolution

### A1. Slug authoring (Phase-1 handoff flag 3)
**Intent says:** "mechanical, do not re-author slugs."
**Resolution:** Accept the long slug `cliff-failure-mode-and-v1-defenses` as-is. No Skeptic objection.

### A2. CHANGELOG section placement (Phase-1 handoff flag 2)
**Intent says:** "Add a new entry in CHANGELOG.md under the current unreleased section" with "Header: `ADR identifier migration (Phase 2 Part 1)`".
**CHANGELOG.md convention:** `## [Unreleased]` with H3 category sub-headers (`### Added`, `### Fixed`, `### Changed`).
**Resolution:** The intent's "Header" is the migration entry's own H3 — treated as a new H3 sibling alongside `### Added` etc., placed inside `## [Unreleased]`. Exact order among existing H3s is Phase-3 judgment; the test asserts presence and content, not position.

### A3. Which tests keep legacy-format fixtures (Phase-1 handoff flag 1)
**Intent says:** "EXCEPT tests that verify hook/validator legacy-format tolerance (e.g., `test_hook_tolerance.py`)".
**Skeptic inventory (tests/unit/ ADR-NNN/`docs/adr/00[0-9]` hits):**
| File | Hits | Load-bearing legacy? |
|------|------|----------------------|
| `test_hook_tolerance.py` | 1 docs/adr/00 + many comments | YES — exercises dual-format hook acceptance |
| `test_hook_relpath_bypass.py` | 3 docs/adr/00 | YES — exercises dual-format across path shapes |
| `test_slice_005_design_decomposition.py` | 52 ADR-NNN + 1 docs/adr/00 | NO — asserts on real ADR frontmatter content |
| `test_snapshot_diff.py` | 4 ADR-NNN + 2 docs/adr/00 | NO — `003-cliff.md` is a synthetic fixture path in tmp_path |
| `test_integration_gate.py`, `test_validate_architecture.py`, `test_feature_skill_conformance.py`, etc. | various | NO — prose comments and assertions about specific ADRs |

**Resolution:** Phase-1's list of two legacy-tolerance tests is complete. All other tests migrate to flat-slug. Synthetic fixture filenames in `test_snapshot_diff.py` (e.g., `"docs/adr/003-cliff.md"` created in tmp_path) migrate — they are not legacy-tolerance tests, they are illustrative snapshot fixtures that can be re-shaped without loss of meaning.

### A4. `docs/lessons.md` "explicitly-historical sections"
**Intent says:** "excluding explicitly-historical sections of `docs/lessons.md` if any".
**Scan result:** No section of `docs/lessons.md` is labeled "historical". Lessons are named L-NNN with active-tense content; all ADR-NNN references are inline prose ("ADR-001 already says…", "ADR-004 phase rethink").
**Resolution:** No exclusion applies. All `ADR-NNN` references in `docs/lessons.md` migrate via the sweep.

### A5. `docs/adr/identifier-scheme.md` frontmatter
**Intent says:** "Already flat-slug (no rename, no frontmatter edit): `d3-bypass-classification.md`, `identifier-scheme.md`."
**But:** `identifier-scheme.md` frontmatter has `supersedes: [ADR-005]` and `supersedes: ADR-005` in prose. Leaving these unchanged contradicts the cross-reference sweep.
**Resolution:** "No frontmatter edit" refers only to the `id:` field (already flat-slug). The token-level substitution `ADR-NNN → <flat-slug>` applies to every `ADR-NNN` occurrence in the live tree, including inside `identifier-scheme.md` frontmatter (`supersedes: [ADR-005]` → `supersedes: [semantic-identity]`) and body prose ("Supersedes ADR-005" → "Supersedes semantic-identity"). Same rule for `d3-bypass-classification.md` body references. Each such frontmatter edit requires `ADR_EDITORIAL_FIX=1`.

### A6. `docs/adr/index.md` "rebuilt"
**Intent says:** "rebuilt as part of the sweep — every entry uses the flat-slug filename and id."
**Resolution:** Outcome-defined, not method-defined. Full rewrite or in-place edit of each row are both acceptable. Tests assert the outcome (every row has flat-slug id, no numeric prefix in the body), not the mechanism.

### A7. INV-005 invariant check
**INV-005 (ARCHITECTURE.md:49,51):** `type: file-exists, target: "docs/adr/identifier-scheme.md"`.
**Resolution:** `identifier-scheme.md` is not renamed; the file-exists check continues to pass. INV-005 is preserved by non-action. No Phase 2 test needed specifically for INV-005 beyond the general "validator exits 0" check.

### A8. Hook scripts (`checks/*.sh`)
**Scope:** Out of envelope per intent.
**Scan result:** `reversibility-guard.sh` mentions `"ADR-NNN"` as a literal placeholder in the deny-message help text — this does not match the verification grep pattern `ADR-00[0-9]` and is not an ADR-specific reference.
**Resolution:** No action on hook scripts in this slice. They already accept flat-slug (reversibility-guard matches `docs/adr/*.md`).

### A9. Validator comment reference (`scripts/validate_architecture.py:153`)
**Current:** `# current tolerance for commentary like \`confirmed by ADR-009\`. Flat-slug…`
**Resolution:** This is an illustrative example inside a comment describing the validator's legacy-tolerance code path. It will be mechanically updated by the sweep (to `confirmed by phase-pipeline-evaluation`) — the comment remains illustrative regardless of the specific token. Phase 3 may edit the comment to a more generic phrasing (e.g., `"confirmed by <adr-id>"`) at its discretion; test asserts only that no `ADR-00[0-9]` token remains in the file.

### A10. CLAUDE.md
**Scan result:** Zero `ADR-NNN` hits in `CLAUDE.md`.
**Resolution:** CLAUDE.md is in the envelope but has nothing to migrate. The sweep running against it is a no-op.

### A11. Frontmatter `invariants-touched: [INV-005]`
**Slice.yaml declares `invariants-touched: [INV-005]`.** INV-005 governs the two-field identity model existence. The rename sweep is the operational realization of the scheme for existing ADRs; INV-005's `file-exists` check on `docs/adr/identifier-scheme.md` is not mechanically impacted, but the invariant's *spirit* (all entities carry flat-slug `id:`) is what this slice enforces across the ADR corpus.
**Resolution:** Phase 4 Auditor verifies INV-005 by the existing file-exists block plus the rename/frontmatter evidence from this slice. Phase 2 does not need a dedicated INV-005 test beyond "validator exits 0".

## Flagged for Phase 3 (not blocking Phase 2)

### F1. Verification #4 vs #10 grep-vs-tolerance-test collision
**Collision:** Intent verification #4 asserts zero `ADR-00[0-9]` / `docs/adr/00[0-9]` hits across `tests/unit/`. Intent verification #10 requires `test_hook_tolerance.py` and `test_hook_relpath_bypass.py` to "still pass", which requires them to contain legacy-format fixture paths (currently `docs/adr/006-feature-slice-model.md`). The two verifications cannot both hold under the literal grep.

**Resolution (carries into Phase 2 tests):** The verification #4 grep is interpreted to **exclude the two named tolerance test files**. Phase 2 tests for V4 run the grep with `--exclude=test_hook_tolerance.py --exclude=test_hook_relpath_bypass.py`. This is consistent with the intent's own exception clause for those two files.

### F2. Tolerance tests lose their subject file post-rename
**Problem:** After `git mv docs/adr/006-feature-slice-model.md docs/adr/feature-slice-model.md`, the legacy path no longer exists. `test_hook_tolerance.py::test_write_existing_legacy_adr_blocked` and equivalent tests in `test_hook_relpath_bypass.py` rely on the hook's `if [ -f "$PROJECT_ROOT/$CANONICAL" ]` branch firing — with no legacy file in the tree, the hook falls through to allow, and the tests fail.

**Phase 3 must resolve.** Options (not prescribed):
1. Rewrite the tolerance tests to create synthetic legacy-shape fixtures under `tmp_path` and set `CLAUDE_PROJECT_DIR=$tmp_path` for the hook invocation.
2. Introduce a permanent synthetic sentinel file `docs/adr/999-tolerance-fixture.md` whose only purpose is exercising the legacy code path. Note `999-` is outside the `00[0-9]` verification grep, so this choice satisfies V4 without needing an exclusion.
3. Point the legacy fixture at a different still-existing numeric-prefix ADR — but verification #1 says zero `[0-9]*-*.md` files remain, so this option is foreclosed.

ADR identifier-scheme §D7 Phase 3 explicitly describes the legacy-tolerance as "dead code once Phase 2 lands, but harmless." Options 1 and 2 preserve the test coverage without a live legacy subject.

**Phase 2 behavior:** This slice's tests treat "full test suite passes" as a Phase-4-level check. Phase 2 does not assert a specific fixture-restructuring mechanism. Verification #10 is represented in this slice's test suite as a structural check (both files still exist) — *behavioral* re-greening is Phase 3's job via the restructuring above.

## Test plan

New test file: `tests/unit/test_adr_rename_sweep.py`. Organized by intent verification number.

| Class / test | Intent §V | Current state | Target state | Technique |
|---|---|---|---|---|
| `TestV1RenameOutcome::test_all_flat_slug_targets_exist` | 1 | RED | GREEN after rename | check each new filename from rename table via `(CAIRN_ROOT / "docs/adr/<slug>.md").exists()` |
| `TestV1RenameOutcome::test_zero_numeric_prefix_files` | 1 | RED | GREEN | glob `docs/adr/[0-9]*.md`, assert empty list |
| `TestV1RenameOutcome::test_exactly_twelve_files` | 1 | GREEN pre/post (regression guard) | GREEN | count `.md` files in `docs/adr/` |
| `TestV2FrontmatterIds::test_id_matches_rename_table` | 2 | RED for 9 renamed | GREEN | parametrized over rename table; read `id:` line from each file, assert flat-slug |
| `TestV3GitLogFollow::test_bootstrap_exception_history_preserved` | 3 | RED (new file absent) | GREEN | `git log --follow --format=%H docs/adr/bootstrap-exception.md`, assert more than 1 commit |
| `TestV4GrepCleanliness::test_no_ADR_NNN_in_live_tree` | 4 | RED (hundreds of hits) | GREEN | `grep -rE 'ADR-00[0-9]'` over in-scope dirs, excluding the two tolerance tests |
| `TestV4GrepCleanliness::test_no_numeric_adr_path_in_live_tree` | 4 | RED | GREEN | `grep -rE 'docs/adr/00[0-9]'` same exclusions |
| `TestV5IndexShape::test_every_row_uses_flat_slug_id` | 5 | RED | GREEN | parse `docs/adr/index.md` table rows, assert each `ID` column entry is flat-slug |
| `TestV5IndexShape::test_no_numeric_prefix_in_index_body` | 5 | RED | GREEN | grep `00[0-9]-` against index.md body |
| `TestV6ChangelogEntry::test_header_present` | 6 | RED (entry absent) | GREEN | grep `ADR identifier migration (Phase 2 Part 1)` in `CHANGELOG.md` |
| `TestV6ChangelogEntry::test_rename_table_has_nine_rows` | 6 | RED | GREEN | parse markdown table inside the entry, assert 9 data rows |
| `TestV6ChangelogEntry::test_consumer_paragraph_names_complex_rag_analysis` | 6 | RED | GREEN | substring check |
| `TestV6ChangelogEntry::test_link_to_identifier_scheme_d7` | 6 | RED | GREEN | substring check for `identifier-scheme` + `D7` |
| `TestV7Validator::test_validate_architecture_exits_0` | 7 | GREEN pre/post (regression guard) | GREEN | `subprocess.run(["uv", "run", "python", "scripts/validate_architecture.py"])` |
| `TestV10ToleranceTestsPresent::test_both_tolerance_tests_exist` | 10 | GREEN pre/post (regression guard) | GREEN | file-exists check on the two named test files |

### Not-asserted-in-Phase-2

- **V8 full test suite** — Phase 4 runs this as the integration pass. Phase 2 does not embed pytest-in-pytest.
- **V9 `implementation/notes.md` audit trail** — Phase 3 artifact; not visible at Phase 2 commit time.
- **Behavioral re-greening of tolerance tests** — Phase 3 implements the fixture restructuring (per F2). Phase 2 does not prescribe the mechanism.

### Envelope discipline

All new tests live in `tests/unit/test_adr_rename_sweep.py` — single file under the envelope's `tests/unit/*.py` glob. No other test-file creation; no source-file creation.

### Verify RED

After writing, run `uv run python -m pytest tests/unit/test_adr_rename_sweep.py -v`. Expected: V1, V2, V3, V4, V5, V6 classes fail with evidence citing current-state legacy names/references; V7 and V10 pass as regression guards. Any unexpected pass or error indicates the test is not actually testing what the intent requires — fix and re-run until the RED picture matches expectations before handing off.
