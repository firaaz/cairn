# Slice Compression Protocol — Design

**Date:** 2026-04-18
**Feature (proposed):** `compression`
**Status:** Design validated in brainstorm; forward plan pending (see companion doc `2026-04-18-slice-compression-protocol-plan.md`).
**Brainstorm source:** 2026-04-18 session (post-audit) resolving seeds 1-6 from `2026-04-18-session-compression-audit.md`.

## 1. Context

The afternoon-wins slice (`efficiency-program-afternoon-wins/all-seven`) shipped seven items in ~1 hour of wall time via a single-session subagent-dispatching orchestrator pattern — roughly a 4× speedup over faithful 4-session cairn execution (estimated 4-5 hours).

An independent audit (`docs/plans/2026-04-18-session-compression-audit.md`) found six correlated-error shapes, three HIGH severity. The compression was mechanically correct (77/77 tests green, invariants preserved) but contaminated across phase boundaries through the orchestrator's unified memory. Root cause: a single Claude session held Phase 1 / Phase 2 / Phase 3 / Phase 4 artifacts simultaneously, so phase-lock D2's "artifact isolation" invariant was violated in memory even while on-disk isolation held.

**Central question:** can single-session subagent compression be a sanctioned cairn mode?

**Brainstorm resolution (2026-04-18):** yes, with mechanical enforcement of clean-context discipline at every level. Compression is a dispatching tactic, not a mode flag. The contamination is preventable if (i) the orchestrator is code (never a Claude session), (ii) subagents are mechanically scoped by role, (iii) evidence persists on disk as committed artifacts, (iv) the same contract composes at every level of the orchestration tree including the future fleet coordinator.

## 2. Core principles

**P1 — Recursion-stable producer-consumer contract.**
Compression is a scaling primitive. The same contract shape applies at every orchestration level: phase subagent → slice orchestrator → fleet coordinator (future F6). Thickness of the contract decreases with nesting.

**P2 — Level-differentiated output contract.** *(Brainstorm Q2 → (d))*
- **Slice level:** subagent commits its declared-output artifacts to the slice branch; returns `{status, commit_hash, bounded_summary}`. Orchestrator reads both: message for fast path, committed artifacts for reconciliation. Un-committed subagent scratch is unreadable (dies with the subagent session).
- **Fleet level:** fleet coordinator receives `{slice_id, status, bounded_summary}` from each slice-orchestrator; does NOT descend into per-slice artifacts. Maximum isolation at scale.

