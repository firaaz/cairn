---
id: trial-e-w1-bogus-source
name: Trial-E W1 bogus source discriminator
snapshot-sha: c371d72
invariants-touched: []
---

## What
Confirm the W1 harness distinguishes semantic blocks from missing-source blocks.

## Premise Grounding

```yaml
premises:
  - source: checks/does_not_exist_for_trial_e_w1.py
    quote: |
      this quote is intentionally unreachable
    label: "bogus source discriminator"
```
