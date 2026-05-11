# plugin-payload-transport — Phase 0 Constraint Envelope

## Invariants

| INV | Claim | Source | Binds This Decision |
|-----|-------|--------|-------------------|
| INV-001 | All post-bootstrap commits carry Conventional Commits prefixes registered in `_FALLBACK_REGISTRY` (scripts/validate_architecture.py). Pipeline-substrate commits use `chore:` prefix. | ARCHITECTURE.md:13–20 | YES — transport mechanism's CI workflow must use a registered prefix; release-publish.yml uses `chore: release` (v4.5:106) |
| INV-011 | Cairn-the-repo retains `.slice-system → .` self-symlink; bootstrap-circularity defense for maintainer dogfood. Plugin consumers use plugin-install, not symlinks. | ARCHITECTURE.md:91–97 | YES — transport choice must not regress `.slice-system` symlink or break maintainer self-consumption |
| INV-012 | Cairn plugin deploys via long-lived `release` branch with `source.source: "url"`, explicit HTTPS URL `https://github.com/firaaz/cairn.git`, explicit `ref: "release"`. No `dist/` subdirectory on `release`; build output lands at branch root. Version signal via `dist/.claude-plugin/plugin.json:version`. | ARCHITECTURE.md:99–105; m5-plugin-deployment-pattern D1; marketplace-source-url-amend D2-revised | YES — INV-012 is the load-bearing invariant this decision touches directly |

## Load-bearing decisions

