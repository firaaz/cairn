---
id: trial-e-w1-case-05
name: Trial-E W1 cross-family probe case 05
snapshot-sha: c371d72
invariants-touched: []
---

## What
Evaluate a diagnostic-only addition in `checks/atomicity_guard.py`.

## Why
The guard can add a stderr diagnostic around intent reads while preserving direct
CLI argument handling.

## Boundary
This is a measurement-only probe case. Do not implement the change.

## Specification
- Preserve direct CLI intent-path handling through `Path(argv[1])`.
- Preserve the existing unreadable-intent failure behavior.

## Premise Grounding

```yaml
premises:
  - source: checks/atomicity_guard.py
    quote: |
      intent_path = Path(argv[1])
    label: "atomicity_guard reads the intent path directly from the CLI argument"
```

## Contract

```yaml
must-satisfy:
  - when the guard reads an intent argument, it shall continue using Path(argv[1])
  - when the intent path is not readable, the guard shall keep returning an unreadable-intent failure
must-not-violate:
  - do not change project-root or cwd handling for the intent argument
wrong-if:
  - the cited source no longer reads the intent path directly from argv[1]
evidence:
  - fresh challenge verdict records whether the premise label faithfully describes the source
```
