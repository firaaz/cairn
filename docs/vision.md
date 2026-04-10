# Cairn — Vision

*Captured 2026-04-10 during session 13 of complex-rag-analysis. Carried forward as the spec that drives cairn's own slices toward v1.*

## What cairn is

A slice-based development methodology tool — a repository containing the protocols, checks, commands, and documentation for the 4-phase slice pipeline, the decision protocol, and the substrate validator. Developed solo until v1, then released to the author's team for broader adoption.

## Why the name

A cairn is a stack of stones marking a path on a long journey. Each slice adds a stone. The cairn is the cumulative substrate. Fresh sessions pause at waymarks. Discipline is cumulative.

## Six non-negotiable commitments for v1

These are the spec. They are NOT what v0 extraction built — they are what cairn builds on itself via slices run in this repo.

### 1. Agent-portable

Claude Code and Windsurf can each independently run the complete workflow. Protocols are plain markdown; checks are shell scripts; commands are thin per-agent wrappers. Adding a third agent later is a directory addition, not a rewrite.

### 2. Parallelism-native

The system assumes N active slices at any moment, not one. Slice state is branch-local and per-slice, never global. Hooks read from the current working tree's slice metadata. The "one active slice" mental model is a bug to fix, not a design.

### 3. Agent split is soft preference, not enforcement

Claude Code preferred for Decision protocol and Phase 2 (test writing) because of reasoning density. Windsurf preferred for Phase 3+ because execution is where Windsurf earns its cost. Documentation in AGENTS.md, not enforced by hooks.

### 4. Meta-dogfoodable from slice #1

Cairn uses itself to develop itself. No bootstrapping exception. If the methodology is too heavy to apply to its own development, that's a bug in the methodology, not a reason to skip it.

### 5. Phase shape is plastic through v1

The current 4-phase decomposition (Intent → Validation → Implementation → Integration) is not committed. The phase rethink is a first-class work item that runs through `/decision` and may produce 3, 4, or 5 phases with different names or boundaries. Phases are locked at v1, not before.

### 6. Explicit cognitive roles per phase

Every phase declares a named role (e.g., architect, skeptic, builder, auditor — exact names decided with the phase rethink). The role is in the protocol, printed by `/catchup`, written to `state.json`. Roles carry explicit anti-behaviors — "the architect does not write code, the skeptic does not propose fixes, the builder does not re-litigate the spec, the auditor does not rewrite." This gives role-reset something textual to latch onto beyond fresh sessions.

## Success criteria for declaring v1

### Mechanical (verifiable)

- Cairn repo exists with its own README, CHANGELOG, git history
- Protocols exist as plain markdown referenced by both agent command sets
- Shell scripts in `checks/` run identically under Claude Code and Windsurf
- At least one slice has run end-to-end on Claude Code alone
- At least one slice has run end-to-end on Windsurf alone
- At least one slice has run split mid-flight across both agents (cross-agent handoff validated)
- Two concurrent slices have completed on separate worktrees without interference (parallelism validated)
- Phase decomposition decision is final (one ADR resolving the rethink)
- Cairn has no references to RAG code

### Subjective

- Dogfood log shows declining bug/friction rate over the last 5 slices
- Mental model is stable (no major reframes in recent sessions)
- Written team-onboarding guide exists and reads shareable

## What cairn is NOT committing to

- Team adoption workflow
- Jira/Confluence integration
- Multi-agent automation beyond "runs on Claude Code and Windsurf"
- Distribution mechanism beyond git submodule
- Cross-family verification automation (stays manual at solo scale)
- A specific phase count
