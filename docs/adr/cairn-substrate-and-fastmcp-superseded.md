---
id: cairn-substrate-and-fastmcp-superseded
name: "Cairn substrate (FastMCP) — superseded"
status: firm
firmness: firm
supersedes: cairn-substrate-and-fastmcp
date: 2026-05-07
program: cairn-shrink-m4
---

# Cairn substrate (FastMCP) — Superseded

## Context

The cairn-substrate-and-fastmcp ADR governed the typed-knowledge graph
(`scripts/cairn_query/`), the FastMCP MCP wrapper (`mcp_servers/cairn_knowledge/`),
the kuzu and fastmcp deps, and INV-010's read-class lockdown under cairn's
pre-shrink architecture.

Per docs/plans/2026-05-06-cairn-shrink-design.md §3.2 / §7, that subsystem retires
in M4 (2026-05-07). This ADR records the supersession.

## Decision

cairn-substrate-and-fastmcp is superseded. The typed-knowledge graph
(`scripts/cairn_query/`), the MCP wrapper (`mcp_servers/cairn_knowledge/`),
the kuzu and fastmcp deps, and the substrate's INV-010 enforcement contract
all retire in M4. The substrate's cost-justification dissolves with targeted
reads + in-brief context; the typed-records value is not load-bearing for
solo-dev TDD and may be re-introduced if a real graph-class query emerges
that grep cannot satisfy.

The surviving behavior — if any — is captured in the carry-forward inventory at
docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md §2.

## Consequences

- `scripts/cairn_query/` deleted (~1900 LOC).
- `mcp_servers/cairn_knowledge/` deleted (JSON-RPC dispatcher).
- kuzu and fastmcp pruned from `pyproject.toml`; `uv.lock` regenerated.
- INV-010 retires (substrate-mediated knowledge access). Removed from
  `ARCHITECTURE.md`.
- `role_guard.py`'s `_CANONICAL_DENY_PATTERNS` / `ROLE_DENY_READ` deleted (no
  substrate to force agents toward).
- Consumer projects continuing to reference the substrate must migrate per
  the M5 plugin packaging plan (out of M4 scope).

## References

- docs/plans/2026-05-06-cairn-shrink-design.md §3.2, §7
- docs/plans/2026-05-06-cairn-shrink-m3-bathwater-audit.md
