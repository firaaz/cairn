```yaml
slice: d3-automated-backstop
date: 2026-04-14
phase: 1-intent
invariants-touched: []
adrs-referenced: [ADR-003]
envelope:
  - "scripts/validate_architecture.py"
  - "scripts/integration_gate.py"
  - "scripts/snapshot_diff.py"
  - "commands/claude-code/integration-sweep.md"
  - "commands/claude-code/integration-sweep.full.md"
  - "commands/claude-code/start-slice.md"
  - "commands/claude-code/start-slice.full.md"
  - "tests/unit/test_integration_gate.py"
  - "tests/unit/test_snapshot_diff.py"
out-of-scope:
  - "D2 assertion runner changes (SLICE-010/011 already landed)"
  - "Hook enforcement of D3 gates (v2+ per ADR-003 D4)"
  - "Windsurf portability (v2+ per ADR-003 D4)"
  - "Changes to the four-phase pipeline itself (ADR-004 locked)"
```

### What and Why

ADR-003 D3 requires promoting integration-sweep Steps 3–4 from manual to mechanically-gating, and adding a structural-snapshot-diff check that flags files whose shape changed outside the declared slice envelope. Today these checks exist only as prose instructions in `integration-sweep.md` — an agent can skip or weaken them without detection. This slice makes them executable scripts that return pass/fail exit codes, so they can gate slice-close and integration sweeps mechanically.

D3 closes the "human Step 2 degrades on AI-written code" gap (ADR-003 §D3): when the agent writing code is also the agent checking invariants, correlated blind spots are inevitable. A mechanical gate has no blind spots for the checks it implements.

### Specification Detail

**1. Integration gate script (`scripts/integration_gate.py`)**

A single-file Python script (stdlib only, matching `validate_architecture.py` conventions) that mechanizes integration-sweep Steps 3–4:

- **Step 3 gate (invariant evidence):** Delegates to D2's assertion runner — calls `validate_architecture.py`'s Check D (invariant-check block execution). D3 does not duplicate the assertion logic; it wraps and gates on it. Exit non-zero if any invariant assertion fails.
- **Step 4 gate (cross-module checks):** Runs in sequence: (a) `ruff check` on all Python files in the repo, (b) `uv run python -m pytest tests/ -x --tb=short`. Each sub-check is logged with pass/fail. Exit non-zero if any sub-check fails.

Exit codes: 0 = all gates pass, 1 = one or more gates failed (details on stderr), 2 = missing prerequisites (e.g. ruff not installed).

**2. Structural-snapshot-diff script (`scripts/snapshot_diff.py`)**

A single-file Python script (stdlib only) that:

- **Snapshot creation:** Scans all `.py` files under `scripts/`, `checks/`, `tests/`, and all `.md` files under `commands/`, `docs/`. For each file, records: file path, size in bytes, SHA-256 hash of contents. Writes the snapshot to `.claude/structural-snapshot.json` as a sorted JSON object keyed by relative path.
- **Diff mode:** Compares a prior snapshot (`.claude/structural-snapshot.json`) against the current file tree. Reports files that are new, deleted, or changed (hash differs). Cross-references against the current slice's `intent.md` envelope globs — any changed file NOT matched by an envelope glob is flagged as an out-of-envelope change.
- **Exit codes:** 0 = no out-of-envelope changes detected, 1 = out-of-envelope changes found (listed on stdout), 2 = no prior snapshot exists (first run — creates snapshot and exits 0).

The snapshot is committed at slice-close so the next sweep has a baseline.

**3. Slice-close gate wiring (`start-slice.md` / `start-slice.full.md`)**

Update the `/start-slice complete` completion sequence (Step 7) to run D3 gates at slice-close alongside the existing D1 refresh gate. The execution model uses parallel subagents dispatched after D1 completes:

