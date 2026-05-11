# Architecture

System: cairn — slice-based development methodology tool
Phase: pre-v1 (solo development, meta-dogfood bootstrap complete; see `docs/roadmap.md`)
Primary target failure mode: the medium-scale AI-managed cliff (cliff-failure-mode-and-v1-defenses D0)
Phase pipeline: four-phase lock with named roles (phase-lock-and-role-declaration)
Feature model: feature-slice decomposition with structured dependencies (feature-slice-model)

This document is a **derived view** synthesized from the ADR corpus in `docs/adr/`. It is validated by `scripts/validate_architecture.py`. Manual edits are permitted as part of an ADR-supersession-justified commit; no automated `/refresh-architecture` step exists post-M4 cairn-shrink.

## Invariants

**INV-001** All cairn development after the bootstrap commit produces commits whose Conventional Commits prefixes are recognised in the validator's `_FALLBACK_REGISTRY` (`scripts/validate_architecture.py`). Direct commits with unregistered prefixes are not permitted except as recorded in a superseding ADR. The registered set spans `/decision`, the `cairn-tdd-feature` dispatch skill, and operator-envelope-gated direct work. True machine-checkable binding via `git-log-walk` assertion type per `invariant-binding-strategy` (D1–D3), landed at `2fb83f6` with `binding-effective-from: 2fb83f6`. The prior registry file `.claude/pipeline-substrate-registry.yaml` was retired in M4 cairn-shrink (2026-05-07); the validator now uses the inline fallback. (bootstrap-exception; pipeline-substrate-naming-superseded; invariant-binding-strategy)

```invariant-check INV-001
type: git-log-walk
binding-effective-from: 2fb83f6faec4d95c53211e2cef8d0bc6dbf061ba
registry: null
description: "True INV-001 binding via authorization-by-name walk over commits since binding-effective-from. Registry file retired per pipeline-substrate-naming-superseded; validator falls back to inline prefix list in _FALLBACK_REGISTRY."
```

**INV-002** Session-to-session context transfer obeys structural discipline on `.claude/handoff.md`: a pointer artifact bounded at 150–400 tokens with fixed section structure (`State`, `Next`, `Blocked / Pending`, `Pointers`; `Features` optional) and a forbidden-sections list (literal: "What This Session Was About", "What Was Accomplished", "Surprises or Discoveries", "Self-Check"; regex: `^##\s+(Lessons|Reflection|Notes)\b`). True machine-checkable binding via `structural-parser` assertion type defined by `invariant-binding-strategy` (D1, D4); per-feature plan docs at `docs/plans/<feature>.md` carry session-spanning context that previously spread across `/catchup`'s Tier-1 list and `/start-slice`'s current-slice/ wipe (both retired in M4 cairn-shrink, 2026-05-07). (context-discipline-protocol; invariant-binding-strategy; slice-close-contract-superseded)

```invariant-check INV-002
type: structural-parser
target: ".claude/handoff.md"
required-sections: ["State", "Next", "Blocked / Pending", "Pointers"]
optional-sections: ["Features"]
forbidden-sections:
  literal: ["What This Session Was About", "What Was Accomplished", "Surprises or Discoveries", "Self-Check"]
  regex: ['^##\s+(Lessons|Reflection|Notes)\b']
forbidden-content:
  regex: ['I (was|am|will|just) ', '\d+\s*/\s*\d+\s+(passed|failed|tests)']
token-budget:
  approximation: bytes-per-token-4
  warn-at: 360
  fail-at: 440
binding-effective-from: 1c4d2f5a0189999452dfdcc24d1e03bcf50978ed
description: "INV-002(a) handoff structural binding per ADR invariant-binding-strategy D4"
```

**INV-003** Every cairn-tdd feature runs through exactly four phases in order — Intent (Reader), Validation (Skeptic), Implementation (Builder), Integration (Auditor). Each phase's role and anti-behaviors are surfaced in the agent prompts at `.claude/agents/phase-{1..4}-tdd.md` and the Phase Skill Guide section of `docs/operational-reference.md`. Phase count, names, and role assignments are locked; changes require a superseding ADR. Role-keyed write-path enforcement via `checks/role_guard.py` is preserved across the M4 shrink (envelope-grant escape and `READ_CLASS_TOOLS` constants intact). (phase-lock-and-role-declaration; phase-pipeline-evaluation; compression-infrastructure-bootstrap-superseded)

