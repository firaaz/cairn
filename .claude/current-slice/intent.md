---
slice: compression/lever-2-orchestrator-split
date: 2026-04-25
phase: 1-intent
invariants-touched: [INV-003, INV-004, INV-008, INV-009]
adrs-referenced: []
envelope:
  - "scripts/slice_orchestrator.py"
  - "scripts/slice_orchestrator/__init__.py"
  - "scripts/slice_orchestrator/__main__.py"
  - "scripts/slice_orchestrator/core.py"
  - "scripts/slice_orchestrator/dispatch.py"
  - "scripts/slice_orchestrator/lifecycle.py"
  - "scripts/slice_orchestrator/resume.py"
  - "scripts/slice_orchestrator/telemetry.py"
  - "scripts/slice_orchestrator/git.py"
  - "tests/unit/test_slice_orchestrator_package_split.py"
  - "docs/ARCHITECTURE.md"
  - "docs/operational-reference.md"
  - "commands/claude-code/start-slice.md"
  - "commands/claude-code/start-slice-legacy.md"
  - ".claude/current-slice/intent.md"
  - ".claude/current-slice/validation/approach.md"
  - ".claude/current-slice/implementation/notes.md"
  - ".claude/current-slice/integration/sweep-notes.md"
  - ".claude/features/compression.yaml"
out-of-scope:
  - "tests/unit/**/*.py except the single new tests/unit/test_slice_orchestrator_package_split.py — every other test file MUST NOT be edited; any other-test diff signals a broken refactor"
  - "docs/adr/**/*.md — ADRs are append-only / firm; historical scripts/slice_orchestrator.py:NNN citations stay frozen by design"
  - ".claude/agents/**/*.md — agent prompts unchanged; INV-003 phase-lock contract preserved"
  - "checks/*.sh — hook surface unchanged"
  - "scripts/* (other) — only slice_orchestrator is being repackaged"
  - "Behavioral changes of any kind — model/effort defaults, retry caps, prompt prefixes, schema_version, dispatch arg surface, telemetry shape, INV-009 thresholds, pricing tables"
  - "H3 invariant-comment colocation in code (separate slice)"
  - "H4 test-name/module-mirror discipline (gradual, opportunistic)"
  - "M0 per-slice orientation (Lever 3 — follows this slice)"
  - "M0.5 source-file API digests (Lever 4)"
  - "M3+M2 read-cap / bash-cap prompt prefixes (Lever 5)"
  - "S1+S3 subagent dispatch discipline (Lever 6)"
  - "H1 doc-port layer (deferred until 2-3 adapters exist)"
  - "Compression Slice C/D/F work; L-008/L-009 follow-ons; sweep.yaml control keys"
---

### What and Why

`scripts/slice_orchestrator.py` is a 2240-line single file mixing pure logic, subprocess dispatch, git I/O, observability writes, lifecycle orchestration, resume reconciliation, and CLI entry. It is read 20× per orchestrator-touching slice at ~19k tokens per read (Part-8 audit §3). This slice splits it into a hexagonal package — `scripts/slice_orchestrator/{core,dispatch,lifecycle,resume,telemetry,git}.py` plus `__init__.py` and `__main__.py` — so each phase can read only the module it actually needs (~3-5k tokens) instead of the entire file. Pure structural change: **zero behavioral diff, zero test-file edits, 746/746 pytest pass at close.**

This is Lever 2 (H2) of the Part-8 compression intervention queue — the highest-leverage move that needs no doc-side architectural commitment, ships first per §13 sequencing, and unblocks the M0/M0.5/M3/S3/S1 levers queued behind it. Estimated savings: $3-5 per orchestrator-touching slice (180-300k cache_creation cut). The savings are measured on the *next* orchestrator-touching slice via Track-0's `<slug>-result.json` instrumentation, recorded in that slice's `sweep-notes.md` — this slice's own savings are by definition zero (this slice IS an orchestrator-touching slice that pays the full pre-split read cost).

### Specification Detail

**S1. Package layout.** A new directory `scripts/slice_orchestrator/` replaces the single file `scripts/slice_orchestrator.py`. The old file is **deleted** in the same Phase 3 commit that creates the package — Python import resolution does not allow both a file and a package directory of the same name to coexist in one parent. After the split the import system finds the package directory.

