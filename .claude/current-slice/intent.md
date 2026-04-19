---
slice: compression/orchestrator-hardening
date: 2026-04-19
phase: 1-intent
invariants-touched: []
adrs-referenced: [compression-infrastructure-bootstrap]
envelope:
  - "scripts/slice_orchestrator.py"
  - "tests/unit/test_slice_orchestrator_state_machine.py"
  - "tests/unit/test_orchestrator_hardening.py"
out-of-scope:
  - "Dogfooding findings #3 (stderr swallow), #4 (writer feature-scan), #5 (envelope schema) — deferred to future slices; only #1, #2, #6 are in this slice"
  - "Phase-agent markdown under `.claude/agents/*.md` — writer/skeptic/builder/auditor prompts untouched"
  - "role_guard.py, scope-guard.sh, reversibility-guard.sh — hook behaviour unchanged"
  - "compression-infrastructure-bootstrap ADR — frontmatter or body edits; provisional status preserved"
  - "Stale-test Findings §1 (test_adr_rename_sweep hardcoded list) and §3 (housekeeping test_item_8) from sweep #20 — separate slice"
---

### What and Why

Second slice under the compressed dispatch protocol. First real dogfood (`housekeeping/post-slice-a-tidy`) surfaced six findings in the orchestrator's phase-dispatch path; two are BLOCKERs that prevent compressed dispatch from completing end-to-end, and one LOW finding corrupts the orchestrator's own test suite against real slice state. This slice fixes those three, unblocking compressed dispatch so subsequent slices can run through `/start-slice` without falling back to `--legacy`.

Pre-v1 D-alignment: this slice is **D1/D2/D3-enabling infrastructure hardening** per cliff-failure-mode-and-v1-defenses. The compressed orchestrator is the mechanism by which downstream D1 (automated refresh), D2 (invariant binding), and D3 (mechanical gating) slices will dogfood in the compressed protocol. A broken dispatcher blocks their validation paths. This is not a waiver.

### Specification Detail

**F1 — `--permission-mode` plumbing in `dispatch_agent`.**
`scripts/slice_orchestrator.py:105-133` currently builds the subagent command without `--permission-mode`. Under `-p` (non-interactive), the default permission mode auto-denies `Write`/`Edit` tool calls, defeating role_guard.py as the designed inner gate. Fix: the command constructed by `dispatch_agent` MUST include `--permission-mode acceptEdits` (or whichever CLI value aligns with role_guard.py being the effective write-path gate per compression-infrastructure-bootstrap). The value is a module-level constant so future audits can locate it without grep. All subagent dispatches — Phase 1–4 writers/skeptic/builder/auditor and the slice-id proposer in `init_new_slice` — inherit this.

**F2 — Brief persistence across dispatches.**
`init_new_slice` (`scripts/slice_orchestrator.py:335-348`) currently passes `{"brief": brief, "ask": "propose_slice_id"}` to the first dispatch only. `run_phase_loop` (`scripts/slice_orchestrator.py:237-`) dispatches Phase 1 with `{"phase": phase, "role": role, "slice_id": slice_id}` — no brief. Fix: persist the user's brief text at slice init-time into a well-known location the Phase 1 writer reads, and ensure every Phase 1 dispatch carries it. The writer's input payload for phase 1 MUST include the brief verbatim.

Persistence site choice is **a new key in `slice.yaml`: `brief: "<verbatim user brief>"`**. Rationale: `slice.yaml` is already the single source of truth for slice metadata (`read_slice_state`), its schema change is contained to the orchestrator, and it survives across the dispatches. No new file. The key is set on slice creation and never mutated afterward.

**F3 — Test isolation from real `.claude/current-slice/slice.yaml`.**
`tests/unit/test_slice_orchestrator_state_machine.py:180,198` (`test_v2_6_run_phase_loop_failed_retries_once` and `test_a8_retry_uses_same_inputs_and_envelope`) monkeypatch `dispatch_agent` but not `_current_phase`. With the real slice.yaml at `current_phase: 4 status: complete`, `run_phase_loop` skips phases 1–3 and the retry-once assertions for `phase-1-writer` see `count == 0`. Fix: tests monkeypatch `slice_orchestrator._current_phase` to return `1` at call-time. No change to orchestrator internals. This matches Finding #6 in `880337b`'s sweep-notes.md.

