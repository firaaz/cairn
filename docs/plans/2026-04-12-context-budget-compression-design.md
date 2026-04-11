# Context Budget Compression — Design

Date: 2026-04-12
Status: validated design, ready for slice sequencing
Author: session-brainstorming with user
Slice: SLICE-003

## Problem

Post-D1 (`2026-04-11-d1-completion.md`), cairn sessions start at ~27.3k turn-1 tokens. The user observes ~30k on a clean "hi" message, which is baseline plus normal measurement variance. The target is a session-start floor of ≤22k tokens (hard) with an aspirational landing zone of ~20k.

The ~5–10k of addressable headroom lives in four places:

1. **Slash-command bodies.** `commands/claude-code/start-slice.md` (14.7 KB), `catchup.md` (9.5 KB), `decision.md` (8.3 KB), `handoff.md` (5.7 KB), `integration-sweep.md` (5.1 KB), `new-adr.md` (3.6 KB), `refresh-architecture.md` (3.0 KB), `status.md` (2.2 KB). These are Markdown cairn owns and can rewrite. Most contain ASCII/Graphviz diagrams and prose rationale that add tokens without improving LLM decision-making.
2. **ASCII art and Graphviz blocks** inside the above files. Numbered conditional rules compress ~3–5× against `digraph` blocks while remaining machine-parseable. The audience for these files is the LLM, not a human reader browsing GitHub.
3. **CLAUDE.md has no terseness rule for output growth.** Session growth past turn 1 is dominated by verbose assistant replies, which D1 did not address.
4. **Potentially the auto-memory rules block and the superpowers SessionStart hook**, both of which D1.2 flagged as deferred. One or both may be reclaimable in the current Claude Code version — needs re-verification in Phase 1.

The diagnosis is not "slash commands are bloated." The diagnosis is a missing architectural pattern: **skills are loaded whole-or-not-at-all, when progressive disclosure at the skill level would let the common case ship in <500 tokens and only pull edge-case context when a specific predicate fires.**

## Principles

### P1. Progressive disclosure applies at the skill level, not just the Tier level.

ADR-002 introduced tiered context loading for catchup (Tier 1 strictly bounded, Tier 2 via subagent, Tier 3 normal work). The same logic generalizes: every slash command has a "common case" decision surface and an "edge case" deep-dive. The common case is the always-loaded lite file; the deep-dive is a separate `.full.md` loaded only when a discrete predicate in the lite file fires.

### P2. Load triggers are discrete predicates, not subjective states.

"If confused, load full" is banned. "If `mode == 'dirty-recovery'`, load `catchup.full.md`" is required. This is the load-bearing rule — without it, the LLM defaults to loading the full file "just in case" and compression is defeated. Phase 2 must have a structural test that verifies every `## Load full` section contains only predicates the LLM can evaluate from visible state.

### P3. LLM-audience docs use structured text, not pictures.

Graphviz `digraph`, ASCII flowcharts, and box-drawing characters are anti-efficient for LLM parsing. A `digraph` block with 10 edges is ~200 tokens; the equivalent numbered conditional list is ~40 tokens and lexically cleaner for the model to follow. Files in `commands/claude-code/` are read by the LLM on invocation, not browsed by humans — optimize for that audience.

### P4. Output growth is a CLAUDE.md concern, not a plugin concern.

Per-turn output growth can be controlled with one line in CLAUDE.md ("default to terse replies, no preamble, no trailing summary") at a cost of ~30 tokens. Plugins like `caveman` that inject terseness via system prompt add risk without unique benefit: they don't compress reasoning tokens, conflict with extended thinking (which generates English reasoning before terse output, net-increasing cost), and introduce distribution mismatch. The cheap inline rule is strictly dominant.

### P5. The hard floor is the hard floor.

System prompt (6.3k) + System tools (10.4k) + superpowers SessionStart injection (1.1k, D1.2-deferred) + minimal message overhead = ~19.3k. Below this requires modifying Claude Code itself, which is out of scope. This slice targets everything above the floor.

## Progressive disclosure pattern

Two-file pair per slash command in `commands/claude-code/`:

### Lite file — `<name>.md`

**Hard cap: 500 tokens.** Always loaded on skill invocation. Structure is fixed:

```markdown
# /<name>

<One-line purpose>

## Rules
1. <imperative rule>
2. <imperative rule>
3. <imperative rule>
...

## Load full
Read `commands/claude-code/<name>.full.md` if:
- <discrete predicate>
- <discrete predicate>
```

Banned from lite files: Graphviz blocks, ASCII diagrams, box-drawing characters, prose rationale, philosophy, ADR links in the body (frontmatter pointers OK), examples longer than one line, "why" explanations.

### Full file — `<name>.full.md`

Loaded only when a lite-file trigger fires. No token cap but aggressive prose compression still applies. Contains:

- Rationale, philosophical grounding, ADR links
- Edge-case handling (Mode D dirty-recovery, rare states)
- Longer examples
- Operator context and historical notes
- Everything that currently bloats the lite file

The split is semantic: lite = "what to do", full = "why, and edge cases".

### Convention notes

- Lite file must end with the `## Load full` section. Phase 2 asserts this structurally.
- Every predicate in `## Load full` must point at a real `.full.md` file that exists. Phase 2 asserts this structurally.
- Lite files are the version-controlled canonical form; full files are siblings, not generated.
- Not every command needs a full file. Small commands (`status.md` at 2.2 KB) may land under the 500-tok cap without splitting — in that case only the lite file exists, and the `## Load full` section says "no full form, this command is simple enough."
- This pattern is NOT being promoted to an ADR in this slice. Deferred to SLICE-005+ if the pattern holds for 2+ slices. Captured in SLICE-003 intent and in the slice's completion report as a graduation candidate.

## Invariants

### INV-002 (existing, from SLICE-002) — preserved

Machine-checked by `tests/unit/test_context_discipline_protocol.py` V1–V7. These tests MUST pass unchanged after compression. This is the "we didn't break context discipline while shrinking" gate.

### INV-003 (new) — session-start token budget

**Statement:** Session-start turn-1 total context (system + tools + memory + skills + first-turn injections) MUST be ≤ 22,000 tokens on a clean "hi" message in cairn. Aspirational target: ≤20,000.

**Rationale:** 22k is the unfixable floor (~19.3k) plus ~2.7k headroom for CC-controlled reminder noise we don't govern. 20k assumes Phase 1 reclaims D1.2 (superpowers SessionStart hook) or the auto-memory rules block. The slice succeeds at ≤22k even if neither is reclaimable.

**Measurement:** `tests/unit/test_context_budget.py` reads `~/.claude/projects/.../-*.jsonl` for the most recent session, extracts `input_tokens + cache_creation_input_tokens + cache_read_input_tokens` from the first usage record, asserts ≤ 22000. Test is operator-gated — requires a fresh "hi" session to exist before it runs. The measurement script at `2026-04-11-d1-floor-cuts-plan.md:28–47` is the starting point, productionized with stdlib pytest assertions.

**Record CC version in test output** so future failures on version bumps get diagnosed (not reverted). Pattern:

```python
def test_session_start_budget_hi_message():
    session_file = _most_recent_session_jsonl()
    turn1 = _first_usage_record(session_file)
    cc_version = _detect_cc_version()
    total = turn1['input_tokens'] + turn1['cache_creation_input_tokens'] + turn1['cache_read_input_tokens']
    assert total <= 22_000, f"turn-1 = {total} tokens (CC {cc_version}, session {session_file})"
```

### INV-003 structural tests (new)

Alongside the token-budget runtime test, Phase 2 adds structural tests that run in CI without a session:

- **S1**: every file in `commands/claude-code/*.md` (non-`.full.md`) ≤ 500 tokens
- **S2**: every lite file contains a `## Load full` section
- **S3**: every predicate under `## Load full` points at a `.full.md` file that exists OR the section explicitly says "no full form"
- **S4**: no lite file contains `digraph`, `\bdot\s*{`, or box-drawing characters (U+2500–U+257F)
- **S5**: lite files contain no H3 (`###`) or deeper headers (enforces flat rule lists)

These are mechanical checks — they don't validate that the content is correct, only that it follows the pattern. INV-003 runtime test validates the outcome; S1–S5 validate the pattern.

## Target surface area