```invariant-check INV-003
type: test-ref
pattern: "tests/unit/test_inv_003_phase_topology.py"
validate_phase_topology: "scripts/validate_architecture.py"
description: "Three-way cross-reference phase-topology binding: (phase_ordinal, role_slug) topology agreed across .claude/agents/role-topology.yaml (authoritative), Phase Skill Guide (docs/operational-reference.md), and agent prompt filenames (.claude/agents/phase-{1..4}-tdd.md). validate_phase_topology() in scripts/validate_architecture.py is the binding entry point; tests/unit/test_inv_003_phase_topology.py is the binding test suite. ROLE_DENY_READ cross-reference dropped (read-class lockdown retired with the substrate; see INV-010 retirement)."
```

**INV-004** Session-start context on a fresh prompt in cairn uses ≤40,000 total tokens (input + cache_creation + cache_read). Slash commands use progressive disclosure: each command has a lite file (≤500 tokens, always loaded) and an optional `.full.md` sibling loaded only on discrete predicates. Machine-checked by `tests/unit/test_context_budget.py`. Re-baselined by `housekeeping/inv004-rebaseline` (2026-04-16) for Claude Code 2.1.110, which added ~8k tokens of system-prompt overhead outside cairn's control. Re-baselined again by `housekeeping/inv004-rebaseline-cc-2.1.116` (2026-04-21) for Claude Code 2.1.116, which added another ~583 tokens of system-prompt overhead outside cairn's control (observed 30,170-30,353 turn-1 tokens under CC 2.1.116 per sweep #22 section 1). (context-discipline-protocol; dedicated ADR pending after 2+ slices of progressive-disclosure use)

```invariant-check INV-004
type: test-ref
pattern: "tests/unit/test_context_budget.py"
description: "Points to the test suite that machine-checks the 40k token budget"
```

**INV-005** All cross-referenceable entities (ADRs, slices, features, decision points) carry a two-field identity model: an immutable `id:` (mechanical — used by hooks, filenames, cross-reference fields) and a mutable `name:` (human/LLM-facing prose label). ADR and feature `id:` shapes are flat semantic slugs; slice and decision-point `id:` shapes are hierarchical (`<feature>/<slice>`, `<adr-id>/<decision-slug>`). Hooks (`reversibility-guard.sh`, `reality-check.sh`, `role_guard.py`) and the validator tolerate both legacy `NNN-slug` filenames and flat-slug filenames during the migration window. Governing ADR: `identifier-scheme` (firm/accepted; supersedes the prior single-field naming ADR). Validator-anchored via the operationally dependent feature-slice model. (identifier-scheme)

```invariant-check INV-005
type: file-exists
target: "docs/adr/identifier-scheme.md"
description: "Verifies the two-field identifier scheme governing ADR exists"
```

**INV-006** Every piece of work decomposes into a feature (the unit of intent) containing one or more slices (the unit of execution). Each feature has a file at `.claude/features/<id>.yaml` carrying the slice list with `after` dependency fields, feature intent, and creation date. Even single-slice features get a feature file (always-create policy). State lives in exactly one file with no duplication; slice status is derived from observable state (branch existence, merge state, `parked` flag), not stored — except `dropped`, which is the one stored exception. (feature-slice-model)

```invariant-check INV-006
type: file-exists
target: ".claude/features/*.yaml"
description: "Verifies at least one feature file exists under .claude/features/"
```

**INV-007** Feature-slice artifacts integrate into context-discipline-protocol's three-tier context model without creating a new tier or amending INV-002: `handoff.md` gains a cross-feature index at Tier 1 (within the 150–400 token budget), feature files load as Tier 2 on-demand reads gated by existing admission criteria, and `slice.yaml` remains Tier 3 working context. Beyond ~5 concurrent features the token budget may bind — this is a named v1 scalability ceiling, not a defect. (context-tiers-integration)

```invariant-check INV-007
type: grep
pattern: '\.claude/features/'
target: ".claude/skills/cairn-tdd-feature/SKILL.md"
expect: match
description: "Verifies the dispatch skill references feature files for context integration"
```

**INV-008** Retired by ADR `slice-close-contract-superseded` (M4 cairn-shrink, 2026-05-07). The orchestrator's slice-close lifecycle no longer exists; per-phase commits via the cairn-tdd-feature dispatch skill replace the close_slice ceremony, and slice-artifact preservation is subsumed by git history of merged branches. (slice-close-contract-superseded; slice-artifact-preservation-superseded)

**INV-009** Retired (advisory-only at introduction; never promoted to firm; M4 cairn-shrink, 2026-05-07). Per-slice cost telemetry retires with the slice unit-of-work; cost data remains observable natively via Claude Code's session telemetry. ADR `cost-per-slice-budget` is amended (Task B6 / Task C-followup) to mark the threshold mechanization deprecated. (cost-per-slice-budget; orchestrator-observability-superseded)

**INV-010** Retired by ADR `cairn-substrate-and-fastmcp-superseded` (M4 cairn-shrink, 2026-05-07). The cairn-knowledge MCP server, scripts/cairn_query/, and the canonical-knowledge read-class lockdown table retire with the substrate. Phase agents read canonical sources directly within their per-role write-path allowlists; the dispatch skill quotes relevant ADR/invariant snippets in spawn prompts to recover the substrate's targeted-context value. (cairn-substrate-and-fastmcp-superseded; compression-infrastructure-bootstrap-superseded)

**INV-011** Cairn-the-repo retains a local self-consumption mechanism so maintainers can iterate on hook scripts (`checks/*`), the dispatch skill (`.claude/skills/cairn-tdd-feature/`), and phase agents (`.claude/agents/phase-{1..4}-tdd*.md`) without going through plugin republish-reinstall-restart cycles. Currently implemented as the `.slice-system → .` self-symlink at the repo root; alternatives (e.g., direct path resolution, plugin-installs-itself) are permitted only via superseding ADR. This is the bootstrap-circularity defense named by Pre-mortem Scenario 3 of `m5-plugin-distribution-and-symlink-retire`: maintainers editing cairn's own hooks while cairn's hooks gate the edits cannot work if the running hook is the plugin-cached copy. Plugin consumers are unaffected — they install via `/plugin install cairn@cairn-marketplace` per `m5-plugin-distribution-and-symlink-retire` D1. M6/F3 explicitly excludes cairn-the-repo from the downstream-consumer migration: the `scripts/migrate_from_symlink.sh` helper aborts with exit 3 if it detects a self-symlink target of `.`, and the retire-docs sweep preserves cairn-the-repo's self-symlink documentation. (m5-plugin-distribution-and-symlink-retire; bootstrap-exception)

```invariant-check INV-011
type: file-exists
target: ".slice-system"
description: "Verifies the .slice-system self-consumption mechanism exists at the cairn-the-repo root, enabling cairn maintainers to iterate on hooks/skills/agents without plugin republish-reinstall cycles."
```

**INV-012** Cairn's plugin payload deploys via a self-marketplace shape: `.claude-plugin/marketplace.json` carries `source: "./dist"` (string-relative-path, matching 49 of Anthropic's reference-marketplace plugins). Consumers' `/plugin marketplace add https://github.com/firaaz/cairn` HTTPS-clones the repo to `~/.claude/plugins/marketplaces/cairn-marketplace/`; `/plugin install cairn@cairn-marketplace` is a filesystem copy from `./dist/` in that clone. There is no second clone, no URL for the resolver to host-coerce, and the SSH-forcing failure mode documented at V-3 attempts 1 + 2 (and in upstream Claude Code issues #26588 / #47088 / #50725) is structurally unreachable. `dev`-tip carrying committed-current `dist/` is the authoritative consumer install target; `release` branch is retained as archaeology + tag anchor (per `m5-plugin-deployment-pattern/D8`) but is no longer the install target. Consumer-visible update signal is `dist/.claude-plugin/plugin.json:version`; manual semver bumps per `m5-plugin-distribution-and-symlink-retire/D2`. CI: `dist-gate.yml` escalated to mandatory (stale-`dist/` is a release blocker); `release-publish.yml` retains force-with-lease on `release` and tag creation, no two-step coupling. Provisional pending the A3a empirical probe (install + update cycles in a fresh consumer session); fallback if probe falsifies is named in `plugin-payload-transport/D9` (document SSH-key prerequisite). (plugin-payload-transport; m5-plugin-deployment-pattern; m5-plugin-distribution-and-symlink-retire)

