# Approach - rename-sweep-test-robust (Phase 2 Skeptic)

## Scope

Widen tests/unit/test_adr_rename_sweep.py from a fixed-12-file cardinality
latch into a flat-slug shape guard over the live docs/adr/ corpus, while
preserving rename-outcome regression (V1 targets, V2 ids, V4 residue,
V5 index, V6 changelog).

## Strategy for Phase 3

1. Drop test_exact_twelve_adr_files_total. Do not reintroduce any assertion
   comparing the docs/adr/ file set (or its length) to a static whole-corpus
   enumeration.
2. Keep UNRENAMED_ADR_FILES iff repurposed strictly as a historical record;
   never as an exhaustive allowlist for live-corpus shape checks.
3. Add a parametrized shape test: enumerate docs/adr/*.md minus index.md
   and per-file assert (a) filename matches ^[a-z][a-z0-9-]*.md$, (b) YAML
   id: equals stem. Assertion messages MUST embed the offending filename.
4. Update the module docstring to name the widened contract (flat-slug
   shape guard, not size-latched - include shape and one of size-latch,
   size latch, not size-latched, cardinality).
5. Never mention the post-sweep ADR slug literally in the test source.

## Skeptic test layout

Envelope is a single file; a separate contract-test file is scope-guard
blocked. Skeptic classes are embedded at the tail of the sweep file as
TestContractC1..C6 with a preservation banner. Driver tests (C3 valid-
corpus pass, C4 robustness under growth) shell sys.executable -m pytest
self with --deselect on C3 and C4 to prevent recursion, staging synthetic
ADRs in docs/adr/ (valid flat-slug, malformed underscore filename, stem/id
mismatch) and asserting subprocess exit code plus failure-message content.

## Coverage map

- C1: size-latch retirement (intent Spec 1, V2). 2/3 probes RED pre-P3.
- C2: no hardcoded post-sweep ADR slug (V3). GREEN pre-P3 (constructed
  via fragment join so probe itself does not contribute to grep count).
- C3: current-corpus pass (V1). RED pre-P3 (size-latch trips on 13 files).
- C4: robustness under growth (V4) - valid green, malformed red w/name.
- C5: rename-outcome regression guards retained (Spec 4, V5). GREEN pre-P3.
- C6: module docstring widened (Spec 7). 2/2 RED pre-P3.

## Out of scope

No ADR file edits. No hook / validator / tolerance-test changes. Fixtures
create-and-revert; docs/adr/ untouched across runs.
