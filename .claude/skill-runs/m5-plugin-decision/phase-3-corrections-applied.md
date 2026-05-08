# Phase 3 Corrections Applied — Final Direction

After Phase 3's adversarial pass returned `passes with caveats`, the convergence is restated with the five caveats applied. The *direction* (Approach A-prime) survives; mechanism specifics are corrected to match the actual Claude Code plugin system.

## Final direction: **A-prime-corrected**

### Distribution mechanism (caveat 2 applied)

- Cairn ships **two manifests in this repo**: `plugin.json` (the plugin definition) AND `marketplace.json` (so cairn is its own marketplace).
- Consumers add cairn as a marketplace: `/plugin marketplace add <git-url>`. Then install: `/plugin install cairn@cairn-marketplace`.
- **Pinning** is via `marketplace.json` `source.ref` (tag) or `source.sha` (SHA) — NOT `<git-url>@<tag>` syntax (which doesn't exist).
- Pre-v1 stance preserved: tags are `v0.x.y`; semver-major stays at 0.

### Payload curation (caveat 1 applied)

- Plugin manifest has NO `include`/`exclude` glob fields. Curation requires **physical separation**.
- **Path chosen:** `plugin.json`'s `source` field specifies a subdir — e.g., `source: { type: "git", url: "<repo>", ref: "<tag>", path: "dist/" }`. CI populates `dist/` at release time from a curated allow-list.
- Alternative considered: separate `cairn-plugin` repo. Rejected — adds repo-management overhead; subdir keeps everything in one repo with clear release boundary.
- `dist/` allow-list (initial M5):
  - `.claude/skills/cairn-tdd-feature/`
  - `.claude/agents/{phase-{1..4}-tdd, triager-tdd, role-topology.yaml}`
  - `checks/{reversibility-guard.sh, reality-check.sh, role_guard.py}`
  - `templates/` (with comprehensive M5 expansion)
  - `hooks/hooks.json` (new — hook registration spec)
  - `plugin.json`, `marketplace.json`
- **Slash-commands deferred to M5.1** — `/catchup`, `/handoff`, `/decision`, `/new-adr`, `/decision.full`, `/new-adr.full` ship in a follow-up payload bump after operator confirms which slash-commands are stable. (Approach B's "consumers bring their own" not endorsed; just deferred.)

### Hook registration (caveat 3 applied)

- Hooks live in `<plugin-root>/hooks/hooks.json` (loaded automatically by Claude Code; resolved via `${CLAUDE_PLUGIN_ROOT}`). NO consumer `.claude/settings.json` merging required.
- Pre-mortem Scenario 2 (settings-merge drift) is now **mostly moot**: there's no consumer-visible settings string to drift. Remaining drift risk is only when cairn itself changes hook command strings between releases — contained to plugin upgrades.
- F1 (packaging) drops "stable shim entry point" defense as unnecessary friction.

### `role_guard.py` fix (caveat 4 applied)

- **Two sites must change**, not one:
  1. `role_guard.py:28` — `CAIRN_ROOT = Path(__file__).resolve().parent.parent` → `CAIRN_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))`
  2. `role_guard.py:121` — `_log_grant()` writes via the same `CAIRN_ROOT`; must use the corrected resolution or the envelope-grant audit trail goes to plugin-cache eviction.
- F1 ships **a positive end-to-end enforcement test** in the post-install validator: write a sample envelope, attempt a denied write, confirm exit 1. Green dep-check that doesn't exercise enforcement is theatre (Pre-mortem Scenario 1 named this directly).

### Audience model (caveat 5 applied)

- **Hybrid: file split + audience tags.**
- `CLAUDE.md` (maintainer-primary, but cross-cutting rules tagged):
  - Maintainer-only sections un-tagged.
  - Cross-cutting rules (e.g., identifier scheme `CLAUDE.md:5-7`, safety-critical rules consumers must follow) tagged `[both]`.
- `CONSUMER.md` (consumer entry):
  - Quickstart, install, dispatch, troubleshooting.
  - Cross-references CLAUDE.md `[both]` sections by anchor link rather than duplicating.
- Portfolio reviewer's "at minimum" floor (`docs/reviews/2026-04-23-from-portfolio-evaluation.md:66`) is satisfied: tagging is present even though split is also adopted.

### Self-consumption (assumption #5 confirmed)

- Cairn-the-repo stays on Path B — self-symlink retained for cairn-the-repo dogfooding.
- Pre-mortem Scenario 3 (self-consumption circularity) is acknowledged but isolated to maintainer workflow.
- Vision commitment "meta-dogfoodable from feature #1" (`docs/why-cairn.md:107-108`) is reinterpreted: the methodology is dogfooded via Path B, not via plugin-installs-itself.

## Items unchanged from convergence note

- Pre-v1 stance.
- M5+M6 combined.
- Comprehensive template extraction.
- Three-feature decomposition (F1 packaging+manifest+validator, F2 consumer-doc surface, F3 migration+symlink retire).
- Brainstorm decisions 1-8 (operator-confirmed).

## Risk register (final)

| # | Pre-mortem scenario | Defense (post-corrections) | Residual risk |
|---|---|---|---|
| 1 | `role_guard.py:28` __file__-anchored CAIRN_ROOT silently breaks envelope enforcement under plugin cache | F1 ships fix to lines 28 + 121 (CWD-anchoring); F1 post-install validator runs positive enforcement self-test | Low if validator is required at install. Need a CI test that exercises the validator under simulated plugin invocation. |
| 2 | Settings-merge drift across N consumers | Mostly moot — `hooks/hooks.json` is plugin-internal; consumers don't merge settings | Limited to plugin upgrades changing hook command strings. Mitigate via plugin-version-pinning + plugin migration notes. |
| 3 | Self-consumption circularity if cairn-the-repo Path A | Cairn stays on Path B (self-symlink); maintainer workflow isolated | Bootstrap circularity persists for cairn maintainers — accepted as cost of meta-dogfooding. |
| 4 | Audience-split done as bisection rather than reading-order fix | Hybrid: file split + audience tags + cross-references | Drift between CLAUDE.md and CONSUMER.md still possible; mitigate via doc-validator + cross-ref check in F2. |
| 5 | `.local/` leakage when audit is allow-list rather than deny-list | Curated payload via `dist/` subdir source — `.local/` files physically not present in plugin payload | None if CI gates `dist/` population; high if CI is missing or skipped. |
| 6 | In-flight skill-run orphaned mid-cutover (M6) | F3 documents quiescence requirement: complete in-flight `cairn-tdd-feature` runs to Phase 4 close before migration | Operator-discipline-dependent; mitigate via F3's pre-migration checklist. |

## Open questions for Phase 5 (independent verification)

- Phase 5 should reproduce Phases 1-3 from the same brief (Phase 0 + 0.5 + brainstorm-decisions) blind to all Phase 1-3 outputs. Compare:
  - Did the fresh agent identify the same top-3 failure scenarios?
  - Did the fresh agent converge on a similar approach (A-prime-shape) or a meaningfully different one?
  - Are there mechanism findings the fresh agent saw that Phase 3 missed?
