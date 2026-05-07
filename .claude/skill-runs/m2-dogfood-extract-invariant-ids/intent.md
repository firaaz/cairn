---
id: m2-dogfood-extract-invariant-ids
name: M2 dogfood — extract invariant ids
snapshot-sha: 743ec9c4d5b575a5269c98c006379c932e11d7d6
invariants-touched: []
---

## What

A pure Python function `extract_invariant_ids(text: str) -> list[str]` that scans arbitrary text for `INV-NNN` tokens (exactly three decimal digits, case-sensitive prefix `INV-`) and returns them sorted and deduplicated.

## Why

Provides a self-contained, I/O-free target to exercise all four phases of the `cairn-tdd-feature` skill as M2 dogfood evidence for the cairn-shrink design. No orchestrator entanglement, no external dependencies, no ambiguous side effects.

## Boundary

New file `scripts/lib/invariant_id_extractor.py` plus an empty `scripts/lib/__init__.py` to make the package importable. No existing code, configuration, or hooks are modified. The function has no I/O, no logging, and no caching.

## Specification

```python
def extract_invariant_ids(text: str) -> list[str]:
    """Return sorted, deduplicated INV-NNN identifiers from `text`.

    NNN is exactly three digits. Matches are case-sensitive on `INV-`.
    """
```

Behaviors:

1. Empty string returns `[]`.
2. Text with no `INV-NNN` patterns returns `[]`.
3. Single occurrence `"INV-001"` returns `["INV-001"]`.
4. Multiple distinct ids are returned sorted: `extract_invariant_ids("INV-008 see also INV-001")` → `["INV-001", "INV-008"]`.
5. Duplicate occurrences collapse to one entry: `extract_invariant_ids("INV-001 and INV-001")` → `["INV-001"]`.
6. Two-digit (`INV-99`) and four-digit (`INV-9999`) forms do NOT match; result is `[]`.
7. Lowercase prefix `inv-001` does NOT match; result is `[]`.
8. The regex `INV-\d{3}` carries no word boundaries; `"xINV-001y"` DOES match and returns `["INV-001"]`. Tests must document this explicitly.

## Verification

Tests at `tests/unit/test_invariant_id_extractor.py` covering all eight behaviors above.

Phase 4 confirms: full suite passes; `validate_architecture.py` reports no new failures; `invariants-touched: []` so the invariant evidence section is empty by design.
