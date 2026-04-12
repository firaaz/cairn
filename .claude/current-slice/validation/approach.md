# SLICE-004 Phase 2 — Validation Approach

## Ambiguities resolved

1. **Log entry format**: fenced YAML code blocks (` ```yaml ... ``` `), not `---`-delimited YAML documents.
2. **Duplicate entries**: same slice+defense+date with different description → both counted, stderr warning for human review.
3. **Post-ADR-003 baseline**: read from `dogfood-log.md` frontmatter field `adr-003-landed-at-slice` (not hardcoded). Intent's "minus 2" comment was factually wrong about when ADR-003 landed; the frontmatter approach decouples the evaluator from that history.
4. **`sweep.yaml` missing**: exit 2 (same as missing log — insufficient data).
5. **`would-manual-have-caught: unclear`**: counts toward catch-rate criterion (it's evidence of an automated catch), but overall evaluation fails until all `unclear` entries are resolved to `yes` or `no`. Shown separately in output. Disincentivizes lazy classification.
6. **False-positive threshold scope**: cumulative (lifetime of log), not windowed. The dogfood gate itself is a ~10-slice window; a window within a window adds no value at this scale.

## Test structure

Single file: `tests/unit/test_dogfood_evaluate.py`. 18 tests total, grouped by verification assertion (V1–V6) plus ambiguity resolutions. All subprocess-based, following `test_validate_architecture.py` conventions. Fixture helpers create tmp_path log files and sweep.yaml.

`_assert_evaluator_ran()` guard on every test prevents false greens from Python's own exit-2 on missing script.
