# Cairn Identity ADR — /decision arc context

Shared brief for all subagents in this arc. Read this; do not re-derive from chat.

## Decision
Author cairn's identity ADR. Adjudicate four load-bearing decisions:
1. **Identity claim positioning** — STARTING POSITION (operator-set): **complement**. "Goal-commitment vs agent-reactivity" rides alongside the preserved medium-scale-cliff thesis as a co-equal value — additive, not a replacement. Arc may push back with evidence.
2. **Methodology replacement** — adopt the **charter cycle** (charter-commit → blind build → blind verify), superseding the 4-phase TDD machinery.
3. **Mechanism deferral** — ship NO semantic intent↔ADR alignment mechanism; N≥3 misalignment trigger (per `schema-amendment-threshold`) as the empirical test.
4. **Supersession** — retire `slice-intent-contract` + `identity-and-scope-deferral`.

## Arc posture (operator-set): HARDEN + ATTACK
Charter cycle is the leading proposal — NOT re-derived from scratch, NOT rubber-stamped. Mandatory adversarial stress-test on its load-bearing claims. Keep two live Phase-2 comparators:
- **(B) Lightened 4-phase** — keep the phase structure, cut ceremony.
- **(C) Infrastructure-only, no bundled preset** — cairn ships infra + intent primitive; methodology is BYO.

## Attack targets (load-bearing claims to prosecute BEFORE synthesis)
- **C5–C8 `verified: null`** — the cross-slice substrate (role_guard, append-only ADR, validator, pointer-handoff) is cairn's CLAIMED durable identity, yet `landscape.md` shows C5–C8 were never skeptic-verified, only self-rated "high." Lowest-rigor verdicts carry the most weight.
- **C1 unmeasured** — the medium-scale cliff is `firmness:provisional`, "intuition not empirical," never observed in cairn itself. The whole identity rests on an unmeasured cliff.
- **C3 now-redundant** — "subagents structurally cannot re-pollute the parent" is the verdict the charter cycle's entire blind-worker execution layer rests on. The one verdict the research verifier couldn't refute — re-verify it holds under the charter cycle's specific orchestration (return-channel accumulation across a multi-phase pipeline driven by one lead).

## Phase-0 inputs (already committed at bf2d05a / da6eb9f)
- `docs/plans/2026-05-22-cairn-identity-direction.md` — brainstorm direction: operator signals, supersession map, follow-up arcs.
- `.claude/skill-runs/cairn-identity-brainstorm-2026-05-22/landscape.md` — research arc A; the C1–C8 verdicts.
- `.claude/skill-runs/cairn-identity-brainstorm-2026-05-22/brainstorm-1-charter-cycle.md` — the charter-cycle design (brainstorm #2 folded in).
- `.claude/skill-runs/cairn-identity-brainstorm-2026-05-22/00-rejected-adaptive-pivot-exploration.md` — input archaeology (rejected adaptive-reliability pivot).

## Charter cycle — open questions for this arc (brainstorm-1 §10)
1. **Charter form** — file vs frontmatter vs native-memory; default = committed file per cycle.
2. **AGENT_ROLE disposition** — native per-subagent `tools`/`permissionMode` scoping vs fix the env-var wiring vs both. (role_guard.py:137 reads AGENT_ROLE but dispatch never injects it — currently dead code; only the operator envelope enforces.)
3. **Test-first** — default-on vs droppable.
4. **Re-injection hook mechanics** — which event, what it injects, compaction interaction.
5. **Multiple concurrent cycles** vs `parallelism-v1` (worktree-per-charter).
6. **Charter ↔ pointer-handoff overlap.**

## Arc artifacts (this directory)
- `01-constraint-envelope.md` — Phase 0 harvest.
- `02-journey-trace.md` — Phase 0.5 charter-cycle walk + mechanism-gap map.
- `03-premortem.md` — Phase 1 failure scenarios.
- `04-approach-*.md` — Phase 2 enumeration (one per approach A/B/C).
- `05-stress-test.md` — Phase 3 adversarial.
- `06-synthesis.md` — pre-ADR synthesis for operator confirmation.
