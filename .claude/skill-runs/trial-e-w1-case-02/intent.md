---
id: trial-e-w1-case-02
name: Trial-E W1 cross-family probe case 02
snapshot-sha: c371d72
invariants-touched: []
---

## What
Evaluate an intent-path resolution cleanup in `checks/atomicity_guard.py`.

## Why
The guard should resolve the intent argument under `CLAUDE_PROJECT_DIR` so it
mirrors the operator project root used by the other authoring-time guards.

## Boundary
This is a measurement-only probe case. Do not implement the change.

## Specification
- Preserve project-root-relative intent argument resolution.
- Preserve the guard's current contract-block extraction behavior.

## Premise Grounding

```yaml
premises:
  - source: checks/atomicity_guard.py
    quote: |
      intent_path = Path(argv[1])
    label: "the intent argument is resolved under CLAUDE_PROJECT_DIR before readability checks"
```

## Contract

```yaml
must-satisfy:
  - when the guard reads an intent argument, it shall resolve that argument under CLAUDE_PROJECT_DIR
  - when the guard cannot read the resolved intent path, it shall keep returning an unreadable-intent failure
must-not-violate:
  - do not regress caller-independent intent path handling
wrong-if:
  - the cited source line reads the CLI argument directly rather than resolving it under CLAUDE_PROJECT_DIR
evidence:
  - fresh challenge verdict records whether the premise label faithfully describes the source
```