```invariant-check INV-012
type: test-ref
pattern: "tests/unit/test_marketplace_schema.py"
description: "Schema-shape lint binding for INV-012's marketplace.json self-marketplace contract: plugins[0].source == './dist' (string-relative-path), ./dist resolves to a directory containing .claude-plugin/plugin.json, no version on the marketplace plugin entry, no legacy type==git field. Assertions in tests/unit/test_marketplace_schema.py per plugin-payload-transport/D5 (replaces the url+ref schema set after V-3 attempt 2 falsified the url-source path)."
```

## Boundaries

The slice pipeline has four phase boundaries, each implemented as a fresh session separated by a committed artifact (phase-lock-and-role-declaration D1):

1. **Intent → Validation** — Phase 1 Reader commits `intent.md`, AND every ADR named in `intent.md`'s `adrs-referenced` field exists as a committed file in `docs/adr/` (phase-lock-and-role-declaration D3 structural-immutability gate).
2. **Validation → Implementation** — Phase 2 Skeptic commits test files matching the envelope's test patterns.
3. **Implementation → Integration** — Phase 3 Builder commits source files within the declared envelope.
4. **Integration → complete** — Phase 4 Auditor commits sweep notes with a PASS verdict on declared invariants backed by `file:line` citation evidence; on implementation failure, the slice is marked `failed` per `docs/spec-v1.md` §13 item 8, not patched.