### Slash commands to compress (Phase 3 order, biggest win first)

| File | Current size | Lite target | Full file expected? |
|---|---|---|---|
| `start-slice.md` | 14.7 KB | ≤500 tok | yes |
| `catchup.md` | 9.5 KB | ≤500 tok | yes (keep Tier/Mode prose in full) |
| `decision.md` | 8.3 KB | ≤500 tok | yes |
| `handoff.md` | 5.7 KB | ≤500 tok | yes |
| `integration-sweep.md` | 5.1 KB | ≤500 tok | yes |
| `new-adr.md` | 3.6 KB | ≤500 tok | probably not |
| `refresh-architecture.md` | 3.0 KB | ≤500 tok | probably not |
| `status.md` | 2.2 KB | ≤500 tok | no (already small) |

### Other changes

- `CLAUDE.md` — add one line for terseness rule: *"Default to terse replies. No preamble, no trailing summary. One sentence between tool calls unless the work demands more."* ~30 token cost. No other CLAUDE.md edits.
- `.claude/handoff.md` — remove stale "SLICE-003-precursor Phase 1 intent already committed at 7ff5d74" line (slice is actually complete)
- `sweep.yaml` — bump `current-slice-number` from 3 → 4 at slice open (skipping SLICE-003 for self-learn, using SLICE-004 for THIS slice — see numbering note below)

**Numbering note:** Despite the design doc header saying "Slice: SLICE-003", the user decision in brainstorming was **SLICE-003 = this slice (context compression)** and **SLICE-004 = self-learn flow** (previously referenced as "Slice #3" in D1 plan docs). The D1 plan's forward-reference to "Slice #3 self-learn flow" becomes "Slice #4 self-learn flow." No file moves or renames — just a slot renumbering, documented in SLICE-003's intent and this design doc.

### Phase 1 investigations (may reclaim more)

- **D1.2 re-verification.** Re-grep the current Claude Code binary (at whatever version is installed, not 2.1.101) for `disabledHooks`, `disableHooks`, `disablePlugins`, `pluginHookOverrides`, `suppressHooks`, and any new keys discovered via `strings` inspection. Check the superpowers upstream repo (GitHub) for any opt-out support shipped since 2026-04-11. If either reclaims the ~1.1k tokens, fold into the slice envelope.
- **Auto-memory rules block.** Investigate whether the ~2–2.5k "Types of memory" instruction block in the CC system prompt is settings-editable (check `~/.claude/settings.json` keys, grep CC binary for `memory` / `autoMemory`). If editable, add to envelope. If not, document as a second-tier deferred item alongside D1.2.

Both investigations are time-boxed to Phase 1. If reclaimable, fold in. If not, record as deferred follow-ups and proceed with slash-command compression alone.

## Carried-forward items absorbed

This slice absorbs these per SLICE-002's sweep notes and I1 drift entry:

- **I1** — slice.yaml close-exception drift. This slice touches start-slice.md and ADR-002 territory, so it folds I1 in per `.claude/learning.md`.
- **M1** — `## Session Handoff Protocol (overview)` rename in `operational-reference.md`. This slice touches that territory.
- **L-001** — scar-class debt per 2026-04-12 sweep notes. Check and fold if applicable.
- **Stale handoff line** — SLICE-003-precursor "pending" phrasing in `.claude/handoff.md` is actually a stale artifact; the precursor is complete.

## Testing strategy

### Reuse from SLICE-002
`tests/unit/test_context_discipline_protocol.py` V1–V7 run unchanged. Any compression that breaks a V-test is reverted immediately — this is the hard gate.

### New in this slice
- `tests/unit/test_context_budget.py` — INV-003 runtime token-budget test
- `tests/unit/test_progressive_disclosure.py` — INV-003 structural tests S1–S5

### Phase 3 gate
After compressing each slash command, run the full test suite (V1–V7 + INV-003 + S1–S5). If any test fails, revert that single compression and investigate before moving to the next command. One-at-a-time compression (not batch) is load-bearing — SLICE-002 just stabilized these files, and batch regression would be hard to diagnose.

## Phase shape

