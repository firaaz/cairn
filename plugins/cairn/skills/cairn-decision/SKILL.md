---
name: cairn-decision
description: Run Cairn's architectural decision protocol in Codex before writing an ADR.
---

# Cairn Decision

Codex port of `/decision <question>`. Use it for decisions that become ADRs: invariants, boundaries, data ownership, module structure, or downstream assumptions.

## Protocol

1. Constraint harvest: read `docs/ARCHITECTURE.md`, `docs/adr/index.md`, relevant ADRs, and `docs/lessons.md`. Produce a constraint envelope with citations.
2. User-journey trace: walk the workflow end-to-end and identify every session, artifact, and state-transition mechanism.
3. Pre-mortem before solutions: write at least three failure scenarios covering technical, scale, and integration failures.
4. Forced enumeration: compare at least three viable approaches using evidence from files or docs.
5. Adversarial stress test: search for disconfirming evidence, steel-man the runner-up, and audit assumptions as verified or believed.
6. Decision record: use `cairn-new-adr` to write the ADR with context, decision, consequences, alternatives, and risk register.
7. Independent verification for firm decisions: use a fresh context with only the question, constraints, architecture, and relevant ADRs.
8. Propagation: refresh architecture, check in-progress intents, update superseded ADR frontmatter when needed, and record lessons.

Read `references/decision.full.md` for the full comparison table, evidence rules, and firm-decision verification protocol.
