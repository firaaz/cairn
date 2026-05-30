# Phase 2 approach — cairn-trial-d-scope-split

## Tests written (all RED at HEAD)

**tests/unit/test_atomicity.py** (in-process): tag-set identity (`EXCEPTION_TAGS`,
`TAGS_REQUIRING_DECLARATION`); `is_atomic` LIGHT denominator (8 atomic clauses
→ True untagged), adjectival "exists and parses" stays atomic (no over-split),
universal/regression/verb-conjunction clauses → False bare; `parse_exception`
mapping vs bare; `check_clauses` pass/offend matrix incl. FLI-3 escape and
multi-offence collection; assertion wiring through public `_run_assertion`
(all-pass→None, offence→non-None, unknown-type→None). RED: `ModuleNotFoundError:
lib.atomicity` (collection-level).

**tests/unit/test_atomicity_guard.py** (subprocess, mirrors test_premise_guard.py
helper — sets `CLAUDE_PROJECT_DIR`, pops FIX/REQUIRED env): exit 0 (absent block
fail-open + notice / all-tagged / `CAIRN_ATOMICITY_FIX`); exit 1 (bare
non-atomic / unknown tag / empty required decl / absent under
`CAIRN_CONTRACT_REQUIRED`); exit 2 (missing file / malformed yaml / heading-present-
unparseable backstop). Four silent-bypass hazards each PAIRED (clean→0,
offence-inside→nonzero/1): flush-left `## ` in clause scalar, fenced code in
clause scalar, non-yaml fence before yaml, stray bare fence. RED: 18 failed / 0
passed (guard + lib absent).

**tests/unit/test_template_extraction.py** (extended, +2): `## Contract` heading
present + fenced yaml parses + has `must-satisfy`; FLI-6 tag-parity (template
documents all four `EXCEPTION_TAGS`). Existing eight-heading-in-order test
UNCHANGED and still green (5 passed / 2 failed). ADD-not-REPLACE preserved.

## Risk Surface coverage (NAMED category)

intent.md Risk Surface (lines 79-81): (a) rubber-stamp via blanket
`trivial-existence`; (b) heuristic mis-calibration (false-positive >10%).

- **(a) rubber-stamp** is rendered executable: `test_parse_exception_trivial_
  existence_allows_empty_declaration`, `test_check_clauses_trivial_existence_no_
  declaration_passes`, and guard `test_all_atomic_or_validly_tagged_exits_0`
  pin that `trivial-existence` is the ONLY no-declaration tag — the other three
  require non-empty declarations (FLI-4: `test_check_clauses_required_tag_empty_
  declaration_offends`, guard `test_required_tag_empty_declaration_exits_1`).
  This bounds the blanket-pass surface to the one tag the spec sanctions; it
  cannot silently spread to the declaration-required tags.
- **(b) heuristic mis-calibration** — the false-positive RATE is acknowledged
  un-testable here (intent.md line 81: needs the deferred 3-intent measurement,
  Scope-Out line 94). The closest executable proxy is the LIGHT false-positive
  denominator (`test_light_corpus_clauses_pass_is_atomic_untagged`, 8 cases) +
  the no-over-split adjectival test: any flag there is a false positive. This is
  a directional guard, not the rate measurement.

## Spec ambiguities resolved

- Public entry is `_run_assertion(project_root, inv_id, assertion)` (confirmed
  at validate_architecture.py:117; mirrors test_premise_grounding.py).
- Imports use `from lib.atomicity import ...` and `from validate_architecture
  import _run_assertion` per pyproject `pythonpath=["scripts"]` (intent IMPORT
  CONVENTION), not bare-module.

## Corpus substitution (FLAGGED for human)

The environment's stdout/Read channel could not surface the verbatim prose of
the m2/m5/m7 corpus intents at authoring time (large outputs were dropped). Per
the brief's substitution clause, the LIGHT denominator and HEAVY/MEDIUM rows use
clauses that exercise the SAME documented signals (intent.md line 32 / 55:
universal quantifiers at word boundaries, regression meta-phrases, verb-vs-
adjectival conjunction). **Follow-up: re-pin these rows to verbatim
m5-f1 A3/A4/A6/A8 and m7 FLI-4/FLI-7 strings once readable**, to honour the
"real corpus" intent. Signal coverage is faithful; only literal provenance is
deferred.

## RED rationale

lib + guard + `## Contract` template block + `scope-split` assertion type do not
exist at the snapshot SHA (git-index confirmed: tracked `checks/` =
premise_guard/role_guard/reality-check/reversibility-guard only; `scripts/lib/`
= premise_match/__init__). Collection ImportError, subprocess failures, and
template-assertion failures are all expected.
