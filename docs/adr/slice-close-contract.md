---
id: slice-close-contract
name: "Slice-close contract — idempotent close, sole commit source, cross-slice isolation"
status: superseded
superseded-by: slice-close-contract-superseded
firmness: firm
supersedes: []
supersedes-sections: []
topic: process
adrs-referenced: [context-discipline-protocol, phase-lock-and-role-declaration, identifier-scheme, compression-infrastructure-bootstrap, cliff-failure-mode-and-v1-defenses]
invariants-touched: [INV-002, INV-003, INV-008]
date: 2026-04-20
---

# slice-close-contract: Orchestrator slice-close lifecycle contract

## Status
Accepted

## Date
2026-04-20

## Context

Across two consecutive slices (`compression/slice-1-infrastructure` and `compression/slice-2-state-machine`), `scripts/slice_orchestrator.py:981-1003` — the `close_slice` function — exhibited pathologies captured in `.claude/learning.md` C2 ("close_slice is the weakest link in the pipeline across two consecutive slices"):

- **R1** — close_slice is not idempotent. A crash between its three steps (write `slice.yaml status: complete`, bundle `handoff.md`, `git commit`) leaves partial state that `--resume` cannot recover from.
- **R2** — the wipe gap: after `9b34f44 slice: complete`, `.claude/current-slice/` retained intent.md, handoff-phase-{1..4}.md, integration/sweep-notes.md, and validation/ subtree. context-discipline-protocol Layer 3 (`docs/adr/context-discipline-protocol.md:79-84`) requires wiping every file except `slice.yaml`; current close_slice does not implement this step. Learning L8.
- **R3** — the redundant-commit race: the orchestrator's `run_phase_loop` calls `commit_phase_handoff(4, ...)` at `scripts/slice_orchestrator.py:841` on every phase-OK transition, producing a `handoff: phase 4 complete` commit; close_slice subsequently commits `slice: complete`. Two commits per close; ordering and intent unclear in `git log`. Learning C2. The original design-doc and brainstorm framing attributed this commit to the Phase-4 agent; Phase 5 independent verification revealed the orchestrator-code source.
- **R4** — no resume-after-mid-slice-crash reconciliation: the orchestrator has no mechanism to compare observable state across `orchestrator-result.json` (introduced by the companion orchestrator-observability ADR), `slice.yaml`, and `git HEAD` when it died mid-phase.

These are operational correctness failures of the close-slice lifecycle. Downstream projects consuming cairn via `.slice-system → .` inherit these pathologies automatically. The fleet-coordinator epic will consume slice-close state and will be blind to correctness gaps in the substrate it reads. This ADR establishes the close-slice correctness contract as a firm invariant.

**Phase 5 independent verification corrections.** A fresh-context subagent (per `/decision` protocol Phase 5) reran Phases 1-3 on the decision question and surfaced two corrections to the initial draft, applied below:

1. **R3 primary source is orchestrator code, not agent prompt.** `scripts/slice_orchestrator.py:732-743` defines `commit_phase_handoff`; `:841` calls it unconditionally for every phase OK including Phase 4. The Phase-4 agent prompt at `.claude/agents/phase-4-integrator.md:1-13` contains no `git commit` instruction. D2 below reflects the corrected enforcement: orchestrator-code skip is the primary mechanism; prompt constraint and defensive check are additional layers.
2. **Slug collisions are possible within INV-005's identifier space.** `_slice_id_slug` at `scripts/slice_orchestrator.py:187-188` maps `slice_id.replace("/", "-")`. Two distinct slice-ids (e.g., `a/b-c` and `a-b/c`) produce the same slug. D5 below gains a tripwire that converts silent overwrite into loud refuse.

The companion orchestrator-observability ADR (same session) establishes the observability-artifact representation (incremental JSON + MD sidecar + index.jsonl + heartbeat, placement in `.claude/orchestrator-debug/`, schema v1.0, heartbeat cadence). The two ADRs are co-landed: the observability shape is provisional and expected to iterate under fleet-coordinator consumer feedback; this ADR is firm because the lifecycle correctness properties are load-bearing for every future slice close.

