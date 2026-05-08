# Adoptable disciplines — cairn's standalone-portable pieces

Cairn's full pipeline (Intent → Validation → Implementation → Integration, four agent roles, dispatch skill, hooks, validator) is calibrated for safety-critical / long-horizon AI-assisted work per `docs/spec-v1.md` §1. That calibration is deliberate; it is also more discipline than many projects need.

This doc is cairn's **menu of standalone disciplines** — the four pieces that are useful on their own, even when the consumer has decided against the full four-phase methodology. Prior-art evidence: `docs/reviews/2026-04-23-from-portfolio-evaluation.md` enumerated which cairn pieces a sibling portfolio planned to port without the rest; this list mirrors that table.

## Handoff-as-pointer

**What it is.** A bounded session-handoff format: `templates/handoff.md`, four body sections (`## State`, `## Next`, `## Blocked / Pending`, `## Pointers`), 150–400 token whole-file budget, banned narrative sections (no "What This Session Was About," no "Surprises or Discoveries," no test tallies). The handoff carries state plus next step, not reflection.

**Why it's portable.** Independent of cairn's phase pipeline. It's a discipline about the shape of a single file the next session reads, not about the surrounding methodology. Citation: `docs/operational-reference.md` "Layer 1 — Handoff is a pointer, not a payload."

**Integration cost.** Low — one template file plus a session-end discipline. No tooling required. Wiping the handoff each session is operator-driven.

**What to copy.** `templates/handoff.md`, plus the "Banned sections" list and the 150–400-token budget rule from `docs/operational-reference.md`.

## The three hooks

**What it is.** Three Claude Code hook scripts: `checks/reversibility-guard.sh` (blocks destructive ops, enforces ADR append-only), `checks/role_guard.py` (operator envelope + per-phase write paths), `checks/reality-check.sh` (runs `ruff format` + `ruff check --fix` on Python edits). Wired in `.claude/settings.json` as `PreToolUse` / `PostToolUse` hooks.

**Why it's portable.** Each hook is a self-contained script with a narrow contract. They do not depend on cairn's phase pipeline; they depend only on Claude Code's hook protocol, `jq`, and (for `reality-check.sh`) `ruff`.

**Integration cost.** Minutes — copy the three scripts into your `checks/` directory, wire them in `.claude/settings.json`, ensure `jq` and `ruff` are installed. Note: F1's plugin-install path is the supported flow for plugin-marketplace consumers; manual copy is for non-plugin adoption.

**What to copy.** `checks/reversibility-guard.sh`, `checks/role_guard.py`, `checks/reality-check.sh`, and the relevant `hooks` block from `.claude/settings.json`.

## The architecture validator

**What it is.** `scripts/validate_architecture.py` — a single-file Python validator that mechanically checks whether ADRs, ARCHITECTURE.md, and the corpus's invariant-citation surfaces stay coherent. Exit-zero on green; otherwise prints the divergence list.

**Why it's portable.** Depends on the consumer's ADR + ARCHITECTURE.md split, not on cairn's phase pipeline. If you keep ADRs as append-only frontmatter + body docs and an ARCHITECTURE.md that names invariants, the validator's checks are useful regardless of how features get built.

**Integration cost.** Low — one Python file (cairn-substrate dep set: pyyaml + stdlib). Tune the regex anchors to your ADR / ARCHITECTURE shapes if they differ from cairn's.

**What to copy.** `scripts/validate_architecture.py`, plus the dependent `scripts/lib/invariant_id_extractor.py` and `scripts/lib/superseded_test_signal.py` if their checks are needed.

## The phase-skill-mapping table

**What it is.** `docs/phase-skill-mapping.md` — a phase → role → Superpowers-skill mapping with the role / anti-behavior matrix. Cairn uses it as a binding surface (INV-003's `validate_phase_topology` keys on the table); but it is also a standalone artefact a Superpowers user can lift directly.

**Why it's portable.** Trivial. The table is a static doc — no scripts, no hooks. The phase-row labels are cairn-specific but the role / anti-behavior axis and the skill citations transfer cleanly to any methodology that recognises an Intent → Validation → Implementation → Integration shape.

**Integration cost.** Trivial — copy one Markdown file. Requires the Superpowers plugin to actually use the skill citations.

**What to copy.** `docs/phase-skill-mapping.md`.
