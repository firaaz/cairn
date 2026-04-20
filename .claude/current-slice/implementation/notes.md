Phase 3 implementation notes — rename-sweep-test-robust

Envelope: tests/unit/test_adr_rename_sweep.py (single file).

Source changes committed as 38100de before Phase-2 re-dispatch:
- Retired TestV1RenameOutcome.test_exact_twelve_adr_files_total (no fixed-int
  latch, no whole-corpus static set equality).
- Repurposed UNRENAMED_ADR_FILES as historical constant only; V5
  test_every_id_column_is_known_flat_slug derives expected_ids from
  adr_dir.glob live enumeration.
- Added TestLiveCorpusFlatSlugShape parametrized over docs/adr minus index.md:
  filename regex plus id-stem match, offender name in assertion message.
- Module docstring updated: widened contract ongoing flat-slug shape over
  every live docs/adr ADR, NOT size-latched.
- No literal reference to compression-infrastructure-bootstrap in source
  (V3 / C2 grep-count 0).

Phase-2 re-dispatch dependency (6985d43): Phase 3 previously raised an issue
that C1 test_exact_count_method_removed embedded the forbidden method name
as a literal, making the probe unsatisfiable. Phase 2 re-dispatched and
fragment-joined the name. That fix unblocked the remaining RED contract
tests without touching the Phase 3 refactor.

Verification:
- uv run pytest tests/unit/test_adr_rename_sweep.py -q passes 66/66 on the
  live 13-file corpus (9 rename-table targets + d3-bypass-classification.md
  + identifier-scheme.md + compression-infrastructure-bootstrap.md + index.md).
- Envelope-clean: only source delta is tests/unit/test_adr_rename_sweep.py.
- C4 robustness: synthetic valid green, malformed red with offender name,
  mismatch red with offender name.

Out-of-envelope pre-existing regressions (not this slice): full-suite run
shows 7 failures in test_hook_tolerance.py, test_hook_relpath_bypass.py,
test_housekeeping_post_slice_a_tidy.py. Root cause: reversibility-guard.sh
hook behavior plus missing Phase-4 sweep-notes.md artifact. Unchanged by
this envelope.