**Placement supersession note.** The earlier `docs/plans/2026-04-20-compression-pipeline-hardening-design.md:201,250,257` placed `orchestrator-result.json` in `.claude/current-slice/`. The companion orchestrator-observability ADR supersedes that placement to `.claude/orchestrator-debug/`; this ADR references the new placement in D5 below.

## Decision

Cairn commits to five properties of the slice-close lifecycle. Three (D1, D2, D5) elevate to a new bundled invariant INV-008; two (D3, D4) are operational correctness contracts without dedicated INV numbers.

### D1 — Idempotent close (DC-3)

`close_slice` is safe to invoke any number of times. The precondition `_is_slice_already_closed(state)` checks four signals:

1. `slice.yaml` present and `status: complete`
2. `.claude/handoff.md` exists and is non-empty
3. `.claude/current-slice/` contains only `slice.yaml` (wipe verified)
4. `git log -1 --format=%s` equals the literal string `slice: complete`

If all four hold, close_slice returns early without side effects. If any fail, close_slice re-runs its steps in their canonical order. Step-level idempotency:

- `_write_slice_state(status=complete)` is idempotent (YAML overwrite).
- `_bundle_handoff_md()` is idempotent (handoff.md overwrite from current-slice files).
- `_wipe_current_slice()` is idempotent under D3's file-already-absent tolerance.
- `_git commit --allow-empty` is idempotent (empty-diff commit of same content is a no-op under `--allow-empty`).

### D2 — Sole commit source (DC-4)

The orchestrator's `close_slice` is the only producer of the `slice: complete` commit, AND the orchestrator itself does not emit any per-phase handoff commit at the Phase-4 boundary. The R3 redundant-commit race is produced by the orchestrator's own `commit_phase_handoff()` at `scripts/slice_orchestrator.py:732-743`, invoked from `run_phase_loop` at `scripts/slice_orchestrator.py:841` on every phase-OK transition — including Phase 4. The Phase-4 agent prompt (`.claude/agents/phase-4-integrator.md:1-13`) does not instruct the agent to commit; the redundant commit is orchestrator-issued.

Enforcement is three-layered.

**Primary — orchestrator code change.** `run_phase_loop` skips `commit_phase_handoff(phase, ...)` when `phase == max_phase`. For Phase 4 OK, the orchestrator proceeds directly to close_slice without emitting its own boundary commit. close_slice reads `handoff-phase-4.md` and `integration/sweep-notes.md` from the working tree, bundles them into `.claude/handoff.md` via `_bundle_handoff_md()` before wipe, then commits `slice: complete` with `slice.yaml` and `handoff.md` staged. This is the mechanical fix for R3; it is the load-bearing mechanism.

**Defense-in-depth — prompt constraint.** `.claude/agents/phase-4-integrator.md` gains the explicit rule: *"Do not issue any `git commit` in Phase 4. Produce `handoff-phase-4.md` and `integration/sweep-notes.md` as working-tree artifacts; the orchestrator's close_slice bundles and commits them."* This extends INV-003's textual-not-enforced role-discipline posture (`docs/adr/phase-lock-and-role-declaration.md:48`). The constraint guards against a future refactor adding `git commit` instructions to the Phase-4 prompt; it is not the primary mechanism because the prompt does not today contain such an instruction.

**Drift detector — orchestrator defensive check.** Before close_slice's `_git commit`, the orchestrator runs `git log -1 --format=%s` and compares against the anchored regex `^handoff: phase [0-9]+ complete$`. A match emits to stderr: `orchestrator: prior phase-commit detected on HEAD ('<subject>'); DC-4 invariant may have been violated — see slice-close-contract D2`. The warning is advisory, not blocking. It catches both regressions: an orchestrator-code change that re-adds the Phase-4 boundary commit, and a Phase-4 agent whose future prompt acquires a `git commit` instruction. Prior art: `scripts/verify_handoff.sh:22` and `tests/unit/efficiency_program/test_item_04_handoff_verifier.py:37`.

The three layers together: orchestrator-code skip is the contract; prompt constraint is the cognitive surface (future-proof against prompt additions); defensive check is the drift detector. Pre-mortem scenarios F2a (orchestrator-code regression re-adding `commit_phase_handoff(4, ...)`) and F2b (agent-prompt drift) are both addressed.