**F-wire — structured return for new code paths unchanged.**
`dispatch_agent`'s JSON-tail return contract (A1 from Phase 2 of compression/infrastructure) is preserved. No new exit statuses. A5 (unknown-status → non-zero) and A8 (retry-once same args) behaviour unchanged.

### Boundary

**Out of scope explicitly:**

- Dogfooding finding #3 (orchestrator swallows agent stderr; `dispatch_agent:105-133` `capture_output=True`). Separate slice — requires a logging-path decision.
- Finding #4 (writer does not scan `.claude/features/*.yaml` before proposing slice_id). Lives in `.claude/agents/phase-1-writer.md` system prompt, not the orchestrator.
- Finding #5 (envelope schema lacks default test-slot). Requires `intent.md` Zone-1 schema work and scope-guard.sh changes; larger design surface.
- Sweep #20 Findings §1 (stale `test_adr_rename_sweep`) and §3 (`test_item_8_dogfooding_findings_section_in_sweep_notes`). Test-hygiene bundle better shipped as a separate `housekeeping/` micro-slice.
- No ADR edits. `compression-infrastructure-bootstrap` remains provisional with its body and firmness untouched; Slice B Part 0 is the ADR-track work for ratification.
- No changes to phase-agent markdown files (`.claude/agents/*.md`). The brief is delivered via the input payload, not via system-prompt mutation.
- No changes to hook scripts (`checks/*.sh`, `checks/role_guard.py`).
- No changes to settings.json hook registration.

### Verification

1. `dispatch_agent` constructs a subprocess command list that contains `--permission-mode` with a value that makes role_guard.py the effective gate. Machine-checked by a unit test that inspects the `cmd` list built by `dispatch_agent` under a monkeypatched `subprocess.run` stub.
2. `init_new_slice(brief)` writes `brief:` into `.claude/current-slice/slice.yaml` verbatim (preserving whitespace and quoting); `read_slice_state` round-trips it. Machine-checked by unit test.
3. Every Phase 1 dispatch through `run_phase_loop` carries `brief` in the inputs payload. Machine-checked by unit test: stub `dispatch_agent`, drive `run_phase_loop(max_phase=1)` with a seed `slice.yaml` containing a `brief:` value, assert `inputs["brief"] == "<seed value>"` for the `phase-1-writer` call.
4. `test_v2_6_run_phase_loop_failed_retries_once` and `test_a8_retry_uses_same_inputs_and_envelope` both pass irrespective of the real `.claude/current-slice/slice.yaml` state. Machine-checked by: run the two named tests under `pytest` with the real repo slice.yaml at `phase: 4, status: complete` (the state this slice starts in) — both GREEN.
5. Full pytest suite run at Phase 4: no new failures beyond the 5 pre-existing classified in sweep #20 MINUS the 2 state-machine failures this slice fixes. Expected: 3 pre-existing failures remain (2 `test_adr_rename_sweep`, 1 `test_item_8_dogfooding_findings_section_in_sweep_notes`) + 0 net new.
6. Architecture validator: `uv run python scripts/validate_architecture.py` exits 0 (7 invariants, 12 ADRs unchanged).
7. Ruff clean: `uv run ruff check scripts/slice_orchestrator.py tests/unit/test_slice_orchestrator_state_machine.py tests/unit/test_orchestrator_hardening.py` exits 0.
8. Manual dogfood readiness: the next slice started via compressed `/start-slice <brief>` (NOT `--legacy`) is able to complete Phase 1 writer dispatch without a permission-denial or brief-loss error. Evidence recorded in the next slice's Phase 1 handoff or intent.md — not verified in THIS slice's integration. Listed here as a successor-slice marker only.
