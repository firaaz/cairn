# Phase 2 Approach — substrate/start-slice-pythonpath-paper-cut

## Stated intent (skeptic re-read)

Replace every operator-facing occurrence of `python -m slice_orchestrator`
in four documentation files with `PYTHONPATH=scripts uv run python -m
slice_orchestrator`. Pure prose change; orchestrator code untouched.

## Test surface

One file: `tests/unit/test_start_slice_dispatcher_doc.py`. Two
parametrized tests, four parametrizations each (8 RED at slice open):

1. `test_envelope_doc_has_no_bare_dispatcher_reference` — for each of the
   four envelope docs, scans every line and asserts the regex
   `(?<!uv run )python -m slice_orchestrator` matches zero times. Failure
   message reports `(lineno, line)` tuples so Phase 3 can locate the edit.
2. `test_envelope_doc_uses_canonical_prefix_when_dispatcher_named` —
   asserts the canonical `PYTHONPATH=scripts uv run python -m
   slice_orchestrator` substring is present in each envelope doc body.
   Guards against a vacuous Phase-3 fix that deletes references rather
   than rewriting them.

## Ambiguities resolved

- **Inline backticked references** (`` `python -m slice_orchestrator` ``
  inside prose): intent §Specification treats these as in-scope. The
  regex is a substring match, so backticks don't matter.
- **Multiple references on one line** (e.g. `--brief|--resume|--legacy`
  on the changelog/feature line): a single rewrite to `PYTHONPATH=scripts
  uv run python -m slice_orchestrator --brief|--resume|--legacy` settles
  the negative-lookbehind in one shot.
- **Self-reference hazard**: the test file itself contains the bare-form
  string in its docstring (explaining what it's banning). The test only
  iterates the four envelope docs — its own body is never scanned, so
  the test will not flag itself.
- **Out-of-scope files**: `docs/lessons.md`, `docs/plans/**`,
  `docs/adr/**`, `docs/operational-reference.md`,
  `.claude/sweep-results/**`, `.claude/completed-slices/**`,
  `.claude/features/**`, `.claude/current-slice/**`, and
  `scripts/slice_orchestrator/**` are explicitly NOT scanned per intent
  §Boundary. The test's `ENVELOPE_DOCS` tuple is the closed enumeration.

## RED confirmed

`uv run pytest tests/unit/test_start_slice_dispatcher_doc.py` — 8 failed,
0 passed at slice open. Each parametrization names its envelope doc;
test-1 failures cite the offending `(lineno, line)`; test-2 failures
confirm canonical prefix absent.

## Phase 3 hand-off

Replace the bare form on each of the four lines (start-slice.md:3,
start-slice-legacy.md:3, CHANGELOG.md:14, docs/features/compression.md:57)
with the canonical prefix; re-run the test; expect 8 GREEN.

No new ADRs needed; no invariants touched.
