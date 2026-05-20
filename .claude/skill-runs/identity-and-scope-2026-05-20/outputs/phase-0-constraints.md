# Phase 0 — Constraint Envelope

## Firm constraints (cannot be violated by any identity choice)

- **Four-phase pipeline is locked and non-negotiable.** The phase sequence (Intent/Reader → Validation/Skeptic → Implementation/Builder → Integration/Auditor) and phase names are load-bearing across hooks, dispatch skill, tests, and documentation. Changes require `phase-lock-and-role-declaration` supersession. — source: `docs/ARCHITECTURE.md:109–116`, `phase-lock-and-role-declaration.md` (firmness: firm, status: accepted)

- **Phase boundaries are enforced by git commits, not session state.** Each phase output is a committed artifact; the next phase cannot start until the previous one is merged. — source: `docs/spec-v1.md:86`, `docs/operational-reference.md:5`

- **Context discipline protocol enforces a three-tier model (INV-002, INV-004).** Handoff docs are bounded to 150–400 tokens with fixed section structure; slash commands use progressive disclosure; session-start context is ≤40k tokens. — source: `docs/ARCHITECTURE.md:22–57`

- **Substrate is markdown + Python + bash hooks, no runtime execution engine.** No orchestrator, no agent scheduling machinery. Dispatch is via skill invocation; phase transitions are via git commits. — source: `docs/ARCHITECTURE.md:120–124`, `cairn-substrate-and-fastmcp-superseded.md` (retired: kuzu, FastMCP, knowledge-graph query surface)

- **Primary user is the operator (Firaaz) doing cairn-on-cairn.** "Ordinary repositories" adoption has no external pull yet; no design commitment to multi-user or cross-team workflows. — source: `/decision` question doc, constraint 47

- **ADRs are append-only.** Overwrites are blocked; only frontmatter edits (status/firmness/superseded-by) are allowed. Supersession requires a new ADR. — source: `CLAUDE.md:22`, `reversibility-guard.sh` enforcement

- **The .slice-system symlink is bootstrap-exception (INV-011).** Cairn's own hook iteration requires self-consumption. Consumer projects use `/plugin install`; plugin-payload-transport-a1 governs dist delivery. — source: `docs/ARCHITECTURE.md:91–97` (INV-011), `m5-plugin-distribution-and-symlink-retire.md` (firm)

## Soft constraints (defaults; can be argued against)

- **Cairn framing is currently "high-consequence four-phase methodology" (scope: greenfield + documented modification extension).** The direction doc proposes shifting to "adaptive reliability layer with graduated tiers," but this is not yet decided. Current identity is load-bearing for existing tests, docs, and phase-skill mappings. — source: `docs/spec-v1.md:25–29`, `docs/operational-reference.md:1–5`, vs. `docs/plans/2026-05-19-adaptive-reliability-direction.md:7–17` (direction draft)

- **The primary target failure mode is the medium-scale AI-managed cliff.** cliff-failure-mode-and-v1-defenses defines D0, D1, D2, D3 defenses (provisional firmness). The spec enumerates nine failure modes (section 13); the ADR scopes Cairn to cliff-defense until dogfood. — source: `cliff-failure-mode-and-v1-defenses.md` (status: accepted, firmness: provisional), `docs/ARCHITECTURE.md:146`

- **Four-phase TDD flow via cairn-tdd-feature dispatch skill is the "primary" execution path.** However, `/decision` for architectural work and direct ad-hoc edits under operator envelope are also valid. No flow has exclusive scope yet. — source: `docs/operational-reference.md:19–29`, `CLAUDE.md:2–5`

## Identity-relevant signals (what the repo currently asserts about itself)

- **Cairn is a methodology repo: protocols, hooks, validators, skills, not a runtime framework.** No build step, no server, no agent orchestration. Consumed via symlink/plugin. — source: `CLAUDE.md:2`, `docs/operational-reference.md:1–3`

- **Value proposition: phase boundaries force clean role transitions and context resets.** Prevents authorship contamination and narrative momentum leakage. — source: `docs/spec-v1.md:33–56` (Core Thesis, scope: safety-critical work)

