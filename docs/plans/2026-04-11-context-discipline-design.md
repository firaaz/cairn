# Context Discipline — Design

Date: 2026-04-11
Status: validated design, ready for slice sequencing
Author: session-brainstorming with user

## Problem

Measured across 10 recent cairn and `complex-rag-analysis` sessions, every session starts at ~30,000 tokens on turn 1. Typical sessions reach 45–75k by turn 20 and peak at 100–170k before the user runs `/clear`. The "sweet spot" for model quality is ~30–40k total, and cairn sessions exceed that by turn 5 in nearly every case.

Breakdown of turn-1 context:

- **~16.6k stable** — core CLI system prompt + baseline tool schemas. Cached across sessions, not addressable without patching the Claude Code binary.
- **~14k dynamic per-session** — CLAUDE.md, skill list metadata, `superpowers` SessionStart hook injection, MCP instructions, deferred tools, git status, environment.

Largest addressable contributors on turn 1:
- `superpowers` SessionStart hook injecting the full `using-superpowers` SKILL.md: ~1,140 tokens
- Cairn `CLAUDE.md` as a 7.7 KB narrative instead of a cheat sheet: ~1,935 tokens
- Skill list from all enabled plugins: ~1,265 tokens

After turn 1 the situation degrades fast. `/catchup` in cairn today loads:
- `.claude/handoff.md` (3,245 tokens — narrative recap with "What This Session Was About", "Accomplished", "Self-check", "Surprises or discoveries")
- `.claude/current-slice/handoff-phase-3.md` (2,010 tokens)
- `.claude/current-slice/intent.md` (2,535 tokens)
- Full source files `validate_architecture.py` (2,600) and `test_validate_architecture.py` (3,085)
- `CHANGELOG.md`, `ARCHITECTURE.md`, the catchup skill text, the orientation summary

Total `/catchup` injection: **~16,700 tokens added on top of the 30k baseline**. A freshly-oriented session sits at ~47k before the user types anything.

**The diagnosis is not "startup is bloated."** The diagnosis is a design philosophy mismatch: handoffs carry narrative payloads, catchup eagerly reads every file it might need, phase-bridge notes accumulate across slice boundaries, and main-context file reads are used where subagent delegation would cost 100× less. The slice pipeline — which exists precisely to enforce context isolation between cognitive roles — is being undermined by artifacts that smuggle mental state across role boundaries.

## Principles

### P1. Context is a budget; the slice pipeline is the budget-management strategy.

The four-phase pipeline exists because context isolation is expensive by default and cheap when phase boundaries are clean. Sessions that grow past ~60k tokens are a protocol-failure signal — the slice was too big or a phase leaked reasoning. The fix is re-scoping, not summarization. `/compact` remains available as a CLI feature; out of scope for this design to instrument it, but note that regular reliance on it is a signal the protocol is misbehaving.

### P2. Progressive disclosure is semi-deterministic.

Tier boundaries are fixed by the protocol. Admission criteria for crossing a tier are written tightly enough that the LLM can apply them defensibly. The LLM retains discretion at the margins, but the criteria — documented verbatim in `commands/claude-code/catchup.md` — keep that discretion bounded. This requires careful prompt engineering of the catchup skill document.

### P3. Handoff = pointer, not payload. Subagents = report, not transcript.

Every persistent artifact (handoff.md, phase-bridge notes, catchup output) is a pointer with annotations, not a narrative. The main agent uses those pointers to dispatch subagents. Subagents are free to think, read, and reason internally without bound — the contract is about the *return value*: a bounded, structured report, not a transcript of exploration. The Agent tool already enforces this structurally (only the final message returns to main context); this design enforces it via prompt-template discipline so subagents return synthesized reports rather than raw dumps.

### P4. Handoffs are team-to-team interfaces.

A handoff is a contract between two "teams" — two sessions that do not share a mental model. This is the practical meaning of the `soft agent split` commitment in `docs/vision.md`. If handoffs carry reflective prose, they smuggle mental state across the role boundary, and the role-reset property collapses. Handoffs must be in an imperative/declarative voice: state, next action, pointers. Not "I wanted to…", not "Surprises or discoveries…", not "Self-check". Those belong in commit messages, PR bodies, `docs/lessons.md`, or ADRs.

