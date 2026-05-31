# Trial-D measurement scratch — LIGHT (m2-dogfood-extract-invariant-ids)

ASSISTANT INSTRUMENTATION ONLY. The `## Contract` -> `must-satisfy` list at the bottom
is AUTHORED BY THE OPERATOR. If the assistant fills it, metrics #1 (authoring-time) and
#2 (rubber-stamp reduction) are VOID (plan Step 2).

Source intent: .claude/skill-runs/m2-dogfood-extract-invariant-ids/intent.md
  (completed-run record; copied below for derivation — do NOT edit the original).
Behaviors to derive from: the 8 numbered behaviors (b1-b8) in `## Specification`.
Post-F1 sanity: b2 ("...returns no INV-NNN patterns") and b8 ("...no word boundaries")
  must now pass BARE (they were the dropped \bno\s false-positive signal).

Operator procedure (do LIGHT first, then MEDIUM, then HEAVY):
  1. Start a stopwatch.
  2. In the `## Contract` block at the BOTTOM of this file, author one atomic EARS
     clause per behavior in the derivation source. Split, or tag with one of
     {universal-set, regression-meta, operator-bound, trivial-existence}, any clause
     that isn't a single tool-call or single file-check. Tagging is the one-line
     escape from a flagged clause.
  3. Stop the stopwatch. Record elapsed + your felt-prose-baseline estimate -> metric #1.
  4. Note any clause where deciding "split vs tag vs leave atomic" surfaced a call you
     would otherwise have waved through -> metric #2 (binary per intent).
  5. Say "<size> ready". The assistant runs
     `uv run python checks/atomicity_guard.py <this-file>` and proposes false-positive
     labels for the flagged clauses; you adjudicate -> metric #3.

EARS shapes (write each must-satisfy item as ONE of these):
  Ubiquitous : the <system> shall <response>
  Event      : when <trigger>, the <system> shall <response>
  State      : while <state>, the <system> shall <response>
  Option     : where <feature>, the <system> shall <response>
  Unwanted   : if <condition>, then the <system> shall <response>

Atomicity (ADR D3): a clause is atomic iff verifiable by a single tool call or single
file check. Untagged clauses must pass atomicity. A non-atomic clause must be split into
atomic clauses OR carry one tag (mapping form {clause: "<EARS>", except: "<tag>: <decl>"}):
  universal-set     - quantifies over a set; declaration enumerates the set
  regression-meta   - "unchanged"/"no regression"; declaration names the baseline
  operator-bound    - needs human action/judgement; declaration names the operator step
  trivial-existence - a file/output simply exists; NO declaration required
The first three tags require a non-empty declaration; an unknown tag always fails.

----- derivation source (verbatim copy of the read-only original) -----


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

## Contract

```yaml
# OPERATOR AUTHORS must-satisfy — one atomic EARS clause per behavior in the derivation source.
# Bare string  -> atomicity-checked.
# Mapping form -> {clause: "<EARS>", except: "<tag>: <declaration>"}  (atomicity-waived).
# The assistant intentionally left this empty; filling it voids metrics #1/#2.
must-satisfy: [ 'if empty value return []', 'if unable to match to the required INV-XXX pattern return []', 'Match strictly to 3 digit numbers', 'Only caps allowed'
]

# The five lists below are NOT measured (the gate checks only must-satisfy).
# Leave empty, or fill if you want a complete block.
must-not-violate: []
wrong-if: []
escalate-when: []
evidence: []
execution-scope: []
```