**Phase 4 FAILED path** is out of scope for this ADR. When Phase 4 fails and close_slice is not invoked, the Phase-4 artifacts remain uncommitted in the working tree. A follow-up slice addresses the failed-slice preservation path (`docs/adr/context-discipline-protocol.md:83-84` exemption and `.claude/completed-slices/<id>-failed/`).

### D3 — Wipe semantics (DC-5, operational)

`_wipe_current_slice()` deletes every file in `.claude/current-slice/` except `slice.yaml`. This implements INV-002 Layer 3 for the orchestrator path. Semantics:

- **Deletion scope.** Every non-`slice.yaml` file recursively. Empty directories after deletion are removed.
- **File-already-absent tolerance.** Attempting to delete a file that does not exist is not an error. This handles operator rebase/reset edge cases (F5 pre-mortem): close_slice re-run after HEAD was manually reset finds an already-wiped tree and proceeds cleanly.
- **Other `OSError` classes propagate.** Permission denied, IO error, or similar filesystem-layer failures raise `RuntimeError` from `_wipe_current_slice()`, which close_slice does not catch. The slice exits non-zero.

The wipe is strict in the failure direction (cannot silently leave residue) and tolerant in the success direction (already-wiped is success).

### D4 — Resume reconciliation (DC-6, operational)

The `--resume` path reads state before acting. `_reconcile_resume_state()` reads (a) `orchestrator-result.json` if present, (b) `slice.yaml`, (c) `git log -1 --format=%s` on HEAD, and optionally (d) `.claude/current-slice/.heartbeat` mtime. The reconciliation matrix:

| `result.json` status | `slice.yaml` | HEAD | Action |
|----------------------|--------------|------|--------|
| absent | absent | any | Fresh slice — start at Phase 1 |
| absent | `in-progress` | subject matches `^slice: .* — init$` | **Re-init from slice.yaml** — populate result.json with `current_phase=1`, persist, continue at Phase 1 |
| absent | `in-progress` | any other subject | **Refuse** — "result.json absent; slice.yaml claims in-progress; HEAD advanced past init; manual intervention required"; exit 1 |
| `IN_PROGRESS` | `in-progress` | matches json's `current_phase` | Resume at `current_phase` |
| `IN_PROGRESS` | `in-progress` | ahead of json's `current_phase` | **Refuse** — "JSON stale vs HEAD"; exit 1 |
| `IN_PROGRESS` | `in-progress` | behind json's `current_phase` | **Refuse** — "expected commit missing"; exit 1 |
| `IN_PROGRESS` | `complete` | subject `slice: complete` | **Fix up** — JSON lagged after close; set `status=OK`, `final_commit=HEAD`, `ended_at=now`, persist, exit 0 |
| `OK` | `complete` | subject `slice: complete` | **Already closed** — print "already closed"; exit 0 |
| `OK` | `complete` | subject not `slice: complete` | **Refuse** — "JSON OK but commit missing"; exit 1 |
| `OK` | `in-progress` | any | **Refuse** — "JSON ahead of slice.yaml"; exit 1 |
| `DEGRADED` | (any) | (any) | Treat as `IN_PROGRESS`; apply corresponding row |
| `FAILED` / `ABORTED` / `SIGNALED` | `in-progress` | any | **Refuse** — "prior run terminated as <status>; manual intervention"; exit 1 |
| corrupt JSON | (any) | (any) | **Refuse** — "result.json parse error"; exit 1 |

Any state-triple not appearing in a matrix row refuses with the literal triple printed to stderr plus an "unrecognized resume state" prefix; this provides exhaustive coverage by construction.

**Heartbeat advisory.** After matrix resolution and before resuming, if `.heartbeat` mtime is within `CAIRN_HEARTBEAT_STALE` seconds (default 30), emit to stderr: `orchestrator: .heartbeat is <age>s old — another orchestrator may be alive; proceed with caution`. Advisory only, non-blocking, does not affect matrix resolution. When the multi-instance slice lands worktree-scoped locking, this advisory tightens to a refuse.

### D5 — Cross-slice artifact isolation (DC-7)

