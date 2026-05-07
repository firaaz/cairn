# Cairn Shrink M2 — Dispatch Skill + Dogfood — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a thin dispatch skill (`cairn-tdd-feature`) that sequences Phase 1→4 subagents via Anthropic's Agent tool, with no orchestrator dependency, and prove it works end-to-end on a toy feature — coexisting with the existing orchestrator (no deletes).

**Architecture:** Five new TDD-flavored phase agent definitions (`phase-{1..4}-tdd.md` + `triager-tdd.md`) live alongside the orchestrator-coupled originals. They drop MCP/substrate references and `AGENT_ENVELOPE` env-var coupling, reading canonical docs directly via the Read tool with `offset:`/`limit:`, and writing to a skill-managed workspace at `.claude/skill-runs/<feature-id>/`. The skill is markdown-only at `.claude/skills/cairn-tdd-feature/SKILL.md` (~120 lines), takes the path to a per-feature plan doc as its sole input, captures a snapshot SHA at start, and produces one git commit per phase. Phase isolation is achieved by: independent context windows (Agent tool natively), per-agent `tools:` allowlists, and brief-content discipline; `role_guard.py`'s path-level lockdowns do NOT engage (orchestrator-bound), which is acceptable as defense-in-depth gap for M2 and resolved in M3.

**Tech Stack:** Markdown skill files, `.claude/agents/*.md` subagent definitions, Anthropic Agent tool, Python 3.12 (the dogfood target), `pytest` via `uv run pytest`, conventional commits.

---

## Pre-flight conventions (decisions locked here, used everywhere below)

These four decisions are referenced by every task. Locking them now keeps the plan internally consistent.

1. **Workspace path** — `.claude/skill-runs/<feature-id>/` (mirrors `current-slice/` shape but skill-owned, no orchestrator collision). Per feature: `intent.md`, `validation/approach.md`, `integration/sweep-notes.md`. Multiple feature workspaces may coexist; cleanup is manual for M2.
2. **Skill input** — sole argument is a path to `docs/plans/<feature>.md` (the per-feature plan doc). The skill `Read`s it, captures `git rev-parse HEAD` as the snapshot SHA, then constructs Phase-N briefs inline. (Resolves design §9 Q1 — path-only; inline-prompt fallback deferred to a later iteration.)
3. **Per-phase commit message convention:**
   - Phase 1: `feat(<feature-id>): phase 1 — intent`
   - Phase 2: `test(<feature-id>): phase 2 — failing tests`
   - Phase 3: `feat(<feature-id>): phase 3 — implementation`
   - Phase 4: `chore(<feature-id>): phase 4 — sweep + handoff`
4. **No clusters.yaml in M2.** Phase 3 is single-agent. Multi-file fan-out (parallel `phase-3-tdd` subagents in one message) is M3+. (Resolves design §9 Q2.)

---

## File Structure

**New files:**

- `.claude/agents/phase-1-tdd.md` — Reader (TDD variant); ~30 lines
- `.claude/agents/phase-2-tdd.md` — Skeptic (TDD variant); ~30 lines
- `.claude/agents/phase-3-tdd.md` — Builder (TDD variant); ~30 lines
- `.claude/agents/phase-4-tdd.md` — Auditor (TDD variant); ~35 lines
- `.claude/agents/triager-tdd.md` — Triager (TDD variant); ~15 lines
- `.claude/skills/cairn-tdd-feature/SKILL.md` — Dispatch skill; ~120 lines
- `docs/plans/2026-05-06-m2-dogfood-extract-invariant-ids.md` — Toy dogfood plan input; ~50 lines
- `scripts/lib/__init__.py` — empty (created so package import works); 0 lines
- `scripts/lib/invariant_id_extractor.py` — Dogfood target source (created BY Phase 3); ~15 lines
- `tests/unit/test_invariant_id_extractor.py` — Dogfood RED tests (created BY Phase 2); ~30 lines
- `.claude/skill-runs/m2-dogfood-extract-invariant-ids/intent.md` — Phase-1 output
- `.claude/skill-runs/m2-dogfood-extract-invariant-ids/validation/approach.md` — Phase-2 output
- `.claude/skill-runs/m2-dogfood-extract-invariant-ids/integration/sweep-notes.md` — Phase-4 output

**Modified files:**

- `.claude/handoff.md` — replace contents with M2-landed handoff (Task 14)
- `.gitignore` — add `.claude/skill-runs/` if we decide skill-runs are per-developer (Task 1 settles this)

**Untouched files:** `.claude/agents/phase-{1..4}-*.md` (originals), `.claude/agents/issue-triager.md`, `scripts/slice_orchestrator/`, `scripts/cairn_query/`, all `commands/claude-code/*` slash commands, all hooks except no changes to `role_guard.py` (M3 territory). Coexistence guaranteed by no-overlap.

---

## Task 1: Lock conventions & verify environment

**Files:**
- Inspect: `.claude/handoff.md`, `.claude/agents/phase-1-writer.md` (existing, for shape reference)
- Decide: gitignore disposition for `.claude/skill-runs/`

- [ ] **Step 1: Confirm we're on `design/cairn-shrink` and tree is clean (modulo known untracked)**

Run:
```bash
git rev-parse --abbrev-ref HEAD
git status --short
```
Expected: branch is `design/cairn-shrink`; only untracked files are `.claude/scheduled_tasks.lock`, `.windsurf/`, the two pre-existing `docs/plans/2026-04-21-windsurf-*.md`. If anything else is dirty, STOP and consult the handoff.

