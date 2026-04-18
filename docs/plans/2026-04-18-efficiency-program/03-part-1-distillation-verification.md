# Part 1: Distillation + Verification Agents

**Date:** 2026-04-18
**Gates:** Part 0 ADR
**Estimated:** ~4 slices
**Ports to:** directly consumed by Part 2 skills + Part 4 maintenance

## Intent

Ship the agents that reduce main-session context load and catch issues earlier. These are "read-only" agents — they inform, they don't mutate. Low-risk path to proving the agent roster concept before investing in phase-role agents (Part 3).

## Agents

### A1 — `context-distiller`

**Role:** Generalize `/catchup` Tier 2 across all skills. Any time a skill needs to answer "what does X say about Y" from files, dispatch context-distiller with a bounded question + ≤5 file list.

**System prompt shape:**
```
You read the listed files and answer the specific question.
Return ≤200 words. Cite at most one file:line.
Do not summarize the repo.
Do not propose next steps.
If the answer isn't in the listed files, return "NOT FOUND in listed files" + the exact gap.
```

**Inputs:** `question` (string), `files` (list, ≤5), `context_preamble` (string, ≤100 words, optional).

**Return contract:** ≤200 words, markdown, one `file:line` reference max.

**Invoked by:** `/catchup` (Tier 2 Mode A), `/refresh-architecture` (for ADR reads), `/integration-sweep` (per-feature check), `/decision` (Phase 0 constraint harvest).

**Slice:** `part-1-s1-context-distiller`.

---

### A2 — `envelope-scout`

**Role:** At Phase 1 draft time, scan proposed envelope against the actual codebase + git log. Return list of "probably needed but not listed" + "listed but likely not touched" + "confirm as-is." Prevents envelope drift mid-slice.

**System prompt shape:**
```
You are given (1) a proposed envelope as a list of file paths, (2) the slice intent summary.
Your job is to check:
- For each listed file, does it exist? Has it been touched recently? Is it plausible it'll be modified given the intent?
- For each file NOT in the envelope but mentioned in the intent (by name or by topic), should it be added?
- For each file in the envelope that seems unrelated to the intent, flag for removal.

Return a table: file | action (keep / add / drop / confirm-suspicious) | one-line rationale.
Max 20 rows. No prose.
```

**Inputs:** `envelope` (list), `intent_summary` (string).

**Return contract:** Markdown table, ≤20 rows, no preamble.

**Invoked by:** `/start-slice` Phase 1 after intent.md draft is ready, before commit.

**Slice:** `part-1-s1-envelope-scout` (same slice as A1 — both are Tier 2 read-only; low cost to bundle).

---

### A3 — `feature-graph-explainer`

**Role:** Answer "what slices are ready to start?" and "what's the dep graph across features?" without the human reading all `.claude/features/*.yaml`.

**System prompt shape:**
```
You read all .claude/features/*.yaml files.
Output:
- Section "Active features": one line per feature (name, status, count of slices in each phase).
- Section "Unblocked slices": list slices where `after:` deps are all satisfied.
- Section "Critical path": if a chain of ≥3 slices is serially blocked, name the first.
- Section "Ambiguities": any feature with inconsistent or missing fields.

Return ≤200 words total. No DOT diagrams in v0.
```

**Inputs:** None (reads `.claude/features/`).

**Return contract:** Four sections, ≤200 words total.

**Invoked by:** `/status` (delegates to this when >1 feature is active), `/integration-sweep` Step 1, human via `/features` shorthand if we add one.

**Slice:** `part-1-s2-feature-graph-explainer`.

---

### A4 — `invariant-preflight`

**Role:** Pre-commit check: given the staged diff, verify it doesn't violate any invariant declared in `docs/ARCHITECTURE.md` or referenced ADRs.

**System prompt shape:**
```
You are given the staged diff and the list of invariants from docs/ARCHITECTURE.md.
For each invariant:
- Does the diff touch files/patterns this invariant governs?
- If yes, does the change preserve or violate the invariant?

Return:
- PASS: no invariants violated.
- FAIL: list each violated invariant + one-line explanation + file:line citation.

≤200 words.
```

**Inputs:** `diff` (string, or Bash `git diff --cached`), `invariants_source` (`docs/ARCHITECTURE.md` or the registry from Part 5).

**Return contract:** PASS/FAIL verdict with violations listed.

**Invoked by:** pre-commit hook (optional), `/integration-sweep` per-slice check, `/start-slice` Phase 4.

**Slice:** `part-1-s3-invariant-preflight`.

**Dependency:** Ideally runs after Part 5 S2 (invariant registry) so invariants are structured data. Pre-registry it parses `docs/ARCHITECTURE.md` which is fine but less robust.

---

### A5 — `sweep-preflight`

