# Part 0: ADR — Principles for the Efficiency Program

**Date:** 2026-04-18
**Type:** One ADR
**Gates:** Parts 1, 2, 3, 4, 5 (principles file)
**Firmness target:** `firm` (Phase 5 Independent Verification required)

## Intent

Before any agent is authored or skill refactored, lock the principles that govern them. Writing agents without these principles risks encoding them in code (wrong artifact) and re-deciding them per slice (drift). One ADR, then everything downstream applies it.

## Principles to codify

### P1 — Tier model applies to every skill, not just `/catchup`

The Tier 1 / Tier 2 / Tier 3 model (`catchup.full.md:48–88`) is the canonical context discipline. Extend it structurally to every skill that does context-heavy reads: `/integration-sweep`, `/refresh-architecture`, `/decision`, `/start-slice` Phase 1 exploration.

**Concrete commitments:**
- Every skill declares its Tier 1 read set in frontmatter (explicit, bounded, ≤5 files).
- Any context load beyond Tier 1 dispatches a subagent with a bounded-return contract.
- Tier 2 subagent return cap: ≤200 words, ≤1 file:line citation, no repo summaries, no prose, no next-step advice. Shape matches `catchup.full.md:71–88` verbatim.
- No skill may escalate to Tier 2 "to be thorough" or "to confirm." Admission criteria must be explicit.

### P2 — Phase roles are named agents, not skill prose

Phase 1/2/3/4 roles are encoded as named agents with system prompts and tool restrictions, not described in skill markdown.

**Concrete commitments:**
- Named agent files live at `.claude/agents/<name>.md` (or `cairn_agents/` if we want project-wide reuse separate from the Claude-Code-native `.claude/agents/` path).
- System prompts include the role name, primary anti-behavior, allowed tools, forbidden tool patterns.
- Phase Skill Guide (`docs/operational-reference.md`) becomes the source-of-truth table; agent files are generated from it.
- Skills that drive phases (`/start-slice`) invoke the named agent; they do not re-describe the role in prose.
- Pre-F6: agents are used as subagents for distillation + Phase 3/4 fan-out (Option B per brainstorm).
- Post-F6: phase-1/2/3/4 agents become the system-prompt layer of `claude -p` worker spawns (Option A per brainstorm; matches F6 design §3.6 worker hook config delivery).

### P3 — Subagents return bounded reports; they do NOT communicate with each other

Subagent-to-subagent communication would reinvent F6 at a smaller scale (protocol, coordinator, backpressure). Explicitly avoid.

**Concrete commitments:**
- Subagent outputs are structured (prescribed fields), bounded (≤200 words default), and flow to the main session only.
- Main session is the only coordinator; it receives N subagent reports, reconciles, and decides.
- If work genuinely requires coordination across parallel units (not just independence), it stays serial OR becomes a coupling-cluster (see P4).

### P4 — Coupling clusters at Phase 2

Phase 2 produces, alongside tests, a **coupling-cluster partition** of the envelope. Files tightly coupled (shared interface, caller/callee, test-coupling) form a cluster; independent files form singleton clusters.

**Concrete commitments:**
- `.claude/current-slice/validation/coupling-clusters.yaml` — Phase 2 output alongside tests + approach.md.
- Format: list of clusters, each a list of file paths + rationale.
- Phase 3 dispatches one subagent (or one `phase-3-implementer` worker, post-F6) per cluster. Parallelism is per-cluster, not per-file.
- If no clean clustering exists (everything coupled), the whole envelope is one cluster and Phase 3 is serial. This is fine and expected for some slices.
- Detection of coupling is the phase-2-skeptic's judgment call, informed by the envelope and read from Phase 1's intent.md. Not a mechanical tool.

### P5 — Stall visibility contracts