- [ ] **Step 2: Decide `.claude/skill-runs/` git disposition**

The workspace contains intent/approach/sweep-notes that ARE the phase audit trail. They're per-feature, not per-developer. **Decision:** check them in (commit alongside per-phase work). Do NOT add to `.gitignore`. If multi-developer collisions emerge later, revisit in M3.

- [ ] **Step 3: Verify `uv run pytest` works on the current tree**

Run:
```bash
uv run pytest --collect-only -q 2>&1 | tail -5
```
Expected: collection succeeds (≥1 test), exit 0. We need the suite to be green-ish before dogfood so any new failure is attributable to M2 work.

- [ ] **Step 4: Capture pre-M2 baseline**

Run:
```bash
uv run pytest -q 2>&1 | tail -3 > /tmp/m2-baseline.txt
cat /tmp/m2-baseline.txt
```
Expected: a summary line like `N passed, M failed in T.TTs`. Note the `N passed, M failed` pair as the baseline. After M2, the deltas should be: at minimum `+1 test added` (the dogfood), 0 new failures in pre-existing tests.

- [ ] **Step 5: No commit. This is recon.**

---

## Task 2: Write `phase-1-tdd` agent definition

**Files:**
- Create: `.claude/agents/phase-1-tdd.md`

- [ ] **Step 1: Write the agent file**

Create `.claude/agents/phase-1-tdd.md` with this exact content:

