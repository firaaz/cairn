# Approach — INV-003 phase-topology binding (Phase 2 RED)

## Decision: option (b) for the asymmetry

Per intent §Asymmetry decision: phase-3-implementer carries no static
`ROLE_POLICIES` entry; its write-path gate is granted dynamically per
`AGENT_ENVELOPE` under `compression-infrastructure-bootstrap`. Operator
recommendation in the brief is option (b) — tolerate envelope-grant-only as
intentional, with explanatory comment in `role_guard.py`. Tests encode (b):

- `test_phase_3_implementer_absent_from_role_policies_via_text` — guard.
- `test_role_guard_has_explanatory_asymmetry_comment` — RED until Phase 3
  adds the comment naming the role, the envelope mechanism, and the
  intentionality marker.
- `test_binding_tolerates_phase_3_envelope_grant_only` — RED until the
  binding lands and accepts the asymmetric source-4 projection.

## Public surface

The brief commits to `validate_phase_topology(project_root: Path) -> list[str]`
in `scripts/validate_architecture.py`. Tests import this function directly.
The internal implementation (separate "phase-topology" assertion type vs
direct call) is not constrained by the tests; only the entry-point shape and
end-to-end invocation surface are.

## Test strategy

- **Clean-tree agreement (3)** — function on CAIRN_ROOT, validator subprocess
  on CAIRN_ROOT, and seeded tmp_path all return no failures.
- **Per-source perturbations (10)** — copy four real sources to tmp_path,
  mutate one, assert non-empty failures + source/pair named in message.
  Covers all five failure modes from intent (drop phase, rename role, key
  drift, extra agent, missing agent).
- **Failure-message contract (2)** — perturbations produce messages naming
  both the offending source and the offending (phase, role) pair.
- **ARCHITECTURE.md surface (4)** — INV-003 block present, old grep proxy
  removed, new block references the binding entry, D2 paragraph no longer
  marks INV-003 "out of scope".
- **Out-of-scope guards (3)** — INV-001/INV-002 blocks intact and
  `ROLE_FOR_PHASE` shape preserved (no refactor leakage).

## Ambiguities flagged & resolved

- A1 — entry-point name: `validate_phase_topology` per brief (intent omits).
- A2 — comment placement: not constrained; test inspects all `#` lines in
  `role_guard.py`. Phase 3 chooses location.
- A3 — failure-message format: not pinned; tests use loose substring checks
  for source name + pair tokens.
- A4 — assertion-block field shape: tests check `parse_assertion_blocks`
  output for a non-grep type referencing the new binding name.

No ambiguity required RAISE_ISSUE. RED state: 21 failed, 6 guard-passes.