Every file in `.claude/orchestrator-debug/` is keyed by a `<slice-id-slug>` prefix, except `index.jsonl`, which is a single shared append-only stream whose entries carry a `slice_id` field.

**Slug derivation.** Given a slice-id matching the `identifier-scheme` shape `<feature>/<slice>` (`docs/adr/identifier-scheme.md`), the slug is produced by replacing the single `/` with a single `-` (current implementation at `scripts/slice_orchestrator.py:187-188`). Example: `compression/slice-3-observability-and-close-slice` → `compression-slice-3-observability-and-close-slice`. The transformation is a string rewrite; no encoding of other characters. Slice-ids not matching the `<feature>/<slice>` shape fall through to a literal rewrite of the entire slice-id string with `/` → `-`.

**Files keyed by slug.** `<slug>-result.json`, `<slug>-result.md`, `<slug>-phase-{N}-{role}-{ts}.log` (failure logs; existing writer unchanged).

**Slug collision tripwire.** Per INV-005 (`docs/adr/identifier-scheme.md`), feature IDs and slice IDs are independent flat slugs. Two distinct slice-ids can produce the same slug after `replace("/", "-")` — e.g., `compression/slice-3-foo` and `compression-slice/3-foo` both produce `compression-slice-3-foo`. Collisions are rare but permitted by the identifier scheme. To convert silent data loss into loud refuse: when `_persist_state` opens `<slug>-result.json` for write, it first reads the file if present and parses its `slice_id` field. If the existing `slice_id` does not match the current slice's ID, the orchestrator exits FAILED with stderr: `orchestrator: slug collision — <slug> is already claimed by <other_slice_id>; rename one of the two slices and retry`. The check is a single stat + single JSON parse; it fires only on collision and does not run on first-write (file absent is the common case).

### Invariant declaration

**INV-008** — *Slice-close lifecycle correctness.* The orchestrator's `close_slice` function satisfies three properties that are separately testable and collectively form the close-slice correctness contract:

(a) **Idempotent close** — close_slice is safe to invoke any number of times; the precondition `_is_slice_already_closed` short-circuits second and subsequent invocations.

(b) **Sole commit source** — the orchestrator's `run_phase_loop` does not emit a Phase-4 boundary commit; close_slice is the only producer of the `slice: complete` commit; the Phase-4 agent does not issue `git commit`; its artifacts are bundled by close_slice into `.claude/handoff.md` before wipe.

(c) **Cross-slice artifact isolation** — every per-slice file in `.claude/orchestrator-debug/` carries a slice-id-slug filename prefix; `index.jsonl` is shared but tags each entry with `slice_id`; slug collisions are refused loudly at write time.

Machine-check path is pytest:
- `tests/unit/test_close_slice_hardened.py::test_close_slice_twice_is_noop`
- `tests/unit/test_close_slice_hardened.py::test_close_slice_produces_single_slice_complete_commit`
- `tests/unit/test_close_slice_hardened.py::test_run_phase_loop_skips_commit_at_phase_4_boundary`
- `tests/unit/test_agent_prompt_updates.py::test_phase_4_prompt_forbids_self_commit`
- `tests/unit/test_cross_slice_isolation.py::test_sequential_slices_keep_separate_result_files`
- `tests/unit/test_cross_slice_isolation.py::test_slice_id_slug_used_in_all_debug_paths`
- `tests/unit/test_cross_slice_isolation.py::test_slug_collision_exits_failed`

## Consequences

**Made easier:**

