```yaml
slice: context-budget-compression
date: 2026-04-12
phase: 1-intent
invariants-touched: [INV-002, INV-004]
adrs-referenced: [ADR-002, ADR-004]
envelope:
  - "commands/claude-code/*.md"
  - "CLAUDE.md"
  - "docs/operational-reference.md"
  - "tests/unit/test_context_budget.py"
  - "tests/unit/test_progressive_disclosure.py"
  - "docs/plans/measurements/*"
out-of-scope:
  - "ADR creation (no ADR-005; INV-004 ADR deferred to later slice)"
  - "checks/*.sh hook changes"
  - "scripts/validate_architecture.py changes"
  - "docs/spec-v1.md edits"
  - "Self-learn flow (SLICE-004)"
  - "D1.2 superpowers hook reclaim (deferred if Phase 1 finds no path)"
  - "Auto-memory rules block reclaim (deferred if not settings-editable)"
```

### What and Why

Cairn sessions start at ~27.3k turn-1 tokens (D1 baseline). The target is ≤22k (hard) / ≤20k (aspirational). Most addressable headroom is in slash commands loaded whole-file on invocation. This slice introduces progressive disclosure at the skill level: each command becomes a ≤500-token lite file (always loaded) with an optional `.full.md` sibling (loaded only when a discrete predicate fires). A CLAUDE.md terseness rule caps output growth. Together these drop turn-1 context to ≤22k.

### Specification Detail

**Progressive disclosure pattern.** Two-file pair per command in `commands/claude-code/`:

Lite file (`<name>.md`, ≤500 tokens, always loaded):
- Fixed structure: `# /<name>`, one-line purpose, `## Rules` (numbered imperatives), `## Load full` (discrete predicates pointing at `<name>.full.md`)
- Banned: Graphviz/digraph blocks, ASCII diagrams, box-drawing characters (U+2500–U+257F), prose rationale, "why" explanations, examples >1 line, H3+ headers

Full file (`<name>.full.md`, loaded on predicate only):
- Contains rationale, edge-case handling, longer examples, historical context
- No token cap but aggressive prose compression applies
- Not every command needs one (small commands may land under 500 tokens as-is)

Load triggers MUST be discrete predicates the LLM can evaluate from visible state ("if `mode == 'dirty-recovery'`"), NEVER subjective states ("if confused").

**INV-004 — session-start token budget.** Turn-1 total context (system + tools + memory + skills + injections) ≤22,000 tokens on a clean "hi" message in cairn. Aspirational: ≤20,000. Measured from most-recent session JSONL (`input_tokens + cache_creation_input_tokens + cache_read_input_tokens`). Test records CC version for version-bump diagnosis.

**Structural tests S1–S5:**
- S1: every non-`.full.md` file in `commands/claude-code/` ≤ 500 tokens
- S2: every lite file contains a `## Load full` section
- S3: every predicate under `## Load full` points at an existing `.full.md` OR says "no full form"
- S4: no lite file contains `digraph`, `\bdot\s*{`, or box-drawing U+2500–U+257F
- S5: no lite file contains H3 (`###`) or deeper headers

**CLAUDE.md terseness rule.** One line (~30 tokens): "Default to terse replies. No preamble, no trailing summary. One sentence between tool calls unless the work demands more."

**V1–V7 hard gate.** `tests/unit/test_context_discipline_protocol.py` must pass unchanged. Any compression that breaks a V-test is reverted.

**Numbering correction.** Design doc (`docs/plans/2026-04-12-context-budget-compression-design.md`) calls the new invariant INV-003. ARCHITECTURE.md already has INV-003 (four-phase lock, ADR-004). The new invariant is INV-004.

**Slice numbering.** SLICE-003 = this slice (context compression). SLICE-004 = self-learn flow (previously "Slice #3" in D1 plan docs). Design doc line 146 contradicts line 148 on this; line 148 (the explicit numbering note) is authoritative.

### Carried-Forward Items

- **I1** (slice.yaml close exception): Resolved by rewriting start-slice.md with clear wording in the lite/full split.
- **M1** (`## Session Handoff Protocol (overview)` rename): Folded into docs/operational-reference.md edits — renamed to `## Session Handoff Protocol` (drop "(overview)").
- **L-001** (scar-class debt, INV-001): Acknowledged, not resolved. 14 non-slice commits remain per sweep notes. Tracking continues.
- **Stale handoff line**: Already resolved — current handoff.md has no precursor reference.

### Boundary

- No ADR creation. INV-004 is declared in this intent and added to ARCHITECTURE.md at Phase 4 via `/refresh-architecture`. Formal ADR deferred — if progressive disclosure holds for 2+ slices, it graduates to ADR-005.
- No hook changes (`checks/*.sh`).
- No validator changes (`scripts/validate_architecture.py`).
- No spec edits (`docs/spec-v1.md`).
- Self-learn flow is SLICE-004, not this slice.
- D1.2 (superpowers SessionStart hook) and auto-memory investigations are Phase 1 time-boxed. If reclaimable, envelope stays the same (settings changes, not cairn files) but INV-004 aspiration may improve. If not reclaimable, deferred with documentation.

### Verification

1. V1–V7 pass unchanged (INV-002 hard gate)
2. `test_context_budget.py`: turn-1 tokens ≤22,000 on fresh "hi" session (INV-004)
3. `test_progressive_disclosure.py`: S1–S5 all pass for every lite file
4. Every `commands/claude-code/*.md` is either ≤500 tokens or has a `.full.md` sibling
5. CLAUDE.md contains the terseness rule
6. Delta vs D1 baseline (27,314 tokens) recorded in `docs/plans/measurements/2026-04-12-slice-003.txt`
7. Carried-forward items I1 and M1 resolved in rewritten files; L-001 acknowledged