- **Scope is complex AI-assisted engineering only; overhead is waste on simple work.** CRUD, prototypes, AI wrappers explicitly out of scope. — source: `docs/spec-v1.md:25–27`

- **Greenfield-first; modification slices documented but undefended (discipline-only).** No hook enforces the "read public interfaces only" rule for modification work. — source: `docs/spec-v1.md:29`, `docs/operational-reference.md:89` (incident #4 at spec-v1 §14)

- **M4 cairn-shrink (2026-05-07) retired substrate machinery:** knowledge graph, FastMCP MCP, kuzu/mistune deps, INV-010 read-class lockdown. Standing dep set is now pydantic + typer + pyyaml only. — source: `cairn-substrate-and-fastmcp-superseded.md` (firm), `CLAUDE.md:30`

- **Parallelism-v1 (provisional) returned concurrent slice execution to v1 scope.** Slices without unmet `after:` dependencies can run in parallel on separate branches. — source: `parallelism-v1.md` (status: accepted, firmness: provisional)

- **Feature-slice model (firm) decomposes work into features (units of intent) containing slices (units of execution).** Slice state is branch-local; feature files live at `.claude/features/<id>.yaml`. — source: `feature-slice-model.md` (firmness: firm), `docs/ARCHITECTURE.md:117–119`

## Conflicts / drift detected

- **Handoff model mismatch:** `.claude/handoff.md` is currently shaped as a contract (frontmatter + pointers), but INV-002 still names the old sectioned narrative shape (State/Next/Blocked/Pointers + forbidden sections). Trial A proposed the contract model; rebaseline is pending. — source: `docs/ARCHITECTURE.md:22–40` (INV-002, binding-effective-from: `<pending-slice-close-sha>`), vs. `docs/plans/2026-05-19-adaptive-reliability-direction.md:200–209` (lists three failing tests)

- **Invariant coverage gap:** ARCHITECTURE.md has INV-011 and INV-012 (released 2026-05-08+), but some tests still expect only INV-001..INV-010. — source: `docs/ARCHITECTURE.md:91–105`, vs. `docs/plans/2026-05-19-adaptive-reliability-direction.md:206–207`

- **Doctrine split on Tier 0/1 utility:** Direction doc questions whether low-risk hygiene (Tier 0) and scoped-work guardrails (Tier 1) are valuable for "ordinary repositories." Current CLAUDE.md and spec-v1 frame Cairn as "complex engineering only." If Tier 0/1 are adopted, that frames Cairn as a graduated system for all projects, not just complex ones. — source: `docs/plans/2026-05-19-adaptive-reliability-direction.md:10–17, 44, 87–107` (B vs. status quo)

## Open questions surfaced

- **Clause 1 from the direction doc:** Does the tier model solve the adoption problem (broad-audience mindset) without diluting Cairn's reliability promise (complex-engineering focus)? The two premises may be contradictory.

- **Clause 3 from the direction doc:** Is Tier 3 (formal flow) still meaningfully different from "just use Claude/Codex carefully," or has native Claude Code/Codex infrastructure (hooks, skills, operators, MCP) absorbed the same value? This touches whether Cairn remains a coherent product or becomes a set of optional overlays.

- **Clause 4 from the direction doc:** Should tiers be selected by deterministic scoring, user declaration, or both? The proposed heuristic (problem.md:156–185) is deterministic; the operator override is declaration. This is a product-design choice not yet decided.

- **Clause 6 from the direction doc:** Which failing tests are evidence the direction is wrong vs. evidence that the current `dev` branch is in a stale rebaseline state? The direction doc claims the latter; decision needs to evaluate this.

- **Relationship to spec-v1 identity:** If identity shifts from methodology (four-phase-only, high-consequence framing) to graduated reliability layer, does spec-v1 §1 scope clause ("not for simple software") change? Who is the user: the complex-engineering operator, or any operator selecting their tier?

EOF
cat /Users/firaazfarook/Developer/github.com/firaaz/cairn/.claude/skill-runs/identity-and-scope-2026-05-20/outputs/phase-0-constraints.md