**S2. Module assignment.** Each top-level definition in the current `scripts/slice_orchestrator.py` lands in exactly one submodule. The assignment is driven by responsibility, not by accident of current line ordering:

- `core.py` — pure functions / module constants with no I/O dependency:
  `SLICE_ID_REGEX`, `ROLE_FOR_PHASE`, `ROLE_TO_PHASE`, `DEFAULT_TIMEOUT_HARD`, `PERMISSION_MODE`, `VALID_TRIAGER_ACTIONS`, `AGENT_MODEL_CONFIG`, `_resolve_model_config`, `INV_009_COST_THRESHOLD_USD`, `INV_009_TOKEN_THRESHOLD`, `PRICING_TABLE_*` constants, `_active_pricing_table_name`, `_active_pricing_table`, `is_valid_slice_id`, `_normalize_slice_id`, `_slice_id_slug`, `_utc_timestamp`, `_iso_now`, `_parse_structured_tail`, `_parse_usage_envelope`, `_extract_agent_result_text`, `_extract_envelope_model`, `_cost_for_tokens`, `_resolve_timeout`, `detect_superseded_test_signal`, `_classify_failure`, `_parse_clusters`, `_intent_envelope`.

- `git.py` — git wrappers and HEAD-introspection helpers:
  `_git`, `_git_head_safe`.

- `telemetry.py` — observability artifacts (`.claude/orchestrator-debug/`, `index.jsonl`, result.md, heartbeat):
  `DEBUG_DIR`, `_observability_paths`, `_atomic_write`, `_persist_state`, `_generate_result_md`, `_write_result_md`, `_append_index_entry`, `_HeartbeatDaemon`, `_start_heartbeat`, `_check_heartbeat_alive`, `_handle_heartbeat_death`, `_write_phase_log`, `_write_cluster_log`, `_record_phase_cost`, `_init_state_dict`, `_default_observability_errors`, `_update_state`.

- `resume.py` — slice-state read/write + the 13-state-triple resume-reconciliation matrix:
  `_read_slice_state_strict`, `read_slice_state`, `_write_slice_state`, `_persist_current_phase`, `_persist_redispatch`, `_is_slice_complete_subject`, `_head_subject_safe` (re-imported from git), `_refuse_resume`, `_reconcile_resume_state`, `_current_phase`, `_slice_id`, `_slice_brief`.

- `dispatch.py` — subprocess-spawning + retry classification + Phase-3 cluster fan-out:
  `_run_with_live_stderr`, `_resolve_phase_and_slice`, `_dispatch_once`, `_log_retry_attempt`, `dispatch_phase_agent`, `_resolve_supersession_hint`, `dispatch_triager`, `_load_clusters`, `_phase3_dispatch_with_log`, `dispatch_phase_3`.

- `lifecycle.py` — phase-loop, slice initialization, slice-close, signal handling, atexit:
  `_dispatch_for_phase`, `commit_phase_handoff`, `run_phase_loop`, `_bundle_handoff_md`, `_wipe_current_slice`, `_is_slice_already_closed`, `_clean_shutdown`, `_register_signal_handlers`, `_register_atexit_terminal_writer`, `_final_persist_and_md`, `_abort_slice`, `init_new_slice`, `close_slice`, `legacy_start_slice`.

- `__main__.py` — CLI entry point:
  `main`, plus `if __name__ == "__main__": sys.exit(main())`.

- `__init__.py` — re-exports the full backward-compat public surface (S3).

Implementation notes (Phase 3 may relocate individual helpers between modules if a stronger responsibility match emerges; the constraint is that **no public name listed in S3 changes module of declaration in a way that breaks `slice_orchestrator.<name>` resolution**, and no submodule introduces a circular import).

**S3. Backward-compat re-export contract.** `scripts/slice_orchestrator/__init__.py` MUST make every one of these names resolvable as `slice_orchestrator.<name>` (i.e. the `import slice_orchestrator as so; so.<name>` form used across `tests/unit/test_*.py`):

