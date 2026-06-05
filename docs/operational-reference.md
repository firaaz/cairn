# Development System

Operational reference for cairn's post-shrink development pipeline. Cairn is a methodology repo: protocols, hooks, slash commands, a Python validator, and a TDD-by-construction dispatch skill. It is consumed by other projects via a `.slice-system → .` symlink. **For the canonical spec (theory, failure modes, empirical support), load `docs/spec-v1.md` on demand** — that document is the canonical spec.

A feature in cairn is a vertical change that goes through four phases: Intent → Validation → Implementation → Integration. Each phase runs in a fresh subagent dispatched by the `cairn-tdd-feature` skill, takes a declared input artifact, and commits a declared output artifact. Phase transitions are enforced by git commits, not by session state.

## Bootstrap

After cloning or pulling cairn on any machine:

```bash
uv sync                                          # recreates .venv and uv.lock
uv run pytest -q                                 # baseline (expect 360/0/2)
uv run python scripts/validate_architecture.py   # expect ALL CHECKS PASSED
bash scripts/smoketest_hooks.sh                  # expect PASS role_guard.py
cat .claude/handoff.md                           # orient
```

## Routing: ad-hoc vs decision vs cairn-intent loop vs cairn-tdd-feature dispatch

Four paths:

- **Ad-hoc edit** (one-line fix, doc tweak, multi-file refactor with no clear failing-test shape): just edit. The operator envelope at `.claude/active-envelope.yaml` gates writes — set `mode: operator` + a `paths:` regex list for focused work, `mode: off` for ad-hoc / cross-cutting work. Commit with a Conventional Commits prefix from the validator's `_FALLBACK_REGISTRY` (`feat:`/`fix:`/`chore:`/`docs:`/`test:`/`slice:`/`handoff:`/`sweep:`/`bootstrap:`/`design:`/`plan:`; scoped `chore(scope):` accepted).
- **Architectural decision** (touches invariants, boundaries, data ownership, module structure): `/decision <question>`, then `/new-adr` to write the ADR. ADRs are append-only — `reversibility-guard.sh` blocks overwrites; frontmatter-only `Edit` is allowed; supersession via a new ADR with `supersedes: <id>`. Manual `docs/ARCHITECTURE.md` edits accompany the ADR.
- **Intent-managed loop** (default for repo-writing work — a durable intent contract anchoring fluid, test-first construction in the current session): invoke the `cairn-intent` skill. It forms the contract from `templates/intent.md`, runs a fresh-context `intent-challenge` before construction and a fresh-context `close-review` before close, and stays in one conversation rather than dispatching per-phase subagents. cairn-internal only; the `using-cairn` SessionStart carrier names the active intent.
- **Feature with TDD discipline** (vertical behavior change with a clear failing-test shape): write a per-feature plan at `docs/plans/<date>-<feature-id>.md` with frontmatter `id:` + `envelope:` regex array + What/Why/Boundary/Specification/Verification sections. Then invoke the `cairn-tdd-feature` dispatch skill via the Skill tool with the plan path as args. The skill runs all four phases as fresh subagents and produces four commits + workspace artifacts under `.claude/skill-runs/<feature-id>/`.

Rule of thumb: if the work could change what downstream features can assume, it needs `/decision`. If it only fills in detail within an existing assumption, operate via the cairn-intent loop (or the `cairn-tdd-feature` dispatch skill for strict per-phase isolation; direct edit for ad-hoc work).

`/catchup` is the session-orientation slash command — reads `.claude/handoff.md`, `git log`, `git status`, and `.claude/active-envelope.yaml`, then stops. The operator drives next.

## Git workflow (`git-workflow-v1`)

Governs the `dev`-side working-branch/merge/naming model (the `dev`→`release`→tag distribution boundary is `m5-plugin-distribution-and-symlink-retire`, separate). Branch lifecycle is **operator-owned**; the dispatch skill is branch-agnostic and commits to HEAD.

- **Branch-per-unit (D1).** Every feature runs on a `feat/<feature-id>` branch cut from `dev`, at the point that becomes the skill's `SNAPSHOT_SHA`. Per `cairn-intent-git-lifecycle`, the same `feat/<id>` + `--no-ff` rule applies **uniformly** to `cairn-intent` intents — the unit is any repo-writing unit of work, feature or intent. Instructed, not hook-enforced — a direct-to-`dev` commit stays INV-001-valid (operator-envelope-gated ad-hoc / read-only work is the legal fast path), but intent-bearing repo-writing work belongs on a branch.
- **Integrate with `git merge --no-ff feat/<feature-id>` (D2).** After Phase 4 passes. Never `-ff`, never `--squash` — those collapse the four phase commits that the audit chain (`intent.md`/`sweep-notes`/handoff anchored on `SNAPSHOT_SHA`) depends on. Never rebase a feature branch mid-work (rewrites the phase SHAs); if `dev` advanced, the `--no-ff` 3-way merge integrates it.
- **Merge commits are validator-exempt.** The INV-001 walk runs `--no-merges` (`scripts/validate_architecture.py:367`), so the unregistered `Merge branch …` subject is never classified. Do not remove `--no-merges` without superseding `git-workflow-v1`.
- **Branch taxonomy:** `feat/<feature-id>` (active feature), `plan/<slug>` (design/decision branches), `archive/<slug>` (frozen reference), `abort/<slug>` (abandoned-with-trail).
- **Canonical history view:** `git log --first-parent dev` — one node per feature; use it for `/catchup` and the release cut.
- **Deferred (gated on first concurrent feature):** out-of-order merge ordering + handoff-append collision (D4), optional worktree lifecycle + per-worktree envelope copy (D5), the merge-step guard / branch automation (D6 — until then the `--no-ff`-only ceremony is instructed, not enforced).

