---
id: compression-infrastructure-bootstrap
name: "Compression-infrastructure bootstrap — narrow authorization for role_guard.py hook"
status: accepted
firmness: provisional
supersedes: []
supersedes-sections: []
superseded-by: null
topic: process
adrs-referenced: [cliff-failure-mode-and-v1-defenses, phase-lock-and-role-declaration]
invariants-touched: [INV-003]
date: 2026-04-19
---

# compression-infrastructure-bootstrap: narrow authorization for role-scoped write-path hook

## Status
Accepted.

## Date
2026-04-19

## Context

The `compression` feature's plan (`docs/plans/2026-04-18-slice-compression-protocol-plan.md` §0) sequences the work as: **Slice A** ships compression infrastructure (orchestrator + role agents + `checks/role_guard.py` hook + thin `/start-slice` refactor) serially as bootstrap; **Slice B** dogfoods that infrastructure by writing the Part 0 ADR (P1–P6 + D1/D2/D3) under compressed execution.

Slice A cannot ship cleanly today because of a sequencing conflict:

- [INV-003](../ARCHITECTURE.md) ([phase-lock-and-role-declaration](phase-lock-and-role-declaration.md)) states "Roles are instructed in protocol text, **not hook-enforced** (commitment #6 mechanization is time-boxed to v2+ per cliff-failure-mode-and-v1-defenses D4)."
- [cliff-failure-mode-and-v1-defenses](cliff-failure-mode-and-v1-defenses.md) D4 defers commitment #6 role mechanization to v2+.
- `docs/ARCHITECTURE.md` §"Pre-v1 scope" requires any pre-v1 slice touching a remaining time-boxed area to declare an explicit non-v1-scope waiver in `intent.md` or be rejected.
- Slice B's Part 0 ADR — which would formally supersede D4's commitment-#6 time-box for the compression substrate — cannot land first because it depends on Slice A's orchestrator as its dogfood execution target (chicken-and-egg).

A waiver in intent.md is insufficient here. `role_guard.py` is not a known-deferred v2+ item being done early — it is a novel mechanism class (role-keyed write-path hook, adjacent to but distinct from envelope-keyed `scope-guard.sh`). Novel mechanisms warrant an ADR, not a waiver line. This ADR provides the narrowest possible authorization to unblock Slice A while preserving D4's broader time-box for every other commitment-#6 item until Slice B ratifies.

## Decision

### Decision 1 — Authorize `checks/role_guard.py` as a new hook class

A single PreToolUse hook — `checks/role_guard.py` — is authorized for the compression feature. The hook:

- Reads tool-call JSON from stdin (same interface as existing bash hooks).
- Keys enforcement on the `AGENT_ROLE` environment variable. When `AGENT_ROLE` is unset, the hook exits 0 (no-op). Non-compressed slices are unaffected.
- When `AGENT_ROLE` is set, restricts `Write` / `Edit` / `MultiEdit` / `NotebookEdit` tool calls to the declared-output path set for that role.
- Declared-output paths for the four phase roles plus `issue-triager` are defined by Slice A and are the authoritative write-scope table until Slice B's Part 0 ADR ratifies them.

This is the only role-keyed hook class authorized by this ADR. Scope is mechanism-specific, not role-specific: adding, say, a role-keyed scope on the `Read` tool or a role-keyed scope for subagent dispatch is **not** authorized and remains v2+ per cliff-failure-mode-and-v1-defenses D4.

### Decision 2 — Relationship to INV-003's "not hook-enforced" clause

INV-003's "instructed not enforced" commitment narrows — for the compression substrate only — to the **cognitive and behavioral** dimension of role discipline (what a role is allowed to *reason about*, what inputs it loads, what decisions it makes). Write-path enforcement becomes a new adjacent mechanism analogous to how [scope-guard.sh](../../checks/scope-guard.sh) enforces envelope boundaries without being read as a role mechanization.

The Reader-never-reads-source rule, the Skeptic-never-implements rule, the Builder-never-expands-scope rule, and the Auditor-never-patches rule all remain instructed-only. `role_guard.py` is a mechanical check on *write destinations*, not on what the role thinks.

### Decision 3 — Sunset commitment

This ADR is explicitly expected to be superseded by Slice B's Part 0 ADR. When that ADR lands:

- `supersedes:` in Slice B's Part 0 ADR must list `compression-infrastructure-bootstrap`.
- This ADR's frontmatter flips to `status: superseded` / `superseded-by: <Part 0 ADR id>`.
- INV-003's synthesized wording updates on the next `/refresh-architecture` to reflect Part 0's canonical formulation of hook-enforced role discipline.

If Slice B fails or is abandoned for more than 10 slices after this ADR lands (measured via the standard rolling-window slice counter), the compression feature itself must be re-evaluated — not this ADR promoted to firm. The provisional status is a load-bearing commitment to the Slice A / Slice B coupling, not a placeholder for indefinite continuation.

### Scope of this ADR — what it does NOT do

- **Does not supersede cliff-failure-mode-and-v1-defenses broadly.** D4's time-box on commitment-#6 mechanization remains in force for every role mechanization other than `role_guard.py`'s write-path enforcement.
- **Does not re-open commitment #6 in full.** Windsurf portability, split-agent slices, three-track routing, and the remaining D4 time-boxed items stay v2+.
- **Does not authorize role-keyed enforcement of any other tool class.** `Read`, `Bash`, subagent dispatch, and every non-write tool remain outside this hook's scope and outside this ADR's authorization.
- **Does not define the declared-output path table.** Slice A defines it in `role_guard.py`'s `ROLE_POLICIES` dict plus the `phase-3-implementer` envelope mechanism; Slice B's Part 0 ADR is the authoritative ratification of that table.

