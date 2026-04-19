---
slice: compression/infrastructure
phase: 4-integration
date: 2026-04-19
sweep-number: 19
last-sweep-at: compression/doc-cleanup-tail
baseline-commit: 2d01546
---

## Summary

Slice-attributable outcome: **PASS with one finding** (ruff F841 in a test file, non-blocking to correctness). All slice-introduced tests (49/49 V1+V2+V3) GREEN; architecture validator exit 0; V4 adversarial hook check denies correctly; V9 settings.json parses; V10 legacy escape-hatch evidence present. V7 INV-003 row below.

Cross-slice integration gate: FAIL on ruff (finding #1) and pytest stops at a pre-existing failure (handoff-declared, out-of-scope). Snapshot diff: three out-of-envelope paths, all provenance traced to pre-Slice-A commit `5c4055d` (finding #2 — informational).

## V1–V11 evidence

| V | Status | Evidence |
|---|---|---|
| V1 role_guard tests | PASS | `uv run pytest tests/unit/test_role_guard.py` — 8+ tests pass incl. V1.1–V1.8 |
| V2 orchestrator state-machine | PASS | `uv run pytest tests/unit/test_slice_orchestrator_state_machine.py` — V2.1–V2.8 + A1–A8 pass |
| V3 slice-id regex | PASS | `uv run pytest tests/unit/test_slice_id_derivation.py` — valid/invalid parameterised pass |
| V4 adversarial hook (by hand) | PASS | `AGENT_ROLE=phase-3-implementer AGENT_ENVELOPE="^scripts/foo\.py$" python3 checks/role_guard.py <<< '{"tool_name":"Edit","tool_input":{"file_path":".claude/current-slice/intent.md"}}'` → exit 1, stderr: `role_guard: phase-3-implementer denied write outside envelope: .claude/current-slice/intent.md` |
| V5 full-suite regression-free | PASS (vs. baseline) | `uv run pytest --tb=no -q` — 501 passed, 8 failed, 1 skipped. The 8 failures match exactly the pre-existing set declared in handoff-phase-3.md:17 (test_adr_rename_sweep ×2, test_hook_relpath_bypass ×3, test_hook_tolerance ×3). Zero Slice-A-attributable regressions. |
| V6 architecture validator | PASS | `uv run python scripts/validate_architecture.py` — `ALL CHECKS PASSED Invariants verified: 7 ADR files checked: 12` (exit 0) |
| V7 INV-003 evidence | PASS | See table below |
| V8 platform probe | PASS | `.claude/platform-probe.md` committed; `claude -p --agent` invocation confirmed |
| V9 settings.json JSON-valid | PASS | `python3 -c "import json; json.load(open('commands/claude-code/settings.json'))"` → silent (valid) |
| V10 legacy escape-hatch | PASS | `commands/claude-code/start-slice.md` references `--legacy` + `CAIRN_LEGACY_START_SLICE`; `start-slice-legacy.md` exists (thin pointer delegating to `start-slice.full.md` per implementation/notes.md D1) |
| V11 F1/F3/F4 mechanisms | PASS | F1 → V1 tests 5–6 cover intent.md write-deny for skeptic+implementer; F3 → `.claude/agents/phase-4-integrator.md` body mandates sweep-notes authorship; F4 → `commit_phase_handoff` is unconditional per test_v2_5 |

## V7 — INV-003 evidence table

| INV | Statement | Status | Evidence |
|---|---|---|---|
| INV-003 | Roles instructed not hook-enforced, narrow exception for role-keyed write-path via `checks/role_guard.py` | PASS | `checks/role_guard.py` is the only new role-keyed hook shipped by this slice. `grep` confirms it gates only `Write\|Edit\|MultiEdit\|NotebookEdit` (no `Read`, no `Bash`, no subagent-dispatch filter). `docs/ARCHITECTURE.md:31` already carries the narrow-exception wording. Remaining hooks (`scope-guard.sh`, `reversibility-guard.sh`, `reality-check.sh`) are untouched by this slice — orthogonal to the role-keyed write-path per INV-003's "scope mechanism-specific" clause. |

## Failure-mode enumeration (cross-slice)

Enumerated BEFORE running gates:

1. **Import conflicts** — `scripts/slice_orchestrator.py` is new module; no existing module of same name. `checks/role_guard.py` is new peer of `scope-guard.sh`/`reversibility-guard.sh`/`reality-check.sh`. No import collisions possible — pure stdlib, function-based.
2. **Schema drift** — `slice.yaml` schema unchanged (reader line-parses existing fields). Agent frontmatter (`.claude/agents/*.md`) is new file type, no existing schema to drift from.
3. **Tool contract breaks** — `role_guard.py` registered in `commands/claude-code/settings.json` template only; `.claude/settings.json` (consumer wiring) not edited. `AGENT_ROLE` unset during Slice A → hook is no-op on own phases. No risk of hook interfering with Slice A commits.
4. **Config conflicts** — New env vars (`CAIRN_PHASE_<N>_TIMEOUT_HARD`, `CAIRN_LEGACY_START_SLICE`, `AGENT_ROLE`, `AGENT_ENVELOPE`) documented in `docs/operational-reference.md`. No collision with existing `CAIRN_*` knobs.
5. **Boundary violations** — `.slice-system → .` symlink: slice edits all target canonical paths (verified: envelope entries are `scripts/…`, `checks/…`, `commands/claude-code/…`, `.claude/agents/…`, `tests/unit/…`, `docs/…`). No symlink recursion hazard introduced.
6. **Invariant interactions** — INV-003's narrow exception for `role_guard.py` is pre-declared in `docs/ARCHITECTURE.md:31`. INV-004 is borderline (see Finding #3); all other invariants verified PASS by validator.

## Findings

### Finding #1 — ruff F841 in slice-authored test (slice-attributable, non-blocking)

`tests/unit/test_slice_orchestrator_state_machine.py:147` — `calls: list[dict] = []` is assigned but never used. Introduced by phase-2-skeptic during Phase 2. Blocks `integration_gate.py` step 4a (ruff). Does not affect test correctness; pytest passes. Trivial one-line fix (remove line 147 or wire `calls.append(…)` inside the stub). Per integration-sweep rule 9 ("Failures → new slices via normal pipeline. Do NOT retroactively edit completed slices.") and session anti-behavior ("Auditor does not rewrite the implementation"): **deferred to a focused follow-up slice.**

Recommended follow-up slice id: `compression/ruff-cleanup` (or fold into a broader test-hygiene slice).

### Finding #2 — snapshot_diff reports pre-Slice-A out-of-envelope paths (not-attributable)

`scripts/snapshot_diff.py --diff` lists:
- `docs/ARCHITECTURE.md` (changed)
- `docs/adr/compression-infrastructure-bootstrap.md` (new)
- `docs/adr/index.md` (changed)

Provenance: all three landed in commit `5c4055d` (`adr: compression-infrastructure-bootstrap (provisional)`), which predates Slice A's first commit `9c8617f`. Last integration sweep (#18) ran at `compression/doc-cleanup-tail`, prior to the bootstrap ADR. Snapshot baseline was stale when this slice started. **Not a Slice-A envelope breach.** Action: refresh baseline via `scripts/snapshot_diff.py --snapshot` at close of this sweep.

### Finding #3 — INV-004 turn-1 budget borderline (deferred per user instruction)

Per implementation/notes.md D4: `test_inv004_turn1_token_budget` measures 29,800–30,050 tokens depending on Anthropic edge-cache hit. 30,000 budget sometimes passes, sometimes ~25-token miss. Root cause: five new agent definitions + new slash command grow auto-loaded surface. **User directive (2026-04-19):** "budget boundary will be a new focused slice when required." Deferred to a dedicated slice. No Slice-A action.

## Staleness check — handoff Blocked/Pending vs git history

Handoff entries cross-referenced against `git log -20`:

- INV-004 budget borderline → **current** (deferred per user 2026-04-19)
- V4 adversarial role_guard by-hand → **resolved** this sweep (exit 1 confirmed)
- Pre-existing 8 failures → **current** (out-of-scope)
- `start-slice-legacy.md` thin-pointer composition → **current** (D1 design, V10 passes)
- No origin remote → **current** (local-only worktree)

No superseded items.

## Gate results

| Gate | Result |
|---|---|
| `python3 scripts/integration_gate.py` | FAIL (exit 1) — ruff F841 + pytest stops at pre-existing test_adr_rename_sweep |
| `python3 scripts/snapshot_diff.py --diff` | FAIL (exit 1) — 3 paths, all pre-Slice-A provenance (Finding #2) |
| `uv run python scripts/validate_architecture.py` | PASS (exit 0) |
| V1+V2+V3 slice-scoped pytest | PASS (49/49) |
| V5 full pytest regression check | PASS vs. baseline (501 passed, 8 failed = declared pre-existing set) |

## Decision

Slice-A integration sweep **closes with findings**. V1–V11 all PASS. Two non-blocking findings (one slice-attributable ruff lint → follow-up slice; one informational stale-snapshot resolved by baseline refresh). INV-004 budget boundary deferred per user. No Slice-A envelope breach; no regression; no invariant violation.

Slice may advance to `status: complete`. Follow-up slice `compression/ruff-cleanup` (or equivalent) recommended before next compressed dispatch.