| ADR & Decision | Binding Text | Source |
|---|---|---|
| **m5-plugin-distribution-and-symlink-retire / D1** | "Cairn ships as a Claude Code plugin via its own marketplace" + "Consumer install flow: /plugin marketplace add <git-url> / /plugin install cairn@cairn-marketplace" | docs/adr/m5-plugin-distribution-and-symlink-retire.md:39–48 |
| **m5-plugin-distribution-and-symlink-retire / D3** | "Plugin manifest has no include/exclude glob fields. Curation requires physical separation. `marketplace.json` `source.path: "dist/".` CI populates `dist/` at release from a curated allow-list" | docs/adr/m5-plugin-distribution-and-symlink-retire.md:55–68 |
| **m5-plugin-deployment-pattern / D1** | "Plugin payload deploys via a long-lived `release` branch" with shape `release/` containing `.claude-plugin/plugin.json`, `agents/`, `checks/`, `hooks/`, `skills/`, `templates/`, `postinstall_validate.py` at branch root. "This shape is forced by the `source.source: 'github'` choice" (later superseded to `url`). | docs/adr/m5-plugin-deployment-pattern.md:45–62 |
| **m5-plugin-deployment-pattern / D2** | "`marketplace.json` uses `source.source: "github"` with explicit `ref: "release"`" — later amended to `source: "url"` with `url: "https://github.com/firaaz/cairn.git"` and same `ref: "release"` | docs/adr/m5-plugin-deployment-pattern.md:64–78; marketplace-source-url-amend D2-revised |
| **m5-plugin-deployment-pattern / D3** | "`dist/.claude-plugin/plugin.json:version` is the canonical consumer-visible update signal" (not marketplace entry's version, which is omitted). Bumped per release via `scripts/build_dist.py:30` copying from `.claude-plugin/plugin-template.json:version` | docs/adr/m5-plugin-deployment-pattern.md:80–86 |
| **m5-plugin-deployment-pattern / D5** | Release CI workflow is `workflow_dispatch`-triggered with `version` input. Workflow asserts input `version` equals built `plugin.json:version` before any push. Force-with-lease (not force) on `release` branch. | docs/adr/m5-plugin-deployment-pattern.md:92–107 |
| **m5-plugin-deployment-pattern / D7** | "`tests/unit/test_marketplace_schema.py` loads `marketplace.json` and asserts: `plugins[0].source.source ∈ {github, url, git-subdir, npm}`, `source.ref == "release"` (after amendment, `source.url == "https://github.com/firaaz/cairn.git"`), no `version` field on marketplace plugin entry, no legacy `type: git`" | docs/adr/m5-plugin-deployment-pattern.md:109–116; marketplace-source-url-amend D7-revised |
| **m5-plugin-deployment-pattern / D8** | "Optional release-tagging step: each `workflow_dispatch` run creates and pushes `v0.x.y` tag pointing at release-branch HEAD. Conditional on `github.event_name == 'workflow_dispatch'`" | docs/adr/m5-plugin-deployment-pattern.md:119–122 |
| **m5-plugin-deployment-pattern / D9** | "F3 audit check 9 acceptance criterion: manual end-to-end install verification in a fresh consumer project. Feature is not merge-final until check 9 records green." | docs/adr/m5-plugin-deployment-pattern.md:124–128 |
| **marketplace-source-url-amend / D2-revised** | "Manifest rewritten from `source: 'github'` to `source: 'url'` with `url: 'https://github.com/firaaz/cairn.git'` and same `ref: "release"` (explicit HTTPS forces HTTPS clone, not SSH)" | docs/adr/marketplace-source-url-amend.md:61–77 |
| **delivery-mechanism-friction / D1** | "`using-cairn` SessionStart skill shipped at `dist/skills/using-cairn/SKILL.md`, registered via `dist/hooks/hooks.json`. Injection is pointer-only, hard-budgeted ≤2,000 tokens." | docs/adr/delivery-mechanism-friction.md:37–39 |

## Hard constraints (cannot violate)

| Constraint | Source |
|-----------|--------|
| **No new deps outside {pydantic, typer, pyyaml}** | CLAUDE.md:11 ("standing dep set as the only allowed dependencies"). Transport mechanism's CI/build scripts must use only `uv`, `python3`, `bash`, and tools already available (jq, ruff). | 
| **Standing prereq floor: {jq, ruff, python3}** | CLAUDE.md:13–15. Transport must not expand consumer prereqs. m5-plugin-deployment-pattern D2 explicitly commits "No expansion of consumer prereq floor." (D2:139) |
| **Operator envelope and write-path enforcement must fire consumer-side after install** | m5-plugin-distribution-and-symlink-retire D5 + D9; m5-plugin-deployment-pattern D9 (F3 audit check 9). Consumer install must result in working `.claude/active-envelope.yaml` enforcement via `checks/role_guard.py` with correct `CLAUDE_PROJECT_DIR` anchoring (D5 fix: env-var fallback, not `__file__`). |
| **INV-012 binding: `release` branch is authoritative payload source, `marketplace.json` points to it** | ARCHITECTURE.md:99–105. Transport must preserve `release` branch + `ref: "release"` invariant; schema lint must pass `tests/unit/test_marketplace_schema.py` assertions. |
| **ADR append-only enforcement:** no overwriting existing ADRs on the transport-decision ADR itself | CLAUDE.md:20; reversibility-guard.sh:48,76. The decision ADR (when accepted) is immutable except frontmatter edits. |
| **Force-with-lease only, never bare `--force`** | CLAUDE.md:26. m5-plugin-deployment-pattern D6 + release-publish.yml:110 enforce this. |
| **`.slice-system` symlink must not regress** | CLAUDE.md:38–39; INV-011. Transport CI must never create infinite-recursion hazards (e.g., find with recursive symlink follow). scripts/build_dist.py:55 explicitly ignores `.slice-system`. |
| **Payload curation via physical separation (`dist/` subdir on `dev`, branch-root on `release`), not globs** | m5-plugin-distribution-and-symlink-retire D3; m5-plugin-deployment-pattern D1. Plugin manifest has no include/exclude fields. |
| **Consumer-facing commands unchanged (no `@release` qualifier in README/CONSUMER.md)** | m5-plugin-deployment-pattern D2 + D3 ("The literal consumer commands at README.md:19, CONSUMER.md:14, and docs/upgrading-from-symlink.md:49 remain UNCHANGED"). marketplace-source-url-amend D2-revised reiterates. |

## Soft constraints (cost-tradeable)

| Constraint | Source | Rationale |
|-----------|--------|-----------|
| **Minimize CI ceremony** | m5-plugin-deployment-pattern Phase 3 stress test; Phase 3: "simpler ceremony + structurally-absent S4 (two-step coupling) + first-party CI (no third-party Actions like peter-evans/create-pull-request)." | Approach D rejected for 3-step ceremony + third-party deps. Approach A (release-branch+sync) preferred for 1-step + first-party only. |
| **Prefer release history that includes tags for archaeology** | m5-plugin-deployment-pattern D8; Risk Register (D8 rationale: "SHA-pinning escape hatch," "archaeology anchor"). | Tagging is optional, but recommended for future maintainers to trace releases. |
| **SessionStart pointer, not payload accretion** | delivery-mechanism-friction D1; R1 mitigation. | CI check on SessionStart token budget (D6) enforces the ≤2,000-token cap. Preference for staying well under budget. |

## Open questions for Phase 0.5

1. **Does INV-012's `release` branch + `ref: "release"` invariant remain authoritative after consumer install?** Test: F3 audit check 9 (manual install verification) must pass — consumer runs `/plugin marketplace add https://github.com/firaaz/cairn` + `/plugin install cairn@cairn-marketplace`, resolves marketplace at `dev`-tip, follows `source: "url"` + `https://github.com/firaaz/cairn.git` + `ref: "release"` to `release` branch, installs cleanly.

2. **Does the consumer's first install carry `.claude/active-envelope.yaml`?** (BELIEVED, not verified.) If not, envelope enforcement fires at first dispatch, not at first install. Impact: when should the envelope-grant audit trail begin?

3. **Does `release` branch's `postinstall_validate.py` execute post-install in the consumer's environment?** The script is part of the shipped payload (build_dist.py:32); the CLI calls it, but we haven't verified end-to-end in a non-cairn project. F3 audit check 9 is the verification gate.

4. **What transport mechanism does `marketplace-add` use (HTTPS or SSH)?** framing.md notes: "Marketplace-add HTTPS clone works (full repo lands at `~/.claude/plugins/marketplaces/cairn-marketplace/` via HTTPS)" — but does the plugin resolver's subsequent clone of the `source: "url"` respect the URL's HTTPS scheme, or does it force SSH based on github.com host? marketplace-source-url-amend D2-revised assumes HTTPS on the URL source-type, but this is BELIEVED and empirically verified only at F3 check 9.

5. **Does `delivery-mechanism-friction` D2 (SessionStart composes with superpowers, never double-loads) require a deployed superpowers plugin in the consumer's environment, or does it probe and degrade gracefully?** If the consumer doesn't have superpowers, does SessionStart still inject cairn context, or does it skip?

## What's NOT a constraint (explicitly unsupported beliefs)

| Belief | Why unsupported |
|--------|-----------------|
| **`release` branch can carry the full source tree (scripts/, docs/, tests/, .venv/)** | m5-plugin-deployment-pattern D1 (shape-i) and marketplace-source-url-amend explicitly state branch root carries only curated payload. `dist/` curation on `dev` prevents source leakage; `release` is CI-only deploy target. |
| **CI can use GitHub's `peter-evans/create-pull-request` or similar third-party Actions** | m5-plugin-deployment-pattern Phase 3 stress test + Approach D rejection; m5-plugin-distribution-and-symlink-retire D9: "first-party CI only." |
| **Marketplace entry carries a `version` field** | m5-plugin-deployment-pattern D3 (explicit omission); marketplace-source-url-amend D7-revised reiterates no `version` on the marketplace plugin entry. Version signal is `dist/.claude-plugin/plugin.json:version` only. |
| **Consumer can pin via `@release` qualifier (e.g., `cairn@cairn-marketplace@release`)** | m5-plugin-deployment-pattern D2: "The literal consumer commands... remain UNCHANGED. No `@release` qualifier; no docs churn." Plugin resolver's ref resolution is transport-internal. |
| **`release` branch stays stable between releases (no force-with-lease)** | m5-plugin-deployment-pattern D6: "Each release replaces the `release` branch tree deterministically. Merges are not used; `--force` is blocked... `--force-with-lease` is the only permitted form." History is rewritten per release. |
