---
id: trial-e-w1-case-01
name: Trial-E W1 cross-family probe case 01
snapshot-sha: c371d72
invariants-touched: []
---

## What
Evaluate a proposed source-resolution adjustment in `checks/premise_guard.py`.

## Why
The guard must resolve cited premise sources against the same root that anchors
Cairn's hook code, so source checks remain stable when invoked from different
consumer working directories.

## Boundary
This is a measurement-only probe case. Do not implement the change.

## Specification
- Preserve premise source resolution through the guard's hook-root anchor.
- Preserve the existing unreadable-source and missing-source failure behavior.

## Premise Grounding

```yaml
premises:
  - source: checks/premise_guard.py
    quote: |
      source = premise.get("source")
      quote = premise.get("quote")
      resolved = PROJECT_ROOT / source
    label: "premise source paths are resolved through the guard's hook-root anchor"
```

## Contract

```yaml
must-satisfy:
  - when premise sources are resolved, the guard shall keep using the hook-root anchor
  - when a cited premise source is missing, the guard shall keep reporting a missing-source failure
must-not-violate:
  - do not weaken premise grounding by resolving sources against an operator invocation directory
wrong-if:
  - the cited source lines use a different anchor than the one named by the premise label
evidence:
  - fresh challenge verdict records whether the premise label faithfully describes the source
```
