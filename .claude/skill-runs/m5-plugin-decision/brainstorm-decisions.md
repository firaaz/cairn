# Brainstorm decisions (operator-confirmed)

Captured via `AskUserQuestion` during brainstorming session, 2026-05-08, before `/decision` invocation. These are the operator's working assumptions; Phase 2 of the decision protocol may still propose alternatives but must justify departures.

| # | Decision | Operator answer |
|---|---|---|
| 1 | Task pick | **Combined: M5 with portfolio-evaluation review folded in** — one design pass for plugin packaging + the consumer-onboarding surface. |
| 2 | Distribution | **Git-URL install** (private or public repo); consumers run `claude plugin install <git-url>` and pin a SHA. Marketplace deferred. |
| 3 | Stability stance | **Pre-v1; consumers pin SHAs and accept drift.** Six amendment ADRs stay open. |
| 4 | Plugin payload scope | **Full repo minus internals** (`tests/`, `docs/adr/` cairn's own decisions, `docs/plans/` cairn's own plans, `commands/claude-code/.local/`) — plus an audit pass to confirm boundary. |
| 5 | Audience model | **Split: maintainer `CLAUDE.md` + consumer `CONSUMER.md`** (new). Repo CLAUDE.md stays maintainer-only. |
| 6 | Templates surface | **Comprehensive** — every phase-boundary contract surface gets a template (feature-plan, intent.md, ADR frontmatter, active-envelope.yaml, plus Phase-2/Phase-4 outputs as named by user "everything needs the template"). |
| 7 | Migration story | **M5+M6 combined; both ship together; symlink retired.** Plugin install becomes the only path. |
| 8 | Dependency story | **CONSUMER.md prerequisites + post-install hook validates and warns** on missing system deps (`jq`, `ruff`). |

## Decomposition

After approaches A/B/C presented, operator picked **Approach B**: one design doc + per-feature plan trio:
- **F1** — Plugin packaging + manifest + hook registration + post-install dep validator
- **F2** — Consumer-doc surface (CONSUMER.md, README reading order, comprehensive templates, phase-skill-mapping promotion, adoptable-disciplines list)
- **F3** — Migration: complex-rag-analysis from `.slice-system → .` to plugin install, symlink retire

## Open questions handed to /decision

- Whether the cairn-maintainer self-consumption stays as `.slice-system → .` self-symlink (Path B from Phase 0.5 Role 3 trace) or migrates to plugin-installs-itself (Path A). Phase 0.5 enumerated both; pre-mortem and Phase 2 must reckon with this.
- Plugin manifest format details (exact required fields for git-URL install; whether the manifest can declare hook registrations vs requiring consumer to merge settings.json snippets).
- Versioning + pinning mechanism beyond raw SHA (semver tags? branch-based? `claude plugin install` UX implications).
- Whether `commands/claude-code/.full.md` variants ship (large reference docs) or stay maintainer-only.
- Audit checklist for "what's internal vs consumer-facing" — explicit file-by-file list.
