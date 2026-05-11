# Phase 0 — Constraint Envelope (delivery-mechanism-friction)

## Invariants (from ARCHITECTURE.md)

- **INV-001**: "All cairn development after the bootstrap commit produces commits whose Conventional Commits prefixes are recognised in the validator's `_FALLBACK_REGISTRY`."  
  (docs/ARCHITECTURE.md:13)  
  Relevance: Any shift in setup/delivery must preserve the commit prefix binding; consumer dispatch skills must commit via approved prefixes.

- **INV-003**: "Every cairn-tdd feature runs through exactly four phases in order — Intent, Validation, Implementation, Integration. Each phase's role and anti-behaviors are surfaced in the agent prompts at `.claude/agents/phase-{1..4}-tdd.md`."  
  (docs/ARCHITECTURE.md:42)  
  Relevance: Phase-locked pipeline is the execution model; delivery friction affects onboarding into the pipeline, not the pipeline's shape.

- **INV-004**: "Session-start context on a fresh prompt in cairn uses ≤40,000 total tokens. Slash commands use progressive disclosure: each command has a lite file (≤500 tokens) and an optional `.full.md` sibling."  
  (docs/ARCHITECTURE.md:51)  
  Relevance: Setup-surface-up (Pyright, ast-grep, ENABLE_LSP_TOOL, superpowers) increases initial context; must not breach 40k budget for fresh-session orientation.

- **INV-005**: "All cross-referenceable entities carry a two-field identity model: immutable `id:` and mutable `name:`."  
  (docs/ARCHITECTURE.md:59)  
  Relevance: Consumer onboarding docs must use consistent id:/name: labeling.

- **INV-011**: "Cairn-the-repo retains a local self-consumption mechanism so maintainers can iterate on hook scripts without going through plugin republish-reinstall-restart cycles. Currently implemented as `.slice-system → .` self-symlink."  
  (docs/ARCHITECTURE.md:91)  
  Relevance: Maintainer delivery surface must preserve dogfood loop; any plugin-distribution shift cannot break maintainer iteration.

- **INV-012**: "Cairn's plugin payload deploys via a long-lived `release` branch, not via the default branch. `.claude-plugin/marketplace.json` carries `source.source: "url"` with explicit HTTPS URL and explicit `ref: "release"`."  
  (docs/ARCHITECTURE.md:99)  
  Relevance: Plugin surface is locked to release-branch + marketplace pattern; framing question about "delivery direction" must operate within this constraint.

## ADRs (status + firmness)

- **phase-lock-and-role-declaration** (accepted; firm; 2026-04-11)  
  Four-phase pipeline shape is load-bearing and locked. Phase names, role names, and ordering unchanged; changes require supersession.  
  Relevance: Setup/discovery friction affects session-start, not pipeline shape. Dispatch skills must present the four phases as the entry point.

- **context-discipline-protocol** (accepted; firm; 2026-04-11)  
  Handoff is a pointer (150–400 tokens), not a payload. Three-tier context (Tier 1 always, Tier 2 on-demand via subagent, Tier 3 post-catchup).  
  Relevance: Consumer onboarding costs paid per-machine (Tier 1 reading) vs. per-session (Tier 2 dispatch); framing question about "friction paid by substrate only" maps to Tier 1 vs. Tier 2 boundary.

- **identifier-scheme** (accepted; firm; 2026-04-15)  
  Two-field id:/name: model for all entities. Cross-references use id:; prose uses name:.  
  Relevance: Consumer-facing docs (README, CONSUMER.md, setup scripts) must correctly cite ADRs and slash commands by id:.

- **m5-plugin-distribution-and-symlink-retire** (accepted; firm; 2026-05-08)  
  Cairn ships as a Claude Code plugin via its own marketplace. D1: consumer install is `/plugin marketplace add <url>` + `/plugin install cairn@cairn-marketplace`. D3: payload curation via `dist/` physical separation. D8: cairn-the-repo keeps self-symlink (Path B dogfood). D6: audience model with `CLAUDE.md` [both] tags + new `CONSUMER.md`.  
  Relevance: Defines the consumer entry surface; delivery-mechanism friction decisions operate within this constraint.

