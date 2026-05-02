---
slice: substrate/papercut-bundle
feature: substrate
phase: 1-intent
date: 2026-05-02
adrs-referenced: []
adrs-created: []
invariants-touched: []
envelope:
  - "checks/scope-guard.sh"
  - "commands/claude-code/integration-sweep.md"
  - "scripts/verify_handoff.sh"
  - "tests/unit/test_scope_guard_admin_allowlist.py"
  - "tests/unit/test_verify_handoff_sweep_subject.py"
design-ref: "docs/plans/2026-05-02-substrate-papercut-bundle-design.md"
plan-ref: "docs/plans/2026-05-02-substrate-papercut-bundle-plan.md"
---

# Intent — substrate/papercut-bundle

## What

Land three independent, single-line substrate paper-cuts surfaced by the
2026-05-02 integration sweep:

1. **`checks/scope-guard.sh`** — extend the admin-allowlist `case` to include
   `.claude/d1-bypasses.log` and `.claude/d3-bypasses.log` so Write/Edit hook
   events on those append-only logs exit 0 under a tight slice envelope (no
   `EXPAND_ENVELOPE=1`, no Bash-heredoc bypass).
2. **`commands/claude-code/integration-sweep.md`** — change the documented
   invocation `python3 scripts/integration_gate.py` to
   `uv run python scripts/integration_gate.py`. The gate imports `pydantic`,
   which only resolves under `.venv`.
3. **`scripts/verify_handoff.sh` check (c)** — accept `sweep: ` as a fourth
   commit-subject prefix alongside `handoff:`, `phase-<N>:`, and
   `slice: ... — complete`. Update the `expected one of:` error string in
   lockstep.

## Why

Each paper-cut blocks or papers over a real downstream operator workflow
(bypass-log audit appends; copy-pasted gate command; sweep commits failing the
handoff verifier). All three are append-only / additive: each fix widens an
accepted set without changing prior behavior. Bundling them into one slice
exploits the disjoint-modules property — three single-line touches in three
different files — to amortize pipeline overhead while keeping the diff
trivially reviewable. Sweep paper-cut #3 (malformed `sweep.yaml`) was
reclassified out of scope: the design plan traces it to pre-fix data carried
through commit `6cfa4d0`, not an active orchestrator bug; the 2026-05-02 sweep
already rewrote the file to protocol shape.

## Boundary (out of scope)

- `scripts/integration_gate.py` itself — no re-exec / bootstrap path; the
  documented invocation is the authoritative entry point.
- The pre-commit hook chain — adding `verify_handoff.sh` to it is a separate
  design question; extending check (c)'s regex is sufficient for existing
  callers (`close_slice`, `tests/unit/test_orchestrator_bug_fixes.py`).
- Issue #26 (phase-2-skeptic stage surface) — owned by the next slice
  `substrate/phase-2-skeptic-stage-surface`, sequenced after this one per the
  design plan.
- Pre-existing reds (`test_d3_bypass_log_format`, `test_extractor_slice` XPASS)
  — tracked under separate housekeeping/v1-defense-d3 slices.

## Specification

### Modification slice — public interfaces only

**`checks/scope-guard.sh`** — admin-allowlist contract widens by two paths:

```
.claude/d1-bypasses.log  → exit 0 (admin-allowed, envelope-independent)
.claude/d3-bypasses.log  → exit 0 (admin-allowed, envelope-independent)
```

No change to deny semantics, scope-stripping behavior, or non-admin paths.

**`commands/claude-code/integration-sweep.md`** — documented invocation
contract changes from `python3 scripts/integration_gate.py` to
`uv run python scripts/integration_gate.py`. No semantic change to the gate;
only the surface form humans/agents copy.

**`scripts/verify_handoff.sh`** — check (c) accepted-subject set widens from
`{handoff:, phase-<N>:, slice: ... — complete}` to add `sweep: ` as a fourth
arm. The `expected one of:` error message updates to enumerate all four
forms. Exit codes unchanged: 0 on accept, 1 on reject.

### Test surface (Phase 2 RED targets)

- `tests/unit/test_scope_guard_admin_allowlist.py` — parametrized over
  `.claude/d1-bypasses.log` and `.claude/d3-bypasses.log`; each invokes
  `scope-guard.sh` against a synthetic Write hook input under a slice
  whose envelope excludes the log; expects exit 0.
- `tests/unit/test_verify_handoff_sweep_subject.py` — initialises a tmp git
  repo with HEAD subject `sweep: post-demo — PASS`; invokes
  `verify_handoff.sh`; expects exit 0.
- No new test for paper-cut #2 (pure doc): no regression surface, and CI
  already runs under uv.

### INV-008 / invariants

None touched. All three changes are additive and live outside the
orchestrator's phase-boundary commit machinery.

## Verification

1. Phase 2 RED: `uv run pytest tests/unit/test_scope_guard_admin_allowlist.py
   tests/unit/test_verify_handoff_sweep_subject.py -v` → both fail.
2. Phase 3 GREEN: same command → both pass.
3. Full-suite regression: `uv run pytest tests/unit/ -q` → matches
   2026-05-02 sweep baseline (1160 pass / 2 known fail / 3 skipped /
   3 xfailed); no new failures.
4. Phase 4 sweep: `scripts/integration_gate.py`, `snapshot_diff.py --diff`,
   full pytest. Sweep-notes recorded.
5. Post-close: `git status --short` clean.