The dogfood 28-min subagent stall (§8.1 #3) established that silent subagent invocations are unacceptable.

**Concrete commitments:**
- Every subagent invocation carries a soft timeout (default: 10 min; configurable per invocation).
- On soft-timeout, main session forces a return: "what have you done so far, what's blocked, what's the next step?" — subagent returns bounded report, main session decides whether to extend.
- On hard-timeout (default: 30 min), main session aborts the subagent and surfaces the stall as a gate event.
- Post-F6: stall-visibility is automatic via the daemon's `SubagentStart`/`SubagentStop`/no-progress detection.
- Pre-F6: stall discipline lives in the invoking skill's prose; every `Agent(...)` call is paired with a timeout budget in the skill frontmatter.

### P6 — Policy files, not skill prose, for repeated rules

Permission policies (what prompts auto-approve), transition policies (when autonomous state changes fire), agent tool restrictions, subagent-dispatch rules — these are policy, not mechanism. Live in YAML, owned by ADR amendment.

**Concrete commitments:**
- `permission-policy.yaml` (from F6) ships early, in the form it will have post-F6.
- `agent-roster.yaml` declares the known agents, their roles, their allowed-tool patterns, their tier cap.
- `skill-tier.yaml` declares the Tier 1 read set per skill. Generated from skill frontmatter or authored directly.
- Any change to these files is an ADR amendment. Not a code edit.
- `scripts/validate_methodology.py` (Part 5) reads these YAMLs + skills + agents + ADRs and asserts cross-consistency.

## Agent roster (initial — Parts 1, 3, 4 implement)

| Name | Role | Tier cap | Allowed tools (illustrative) |
|---|---|---|---|
| `context-distiller` | General Tier 2 reads with ≤200-word return | N/A (itself Tier 2) | Read, Grep, Glob |
| `envelope-scout` | Phase 1: scan proposed envelope for drift | N/A | Read, Grep, Glob |
| `feature-graph-explainer` | Explain `.claude/features/*.yaml` dep graph | N/A | Read |
| `invariant-preflight` | Pre-commit check against invariants | N/A | Read, Bash (read-only) |
| `sweep-preflight` | Before `/integration-sweep` gate | N/A | Read, Bash (read-only) |
| `doc-drift-detector` | Cross-ref code vs docs | N/A | Read, Grep |
| `skill-lint` | Find prose-specified side-effects in skills | N/A | Read, Grep |
| `phase-1-writer` | Scope + intent authoring | Tier 1 (ADRs + architecture only) | Read, Write (intent.md only) |
| `phase-2-skeptic` | Test authoring | Tier 1 + phase-2 declared inputs | Read, Write (tests/ only) |
| `phase-3-implementer` | Code to tests | Tier 1 + envelope | Read, Edit, Write (envelope-only) |
| `phase-4-integrator` | Integration + sweep | Tier 1 + full slice | Read, Edit, Write, Bash |
| `adr-author` | ADR body drafting | Tier 1 + ADR corpus | Read, Write (new ADR paths only) |
| `adr-drift-auditor` | ADR corpus audit | N/A | Read, Grep |
| `adr-impact-classifier` | New ADR → affected slices | N/A | Read, Grep |
| `lesson-extractor` | Propose lessons.md additions | N/A | Read |
| `merge-conflict-specialist` | Cairn-pipeline-aware merges | N/A | Read, Edit, Bash (git) |
| `cross-repo-awareness` | Downstream consumer usage check | N/A | Read, Grep (cross-repo), Bash |
| `dogfood-interpreter` | Run + interpret dogfood_evaluate.py | N/A | Read, Bash |

## Out of scope for this ADR

- Specific system prompts per agent (Parts 1/3/4 draft these).
- Skill refactor plans (Part 2).
- Telemetry schema (Part 5 S1).
- Multi-repo slice protocol (Part 5 S5).

## Phase 5 Independent Verification checklist

When this ADR reaches Phase 5, the verifier must independently answer:

1. Is the Tier model extension to all skills (P1) actually implementable, or does it hide admission-criteria ambiguity that will drift?
2. Does P2 (named agents for phases) conflict with Feature 6's worker-spawn model, or does it compose cleanly?
3. Is P3 (no subagent-to-subagent comms) too strict? Any real-world Phase 3 scenarios where it forces unnecessary serialization?
4. Is P4 (coupling clusters) mechanically detectable, or will phase-2-skeptics judgment-call it inconsistently?
5. P5 timeout defaults (10 min soft, 30 min hard) — empirically grounded or guessed?
6. P6 assumes YAML policies are ADR-amendable without code changes. Is there a case where the daemon needs a code path that YAML can't express?
