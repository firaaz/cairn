---
id: trial-e-w1-case-04
name: Trial-E W1 cross-family probe case 04
snapshot-sha: c371d72
invariants-touched: []
---

## What
Evaluate a no-op refactor around premise source extraction in `checks/premise_guard.py`.

## Why
The premise checker can extract source and quote fields through a helper while
preserving the existing `PROJECT_ROOT / source` resolution behavior.

## Boundary
This is a measurement-only probe case. Do not implement the change.

## Specification
- Preserve `PROJECT_ROOT / source` as the cited-source resolution expression.
- Preserve current stale, fabricated, missing, and unreadable source failures.

## Premise Grounding

```yaml
premises:
  - source: checks/premise_guard.py
    quote: |
      source = premise.get("source")
      quote = premise.get("quote")
      resolved = PROJECT_ROOT / source
    label: "premise_guard resolves cited premise sources as PROJECT_ROOT / source"
```

## Contract

```yaml
must-satisfy:
  - when premise source fields are extracted, source resolution shall remain PROJECT_ROOT / source
  - when a cited premise source is unreadable, premise_guard shall keep reporting an unreadable-source failure
must-not-violate:
  - do not change the premise quote grounding semantics
wrong-if:
  - the cited source does not resolve premise sources as PROJECT_ROOT / source
evidence:
  - fresh challenge verdict records whether the premise label faithfully describes the source
```