## Handoff format

Target: **150–400 tokens**. Imperative/declarative voice only.

```markdown
---
slice: <SLICE-id or "none">
phase: <1-intent | 2-validation | 3-implementation | 4-integration | complete | n/a>
branch: <branch-name>
as-of: <YYYY-MM-DD commit-sha>
---

## State
<1–2 present-tense sentences describing current state. No history.>

## Next
<One imperative. One line. Specific.>

## Blocked / Pending
- <short item> → <where to look>
<Max 5 lines. Each is a one-liner + a pointer. No explanation of why.>

## Pointers
- `path/to/file.md` — what's there + when to read it
- `.claude/current-slice/intent.md` — slice envelope; read only if re-entering a phase
```

### Banned from handoff

| Section found in old handoffs | Where it actually belongs |
|---|---|
| "What this session was about" | Commit message |
| "What was accomplished" | `git log` |
| "Surprises or discoveries" | `docs/lessons.md` or a new ADR |
| "Self-check" | Nowhere — personal reflection, delete |
| Narrative paragraphs of reasoning | PR description or an ADR |
| Test run output with pass/fail tallies | Commit message or phase gate record |

The old cairn handoff.md was ~3,500 tokens; of that, roughly 150 tokens were actual handoff content. The rewrite is not information loss — it is relocation to the right artifact.

## Catchup protocol — three tiers

### Tier 1 — always runs, ~400–800 tokens into main context

Read only:

- `.claude/handoff.md` (new pointer format)
- `.claude/current-slice/slice.yaml` (if exists)
- `.claude/sweep.yaml` (if exists)
- `git log --oneline -5`
- `git status --short`

Produce the orientation summary. **Stop.** No additional file reads without explicit Tier 2 admission.

### Tier 2 — conditional, dispatched through a subagent, ~200 tokens back to main context regardless of underlying file size

Admission criteria, written verbatim into `commands/claude-code/catchup.md` so the LLM applies them deterministically:

```
DISPATCH Tier 2 subagent if and only if:
  1. User asked a specific factual question that Tier 1 data did not answer, OR
  2. User directed entry into a specific pipeline phase and the handoff pointers
     explicitly list files for that phase, OR
  3. You are about to take an action that requires verifying the current state of
     a specific file, AND that file is named in the handoff pointers.

DO NOT DISPATCH Tier 2 if:
  - You are orienting "just in case"
  - Tier 1 data sufficed to answer the user
  - The user has not given you a concrete direction
  - You want to "be thorough"
```

### Tier 3 — work begins, unbounded

When the user gives a direct imperative ("start phase 3", "fix the bug in X.py", "refactor Y"), the agent is no longer doing catchup — it is doing work. Normal file reading into main context is appropriate here because the files are about to be modified. This is not "Tier 3 of catchup"; it is the end of catchup.

## Subagent contract template

Embedded in `commands/claude-code/catchup.md` and available for reuse by any skill dispatching orientation subagents.

```
Subagent type: Explore

Prompt:
  CONTEXT: <1 sentence — what's happening in the main conversation>
  QUESTION: <specific thing the main agent needs answered>
  FILES AVAILABLE: <explicit list of paths from handoff pointers — no globs>

  YOUR BEHAVIOR:
  - Think and explore internally as much as you need
  - Read beyond the file list if a chain of reasoning requires it
  - Do not be lazy in your investigation

  YOUR RETURN (hard format — max 200 words, no exceptions):
    STATE: <1–3 sentences of current state>
    OPEN: <bullet list, max 5 items, each ≤15 words>
    POINTERS: <paths main agent should read IF it decides to act; annotated>

  DO NOT return:
  - Your exploration process or reasoning chain
  - File contents verbatim
  - Test output, logs, or tool-call transcripts
  - Code snippets unless the main agent explicitly asked for a named function
```

## Phase archive on slice close

When a slice transitions to `status: complete` or `status: failed`:

1. Move `.claude/current-slice/handoff-phase-*.md` to `.claude/archive/<slice-id>/`.
2. Move `.claude/current-slice/intent.md`, `.claude/current-slice/slice.yaml`, and any `.claude/current-slice/{validation,implementation,integration}/*` artifacts to the same archive path.
3. Wipe `.claude/current-slice/` back to empty.
4. `/catchup` Tier 1 no longer reads archived files. They exist for post-mortem use, not for orientation.

This closes the loop: each new slice starts with a clean `.claude/current-slice/` and inherits nothing from prior slices. The archive path is kept out of Tier 1's read set, so archived content has zero token cost on future sessions.

## Self-learn at handoff — `learning.md` staging + 3× rule

### Flow

```
session end → /handoff → append candidate learnings to .claude/learning.md
                                       │
                                       ▼
                  (periodic, threshold-triggered)
                                       │
                                       ▼
          claude-md-management:revise-claude-md  (session-aware additive pass)
          claude-md-management:claude-md-improver (structural audit pass)
                                       │
                                       ▼
                     3× similarity filter applied
                                       │
                                       ▼
                User review → CLAUDE.md edit (≤400 tokens total)
                  (entries promoted are marked in learning.md but kept for history)
```

### `.claude/learning.md` conventions

- Append-only. Free-form entries at capture time. No size cap.
- Each entry has a date, session-id or commit-sha, a one-sentence claim, and an optional evidence pointer.
- Entries are never edited — only appended or marked `[promoted YYYY-MM-DD]` during promotion review.
- Lives at `.claude/learning.md` alongside `handoff.md` because it is session-captured staging data, not project documentation. Not in `docs/`.

### 3× rule

A learning is promoted from `learning.md` to `CLAUDE.md` **only if the same claim has surfaced in at least 3 independent sessions**. The Principle of Three applied to documentation: don't abstract until you see the pattern repeat.

Single- and double-occurrence claims stay in `learning.md` as "not yet load-bearing." This keeps `CLAUDE.md` tight and prevents single-session hot-takes from becoming project gospel.

Promotion review is **not** run at every handoff. It is threshold-triggered: when `learning.md` grows past a threshold (initial proposal: 20 entries or 2 KB, revisit after data), the next `/handoff` triggers the promotion cycle. Most handoffs append and exit.

### Why two skills, not one

- `claude-md-management:revise-claude-md` is session-aware — it pulls from the current session's conversation and proposes additions based on what was just learned.
- `claude-md-management:claude-md-improver` is structural — it audits `CLAUDE.md` against templates independent of any session, and proposes tightening or reorganization.

Running both at promotion review gives one additive pass and one pruning pass. If they disagree, the tighter recommendation wins — the hard constraint is CLAUDE.md stays ≤400 tokens.

## Startup floor cuts

Independent of the protocol changes. Reversible, low-risk, ships as a single bundled commit outside the slice pipeline.

| # | Change | Tokens saved | Reversibility |
|---|---|---|---|
| D1.1 | Trim cairn `CLAUDE.md` from ~7.7 KB → ~1.6 KB. Keep: canonical-path rule, hook dependencies, scope-guard prefix bug, symlink recursion hazard, ADR editorial rule. Move repo layout + commentary to `docs/operational-reference.md`. | ~1,500 | `git revert` |
| D1.2 | Disable the `superpowers` SessionStart hook injection for cairn. Options during writing-plans: (a) project settings override if supported, (b) wrapper hook that short-circuits on cairn, (c) document as unfixable. | ~1,100 (if (a) or (b) works) | Delete override |
| D1.3 | Move `context7`, `claude-md-management`, `commit-commands` from `~/.claude/settings.json` to per-project `.claude/settings.json` in projects that actually use them. Cairn needs `claude-md-management` for the self-learn flow; `context7` and `commit-commands` are discretionary. | ~100–800 | Re-enable globally |
| D1.4 | Keep `superpowers` project-scoped (already is in cairn). No action needed. | 0 | n/a |

Expected floor savings: **~2,700–3,400 tokens off turn 1**, depending on whether D1.2 finds a working override.

## Slice sequencing