**Phase 1 — Intent**
- Re-verify D1.2 against current CC binary (grep + version check)
- Check superpowers upstream for opt-out support
- Investigate auto-memory rules block editability
- Declare final envelope (slash commands in scope, CLAUDE.md addition, test files)
- Reconcile slice numbering: SLICE-003 = this work, SLICE-004 = self-learn (document in intent.md)
- Reconcile carried-forward items (I1, M1, L-001, stale handoff line)
- Trigger sweep per sweep.yaml cadence (last-sweep-at-slice=3, interval=1, current=3 → sweep due)
- No ADR-005 in this slice (deferred)

**Phase 2 — Validation (RED)**
- Write `tests/unit/test_context_budget.py` for INV-003 runtime
- Write `tests/unit/test_progressive_disclosure.py` for S1–S5 structural
- Verify V1–V7 still pass on unchanged files (regression baseline)
- All new tests start RED (no compression has landed yet)

**Phase 3 — Implementation (GREEN gate per file)**
- Compress `start-slice.md` → run full test suite → must be green → commit
- Compress `catchup.md` → run full test suite → must be green → commit
- Compress `decision.md` → ... → commit
- Compress `handoff.md` → ... → commit
- Compress `integration-sweep.md` → ... → commit
- Compress `new-adr.md` → ... → commit
- Compress `refresh-architecture.md` → ... → commit
- Compress `status.md` → ... → commit (may stay single-file if under cap)
- Add terseness line to CLAUDE.md → verify INV-003 still green → commit
- Fold I1, M1, L-001 edits (co-located with their relevant commands) → commit

**Phase 4 — Integration**
- Full V1–V7 + INV-003 + S1–S5 green
- Operator starts fresh "hi" session → `pytest tests/unit/test_context_budget.py` → pass
- Record delta against 27,314 D1 baseline in `docs/plans/measurements/2026-04-12-slice-003.txt`
- Run sweep
- Update `.claude/handoff.md` per SLICE-002's new handoff format

## Risks

1. **Re-opening SLICE-002 territory.** This slice rewrites the same files SLICE-002 just stabilized. V1–V7 as the hard gate; one-file-at-a-time compression; immediate revert on failure.
2. **Compressed lite files cause operator confusion.** Mitigation: lite files point at their .full.md explicitly in the `## Load full` section. Any operator can pull the full file if they need context.
3. **Progressive disclosure becomes an empty ritual.** If the LLM loads .full.md on every invocation anyway, the compression is defeated. Mitigation: S2–S5 enforce structural compliance; the training is "load full only when predicate fires." If the pattern fails behaviorally in practice, the lite/full split is abandoned in SLICE-004+ and the rollback is documented.
4. **INV-003 is observation-based, not deterministic.** A future CC version bump could blow the 22k ceiling with no cairn-side change. Mitigation: test output records CC version; version-bump failures get diagnosed, not reverted. Ceiling may be re-negotiated against a new floor.
5. **Phase 1 reclaims nothing from D1.2 or auto-memory.** Expected outcome: hit 22k cleanly, miss 20k. Acceptable — 22k is the hard assertion. If D1.2 re-verification finds something, that's a bonus.
6. **Slice numbering confusion across cairn's own doc trail.** D1 plan docs reference "Slice #3 self-learn flow." This slice takes SLICE-003. Mitigation: explicit numbering-note in this design doc + in SLICE-003 intent.md + in Phase 4 completion report. Future readers tracing from D1 plan docs will land here and see the re-slot.

## Success criteria

Slice is complete when:
- V1–V7 from SLICE-002 still pass
- INV-003 runtime test passes (≤22k on fresh "hi" session)
- S1–S5 structural tests pass
- All slash commands in `commands/claude-code/` are either ≤500 tokens (as lite files) or have a `<name>.full.md` sibling
- CLAUDE.md has the terseness rule
- Measurement recorded in `docs/plans/measurements/2026-04-12-slice-003.txt` with delta against D1 baseline (27,314)
- Carried-forward items (I1, M1, L-001, stale handoff line) resolved
- Sweep has run
- Handoff updated per SLICE-002 format

Aspirational (not required for success):
- Turn-1 budget ≤20k (requires D1.2 or auto-memory reclaim)
- Phase 1 D1.2 re-verification documents finding for future reference
