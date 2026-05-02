# Phase 4 handoff — v1-defense-d2/inv-003-phase-topology-binding

## Outcome
OK. INV-003 upgraded from grep-proxy to a true four-way phase-topology binding. Validator green; INV-003 suite 27/27; full pytest matches the inherited handoff baseline (2 pre-existing L-015 XPASS-strict failures).

## What landed
- `scripts/validate_architecture.py`: `validate_phase_topology()` cross-checks `ROLE_FOR_PHASE` (core.py), Phase Skill Guide tables (operational-reference.md), `.claude/agents/phase-N-*.md` filenames, and `ROLE_DENY_READ` (role_guard.py); invoked from the assertion loop via `test-ref`.
- `docs/ARCHITECTURE.md`: INV-003 block now `test-ref`; D2 paragraph updated to record the landed binding.
- `checks/role_guard.py`: explanatory comment at the top of `ROLE_POLICIES` records the option-(b) phase-3 asymmetry.
- `tests/unit/test_inv_003_phase_topology.py`: 27 tests covering positive agreement and the four declared failure modes (drop a phase, rename a role, drift a `ROLE_DENY_READ` key, add stray `phase-5-*.md`).

## Decision recorded
Option (b) — envelope-grant-only for `phase-3-implementer` is tolerated. Comment names the asymmetry at `checks/role_guard.py:48-55`.

## Inherited debt (unchanged)
- L-015 substrate Slice 4 (extractor disk-fallback) → 2 XPASS(strict) failures.
- Phase-2-skeptic write-timing bug (issue #26 follow-up).
- INV-004 rebaseline for CC 2.1.126 (not observed failing this run; monitor).

## Next
No firm Next from this slice. Operator can pick from the inherited debt list.

---
# Sweep notes — v1-defense-d2/inv-003-phase-topology-binding

## Phase 4 Integration audit

- `uv run pytest`: 1223 passed, 3 skipped, 2 xfailed, 2 failed. Both failures (`test_extractor_slice::test_extracts_at_least_four_slices`, `test_emits_parent_edge_to_feature`) are pre-existing XPASS(strict) entries tracked in `.claude/handoff.md` against L-015 / substrate Slice 4. Out of scope for this slice.
- `uv run scripts/validate_architecture.py`: ALL CHECKS PASSED (10 invariants, 20 ADR files). The new INV-003 `test-ref` block resolves cleanly.
- INV-003 dedicated suite: `uv run pytest tests/unit/test_inv_003_phase_topology.py -q` → 27 passed.
- Phase 3 introduced no edits to source/tests beyond the declared envelope. Diff scope: `scripts/validate_architecture.py` (+222), `docs/ARCHITECTURE.md` (assertion block + D2 paragraph), `checks/role_guard.py` (asymmetry comment), `scripts/checks_role_guard_module.py` (loader shim) — all within envelope or auxiliary to it.

## Invariants table

| Invariant | Statement (canonical, abbreviated) | Status | Evidence |
|-----------|------------------------------------|--------|----------|
| INV-003 | Every slice runs through exactly four phases in order — Intent (Reader), Validation (Skeptic), Implementation (Builder), Integration (Auditor); phase count, names, and role assignments are locked. | PASS | `scripts/validate_architecture.py:454-560` (`validate_phase_topology`); `docs/ARCHITECTURE.md:33-39` (test-ref block); `tests/unit/test_inv_003_phase_topology.py` 27/27 green |

## Asymmetry decision (recorded)

Option (b) selected: phase-3-implementer's missing static `ROLE_POLICIES` entry is intentional per `compression-infrastructure-bootstrap` (envelope-driven write gate). The binding tolerates this because the role appears in `ROLE_DENY_READ`, and an explanatory comment was added at `checks/role_guard.py:48-55` naming the asymmetry.

## Out-of-scope / pre-existing

- `test_extractor_slice` two XPASS(strict) — substrate Slice 4 (L-015). Inherited.
- `test_inv004_turn1_token_budget` — not observed failing in this run.
- INV-001 / INV-002 bindings — separately scoped in `invariant-binding-strategy`.