Top-level public defs/classes:
`is_valid_slice_id`, `read_slice_state`, `dispatch_phase_agent`, `dispatch_triager`, `dispatch_phase_3`, `detect_superseded_test_signal`, `commit_phase_handoff`, `run_phase_loop`, `init_new_slice`, `close_slice`, `legacy_start_slice`, `main`, `_HeartbeatDaemon`.

Module constants (load-bearing per cost-per-slice-budget ADR D7 + identifier-scheme):
`AGENT_MODEL_CONFIG`, `INV_009_COST_THRESHOLD_USD`, `INV_009_TOKEN_THRESHOLD`, `PRICING_TABLE_<date>` (every dated constant currently present), `ROLE_FOR_PHASE`, `ROLE_TO_PHASE`, `DEBUG_DIR`, `DEFAULT_TIMEOUT_HARD`, `PERMISSION_MODE`, `VALID_TRIAGER_ACTIONS`, `SLICE_ID_REGEX`.

Underscore-prefixed helpers reached into by tests (audit by grep against `tests/unit/`):
`_resolve_model_config`, `_classify_failure`, `_parse_structured_tail`, `_parse_usage_envelope`, `_extract_agent_result_text`, `_extract_envelope_model`, `_cost_for_tokens`, `_record_phase_cost`, `_active_pricing_table`, `_active_pricing_table_name`, `_resolve_timeout`, `_normalize_slice_id`, `_slice_id_slug`, `_utc_timestamp`, `_iso_now`, `_init_state_dict`, `_default_observability_errors`, `_update_state`, `_observability_paths`, `_atomic_write`, `_persist_state`, `_generate_result_md`, `_write_result_md`, `_append_index_entry`, `_start_heartbeat`, `_check_heartbeat_alive`, `_handle_heartbeat_death`, `_bundle_handoff_md`, `_wipe_current_slice`, `_is_slice_already_closed`, `_reconcile_resume_state`, `_is_slice_complete_subject`, `_head_subject_safe`, `_refuse_resume`, `_final_persist_and_md`, `_register_atexit_terminal_writer`, `_write_phase_log`, `_git`, `_git_head_safe`, `_run_with_live_stderr`, `_resolve_phase_and_slice`, `_dispatch_once`, `_log_retry_attempt`, `_resolve_supersession_hint`, `_load_clusters`, `_parse_clusters`, `_intent_envelope`, `_phase3_dispatch_with_log`, `_write_cluster_log`, `_dispatch_for_phase`, `_current_phase`, `_persist_current_phase`, `_persist_redispatch`, `_clean_shutdown`, `_register_signal_handlers`, `_slice_id`, `_slice_brief`, `_abort_slice`, `_read_slice_state_strict`, `_write_slice_state`.

Phase 3 MUST verify the public-surface list is exhaustive by `grep "^def \|^class \|^[A-Z_][A-Z0-9_]* =" scripts/slice_orchestrator.py` against the now-deleted file's git history (HEAD~1) and confirm every name has either (a) been re-exported in `__init__.py` or (b) been deliberately retired with rationale recorded in `implementation/notes.md`.

**S4. CLI entry-point contract.** The `--brief`, `--resume`, `--legacy` arg surface of `main(argv)` is preserved with byte-identical behavior. The CLI is invocable in at least one of the forms below; whichever forms work pre-split MUST continue to work post-split:

- `python -m slice_orchestrator --brief "..."` (with `scripts` on `PYTHONPATH`)
- `python scripts/slice_orchestrator/__main__.py --brief "..."` (direct path to `__main__.py`)

The pre-split form `python scripts/slice_orchestrator.py --brief "..."` ceases to function (the file no longer exists); the slash-command body in `commands/claude-code/start-slice.md` MUST be updated to point at one of the working forms above.

**S5. Doc + command path-string updates.** Every literal occurrence of the string `scripts/slice_orchestrator.py` in the in-envelope files MUST be reviewed for accuracy after the split:

- `commands/claude-code/start-slice.md` — header + invocation form.
- `commands/claude-code/start-slice-legacy.md` — bypass description.
- `docs/operational-reference.md` — env-var table "Source" column entries (the CAIRN_PHASE_*_TIMEOUT_HARD, CAIRN_HEARTBEAT_*, CAIRN_MODEL_*, CAIRN_EFFORT_* knob list); pricing-table convention paragraph.
- `docs/ARCHITECTURE.md` — `invariant-check` blocks whose `target:` field names `scripts/slice_orchestrator.py` MUST be re-pointed at the new submodule path so `validate_architecture.py` resolves them. (The ADR file edits — `docs/adr/slice-close-contract.md` line-number citations etc. — are explicitly out of envelope; ADRs are append-only and historical.)

Where a path string conceptually still refers to "the orchestrator as a module," the directory form `scripts/slice_orchestrator/` (no `.py` suffix) is the correct replacement. Where a citation is line-specific to a definition, the new submodule path is the correct replacement.

**S6. Test-file invariance.** Zero **existing** `tests/**/*` files MAY be edited in this slice. The single exception is the new RED-gate test file `tests/unit/test_slice_orchestrator_package_split.py`, written by Phase 2 to mechanically verify gates V2–V6 (public-surface re-export, CLI invocation, filesystem shape, architecture validator, path-string sweep). Every existing test currently passing pre-split MUST continue to pass post-split with no source change. A diff in any test file other than the new gate file (whether in Phase 3's commit or Phase 4's audit) is a hard FAIL signal that the refactor leaked a behavioral change.

**S7. Invariant preservation contract.** Each invariant in `invariants-touched` is preserved by construction:
- **INV-003** (phase-lock-and-role-declaration) — dispatch logic moves to `dispatch.py`; role/phase tables (`ROLE_FOR_PHASE`, `ROLE_TO_PHASE`) move to `core.py`; the agent-side phase-lock contract is untouched, agent prompts unchanged.
- **INV-004** (orchestrator-observability) — telemetry writes (`<slug>-result.json`, `index.jsonl`, `.heartbeat`, debug logs) move to `telemetry.py`; output paths, schema, and atomic-write semantics preserved byte-identically.
- **INV-008** (slice-close-contract) — `close_slice` moves to `lifecycle.py` as the sole producer of `slice: complete` commits; the four-signal precondition idempotency, the orchestrator-code skip at the Phase-4 boundary in `run_phase_loop`, and the slug-collision tripwire all preserved.
- **INV-009** (cost-per-slice-budget) — `_record_phase_cost` and `_init_state_dict` move to `telemetry.py`; `INV_009_COST_THRESHOLD_USD` / `INV_009_TOKEN_THRESHOLD` / `PRICING_TABLE_*` module-level constants stay reachable as `slice_orchestrator.<name>` via `__init__.py` re-export so the `tests/unit/test_slice_orchestrator_cost.py` test-file assertion path is unchanged.

### Boundary

In scope ⟶ each path enumerated in `envelope:` above; the deletion of `scripts/slice_orchestrator.py`; the `validate_architecture.py`-resolvable `invariant-check` `target:` updates in `docs/ARCHITECTURE.md`.

Out of scope ⟶ everything in `out-of-scope:` above. Particularly:
- **No test-file edit, no test-file add, no test-file move.** The 746-test suite is the load-bearing harness for this refactor; touching it forfeits the external check.
- **No ADR edit.** ADRs cite historical line numbers in `scripts/slice_orchestrator.py:NNN`. Those citations stay frozen — they are snapshots of what was true at the time of the ADR. The append-only invariant + ADR firmness rule binds.
- **No agent-prompt edit.** Agent prompts (`.claude/agents/*.md`) declare reads/writes; the `Reads:` patterns may name `scripts/slice_orchestrator.py` but the resolution is filesystem read-time, and the new package replaces the file as the agent's effective read target. If an agent prompt explicitly names the path string, that's a Lever-3+ concern (orientation) — out of scope.
- **No behavioral change.** No retry-cap tuning, no new env-var, no new prompt prefix, no new schema field, no model/effort default change.
- **No package name change.** The package is `scripts/slice_orchestrator/` exactly — not `scripts/orchestrator/`, not `scripts/cairn_orchestrator/`. The import name `slice_orchestrator` is the load-bearing public symbol.

### Verification

