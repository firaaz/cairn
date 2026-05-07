# role_guard.py — Post-Orchestrator Simplification Design

```
firmness: provisional
status: design — informs M4 implementation
date: 2026-05-06
scope: target shape for checks/role_guard.py once orchestrator + substrate retire (M4)
inputs:
  - docs/plans/2026-05-06-cairn-shrink-design.md §2.2, §4
  - checks/role_guard.py (current)
  - docs/adr/cliff-failure-mode-and-v1-defenses.md (D9 envelope-grant escape)
  - docs/adr/compression-infrastructure-bootstrap.md (phase-3 envelope asymmetry)
```

## 1. What dies, what survives

**Dies (M4):**

- `_CANONICAL_DENY_PATTERNS` — the read-class lockdown of `scripts/cairn_query/`, `docs/ARCHITECTURE.md`, `docs/adr/`, `docs/lessons.md`, `docs/spec-v1.md`, `docs/operational-reference.md`. Without the substrate (cairn_query + MCP), there is no MCP-equivalent to force agents to use. The lockdown was substrate-machinery; it dies with the substrate.
- `ROLE_DENY_READ` table — emptied (or removed entirely; see §3 option (a) vs (b)).
- The Bash-token deny logic (lines 179-189) — only existed to lock down canonical-knowledge paths via `cat`/`head`/`grep`.
- INV-010 — the canonical-knowledge-lockdown invariant retires when its substrate retires; supersession ADR in M4 (per design §7 entry for `cairn-substrate-and-fastmcp`).

**Survives (M4 carries forward):**

- `READ_CLASS_TOOLS = {Read, Grep, Glob}` — still load-bearing for any future read-restriction (e.g., per-phase write boundaries that also need to gate Grep). Even if no current rule uses it, it's a one-line constant; cost-of-keeping is zero, cost-of-losing-and-re-deriving is positive.
- Envelope-grant mechanism (`_envelope_patterns`, `AGENT_ENVELOPE` parsing) — moves from "escape hatch" to "primary mechanism". The dispatch skill passes the source-write envelope as `AGENT_ENVELOPE`; `role_guard` enforces it.
- `_log_grant` / `.claude/envelope-grants.log` — preserves audit trail of envelope writes; trivial cost.
- Per-role write allowlists (`ROLE_POLICIES`) — preserved, but UPDATED to the new TDD agents' write paths (no `current-slice/` references).

## 2. Shape of the new module

Target structure (~70-90 lines, down from 226):

```python
"""PreToolUse hook — denies writes outside a role's allow-list when AGENT_ROLE is set.

Inner gate paired with each agent's `tools:` frontmatter. Reads tool-call JSON
from stdin. AGENT_ROLE unset is the no-op path. Post-shrink (M4):
- Read-class lockdown removed (canonical-knowledge-via-MCP retired).
- Write paths target dispatch-skill workspace (.claude/skill-runs/) and tests/.
- Phase-3 write gate is envelope-driven (AGENT_ENVELOPE), unchanged in spirit.
"""

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
READ_CLASS_TOOLS = {"Read", "Grep", "Glob"}  # preserved; not currently used by any rule

ROLE_POLICIES = {
    "phase-1-tdd": [
        r"^\.claude/skill-runs/[^/]+/intent\.md$",
    ],
    "phase-2-tdd": [
        r"^tests/",
        r"^\.claude/skill-runs/[^/]+/validation/",
    ],
    "phase-4-tdd": [
        r"^\.claude/skill-runs/[^/]+/integration/",
        r"^\.claude/handoff\.md$",
    ],
    # phase-3-tdd: no static entry; envelope-driven (preserves slice-2 asymmetry).
}
```

## 3. Two open questions for M4 implementer

### (a) Drop `ROLE_DENY_READ` entirely, or empty-dict it?

- **Drop entirely**: cleaner code; smaller surface; M4 supersession ADR for INV-010 makes this honest.
- **Empty-dict it**: forward-compatible if a future invariant wants to re-introduce a read lockdown for a different reason; cost is one constant.

Recommendation: **drop entirely**. Forward-compat without a use case is YAGNI.

### (b) Should `phase-3-tdd` get a static partial allowlist, or stay envelope-only?

- **Static partial**: reduces operator burden of envelope authoring; constrains drift.
- **Envelope-only (status quo)**: preserves the phase-3 asymmetry slice-2 enshrined; matches the dispatch-skill's existing envelope contract.

Recommendation: **envelope-only**. The dispatch skill's plan-doc frontmatter already carries the envelope; no second source.

## 4. Migration sequence for M4

1. Author supersession ADR for `cairn-substrate-and-fastmcp` (retires substrate; INV-010 retires).
2. Delete `_CANONICAL_DENY_PATTERNS`, `ROLE_DENY_READ`, the Bash-token deny block, and `_log_grant`'s slice-id reference (or update to a generic identifier).
3. Update `ROLE_POLICIES` keys from canonical role slugs (`phase-1-writer`, etc.) to TDD slugs (`phase-1-tdd`, etc.) with paths under `.claude/skill-runs/<feature>/`.
4. Update `ROLE_POLICIES` values from `current-slice/` paths to `skill-runs/<feature>/` paths.
5. Confirm INV-003 binding still passes — note: M4 also moves the canonical role-slug source out of `scripts/slice_orchestrator/core.py` (which dies). Either:
   - Move `ROLE_FOR_PHASE` to a stable location (e.g., `.claude/agents/role-topology.yaml`) and update the validator, OR
   - Retire INV-003's canonical-source-vs-mirrors check; replace with a simpler "the four canonical agent files exist" check.
   This sub-decision is M4's, not M3's.
6. Run the full suite. Add new tests for the simplified shape if existing tests bind to the old surface (e.g., the asymmetry-comment test asserts a specific comment in role_guard.py — preserve or update).

## 5. Don't-regress (carry-forward from §1)

- M4 plan MUST preserve `READ_CLASS_TOOLS = {Read, Grep, Glob}` even if unused (zero cost, future-proof).
- M4 plan MUST preserve `_envelope_patterns` parsing (JSON array shape, JSON object with `paths` key, legacy colon-separated with deprecation warning).
- M4 plan MUST preserve `_log_grant` writing to `.claude/envelope-grants.log` (audit surface — useful for forensics on the new TDD path too).
- M4 plan MUST preserve the phase-3 asymmetry decision (option (b) per `compression-infrastructure-bootstrap`): no static `ROLE_POLICIES` entry; envelope-driven.
- M4 plan MUST preserve INV-002(a) handoff structural binding's load-bearing role on `.claude/handoff.md` writes — the phase-4-tdd write rule must NOT bypass the structural-parser check (the parser runs in `validate_architecture.py`, independent; this is an integration-level commitment).
