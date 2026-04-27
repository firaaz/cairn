# Phase 2 — Validation approach for compression/lever-Z-fixup

Five RED test files under `tests/unit/`, one per Phase-3 cluster, each with at least one load-bearing failing assertion that flips GREEN only after its source edit lands. Cluster-RED-test discipline preserved per `compression/learnings-capture` retry: brittleness explicitly accepted as the price of progress signal that GREEN cannot vacuously satisfy.

## Cluster → RED test mapping

- **S1 (phase-1-writer Bash restore)** → `test_phase_1_writer_bash_restored.py`. Brittleness: literal `Bash` membership in comma-split frontmatter `tools:` line. Co-asserts: Write/Edit kept, Grep/Glob still absent (hard-non-goal regression guard).
- **S2 (consumer-migration doc)** → `test_consumer_migration_doc.py`. Brittleness: file existence + 5 stable-substring tokens (one per delta) + Verify-marker count ≥5 + retired-constraint name-checks. Phase-3 keeps prose latitude; tokens load-bearing.
- **S3 (lessons L-014)** → `test_lessons_cross_slice_contradiction.py`. Brittleness: L-014 heading + load-bearing token `pre-grep the existing test corpus` + Phase-2 actor named within L-014 entry body (scoped, not file-scoped) + ordering after L-013.
- **S4.a (`_ARTIFACT_RELPATHS`)** → `test_lifecycle_artifact_relpaths_paper_cut.py`. Brittleness: two-sided membership (presence of `integration/envelope-expansions.log` AND absence of bare `envelope-expansions.log`) — silent-skip prevention.
- **S4.b (phase-4-integrator)** → `test_phase_4_integrator_paper_cuts.py`. Brittleness: three substring tokens (`entity_type` with `lookup`; one of four attribute-access tokens incl. `record.statement`; `stdio` with `cairn-knowledge`).

S4 splits into two file-disjoint clusters per intent §S4 (`lifecycle.py` vs `phase-4-integrator.md`).

## L-014 self-application dogfood (load-bearing)

Pre-grep over `tests/`:

- `_ARTIFACT_RELPATHS` membership: no inversions (only `test_orchestrator_events_capture.py:475` references the tuple, and asserts a different path).
- `phase-1-writer` frontmatter: **INVERSION.** `test_phase_1_writer_query_first.py::test_v7_tools_frontmatter_excludes_read_and_bash` lines 53-55 asserts `"Bash" not in tools`. S1 inverts it.
- `envelope-expansions.log` bare-string in fixtures: **TWO INVERSIONS.** `test_slice_orchestrator_artifact_preservation.py` (line 49 + `test_d2_phase_artifact_files_copied_byte_identical`) and `test_orchestrator_events_capture.py::populated_current_slice` (line 73) put the file at the bare path; S4.a redirects the helper to `integration/`, so fixtures fall through to missing-source skip and silently lose coverage.

Per slice-specific directive: surfacing structurally, NOT silently expanding the envelope. Returning `RAISE_ISSUE` with proposed expansion list — operator routes. This is the slice's first L-014 dogfood; suppressing defeats the lesson on the slice that creates it.