- close_slice becomes safe to re-run under any crash or operator-intervention scenario. `--resume` has defined behavior for every observed state-triple combination (D4's matrix).
- `git log --oneline` for any slice has exactly one close-related commit (`slice: complete`). Slice-close history is unambiguous.
- Fleet-coordinator era gets a reliable substrate: slice-complete commits are unique, per-slice artifacts are named, `index.jsonl` stream can be tailed across slices.
- Operator-facing errors are explicit. Resume-path refusals name the reason and suggest manual intervention; they do not silently pick a wrong winner.
- Slug collisions — theoretically possible under INV-005 — become observable rather than silent.

**Made harder:**

- Phase-4 boundary behavior changes. The orchestrator-code change (skipping `commit_phase_handoff` at Phase 4) and the prompt-constraint change must land in the same commit cluster; partial landing produces either R3 regression (if orchestrator code lands without skip) or harmless stderr warnings (if skip lands and prompt guard is pending).
- `_is_slice_already_closed` reads four signals including a `git log` call. Cold-start close has a ~30–50ms overhead per invocation. Not material for human-scale workflows.
- `_persist_state` performs a slug-collision check on every write. One `stat` + one small JSON parse per state transition; negligible.
- INV-008 is firm. Supersession requires a new ADR. Future refactors of close_slice or Phase-4 integration must preserve these three properties or supersede this ADR.
- The resume matrix has 13 rows plus a default-refuse clause. Operator cognitive load on unusual resume scenarios is higher than a trivial matrix.

**Invariant impact:**

- **INV-002 Layer 3 (wipe on close).** This ADR operationalizes the wipe in `_wipe_current_slice()` with F5-tightened semantics. No INV-002 text change; the mechanism-naming is consistent with INV-002's commitment.
- **INV-003 D2 Auditor anti-behavior.** This ADR adds "does not self-commit; close_slice finalizes" to Phase-4 Auditor's anti-behavior list. This is an additive narrowing consistent with INV-003's "instructed not hook-enforced" posture (`docs/adr/phase-lock-and-role-declaration.md:48`). No INV-003 text change; the addition is absorbed into the anti-behavior table via normal operational-reference updates when the follow-up operational-reference slice lands.
- **INV-008 (new).** Declared by this ADR. `/refresh-architecture` propagates it to `docs/ARCHITECTURE.md` with an `invariant-check` block naming the pytest targets above.

**Operational envelope:**

- `.claude/orchestrator-debug/**` is reserved as orchestrator-owned substrate (companion orchestrator-observability ADR D1 defines placement). `/integration-sweep` does not trim this directory; any future rotation policy requires an explicit superseding slice (deferred per orchestrator-observability D8's tripwire).
- `.claude/current-slice/.heartbeat` is reserved as ephemeral per-slice liveness. Wiped by D3.

## Alternatives Considered

### D2 enforcement alternatives

| Approach | Core idea | Why rejected or chosen |
|----------|-----------|--------------|
| **C1 — prompt-only** | `.claude/agents/phase-4-integrator.md` says "do not self-commit"; grep test enforces | **Misidentifies R3 source.** R3 is produced by the orchestrator's `commit_phase_handoff(4, ...)` at `scripts/slice_orchestrator.py:841`, not by the Phase-4 agent (whose prompt contains no `git commit` instruction). Even if prompt enforcement were perfect, the orchestrator would continue emitting the commit. Revealed during Phase 5 verification. C1 remains in the taxonomy as defense-in-depth but is not a standalone solution |
| **C2 — orchestrator-side reconciliation** | close_slice detects pre-existing `handoff: phase N complete` commit on HEAD, amends or refuses | Rejected at `docs/plans/2026-04-20-observability-and-close-slice-brainstorm.md:308`: more code, less discipline. close_slice taking ownership of git-state reconciliation expands its surface for correctness bugs |
| **C3 — role-scoped Bash hook** | Extend `checks/role_guard.py` to gate `Bash` tool calls matching `git commit` when `AGENT_ROLE=phase-4-integrator` | Blocked by `docs/adr/compression-infrastructure-bootstrap.md:68-70`: "Does not authorize role-keyed enforcement of any other tool class." Expanding role_guard scope requires a dedicated ADR and is out of scope for slice 3 |
| **C4 — chosen: orchestrator-code skip + prompt + defensive warning** | `run_phase_loop` skips `commit_phase_handoff(phase)` when `phase == max_phase`; prompt constraint guards against future prompt additions; defensive `git log -1 --format=%s` check warns on regression | Addresses the actual R3 source (orchestrator code) surfaced during Phase 5 verification. Three-layer design: mechanical fix for the known-present bug + prompt constraint against hypothetical future-prompt-self-commit + defensive check as drift detector. Matches prior art at `scripts/verify_handoff.sh:22` |

### D4 matrix alternatives

| Approach | Core idea | Why rejected |
|----------|-----------|--------------|
| **Design-doc matrix only** | 10 rows; G1 (result.json absent + slice.yaml in-progress) unresolved | G1 is observable — orchestrator died between `init_new_slice` and first `_persist_state`. Undefined behavior on resume is unacceptable for a firm contract |
| **Strict-refuse-on-absent-json** | Always refuse when result.json absent + slice.yaml in-progress | Forces operator to delete slice.yaml manually on a recoverable case (HEAD exactly at init) |
| **Re-init always** | Re-init result.json from slice.yaml whenever absent | Silently loses work if HEAD advanced past init |
| **Chosen — refuse default + re-init guarded + default-refuse fallback** | Refuse by default; re-init only when HEAD subject matches `^slice: .* — init$`; unrecognized triples refuse with the triple printed | Tight guard recovers the recoverable case; default-refuse-on-unknown makes the matrix exhaustive by construction |
| **Heartbeat as blocker** | Resume refuses if heartbeat recent | False positives in single-instance use; multi-instance hardening is a separate slice |
| **Chosen — heartbeat advisory** | Warn but proceed | No false-positive blocks today; tightens naturally when multi-instance slice lands |

### Contract-level alternatives considered and rejected

- **DC-3 idempotency via lock file instead of precondition check.** Rejected: lock files interact poorly with `--resume` after crash (stale lock problem); precondition check from observable state is simpler and correct.
- **DC-4 enforcement via removing Phase-4 commit authority entirely (C3).** Blocked by compression-infrastructure-bootstrap scope.
- **DC-5 strict-on-every-error.** Rejected: operator-rebase edge case (F5) produces spurious RuntimeError on re-close; file-already-absent tolerance is the minimum correct semantics.
- **DC-6 single-refuse matrix (every mismatch exits 1).** Rejected: JSON-lagged-after-close is a legitimate recoverable case; one fix-up row preserves forward progress without silently picking wrong state.
- **DC-7 per-slice subdirectories instead of slug prefix.** Considered: `.claude/orchestrator-debug/<slug>/result.json`. Rejected: two-deep glob for fleet-coordinator read; flat directory with slug-prefixed filenames matches existing failure-log pattern (`<slug>-phase-{N}-{role}-{ts}.log`).
- **DC-7 disambiguating slug scheme (`/` → `--`).** Considered to eliminate collisions structurally. Rejected: backwards-incompatible with existing `<slug>-phase-{N}-{role}-{ts}.log` files in `.claude/orchestrator-debug/`. D5 tripwire provides collision-safety without the rename cost.

## Risk Register

The Phase 1 pre-mortem produced five scenarios; Phase 5 independent verification surfaced a sixth. Each is addressed by the chosen approach or explicitly accepted.

- **F1 — Schema forward-compat bet missed.** Addressed by the companion orchestrator-observability ADR's B2/B3 hybrid. This ADR's lifecycle contract is schema-agnostic (it uses `status`, `current_phase` without assuming shape of auxiliary fields); if schema v2 supersedes v1, close_slice reads the latest shape.
- **F2 — DC-4 enforcement drift.** Two sub-scenarios, both addressed by D2's three-layer enforcement:
  - **F2a — Orchestrator-code regression.** A future refactor re-adds `commit_phase_handoff(phase=max_phase, ...)` to `run_phase_loop`. Addressed by the `test_run_phase_loop_skips_commit_at_phase_4_boundary` unit test, plus the defensive check surfacing drift as stderr warnings.
  - **F2b — Agent-prompt drift.** A future prompt rewrite adds a git-commit instruction to the Phase-4 agent. Addressed by the prompt constraint + grep test, plus the defensive check surfacing the resulting commit.
  Phase 5 independent verification established F2a as the primary risk; the original pre-mortem framing (F2b only) came from a misreading of R3's source.
- **F3 — DEGRADED signal collapse.** Addressed by the companion orchestrator-observability ADR's D7 persistence contract (`degradation_reason` is append-preserving).
- **F4 — Debug-dir growth unbounded.** Addressed by the companion orchestrator-observability ADR's D8 tripwire. This ADR's D5 ensures filenames are well-structured for future rotation.
- **F5 — DC-3 + DC-5 corner case on operator rebase.** Addressed by D3's file-already-absent tolerance. Operator rebase that drops the `slice: complete` commit causes `_is_slice_already_closed` to return False, close_slice re-runs, wipe tolerates already-gone files, re-commits.
- **F6 — Slug collision.** INV-005's identifier space permits two distinct slice-ids to flatten to the same slug. Addressed by D5's tripwire: on write, `_persist_state` reads any existing `<slug>-result.json`, confirms `slice_id` matches, exits FAILED on mismatch with a loud refuse. Surfaced during Phase 5 verification; converts a theoretical silent-data-loss bug into a loud-exit recoverable situation.

### Assumption audit

Thirteen assumptions classified. Four are catastrophic-if-wrong; each has a named mitigation.

| # | Assumption | Status | Degradation | Mitigation |
|---|------------|--------|-------------|------------|
| 1 | `os.rename` within same directory is POSIX-atomic | Verified | N/A | — |
| 2 | `O_APPEND` writes of small bytes are atomic | Verified | N/A | — |
| 3 | Fleet-coordinator consumer pattern matches our schema | **Believed** | Graceful | B3 additive-safe contract in companion ADR |
| 4 | R3 sources are (a) orchestrator `commit_phase_handoff(4, ...)` and (b) hypothetical future Phase-4 prompt addition | **Verified (a)** / Believed (b) | Graceful | D2 three-layer enforcement (orchestrator-code skip + prompt + defensive check) |
| 5 | Heartbeat thread survives laptop sleep | Believed | Graceful | D4 advisory only |
| 6 | `schema_version` consumer contract "ignore unknown fields" is implementable | Verified | N/A | — |
| 7 | F4 tripwire (100 files / 1 MB) fires before operator pain | Believed | Graceful | Tripwire-in-ADR makes deferral observable |
| 8 | `_is_slice_already_closed` handles operator rebase | **Believed** | Catastrophic | D3 file-already-absent tolerance |
| 9 | `index.jsonl` is per-worktree | Design choice | Correct by construction | — |
| 10 | R3 is the only close_slice pathology currently known | Verified (`.claude/learning.md:29`) | Graceful | New pathologies → new slice |
| 11 | DC-4 prompt-change matches INV-003 "instructed not hook-enforced" | Verified (`docs/adr/phase-lock-and-role-declaration.md:48`) | N/A | — |
| 12 | `degradation_reason` persists through terminal transition | **Believed** | Catastrophic | D7 persistence contract in companion ADR |
| 13 | `_slice_id_slug` (`scripts/slice_orchestrator.py:187-188`) is collision-free within INV-005 identifier space | **Verified false** — collision permitted between e.g. `a/b-c` and `a-b/c` | Catastrophic (silent data loss) | D5 slug collision tripwire converts to loud refuse |

### Load-bearing belief and tripwire

INV-008 rests on **A4**: *"Pre-commit checks of a four-signal state — slice.yaml complete + handoff.md present + current-slice wiped + HEAD matches `slice: complete` — correctly identifies already-closed slices across all operator scenarios."*

If A4 is wrong, `_is_slice_already_closed` false-positives (treats in-progress as closed → breaks idempotency) or false-negatives (treats closed as in-progress → redundant commits).

**Tripwire.** The slice implementing this ADR lands `tests/unit/test_close_slice_hardened.py::test_close_slice_twice_is_noop` and related tests. Any slice-close scenario observed in the wild that is not covered by those tests is a candidate A4-falsification event. Two such events in a rolling 10-slice window trigger supersession review.

## Consequences for in-progress work

- **Compression Slice 3 (observability + close_slice hardening)** implements this ADR. Its scope includes the `run_phase_loop` skip at Phase 4, the `_is_slice_already_closed` precondition, the DC-5 wipe, the DC-6 matrix, and the DC-7 slug tripwire plus associated tests.
- **Fleet-coordinator epic (future)** reads `.claude/orchestrator-debug/` artifacts; this ADR's D5 ensures the substrate is consumable.
- **parallelism-v1** is unaffected by this ADR; multi-instance locking remains a future slice, and the heartbeat advisory in D4 is the current-slice hook for that future tightening.