The four phase names (Intent, Validation, Implementation, Integration) and role names (Reader, Skeptic, Builder, Auditor) are load-bearing for `/catchup`, the `cairn-tdd-feature` dispatch skill (`.claude/skills/cairn-tdd-feature/SKILL.md`), the canonical agent prompts under `.claude/agents/phase-{1..4}-tdd.md`, `.claude/agents/role-topology.yaml`, `checks/reality-check.sh`, and `docs/operational-reference.md` — all string-match on the phase names. Renames are not refactors; they require phase-lock-and-role-declaration supersession.

Work is organized as features containing slices (feature-slice-model). Features are the unit of intent; slices are the unit of execution. Within a feature, slice ordering is governed by `after` fields in the feature file. Slices without unmet `after` constraints can run concurrently on separate branches (parallelism-v1, provisional). Feature files live on the feature branch; slice state lives on the slice branch. There is no global active-slice pointer — state is branch-local (parallelism-v1 D2).

Beyond the pipeline, cairn has no runtime module boundaries. The substrate is markdown protocols, shell hooks, and a Python validator (see Data Ownership).

## Data Ownership

Cairn has no runtime data. The substrate is files on disk: shell hooks in `checks/`, slash commands in `commands/claude-code/`, the validator in `scripts/`, documentation in `docs/`, per-feature dispatch artifacts under `.claude/skill-runs/<feature-id>/` when the `cairn-tdd-feature` skill is mid-run, and feature files at `.claude/features/<id>.yaml` (feature-slice-model D1). Ownership of each path is specified by its location, not by module convention.

A further substrate file is reserved by context-discipline-protocol Consequences: `.claude/learning.md` (append-only staging ground for post-feature learnings). The `.claude/d1-bypasses.log` path was reserved by cliff-failure-mode-and-v1-defenses D1 and is retired with D1 in M4 cairn-shrink (2026-05-07).

The substrate paths reserved by orchestrator-observability and slice-close-contract retire with M4 cairn-shrink (2026-05-07): `.claude/orchestrator-debug/**`, `.claude/current-slice/.heartbeat`, the per-slice `<slug>-result.json` / `<slug>-result.md` / `<slug>-phase-{N}-{role}-{ts}.log` failure logs, and the `index.jsonl` event stream are no longer written. Per-feature dispatch artifacts under `.claude/skill-runs/<feature-id>/` replace the orchestrator-debug surface; cleanup of these is operator-discretion (no rotation policy and no D8-style tripwire). See `orchestrator-observability-superseded` and `slice-close-contract-superseded`.