- **m5-plugin-deployment-pattern** (accepted; firm; 2026-05-09)  
  D1: payload deploys via long-lived `release` branch, not `dist/` subdirectory; shape is branch-root. D2: `marketplace.json` uses `source.source: "github"` with explicit `ref: "release"`. D9: F3 audit check 9 (manual end-to-end install) is non-skippable acceptance gate.  
  Relevance: Plugin consumer-visibility surface is locked. Delivery friction cannot be resolved by changing the install mechanism itself; must work within release-branch + marketplace pattern.

- **cairn-substrate-and-fastmcp** (superseded by cairn-substrate-and-fastmcp-superseded; firm; 2026-04-26)  
  D1: standing v1 dep set = {pydantic, kuzudb, mistune, typer, fastmcp, pyyaml}. D2: new deps require deliberate ADR. D8: agent-context structural lockdown on canonical-knowledge sources when MCP exposes a query surface.  
  Relevance: New code constraints; impacts whether consumer-facing scripts may add Pyright/ast-grep without an ADR.

- **parallelism-v1** (accepted; provisional; 2026-04-12)  
  Concurrent slice execution is v1-legal when slices have no unmet `after` constraints. State is branch-local; no global active-slice pointer.  
  Relevance: Delivery-surface friction affects onboarding into slices; parallelism constraints the slice-dispatch entry point.

- **feature-slice-model** (accepted; firm; 2026-04-12)  
  Features are unit of intent, slices unit of execution. Feature files at `.claude/features/<id>.yaml` carry slice dependency graph.  
  Relevance: Consumer must understand feature/slice decomposition to use the dispatch skill; onboarding surfaces must teach this.

- **cliff-failure-mode-and-v1-defenses** (accepted; provisional; 2026-04-11)  
  v1 defense commitments D1/D2/D3 (automated refresh, code↔invariant binding, unknown-unknown backstop). Provisionally expected to be superseded.  
  Relevance: Pre-v1 scope constraint; delivery-mechanism work must declare explicit non-v1-scope waiver if it touches v1 commitment areas.

## Lessons

- **L-022**: "Manifest-schema lints must reference the live upstream docs, not memory."  
  (docs/lessons.md:437)  
  When publishing deliverables (plugin manifest, hooks.json, plugin.json), schema correctness is undetectable until real consumer round-trip. Include live-docs cross-reference in Phase 0 constraint harvest.

- **L-020**: "Skill-layer execution contracts the protocol relies on must be mechanized, not prose-specified."  
  (docs/lessons.md:100)  
  Delivery/onboarding scripts whose side effects are prose-specified (install, register hooks, emit guidance) have latent cost under context pressure. Non-skippable steps require code, not just description.

- **L-013**: "When planning parallel-execution work, budget separately for branching/merge mechanics vs. skill-layer execution contracts."  
  (docs/lessons.md:100)  
  Applies to consumer onboarding: the plugin install mechanics (checkout, unpack) are predictable; the setup-automation contracts (register hooks, emit diagnostics, validate post-install) are the latent cost.

- **L-005**: "Prompt-layer enforcement is empirically inadequate; structural enforcement preserves value-prop under context pressure."  
  (docs/lessons.md, referenced in docs/adr/cairn-substrate-and-fastmcp.md:37)  
  Consumer-setup guidance saying "configure Pyright" or "enable ENABLE_LSP_TOOL=1" will drift without automated enforcement; auto-configuration or skip-if-unavailable is required.

## Spec / operational reference

- **Current consumer install steps** (docs/operational-reference.md:8–17, CONSUMER.md §Quickstart, README.md:19):
  ```
  /plugin marketplace add https://github.com/firaaz/cairn
  /plugin install cairn@cairn-marketplace
  ```
  No consumer-run setup steps currently shipped. Post-install: hooks auto-register via `dist/hooks/hooks.json` (D4 of m5-plugin-deployment-pattern).

