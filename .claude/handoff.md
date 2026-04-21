# Phase 4 Handoff — compression/slice-3-observability-and-close-slice

**Status:** OK (manual recovery — orchestrator escalated mid-Phase-3; manual Phase 4 + close).

## What landed (per the firm `slice-close-contract` ADR + provisional `orchestrator-observability` ADR)

INV-008 (slice-close lifecycle correctness) is now load-bearing in `scripts/slice_orchestrator.py`:

- **DC-3 idempotent close** — `_is_slice_already_closed:580` 4-signal precondition; `close_slice:1607` short-circuits.
- **DC-4 sole commit source** — orchestrator-code skip at `run_phase_loop:1463-1468` + Phase-4 prompt anti-behavior + drift detector at `close_slice:1631-1640`.
- **DC-5 wipe** — `_wipe_current_slice:548-577` (F5-tolerant on `FileNotFoundError`, strict otherwise).
- **DC-6 resume matrix** — `_reconcile_resume_state:650` (13 rows + default-refuse + heartbeat advisory).
- **DC-7 slug isolation** — `_persist_state` reads existing `<slug>-result.json`, refuses on `slice_id` mismatch.

Observability primitives implement the provisional ADR D1–D9: placement at `.claude/orchestrator-debug/`, JSON canonical + MD derived close-only, schema v1.0 with additive-safe `worktree_path`/`orchestrator_pid`, three-level error policy, append-preserving `degradation_reason`, heartbeat (`CAIRN_HEARTBEAT_INTERVAL=10.0`, `CAIRN_HEARTBEAT_STALE=30.0`).

P1 (Bash heredoc note) + P2 (no-preemptive-refuse rule) landed across all four phase agents; Phase-4 agent additionally carries the DC-4 anti-behavior.

## Test verdict

- **Slice-3 RED-to-GREEN:** 51 new tests across 8 files (7 unit + 1 integration), all GREEN.
- **v6 e2e regression:** 3 pre-existing tests (`test_v6_state_machine_runs_end_to_end`, `test_v6_four_phase_handoff_commits_present`, `test_item_a_state_machine_target_function_still_passes`) updated in `48926fd` to align with the now-firm DC-4/DC-5 semantics.
- **Architecture validator:** PASS (8 invariants, 14 ADR files).
- **Inherited tech debt:** 11 pre-existing reds (hook tolerance, relpath bypass, INV-004 budget, learning.md cap, INV-008-aware count assertions, handoff-tracked) catalogued in `integration/sweep-notes.md` § "Inherited tech debt"; **out of scope** for this slice; recommended follow-up: `housekeeping/post-inv008-tech-debt`.

## Recovery note (auditor-facing)

The orchestrator did NOT drive Phase 4 — it escalated mid-Phase-3 after the re-dispatch cap (`run_phase_loop` B15) fired on a triager misroute. Diagnosis + manual-recovery steps in `integration/sweep-notes.md` § Recovery.

Phase-3 cluster commits (`f8c0a5b`, `0044439`) and Phase-2 RED suite (`95c1beb`) all landed via the orchestrator before escalation; my manual interventions were limited to the 3 v6/housekeeping test edits (`48926fd`) and this Phase-4 close.

## Close-handoff queue (post-slice, not in scope)

- `/integration-sweep` — first since Slice 2 close (`sweep.yaml` pre-bumped per Slice-2 closeout).
- `/refresh-architecture` — INV-008 already in `docs/ARCHITECTURE.md` (landed at `ff6a08e` during /decision); validator PASS confirms. No re-refresh needed unless the post-close validator shows drift.
- Document `CAIRN_HEARTBEAT_INTERVAL` + `CAIRN_HEARTBEAT_STALE` in `docs/operational-reference.md` (~`:339-344` neighborhood per intent).
- `housekeeping/post-inv008-tech-debt` slice — address the 11 pre-existing reds.
- `triager-prompt-iteration` (informal): triager should consider "edit pre-existing test to match firm contract" as an alternative to RE_DISPATCH-to-Phase-2 when a RAISE_ISSUE names superseded tests.
- Path C (orchestrator-owned `.claude/**` writes) and multi-instance hardening (worktree-scoped locking, PID-scoped role_guard) — explicitly deferred per intent.md `## Boundary` § Out.
- Ruff F841 at `tests/unit/test_post_timeout_reconcile.py:101` — housekeeping leftover.

---
# Phase 4 Sweep — compression/slice-3-observability-and-close-slice