**P3 — No mode flag.** *(Brainstorm Q3 → (e))*
Compression is a dispatching tactic, not a mode. No `mode: compressed` field in `slice.yaml`. Governed by:
- Universal phase-artifact-immutability discipline (D1/D2/D3, per audit's Part 0 ADR proposal — see §8).
- Existing `parallelism-v1` D3 (within-slice parallel dispatch is v1-legal).
- Orchestrator writes phase-commit handoffs on subagents' behalf, so `scripts/verify_handoff.sh` check (b) remains satisfied by construction (F4 audit finding resolved).

**P4 — Mechanical enforcement via two-layer gating.** *(Brainstorm Q4 → (β1))*
- **Outer gate:** Claude Code agent-definition `allowed-tools` frontmatter. phase-N agent cannot call tools outside its role authority.
- **Inner gate:** role-scoped write-path hook (`checks/role_guard.py`). Reads `AGENT_ROLE` env var set by orchestrator at dispatch; validates every Write/Edit path against that role's declared-output paths. Analog of `scope-guard.sh`, role-indexed instead of slice-indexed.

**P5 — Layered escalation.** *(Brainstorm Q5 → (α) transport + (β) within-slice persistence; (γ) slice-candidates deferred)*
- **Transport layer (universal):** every subagent return uses structured message `{status ∈ {OK, RAISE_ISSUE, FAILED}, commit_hash, bounded_summary}`.
- **Within-slice persistence layer:** when `status=RAISE_ISSUE`, subagent commits `.claude/current-slice/issues/<phase>-<n>.md` before returning. Bounded message points to the commit (D2 applied to issues).
- **Cross-slice feed-forward layer (`.claude/slice-candidates/`):** deferred. Re-entry criterion: ship after ≥5 compressed slices produce real issue patterns that obviously want cross-slice persistence.

**P6 — Orchestrator is code, not a Claude session.** *(Brainstorm Q6 → (C))*
`scripts/slice_orchestrator.py` is a Python state machine. At each phase boundary it invokes `claude -p --agent <role>` with bounded inputs, parses the structured return, writes the phase handoff on the agent's behalf, advances state. The orchestrator holds zero cross-phase Claude context. Narrow agent reasoning is available at specific decision points (RAISE_ISSUE triage) via tiny Claude invocations, never as a long-running session.

## 3. Architecture

A compressed slice runs as a state machine in code, not a Claude session. `scripts/slice_orchestrator.py` owns the four-phase lifecycle: init → Phase 1 → Phase 2 → Phase 3 → Phase 4 → close.

At each phase boundary, the script invokes a role-scoped Claude agent (`claude -p --agent <role>`) with bounded inputs: `{slice_id, phase, phase-specific-inputs, return-shape-contract}`. The agent performs its phase's work, commits its declared-output artifacts to the slice branch, and returns a structured message. The script parses the return, writes the phase handoff on the agent's behalf, and advances state.

**Three layers of enforcement:**

1. **Allowed-tools per agent** (Claude Code agent-definition frontmatter). phase-3-implementer can only Edit/Write; phase-1-writer can't Edit existing files; etc.
2. **Role-scoped write-path hook** (`checks/role_guard.py`). Keyed on `AGENT_ROLE` env var; validates every Write/Edit path against the dispatched role's declared-output paths. Denies out-of-role writes the same way `scope-guard.sh` denies out-of-slice writes today.
3. **Universal phase-artifact discipline** (D1/D2/D3 added to Part 0 ADR). Envelope append-only mid-slice; sweep-notes.md required at close; candidate-sets cite intent.md. Enforced by existing + new hooks.

**The orchestrator holds no cross-phase Claude context** because it's code. Each Claude invocation is narrow (role + phase-specific inputs + slice id + return-shape). The session dies on return. The only memory crossing phase boundaries is: committed artifacts on the slice branch, and the orchestrator script's own state variables.

**Recursion falls out for free.** A future fleet coordinator (F6 daemon) dispatches `scripts/slice_orchestrator.py` processes (not Claude sessions). Each slice orchestrator dispatches role agents. Same producer-consumer contract shape at every level; different allowed-tool surface per level.

## 4. Platform primitives required

Portability contract. Claude Code provides all of these; other platforms (Windsurf, Cursor, etc.) must be checked against this list before any port is attempted.

**Required:**

1. **Shell execution** — run `scripts/slice_orchestrator.py` from a user-triggered entry point. Universal.
2. **Tool-call interception hooks** — run a script before a tool call; block/allow based on exit code. Without hooks, enforcement falls back to prose-only — exactly what the audit showed fails.
3. **Scoped subagent dispatch** — spawn a new agent session with: named role, bounded inputs via CLI/env, structured return to the caller, session isolation from caller's context.
4. **Allowed-tools per agent** — mechanical "this agent can only call these tools" at the agent level.
5. **Agent-definition files** — markdown/JSON/YAML schema storing `{role, system-prompt, allowed-tools}`.

**Nice-to-have:**

6. **Parallel subagent dispatch** — spawn N concurrently for Phase 3 cluster parallelism. Fallback: serial dispatch. Slower but correct.
7. **Structured return format** — subagent returns as parsed data vs free text. Fallback: parse bounded text per system-prompt-imposed schema.

**Explicitly NOT assumed:**

- Persistent cross-session memory (cairn uses git).
- Shared filesystem across subagent sessions (cairn uses slice branch + commits).
- Inter-subagent communication (forbidden by Part 0 ADR P3).

**Portability implication:**

| Platform | #1 | #2 | #3 | #4 | #5 | Port feasibility |
|---|---|---|---|---|---|---|
| Claude Code | ✓ | ✓ | ✓ | ✓ | ✓ | Primary target |
| Windsurf 2.0 (Jan 2026 cutoff) | ✓ | ? | ? | ? | ~ | Plausible; verify #2 and #3 before committing |
| Future platforms | — | — | — | — | — | Gate-check this table before any port attempt |

## 5. Components

All new scripts are Python stdlib-only (Rust-port-friendly per end-of-v1 migration direction).

### New (cairn ships)

| Path | Purpose | Size |
|---|---|---|
| `scripts/slice_orchestrator.py` | State machine; dispatches role agents per phase via `subprocess`, parses structured returns, writes phase handoffs, advances state. Uses `concurrent.futures` for Phase 3 parallel dispatch. | ~200-250 lines |
| `.claude/agents/phase-1-writer.md` | Intent + envelope authoring. Allowed-tools: Read, Write(`intent.md` only). | system prompt + frontmatter |
| `.claude/agents/phase-2-skeptic.md` | Tests + approach.md + coupling-clusters.yaml. Allowed-tools: Read, Write(`validation/*`). | system prompt + frontmatter |
| `.claude/agents/phase-3-implementer.md` | Dispatched N times (one per coupling cluster). Allowed-tools: Read, Edit, Write(envelope paths). | system prompt + frontmatter |
| `.claude/agents/phase-4-integrator.md` | Integration + sweep-notes. Allowed-tools: Read, Bash(test runners), Write(`sweep-notes.md`, handoff). | system prompt + frontmatter |
| `.claude/agents/issue-triager.md` | Narrow reasoning on RAISE_ISSUE: escalate-to-user vs re-dispatch-previous-phase. Allowed-tools: Read only. | small system prompt |
| `checks/role_guard.py` | Role-scoped write-path hook; reads tool-input JSON from stdin, checks `AGENT_ROLE` env var, validates path against role's declared-outputs. First Python hook in `checks/`. | ~60-80 lines |

### Refactored

| Path | Change |
|---|---|
| `commands/claude-code/start-slice.md` | ~300 lines prose → ~30 lines: parse args, validate preconditions, invoke `python3 scripts/slice_orchestrator.py`. |

### Settings update

| Path | Change |
|---|---|
| `commands/claude-code/settings.json` | Register `checks/role_guard.py` as a PreToolUse hook for Write/Edit when `AGENT_ROLE` env var is set. Recommended: package as `settings-compression.json` to avoid consumer-project conflicts (see §9). |

### Artifact paths (slice branch; extended from current)

- **Existing:** `intent.md`, `validation/tests/`, `validation/approach.md`, `implementation/` (envelope commits), `integration/`, `handoff-phase-<N>.md`, top-level `handoff.md`.
- **Added:** `validation/coupling-clusters.yaml` (Part 0 ADR P4), `integration/sweep-notes.md` (audit D2 mandatory at close), `issues/<phase>-<n>.md` (RAISE_ISSUE β persistence).

### Unchanged

Existing bash hooks (`scope-guard.sh`, `reversibility-guard.sh`, `reality-check.sh`, `role-cheatsheet.sh`, `prepare-commit-msg.sh`) stay bash until their own migration slices. `scripts/verify_handoff.sh` stays bash; its `handoff-phase-<N>.md` check is satisfied because the orchestrator writes them on subagents' behalf.

### Rust-portability constraints (end of v1)

- stdlib only: `subprocess`, `json`, `os`, `sys`, `pathlib`, `argparse`, `concurrent.futures`. Maps to Rust `std::process`, `serde_json`, `std::env`, `std::path`, `clap`, `std::thread` (or `tokio`).
- No decorators, metaprogramming, or dynamic imports.
- Data: plain `dict`/`list`, typed via `typing.TypedDict` if helpful. Rust port becomes `struct` one-for-one.

**Totals:** 7 new files (1 Python script, 1 Python hook, 5 agent markdown), 1 refactored, 1 settings edit.

## 6. Data flow + phase lifecycle

### Init

- User runs `/start-slice` (no args) OR `/start-slice "<natural-language description>"`.
- Skill dispatcher (`commands/claude-code/start-slice.md`, ~30 lines) resolves inputs:
  1. If `slice.yaml` exists with `status ∈ {in-progress, aborted}` → propose resume to user (y/n).
  2. Else if args provided → `brief_text = args`.
  3. Else → read `.claude/handoff.md` "Next" section; if it names an obvious pending slice, propose it (y/n/edit). If declined or empty, prompt user.
- Invoke `python3 scripts/slice_orchestrator.py --brief "<text>"` OR `--resume`.

### Slice ID derivation (inside orchestrator)

- Orchestrator dispatches `phase-1-writer` with the brief text only — no pre-chosen ID.
- `phase-1-writer`'s system prompt: "Propose a slice ID in `namespace/topic-name` format based on the brief. Return it alongside intent.md. Format: `{status, commit_hash, summary, proposed_slice_id}`."
- Orchestrator receives proposal, creates `slice.yaml` with that ID, commits.
- User can override the proposal post-hoc by renaming in `slice.yaml` before Phase 2 dispatch — identifier scheme supports id-name separation.

### Per-phase loop (N = 1..4)

1. Set env `AGENT_ROLE=<phase-N-role>`.
2. Dispatch `claude -p --agent <role>` with bounded inputs `{slice_id, phase, phase-specific-state, return-shape-contract}`.
3. Agent performs its phase's work, commits declared outputs to slice branch, returns `{status, commit_hash, summary}`.
4. Script parses return:
   - **`OK`** → write `handoff-phase-N.md` from summary + commit ref, commit, advance to phase N+1.
   - **`RAISE_ISSUE`** → agent has already committed `issues/<phase>-<n>.md` (β); go to RAISE_ISSUE handler.
   - **`FAILED`** → retry phase ONCE with diagnostic added; second failure escalates to user.

### Phase 3 fan-out

After Phase 2 commits `coupling-clusters.yaml`, Phase 3 dispatches one `phase-3-implementer` per cluster via `concurrent.futures.ThreadPoolExecutor`. All must return `OK` before advancing. Any RAISE_ISSUE pauses the whole phase; any FAILED triggers single-cluster retry. Reconciliation: orchestrator verifies no path overlaps between cluster commits (clusters were partitioned by Phase 2; overlap = Phase 2 bug, raise to user).

### RAISE_ISSUE handler

Script dispatches `issue-triager` agent with `{issue_commit_hash, current_phase, slice_id}`. Triager returns `{action ∈ {ESCALATE_TO_USER, RE_DISPATCH, ABORT}, ...}`:

- **`ESCALATE_TO_USER`** → write partial-close handoff naming the issue; exit non-zero. User sees issue via `.claude/handoff.md`, decides next step.
- **`RE_DISPATCH`** → amend previous-phase inputs per triager's guidance, re-dispatch that phase. Max **1 re-dispatch per phase** (prevents infinite loops).
- **`ABORT`** → write abort-reason to handoff, set `slice.yaml status=aborted`, exit non-zero.

### Close

After Phase 4 OK: update `slice.yaml` to `status=complete`; construct final `.claude/handoff.md` from phase-handoffs + sweep-notes; final commit; return success.

### Idempotence + resume

Script state lives in `slice.yaml` (current_phase, last_commit_hash-per-phase). If the orchestrator crashes mid-slice, `/start-slice --resume` picks up from the last completed phase. Each agent's system prompt includes: "if your declared outputs already exist at the expected commit, return OK without re-working." Re-running a phase is a no-op on success.

### What crosses phase boundaries

- **Crosses:** committed artifacts on the slice branch (intent, tests, approach, coupling-clusters, envelope files, sweep-notes, phase handoffs) + orchestrator script's state variables.
- **Does NOT cross:** subagent in-session scratch (dies with session), orchestrator Claude context (there is none — orchestrator is Python).

## 7. Error handling + testing

### Error handling beyond phase-level

1. **Malformed agent return.** Strict-parse `{status, commit_hash, summary}`. On parse failure: treat as FAILED with diagnostic "malformed return from <role>"; single retry.
2. **Agent timeout.** Part 0 ADR P5: 10-min soft / 30-min hard (env-overridable — see §9). Soft: send a bounded "what's blocked?" probe via a second `claude -p` call to the same role with stall context. Hard: `subprocess` kill; treat as FAILED.
3. **Git state errors.** Check `git status --porcelain` pre-dispatch; refuse to dispatch if worktree dirty or branch diverged. Report, exit.
4. **Orchestrator crash / Ctrl-C.** State durable in `slice.yaml` + commit trail. `--resume` picks up from last completed phase.
5. **Disk / permission errors.** Python exceptions bubble up; log to stderr; non-zero exit; slice.yaml status unchanged so resume works.

### Testing strategy

**Unit** (in `tests/unit/`, existing pytest pattern):
- `test_slice_orchestrator_state_machine.py` — mock subprocess, verify phase transitions on OK/RAISE_ISSUE/FAILED, max-1-redispatch limit, resume correctness.
- `test_role_guard.py` — feed stdin JSON for each role + path combinations, verify allow/deny against declared-output tables.
- `test_slice_id_derivation.py` — phase-1-writer proposals match `namespace/topic-name` format.

**Dogfood integration:**
- **Slice A verification**: close Slice A using the OLD serial `/start-slice`. Then run Slice B (Part 0 ADR) using the new compressed orchestrator. If Slice B completes with all audit findings verifiably prevented (envelope not amended, sweep-notes committed, no orphan handoffs), infrastructure works.
- **Adversarial test**: deliberately script a phase-3-implementer attempt to Edit intent.md; confirm `role_guard.py` blocks.

### Verification mapping (each audit finding → prevention mechanism)

| Finding | Prevention |
|---|---|
| F1 (envelope amendment) | `role_guard.py` blocks Phase-3 Edit on `intent.md`. |
| F2 (candidate-set leak) | Part 0 ADR D3 enforcement (candidate sets cite intent.md) — out-of-scope for compression's Slice A; delivered in Part 0 ADR slice. |
| F3 (sweep-notes missing) | phase-4-integrator's declared outputs include `sweep-notes.md`; `role_guard.py` enforces; orchestrator won't mark phase OK without it. |
| F4 (verifier self-contradiction) | Orchestrator writes phase handoffs on agents' behalf — `verify_handoff.sh` passes by construction. |
| F5 (ephemeral-memory handoff) | Orchestrator is Python, no Claude memory; final handoff is constructed deterministically from committed artifacts only. |
| F6 (rolling-window buried) | Out-of-scope for compression; Part 2/3 work on `/status` surfacing (d3-rolling-window-surfacing follow-up slice). |

## 8. Relationship to in-flight plans

Compression intersects with multiple in-flight plans. Disposition:

| Plan item | Compression's effect |
|---|---|
| `parallelism-v1` ADR D0 / D1 / D2 / D4 | **Unchanged** |
| `parallelism-v1` D3 (within-slice parallel dispatch carve-out) | **Implemented concretely** via Phase 3 fan-out |
| Efficiency Program Part 3 S1 (define agent files + harness) | **Subsumed** into compression's Slice A |
| Efficiency Program Part 3 S2 (integrate into `/start-slice` + `/decision`) | **Subsumed** into compression's Slice A (for `/start-slice`); `/decision` integration deferred |
| Efficiency Program Part 3 S3 (F6 worker integration) | **Unchanged** — still post-F6 |
| Efficiency Program Part 2 E2 (`commit_handoff.sh`) | **Superseded in original form** — orchestrator writes phase handoffs; E2's goal (mechanical side-effects) achieved differently |
| Efficiency Program Part 2 E6 (coupling-cluster parallelism) | **Implemented within compression** — no separate slice; built into `slice_orchestrator.py` Phase 3 fan-out |
| Efficiency Program Part 2 E1 / E3 (auto-phase-detect, state.json) | **Unchanged** — orthogonal |
| Efficiency Program Part 0 ADR (P1-P6) | **Extended** — compression proposes D1/D2/D3 as new principles (per audit) |
| Efficiency Program Part 1 (distillation agents) | **Unchanged** — orthogonal |
| Fleet-coordinator F6 design | **Composes cleanly** — compression defines F6's worker-spawn primitive; no F6 design changes |
| `identifier-scheme` feature (this branch) | **Must close first.** 2 remaining slices (`slice-and-feature-rename`, `doc-sweep`) continue serially pre-compression |

### D1/D2/D3 proposed additions to Part 0 ADR

Part 0 ADR currently specifies P1-P6. Compression proposes adding:

- **D1 — Phase 1 envelope is append-only within a slice.** Appends require machine-readable marker + rationale commit; overwrite/reorder prohibited. (Audit F1 prevention.)
- **D2 — Phase 4 evidence is committed-artifact-first.** `sweep-notes.md` must exist at close; commit message is a pointer, not a source. (Audit F3 prevention.)
- **D3 — Phase 2 candidate-sets must cite the `intent.md` line that authorized the ambiguity.** No candidate set without a paper trail. (Audit F2 prevention.)

These land in the Part 0 ADR slice (Slice B of compression feature).

## 9. Consumer impact + migration

Downstream cairn consumers (via `.slice-system → .` symlink) see changes once the compression infrastructure lands on the branch they pull from (`dev` for bleeding-edge, `master` for stability).

### What consumers automatically receive

- 7 new files (1 Python script, 1 Python hook, 5 agent markdown).
- Refactored `/start-slice`.
- `role_guard.py` hook registration.

### Risk for consumers

- `role_guard.py` is a **no-op when `AGENT_ROLE` env var is not set** — zero friction for non-`/start-slice` workflows.
- `settings.json` is a shared file; consumer customizations could conflict with cairn's additions. **Mitigation:** ship the hook registration as a separate `settings-compression.json` that consumers merge via their own `install` step, OR push compression-specific config into a dedicated YAML that cairn reads and consumers inherit via symlink.
- `.claude/agents/` directory introduced — new primitive; consumer-own agents coexist. No conflict expected.
- **`/start-slice` behavior change** is the real one — any consumer with prose customizations of `/start-slice` gets their changes superseded. **Audit required:** does any downstream consumer currently override `/start-slice`?

### Known-consumer callout: `complex-rag-analysis`

Per cairn memory (`complex_rag_analysis_consumer.md`): ~917s pytest suite. Phase 4 integrator's default 10-min soft-timeout would fire mid-test.

**Fix:** make Phase 4 timeout env-overridable per the existing cairn-pattern (cairn-friendly default with env-var override):

```
CAIRN_PHASE_4_TIMEOUT_SOFT   # default: 600 (10 min)
CAIRN_PHASE_4_TIMEOUT_HARD   # default: 1800 (30 min)
CAIRN_PHASE_N_TIMEOUT_SOFT   # default per phase; env override allowed
```

### Merge-gate

1. `identifier-scheme` feature's 2 remaining slices close on `feature/identifier-scheme`; merge to `dev`.
2. Compression Slice A closes on a new `feature/compression` branch; Slice B (Part 0 ADR) runs compressed on the same branch and validates.
3. **Then** merge `feature/compression` to `dev`. Consumers pulling from `dev` see a validated end-to-end system.
4. After ≥3 clean compressed slices ship on `dev`, merge to `master`. Bleeding-edge consumers become stable consumers.

## 10. Transition plan + compounding ordering

### Slice A — compression infrastructure (serial execution, ~1 day)

Ships:
- `scripts/slice_orchestrator.py`
- `.claude/agents/{phase-1-writer, phase-2-skeptic, phase-3-implementer, phase-4-integrator, issue-triager}.md`
- `checks/role_guard.py`
- Thin `commands/claude-code/start-slice.md` refactor
- `settings.json` (or `settings-compression.json`) hook registration

Executes serially because it's building the tool it would use. Zero-ADR, additive. Gate: all audit findings that Slice A targets (F1, F3, F4, F5) verified by the dogfood test plan.

### Slice B — Part 0 ADR (compressed execution, ~1 hour)

Consumes Slice A. Ships Part 0 ADR with P1-P6 + D1/D2/D3. Verifier: does Slice B complete without audit findings recurring? If yes, compression infrastructure is proven.

### Slice C..N — compressed, parallel where independent

- Audit's three follow-ups (`envelope-immutability-guard`, `phase-4-sweepnotes-required`, `d3-rolling-window-surfacing`) — land within the compression feature as mechanical enforcement of D1/D2/D3.
- Part 1 distillation agents — serial on Part 0 ADR.
- F2 fix (candidate-set hygiene per audit seed 5) — compressed slice, part of Part 0 ADR slice or Part 1.

### Compounding timeline

| Week | Activity |
|---|---|
| Week 1 | Close `identifier-scheme` tail (2 slices, serial). Start `feature/compression`. Slice A (1 day serial) + Slice B (1 hr compressed). Tool proven. |
| Week 2 | 5-10 compressed slices (Part 0 finish, follow-ups, Part 1 start). |
| Weeks 3-4 | Parallel compressed slices across Parts 1/2/6. Multiple slices/day. |

Original "months-long" shape-change collapses to ~2 weeks after identifier-scheme merges.

### Hedges for compression risk

- Old `/start-slice` remains runnable via `--legacy` flag until 5 clean compressed slices land.
- Each of the first 5 compressed slices includes a `ROLLBACK_PLAN` section in `intent.md`: rollback to pre-slice commit + re-run serial if the orchestrator misbehaves.
- After 5 clean runs: drop `--legacy`, delete serial-session prose.

### Dependencies

- `identifier-scheme` feature close → compression Slice A start (hard).
- Slice A → all compressed slices (hard).
- Slice B (Part 0 ADR) → Parts 1-5 per existing efficiency program (soft; the program can proceed on some tracks without Part 0).
- F6 fleet coordinator (future) → consumes `slice_orchestrator.py` as its worker-spawn primitive; no blocker.

## 11. Out of scope for this design (deferred with re-entry criteria)

- **(γ) slice-candidate primitive** (`.claude/slice-candidates/`). Re-entry: ship after ≥5 compressed slices produce issues obviously wanting cross-slice persistence.
- **Full skill refactor** of `/catchup`, `/handoff`, `/integration-sweep` to thin dispatchers. Refactor incrementally when next touched. Part 2/3 scope.
- **Windsurf port.** Deferred per brainstorm Q-Windsurf-(ii); "Platform Primitives Required" (§4) is the portability contract for any future port.
- **Rust migration.** End of v1 per user direction; Python stdlib-only constraints (§5) keep the port mechanical.
- **Seed 6 middle-management-framing slice.** Too abstract for a methodology slice shape; absorbed as philosophical context in ADR commentary.
- **F6 worker integration** (Part 3 S3). Stays post-F6.
- **`/decision` integration of agents** (Part 3 S2 half). Deferred to its own slice; `/start-slice` is the first integration target.

## 12. Open questions

1. **Settings.json packaging.** Should the `role_guard.py` hook registration live in the main `settings.json` (consumer merge burden) or in a separate `settings-compression.json` (consumer install step)? Recommendation: separate file; decision pending consumer audit.
2. **`commit_handoff.sh` (E2) obsolescence.** E2 was planned as mechanical side-effect extraction from `/handoff` prose. Compression achieves this for the `/start-slice` side. Does `/handoff` retain a standalone need for `commit_handoff.sh`, or does compression subsume E2 entirely? Likely the latter, but confirm when `/handoff` next touches.
3. **Phase 3 implementer granularity** (open from Part 3). Is "refactor" vs "greenfield" vs "bugfix" a granularity that deserves separate phase-3 agents? Or is one `phase-3-implementer` enough? Pushed forward from Part 3's open question.
4. **Agent-bypass env var** (`CAIRN_AGENT_BYPASS=<name>`, Part 3). Should the compressed orchestrator honor this escape hatch for emergencies, or is the `--legacy` flag sufficient?
5. **`claude -p --agent` availability.** Does the Claude Code CLI currently accept `--agent <role>` for subagent dispatch with agent-definition frontmatter? If not, Slice A's interface design needs to adapt (e.g., pass system prompt inline via `--system-prompt` file or similar).

## 13. Pointers

- `docs/plans/2026-04-18-session-compression-audit.md` — brainstorm input; six-finding audit that motivated the protocol.
- `docs/adr/parallelism-v1.md` — D3 carve-out compression implements.
- `docs/plans/2026-04-18-efficiency-program/02-part-0-adr-principles.md` — Part 0 ADR scope; compression extends with D1/D2/D3.
- `docs/plans/2026-04-18-efficiency-program/05-part-3-phase-role-agents.md` — Part 3 plan compression subsumes S1+S2 of.
- `docs/plans/2026-04-15-fleet-coordinator-design.md` — F6 epic; compression defines F6's worker-spawn primitive.
- **Companion doc:** `docs/plans/2026-04-18-slice-compression-protocol-plan.md` — forward implementation plan, to be authored next via `writing-plans` skill.