## Consequences

**Made easier:**

- Slice A can ship `checks/role_guard.py` without each write triggering an invariant review against INV-003. The hook has an explicit authorizing ADR.
- Slice B's dogfood becomes a genuine test of compressed execution rather than an out-of-order ratification — the Part 0 ADR is consumed by the orchestrator that already exists.
- The audit finding F1 (intent.md edited after Phase 2 started) gains mechanical prevention during Slice B's compressed execution, which is the point of the coupling.

**Made harder:**

- INV-003's synthesized wording in `docs/ARCHITECTURE.md` will need two versions: the narrow exception during the Slice A → Slice B window, and the full Part 0 formulation after. `/refresh-architecture` handles both; operators reading ARCHITECTURE.md mid-window should not be surprised by the transitional phrasing.
- Provisional-ADR debt increases by one until Slice B closes. The rolling-window check for provisional accumulation remains operator-visible.
- A second authorization surface exists for role-keyed hooks (this ADR) until Slice B's Part 0 ADR absorbs it. Any attempt to expand `role_guard.py`'s scope before Slice B closes must be rejected — this ADR's narrow scope is the ceiling.

**Invariant impact:**

- INV-003 is touched narrowly: the "not hook-enforced" clause acquires an explicit named exception for `role_guard.py` write-path enforcement. All other aspects of INV-003 remain unchanged.
- No other invariant is affected. `scope-guard.sh`'s envelope enforcement is orthogonal and unchanged. `reversibility-guard.sh`'s destructive-op blocks are orthogonal and unchanged.

## Alternatives Considered

- **Waiver in intent.md only (no ADR), per ARCHITECTURE.md §"Pre-v1 scope" line 114.** Rejected. The waiver path is designed for pre-v1 slices picking up known-deferred v2+ work, not for introducing novel mechanism classes. A role-keyed hook has no prior art in cairn; a mechanism-naming ADR is the right paper trail.

- **Do Slice B first (write the full Part 0 ADR before Slice A).** Rejected. Slice B's purpose per plan §0 is to *dogfood* the compressed execution path — it is the first compressed slice. Running Slice B serially would lose the dogfood target; running it compressed requires Slice A's orchestrator to exist. The sequencing in plan §0 (Slice A serial, Slice B compressed) is load-bearing for the program's correctness claim.

- **Bundle the Part 0 ADR into Slice A's deliverables.** Rejected. Bundling conflates two distinct concerns: the *infrastructure mechanism* (this ADR scopes) and the *full discipline principles* (Slice B's Part 0 scopes, P1–P6 + D1/D2/D3). Slice B's compressed-execution dogfood cannot validate the orchestrator if the ADR it produces is already known-to-exist from Slice A.

- **Edit cliff-failure-mode-and-v1-defenses D4 directly.** Rejected and mechanically blocked. `reversibility-guard.sh` enforces ADR append-only on body edits; supersession is the only authorized change path. Direct edit would be a violation of cairn's own invariant chain.

- **Promote this ADR to firm.** Rejected. Firm ADRs require the Phase 5 independent-verification protocol (per `commands/claude-code/decision.md`), and this ADR is explicitly a transitional authorization expected to be superseded within a named window. Provisional is the correct firmness for a decision whose sunset is already planned.

## Risk Register

- **Risk:** Slice B delays past the 10-slice window and this ADR becomes de facto permanent without Part 0 ratification. **Mitigation:** Decision 3's sunset commitment names the window explicitly; if Slice B stalls, the compression feature itself is re-evaluated rather than this ADR promoted. The debt is visible to every integration sweep via the provisional-ADR count.

- **Risk:** Scope creep — "we already have role-keyed hooks" becomes license for new role-keyed mechanisms (role-keyed Read gates, role-keyed subagent dispatch filters). **Mitigation:** Decision 1's scope is mechanism-specific, not role-specific. This ADR's "Scope of this ADR" section enumerates what it does NOT authorize; any new role-keyed mechanism requires its own ADR or explicit inclusion in Slice B's Part 0 ADR.

- **Risk:** `role_guard.py` has bugs that deny legitimate writes during Slice A's own development (chicken-and-egg). **Mitigation:** The hook is a no-op when `AGENT_ROLE` is unset. Slice A's own phases (1–4) run under the *existing* serial `/start-slice` protocol without compressed dispatch, so `AGENT_ROLE` is unset and the hook has no effect on Slice A's implementation path. The hook only activates once the orchestrator dispatches Slice B.

- **Risk:** INV-003's synthesized wording in `docs/ARCHITECTURE.md` becomes inconsistent with `phase-lock-and-role-declaration`'s own body text during the Slice A → Slice B window. **Mitigation:** `/refresh-architecture` is deterministic over the ADR corpus; the transitional phrasing is a feature of the corpus at this moment, not a validator violation. Operators reading ARCHITECTURE.md will see the narrow exception cited to this ADR until Slice B supersedes.

- **Risk:** `role_guard.py`'s declared-output table diverges from Slice B's Part 0 formulation. **Mitigation:** Slice B's Part 0 ADR is required to list `compression-infrastructure-bootstrap` in its `supersedes:` field, and its ratification commitment includes reconciling the tables. If Slice B's Part 0 changes the table, `role_guard.py` is updated in the same slice.