**Driven manually** (not by `phase-4-integrator` agent). Orchestrator escalated mid-Phase-3 (RAISE_ISSUE re-dispatch cap hit on a misclassified failure — see Recovery section below). Phase 3 cluster commits already on HEAD; manual Phase 4 + close.

## Gates run

| Gate | Result | Evidence |
|------|--------|----------|
| Slice-3 RED suite (51 tests) | PASS | `uv run pytest tests/unit/test_observability_writer.py tests/unit/test_state_schema.py tests/unit/test_heartbeat.py tests/unit/test_close_slice_hardened.py tests/unit/test_resume_reconcile.py tests/unit/test_cross_slice_isolation.py tests/integration/test_signal_observability.py tests/unit/test_agent_prompt_updates.py -v` → all GREEN |
| Architecture validator | PASS | `uv run python scripts/validate_architecture.py` — 8 invariants verified (incl. INV-008), 14 ADR files checked |
| End-to-end e2e | PASS | `tests/integration/test_compressed_slice_end_to_end.py::test_v6_state_machine_runs_end_to_end` + `…::test_v6_four_phase_handoff_commits_present` GREEN against new `close_slice` |
| Full unit + integration | PARTIAL — 649 passed, 11 pre-existing reds, 0 slice-3-induced | See "Inherited tech debt" |
| `scripts/integration_gate.py` | FAIL on first | Stops at `test_inv004_turn1_token_budget` (pre-existing context budget overrun); not slice-3-attributable |

## Slice-3 contributions verified

**INV-008 declared by `slice-close-contract` ADR; this slice implements it.**

- **DC-3 idempotent close** — `close_slice` short-circuits when 4-signal precondition holds. Tests: `test_close_slice_twice_is_noop`, `test_close_slice_short_circuits_on_already_closed_state`. GREEN.
- **DC-4 sole commit source** — `run_phase_loop:1463-1468` skips `commit_phase_handoff` at `phase == max_phase`; Phase-4 prompt (`agents/phase-4-integrator.md`) forbids self-commit; defensive `git log -1` drift detector in `close_slice:1631-1640`. Tests: `test_run_phase_loop_skips_commit_at_phase_4_boundary`, `test_close_slice_produces_single_slice_complete_commit`, `test_phase_4_prompt_explicitly_forbids_self_commit`. GREEN.
- **DC-5 wipe** — `_wipe_current_slice:548-577` deletes everything except `slice.yaml`; `FileNotFoundError` tolerated (F5), other `OSError` raises `RuntimeError`. Tests: `test_wipe_clears_all_except_slice_yaml`, `test_wipe_raises_on_undeletable_file`, `test_wipe_tolerates_file_already_absent`. GREEN.
- **DC-6 resume matrix** — `_reconcile_resume_state:650` implements the 13-row matrix + default-refuse + heartbeat advisory. Tests: `test_resume_reconcile.py` (13 row-parametrized + unmatched-triple). GREEN.
- **DC-7 slug isolation** — `_persist_state` reads existing `<slug>-result.json`, refuses on `slice_id` mismatch. Tests: `test_sequential_slices_keep_separate_result_files`, `test_slice_id_slug_used_in_all_debug_paths`, `test_slug_collision_exits_failed`. GREEN.

**Provisional `orchestrator-observability` ADR contracts verified.**

- D1 placement (`.claude/orchestrator-debug/`); D2 JSON canonical + MD derived (`_generate_result_md` pure); D3 thread decoupling; D4 schema v1.0 B2/B3 hybrid (additive-safe `worktree_path`, `orchestrator_pid`); D6 three-level error policy (retry → degrade → fail); D7 append-preserving `degradation_reason`; D9 heartbeat cadence env vars (`CAIRN_HEARTBEAT_INTERVAL=10.0`, `CAIRN_HEARTBEAT_STALE=30.0`).

**P1 + P2 prompt rules** landed across all four phase agents. Tests: `test_agent_prompt_updates.py` (6 tests, GREEN).

## Slice-3-induced regressions fixed in Phase 4

The new INV-008 contracts (DC-4, DC-5) explicitly superseded assertions in two pre-existing v6 e2e tests. Updated in commit `48926fd`:

- `test_v6_state_machine_runs_end_to_end` — was asserting `sweep-notes.md` persists post-Phase-4 (DC-5 wipes it). Now asserts bundled `handoff.md` contains sweep content + `sweep-notes.md` is wiped.
- `test_v6_four_phase_handoff_commits_present` — was asserting "phase 4" appears in git log (DC-4 forbids the boundary commit). Now asserts phases 1–3 each produce `handoff: phase N complete` + a single `slice: complete` commit + no `handoff: phase 4 complete`.
- `test_item_a_state_machine_target_function_still_passes` — subprocess wrapper of the first test; auto-fixed.

## Inherited tech debt (out of scope; queued for follow-up)

These 11 reds were already failing at `4579f31` (pre-slice-3 HEAD) — confirmed via baseline subagent run on a temp worktree. Slice 3 inherits but does not own them.

| Test | Pre-existing failure mode |
|------|----------|
| `test_context_budget::test_inv004_turn1_token_budget` | INV-004 token budget already over (30213 > 30000); slice-3 docs add ~+3k delta |
| `test_context_discipline_protocol::test_v5_learning_staging_ground_exists_and_is_minimal` | `.claude/learning.md` 4214 bytes vs 500-byte cap |
| `test_hook_relpath_bypass::TestV1`/`TestV2`/`TestV3` (3 tests) | `reversibility-guard` returns exit 0 on bare-relative + `.slice-system/`-prefixed flat-slug Edits (bypass open) |
| `test_hook_tolerance::TestV3FrontmatterEditBothForms` (3 tests) | body-prose Edit on flat-slug + legacy ADR not blocked |
| `test_housekeeping_post_slice_a_tidy::test_item_b_handoff_not_tracked` | `.claude/handoff.md` is git-tracked (must be untracked) |
| `test_invariant_assertions::test_no_extra_assertion_blocks` | unexpected `INV-008` assertion block in ARCHITECTURE.md (test predates INV-008) |
| `test_invariant_assertions::test_invariant_count_unchanged` | ARCHITECTURE.md has 8 invariants, test expects 7 (test predates INV-008) |

**Recommended follow-up slice scope:** `housekeeping/post-inv008-tech-debt` — update test_invariant_assertions for INV-008 count; investigate hook-tolerance/relpath-bypass scope-guard regressions; trim `.claude/learning.md` per L-cap; rotate `docs/plans/measurements/` measurements; address INV-004 budget overrun (likely needs a global cleanup or budget bump).

## Recovery context (operator audit trail)

The orchestrator escalated after Phase-3 implementer correctly RAISE_ISSUE'd on the 3 v6/housekeeping tests now superseded by INV-008. The triager re-dispatched to Phase-2 skeptic to update the tests, but Phase-2's charter is producing new RED tests, not editing pre-existing ones — it fixed an unrelated test-construction defect in `test_signal_observability.py::_driver` (commit `6c7ac82`) and re-emitted Phase-3, which RAISE_ISSUE'd again on the same three tests. Re-dispatch cap (`run_phase_loop` B15) hit → escalated correctly.

**Diagnosis:** the triager could not distinguish "Phase-2 produces new RED tests" from "pre-existing tests need updating per a now-firm contract." Either route would be valid. Phase-3-implementer's RAISE_ISSUE message was specific (named the three tests + the contracts they superseded), but the triager defaulted to RE_DISPATCH-to-Phase-2 without noting Phase-2's charter mismatch. Worth flagging in a future triager-prompt iteration.

**Manual recovery:** in this session, after the orchestrator exit, I:
1. Classified the 14 reds via baseline-test against `4579f31` — 3 slice-3-induced, 11 pre-existing.
2. Edited the 3 v6/housekeeping tests to align with INV-008 DC-4/DC-5; committed `48926fd`.
3. Ran architecture validator + the 51-test slice-3 suite — both PASS.
4. Wrote this sweep + handoff-phase-4.md.
5. Invoked `close_slice` directly via Python (bypassing `run_phase_loop` since the slice was mid-resume).

## Observability artifacts (DC-7)

Manual close initialized `_state` with `slice_id=compression/slice-3-observability-and-close-slice`, then called `close_slice`. Expected post-close artifacts in `.claude/orchestrator-debug/`:
- `compression-slice-3-observability-and-close-slice-result.json` — terminal state, `status=OK`
- `compression-slice-3-observability-and-close-slice-result.md` — derived sidecar
- `index.jsonl` — empty for this manual close (no `_append_index_entry` calls; orchestrator never wrote one mid-run either).

The 11+ failure logs from the orchestrator's Phase-2/Phase-3 churn (already in `.claude/orchestrator-debug/`) are preserved as evidence per DC-7's keep-on-fail contract.