`docs/operational-reference.md § Phase Skill Guide` is the living registry of per-phase role anti-behaviors and recommended Superpowers skills, reserved by phase-lock-and-role-declaration D4. Created by the `phase-lock-and-role-declaration` operationalization slice; updated by normal documentation commits without ADR supersession.

## Current Phase Constraints

**Phase shape is firmly locked at four phases (phase-lock-and-role-declaration).** The slice pipeline is `Intent (Reader) → Validation (Skeptic) → Implementation (Builder) → Integration (Auditor)`. Phase count, names, and roles are fixed; changes require phase-lock-and-role-declaration supersession. Roles carry anti-behaviors declared in protocol text and surfaced at phase entry by the `cairn-tdd-feature` dispatch skill (`.claude/skills/cairn-tdd-feature/SKILL.md`) and the canonical agent prompts under `.claude/agents/phase-{1..4}-tdd.md`. The Risk Register's A2 tripwire — novel design tokens appearing in any slice's Phase 2 `approach.md` that are absent from the committed `intent.md`, where more than 1 slice in a rolling 10-slice window fires the canary — is the mechanical supersession trigger toward the preserved Approach B (5-phase RIPER split) if dogfood reveals that the Phase 1→Phase 2 session boundary fails to prevent Intent-conflation. Commitment #5 (plastic phases) is resolved; commitment #6 (explicit roles) is resolved at the textual layer, with mechanization deferred to v2+ per cliff-failure-mode-and-v1-defenses D4.

**Pre-v1 scope is governed by cliff-failure-mode-and-v1-defenses (provisional).** Every pre-v1 slice after 2026-04-11 must either declare in `intent.md` which of D0/D1/D2/D3 it implements, or mark itself as a non-v1-scope waiver. The legibility criterion is: *does this contribute to D1, D2, or D3? If not, it is deferred to v2.* cliff-failure-mode-and-v1-defenses and phase-lock-and-role-declaration deliberately carry different firmnesses — cliff-failure-mode-and-v1-defenses provisional because the cliff framing and defense set are expected to be superseded after dogfood; phase-lock-and-role-declaration firm because the phase shape is load-bearing for every downstream slice and supersession cost rises linearly with the number of slices built on it. The two ADRs resolve different classes of uncertainty.

**The three v1 defense commitments (cliff-failure-mode-and-v1-defenses D1/D2/D3):**

- **D1 — automated architecture refresh: retired in M4 cairn-shrink (2026-05-07).** The auto-refresh-on-slice-close mechanism retires with the orchestrator close ceremony; manual `ARCHITECTURE.md` edits are now the path, gated by `reversibility-guard.sh`'s ADR append-only enforcement on the underlying ADR corpus. `ADR_D1_BYPASS=1` retires with D1. cliff-failure-mode-and-v1-defenses D1 is amended (queued amendment ADR) to reflect this; until that ADR lands, treat this paragraph as the authoritative surface.

- **D2 — code↔invariant binding.** Every firm invariant carries a machine-checkable assertion (AST-level, schema-level, or strict-grep with anchoring). The validator runs assertions on each refresh and flags code that violates a declared invariant. Invariants that cannot be machine-checked at introduction time are marked `firmness: advisory` and do not count toward v1 defense satisfaction. **Binding strategy ADR landed 2026-05-02** (`invariant-binding-strategy` co-landing with `pipeline-substrate-naming`): two new validator types (`git-log-walk`, `structural-parser`) plus `test-ref` delegation graduate INV-001 and INV-002 from advisory proxies to true bindings. Implementation slice not yet landed — until then, INV-001 and INV-002 continue to carry their deletion-detection proxy assertion blocks. INV-003 carries a true three-way phase-topology binding (`validate_phase_topology` in `scripts/validate_architecture.py`), landed in the same D2 wave. phase-lock-and-role-declaration's A2 canary is scoped separately from D2 but will migrate to D2's assertion runner when D2 lands.