## The cairn-tdd-feature dispatch skill

The skill at `.claude/skills/cairn-tdd-feature/SKILL.md` is cairn's protocol-layer dispatch primitive. Each phase runs in a fresh context window via the Agent tool, takes a declared input artifact, and commits a declared output artifact. The four phases and their roles are unchanged from pre-shrink (Intent/Reader, Validation/Skeptic, Implementation/Builder, Integration/Auditor); what changed is the invocation surface (Skill tool, no orchestrator) and the workspace directory (`.claude/skill-runs/<feature-id>/`, replacing the retired `.claude/current-slice/`).

### Per-feature plan-doc shape

Plan docs at `docs/plans/<date>-<feature-id>.md` carry the session-spanning context. Frontmatter:

```yaml
---
id: <feature-id>
envelope:
  - "^scripts/path/to/.+\\.py$"
  - "^tests/unit/test_.+\\.py$"
---
```

Body sections: **What/Why** (the behavior change), **Boundary** (out-of-scope explicitly), **Specification** (protocol-level commitments — wire formats, return shapes, error codes), **Verification** (concrete checks Phase 4 will run). The `id:` field becomes the feature id used throughout the dispatch run; the `envelope:` array is the source-write regex set Phase 3's `role_guard.py` enforces. See `docs/plans/2026-05-08-hook-bare-python3-smoketest.md` for a working example.

### Phase artifacts

| Phase | Writes | Path |
|---|---|---|
| 1. Intent (Reader) | `intent.md` | `.claude/skill-runs/<feature-id>/intent.md` |
| 2. Validation (Skeptic) | tests + approach summary | `tests/<test files>`, `.claude/skill-runs/<feature-id>/validation/approach.md` |
| 3. Implementation (Builder) | source under envelope | source paths matching the envelope regex array |
| 4. Integration (Auditor) | sweep notes + optional handoff append | `.claude/skill-runs/<feature-id>/integration/sweep-notes.md`; optional append to `.claude/handoff.md` |

### Pre-flight conventions

Three preconditions the skill verifies before dispatching Phase 1:

1. **Agent definitions are session-pre-existing.** Claude Code's agent registry loads at session start; agent definitions added mid-session aren't `subagent_type`-discoverable. The five agents the skill dispatches (`phase-1-tdd`, `phase-2-tdd`, `phase-3-tdd`, `phase-4-tdd`, `triager-tdd`) live at `.claude/agents/`. Confirm with `ls .claude/agents/phase-{1..4}-tdd.md .claude/agents/triager-tdd.md` before dispatch. If any are missing or the session predates their commit, abort and start a fresh session.

2. **Project import convention is in every Phase brief.** `pyproject.toml` sets `[tool.pytest.ini_options] pythonpath = ["scripts"]`, so test imports use `from <subpackage>.<module> import ...` where `<subpackage>` is a directory under `scripts/` (e.g., `from lib.invariant_id_extractor import extract_invariant_ids`). The Phase-2 brief MUST include this convention verbatim — see the M2 dogfood incident in `.claude/skill-runs/m2-dogfood-extract-invariant-ids/integration/sweep-notes.md`.

3. **Baseline capture uses the full FAILED list.** Before Phase 1, run `uv run pytest -q --tb=no -rf` and capture the full output to `/tmp/<feature-id>-baseline-failures.txt`. This file is the comparison anchor for Phase 4's regression-attribution check.

### RAISE_ISSUE handling

On any phase RAISE_ISSUE, the skill dispatches `triager-tdd` to adjudicate:

- `ESCALATE_TO_USER`: stop and surface to operator.
- `RE_DISPATCH`: re-run the named target phase with the amendment included in the brief. Cap one re-dispatch per phase per skill run; second RAISE_ISSUE → ESCALATE_TO_USER.
- `ABORT`: stop and surface to operator.

## The Four Phases

Each phase is a fresh session, takes a declared input, commits a declared output. The canonical agent prompts at `.claude/agents/phase-{1..4}-tdd.md` are authoritative for per-phase behavior; this section is the operational summary.

### Phase 1: Intent

**Input:** plan doc + `docs/ARCHITECTURE.md` + targeted ADRs.
**Output:** `.claude/skill-runs/<feature-id>/intent.md`.

**Rules:**

