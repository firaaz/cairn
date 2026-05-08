---
id: m5-plugin-distribution-and-symlink-retire
status: accepted
firmness: firm
supersedes: []
supersedes-sections: []
superseded-by: null
topic: architecture
invariants-touched: []
date: 2026-05-08
---

# m5-plugin-distribution-and-symlink-retire: M5 Plugin Distribution and Symlink Retire

## Status

Accepted (post-`/decision` Phase 5 independent verification, 2026-05-08).

## Date

2026-05-08

## Context

Cairn has been consumed via `.slice-system → .` symlink since the bootstrap. M4 retired the slice substrate (`docs/plans/2026-05-06-cairn-shrink-design.md`); M5 packages cairn as a Claude Code plugin and M6 migrates the existing symlink consumer (`complex-rag-analysis`).

A prospective consumer (`personal-portfolio`) evaluated cairn at 2026-04-23 and chose copy-adoption over symlink-adoption (`docs/reviews/2026-04-23-from-portfolio-evaluation.md:32`), citing pre-v1 instability and audience-split friction (Findings 1-5). Their evidence shapes this ADR's docs commitments.

`/decision` ran 2026-05-08:
- **Phase 0** surfaced 27 constraints across distribution / audience / deps / hooks / migration / docs / other (`.claude/skill-runs/m5-plugin-decision/phase-0-constraints.md`).
- **Phase 0.5** traced three role journeys (first-time consumer, existing symlink consumer, cairn maintainer) and 13 cross-role boundaries (`.../phase-0.5-journey.md`).
- **Phase 1** named 6 failure scenarios (technical / scale / integration / adoption), severity-tagged (`.../phase-1-pre-mortem.md`).
- **Phase 2** forced-enumerated three approaches: A=git-URL plugin, B=marketplace+curated+v1-first, C=copy-recommended-no-plugin (`.../phase-2-approach-{A,B,C}.md`).
- **Phase 3** stress-tested the convergence; verified 5 mechanism corrections against `code.claude.com/docs/en/plugins-reference` (`.../phase-3-adversarial.md`, `.../phase-3-corrections-applied.md`).
- **Phase 5** ran independent verification (fresh-context blind agent); reconciled with 1 mechanism-evidence divergence resolved (`.../phase-5-independent-verification.md`, `.../phase-5-reconciliation.md`).

## Decision

### D1 — Cairn ships as a Claude Code plugin via its own marketplace

This repo hosts both manifests:
- `.claude-plugin/marketplace.json` (cairn becomes its own marketplace)
- `dist/.claude-plugin/plugin.json` (the plugin manifest at the curated payload subdir)

Consumer install flow:
```
/plugin marketplace add <git-url>
/plugin install cairn@cairn-marketplace
```

### D2 — Pre-v1 stability stance with explicit semver-via-tags

`dist/.claude-plugin/plugin.json` carries an explicit `"version": "0.x.y"` field. Tags follow `v0.x.y`. Major version stays at `0` until the 6 pending amendment ADRs (`cost-per-slice-budget`, `parallelism-v1`, `phase-pipeline-evaluation`, `feature-slice-model`, `context-tiers-integration`, `identifier-scheme`) close. Consumers pin via `marketplace.json` `source.ref` (tag) or `source.sha` (commit). Per `code.claude.com/docs/en/plugins-reference:1004-1008`, explicit version strings require manual bumps — cairn commits to bumping on every consumer-visible change.

### D3 — Payload curation by physical separation

Plugin manifest has no `include`/`exclude` glob fields. Curation requires physical separation. `marketplace.json` `source.path: "dist/"`. CI populates `dist/` at release from a curated allow-list:

- `.claude/skills/cairn-tdd-feature/` → `dist/skills/cairn-tdd-feature/`
- `.claude/agents/{phase-1-tdd, phase-2-tdd, phase-3-tdd, phase-4-tdd, triager-tdd}.md` + `role-topology.yaml` → `dist/agents/`
- `checks/{reversibility-guard.sh, reality-check.sh, role_guard.py}` → `dist/checks/`
- `templates/` → `dist/templates/` (with comprehensive M5 expansion per D7)
- New: `dist/hooks/hooks.json` (hook registration)
- New: `dist/.claude-plugin/plugin.json` (plugin manifest)

Slash-commands deferred to **M5.1** — `/catchup`, `/handoff`, `/decision`, `/decision.full`, `/new-adr`, `/new-adr.full` ship in a follow-up payload bump after stability audit.

Cairn-internal surfaces excluded from `dist/`: `commands/claude-code/.local/`, `tests/`, `docs/adr/`, `docs/plans/`, `docs/reviews/`, `scripts/` (other than `_root.py` + `lib/` if hooks need them — confirm in F1), `pyproject.toml`, `uv.lock`, `.venv/`.

### D4 — Hook registration via plugin-internal `hooks/hooks.json`

Hooks register via `dist/hooks/hooks.json` per `code.claude.com/docs/en/plugins-reference:85,671`. NO consumer `.claude/settings.json` merge is required. Hook command strings resolve `${CLAUDE_PLUGIN_ROOT}` substitution to the plugin's installation directory (`code.claude.com/docs/en/plugins-reference:542`).

### D5 — `role_guard.py` anchoring fix (must-fix in F1)

Two sites in `checks/role_guard.py` use `Path(__file__).resolve().parent.parent` to anchor `CAIRN_ROOT`:
- `checks/role_guard.py:28` — `CAIRN_ROOT` definition; drives `OPERATOR_ENVELOPE_PATH`
- `checks/role_guard.py:121` — `_log_grant()` writes `envelope-grants.log` via the same `CAIRN_ROOT`

Under plugin-cache invocation, `__file__` resolves to the plugin cache, breaking envelope enforcement (silent fail-open) and routing audit trail to ephemeral plugin storage. Both sites change to:

```python
CAIRN_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
```

F1 ships **a positive end-to-end enforcement test** in the post-install validator: write a sample envelope, attempt a denied write, confirm exit 1. Green dep-check that doesn't exercise enforcement is theatre.

### D6 — Audience model: file split + audience tags for cross-cutting

- `CLAUDE.md` stays maintainer-primary. Cross-cutting rules consumers must follow (e.g., identifier scheme `CLAUDE.md:5-7`, ADR append-only `CLAUDE.md:20`, envelope contract `CLAUDE.md:24`) tagged `[both]` per portfolio review's "at minimum" floor (`docs/reviews/2026-04-23-from-portfolio-evaluation.md:66`).
- New `CONSUMER.md` is the consumer entry doc (quickstart, install, dispatch, troubleshooting). Cross-references CLAUDE.md `[both]` sections by anchor link rather than duplicating.
- README adds explicit reading order (Finding 2): README → CONSUMER.md → operational-reference.md → spec-v1.md.

### D7 — Comprehensive template extraction

