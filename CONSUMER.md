# Cairn — consumer entry doc

You are about to consume cairn from another project. This file is the navigation surface: install flow, first dispatch, troubleshooting, and pointers to the canonical rules in `CLAUDE.md`. It deliberately does not duplicate prose — anchor links into `CLAUDE.md` are the source of truth.

## What you get

The cairn plugin installs the four-phase TDD dispatch skill (`cairn-tdd-feature`), the four phase agents (`phase-1-tdd` … `phase-4-tdd`) plus the triager, three Claude Code hooks (`reversibility-guard.sh`, `role_guard.py`, `reality-check.sh`), the architecture validator (`scripts/validate_architecture.py`), and the templates under `templates/`. Slash commands (`/catchup`, `/handoff`, `/decision`, `/decision.full`, `/new-adr`, `/new-adr.full`) ship in a follow-up payload bump (M5.1 per ADR D3) — they are not in the F1 plugin install.

## Install (quickstart)

Two-line install via the marketplace:

```bash
/plugin marketplace add https://github.com/firaaz/cairn
/plugin install cairn@cairn-marketplace
```

After install, run the post-install validator:

```bash
# F1-followup (intentional, separately tracked): validator stdout literal lands in F1.1. See docs/roadmap.md or .claude/skill-runs/cairn-m6-f3-migration-and-symlink-retire/integration/sweep-notes.md.
uv run python scripts/validate_plugin_install.py
```

The validator exits non-zero if `jq` or `ruff` are missing (the hooks silently no-op without them). Install both before any work — see [`CLAUDE.md#hook-dependencies`](CLAUDE.md#hook-dependencies).

## First dispatch in 10 minutes

1. Copy `templates/feature-plan.md` to `docs/plans/<YYYY-MM-DD>-<feature-id>.md`. Fill the frontmatter (`id:`, `envelope:` regex array) and the four body sections (What/Why, Boundary, Specification, Verification).
2. Copy `templates/active-envelope.yaml` to `.claude/active-envelope.yaml`. The default ships `mode: off`; switch to `mode: operator` with a `paths:` regex list when starting focused feature work. The file must include a self-pattern matching itself or you cannot edit it under enforcement — see [`CLAUDE.md#operator-envelope`](CLAUDE.md#operator-envelope).
3. Invoke the `cairn-tdd-feature` dispatch skill via the Skill tool with the plan path as args. The skill runs all four phases as fresh subagents and produces four commits plus workspace artefacts under `.claude/skill-runs/<feature-id>/`.
4. Observe the four commits in `git log`: phase 1 (intent), phase 2 (validation), phase 3 (implementation), phase 4 (integration sweep notes).

## The four phases

Each phase is a fresh session, takes a declared input artefact, and commits a declared output artefact: Phase 1 (Reader) writes `intent.md`; Phase 2 (Skeptic) writes failing tests; Phase 3 (Builder) writes source within the envelope to make tests pass; Phase 4 (Auditor) writes sweep notes verifying invariants. Full details: `docs/operational-reference.md` "The Four Phases".

## The Phase Skill Guide

The phase → role → Superpowers-skill mapping is its own doc: `docs/phase-skill-mapping.md`. It is independently cherry-pickable by Superpowers users without committing to cairn's full pipeline — see also the partial-adoption menu at `docs/adoptable-disciplines.md`.

## Cross-cutting rules consumers must follow

These rules live in `CLAUDE.md` under the `[both]` audience tag. Anchor links are the source of truth; do not paraphrase here.

- [Identifier scheme](CLAUDE.md#identifier-scheme-both) — every ADR, slice, feature, and decision point carries `id:` (immutable) and `name:` (mutable).
- [Hook dependencies](CLAUDE.md#hook-dependencies) — install `jq` and `ruff` before any work; missing deps cause silent no-op.
- [ADRs are append-only](CLAUDE.md#adrs-are-append-only) — frontmatter-only edits permitted; new content via supersession.
- [Force-push policy](CLAUDE.md#force-push-policy) — `--force` blocked; `--force-with-lease` allowed.
- [Operator envelope](CLAUDE.md#operator-envelope) — write-gate file at `.claude/active-envelope.yaml`; `mode: operator` enforces, `mode: off` disables.

## Templates

- `templates/feature-plan.md` — per-feature plan-doc shape (frontmatter + What/Why, Boundary, Specification, Verification).
- `templates/intent.md` — Phase 1 output shape (eight required sections, four frontmatter keys).
- `templates/sweep-notes.md` — Phase 4 output shape (test results, validator results, invariant verification, adjacent-code regression check).
- `templates/handoff.md` — bounded session-handoff shape (four sections, 150–400 token budget).
- `templates/adr-frontmatter.yaml` — ADR frontmatter for `/new-adr` authoring.
- `templates/active-envelope.yaml` — operator-envelope shape with self-pattern example and `mode: off` default.

## Troubleshooting

- **Hooks silently no-op.** `jq` or `ruff` missing — install both per [hook dependencies](CLAUDE.md#hook-dependencies). The hook prints a stderr warning then exits 0; enforcement is silently disabled.
- **Writes denied unexpectedly.** The operator envelope is in `mode: operator` and your write path does not match any regex. Either widen the `paths:` list, switch to `mode: off`, or move the work into a dispatch-skill phase. See [Operator envelope](CLAUDE.md#operator-envelope).
- **Phase 3 cannot find tests.** Phase 2's tests must be committed to git before Phase 3 dispatches. Check `git log` for the phase 2 commit; if missing, Phase 2 did not exit cleanly.
- **ADR edit blocked.** `reversibility-guard.sh` allows only frontmatter `status:` / `superseded-by:` / `firmness:` first-line edits on existing ADRs. To change a decision body, write a new ADR with `supersedes: <id>`. Typo escape hatch: `ADR_EDITORIAL_FIX=1`. See [ADRs are append-only](CLAUDE.md#adrs-are-append-only).
- **Post-install validator fails.** Re-run `uv tool install ruff` and `brew install jq`; re-run the validator. F1's validator stdout literal lists the exact diagnostic message — see the F1-followup placeholder in the Install section.

## Where to next

Mirrors the README reading order:

1. README.md — what cairn is, at a glance.
2. CONSUMER.md — you are here.
3. `docs/operational-reference.md` — how cairn works (Layer 1).
4. `docs/spec-v1.md` — why cairn is shaped this way (Layer 2; pull in deliberately).

## Adoptable disciplines (no plugin install)

Cairn's full pipeline is calibrated for safety-critical / long-horizon work. Four pieces are useful standalone — handoff-as-pointer, the three hooks, the architecture validator, and the phase-skill-mapping table — without committing to the four-phase methodology. See `docs/adoptable-disciplines.md`.