```
slice-close sequence:
  1. D1 refresh gate (sequential, first)
     — /refresh-architecture + validate_architecture.py
     — modifies ARCHITECTURE.md, must complete before D3 gates read it
  
  2. D3 gates (parallel subagents, after D1)
     ├─ subagent A: integration gate
     │   — python3 scripts/integration_gate.py
     │   — returns pass/fail + details
     └─ subagent B: snapshot diff
         — python3 scripts/snapshot_diff.py --diff
         — then python3 scripts/snapshot_diff.py --snapshot (update baseline)
         — returns pass/fail + out-of-envelope file list
```

Each subagent runs in its own context and returns a short pass/fail report (≤200 words). If either gate fails, the slice MUST NOT transition to `status: complete` — same semantics as the D1 gate. The `start-slice.full.md` Step 7 "D1 Refresh Gate" section expands to a "D1 + D3 Gate" section documenting this sequence.

**D3 bypass escape hatch.** Mirrors D1's `ADR_D1_BYPASS=1` pattern: `D3_GATE_BYPASS=1` skips the D3 gates and logs to `.claude/d3-bypasses.log` (same format as `d1-bypasses.log`: `<slice-id> <YYYY-MM-DD> <one-line-reason>`). Rolling-window check: 3+ bypasses in last 10 slices triggers a warning.

**4. Integration-sweep command updates**

Update `integration-sweep.md` and `integration-sweep.full.md` to reference the new scripts. Steps 3–4 instructions change from "run these checks manually" to "run `scripts/integration_gate.py`" and "run `scripts/snapshot_diff.py --diff`". The sweep still produces a human-readable report, but the gates are now mechanically executable.

**5. Falsification test (ADR-003 D3 Phase 4 gate)**

The test suite must include a planted violation that D3's checks must catch:

- **Falsification case for snapshot-diff:** A test that creates a temporary file tree, takes a snapshot, modifies a file outside the declared envelope, and verifies that `snapshot_diff.py --diff` exits 1 and names the changed file.
- **Falsification case for integration-gate:** A test that creates a deliberately malformed invariant-check block (or patches one to fail), runs the integration gate, and verifies exit code 1 with the failing invariant named in output.

If either falsification test does not pass at Phase 4, D3 is rejected per ADR-003's falsification requirement.

### Boundary

- Does NOT modify `validate_architecture.py`'s existing Check A/B/C/D/E logic — only calls it.
- Does NOT add hook enforcement (no new entries in `.claude/settings.json`) — D3 gates are invoked by the integration-sweep command and slice-close protocol, not by PreToolUse/PostToolUse hooks.
- DOES update `start-slice.md` and `start-slice.full.md` Step 7 completion sequence to wire D3 gates into slice-close. Does NOT change any other step or phase-gate logic.
- Type checking (`ty check`) is excluded from the mandatory gate — it's listed as optional in integration-sweep Step 4 and cairn has no typed Python to check.

### Verification

1. `python3 scripts/integration_gate.py` exits 0 on a clean cairn repo with all tests passing and ruff clean.
2. `python3 scripts/snapshot_diff.py --snapshot` creates `.claude/structural-snapshot.json` with entries for every in-scope file.
3. `python3 scripts/snapshot_diff.py --diff` exits 0 when no files have changed since the last snapshot.
4. `python3 scripts/snapshot_diff.py --diff` exits 1 and names the file when an out-of-envelope file is modified after snapshot.
5. Falsification test for snapshot-diff passes: planted out-of-envelope change is caught.
6. Falsification test for integration-gate passes: planted invariant violation is caught.
7. `uv run python -m pytest tests/unit/test_integration_gate.py tests/unit/test_snapshot_diff.py` — all tests pass.
8. `integration-sweep.md` and `integration-sweep.full.md` reference the new scripts for Steps 3–4.
9. `start-slice.full.md` Step 7 documents the D3 gate sequence (D1 first, then D3 integration gate + snapshot diff in parallel subagents).
10. `start-slice.md` Step 7 summary references D3 gates alongside D1.