- **D3 — automated unknown-unknown backstop: retired in M4 cairn-shrink (2026-05-07).** `/integration-sweep`, the `.claude/d3-bypasses.log` substrate, `scripts/snapshot_diff.py`, and the rolling-window `3-in-10 → design-review` false-positive trigger retire with the integration-sweep command and the orchestrator close ceremony. Auditor (Phase 4) per-feature integration via the `cairn-tdd-feature` dispatch skill subsumes the per-slice half of D3; the cross-slice / structural-snapshot-diff backstop returns to v2+ scope. cliff-failure-mode-and-v1-defenses D3 is amended (queued amendment ADR) to reflect this. `d3-bypass-classification-superseded` supersedes the bypass schema.

**D0** names the medium-scale AI-managed cliff as cairn's primary target failure mode, into which `docs/spec-v1.md` §13's nine enumerated failure modes compose as aggravators or components rather than parallel targets.

**D4 v1 time-box (cliff-failure-mode-and-v1-defenses, partially superseded by parallelism-v1).** The following `docs/vision.md` success criteria and roadmap items are superseded for v1 purposes only and return as v2+ scope: vision commitment #1 (Windsurf portability and split-agent slices), spec-v1 §9 three-track routing, commitment #6 mechanization (roles stay instructed, not hook-enforced), retroactive invariant enforcement against existing code, slice pause/resume as a built-in command (partially addressed by feature-slice-model D6 parked-state protocol), and cached-mind size management / `ARCHITECTURE.md` chunking. **Vision commitment #2 (parallelism-native) has returned to v1 scope via parallelism-v1** — concurrent slice execution is v1-legal when slices have no unmet `after` constraints. Any pre-v1 slice touching a remaining time-boxed area must declare explicit non-v1-scope waiver in `intent.md` or be rejected. **Commitment #5 (phase rethink) is resolved by phase-lock-and-role-declaration and no longer on the pre-v1 critical path.**

