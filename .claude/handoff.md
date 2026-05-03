---
slice: none
phase: n/a
branch: feature/compression-followup
as-of: 2026-05-03 fd1823e
---

## State
INV-001 bound to true `git-log-walk` machine-check at slice close `2fb83f6`; `binding-effective-from` set to that SHA at `fd1823e`. v1-defense-D2 progress 2/3.

## Next
Run `/integration-sweep` in a fresh session — sweep due (`sweep-interval: 1`, last at `inv-003-phase-topology-binding`).

## Blocked / Pending
- INV-002 + INV-008 binding → next slice `v1-defense-d2/inv-002-binding-implementation` (closes D2 at 3/3)
- L-015 extractor disk-fallback → 2 XPASS(strict) failures, substrate Slice 4
- INV-004 rebaseline for CC 2.1.126 → housekeeping/inv004-rebaseline-cc-2.1.126 (intermittent)
- `V1_ASSERTION_TYPES` allowlist hardcoded in tests, not sourced from substrate → future cleanup slice (auditor flagged)
- Phase-3 revert-under-RED-pressure → prompt-iteration candidate (slice 1 hit it; memory captured)

## Pointers
- `docs/plans/2026-05-02-inv-001-binding-design.md` / `-plan.md` — slice 1 reference
- `docs/adr/invariant-binding-strategy.md` — read before slice 2 (D4–D7 cover INV-002/008)
- `.claude/pipeline-substrate-registry.yaml` — live registry; ADR-amend before adding entries
- `tests/unit/test_invariant_assertions.py:1116` — allowlist; expand for any new assertion type
