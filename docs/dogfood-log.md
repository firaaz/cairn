---
schema-version: 1
adr-003-landed-at-slice: 2
---

# Dogfood Log

Append entries as fenced YAML blocks. Each entry must contain: slice, date,
defense, type, description, would-manual-have-caught, disposition.

See `scripts/dogfood_evaluate.py` for evaluation criteria and field reference.
