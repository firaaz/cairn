# /start-slice (legacy prose protocol)

Fallback path. Invoke via `/start-slice --legacy` or env `CAIRN_LEGACY_START_SLICE=1`. Bypasses the orchestrator (`scripts/slice_orchestrator.py`) and defers to the prose protocol preserved in `start-slice.full.md`.

Use this when the agent dispatch path is unavailable (mid-bootstrap, sandbox without `claude`), under adversarial review of the orchestrator's behaviour, or when a deliberate human-driven walk through the four phases is preferable to autonomous dispatch. Retained until ≥5 clean compressed slices have landed (compression design §10).

## Load full

- Always: read start-slice.full.md for the canonical pre-refactor prose protocol — phase rules, slice.yaml schema, gate validation, completion sequence, failed-slice archive protocol.