**Role:** Before `/integration-sweep`, scan for likely issues. Go/no-go gate. If pre-flight fails, the human fixes first; full sweep isn't burned.

**System prompt shape:**
```
Run the following read-only checks:
1. git status — any unstaged work?
2. git log — any commits since last sweep that are suspicious (non-phase, non-handoff, non-adr)?
3. .claude/current-slice — does it exist? If yes, is a slice mid-flight?
4. .claude/features/ — any feature with inconsistent slice states?
5. docs/adr/index.md — regenerable, or stale?

Return:
- SWEEP-READY: all good, proceed.
- FIX-FIRST: list issues with file:line citations.

≤200 words.
```

**Inputs:** None (runs `git` + reads structured files).

**Return contract:** SWEEP-READY or FIX-FIRST.

**Invoked by:** `/integration-sweep` Step 1 (new pre-flight).

**Slice:** `part-1-s3-sweep-preflight` (bundle with A4).

---

### A6 — `doc-drift-detector`

**Role:** Given a diff, cross-reference against ADRs, ARCHITECTURE.md, CLAUDE.md, relevant operational-reference.md sections, docstrings. Flag where docs are stale.

**System prompt shape:**
```
You are given the diff of a recent change.
Enumerate:
- Which ADRs does the diff reference (by ID)? Do those ADRs still accurately describe the changed code?
- docs/ARCHITECTURE.md — any section describing invariants touched?
- CLAUDE.md — any safety-critical rule or pointer changed?
- docs/operational-reference.md — any phase-protocol described that the diff invalidates?
- Module/function docstrings — stale?

Return table: doc | file:line | stale? (yes/no/uncertain) | one-line rationale.
Max 15 rows.
```

**Inputs:** `diff` (string).

**Return contract:** Table, ≤15 rows.

**Invoked by:** `/integration-sweep` (optional), `/handoff` phase 4 only.

**Slice:** `part-1-s4-doc-drift`.

---

### A7 — `skill-lint`

**Role:** Read `commands/claude-code/*.md` + `.full.md` files, flag where prose-specified side effects could be code (L-005-class risks). One-time audit with periodic re-runs.

**System prompt shape:**
```
Read the listed skill files. For each skill:
- Identify sentences that say "also", "then", "make sure to", "finally" as side-effect prescriptions.
- For each: is the side-effect mechanically expressible (file write, status flip, command exec) or does it require judgment?
- Mechanical → candidate for code-not-prose refactor.
- Judgment → prose is correct.

Return table: skill | section | prescription | classification (mechanical/judgment) | refactor hint.
```

**Inputs:** `skills` (list of file paths, default: all under `commands/claude-code/`).

**Return contract:** Table per skill.

**Invoked by:** initially one-shot during Part 2 planning; later periodic (quarterly).

**Slice:** `part-1-s4-skill-lint` (bundle with A6).

## Slice breakdown

- **S1** — A1 (`context-distiller`) + A2 (`envelope-scout`). Both pure Tier 2 read. Share infrastructure (agent definition, invocation harness).
- **S2** — A3 (`feature-graph-explainer`). Plus integration into `/status` (Part -1 #7 already touches `/status`; coordinate).
- **S3** — A4 (`invariant-preflight`) + A5 (`sweep-preflight`). Both are pre-commit/pre-sweep gates. Share patterns.
- **S4** — A6 (`doc-drift-detector`) + A7 (`skill-lint`). Both are cross-ref audits. Share patterns.

## Cross-cutting concerns

1. **Agent definition location.** `.claude/agents/<name>.md` follows Claude Code's native convention. Check Part 0 ADR decision; if cairn wants a framework-agnostic location, pick now.
2. **System prompt authoring discipline.** Every agent's prompt is ≤200 words; committed; reviewed like code. Not edited casually.
3. **Timeout budgets per P5.** Default 10 min soft, 30 min hard. Override in agent frontmatter if justified.
4. **Invocation harness.** Skills invoke via Claude Code's `Agent` tool with `subagent_type: <name>`. No shell wrappers.

## Out of scope for Part 1

- Agents that mutate code (those are Part 3 phase-role agents).
- Agents that run async / scheduled (Part 4 maintenance cluster).
- Changes to skills themselves (those are Part 2).

## Success criteria

1. `/catchup` Tier 2 dispatches use `context-distiller` instead of ad-hoc subagent briefings.
2. `/start-slice` Phase 1 routinely calls `envelope-scout` and the scout catches ≥1 envelope drift per average slice.
3. `/status` with >1 active feature shows a structured graph output, not a flat list.
4. `sweep-preflight` catches ≥75% of sweep-abortable issues before sweep runs.
5. A one-time `skill-lint` pass identifies ≥3 L-005-class prescriptions across current skills. (Those become Part 2 inputs.)