### D1 — floor cuts (this week, no slice)

Single bundled commit. CLAUDE.md trim + settings.json reorganization + superpowers hook override attempt. Reversible. Verify savings against measurement baseline before proceeding.

### Slice #2 — `handoff-catchup-protocol-rewrite`

**Envelope**:

- `commands/claude-code/handoff.md` (rewrite)
- `commands/claude-code/catchup.md` (rewrite)
- `commands/claude-code/start-slice.md` (add phase archive step on slice-complete transition)
- New `templates/handoff.md`
- New `.claude/archive/` directory convention (documented, not a code change)
- New empty `.claude/learning.md` with a header
- `docs/operational-reference.md` (document the tier model)

**Delivers**:

- New pointer-format handoff
- Tier 1 / Tier 2 / Tier 3 catchup with admission criteria
- Phase archive on slice close
- Subagent contract template embedded in catchup.md
- `learning.md` staging ground convention

**Expected savings per catchup session**: ~10–18k tokens.

**Risk**: rewrites cairn's core protocol. This is the meta-dogfood case the slice pipeline was built for. Self-referential but correct.

### Slice #3 — `selflearn-at-handoff`

**Envelope**:

- `commands/claude-code/handoff.md` (extend with selflearn step)
- `docs/operational-reference.md` (document the 3× rule and promotion cadence)

**Delivers**:

- Handoff invokes `claude-md-management:revise-claude-md` and `claude-md-management:claude-md-improver` on threshold
- 3× rule wired into promotion logic
- `learning.md` append-only discipline enforced at handoff

**Why separate from Slice #2**: Slice #2 establishes the format and staging ground. Slice #3 wires the automation. Keeping them separate lets the new handoff format be verified in practice before adding selflearn overhead.

### Slice #4 (optional, deferred) — `catchup-subagent-hardening`

Only if data from Slices #2–3 shows the embedded subagent template is insufficient. May not be needed at all. Decide after measurement.

## Measurement

After each phase of rollout, measure turn-1 and turn-20 context on 3 fresh cairn sessions (same method as the baseline: read `~/.claude/projects/.../<session>.jsonl` and sum `input_tokens + cache_creation + cache_read` on the first assistant message and the 20th).

| Checkpoint | Turn 1 target | Post-catchup target | Notes |
|---|---|---|---|
| Baseline (today) | ~30,300 | ~47,000 | Measured |
| After D1 floor cuts | ~26,500–27,500 | ~43,000–44,000 | CLAUDE.md trim + hook override |
| After Slice #2 | ~26,500–27,500 | **~28,000–30,000** | Tiered catchup, pointer handoff |
| After Slice #3 | no regression | no regression | CLAUDE.md stays ≤400 tokens; learning.md accumulates |

If any measurement misses its target by >30%, stop and re-investigate before proceeding to the next phase.

## Open questions to resolve during implementation

1. **Does Claude Code 2.1.101 support per-project disabling of a plugin hook via `.claude/settings.json`?** If yes, D1.2 is a one-line change. If no, fall back to a wrapper hook or accept the ~1,100 tokens as unfixable.
2. **Where does `.claude/archive/` live relative to `.gitignore`?** Archived slices are post-mortem artifacts — probably worth keeping in git, but the archive directory may accumulate fast and warrant a separate retention policy. Decide during Slice #2 intent phase.
3. **Threshold for promotion review in Slice #3** — initial proposal is "20 entries or 2 KB in learning.md". Revisit after the first month of data.
4. **Does the 3× similarity detection need its own helper skill**, or is a natural-language pass in `revise-claude-md` sufficient? Decide based on how noisy the initial `learning.md` entries are.

## Non-goals

- **Cutting the ~16.6k stable baseline.** Not addressable from user space; would require CLI changes. Out of scope.
- **`/compact` instrumentation.** Explicitly out of scope for this design per session decision.
- **Rewriting the slice pipeline itself.** The four-phase structure is load-bearing and this design reinforces it, not replaces it.
- **Automatic pattern mining from `learning.md`.** The 3× rule is applied during promotion review by an LLM-based similarity pass, not by a batch job.
