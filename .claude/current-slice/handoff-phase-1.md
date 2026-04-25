---
slice: compression/lever-2-orchestrator-split
phase: 1-intent → 2-validation
branch: feature/compression
as-of: 2026-04-25 18afa0c
---

## State
Phase 1 (Reader) complete. `intent.md` declares: package layout (§S2), public-surface re-export contract (§S3), CLI entry-point contract (§S4), doc/command path-string updates (§S5), test-file invariance with single gate-file exception (§S6), invariant preservation (§S7). Verification gates V1–V8 enumerated. Envelope amendment 18afa0c added the gate test file path before Phase 2 dispatch.

## Next
Dispatch `phase-2-skeptic` subagent in a fresh session with `intent.md` as sole input; produce RED tests at `tests/unit/test_slice_orchestrator_package_split.py` plus `validation/approach.md`.

## Blocked / Pending
- OQ2 (CLI invocation form `python -m` vs path-to-`__main__.py`) — Phase 3's call, recorded for Builder
- OQ3 (`__init__.py` re-export style — star vs explicit) — Phase 3's call, recorded for Builder
- Skeptic must enumerate any remaining ambiguities before writing tests; escalate via RAISE_ISSUE if a gate is unprovable from intent.md alone

## Pointers
- `.claude/current-slice/intent.md` — sole Phase 2 input; do not read source code or Phase 3 implementation
- `intent.md` §S3 — full public-name list (test V2 enumerates this)
- `intent.md` §V1–V8 — verification gates the Skeptic's RED tests must mechanise
- `intent.md` `out-of-scope:` — boundary the Skeptic must respect; tests touching anything outside envelope must be rejected
