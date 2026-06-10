---
id: compression-infrastructure-bootstrap-superseded
name: "Compression infrastructure bootstrap — superseded"
status: firm
contract:
  must-satisfy:
    - "per-role write allowlists enforce phase write paths (carrier: checks/role_guard.py ROLE_POLICIES)"
  evidence:
    - "tests/unit/test_role_guard_post_m4.py passes"
firmness: firm
supersedes: compression-infrastructure-bootstrap
date: 2026-05-07
program: cairn-shrink-m4
---

# compression-infrastructure-bootstrap-superseded: supersession record

## Status
Firm.

## Date
2026-05-07

## Context

compression-infrastructure-bootstrap (provisional, 2026-04-19) authorized `checks/role_guard.py` as a narrow hook for the compression feature's orchestrator dispatch and introduced AGENT_ENVELOPE as a write-allowlist primitive. M4 (cairn-shrink) retires the MCP-forcing gate (Task B1) and the standalone dispatch substrate, collapsing the compression orchestrator into the dispatch skill.

## Decision

compression-infrastructure-bootstrap is superseded. The compression program's
infrastructure — phase-3 envelope-driven write asymmetry under role_guard,
the canonical-knowledge MCP-forcing gate, AGENT_ENVELOPE as a JSON-array
write-allowlist primitive — survives in spirit. The dispatch skill's plan-doc
frontmatter carries the envelope; role_guard enforces phase-3 writes against
it. The MCP-forcing gate retires with the substrate (Task B1).

## Consequences

- Phase-3 asymmetry preserved (no static ROLE_POLICIES entry; envelope-driven).
- AGENT_ENVELOPE shapes (JSON-array, JSON-object-with-paths, legacy
  colon-separated) preserved per the M3 role_guard simplification doc §5.
- INV-003 narrow named exception clause retires (compression's orchestrator
  dispatch retires; phase-role enforcement now lives in the dispatch skill
  + role_guard, no longer scoped to "compression feature's orchestrator
  dispatch"); see Task C5 INV-003 amendment.
- Consumer projects continuing to reference the compression bootstrap must
  migrate per the M5 plugin packaging plan (out of M4 scope).
