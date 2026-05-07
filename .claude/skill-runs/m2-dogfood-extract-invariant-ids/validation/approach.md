---
phase: 2
feature_id: m2-dogfood-extract-invariant-ids
---

# Phase 2 — Approach memo

## Tests written (8)

| # | Function | Behavior |
|---|----------|----------|
| 1 | `test_empty_string_returns_empty_list` | Empty string → `[]` |
| 2 | `test_no_matching_pattern_returns_empty_list` | No pattern match → `[]` |
| 3 | `test_single_occurrence_returns_list_with_one_entry` | `"INV-001"` → `["INV-001"]` |
| 4 | `test_multiple_distinct_ids_returned_sorted` | `"INV-008 see also INV-001"` → `["INV-001", "INV-008"]` |
| 5 | `test_duplicate_occurrences_collapsed_to_one` | `"INV-001 and INV-001"` → `["INV-001"]` |
| 6 | `test_two_digit_and_four_digit_forms_do_not_match` | `"INV-99 INV-9999"` → `[]` |
| 7 | `test_lowercase_prefix_does_not_match` | `"inv-001"` → `[]` |
| 8 | `test_embedded_in_word_does_match` | `"xINV-001y"` → `["INV-001"]` |

## Ambiguity resolutions

**Behavior 8 (word-boundary question):** intent.md is explicit — the regex is `INV-\d{3}` with no `\b` anchors, so `"xINV-001y"` DOES match. Test docstring documents this contract verbatim so a future reader cannot mistake it for an oversight.

**Return type:** spec signature is `list[str]`. Tests assert equality against Python lists; sorted order is lexicographic string sort, which matches numeric sort for zero-padded three-digit IDs (000–999).

**Deduplication mechanism:** spec says "sorted, deduplicated". Tests rely on the observable contract (one entry per id), not the implementation mechanism (set, dict, etc.).

## Flags for human review

None. The spec is unambiguous on all eight behaviors. The `invariants-touched: []` field is intentional by design; Phase 4 confirms no invariant evidence section is required.

## Failure confirmation

`uv run pytest tests/unit/test_invariant_id_extractor.py -v` exits 2 with:
`ModuleNotFoundError: No module named 'scripts'`
(collection error — `scripts.lib.invariant_id_extractor` does not exist yet, as intended).
