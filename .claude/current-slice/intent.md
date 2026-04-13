```yaml
slice: phase-rethink
date: 2026-04-13
phase: 1-intent
invariants-touched: [INV-003]
adrs-referenced: [ADR-004, ADR-003]
envelope:
  - "docs/adr/*-phase-*.md"
  - "docs/operational-reference.md"
  - "commands/claude-code/start-slice.md"
  - "commands/claude-code/catchup.md"
  - "tests/unit/test_phase_*.py"
out-of-scope:
  - "Hook implementation changes (checks/*.sh) — hooks adapt to whatever phases land, but are not redesigned here"
  - "Windsurf port (roadmap item 7) — phase shape informs it, but the port is a separate slice"
  - "D1/D2/D3 defense mechanism design — those slices consume the phase shape, they don't define it"
```

### What and Why

ADR-004 locked the slice pipeline at four phases (Intent/Validation/Implementation/Integration) with firm roles (Reader/Skeptic/Builder/Auditor) after 2 slices of experience. Five more slices have shipped since. The lock was the right call at the time — it prevented churn during early dogfood — but the strict definitions create friction when work doesn't fit the implementation-heavy mold the phases assume. Not all slices produce code; some produce ADRs, documentation restructuring, or protocol changes. The same 4-phase ceremony applies uniformly regardless.

Before roadmap item 2 (protocol extraction to `protocols/phase-N-<role>.md`) bakes the current phase shape into standalone files, we need to evaluate whether the abstraction level is right. Too strict and the system fights legitimate work patterns. Too loose and the correlated-error defense — the reason phases exist — dissolves.

This slice evaluates the current phase structure against observed usage patterns and determines whether ADR-004 should be confirmed, amended, or superseded.

### Specification Detail

**What this slice produces:** An ADR — either confirming ADR-004's current shape holds, or superseding it with an updated phase structure. The ADR must address:

1. **Phase count and names** — Are four phases the right number? Are the current names load-bearing or misleading for non-code work?
2. **Role flexibility** — Do Reader/Skeptic/Builder/Auditor map to all work types, or do some roles become vacuous for certain slice categories?
3. **Ceremony calibration** — Which phases can be lightweight (or skipped) for which categories of work, without losing the correlated-error defense?
4. **Protocol extraction readiness** — Whatever shape lands must be stable enough that roadmap item 2 can extract it without immediate churn.

**What this slice does NOT produce:** Implementation of the phase changes. If the ADR changes the phase structure, a follow-up slice implements it across operational-reference.md, slash commands, and hooks.

**Evidence required:** The evaluation must cite specific slices (SLICE-001 through SLICE-005) where the current structure fit well, fit poorly, or required workarounds. Claims without slice evidence are assertions, not findings.

### Boundary

- Does NOT implement protocol extraction (roadmap item 2) — only ensures the phase shape is ready for it
- Does NOT change hook behavior — hooks adapt downstream
- Does NOT redesign the `/decision` protocol — the decision/slice routing stays as-is per operational-reference.md
- Does NOT touch ADR-003's defense commitments — D1/D2/D3 consume the phase shape

### Verification

1. The output ADR explicitly addresses all four specification items (phase count, role flexibility, ceremony calibration, protocol-extraction readiness)
2. The ADR cites at least 3 of the 5 completed slices as evidence for its claims
3. If superseding ADR-004, the new ADR's Consequences section names every file that string-matches on phase names (per ARCHITECTURE.md Boundaries section) and declares migration path for each
4. If confirming ADR-004, the ADR explains what changed since the original decision to justify re-confirmation (not just "it still works")
5. The A2 tripwire status (ADR-004 Risk Register) is evaluated against available evidence and the finding is recorded