`templates/` expands beyond `handoff.md` to cover every phase-boundary contract surface:
- `templates/feature-plan.md` — per-feature `docs/plans/<feature>.md` shape (the dispatch skill's input contract)
- `templates/intent.md` — Phase 1 Reader output shape
- `templates/sweep-notes.md` — Phase 4 Auditor output shape
- `templates/adr-frontmatter.yaml` — ADR id/name/status/firmness frontmatter
- `templates/active-envelope.yaml` — operator envelope sample (`mode: off` default)

### D8 — Cairn self-consumption stays on Path B

Cairn-the-repo retains `.slice-system → .` self-symlink for its own dogfooding. Plugin-installs-itself (Path A) rejected: bootstrap circularity (Pre-mortem Scenario 3) makes hook iteration unworkable — modifying `checks/role_guard.py` while the running hook is the plugin-cached copy requires republish-reinstall-restart per iteration. Vision commitment "meta-dogfoodable from feature #1" (`docs/why-cairn.md:107-108`) is reinterpreted: cairn dogfoods via Path B, not via plugin-installs-itself.

### D9 — M5+M6 ship together as one design milestone, three features

- **F1** — packaging + manifests + `hooks.json` + post-install validator + `role_guard.py:28,121` fixes
- **F2** — `CONSUMER.md` + README reading order + comprehensive templates + phase-skill-mapping promotion (Finding 4) + adoptable-disciplines list (Finding 5)
- **F3** — `complex-rag-analysis` migration + `.slice-system → .` retire for downstream consumers (cairn-the-repo keeps self-symlink per D8)

Each feature gets its own per-feature plan doc and runs through `cairn-tdd-feature` dispatch in sequence.

## Consequences

### Easier (positive)

- **M5+M6 ships in one milestone.** `complex-rag-analysis` migrates atomically rather than waiting on a separate program.
- **Curated payload via `dist/` is structurally clean.** `.local/` files, internal docs, tests, ADRs, `.venv/` cannot leak — they are physically not present in the plugin payload.
- **Pre-v1 SHA/tag-pin is honest about substrate state.** Consumers control update cadence; cairn doesn't push surprise changes.
- **`hooks/hooks.json` removes consumer settings.json merge complexity.** Pre-mortem Scenario 2 (settings-merge drift) becomes mostly moot — there is no consumer-visible settings string to drift.
- **Plugin install registers skills/agents/hooks automatically.** Consumer onboarding shrinks to ~10 minutes for a TDD-by-construction first dispatch.
- **Cairn becomes its own marketplace.** Single repo, single source of truth; no separate `cairn-plugin` repo to manage.
- **Audience split + tags hybrid satisfies portfolio review's literal suggestion.** Both file separation AND tagging — strictly better than either alone.

### Harder (negative)

- **Cairn becomes its own marketplace.** Adds three new artifacts: `marketplace.json`, `dist/.claude-plugin/plugin.json`, `dist/hooks/hooks.json`. CI must populate `dist/` correctly on release.
- **Slash-commands deferred to M5.1.** Consumer doesn't get `/catchup`, `/decision`, `/new-adr` etc. on first install. Operator must communicate this expectation.
- **Path B circularity persists for cairn maintainers.** Self-symlink retained; bootstrap-exception ADR remains relevant.
- **Six amendment ADRs stay open.** v1 is gated on closing them; until then, cairn ships as `v0.x.y`. Consumers pin SHAs / tags accordingly.
- **Layout transform in `dist/` build script is a CI dependency.** Build script renames `.claude/agents/*` → `dist/agents/*`, `.claude/skills/*` → `dist/skills/*`, `commands/claude-code/*` → `dist/commands/*` (when slash-commands ship in M5.1). Must stay green on every release tag.
- **`role_guard.py` envelope-grant log moves to consumer's `.claude/envelope-grants.log` (D5 fix).** Audit trail is consumer-side, not plugin-side — cairn-the-repo and consumer projects each own their own log. Acceptable.

## Alternatives Considered

### Approach B — marketplace + curated + v1 first

Rejected. The "cut v1 first" gate ties M5+M6 to closing 6 amendment ADRs (uncertain timeline). `complex-rag-analysis` would stay on a deprecation-flagged symlink indefinitely while v1 is negotiated. Discoverability and curated-payload structure are absorbed into the chosen direction (D1+D3); the *gate* is what made B unworkable, not its substance. (`.claude/skill-runs/m5-plugin-decision/phase-2-approach-B.md`)

### Approach C — no plugin, copy-recommended

Rejected. Avoids most blocking pre-mortem scenarios (1, 3, 5 evaporate without a plugin cache). Converts portfolio reviewer's actual choice (copy not symlink) from apology to asset. But: M6 doesn't happen at all under C; `complex-rag-analysis` stays on a deprecated symlink with no end-state. The consumer-doc surface (CONSUMER.md, templates, etc.) lands in F2 of the chosen direction anyway, so C's strongest pillar is a subset of A-prime, not a competing position. (`.claude/skill-runs/m5-plugin-decision/phase-2-approach-C.md`)

### Audience-tagged single CLAUDE.md (no split)

Rejected. Phase 3 verified the portfolio reviewer's `2026-04-23-from-portfolio-evaluation.md:66` "at minimum" clause endorses tagging EVEN with split. Hybrid (split + tags) is strictly better than either alone. (`.claude/skill-runs/m5-plugin-decision/phase-3-adversarial.md`)

### Path A self-consumption (cairn installs itself as plugin)

Rejected. Pre-mortem Scenario 3 named the bootstrap circularity tax. Phase 5 (independent verification) reached the same Path-B conclusion via the same reasoning. Vision commitment "meta-dogfoodable from feature #1" is preserved by reinterpretation: dogfooding via Path B is meta-dogfooding. (`.claude/skill-runs/m5-plugin-decision/phase-1-pre-mortem.md` Scenario 3, `.claude/skill-runs/m5-plugin-decision/phase-5-reconciliation.md`)

## Risk Register

| # | Pre-mortem scenario | Defense | Residual risk |
|---|---|---|---|
| 1 | `role_guard.py:28` __file__-anchored CAIRN_ROOT silently breaks envelope enforcement under plugin cache | D5: fix lines 28 + 121 to `CLAUDE_PROJECT_DIR` anchoring; F1 post-install validator runs positive enforcement self-test | Low if validator gates install. CI must include a test exercising the validator under simulated plugin invocation. |
| 2 | Settings-merge drift across N consumers | D4: `hooks/hooks.json` is plugin-internal; no consumer settings.json edits | Limited to plugin upgrades changing hook command strings. Mitigate via plugin-version pinning + migration notes. |
| 3 | Self-consumption circularity if cairn-the-repo Path A | D8: cairn stays on Path B (self-symlink); maintainer workflow isolated | Bootstrap circularity persists for cairn maintainers — accepted as cost of meta-dogfooding. |
| 4 | Audience-split done as bisection rather than reading-order fix | D6: hybrid file split + audience tags + cross-references | Drift between CLAUDE.md and CONSUMER.md still possible; mitigate via doc-validator + cross-ref check in F2. |
| 5 | `.local/` leakage when audit is allow-list rather than deny-list | D3: curated `dist/` subdir — `.local/`, `tests/`, etc. physically not present | None if CI gates `dist/` population; high if CI is missing or skipped. F1 must include the CI gate. |
| 6 | In-flight skill-run orphaned mid-cutover (M6) | F3: documents quiescence requirement — complete in-flight `cairn-tdd-feature` to Phase 4 close before migration | Operator-discipline-dependent; mitigate via F3's pre-migration checklist. |

## Verification Trail

All artifacts under `.claude/skill-runs/m5-plugin-decision/`:

- `phase-0-constraints.md` — 27 numbered constraints, source-cited.
- `phase-0.5-journey.md` — three role traces + cross-role boundaries.
- `brainstorm-decisions.md` — operator-confirmed working assumptions.
- `phase-1-pre-mortem.md` — 6 failure scenarios.
- `phase-2-approach-A.md`, `phase-2-approach-B.md`, `phase-2-approach-C.md` — three steel-mans.
- `phase-2-convergence-note.md` — lead synthesis pre-Phase-3.
- `phase-3-adversarial.md` — 5 mechanism corrections.
- `phase-3-corrections-applied.md` — final direction post-corrections.
- `phase-5-independent-verification.md` — fresh-context blind verification.
- `phase-5-reconciliation.md` — comparison + divergence resolution.

Mechanism evidence: `code.claude.com/docs/en/plugins-reference` (fetched 2026-05-08). Direct code verification of `checks/role_guard.py:28,121`.
