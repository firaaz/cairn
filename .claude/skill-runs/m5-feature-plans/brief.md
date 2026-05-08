# Shared brief for m5-feature-plans team

## Context

The ADR `m5-plugin-distribution-and-symlink-retire` (committed 2026-05-08, `docs/adr/m5-plugin-distribution-and-symlink-retire.md`) commits cairn to packaging as a Claude Code plugin via its own marketplace. The decision-trail lives at `.claude/skill-runs/m5-plugin-decision/`.

The ADR splits implementation into three features that ship as one milestone:

- **F1 — Plugin packaging.** Manifests (`marketplace.json` + `dist/.claude-plugin/plugin.json`), `dist/` build script, `dist/hooks/hooks.json`, post-install validator, `role_guard.py:28,121` runtime-anchoring fix.
- **F2 — Consumer-doc surface.** New `CONSUMER.md`, README reading order, comprehensive template extraction, `[both]` audience tags in CLAUDE.md, phase-skill-mapping promotion (Finding 4), `docs/adoptable-disciplines.md` (Finding 5).
- **F3 — Migration + symlink retire.** `complex-rag-analysis` migration; downstream consumers retire from `.slice-system → .` symlink (cairn-the-repo keeps its self-symlink per INV-011/D8).

## Each agent's job

Author one per-feature plan doc that the `cairn-tdd-feature` dispatch skill consumes. Output paths:

- F1 → `docs/plans/2026-05-08-cairn-m5-f1-packaging.md`
- F2 → `docs/plans/2026-05-08-cairn-m5-f2-consumer-doc-surface.md`
- F3 → `docs/plans/2026-05-08-cairn-m6-f3-migration-and-symlink-retire.md`

## Required reading

1. **The ADR** — `docs/adr/m5-plugin-distribution-and-symlink-retire.md` — your authoritative source of decisions. Quote the relevant `D<n>` references in your plan.
2. **The verification trail** — `.claude/skill-runs/m5-plugin-decision/{phase-0-constraints, phase-0.5-journey, phase-1-pre-mortem, phase-3-corrections-applied, phase-5-reconciliation}.md` — for context on constraints, boundaries, and risks. Don't restate; reference.
3. **The plan-doc template (cairn convention)** — `docs/plans/2026-05-07-cairn-shrink-m4-delete-and-relocate.md` — match its shape: frontmatter block (firmness/status/date/scope/inputs), Goal paragraph, Architecture paragraph, Tech Stack line, Self-review summary, sections with `- [ ]` checkboxes for tracking, Out-of-scope follow-ups at the bottom.
4. **Plan-doc spec** — `docs/operational-reference.md:39-46` — the required frontmatter fields including `id:` and `envelope:` (the `envelope:` field drives Phase 3 write-path enforcement).

You MAY spot-read source files (`checks/role_guard.py`, `.claude/settings.json`, `templates/handoff.md`, `pyproject.toml`, `.claude/skills/cairn-tdd-feature/SKILL.md`) when your plan needs evidence for a step.

You MAY `WebFetch` `https://code.claude.com/docs/en/plugins-reference` and `https://code.claude.com/docs/en/plugin-marketplaces` for plugin-system mechanism evidence.

## Plan-doc shape (cairn convention)

```yaml
---
id: <feature-slug>            # e.g., cairn-m5-f1-packaging
envelope:                      # Phase 3 write-path allow-list (regex)
  paths:
    - ^docs/plans/2026-05-08-cairn-m5-f1-packaging\.md$
    - ^<other paths the feature touches>$
firmness: provisional
status: draft
date: 2026-05-08
scope: <one-line scope statement>
inputs:
  - docs/adr/m5-plugin-distribution-and-symlink-retire.md
  - <other inputs>
---

# <Title>

> **For agentic workers:** REQUIRED SUB-SKILL: <choose: cairn-tdd-feature is the dispatch shell; this plan is its input. Within-feature parallelism via parallel Agent calls is permitted per CLAUDE.md "Within-slice parallel subagents are allowed".>

**Goal:** <one paragraph>

**Architecture:** <one paragraph — how the work threads together>

**Tech Stack:** <one line — Python/Bash/Markdown surfaces touched>

## Self-review summary

<self-review against the ADR's D<n> commitments — confirm coverage>

## <Section 1: e.g., F1.1 Plugin manifest authoring>

- [ ] <step 1: specific file change>
- [ ] <step 2: ...>

## <Section 2: ...>

...

## Out-of-scope follow-ups

<what's deferred to M5.1 or a later feature>
```

## Conventions to follow

- **`id:` is a kebab-case slug** matching the filename stem. No prefix numbers.
- **`envelope:` paths are regexes** anchored with `^` and `$` where exact-match is intended; matched against repo-root-relative paths.
- **TDD-shaped steps preferred** for code work — write tests first, then implementation. Cairn-tdd-feature dispatch enforces this via the four-phase pipeline.
- **No premature abstraction.** Three similar lines is better than one abstraction.
- **No comments explaining WHAT.** Only comments for non-obvious WHY (hidden constraint, subtle invariant, workaround for a specific bug).
- **Cite `D<n>` from the ADR** when a step implements a specific commitment. Example: "Step F1.5: Fix `role_guard.py:28,121` per D5 — replace `Path(__file__).resolve().parent.parent` with `Path(os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd()))`."

## Plan-doc cap

Each per-feature plan: ~2000-3500 words. Verbose enough to drive the four-phase dispatch; tight enough to fit in context.

## Final agent message

A one-paragraph summary stating:
- The plan-doc filename you wrote.
- The headline shape (X sections, Y `- [ ]` steps).
- Anything you flagged for a follow-up (likely scope-creep candidates, mechanism unknowns, etc.).
- Confirmation that the plan covers all `D<n>` commitments from the ADR that fall within your feature's scope.

## What NOT to do

- Don't author the implementation itself — only the plan doc that the dispatch skill consumes.
- Don't write outside your assigned plan-doc filename.
- Don't invoke any skill (`/decision`, `/new-adr`, `cairn-tdd-feature`).
- Don't restate the ADR's decisions in detail — reference them by `D<n>` and trust the reader to look up.
- Don't create new ADRs (your work is implementation, not architecture).
