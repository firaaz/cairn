---
slice: SLICE-018 (identifier-scheme/validator-flat-slug)
phase: complete
branch: slice/identifier-scheme-validator
as-of: 2026-04-16 a057bbc
---

## State
SLICE-018 closed. Validator recognizes flat-slug ADR ids alongside legacy `ADR-NNN`; 238/238, validator self-check exit 0, integration_gate.py PASS. D3 snapshot_diff flagged `docs/ARCHITECTURE.md` (INV-005 parenthetical re-pointed in Phase 3 as acknowledged scope deviation); bypass logged as slice-caused, baseline refreshed.

## Next
Run `/integration-sweep` in a fresh session (slice 18, interval 1, last sweep at 17 — due).

## Blocked / Pending
- `/refresh-architecture` deferred to coordinator level → clears `docs/ARCHITECTURE.md:116` stale substrate-gap + ADR-006 proxy clauses that contradict line 49.
- Uncommitted `docs/plans/measurements/2026-04-12-slice-003.txt` → unrelated to SLICE-018; triage separately.
- Stale envelope-compliance tests (SLICE-005 V7, SLICE-007 V4) → diff working tree against HEAD.
- `docs/ARCHITECTURE.md:46` INV-004 "22k token budget" stale; `tests/unit/test_context_budget.py:103` docstring stale.
- d3-bypass-classification substrate implementation slice → queued.
- `reversibility-guard.sh` relative-path bypass → queued.

## Features
- identifier-scheme: SLICE-018 closed; validator-flat-slug + hook-tolerance + scheme-adr all landed. Phase 2 one-shot rename sweep and Phase 3 legacy-format drop deferred per ADR D7.
- v1-defense-d2: SLICE-010/011 queued.
- v1-defense-d3: ADR landed; substrate implementation slice pending.

## Pointers
- `.claude/d3-bypasses.log` — SLICE-018 slice-caused entry; sweep should cross-check against three-class schema.
- `docs/ARCHITECTURE.md:49, :116` — line 49 now cites `(identifier-scheme)`; line 116 still says "queued substrate work" + "ADR-006 as validator-anchored proxy". Refresh target.
- `scripts/validate_architecture.py:160, :171, :319` — widened ref + frontmatter-id resolution; sweep verifies no regression.
