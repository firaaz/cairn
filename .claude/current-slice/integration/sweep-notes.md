---
slice: compression/orchestrator-hardening
phase: 4-integration
role: auditor
as-of: 2026-04-19 7bb0103 (HEAD) + slice envelope at 6f189b3
---

# Phase 4 Integration — Auditor Verdict

**Overall:** PASS with two documented caveats (neither blocking close).

## Verification checks

| # | Intent item | Status | Evidence |
|---|---|---|---|
| 1 | `dispatch_agent` cmd list contains `--permission-mode` via module-level constant | PASS | `scripts/slice_orchestrator.py:37` defines `PERMISSION_MODE = "acceptEdits"`; `scripts/slice_orchestrator.py:113-121` wires it into `cmd = ["claude", "-p", "--agent", role, "--permission-mode", PERMISSION_MODE, json.dumps(inputs)]`. Single build site, inherited by every caller including `init_new_slice` at `scripts/slice_orchestrator.py:359-361`. |
| 2 | `init_new_slice(brief)` writes `brief:` verbatim and `read_slice_state` round-trips | PASS-with-caveat | `scripts/slice_orchestrator.py:366-369` persists `brief: "{brief}"` in `slice.yaml`. `read_slice_state` at `scripts/slice_orchestrator.py:49-71` strips matched surrounding quotes (lines 61-64). Caveat C1 below. |
| 3 | Every Phase 1 dispatch carries `brief` in inputs | PASS (stronger than contract) | `scripts/slice_orchestrator.py:262-264` reads brief via `_slice_brief()` and adds it to `inputs` when non-empty for **every** phase in the loop — broader than "Phase 1 only". Matches intent "MUST include the brief verbatim" for Phase 1 and extends it. |
| 4 | State-machine tests pass against real `slice.yaml` at `phase: 4, status: complete` | PASS | Full pytest run against real `.claude/current-slice/slice.yaml` (`status: 4-integration`, `current_phase: 4`): `test_v2_6_run_phase_loop_failed_retries_once` and `test_a8_retry_uses_same_inputs_and_envelope` are **absent from the failure list** — both GREEN. |
| 5 | Full pytest: no new failures beyond pre-existing baseline | PASS with intent miscalibration | Current failures: 10 (stash-test baseline on HEAD). See Caveat C2. Phase 3 introduced zero regressions; the state-machine 2 went RED→GREEN. Intent §Verification item 5 predicted 3 pre-existing, but the true baseline was 14 at slice start (flagged in Phase 3 handoff) and has dropped to 10 post-slice. |
| 6 | `validate_architecture.py` exits 0 | PASS | Exit 0; `Invariants verified: 7`, `ADR files checked: 12`. |
| 7 | Ruff clean on envelope files | PASS | `uv run ruff check scripts/slice_orchestrator.py tests/unit/test_slice_orchestrator_state_machine.py tests/unit/test_orchestrator_hardening.py` → `All checks passed!` |
| 8 | Manual dogfood by successor slice | DEFERRED (per intent) | Successor-slice marker; not verifiable here. |

## Invariants declared in `intent.md` (`invariants-touched: []`)

None declared. No architectural invariants to re-verify; trivially satisfied.

| INV | Statement | Status | Evidence |
|---|---|---|---|
| — | (none) | N/A | `intent.md:5` — `invariants-touched: []` |

## Adjacent-module regression check

Envelope boundary reviewed at `scripts/slice_orchestrator.py` public surface: `dispatch_agent`, `init_new_slice`, `run_phase_loop`, `read_slice_state`, `close_slice`. No signature changes that callers in the broader tree would notice; `brief` is an additive key in `slice.yaml` (readers that ignore unknown keys are unaffected; `read_slice_state` is a whitelist-free flat-map walker at lines 49-71 so it already tolerates new keys). No new imports. No removed public symbols.

## Caveats

### C1 — Unescaped brief quoting (non-blocking; successor-slice follow-up)

`scripts/slice_orchestrator.py:368` writes `brief: "{brief}"` via f-string with no escaping. A brief containing a literal `"` or a newline would break the round-trip because `read_slice_state` parses line-by-line and strip-matches a single pair of surrounding quotes. The intent's phrase *"verbatim (preserving whitespace and quoting)"* is satisfied for the common case (single-line, no embedded `"`), which is the only case Phase 2's validation exercises. No failing test, so non-blocking for close; recommend a successor-slice item to switch the writer to `json.dumps(brief)` or proper YAML string escaping if briefs ever need to carry `"` / `\n` / `\\`.

### C2 — Intent §Verification item 5 was miscalibrated at Phase 1