- **Greenfield features** (new modules): Do NOT read source code. Work from architecture docs only.
- **Modification features** (changing existing behavior): Read only the public interfaces of files in the envelope (function signatures, class definitions, docstrings). Do NOT read internal implementation logic. *(Discipline only — no hook enforces this. See spec-v1 §14 incident #4.)*
- Write `intent.md` with YAML frontmatter (`id`, `name`, `snapshot-sha`, `invariants-touched`) followed by sections, in order: What, Why, Boundary, Specification, Verification, **Risk Surface**, **Feature-Local Invariants**, **Explicit Scope-Out**. The trailing three are required and elicited from the plan-doc + cited ADRs + ARCHITECTURE.md only. Phase 1 RAISE_ISSUEs rather than fabricating them when the inputs don't support derivation — that signals an under-specified plan-doc, not a Phase 1 failure. `phase-1-tdd.md` is authoritative for the elicitation contract.
- Declare which invariants and ADRs are touched.

**Exit gate:** `intent.md` committed to git.

### Phase 2: Validation

**Input:** `intent.md` only (+ `docs/ARCHITECTURE.md` and targeted ADRs if referenced).
**Output:** Test suite under `tests/` + `.claude/skill-runs/<feature-id>/validation/approach.md`.

**Rules:**

- The Phase 2 agent has NEVER seen how the implementation will work.
- Before writing tests, enumerate ambiguities in the intent. Resolve each by reference to `docs/ARCHITECTURE.md`/ADRs, or escalate before writing any test.
- Write tests against the stated intent and specification details, NOT against hypothetical implementation.
- Tests must be runnable: pytest files, not pseudocode.

**Exit gate:** Validation suite committed to git.

### Phase 3: Implementation

**Input:** `intent.md` + the validation test files (NOT Phase 2's reasoning or `approach.md`).
**Output:** Code that passes the validation suite, written within the source-write envelope from the plan doc.

**Rules:**

- The implementing agent has never seen the reasoning behind the validation suite.
- Fast feedback runs continuously via the reality hook (`ruff format` + `ruff check` on every edit).
- Full test suite runs at logical-unit boundaries.
- Write paths are gated by `role_guard.py` against the envelope regex array (passed as `AGENT_ENVELOPE`).

**Exit gate:** All validation tests pass. Implementation committed to git.

### Phase 4: Integration

**Input:** Implementation + `intent.md` + `docs/ARCHITECTURE.md` + invariants touched.
**Output:** Pass/fail on declared invariants, recorded in `.claude/skill-runs/<feature-id>/integration/sweep-notes.md`.

**Rules:**

- Run the full test suite (not just feature tests): `uv run pytest`.
- Run the architecture validator: `uv run python scripts/validate_architecture.py`.
- Verify each declared invariant with `grep`/file evidence — assertions backed by what you actually found, not from memory.
- Check for regressions in adjacent code.

**Exit gate:** All tests pass, invariants verified, sweep notes committed.

**Failure handling:** If Phase 4 fails because the implementation is wrong, RAISE_ISSUE so the triager can ESCALATE_TO_USER. Do NOT patch the implementation to force Phase 4 to pass — that recreates the correlated-error problem the system is designed to prevent.

**Escape hatch:** If Phase 4 fails because an invariant is outdated (not because the implementation is wrong), RAISE_ISSUE — the triager may direct an ADR-supersession path before re-dispatch.

## Phase Skill Guide

The phase → role → Superpowers-skill mapping is now a standalone artefact at `docs/phase-skill-mapping.md` so that consumers and Superpowers-only adopters can cherry-pick the table without taking the rest of cairn. The relocated doc preserves the binding surface INV-003's `validate_phase_topology` regex-extracts from (the four canonical agent slugs, role names, and the literal `Superpowers` token are unchanged). Mapping updates remain ordinary documentation edits per phase-lock-and-role-declaration; ADR supersession is not required.

## Context Isolation Rules

- Each phase starts fresh. No memory of previous phase's reasoning.
- Only the declared artifacts cross between phases.
- The intent document must stand alone — a reader with no other context should understand the feature from `intent.md` alone.
- Phase 1 must NOT read source code (greenfield) or must limit to public interfaces (modification).
- Phase 2 must NOT write code.
- Phase 3 must NOT expand scope beyond the envelope.

## Per-feature artifact layout

```
.claude/skill-runs/<feature-id>/
  intent.md                  # Phase 1 output
  validation/
    approach.md              # Phase 2 approach summary (tests live in tests/)
  integration/
    sweep-notes.md           # Phase 4 observations
```

The feature id is derived from the plan doc's frontmatter `id:` field, or from the filename stem. Cleanup of `.claude/skill-runs/<feature-id>/` directories is operator-discretion — there is no automatic prune ceremony.

## Identifier scheme

Every ADR, slice, feature, and decision point carries two fields: `id:` (immutable mechanical identifier) and `name:` (mutable human/LLM-facing label). Cross-references, filenames, and hook inputs use `id:`; prose uses `name:`. Full theory and firmness live in ADR `identifier-scheme` (`docs/adr/identifier-scheme.md`); this section is the operational quick reference.

**Per-entity `id:` shape** (from ADR `identifier-scheme` D2):

| Entity | id: shape | Example | Hierarchy |
|--------|-----------|---------|-----------|
| ADR | flat semantic slug | `identifier-scheme`, `parallelism-v1` | — (flat; versioning via `-v1`→`-v2` on supersession, D3) |
| Decision point | `<adr-id>/<decision-slug>` | `identifier-scheme/flat-slug-id` | hierarchical under the owning ADR |
| Slice | `<feature-id>/<slice-slug>` | `identifier-scheme/template-updates` | hierarchical under the owning feature |
| Feature | flat feature slug | `identifier-scheme`, `coordinator` | — (flat) |

**`name:` is a frontmatter slot**, not reach-into-prose text. Each entity's YAML/frontmatter block carries `name:` explicitly and that is the canonical surface any tool or renderer reads. Prose inside an entity's body freely uses `name:` but does not redefine it — frontmatter is authoritative.

**`shaped-from:` is the feature-provenance field** (ADR `identifier-scheme` D5). Each feature file records in `shaped-from:` either a path (e.g., `docs/plans/2026-04-15-fleet-coordinator-design.md`), a URL, or `null` for unshaped features. The field is append-only to the feature file at creation; rewriting it later requires the same discipline as ADR frontmatter edits.

**Legacy transition.** ADR `identifier-scheme` D7 Phase 1 (mixed-window tolerance) and Phase 2 (ADR renames; slice/feature renames) are complete. Hooks and the validator retain mixed-window tolerance indefinitely — Phase 3 of migration (drop legacy-format tolerance) is deferred per ADR `identifier-scheme` D7.

## Phase gate enforcement

Phase transitions are enforced by git, not by session state:

- Phase 2 cannot start until `intent.md` is committed.
- Phase 3 cannot start until the validation suite is committed.
- Phase 4 cannot start until the implementation is committed.

The `cairn-tdd-feature` dispatch skill verifies each prior phase commit (Steps 5/7/9/11 of `.claude/skills/cairn-tdd-feature/SKILL.md`) before advancing; ad-hoc edits sidestep this entirely.

## Premise-grounding gate (`checks/premise_guard.py`)

A Phase-1→Phase-2 approval gate that blocks dispatch when an intent's claims about existing source have gone stale or fabricated. It reads the intent's optional `## Premise Grounding` block and diffs each verbatim `quote:` against live source, so the dispatch skill never proceeds on a premise the current tree no longer supports.

**Invocation:**

```bash
uv run python checks/premise_guard.py .claude/skill-runs/<feature-id>/intent.md
```

Run by the dispatch skill at Step 5a (between the Phase-1 commit verify and the Phase-2 dispatch). `source:` paths resolve relative to `CLAUDE_PROJECT_DIR` (the consumer cwd); the shared matcher loads from cairn's own root, so the two diverge cleanly when cairn is consumed downstream.

**Exit codes** (mirror `role_guard.py`):

- `0` — all premises grounded, OR no `## Premise Grounding` section, OR a `premises:` value of YAML null (`~`/absent value) or an empty list. Proceed to Phase 2.
- `1` — one or more premises not grounded: the quoted span is absent (stale or fabricated), or the cited source is missing/unreadable. The stderr names each failing premise; **block dispatch** until corrected.
- `2` — malformed input: intent file missing/unreadable, unparseable YAML block, a `premises` value that is not a list, a premise that is not a mapping or whose `source`/`quote` is not a string (e.g. an int or list value), or bad args. Treat as a malformed-intent `RAISE_ISSUE`.

This is the FLI-2 contract: **fail-open on absence** (no block → `0`) but **fail-closed on malformation** (present-but-broken block → `2`). A present-but-broken premise block never silently passes.

**The `## Premise Grounding` intent section.** Optional and **operator-authored at the Phase-1→Phase-2 gate**, not by `phase-1-tdd` — the Reader contract forbids reading implementation source, so Phase 1 cannot verify a verbatim span. Omit the section when the intent makes no source-behaviour claims. When present, it carries one fenced ```yaml block with a `premises:` list; each entry pins a repo-root-relative `source:`, a verbatim `quote:` (block scalar), and a one-line `label:` stating the current-behaviour claim the intent depends on. Template shape: `templates/intent.md`.

**Override.** `CAIRN_PREMISE_FIX=1` bypasses the grounding check (exit `0` with a stderr notice) — for a known, operator-accepted divergence where the quote intentionally no longer matches.

**Tolerance semantics.** Quote-vs-source matching is whitespace- and comment-tolerant via `scripts/lib/premise_match.grounded`: both sides are whitespace-normalized (all runs collapse to single spaces), and comments are stripped before the compare — line comments (`#`) for `.py`/`.sh`/`.yaml`/`.yml`, HTML comments (`<!-- -->`) for `.md`. So a re-indented or line-wrapped span still grounds, and a comment edit inside the cited span still grounds; a token or value change does not. An empty or comment-only quote never grounds. The comment-strip is naive: a `#` (or `<!--`) inside a string literal in the cited source is treated as a comment-start, so a change confined to text after a string-internal `#` may not be caught — this is an accepted bound of the mechanical verbatim-quote diff, which does not parse source semantics (premise_guard is not a source-comprehension layer).

**FLI-1 (shared-matcher invariant).** `premise_guard.py` and `validate_architecture.py`'s `premise-grounding` assertion MUST route quote-vs-source through the same `scripts/lib/premise_match.grounded` — they cannot diverge on tolerance. A premise that passes one passes the other for identical inputs — i.e. the same `quote` against the same resolved source text; the equivalence is matcher-scoped, not whole-pipeline, because the two callers resolve `source` paths against different roots (the guard uses `CLAUDE_PROJECT_DIR`/cwd, the validator its own `project_root`).

## Scope-split (atomicity) gate (`checks/atomicity_guard.py`)

The scope-split (atomicity) gate is a sibling of the premise gate at the same Phase-1→Phase-2 boundary (skill Step 5a). It reads an intent's optional `## Contract` block and runs the atomicity check on its `must-satisfy` clauses, blocking Phase-2 dispatch on a non-atomic untagged clause.

```bash
uv run python checks/atomicity_guard.py .claude/skill-runs/<feature-id>/intent.md
```

**Atomicity (ADR D3).** A clause is atomic iff verifiable by a single tool call or single file check. Clauses without a tag must pass atomicity. A non-atomic clause must be split into atomic clauses OR carry one of four named exception tags — tagging is the cheap one-line escape:

- `universal-set` — quantifies over a set; declaration enumerates the set.
- `regression-meta` — `unchanged`/`no regression` meta-clause; declaration names the baseline.
- `operator-bound` — needs human action/judgement; declaration names the operator step.
- `trivial-existence` — a file/output simply exists; NO declaration required.

The first three tags require a non-empty declaration after the colon; an unknown tag always fails. Mapping form: `{clause: "<EARS>", except: "<tag>: <declaration>"}`.

**Exit codes.** `0` = all clauses atomic-or-validly-tagged, or no `## Contract` block (fail-open with a visible stderr notice unless `CAIRN_CONTRACT_REQUIRED=1`). `1` = ≥1 offence (non-atomic untagged clause, unknown tag, or required tag with an empty declaration), or an absent block under `CAIRN_CONTRACT_REQUIRED=1`. `2` = intent unreadable, malformed YAML, or a `## Contract` heading present but no parseable fenced block (fail-closed backstop).

**Override.** `CAIRN_ATOMICITY_FIX=1` bypasses the check (exit `0` with a stderr notice).

**FLI-1 (shared-lib invariant).** `atomicity_guard.py` and `validate_architecture.py`'s `scope-split` assertion (`type: scope-split`) MUST route through the same `scripts/lib/atomicity.check_clauses` (and its `EXCEPTION_TAGS`) — they cannot diverge on the tag set or pass/fail logic.

## Operator envelope (`.claude/active-envelope.yaml`)

The operator-session write gate. Read by `checks/role_guard.py` when `AGENT_ROLE` is unset (i.e., a regular Claude Code session, not a dispatch-skill phase run).

Shape:

```yaml
mode: operator   # values: "operator" (enforce), "off" (no-op)
paths:
  - ^docs/operational-reference\.md$
  - ^scripts/.*
  - ^\.claude/active-envelope\.yaml$   # must include itself
```

Semantics:

- `mode: operator` + `paths:` enforces — `Write`/`Edit`/`MultiEdit`/`NotebookEdit` against any path not matching one of the regexes is denied with a stderr diagnostic. Read-class tools (`Read`, `Grep`, `Glob`) are unaffected.
- `mode: off` — hook is a no-op. Use this when returning to ad-hoc / cross-cutting work.
- File absent — hook is a no-op (default fail-open for un-envelope'd sessions).
- Malformed YAML, non-mapping root, unrecognised mode, or `mode: operator` without a `paths:` list — fails closed (denies the write) with stderr diagnostic.
- PyYAML 1.1 quirk: bare `off` parses as `False`, which the hook normalises back to `"off"`.

**Self-pattern requirement.** The file must include a regex matching itself (`^\.claude/active-envelope\.yaml$`) when `mode: operator`, otherwise you cannot edit it while enforcement is active. The shipped envelope includes this self-pattern.

**Worktree-scoped.** Each git worktree has its own copy. Set `mode: operator` when starting focused feature work; clear (`mode: off` or delete the file) when returning to ad-hoc work.

## Hooks

Three hooks wired in `.claude/settings.json`:

- **`reversibility-guard.sh`** (PreToolUse on `Bash|Edit|Write`): blocks destructive ops (`rm -rf`/`-fr`, `git push --force`/`-f`, `git reset --hard`, `git clean -fd`, `DROP TABLE`/`DROP DATABASE`), `.env*` writes, lock-file writes (`uv.lock`/`package-lock.json`/`poetry.lock`); enforces ADR append-only on `docs/adr/*.md` (Write blocks new on existing; Edit allows only frontmatter `status:`/`superseded-by:`/`superseded_by:`/`firmness:` first-line edits + `ADR_EDITORIAL_FIX=1` additive escape, logged to `.claude/adr-editorial-fixes.log`). Allows `git push --force-with-lease`.
- **`role_guard.py`** (PreToolUse on `Edit|Write|MultiEdit|NotebookEdit`): two paths.
  - When `AGENT_ROLE` is set (dispatch-skill subagents): per-role static allowlist for `phase-1-tdd` / `phase-2-tdd` / `phase-4-tdd`; `phase-3-tdd` is envelope-driven via `AGENT_ENVELOPE` (no static entry — intentional asymmetry per `compression-infrastructure-bootstrap-superseded`). Wider grants via `AGENT_ENVELOPE` for static-policy roles are logged to `.claude/envelope-grants.log` (D9 envelope-grant escape).
  - When `AGENT_ROLE` is unset: reads `.claude/active-envelope.yaml` per the Operator envelope section above.
- **`reality-check.sh`** (PostToolUse on `Edit|Write`): runs `ruff format` and `ruff check --fix` on `*.py` files. No-op for non-Python paths.

**Hook dependencies.** All three hooks expect `jq` (the bash hooks parse stdin JSON). `reality-check.sh` additionally needs `ruff`. Missing deps cause silent no-op with a stderr warning. Install before any work in cairn:

```
brew install jq && uv tool install ruff
```

Hooks are friction-plus-walls, not security boundaries. A determined or careless agent can route around the friction layer; the wall layer (the explicit patterns above) holds.

## Environment variables

Knobs the operator (or downstream consumer) may set. Defaults follow the "no hardcoded timeouts/sizes in consumer-facing scripts" rule — every script that reads a knob falls back to a documented default.

| Var | Default | Read by | Purpose |
|---|---|---|---|
| `CLAUDE_PROJECT_DIR` | unset (falls back to `git rev-parse`) | `scripts/_root.py`, `scripts/validate_architecture.py`, `checks/reversibility-guard.sh` | Canonical project-root override. Set when running scripts from outside the repo root. |
| `AGENT_ROLE` | unset | `checks/role_guard.py` | Identifies the spawned-session role for inner-gate enforcement. Unset → operator-envelope path. |
| `AGENT_ENVELOPE` | unset | `checks/role_guard.py` | JSON array of regex strings (or `{paths:[...]}` object). For `phase-3-tdd`, the only write-path gate; for static-policy roles, the wider envelope-grant escape (D9). |
| `ADR_EDITORIAL_FIX` | unset | `checks/reversibility-guard.sh` | Typo-fix escape hatch for ADR body edits; new content must be additive over old. Logs to `.claude/adr-editorial-fixes.log`. |
| `CAIRN_RECORD_MEASUREMENTS` | unset | `tests/unit/test_context_budget.py` | Opt-in: rewrite `docs/plans/measurements/2026-04-12-slice-003.txt` with fresh turn-1 reading. Unset by default. |
| `CAIRN_PREMISE_FIX` | unset | `checks/premise_guard.py` | `=1` bypasses the premise-grounding check (exit 0 with stderr notice) for a known, operator-accepted divergence. See "Premise-grounding gate". |
| `CAIRN_ATOMICITY_FIX` | unset | `checks/atomicity_guard.py` | `=1` bypasses the scope-split (atomicity) check (exit 0 with stderr notice) for a known, operator-accepted divergence. See "Scope-split (atomicity) gate". |
| `CAIRN_CONTRACT_REQUIRED` | unset | `checks/atomicity_guard.py` | `=1` makes an intent with no `## Contract` block exit `1` (block) instead of fail-open. See "Scope-split (atomicity) gate". |

**Dev-mode local knobs** (read by `commands/claude-code/.local/dev-mode.md`, cairn-internal — not part of the consumer surface): `CAIRN_DEVMODE_PLAN_STALE_DAYS` (default 30), `CAIRN_DEVMODE_MEMORY_STALE_DAYS` (default 60), `CAIRN_DEVMODE_LESSON_STALE_DAYS` (reserved).

## Project-root resolution

`scripts/_root.py:project_root()` is the single source of truth for path construction in `scripts/`. Resolution precedence:

1. `CLAUDE_PROJECT_DIR` env var — if set and non-empty, returns `Path(value).resolve()`.
2. `git rev-parse --show-toplevel` from `os.getcwd()` — subprocess with `cwd=os.getcwd()`, returns `Path(stdout.strip()).resolve()`.
3. `RuntimeError` — loud message naming both mechanisms and the originating error.

**Symlink trap (L-017).** Cairn ships a `.slice-system → .` self-symlink (consumed by downstream projects). Any `Path(__file__).parent` chain run from a file reached through that symlink resolves to the consumer-side path, not the cairn root. `project_root()` avoids this by never using `__file__` — it uses only env-var and git.

**Call-site rules.** Replace every `Path(".claude/...")` literal with `project_root() / ".claude" / ...`; replace every `Path.cwd()` with `project_root()`; add `cwd=project_root()` to every `subprocess.run(["git", ...])` call. Files under `tests/` are exempt — they use `tmp_path` and synthetic roots freely.

Set `CLAUDE_PROJECT_DIR` to the absolute repo root when running cairn scripts from a working directory other than the root.

## Context Discipline Protocol

context-discipline-protocol / INV-002. Three load-bearing layers that together hold post-catchup session context bounded. None of the three layers is optional — the savings come from all three interacting, not from any one in isolation.

### Layer 1 — Handoff is a pointer, not a payload

`.claude/handoff.md` is overwritten each session against `templates/handoff.md`. The current format is fixed:

- YAML frontmatter contains a `contract:` block with `must-satisfy`, `must-not-violate`, `wrong-if`, and `evidence`.
- The body is a pointer-only bullet list. Each nonblank body line has the shape `- <pointer> <state> [<short context>]`, where `state` is one of `open`, `blocked`, or `deferred`.
- Pointers must resolve on read: GitHub issue/PR refs (`gh:<org>/<repo>#<num>`), repo docs such as `docs/adr/<slug>.md` or `docs/plans/<filename>.md`, or reachable commit SHAs.

**Token budget: 150 to 400 tokens, whole-file.** 150 is a soft lower bound (if you cannot say enough to orient the next session inside that, your next step isn't specific). 400 is a hard upper bound (if you need more than 400 tokens to say what state the repo is in, the overflow belongs in commit messages, ADRs, plan docs, or `docs/lessons.md` — not in the handoff). Measured in bytes, 400 tokens is roughly 2000 characters at the 5-char-per-token approximation the contract test uses.

**Banned payload shapes** — the handoff template MUST NOT contain, and the operator MUST NOT produce:

- Retired markdown sections such as `## State`, `## Next`, `## Blocked / Pending`, `## Pointers`, or `## Features`
- "What This Session Was About"
- "What Was Accomplished"
- "Surprises or Discoveries"
- "Self-Check" / "Self Check"
- Narrative paragraphs of reasoning
- Pass/fail test tallies or test output

These belong in commit messages, ADRs, plan docs, or `docs/lessons.md`. The handoff carries resolvable pointers plus state, not reflection. If you feel an urge to explain *why* in the handoff, the urge is a signal the explanation belongs elsewhere.

The handoff is wiped (overwritten) at every end-of-session step; git provides the historical record.

### Layer 2 — Catchup reads in tiers, dispatches subagents, never eager-loads

`/catchup` runs in three tiers. The tier boundaries are the whole point of the protocol — crossing a tier without satisfying its admission criteria is the failure mode this layer is closing.

**Tier 1 — always runs, strictly bounded.** Reads ONLY these four items:

- `.claude/handoff.md`
- `git log --oneline -10`
- `git status -s`
- `.claude/active-envelope.yaml` (when present — surfaces the write-gate state)

Produces the orientation summary. STOPS. No `CLAUDE.md` rereads, no `docs/ARCHITECTURE.md`, no source, no ADRs. Any additional main-context file read crosses into Tier 2 — and Tier 2 has admission criteria.

**Tier 2 — dispatched via subagent, under admission criteria.** Tier 2 exists to answer a *specific* question or to load a phase's declared inputs when the operator has given explicit direction. It runs in a subagent, never in main context. The full admission block (and its mirror "do not dispatch" block) lives verbatim in `commands/claude-code/catchup.md` — the slash-command file is the canonical copy; this section defers to it. The key literal on the positive side is `DISPATCH Tier 2 subagent if and only if:`; the three conditions are (1) specific factual question Tier 1 did not answer, (2) operator directed entry into a feature phase, (3) about to act on a file named in the handoff pointers. None of those? Do not dispatch.

The subagent contract caps the return at ~200 words regardless of underlying file size. A subagent that dumps everything it read back into main context defeats the savings Tier 2 is supposed to buy. If a legitimate answer genuinely does not fit in 200 words, split the question into two Tier 2 dispatches rather than raise the cap.

**Tier 3 — the absence of catchup.** Once the operator gives a direct work imperative, catchup is over and normal file reading resumes under whatever skill governs the work. No bookkeeping — Tier 3 is the boundary past which `/catchup` is simply not running anymore.

### Layer 3 — Dispatch artifacts are ephemeral; handoff is wiped each session

`.claude/skill-runs/<feature-id>/` accumulates per-feature artifacts during a `cairn-tdd-feature` dispatch run; cleanup is operator-discretion (no automatic wipe ceremony, no archive directory). The post-shrink dispatch skill commits each phase's writes by name through git — git history covers the artifact-preservation case the pre-M4 close ceremony used to handle.

`.claude/handoff.md` is wiped (overwritten) each session and represents current state, not history. `.claude/learning.md` is the append-only session-end staging ground for post-feature learnings; the 3× promotion rule that moves stable patterns from `learning.md` into `CLAUDE.md` is specified in `context-discipline-protocol` but not yet automated. Nothing in cairn writes to `learning.md` automatically — sessions may append by hand.

### Operator mental model

One sentence each:

- Handoff is a **team interface**, not a diary. The next session reads it to *act*, not to relive the last one.
- Catchup is a **tiered query**, not a flood. Tier 1 orients, Tier 2 answers specific questions via subagents, Tier 3 is the exit.
- Dispatch artifacts are **ephemeral**, not archived. Git history plus `.claude/learning.md` plus ADRs cover the post-mortem case.

If any of those three drift, reload this section and `commands/claude-code/catchup.md` before trying to patch the symptom.

## Next-task selection

`/catchup` orients (it lists handoff threads by state) but deliberately does not rank — picking the next task is a separate, operator-owned judgment. This is the policy for that pick: a ladder applied to signal the repo already carries (handoff states, GitHub `severity:` labels, roadmap `Depends on` order). No tool ranks for you, by design — a bespoke ranker with frozen weights would drift, the same anti-coupling argument `board-as-roadmap-substrate` makes for its F5 risk. The ladder just makes the judgment repeatable and auditable.

Apply the rungs in order; the first that resolves a candidate wins:

1. **`blocked` rots — clear it or surface it.** A `blocked` handoff thread does not wait quietly: either take the unblocking action or surface the blocker to the operator. *Signal:* `.claude/handoff.md` state `blocked`.
2. **`deferred` is parked — skip until its trigger fires.** A `deferred` thread carries a trigger (a date or condition) in its context tail; ignore it until the trigger is met. *Signal:* `.claude/handoff.md` state `deferred` + the freetext trigger.
3. **Finish-started beats start-new.** Among `open` threads, prefer work already in motion, lowest-friction first: staged-but-uncommitted → committed-but-unpushed → paused-mid-trial → untouched. Reduces entropy and unblocks downstream. *Signal:* `git status` / `git log origin/<branch>..<branch>` + handoff context tails (`pending-push`, `paused`).
4. **Tiebreak by severity.** Among otherwise-equal `open` items, higher severity first (`severity:S1` highest, then `S2`, then `S3`). *Signal:* GitHub issue `severity:` labels.
5. **Tiebreak by roadmap dependency order.** Among equal-severity items, pick the lowest-positioned Must-land item whose `Depends on` prerequisites are all satisfied. *Signal:* `docs/roadmap.md` Must-land ordering + `Depends on (N)` markers.
6. **Route by weight.** Once a candidate is chosen, if it is outward-facing (push, PR, messaging a shared system), decision-weight, or cross-cutting, surface it to the operator rather than self-executing; proceed unprompted only on self-contained internal work. *Signal:* the candidate's own nature, not a stored field.

The ladder reads only signal that already exists and is maintained independently — it adds no field, command, or file to keep current. Selection stays a human judgment the ladder makes explicit, not deterministic automation. If the rungs cannot resolve a defensible pick without inventing a new maintained input, that is the cue to escalate to the operator, not to add machinery.

Out of scope (separate, deferred tracks): a read-only `/next` aid that gathers and surfaces candidates for the operator to apply this ladder to, and the `board-as-roadmap-substrate` D2/D4/D7 board implementation. Default-no on both until this written policy proves insufficient in practice.

## ADR rules during a feature

If implementation requires violating an invariant:

1. RAISE_ISSUE from the phase observing the conflict; the triager will likely ESCALATE_TO_USER.
2. Operator writes a new ADR in `docs/adr/` with proper YAML frontmatter (`status: provisional`, `firmness: provisional`).
3. Update `docs/adr/index.md`.
4. Manually update `docs/ARCHITECTURE.md` to reflect the new invariant or supersede the old one (gated by `reversibility-guard.sh`'s ADR append-only check on the underlying ADR corpus).
5. Re-dispatch the phase with the amendment.

ADRs are append-only. Never edit an accepted ADR's body. To change a decision, write a new ADR that supersedes it.

## Cairn repo internals

This section documents cairn's own repo layout and working practices. It is deliberately not in `CLAUDE.md` — CLAUDE.md is a safety cheat sheet, not a README. Load this section when doing non-trivial work on cairn itself.

### What this repo is

Cairn is a methodology repository, not a runnable application or library. It contains the protocols, shell-script hooks, slash commands, the `cairn-tdd-feature` dispatch skill, and documentation that implement a four-phase development pipeline (Intent → Validation → Implementation → Integration), a decision protocol for architectural work, and an architecture validator. It is consumed by *other* projects, which symlink it as `.slice-system/` and reference its scripts/docs from their own `.claude/` configuration. Cairn also consumes itself the same way — a `.slice-system → .` self-symlink lets the same pipeline run on cairn's own development.

Status: solo, pre-v1. See `docs/roadmap.md` for the work required to reach v1, and `CHANGELOG.md` for the delta since v0.1.0.

### Repo layout

- `checks/` — POSIX shell hooks plus one Python hook. Three hooks: `reversibility-guard.sh` (blocks destructive ops, enforces ADR append-only), `role_guard.py` (operator envelope + per-phase write paths), `reality-check.sh` (runs `ruff format` + `ruff check --fix` on Python edits).
- `commands/claude-code/` — Markdown slash commands: `catchup`, `decision`, `decision.full`, `new-adr`, `new-adr.full`. Plus a `.local/` directory of cairn-internal dev aids (not shipped to consumers).
- `.claude/skills/cairn-tdd-feature/SKILL.md` — the dispatch skill that sequences the four phases via fresh subagents.
- `.claude/agents/` — agent definitions (`phase-1-tdd.md`, `phase-2-tdd.md`, `phase-3-tdd.md`, `phase-4-tdd.md`, `triager-tdd.md`) and `role-topology.yaml` (the authoritative phase→role-slug mapping consumed by INV-003's binding).
- `docs/` — Three layers: `operational-reference.md` (Layer 1, this file), `spec-v1.md` (Layer 2, canonical spec — deliberately not auto-loaded), `vision.md` + `roadmap.md` (what v1 commits to and the ordered slice sequence to get there). ADRs under `docs/adr/`.
- `scripts/` — `_root.py` (path-resolution primitive), `validate_architecture.py` (single-file architecture validator), `smoketest_hooks.sh` (bare-`python3` hook smoketest), `lib/` (shared utilities — `invariant_id_extractor.py`, `superseded_test_signal.py`).
- `tests/unit/` — pytest suite. `pyproject.toml` sets `pythonpath = ["scripts"]` so test imports use `from <subpackage>.<module>`.
- `templates/` — handoff template; expansion roadmapped.

**Vestigial.** `scripts/slice_orchestrator/`, `scripts/cairn_query/`, and `mcp_servers/cairn_knowledge/` are leftover `__pycache__`-only directories from retired surfaces (orchestrator, cairn-knowledge MCP server). Future cleanup may prune them.

**Symlink recursion hazard.** `.slice-system → .` is an infinite-depth loop for any tool that follows symlinks recursively. If you add `find`, `glob("**/*")`, or similar, exclude `.slice-system` explicitly.

### Working on cairn itself

Common operations:

- **Lint a hook script:** `shellcheck checks/<name>.sh` (if shellcheck is installed).
- **Smoke-test a hook locally:** `echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | bash checks/reversibility-guard.sh`. Exit code 1 + stderr diagnostic = blocked. Exit 0 = allowed.
- **Run the validator:** `uv run python scripts/validate_architecture.py`. Expect `ALL CHECKS PASSED`.
- **Run the suite:** `uv run pytest -q`. Expect `360/0/2`.
- **Smoketest hooks:** `bash scripts/smoketest_hooks.sh`. Expect `PASS role_guard.py` and exit 0.

When doing non-trivial work on cairn, the intended flow is meta-dogfood: use the `cairn-tdd-feature` dispatch skill on cairn itself when the work has a clear failing-test shape; use the ad-hoc-edit + operator-envelope path otherwise.

### Editing rules expanded

- **Edit canonical paths only, never via `.slice-system/`.** Slice-system files are symlinked from consumers; editing through the symlink produces tool-input paths starting with `.slice-system/`. `reversibility-guard.sh` strips that prefix before its allow/deny check, but `role_guard.py` does NOT — the operator-envelope and per-role allowlists are anchored at the canonical repo root, so a `.slice-system/...` path matches no pattern and the edit is denied. Always target `checks/...`, `commands/claude-code/...`, `scripts/...` directly.
- **Operator envelope is the write gate** when `AGENT_ROLE` is unset. Set `mode: operator` + a `paths:` regex list when starting focused feature work (the file must include a self-pattern); set `mode: off` (or delete) when returning to ad-hoc cross-cutting edits. The file is worktree-scoped.
- **Six v1 commitments** (`docs/vision.md`) are the spec for cairn's own development: agent-portable, parallelism-native, soft agent-split, meta-dogfoodable from feature #1, plastic phase shape through v1, explicit cognitive roles per phase. Don't lock in designs that contradict these — especially not a global "one active feature" pointer (parallelism is a v1 commitment, not a future feature).

### Documentation tiers — when to load what

If a question is operational ("what does Phase 2 receive as input?", "what does the operator envelope allow?"), this file (`docs/operational-reference.md`) is sufficient. If a question is about the *why* (failure modes, the dual context-engineering / role-reset thesis, empirical support, what the system does and does not claim), read `docs/spec-v1.md`. The spec is long and intentionally kept out of default context — pull it in deliberately when needed. The `cairn-tdd-feature` dispatch protocol lives in `.claude/skills/cairn-tdd-feature/SKILL.md` and is loaded by the skill at dispatch time.