- **Current required consumer deps** (CLAUDE.md:13–15):
  - `jq` (all three checks/*.sh hooks require it)
  - `ruff` (reality-check.sh also requires it)
  - `python3` (validators, hooks run under python3)
  
  The framing's "setup-surface up" proposal adds: Pyright, ast-grep, `ENABLE_LSP_TOOL=1`, user-scope superpowers. The "setup-surface down" proposal retains the current floor.

- **Phase Skill Guide** (docs/phase-skill-mapping.md, operationally-dependent on docs/operational-reference.md):
  Documents per-phase role → Superpowers-skill mapping. Phase-1 Reader uses `superpowers:brainstorming`, Phase-2 Skeptic uses `superpowers:test-driven-development`, Phase-3 Builder uses `superpowers:systematic-debugging` as escape route, Phase-4 Auditor uses `superpowers:verification-before-completion` + `superpowers:requesting-code-review`.

## Marketplace / release surface (current state)

- **`.claude-plugin/marketplace.json`** (current shape):
  ```json
  {
    "source": "github",
    "repo": "firaaz/cairn",
    "ref": "release"
  }
  ```
  (per m5-plugin-deployment-pattern D2; prior schema was broken, fixed in the ADR)

- **`dist/.claude-plugin/plugin.json`** (shipped structure):
  Manifest with explicit `version: "0.x.y"`. Consumer-visible version signal per D3 of m5-plugin-deployment-pattern.

- **`dist/` contents** (what the plugin actually ships, per m5-plugin-distribution-and-symlink-retire D3):
  - `.claude/skills/cairn-tdd-feature/` → `dist/skills/cairn-tdd-feature/`
  - `.claude/agents/{phase-{1..4}-tdd, triager-tdd}.md` + `role-topology.yaml` → `dist/agents/`
  - `checks/{reversibility-guard.sh, reality-check.sh, role_guard.py}` → `dist/checks/`
  - `templates/` (expanded with feature-plan.md, intent.md, sweep-notes.md, adr-frontmatter.yaml, active-envelope.yaml)
  - `dist/hooks/hooks.json` (hook registration per D4)
  - `dist/.claude-plugin/plugin.json` (plugin manifest)
  
  **Explicitly excluded** from `dist/`: `commands/claude-code/.local/`, `tests/`, `docs/adr/`, `docs/plans/`, `docs/reviews/`, `scripts/` (except _root.py + lib/ if needed), `pyproject.toml`, `uv.lock`, `.venv/`.

- **Hook registration** (dist/hooks/hooks.json per m5-plugin-deployment-pattern D4):
  No consumer `.claude/settings.json` merge required. Hook command strings resolve `${CLAUDE_PLUGIN_ROOT}` substitution.

- **Current pre-v1 version policy** (m5-plugin-deployment-pattern D2):
  Major version stays at `0` until the 6 pending amendment ADRs close. Consumers pin via `marketplace.json` `ref: "release"` (tracks branch HEAD) or `source.sha` (static commit pin).

- **Release workflow** (.github/workflows/release-publish.yml, implements m5-plugin-deployment-pattern D5/D6/D8):
  - Manually triggered via `workflow_dispatch` with `version` input.
  - Builds `dist/` payload.
  - Cross-checks `version` input against `dist/.claude-plugin/plugin.json:version` (D5).
  - Force-with-leases the `release` branch tree to match built payload (D6).
  - Tags the release as `v0.x.y` (D8).

## Hard constraints (must hold for any decision)

1. **Phase-pipeline shape is locked** (INV-003, phase-lock-and-role-declaration). Delivery-mechanism changes operate orthogonal to the four-phase execution, not modifying phase count/names/roles.

2. **Plugin distribution is locked to release-branch + marketplace** (INV-012, m5-plugin-deployment-pattern D1/D2). Consumer install is `/plugin marketplace add` + `/plugin install cairn@cairn-marketplace`; the release-branch + explicit-ref structure cannot change.

3. **Cairn maintainer dogfood loop must stay intact** (INV-011, m5-plugin-distribution-and-symlink-retire D8). Self-symlink `.slice-system → .` is preserved; maintainers iterate on hooks/skills/agents without republish-reinstall cycles.

4. **Role isolation in phase agents is fabrication-blocking** (framing Substrate non-negotiables). Delivery-mechanism cannot weaken per-role write-path enforcement (role_guard.py).

5. **ADRs remain append-only with supersession protocol** (framing Substrate non-negotiables, reversibility-guard.sh). Delivery changes cannot bypass ADR governance.

6. **Conventional Commits binding is machine-checkable** (INV-001). Any consumer-facing automation must produce commits with validated prefixes.

7. **Session-start context budget is ≤40k tokens** (INV-004). Setup-surface-up changes must be defended by evidence that they do not breach budget for fresh-session orientation.

8. **Handoff context discipline holds three tiers** (context-discipline-protocol, INV-002). Consumer onboarding cannot conflate Tier 1 (always) with Tier 2 (on-demand subagent) or Tier 3 (post-catchup).

## Soft constraints (preferences, can be traded)

1. **Slash-command progressive disclosure preferred over eager loading** (INV-004 spirit). Lite files (≤500 tokens) for discovery; `.full.md` siblings on explicit request.

2. **Audience-tagged split approach for CLAUDE.md / CONSUMER.md** (m5-plugin-distribution-and-symlink-retire D6). Cross-cutting rules tagged `[both]` in CLAUDE.md; consumer entry in separate CONSUMER.md.

3. **New deps require deliberate ADR** (cairn-substrate-and-fastmcp D2). Pyright, ast-grep, superpowers additions should be justified by ADR if shipped as consumer requirements.

4. **Structural enforcement > prompt-layer enforcement** (cairn-substrate-and-fastmcp D8 rationale, L-005). Post-install validator should run automated checks (hook presence, config sanity) rather than relying on consumer prose compliance.

5. **Mechanisms minimize setup ceremony** (m5-plugin-distribution-and-symlink-retire D4 consequence). Hook registration via hooks.json vs. consumer settings.json merge reduces friction.

6. **Bootstrap autonomy preferred over manual steps** (L-020 pattern). Post-install setup should execute automatically or emit `RAISE_ISSUE`; prose-specified side effects have latent cost.

## Explicit gaps (areas the constraint set DOES NOT speak to)

1. **Whether `using-cairn` SessionStart bootstrap skill is the highest-leverage item** (framing load-bearing claim 1). Constraint harvest shows INV-004's budget is shared resource; does not adjudicate whether SessionStart skill or /decision entry point is better discovery.

2. **Magnitude of practical setup friction pain** (framing load-bearing claim 2). Constraints show friction is paid per-machine; does not measure actual operator pain or adoption impact.

3. **Whether auto-routed subagents are better than slash-command surfacing** (framing load-bearing claim 3). Constraints document both surfaces exist (phase agents, slash commands); does not compare discoverability.

4. **Whether Pyright/ast-grep/ENABLE_LSP_TOOL are worth their setup cost** (framing load-bearing claim 4). Constraints show consumer-facing new-deps require ADR; does not evaluate the capability-vs-friction tradeoff.

5. **Whether external-plugin coupling (superpowers:systematic-debugging / defense-in-depth) should be hard, soft, or none** (framing sub-question 3). Constraints show Phase Skill Guide documents the mapping; does not prescribe coupling strength.

6. **Whether feature/workflow-subagents branch merges as-is, gets reworked, or deferred** (framing sub-question 4). Constraints specify plugin/delivery surface is locked; does not evaluate branch's specific additions against that surface.

7. **Consumer onboarding success metrics** (not addressed by ARCHITECTURE.md or ADRs). Constraint harvest has no evidence on operator time-to-dispatch, adoption rate, or friction pain severity.

8. **Whether post-install hooks should emit warnings/errors vs. silent no-op** (behavioral choice). Constraints require hooks to run; does not specify their chattiness.

## Tension watch (conflicts between cited items)

- **Context budget vs. setup-surface-up**: INV-004's 40k-token fresh-session budget is shared. Adding Pyright/ast-grep/superpowers discovery to initial context directly competes with cairn's own setup guidance (phase-skill-mapping, ARCHITECTURE.md snippets). Framing proposes both higher (more setup surface) and lower (less friction) directions; they cannot both increase context *and* stay under budget.

- **Prompt-only guidance vs. structural enforcement (L-005)**: Delivery changes proposing "consumers should run `ENABLE_LSP_TOOL=1`" or "read PREREQS.md before dispatch" face L-005's empirical finding that context pressure causes prose-compliance drift. Delivery-mechanism cannot resolve this via docs alone.

- **Plugin distribution is locked (INV-012) vs. distribution-direction decision**: Framing question asks "what is cairn's delivery-mechanism direction-of-travel?" but m5-plugin-deployment-pattern D1 locks the mechanism to release-branch + marketplace. The decision question operates within that constraint, not above it. Reframing may be required (e.g., "within release-branch + marketplace, should setup surface go up or down?").

- **Maintainer dogfood loop (INV-011, Path B) vs. consumer plugin-install simplicity**: m5-plugin-distribution-and-symlink-retire D8 preserves self-symlink for maintainers to avoid republish-reinstall cycles. The release-branch layout (shape without `dist/` subdirectory) makes maintainers and consumers consume different trees (dev vs. release). Divergence is intentional per D8 but adds edge-case risk (what if maintainer branch falls behind release?).