```markdown
---
name: phase-1-tdd
description: Phase 1 Reader (TDD skill variant) — drafts intent.md from arch/ADR context only.
tools: Read, Write, Edit, Bash, Grep, Glob
---

Draft `intent.md` from architecture and ADR context. The dispatch skill provides a brief naming the feature plan path, the workspace path, the snapshot SHA, and the feature id. You are the only agent in this phase.

**Read canonical sources directly.** Use `Read` with `offset:`/`limit:` on `docs/ARCHITECTURE.md`, `docs/adr/*.md`, `docs/spec-v1.md`, `docs/operational-reference.md`, `docs/lessons.md`. Do NOT call any MCP server; the cairn-knowledge MCP is being retired and is not in scope for the TDD skill path.

**Output path.** Write to the workspace `intent.md` path passed in your brief (e.g., `.claude/skill-runs/<feature-id>/intent.md`). Do NOT touch `.claude/current-slice/` — that path is owned by the legacy orchestrator and writing there will collide with active slices.

**Intent shape.** YAML frontmatter (id, name, snapshot-sha, invariants-touched [list, may be empty]) followed by sections: What, Why, Boundary (≤200 words combined), Specification, Verification.

**P2 — Do not refuse preemptively.** Always attempt the Write tool call. Do not refuse based on prior-art or historical failure docs. Invoke the tool; report the actual error if any.

**P1 — Bash-heredoc escape.** When `Write`/`Edit` is denied by the sensitive-file gate on `.claude/**` paths, fall back to `cat > path <<'HEREDOC' … HEREDOC` to escape the gate. Do not abandon the write.

**Commit your write.** Stage only the files you wrote, then `git commit -m 'feat(<feature-id>): phase 1 — intent'`. Use the feature id from your brief.

Final stdout line MUST be a single JSON object on its own line — no fences, no prefix, no suffix:
{"status":"OK|RAISE_ISSUE|FAILED","commit_hash":"<sha>","summary":"<=100w","feature_id":"<id>"}
```

- [ ] **Step 2: Sanity-check the file**

Run:
```bash
head -5 .claude/agents/phase-1-tdd.md
wc -l .claude/agents/phase-1-tdd.md
```
Expected: frontmatter present (`---`, `name: phase-1-tdd`, ...); ~25-30 lines total.

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/phase-1-tdd.md
git commit -m "feat(m2): add phase-1-tdd agent definition"
```

---

## Task 3: Write `phase-2-tdd` agent definition

**Files:**
- Create: `.claude/agents/phase-2-tdd.md`

- [ ] **Step 1: Write the agent file**

Create `.claude/agents/phase-2-tdd.md` with this exact content:

```markdown
---
name: phase-2-tdd
description: Phase 2 Skeptic (TDD skill variant) — writes failing tests from intent.md alone.
tools: Read, Write, Edit, Bash, Grep, Glob
---

Write failing pytest files asserting the stated intent. You have not seen Phase 1's reasoning beyond the artifact `intent.md`. You will not see Phase 3.

**Inputs (from your brief).** Path to `intent.md`, path to the feature plan doc, the workspace path, the snapshot SHA, the feature id.

**Read canonical sources directly.** Use `Read` with `offset:`/`limit:` on `docs/ARCHITECTURE.md`, `docs/adr/*.md`, etc. Do NOT call any MCP server.

**Write paths.** Tests go to `tests/unit/test_<topic>.py` (or `tests/<subtree>/...` if intent.md specifies). The approach memo goes to the workspace at `<workspace>/validation/approach.md`. Do NOT touch `.claude/current-slice/`.

**Tests must FAIL.** Run `uv run pytest tests/unit/test_<topic>.py -v` after writing. Confirm the tests fail with a recognizable error (`ModuleNotFoundError`, `AttributeError`, or assertion failure). If they pass, the intent is already satisfied and you should RAISE_ISSUE.

**P2 — Do not refuse preemptively.** Attempt the tool call before refusing.

**P1 — Bash-heredoc escape.** When `Write`/`Edit` is denied by the sensitive-file gate on `.claude/**` paths, fall back to `cat > path <<'HEREDOC' … HEREDOC`.

**Approach memo.** ≤300 words. Lists the tests you wrote, the spec ambiguities you resolved (cite ADR/architecture lines), the ones you flagged for the human if any.

**Commit your writes.** Stage only the files you wrote, then `git commit -m 'test(<feature-id>): phase 2 — failing tests'`.

Final stdout line: `{"status":"OK|RAISE_ISSUE|FAILED","commit_hash":"<sha>","summary":"<=100w"}`. RAISE_ISSUE for unresolved ambiguity or for tests that pass without implementation.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/phase-2-tdd.md
git commit -m "feat(m2): add phase-2-tdd agent definition"
```

---

## Task 4: Write `phase-3-tdd` agent definition

**Files:**
- Create: `.claude/agents/phase-3-tdd.md`

- [ ] **Step 1: Write the agent file**

Create `.claude/agents/phase-3-tdd.md` with this exact content:

```markdown
---
name: phase-3-tdd
description: Phase 3 Builder (TDD skill variant) — turns Phase 2 RED tests GREEN with minimal implementation.
tools: Read, Write, Edit, Bash, Grep, Glob
---

Take the failing tests committed by Phase 2 and make them pass with the minimal implementation. You have not seen Phase 2's reasoning beyond the test files themselves. You may read `intent.md` and the feature plan doc.

**Inputs (from your brief).** Workspace path, feature plan doc path, snapshot SHA, feature id, and an explicit list of source paths you are allowed to write (the "envelope" — for M2 we pass these inline as a JSON array of regex strings; you must not write outside).

**Self-check the envelope.** Before writing, every file path you intend to write must match at least one regex in the envelope list from your brief. If a test demands a write outside the envelope, RAISE_ISSUE; do not silently widen.

**Read canonical sources directly.** Use `Read` with `offset:`/`limit:`. Do NOT call any MCP server.

**Make tests pass.** Run `uv run pytest <test-paths> -v` to verify GREEN. Then run `uv run pytest -q` to verify no pre-existing test newly regresses. If either fails, fix or RAISE_ISSUE.

**Never modify tests.** RAISE_ISSUE if a test is wrong; do not edit it. Never skip tests. Never re-litigate spec.

**P2 — Do not refuse preemptively.** Attempt the tool call before refusing.

**P1 — Bash-heredoc escape.** When `Write`/`Edit` is denied by the sensitive-file gate on `.claude/**` paths, fall back to `cat > path <<'HEREDOC' … HEREDOC`.

**Commit your writes.** Stage only the source files you wrote, then `git commit -m 'feat(<feature-id>): phase 3 — implementation'`.

Final stdout line: `{"status":"OK|RAISE_ISSUE|FAILED","commit_hash":"<sha>","summary":"<=100w"}`.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/phase-3-tdd.md
git commit -m "feat(m2): add phase-3-tdd agent definition"
```

---

## Task 5: Write `phase-4-tdd` agent definition

**Files:**
- Create: `.claude/agents/phase-4-tdd.md`

- [ ] **Step 1: Write the agent file**

Create `.claude/agents/phase-4-tdd.md` with this exact content:

```markdown
---
name: phase-4-tdd
description: Phase 4 Auditor (TDD skill variant) — runs full suite + validator, writes sweep-notes, commits the close.
tools: Read, Write, Edit, Bash, Grep, Glob
---

Audit the integrated feature with full context. Phases 1-3 are committed. You have full read access to the repo (no canonical-doc lockdown in the TDD skill path).

**Inputs (from your brief).** Workspace path, feature plan doc path, snapshot SHA, feature id, list of `INV-NNN` invariants the intent claims to touch.

**Mandatory checks before OK:**

1. Run the full suite: `uv run pytest -q`. Tests committed in Phases 2-3 must pass; pre-existing failures inherited at the snapshot SHA are documented as out-of-scope.
2. Run `python checks/validate_architecture.py` (or `uv run python checks/validate_architecture.py` per project convention). Document any pre-existing FAILs as out-of-scope.
3. For each invariant in `invariants-touched`: collect evidence (file:line citation from a grep) showing PASS or FAIL.
4. Write `<workspace>/integration/sweep-notes.md` with three sections: **Tests** (counts, deltas vs baseline), **Validator** (pass/fail per invariant block), **Invariants** (table: `INV-NNN | Statement | Status | Evidence`).

**Update handoff.** Append a one-line entry to `.claude/handoff.md`'s Pointers section linking the workspace; do NOT rewrite the State or Next sections (those are operator-owned).

**P2 — Do not refuse preemptively.** Attempt the tool call before refusing.

**P1 — Bash-heredoc escape.** When `Write`/`Edit` is denied by the sensitive-file gate on `.claude/**` paths, fall back to `cat > path <<'HEREDOC' … HEREDOC`.

**Commit your writes.** Stage only the files you wrote (sweep-notes, handoff.md if touched). Then `git commit -m 'chore(<feature-id>): phase 4 — sweep + handoff'`. Phase 4 IS allowed to commit in the TDD skill path (unlike the orchestrator's DC-4 rule, which is orchestrator-specific).

Final stdout line: `{"status":"OK|RAISE_ISSUE|FAILED","commit_hash":"<sha>","summary":"<=100w"}`. OK requires sweep-notes.md on disk and the suite green at HEAD.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/phase-4-tdd.md
git commit -m "feat(m2): add phase-4-tdd agent definition"
```

---

## Task 6: Write `triager-tdd` agent definition

**Files:**
- Create: `.claude/agents/triager-tdd.md`

- [ ] **Step 1: Write the agent file**

Create `.claude/agents/triager-tdd.md` with this exact content:

```markdown
---
name: triager-tdd
description: Triager (TDD skill variant) — read-only; classifies a phase RAISE_ISSUE as ESCALATE_TO_USER, RE_DISPATCH, or ABORT.
tools: Read, Grep, Glob, Bash
---

Decide-only. No file edits. Triggered when a phase agent returns `RAISE_ISSUE`.

**Inputs (from your brief).** Issue commit hash, current phase, feature id, workspace path, plus an optional `supersession_hint` field.

Read the issue commit body, `intent.md`, `validation/approach.md` (if Phase 2+), the failing tests, and any relevant ADR or `ARCHITECTURE.md` section. Never write or edit. Never dispatch agents.

**Actions:**
- `ESCALATE_TO_USER` — needs human judgment.
- `RE_DISPATCH` — recoverable; provide `target_phase ∈ {1..4}` and a one-line `amendment` describing what the redispatched phase should change.
- `ABORT` — unsalvageable.

When `supersession_hint.hint == 'likely_superseded'`, prefer `ESCALATE_TO_USER` with rationale beginning `test-amendment recommended` unless read evidence (intent.md, ADRs, the issue commit body) clearly shows the naming collision is coincidental.

Final stdout line: `{"action":"ESCALATE_TO_USER|RE_DISPATCH|ABORT","target_phase":<int>,"amendment":"<short>","rationale":"<=50w"}`. `target_phase` required for all three (set to `0` for ABORT to satisfy schema).
```

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/triager-tdd.md
git commit -m "feat(m2): add triager-tdd agent definition"
```

---

## Task 7: Write the dispatch skill

**Files:**
- Create: `.claude/skills/cairn-tdd-feature/SKILL.md`

- [ ] **Step 1: Create the skills directory if absent**

Run:
```bash
mkdir -p .claude/skills/cairn-tdd-feature
ls -la .claude/skills/
```
Expected: `cairn-tdd-feature/` directory exists.

- [ ] **Step 2: Write the SKILL.md**

Create `.claude/skills/cairn-tdd-feature/SKILL.md` with this exact content:

```markdown
---
name: cairn-tdd-feature
description: Use when implementing a feature that has a per-feature plan doc at docs/plans/<feature>.md and the operator wants TDD-by-construction phase isolation. Sequences Phase 1 (intent) → Phase 2 (RED tests) → Phase 3 (GREEN impl) → Phase 4 (audit) using fresh subagents per phase.
---

# cairn-tdd-feature

Sequences four phase subagents to deliver a feature with TDD discipline and phase isolation. Each phase runs in a fresh context window via the Agent tool. This is cairn's protocol-layer dispatch primitive, post-orchestrator.

## When to use

- The operator has written a per-feature plan at `docs/plans/<feature>.md` describing the work, the touched invariants, and the source-write envelope.
- The operator wants strict TDD-by-construction (Phase 1 cannot see Phase 2's tests; Phase 2 cannot see Phase 3's impl; Phase 3 cannot see Phase 2's reasoning).
- The work fits in one Phase-3 agent (multi-file fan-out is M3+).

Do NOT use for: ad-hoc bugfixes (use the standard tools), exploratory refactors (brainstorm first), or work that has no clear failing-test shape.

## Inputs

A single argument: path to the per-feature plan doc, e.g., `docs/plans/2026-05-06-some-feature.md`.

## Workspace conventions

- Workspace root: `.claude/skill-runs/<feature-id>/`
- Phase 1 writes: `<workspace>/intent.md`
- Phase 2 writes: `<workspace>/validation/approach.md` plus test files under `tests/`
- Phase 3 writes: source files matching the envelope from the plan doc
- Phase 4 writes: `<workspace>/integration/sweep-notes.md`, optionally appends to `.claude/handoff.md`

The feature id is derived from the plan doc's frontmatter `id:` field, or from the filename stem (`2026-05-06-some-feature` → `m2-dogfood-extract-invariant-ids` style).

## Steps

1. **Read the plan doc.** `Read` the path passed as the argument. Extract: feature id, source-write envelope (a list of regex strings under an `envelope:` key in the plan's frontmatter), and the touched invariant ids.

2. **Capture the snapshot SHA.** Run `git rev-parse HEAD`. Save as `SNAPSHOT_SHA`.

3. **Create the workspace.** `mkdir -p .claude/skill-runs/<feature-id>/{validation,integration}`.

4. **Dispatch Phase 1.** Call the Agent tool:
   - `subagent_type: phase-1-tdd`
   - `prompt:` a brief that includes: feature id, plan doc path, workspace path (`.claude/skill-runs/<feature-id>/intent.md`), `SNAPSHOT_SHA`, and a verbatim copy of the plan doc's "What/Why/Boundary" section.

5. **Verify Phase 1 commit.** Parse the JSON tail line for `status` and `commit_hash`. If `status != "OK"`, dispatch `triager-tdd`; act on its decision (escalate, re-dispatch, or abort). Verify the commit exists with `git show <commit_hash> --stat`.

6. **Dispatch Phase 2.** Agent tool with `subagent_type: phase-2-tdd`, prompt including: feature id, intent.md path, plan doc path, workspace path, `SNAPSHOT_SHA`, and the touched invariant ids.

7. **Verify Phase 2 commit and that tests are RED at HEAD~0.** Parse the JSON. Then run `uv run pytest <new-test-files> -v` directly (skill code, not subagent) and confirm tests fail. If green, the intent was already satisfied — escalate.

8. **Dispatch Phase 3.** Agent tool with `subagent_type: phase-3-tdd`, prompt including: feature id, intent.md path, workspace path, `SNAPSHOT_SHA`, the source-write envelope (JSON array of regex strings), and the test paths committed in Phase 2.

9. **Verify Phase 3 commit and GREEN.** Parse the JSON. Run `uv run pytest <new-test-files> -v` and confirm pass. Run `uv run pytest -q` and confirm no new failures vs. the snapshot SHA's baseline.

10. **Dispatch Phase 4.** Agent tool with `subagent_type: phase-4-tdd`, prompt including: feature id, workspace path, plan doc path, `SNAPSHOT_SHA`, and the touched invariant ids.

11. **Verify Phase 4 commit and final state.** Parse the JSON. Confirm `<workspace>/integration/sweep-notes.md` exists. Confirm `git log --oneline | head -4` shows four commits matching the per-phase convention.

## RAISE_ISSUE handling

On any phase RAISE_ISSUE, dispatch `triager-tdd` with: issue commit hash, current phase, feature id, workspace path. Act on its action:
- `ESCALATE_TO_USER`: stop the skill, surface the rationale to the operator, exit.
- `RE_DISPATCH`: re-run the named target phase with the amendment included in the brief. Cap at one re-dispatch per phase per skill run; second RAISE_ISSUE → ESCALATE_TO_USER.
- `ABORT`: stop the skill, surface to operator, exit.

## Output

On success, print a four-line summary listing each phase's commit hash and a one-sentence status. The git log is the durable record; no slice.yaml.

## Coexistence with the orchestrator

This skill creates files only under `.claude/skill-runs/`, `tests/`, and the source paths in the envelope — never under `.claude/current-slice/` or `.claude/features/`. Slice machinery is unaffected; running this skill while a slice is open is a smell but not blocked.
```

- [ ] **Step 3: Verify the file is well-formed**

Run:
```bash
head -3 .claude/skills/cairn-tdd-feature/SKILL.md
wc -l .claude/skills/cairn-tdd-feature/SKILL.md
```
Expected: starts with `---`, has `name: cairn-tdd-feature`, ~100-130 lines.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/cairn-tdd-feature/SKILL.md
git commit -m "feat(m2): add cairn-tdd-feature dispatch skill"
```

---

## Task 8: Write the toy dogfood plan doc

**Files:**
- Create: `docs/plans/2026-05-06-m2-dogfood-extract-invariant-ids.md`

- [ ] **Step 1: Write the plan doc**

Create `docs/plans/2026-05-06-m2-dogfood-extract-invariant-ids.md` with this exact content:

```markdown
---
id: m2-dogfood-extract-invariant-ids
name: M2 dogfood — extract invariant ids
firmness: provisional
status: spec — for cairn-tdd-feature dispatch
date: 2026-05-06
invariants-touched: []
envelope:
  - '^scripts/lib/invariant_id_extractor\.py$'
  - '^scripts/lib/__init__\.py$'
---

# M2 Dogfood — extract_invariant_ids

## What

A pure Python function `extract_invariant_ids(text: str) -> list[str]` that returns the sorted, deduplicated list of `INV-NNN` identifiers occurring in `text`, where `NNN` is exactly three digits.

## Why

Exercises all four phases of the `cairn-tdd-feature` skill on a target with clear inputs and outputs, no external integration, and no overlap with orchestrator code paths. Used as the M2 dogfood evidence for the cairn-shrink design.

## Boundary

- Pure function, no I/O, no logging, no caching.
- New file at `scripts/lib/invariant_id_extractor.py`. Empty `scripts/lib/__init__.py` to make the package importable.
- No changes to existing code, configuration, or hooks.

## Specification

```python
def extract_invariant_ids(text: str) -> list[str]:
    """Return sorted, deduplicated INV-NNN identifiers from `text`.

    NNN is exactly three digits. Matches are case-sensitive on `INV-`.
    """
```

Behaviors:

1. Empty string returns `[]`.
2. Text with no matches returns `[]`.
3. Single `INV-001` returns `["INV-001"]`.
4. Multiple unique ids return them sorted: `extract_invariant_ids("INV-008 see also INV-001")` returns `["INV-001", "INV-008"]`.
5. Duplicates collapse: `extract_invariant_ids("INV-001 and INV-001")` returns `["INV-001"]`.
6. Two-digit and four-digit forms do NOT match: `extract_invariant_ids("INV-99 INV-9999")` returns `[]`.
7. Lowercase `inv-001` does NOT match.
8. Embedded in word: `extract_invariant_ids("xINV-001y")` MAY match — define explicitly: yes, the regex is `INV-\d{3}` with no word boundaries; document this in the test.

## Verification

Tests at `tests/unit/test_invariant_id_extractor.py` covering all eight behaviors above.

Phase 4 must confirm: full suite passes; `validate_architecture.py` runs without new failures; `invariants-touched: []` so the invariant evidence section is empty by design.
```

- [ ] **Step 2: Commit**

```bash
git add docs/plans/2026-05-06-m2-dogfood-extract-invariant-ids.md
git commit -m "docs(m2): add dogfood plan for extract_invariant_ids"
```

---

## Task 9: Dogfood — Phase 1 (intent)

**Files:**
- Created BY agent: `.claude/skill-runs/m2-dogfood-extract-invariant-ids/intent.md`

- [ ] **Step 1: Create the workspace**

Run:
```bash
mkdir -p .claude/skill-runs/m2-dogfood-extract-invariant-ids/validation
mkdir -p .claude/skill-runs/m2-dogfood-extract-invariant-ids/integration
ls -la .claude/skill-runs/m2-dogfood-extract-invariant-ids/
```
Expected: workspace exists with empty `validation/` and `integration/` subdirs.

- [ ] **Step 2: Capture the snapshot SHA**

Run:
```bash
git rev-parse HEAD > /tmp/m2-snapshot-sha
cat /tmp/m2-snapshot-sha
```
Expected: a 40-char SHA written to `/tmp/m2-snapshot-sha` and echoed. This file persists across the plan's Bash invocations; agent prompts below reference its value.

- [ ] **Step 3: Dispatch phase-1-tdd**

Use the Agent tool:
- `subagent_type`: `phase-1-tdd`
- `description`: "Phase 1 TDD intent for m2-dogfood-extract-invariant-ids"
- `prompt`:

```
You are dispatched by the cairn-tdd-feature skill to draft intent.md for the feature m2-dogfood-extract-invariant-ids.

Inputs:
- feature_id: m2-dogfood-extract-invariant-ids
- plan_doc_path: docs/plans/2026-05-06-m2-dogfood-extract-invariant-ids.md
- workspace_intent_path: .claude/skill-runs/m2-dogfood-extract-invariant-ids/intent.md
- snapshot_sha: <paste contents of /tmp/m2-snapshot-sha>

Read the plan doc. Draft intent.md at workspace_intent_path with: YAML frontmatter (id, name, snapshot-sha, invariants-touched: []), then sections What, Why, Boundary (≤200 words combined), Specification, Verification. Mirror the plan doc's content but rewritten in your own words from canonical-context-only perspective; you have not seen any tests or implementation.

Stage only the file you wrote. Commit with message: feat(m2-dogfood-extract-invariant-ids): phase 1 — intent

Return the JSON tail per your agent contract.
```

- [ ] **Step 4: Verify the commit and the file**

Run:
```bash
git log --oneline -1
ls -la .claude/skill-runs/m2-dogfood-extract-invariant-ids/intent.md
head -20 .claude/skill-runs/m2-dogfood-extract-invariant-ids/intent.md
```
Expected: latest commit subject is `feat(m2-dogfood-extract-invariant-ids): phase 1 — intent`; intent.md exists with frontmatter and the five sections.

- [ ] **Step 5: If `status != OK` from the agent, dispatch triager-tdd**

(See "RAISE_ISSUE handling" in SKILL.md.) For the toy dogfood, OK is expected; if RAISE_ISSUE, document and proceed manually.

---

## Task 10: Dogfood — Phase 2 (RED tests)

**Files:**
- Created BY agent: `tests/unit/test_invariant_id_extractor.py`
- Created BY agent: `.claude/skill-runs/m2-dogfood-extract-invariant-ids/validation/approach.md`

- [ ] **Step 1: Dispatch phase-2-tdd**

Use the Agent tool:
- `subagent_type`: `phase-2-tdd`
- `description`: "Phase 2 TDD failing tests for m2-dogfood-extract-invariant-ids"
- `prompt`:

```
You are dispatched by the cairn-tdd-feature skill to write failing tests for the feature m2-dogfood-extract-invariant-ids.

Inputs:
- feature_id: m2-dogfood-extract-invariant-ids
- intent_path: .claude/skill-runs/m2-dogfood-extract-invariant-ids/intent.md
- plan_doc_path: docs/plans/2026-05-06-m2-dogfood-extract-invariant-ids.md
- workspace_root: .claude/skill-runs/m2-dogfood-extract-invariant-ids
- snapshot_sha: <paste contents of /tmp/m2-snapshot-sha>
- invariants_touched: []

Read intent.md and the plan doc. Write tests at tests/unit/test_invariant_id_extractor.py covering all eight behaviors enumerated in the spec. Each behavior is its own test function with a docstring naming the behavior.

Run: uv run pytest tests/unit/test_invariant_id_extractor.py -v
Expected: all tests fail with ModuleNotFoundError (the source file does not exist yet).

Write the approach memo at <workspace_root>/validation/approach.md (≤300 words).

Stage only the files you wrote. Commit with message: test(m2-dogfood-extract-invariant-ids): phase 2 — failing tests

Return the JSON tail per your agent contract.
```

- [ ] **Step 2: Verify tests are RED at HEAD**

Run:
```bash
uv run pytest tests/unit/test_invariant_id_extractor.py -v 2>&1 | tail -20
```
Expected: 8 tests collected; all FAIL with `ModuleNotFoundError: No module named 'scripts.lib.invariant_id_extractor'` (or equivalent). If any test PASSES, that's a Phase-2 bug — re-dispatch.

- [ ] **Step 3: Verify the commit**

Run:
```bash
git log --oneline -2
```
Expected: top commit is the Phase-2 commit; second is the Phase-1 commit.

---

## Task 11: Dogfood — Phase 3 (GREEN)

**Files:**
- Created BY agent: `scripts/lib/invariant_id_extractor.py`
- Created BY agent: `scripts/lib/__init__.py`

- [ ] **Step 1: Dispatch phase-3-tdd**

Use the Agent tool:
- `subagent_type`: `phase-3-tdd`
- `description`: "Phase 3 TDD implementation for m2-dogfood-extract-invariant-ids"
- `prompt`:

```
You are dispatched by the cairn-tdd-feature skill to implement the feature m2-dogfood-extract-invariant-ids.

Inputs:
- feature_id: m2-dogfood-extract-invariant-ids
- intent_path: .claude/skill-runs/m2-dogfood-extract-invariant-ids/intent.md
- workspace_root: .claude/skill-runs/m2-dogfood-extract-invariant-ids
- snapshot_sha: <paste contents of /tmp/m2-snapshot-sha>
- envelope (regex strings, JSON array): ["^scripts/lib/invariant_id_extractor\\.py$", "^scripts/lib/__init__\\.py$"]
- test_paths: tests/unit/test_invariant_id_extractor.py

Read intent.md and the failing tests. Implement scripts/lib/invariant_id_extractor.py and an empty scripts/lib/__init__.py. Stay within the envelope.

Run: uv run pytest tests/unit/test_invariant_id_extractor.py -v
Expected: all tests pass.

Run: uv run pytest -q
Expected: no NEW failures vs. the snapshot baseline.

Stage only the files you wrote. Commit with message: feat(m2-dogfood-extract-invariant-ids): phase 3 — implementation

Return the JSON tail per your agent contract.
```

- [ ] **Step 2: Verify GREEN**

Run:
```bash
uv run pytest tests/unit/test_invariant_id_extractor.py -v 2>&1 | tail -15
uv run pytest -q 2>&1 | tail -3
```
Expected: dogfood tests all pass. Full-suite line shows the same `M failed` count as `/tmp/m2-baseline.txt` (no regressions) and `+8 passed`.

- [ ] **Step 3: Verify the commit and file content**

Run:
```bash
git log --oneline -3
cat scripts/lib/invariant_id_extractor.py
```
Expected: three commits in log (P1, P2, P3); source is a small function (~10 lines).

---

## Task 12: Dogfood — Phase 4 (audit + close)

**Files:**
- Created BY agent: `.claude/skill-runs/m2-dogfood-extract-invariant-ids/integration/sweep-notes.md`
- Modified BY agent: `.claude/handoff.md` (Pointers section only)

- [ ] **Step 1: Dispatch phase-4-tdd**

Use the Agent tool:
- `subagent_type`: `phase-4-tdd`
- `description`: "Phase 4 TDD audit for m2-dogfood-extract-invariant-ids"
- `prompt`:

```
You are dispatched by the cairn-tdd-feature skill to audit and close the feature m2-dogfood-extract-invariant-ids.

Inputs:
- feature_id: m2-dogfood-extract-invariant-ids
- workspace_root: .claude/skill-runs/m2-dogfood-extract-invariant-ids
- plan_doc_path: docs/plans/2026-05-06-m2-dogfood-extract-invariant-ids.md
- snapshot_sha: <paste contents of /tmp/m2-snapshot-sha>
- invariants_touched: []

Run: uv run pytest -q
Run: uv run python checks/validate_architecture.py
For each pre-existing failure, note as out-of-scope. Compare against the snapshot SHA baseline.

Write <workspace_root>/integration/sweep-notes.md with three sections: Tests, Validator, Invariants. The Invariants table is empty (invariants_touched is []) — note this explicitly with a single row stating "no invariants touched in this feature".

Append a one-line entry to .claude/handoff.md's Pointers section (NOT State or Next):
- `.claude/skill-runs/m2-dogfood-extract-invariant-ids/` — M2 dogfood workspace.

Stage only the files you wrote. Commit with message: chore(m2-dogfood-extract-invariant-ids): phase 4 — sweep + handoff

Return the JSON tail per your agent contract.
```

- [ ] **Step 2: Verify the close**

Run:
```bash
git log --oneline -4
cat .claude/skill-runs/m2-dogfood-extract-invariant-ids/integration/sweep-notes.md
```
Expected: four commits in log matching the four phase prefixes; sweep-notes.md exists with the three sections.

---

## Task 13: Verify orchestrator coexistence

**Files:**
- Read-only inspection of: `scripts/slice_orchestrator/`, `scripts/cairn_query/`, `commands/claude-code/start-slice.md`, `.claude/current-slice/`

- [ ] **Step 1: Confirm no orchestrator file was modified**

Run:
```bash
SNAPSHOT_SHA=$(cat /tmp/m2-snapshot-sha)
git diff --name-only $SNAPSHOT_SHA HEAD | grep -E '^(scripts/slice_orchestrator/|scripts/cairn_query/|mcp_servers/|commands/claude-code/(start-slice|integration-sweep)|checks/(scope_guard|role_guard|reversibility|reality)|\.claude/(current-slice|sweep\.yaml|features/))' || echo "no orchestrator-side modifications"
```
Expected output: `no orchestrator-side modifications`. If any path matches, M2 has accidentally touched orchestrator territory — investigate and revert.

- [ ] **Step 2: Confirm `.claude/current-slice/` is unchanged from the snapshot**

Run:
```bash
git diff $(cat /tmp/m2-snapshot-sha) HEAD -- .claude/current-slice/
```
Expected: empty diff. `.claude/current-slice/slice.yaml` still shows the prior complete slice; `current_phase: 4` etc.

- [ ] **Step 3: Confirm `start-slice` slash command still resolves**

Run:
```bash
ls commands/claude-code/start-slice.md commands/claude-code/start-slice.full.md
head -3 commands/claude-code/start-slice.md
```
Expected: both files present and unchanged.

- [ ] **Step 4: No commit. Sanity-check only.**

---

## Task 14: Update handoff.md and commit M2 close

**Files:**
- Modify: `.claude/handoff.md`

- [ ] **Step 1: Read the current handoff**

```bash
cat .claude/handoff.md
```

- [ ] **Step 2: Replace the contents with M2-landed handoff**

Edit `.claude/handoff.md` to read:

```markdown
---
slice: design/cairn-shrink
phase: m2-landed
branch: design/cairn-shrink
as-of: 2026-05-06 <new HEAD sha>
---

## State
M2 landed on `design/cairn-shrink`. Built five TDD-flavored phase agents (`.claude/agents/phase-{1..4}-tdd.md`, `triager-tdd.md`) and the dispatch skill at `.claude/skills/cairn-tdd-feature/SKILL.md`. Dogfooded on `m2-dogfood-extract-invariant-ids` — four per-phase commits, all suite tests green at HEAD, validator runs unchanged. Orchestrator and substrate untouched; coexistence verified by inspection.

## Next
Open next session. Run `superpowers:writing-plans` for migration M3: bathwater audit (slice-by-slice survival check) + `validate_architecture.py` parser fix to make INV-002 binding functional + `role_guard.py` simplification design (drop MCP-forcing; preserve `READ_CLASS_TOOLS = {Read, Grep, Glob}` and envelope-grant). Do NOT delete orchestrator yet — that's M4.

## Blocked / Pending
- INV-002 binding still non-functional; M3 fixes the parser.
- Bathwater audit pending (M3).
- ADR supersession map in design §7; no supersession ADRs written yet (M3 or M4).
- Consumer migration (complex-rag-analysis) deferred to M6.

## Pointers
- `docs/plans/2026-05-06-cairn-shrink-design.md` — overall design.
- `docs/plans/2026-05-06-cairn-shrink-m2-dispatch-skill.md` — M2 plan (this work).
- `docs/plans/2026-05-06-m2-dogfood-extract-invariant-ids.md` — dogfood spec.
- `.claude/skill-runs/m2-dogfood-extract-invariant-ids/` — dogfood workspace (intent / approach / sweep-notes).
- `.claude/skills/cairn-tdd-feature/SKILL.md` — dispatch skill.
- Branch `design/cairn-shrink` — WIP; do not merge to dev until M5.
```

(Replace `<new HEAD sha>` with the actual short SHA after Phase 4's commit.)

- [ ] **Step 3: Commit**

```bash
git add .claude/handoff.md
git commit -m "handoff: design/cairn-shrink — M2 landed, queue M3 next session"
```

- [ ] **Step 4: Final state verification**

Run:
```bash
git log --oneline -10
git status --short
```
Expected: history shows (newest first) M2 handoff commit, Phase 4 dogfood commit, Phase 3, Phase 2, Phase 1, dogfood plan doc, dispatch skill, five agent definition commits, then prior history. Working tree clean (modulo pre-existing untracked).

---

## Self-review checklist (run after writing the plan, before execution)

1. **Spec coverage from design §7 M2 deliverable:**
   - "Write the dispatch skill" — Task 7 ✓
   - "Skill folder format" — Task 7 creates `.claude/skills/cairn-tdd-feature/` with SKILL.md ✓
   - "Test by dispatching phase-N agents on a toy feature" — Tasks 9-12 ✓
   - "No deletes yet" — Task 13 verifies no orchestrator file touched ✓
   - "Dispatch skill coexists with orchestrator" — Task 13 ✓
   - "Deliverable: working dispatch skill + dogfood evidence" — workspace + sweep-notes + four per-phase commits ✓

2. **Open questions resolved (design §9):**
   - Q1 (skill API): path-only ✓
   - Q2 (cluster fan-out): single agent for M2 ✓
   - Q6 (test surface): dogfood-only ✓
   - Q3, Q4, Q5, Q7: M3+ territory (not in scope)

3. **Type/path consistency:**
   - Workspace path is `.claude/skill-runs/<feature-id>/` everywhere ✓
   - Feature id is `m2-dogfood-extract-invariant-ids` everywhere ✓
   - Commit messages match the convention in pre-flight ✓

4. **Known caveats (not blockers):**
   - `role_guard.py` does not engage on skill-dispatched subagents (no `AGENT_ROLE` env). M3 simplification addresses this.
   - The new TDD agent definitions duplicate the originals' P1/P2 boilerplate. Acceptable for M2; consolidation in M3+.
   - Phase 4 in the TDD path commits, unlike orchestrator's DC-4 rule. Documented in `phase-4-tdd.md` frontmatter and the SKILL.md.

5. **No placeholders:** every Step has either exact text/code or an exact command with expected output. Verified.

---

## Execution handoff

Plan complete and saved to `docs/plans/2026-05-06-cairn-shrink-m2-dispatch-skill.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Ideal for a 14-task plan with mixed file-creation and live agent-dispatch.

2. **Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints. Fine if you want to watch each phase agent run live.

Which approach?