**V1. Test suite green, zero diff except the gate file.** `uv run python -m pytest` returns ≥746 passed (3 skipped allowed; the new `test_slice_orchestrator_package_split.py` adds N gate tests, all GREEN at Phase 4). `git diff HEAD~1 -- tests/` for the Phase 3 commit MUST be empty (Phase 3 does not touch any test file). `git diff <phase-1-intent-commit> -- tests/` at Phase 4 MUST show changes only in `tests/unit/test_slice_orchestrator_package_split.py` — every other test file is byte-identical.

**V2. Public-surface re-export proof.** `python -c "import slice_orchestrator as so; print(so.is_valid_slice_id('a/b'), so.AGENT_MODEL_CONFIG, so.INV_009_COST_THRESHOLD_USD, so.dispatch_phase_agent, so.run_phase_loop, so.close_slice)"` succeeds and prints non-error values for every name. Every name in §S3 MUST be importable.

**V3. CLI invocation.** Both `python -m slice_orchestrator --legacy` and `python scripts/slice_orchestrator/__main__.py --legacy` exit 0 and emit the legacy-protocol stub message. `python -m slice_orchestrator --brief "x/y test"` initializes a transient slice (immediately rolled back via `git restore`/`git clean`); arg-parse semantics are unchanged.

**V4. File-system shape.** `scripts/slice_orchestrator.py` does NOT exist (`ls scripts/slice_orchestrator.py` exits non-zero). `scripts/slice_orchestrator/` exists as a directory with the eight files: `__init__.py`, `__main__.py`, `core.py`, `dispatch.py`, `lifecycle.py`, `resume.py`, `telemetry.py`, `git.py`.

**V5. Architecture validator.** `uv run python .slice-system/scripts/validate_architecture.py` exits 0. Every `invariant-check` block in `docs/ARCHITECTURE.md` whose `target:` previously named `scripts/slice_orchestrator.py` now resolves to a real path (an existing submodule under `scripts/slice_orchestrator/`).

**V6. Path-string sweep.** `grep -rn "scripts/slice_orchestrator\.py" -- commands/ docs/ARCHITECTURE.md docs/operational-reference.md` returns NO hits in the in-envelope files. (Hits inside `docs/adr/**/*.md` are expected and acceptable — those are out-of-envelope historical citations.)

**V7. Invariant evidence.** Phase 4's `sweep-notes.md` contains an invariant-evidence table for INV-003 / INV-004 / INV-008 / INV-009, each row carrying a specific `scripts/slice_orchestrator/<submodule>.py:LINE` citation that proves the invariant binding survived the move. INV-009's row specifically asserts `slice_orchestrator.INV_009_COST_THRESHOLD_USD` and `slice_orchestrator.INV_009_TOKEN_THRESHOLD` are reachable through the package facade.

**V8. No-behavioral-diff smoke (advisory, evidence-only).** Phase 4 records in `sweep-notes.md` that `git diff HEAD~N -- scripts/` shows no logic changes other than physical relocation between modules: every `def` body that existed in `scripts/slice_orchestrator.py` at HEAD~N exists with byte-identical body at some `scripts/slice_orchestrator/<submodule>.py:LINE`. (Whitespace, import-line reshuffling, and the `__init__.py` re-export shim are exempt.) The integration-gate test pass + zero test-file diff is the firm signal; this advisory line is recorded for future audit.

### Open Questions for the operator (record-only; non-blocking)

OQ1. **Package name.** Is `scripts/slice_orchestrator/` the right import name, or do you want a shorter `scripts/orchestrator/` (renaming the public symbol from `slice_orchestrator` to `orchestrator`)? Renaming would be a *behavioral diff* — it changes every test's `import slice_orchestrator as so` line — so this slice keeps `slice_orchestrator`. Pre-emptive answer: keep the name; no rename.

OQ2. **CLI invocation form in `start-slice.md`.** Two valid forms exist (`python -m slice_orchestrator` vs direct path to `__main__.py`). Phase 3 will pick the form most consistent with how Claude Code currently invokes the orchestrator (operator: confirm at Phase-1 review or let Phase 3 pick).

OQ3. **`__init__.py` re-export style.** Star-import `from .core import *` requires `__all__` discipline in each submodule; explicit name-by-name re-export is verbose but auditable. Phase 3's choice; recorded in `implementation/notes.md`.