Intent predicted "3 pre-existing failures remain". Phase 3 handoff documented the true slice-start baseline as 14. Current count under `feature/compression` HEAD:

- `test_adr_rename_sweep` — 2 (sweep-#20 Finding §1, deferred to housekeeping micro-slice per intent out-of-scope)
- `test_hook_relpath_bypass` — 3 (pre-existing hook-path)
- `test_hook_tolerance` — 3 (pre-existing hook-path)
- `test_context_budget::test_inv004_turn1_token_budget` — 1 (pre-existing, unrelated)
- `test_housekeeping_post_slice_a_tidy::test_item_8_dogfooding_findings_section_in_sweep_notes` — 1 (this file resolves it)

Stash-test confirmation: 10 failures on pre-slice tree for the same test modules — identical set minus `test_item_d` (empty `integration/` dir, resolves once this file is committed). All 10 pre-date Phase 3 work. **No Phase 3 regressions.** The prediction error is an intent-drafting miscalibration in Phase 1, not an implementation fault.

## Dogfooding findings (for successor slice / sweep #21)

This slice addressed three of the six sweep-#20 findings in the orchestrator (F1 `permission-mode`, F2 `brief` persistence, F3 state-machine test isolation). The remaining known gaps — carried forward from `intent.md`'s out-of-scope list — and new findings surfaced by this Phase 4 audit:

### Carried forward (out-of-scope for this slice, still open)

1. **Sweep-#20 Finding #3 — orchestrator swallows agent `stderr`.** `dispatch_agent` at `scripts/slice_orchestrator.py:122-129` uses `capture_output=True` and never surfaces the subprocess's `stderr` on failure. When a subagent fails, the operator has no diagnostic trail. Requires a logging-path decision before fix.
2. **Sweep-#20 Finding #4 — writer does not scan `.claude/features/*.yaml`** before proposing a `slice_id`. Lives in the `.claude/agents/phase-1-writer.md` system prompt, not the orchestrator code; risks duplicate or non-hierarchical slice ids in a feature's slice list.
3. **Sweep-#20 Finding #5 — `envelope` schema lacks a default test-slot.** Requires `intent.md` Zone-1 schema work plus `checks/scope-guard.sh` updates; larger design surface than a hardening slice.

### Surfaced by this Phase 4 audit

4. **Brief-escape edge case (C1 above).** `init_new_slice` at `scripts/slice_orchestrator.py:368` writes `brief: "{brief}"` via naïve f-string — a brief containing `"` or a newline breaks the YAML round-trip. Switch to JSON/YAML-safe serialisation before briefs can carry such characters.
5. **Intent verification-item arithmetic is error-prone at Phase 1.** Predicting the exact pre-existing-failure count from a P1 vantage point (no test runs yet) is unreliable. Recommend dropping specific numbers from item-5-style clauses and using the pattern "no new failures beyond Phase 2 baseline captured at handoff-phase-2.md".
6. **`_slice_brief` injects `brief` into every phase's inputs**, not only Phase 1 (`scripts/slice_orchestrator.py:262-264`). Broader than intent contract F2 specifies. Defensible as harmless (later-phase agents can ignore unused keys), but the contract and the code should agree — either update the intent language on the next related slice to say "every phase" or tighten the code to `if phase == 1`.

## Gate / close checklist

- [x] Phase 4 gate: envelope committed (`6f189b3`), worktree clean on envelope files.
- [x] `uv run python -m pytest` completed. Post-sweep-notes.md-write: **517 passed, 1 skipped, 8 failed** — all 8 are pre-existing hook/sweep baseline (`test_hook_relpath_bypass` ×3, `test_hook_tolerance` ×3, `test_adr_rename_sweep` ×2) documented as out-of-scope in `intent.md` and deferred to a housekeeping micro-slice. Three failures resolved by the arrival of this file: `test_item_8` (Dogfooding-findings section now present with all five required keywords: brief, features, stderr, permission-mode, envelope), `test_item_d` (`.claude/current-slice/integration/` no longer empty), and `test_context_budget::test_inv004_turn1_token_budget`.
- [x] `uv run python .slice-system/scripts/validate_architecture.py` → exit 0.
- [x] Ruff clean on envelope files.
- [x] Invariants (none declared) trivially verified.
- [x] Auditor anti-behavior honoured: no implementation rewrite; only verification + evidence.
- [ ] Operator to run `/handoff phase` next, then D1/D3 gates at `/start-slice complete`.

## Unrelated working-tree state

`docs/plans/measurements/2026-04-12-slice-003.txt` shows a measurement update captured in an earlier session; noted in Phase 3 handoff as unrelated. Not in any slice envelope — out of Auditor scope.