**Identifier scheme (identifier-scheme ADR; supersedes semantic-identity).** All cross-referenceable entities — ADRs, slices, features, decision points — carry a two-field identity: immutable `id:` (mechanical) and mutable `name:` (human-facing). ADR IDs are flat semantic slugs (`identifier-scheme`); slice IDs are hierarchical `<feature>/<slice>` (`identifier-scheme/scheme-adr`); decision-point IDs are hierarchical `<adr-id>/<decision-slug>` (`identifier-scheme/d2-id-shape`); feature IDs are flat slugs (`identifier-scheme`). Migration is three-phase: Phase 1 additive (no renames), Phase 2 one-shot rename sweep, Phase 3 drop legacy-format tolerance (deferred indefinitely per the governing ADR's D7). Currently in Phase 1 — both legacy `NNN-slug` and flat-slug naming coexist. Substrate support for the mixed-shape window landed across the identifier-scheme feature: `hook-tolerance` widened `scope-guard.sh` / `reversibility-guard.sh` / `reality-check.sh` globs to accept flat-slug ADR filenames; `hook-relpath-bypass` normalized bare-relative and `.slice-system/`-prefixed tool-input paths so `reversibility-guard.sh` cannot be bypassed; `validator-flat-slug` widened `scripts/validate_architecture.py` to resolve both ADR filename shapes and recognize flat-slug IDs in `**INV-NNN**` / `(adr-id)` references. INV-005 anchors to `identifier-scheme` directly — no validator proxy required. The identifier-scheme feature is drained for Phase 1.

**Feature-slice model (feature-slice-model, context-tiers-integration).** Work is organized as features containing slices. Feature files at `.claude/features/<id>.yaml` carry structured decomposition with `after` dependency fields. Feature-slice artifacts integrate into context-discipline-protocol's three-tier context model: cross-feature index in `handoff.md` (Tier 1), feature files on-demand (Tier 2), `slice.yaml` as working context (Tier 3). No new tier is introduced; INV-002 is unaffected.

**Parallelism (parallelism-v1, provisional).** Concurrent slice execution is v1-legal. Slices without unmet `after` constraints can run in parallel on separate branches. State is branch-local; there is no global active-slice pointer. `dispatching-parallel-agents` and `using-git-worktrees` Superpowers skills return to the Phase Skill Guide. All other cliff-failure-mode-and-v1-defenses D4 time-boxed items remain deferred except as noted above. parallelism-v1 is provisional — the first concurrent-slice execution is the validation event; persistent merge conflicts or state corruption trigger supersession.

**Role-keyed write-path enforcement (compression-infrastructure-bootstrap-superseded, post-M4).** `checks/role_guard.py` is a PreToolUse hook on `Write`/`Edit`/`MultiEdit`/`NotebookEdit`. Two paths: (a) when `AGENT_ROLE` is set (dispatch-skill subagents), the hook enforces a per-role write allowlist plus an envelope-grant escape via `AGENT_ENVELOPE` (D9); `phase-3-tdd` has no static allowlist and is envelope-driven (intentional asymmetry per `compression-infrastructure-bootstrap-superseded`). (b) When `AGENT_ROLE` is unset (operator session), the hook reads `.claude/active-envelope.yaml`; `mode: operator` enforces writes against `paths:`, `mode: off` is no-op, malformed YAML or unrecognised mode fails closed. INV-003's three-way binding (`validate_phase_topology`) tests the role topology cross-reference.

**Slice-close lifecycle — retired (slice-close-contract-superseded, orchestrator-observability-superseded, 2026-05-07).** The pre-M4 close_slice contract and orchestrator-observability schema retire with the slice machinery. The dispatch skill (`.claude/skills/cairn-tdd-feature/SKILL.md`) commits each phase's writes by name; there is no separate close ceremony, no .claude/orchestrator-debug/ output, and no resume reconciliation matrix.

**Board as roadmap substrate (board-as-roadmap-substrate, provisional).** Cairn's planning surface is layered as four stacked substrates: (1) the GH Project board (name `cairn`, account-owned) is the front-door catchment for un-committed ideas and roadmap items; (2) `.claude/features/<id>.yaml` is the feature commitment register; (3) the `cairn-tdd-feature` dispatch skill plus the per-feature plan doc at `docs/plans/<feature>.md` is the execution engine; (4) `docs/lessons.md`, `.claude/handoff.md`, and operator memory are permanent / churning memory. The board is never a mirror of cairn-side state — it is its own truth (what could be worked on); cairn-side state remains derived per `feature-slice-model/d4-status-derived`. The pre-M4 `/start-slice`/`/close-slice` board-pending queue (`.claude/board-pending.log`) and the `slice.yaml`-keyed `issue-number:`/`board-item-id:` schema additions retire in M4 cairn-shrink (2026-05-07); board-as-roadmap-substrate is queued for amendment to refit the post-shrink execution engine. PM-session commands (`/groom`, `/promote`, `/weekly-status`, `/board-sync`) start in `commands/claude-code/.local/` per the `/dev-mode` precedent and do not ship to consumers. Parent-issue creation for features is **lazy** (at first-feature-open), not eager. Non-v1-scope per `cliff-failure-mode-and-v1-defenses/d4-time-box`. ADR is provisional with a dogfood gate at 10 features using the system OR 2026-10-11 (whichever first); six failure-mode tripwires named in the ADR's risk register guide promotion, amendment, or supersession at the gate.

**Provisional firmness and dogfood.** cliff-failure-mode-and-v1-defenses is explicitly expected to be superseded. The dogfood target is cairn reaching 10 completed slices post-cliff-failure-mode-and-v1-defenses OR 2026-10-11 (whichever first). Dogfood passes if D1/D2/D3 together catch ≥1 class of drift that integration-sweep Step 3 manual check would have missed, and no defense has false-positive rate high enough to force muting. Three supersession outcomes are planned and acceptable: promote (to firm), amend (add/remove/replace defenses), or reframe (different primary target). Until dogfood completes, no slice beyond D1/D2/D3's own design slices may take a hard dependency on the provisional defenses. phase-lock-and-role-declaration's firm lock is independent of this dogfood gate — phase-lock-and-role-declaration is superseded only by its own A2 tripwire (not by cliff-failure-mode-and-v1-defenses's dogfood outcome).
