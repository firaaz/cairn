# D1 — Startup Floor Cuts Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduce cairn session turn-1 context from ~30,300 tokens to ~27,000–28,000 tokens via reversible, low-risk changes that ship as a single bundled commit outside the slice pipeline.

**Architecture:** Three independent changes applied to documentation and settings only: (1) trim `CLAUDE.md` from a 7.7 KB narrative to a ~400-token safety cheat sheet, moving the narrative content into `docs/operational-reference.md` which loads on demand; (2) relocate globally-enabled plugins from `~/.claude/settings.json` to per-project `.claude/settings.json`, keeping only `claude-md-management` in cairn (needed for the Slice #3 self-learn flow); (3) document that the `superpowers` SessionStart hook injection is not disableable in Claude Code 2.1.101 — it becomes a deferred item, not an active task. No protocol changes, no slice, no code.

**Tech Stack:** Markdown, JSON (settings), bash, git. Verification uses python stdlib against `~/.claude/projects/.../*.jsonl` transcripts.

**Design reference:** `docs/plans/2026-04-11-context-discipline-design.md` — the validated design this plan implements.

**Scope-guard note:** `SLICE-001` is `status: complete`; scope-guard is dormant for the duration of this work. No slice envelope is declared and none is needed.

---

## Task 1: Capture the baseline measurement

**Files:**
- Create: `docs/plans/measurements/2026-04-11-baseline.txt`

**Why a baseline first:** D1's success criteria are measurable (turn-1 token delta). Without a baseline captured before any changes, the post-change measurement is unfalsifiable.

**Step 1.1: Measure turn-1 context on the 5 most recent cairn sessions**

Run:
```bash
python3 <<'PY'
import json, os, glob
paths = sorted(
    glob.glob('/Users/mohammed.farook/.claude/projects/-Users-mohammed-farook-Developer-lab-cairn/*.jsonl'),
    key=os.path.getmtime, reverse=True
)[:5]
print('baseline turn-1 context (cairn, 5 most recent sessions):')
print('-' * 60)
for p in paths:
    with open(p) as f:
        for line in f:
            obj = json.loads(line)
            u = obj.get('message', {}).get('usage')
            if u:
                total = u.get('input_tokens',0) + u.get('cache_creation_input_tokens',0) + u.get('cache_read_input_tokens',0)
                name = os.path.basename(p)[:8]
                print(f'  {name}  total={total:>6}  (cc={u.get("cache_creation_input_tokens",0)} cr={u.get("cache_read_input_tokens",0)})')
                break
PY
```

**Step 1.2: Record the result**

Write the command output to `docs/plans/measurements/2026-04-11-baseline.txt`. The file will be committed as part of the D1 bundle so the measurement is reproducible and the delta is defensible.

**Expected:** 5 lines, each in the 28k–33k range.

**Step 1.3: Commit**

```bash
mkdir -p docs/plans/measurements
# (write the file with the command output captured in Step 1.1)
git add docs/plans/measurements/2026-04-11-baseline.txt
git commit -m "docs(plans): capture D1 baseline turn-1 measurements"
```

---

## Task 2: Extend `docs/operational-reference.md` with the cairn-internals content

**Files:**
- Modify: `docs/operational-reference.md` (append a new section at the end)

**Why this task runs before Task 3:** `CLAUDE.md` should never link to content that doesn't exist yet. Write the destination first, then redirect.

**Step 2.1: Add a "Cairn repo internals" section at the end of `docs/operational-reference.md`**

Append the following content verbatim at the bottom of the file (after the last existing section, preserving trailing newline):

```markdown

## Cairn repo internals (load on demand)

This section documents cairn's own repo layout and working practices. It is deliberately not in `CLAUDE.md` — CLAUDE.md is a safety cheat sheet, not a README. Load this section when doing non-trivial work on cairn itself.

### What this repo is

Cairn is a methodology repository, not a runnable application or library. It contains the protocols, shell-script hooks, slash commands, and documentation that implement a four-phase slice pipeline (Intent → Validation → Implementation → Integration), a decision protocol for architectural work, and a substrate validator. It is consumed by *other* projects, which symlink it as `.slice-system/` and reference its scripts/docs from their own `.claude/` configuration. Cairn also consumes itself the same way — a `.slice-system → .` self-symlink lets the same pipeline run on cairn's own development (see ADR-001 for the bootstrap exception that put this in place).

Status: solo, pre-v1. See `docs/roadmap.md` for the work required to reach v1, and `CHANGELOG.md` for the delta since v0.1.0.

### Repo layout

- `checks/` — POSIX shell hooks. PreToolUse / PostToolUse handlers that read JSON from stdin. Three hooks: `reversibility-guard.sh` (blocks destructive ops, enforces ADR append-only), `scope-guard.sh` (blocks edits outside the current slice envelope), `reality-check.sh` (runs `ruff format` + `ruff check --fix` on Python edits).
- `commands/claude-code/` — Markdown slash commands (`/start-slice`, `/decision`, `/catchup`, `/handoff`, `/integration-sweep`, `/new-adr`, `/refresh-architecture`, `/status`). A `commands/windsurf/` mirror is roadmapped but does not exist yet.
- `docs/` — Three layers: `operational-reference.md` (Layer 1, this file), `spec-v1.md` (Layer 2, canonical spec — deliberately not auto-loaded), `vision.md` + `roadmap.md` (what v1 commits to and the ordered slice sequence to get there).
- `scripts/validate_architecture.py` — single-file validator checking consistency between `docs/ARCHITECTURE.md` invariants and the `docs/adr/` corpus.
- `templates/` — currently empty; template extraction is a may-land-before-v1 item.

### Working on cairn itself

There is no build, no package manifest, and no test suite in this repo. Common operations:

- **Lint a hook script:** `shellcheck checks/<name>.sh` (if shellcheck is installed).
- **Smoke-test a hook locally:** the hooks read JSON from stdin. Example:
  ```
  echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | bash checks/reversibility-guard.sh
  ```
  Exit code 2 + JSON on stdout = blocked. Exit 0 = allowed.
- **Run the validator:** `python3 scripts/validate_architecture.py` (stdlib only). Fails in this repo until the meta-dogfood `docs/ARCHITECTURE.md` and `docs/adr/` exist — expected, not a bug.

When doing non-trivial work on cairn, the intended flow is meta-dogfood: use cairn's own slice pipeline (via the slash commands) to develop cairn. Per CHANGELOG, this is not yet wired up — the first cairn slice is supposed to set it up.

### Editing rules expanded

- **Scope-guard goes dormant when slice status is `complete` or `failed`** and always allows writes under `.claude/current-slice/`, `.claude/handoff.md`, `.claude/sweep.yaml`, `docs/adr/`, `docs/ARCHITECTURE.md`, `docs/lessons.md`. Auto-includes test mirrors of envelope source files. Override: `EXPAND_ENVELOPE=1`, which logs to `.claude/current-slice/envelope-expansions.log`.
- **Six v1 commitments** (`docs/vision.md`) are the spec for cairn's own development: agent-portable, parallelism-native, soft agent-split, meta-dogfoodable from slice #1, plastic phase shape through v1, explicit cognitive roles per phase. Don't lock in designs that contradict these — especially not a global "one active slice" pointer (parallelism is a v1 commitment, not a future feature).

### Documentation tiers — when to load what

If a question is operational ("what does Phase 2 receive as input?", "what does scope-guard allow?"), this file (`docs/operational-reference.md`) is sufficient. If a question is about the *why* (failure modes, the dual context-engineering / role-reset thesis, empirical support, what the system does and does not claim), read `docs/spec-v1.md`. The spec is long and intentionally kept out of default context — pull it in deliberately when needed.
```

**Step 2.2: Verify the file still parses as markdown**

Run:
```bash
head -1 docs/operational-reference.md
tail -5 docs/operational-reference.md
wc -l docs/operational-reference.md
```

Expected: header `# Development System` at top, new section content at bottom, line count has grown by the appended content.

**Step 2.3: Commit**

```bash
git add docs/operational-reference.md
git commit -m "docs(operational-reference): absorb cairn-internals content from CLAUDE.md

Consolidates repo layout, working-on-cairn commands, expanded editing
rules, and documentation tier guidance into the load-on-demand
operational reference. Destination for CLAUDE.md's narrative content
ahead of the D1 trim. Content is preserved, not deleted."
```

---

## Task 3: Rewrite `CLAUDE.md` as a safety cheat sheet

**Files:**
- Modify: `CLAUDE.md` (full rewrite)

**Step 3.1: Write the replacement content**

Replace the entire contents of `CLAUDE.md` with:

```markdown
# CLAUDE.md

Cairn is a methodology repo — slice pipeline, hooks, slash commands — consumed by other projects via a `.slice-system → .` symlink. No build, no test suite. For repo layout, working commands, expanded editing rules, and documentation tier guidance, load `docs/operational-reference.md` on demand. For the canonical spec (theory, failure modes, empirical support), load `docs/spec-v1.md` on demand.

## Safety-critical rules

**Edit canonical paths only, never via `.slice-system/`.** Slice-system files are symlinked from consumers; editing through the symlink produces tool-input paths starting with `.slice-system/`, which `scope-guard.sh:53` strips as a literal prefix. The resulting relative path matches no allowlist entry and the edit gets denied during an active slice. Always target `checks/...`, `commands/claude-code/...`, `scripts/...` directly.

**Hook dependencies.** All three `checks/*.sh` hooks require `jq`; `reality-check.sh` also needs `ruff`. Missing deps cause the hook to no-op with a stderr warning — enforcement silently disabled. Install both before any work in cairn:
```
brew install jq && uv tool install ruff
```

**Symlink recursion hazard.** `.slice-system → .` is an infinite depth loop for any tool that follows symlinks recursively. No current tool in this repo walks root recursively. If you add a `find`, a `glob("**/*")`, or anything that does, exclude `.slice-system` explicitly.

**ADRs are append-only.** `reversibility-guard.sh` allows `Write` on new ADRs and blocks overwriting existing ones. It allows `Edit` on an ADR only if `old_string`'s first line begins with `status:`, `superseded-by:`, `superseded_by:`, or `firmness:`. Multi-line `old_string` with a frontmatter keyword on a later line is intentionally treated as a body edit. Typo escape hatch: `ADR_EDITORIAL_FIX=1`.

**Force-push policy.** `git push --force` and `-f` are blocked by `reversibility-guard.sh`. `git push --force-with-lease` is allowed.
```

**Step 3.2: Verify the new CLAUDE.md is under 400 tokens**

Run:
```bash
wc -c CLAUDE.md
python3 -c "import sys; print('approx tokens:', round(open('CLAUDE.md').read().__len__() / 4))"
```

Expected: ~1,600 bytes, ~400 tokens. If the tokens estimate exceeds 450, trim one safety rule and re-verify (most likely candidates: the force-push note, or the ADR first-line explanation can be shortened).

**Step 3.3: Verify no broken internal references**

Run:
```bash
grep -c "operational-reference.md" CLAUDE.md
grep -c "spec-v1.md" CLAUDE.md
test -f docs/operational-reference.md && echo "operational-reference.md: exists"
test -f docs/spec-v1.md && echo "spec-v1.md: exists"
```

Expected: both CLAUDE.md references are present and both target files exist.

**Step 3.4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(claude.md): trim to safety cheat sheet, target ~400 tokens

Reduces CLAUDE.md from ~1,935 to ~400 tokens by keeping only the
five safety-critical rules (canonical paths, hook deps, symlink
recursion, ADR append-only, force-push policy) and redirecting
narrative content to docs/operational-reference.md which loads on
demand. Part of D1 floor cuts.

Savings: ~1,500 tokens off every session turn-1."
```

---

## Task 4: Relocate global plugins to per-project scope

**Files:**
- Modify: `/Users/mohammed.farook/.claude/settings.json`
- Modify: `/Users/mohammed.farook/Developer/lab/cairn/.claude/settings.json`

**Context:** Current state from `~/.claude/settings.json`:

```json
"enabledPlugins": {
  "context7@claude-plugins-official": true,
  "claude-md-management@claude-plugins-official": true,
  "commit-commands@claude-plugins-official": true
}
```

All three are globally enabled. They load in every project even when unused. Per the design, we move them out of global scope. Cairn needs `claude-md-management` for the Slice #3 self-learn flow — that one lands in the cairn project settings. `context7` and `commit-commands` are discretionary per project; cairn does not need them for the slice pipeline.

**Step 4.1: Read current global settings**

Run:
```bash
cat ~/.claude/settings.json
```

Expected: the three plugins in `enabledPlugins`, plus `effortLevel` and `attribution` keys.

**Step 4.2: Remove the three plugins from global settings**

Edit `~/.claude/settings.json` to change:

```json
"enabledPlugins": {
  "context7@claude-plugins-official": true,
  "claude-md-management@claude-plugins-official": true,
  "commit-commands@claude-plugins-official": true
},
```

to:

```json
"enabledPlugins": {},
```

Preserve all other keys (`effortLevel`, `attribution`) unchanged.

**Step 4.3: Verify the file still parses as valid JSON**

Run:
```bash
python3 -c "import json; print(json.load(open('/Users/mohammed.farook/.claude/settings.json')))"
```

Expected: dict with empty `enabledPlugins`, unchanged `effortLevel` and `attribution`.

**Step 4.4: Read current cairn project settings**

Run:
```bash
cat /Users/mohammed.farook/Developer/lab/cairn/.claude/settings.json
```

Expected: `enabledPlugins` contains only `superpowers@claude-plugins-official`, plus the three hooks config.

**Step 4.5: Add `claude-md-management` to cairn project settings**

Edit `/Users/mohammed.farook/Developer/lab/cairn/.claude/settings.json` to change:

```json
"enabledPlugins": {
  "superpowers@claude-plugins-official": true
},
```

to:

```json
"enabledPlugins": {
  "superpowers@claude-plugins-official": true,
  "claude-md-management@claude-plugins-official": true
},
```

Preserve the `hooks` block unchanged.

**Step 4.6: Verify the file still parses as valid JSON**

Run:
```bash
python3 -c "import json; d=json.load(open('/Users/mohammed.farook/Developer/lab/cairn/.claude/settings.json')); print(d['enabledPlugins']); print(list(d['hooks'].keys()))"
```

Expected: `{'superpowers@claude-plugins-official': True, 'claude-md-management@claude-plugins-official': True}` and `['PreToolUse', 'PostToolUse']`.

**Step 4.7: Commit the cairn project settings change**

The global `~/.claude/settings.json` is NOT under cairn's version control; it cannot be committed here. Only commit the cairn project settings change:

```bash
git add .claude/settings.json
git commit -m "claude(settings): enable claude-md-management at project scope

Adds claude-md-management to cairn's project-scoped plugins for the
Slice #3 self-learn flow (revise-claude-md + claude-md-improver
invocation at handoff). Global ~/.claude/settings.json is being
cleaned up in parallel — see D1 plan for the full rationale.

Part of D1 floor cuts."
```

**Note for the human:** the global `~/.claude/settings.json` edit is a one-time change made outside git. Document it in the completion report so it is not accidentally re-enabled later.

---

## Task 5: Document the D1.2 deferral (superpowers SessionStart hook)

**Files:**
- Create: `docs/plans/2026-04-11-d1-2-superpowers-hook-deferral.md`

**Why this task exists:** The design doc listed D1.2 (disable superpowers SessionStart hook injection) as an active item with a ~1,100-token saving. Investigation during planning (grep of the Claude Code 2.1.101 binary for `disabledHooks`, `disablePlugins`, `pluginHookOverrides` — all zero hits) confirmed there is no per-project setting to suppress a plugin-defined hook. D1.2 has no working override. Rather than silently drop it, we record the investigation and options for later.

**Step 5.1: Write the deferral note**

Create `docs/plans/2026-04-11-d1-2-superpowers-hook-deferral.md` with the following contents:

```markdown
# D1.2 — Superpowers SessionStart Hook Override: Deferred

**Date:** 2026-04-11
**Status:** Deferred — no working per-project override in Claude Code 2.1.101
**Related:** `docs/plans/2026-04-11-context-discipline-design.md` D1.2; `docs/plans/2026-04-11-d1-floor-cuts-plan.md` Task 5

## Problem

The `superpowers` plugin's `SessionStart` hook (`~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/hooks/session-start`) injects the full `using-superpowers` SKILL.md into every session's context wrapped in an `<EXTREMELY_IMPORTANT>` block. Measured at ~1,140 tokens per session. The content is redundant — the skill is already listed in the `Skill` tool metadata.

## Investigation

Searched the Claude Code 2.1.101 binary (`/Users/mohammed.farook/.local/share/claude/versions/2.1.101`, 201 MB Mach-O arm64) for known settings keys that would support disabling a plugin-defined hook from user or project settings:

- `disabledHooks` — 0 hits
- `disableHooks` — 0 hits
- `disablePlugins` — 0 hits
- `pluginHookOverrides` — 0 hits
- `suppressHooks` — 0 hits

The plugin hook is defined in `hooks/hooks.json` inside the plugin cache and runs whenever the plugin is enabled. There is no user-space mechanism to disable the hook while keeping the plugin's skills available.

## Options considered

1. **Disable the `superpowers` plugin entirely in cairn** — rejected. Cairn needs the superpowers skills (brainstorming, TDD, systematic-debugging, executing-plans, subagent-driven-development) for the protocol work in Slice #2 and beyond. Losing all skills to save 1,100 tokens is a bad trade.

2. **Fork the plugin with a no-op SessionStart hook** — rejected for D1. Maintenance burden, and the fork needs to be re-synced on every upstream update. Not appropriate for a reversible floor-cut change.

3. **Replace `hooks/session-start` in the plugin cache with a no-op** — rejected. Direct edits to plugin cache files are reverted on plugin update and leave no breadcrumb when they break. Fragile.

4. **Upstream request** — pending. File an issue/PR on the superpowers repository asking for either (a) a "minimal SessionStart" mode that outputs only a one-line "superpowers skills available via Skill tool" reminder, or (b) a plugin-config opt-out. This is the correct long-term path.

5. **Accept the ~1,100 tokens as unfixable until upstream supports it** — chosen. Document the trade, measure without the cut, and revisit when upstream or Claude Code exposes a mechanism.

## Decision

D1.2 is deferred. The D1 ship-set (Tasks 1–4 in the implementation plan) proceeds without it. Expected D1 savings are revised downward from ~2,700–3,400 tokens to **~1,600–2,300 tokens** (CLAUDE.md trim + global plugin relocation, minus D1.2).

## Revisit criteria

Revisit this deferral when any of the following is true:

- Claude Code exposes a settings key that lets a user or project disable a specific plugin hook.
- The superpowers upstream repo exposes a plugin-config opt-out or a minimal-mode SessionStart.
- The measured cost of the injection rises materially (e.g., the `using-superpowers` SKILL.md grows past 2,000 tokens).
- Cairn ships its own protocol work that conflicts with the injection (unlikely, but possible).
```

**Step 5.2: Commit**

```bash
git add docs/plans/2026-04-11-d1-2-superpowers-hook-deferral.md
git commit -m "docs(plans): record D1.2 superpowers hook override deferral

Claude Code 2.1.101 exposes no per-project setting to suppress a
plugin-defined hook. Records the investigation, options considered,
and revisit criteria so D1.2 is not silently dropped from the
design doc."
```

---

## Task 6: Measure post-change context and verify savings

**Files:**
- Create: `docs/plans/measurements/2026-04-11-post-d1.txt`

**Why this task matters:** The whole D1 effort is defensible only if the measurement confirms the savings. If it misses by >30%, stop and re-investigate before proceeding to Slice #2.

**Step 6.1: Start a fresh cairn session**

The human runs this step manually. Open a new Claude Code session in the cairn directory (`/Users/mohammed.farook/Developer/lab/cairn`). Enter any trivial prompt (e.g., "hi") and let it respond once. Then exit or switch sessions.

**Step 6.2: Measure the new session's turn-1 context**

Run the same script from Task 1.1:

```bash
python3 <<'PY'
import json, os, glob
paths = sorted(
    glob.glob('/Users/mohammed.farook/.claude/projects/-Users-mohammed-farook-Developer-lab-cairn/*.jsonl'),
    key=os.path.getmtime, reverse=True
)[:3]
print('post-D1 turn-1 context (cairn, 3 most recent sessions):')
print('-' * 60)
for p in paths:
    with open(p) as f:
        for line in f:
            obj = json.loads(line)
            u = obj.get('message', {}).get('usage')
            if u:
                total = u.get('input_tokens',0) + u.get('cache_creation_input_tokens',0) + u.get('cache_read_input_tokens',0)
                name = os.path.basename(p)[:8]
                print(f'  {name}  total={total:>6}  (cc={u.get("cache_creation_input_tokens",0)} cr={u.get("cache_read_input_tokens",0)})')
                break
PY
```

The newest session is the one from Step 6.1.

**Step 6.3: Record the result**

Write the output to `docs/plans/measurements/2026-04-11-post-d1.txt`. Include a one-line diff against the baseline:

```
baseline avg: <N>
post-D1 avg:  <M>
delta:        <N - M> tokens (<percent>%)
```

**Step 6.4: Compare against target**

| Measurement | Target | Pass if |
|---|---|---|
| Turn-1 context post-D1 | ~27,500–28,500 | avg is within ±1,000 of target |
| Delta from baseline | 1,600–2,300 tokens | delta ≥ 1,500 |

**If the delta is < 1,500:** stop. Investigate which change didn't land as expected (most likely cause: `~/.claude/settings.json` edit was not saved correctly, or the CLAUDE.md trim did not reach disk).

**If the delta is ≥ 1,500:** proceed to Task 7.

**Step 6.5: Commit the measurement**

```bash
git add docs/plans/measurements/2026-04-11-post-d1.txt
git commit -m "docs(plans): capture D1 post-change measurement"
```

---

## Task 7: Write a short completion report

**Files:**
- Create: `docs/plans/2026-04-11-d1-completion.md`

**Why:** D1 ships as non-slice work. There is no `/handoff` at the end, no phase-bridge note, no `slice.yaml complete`. A short completion report is the only persistent record that D1 happened. It also captures the delta and any surprises for later review.

**Step 7.1: Write the completion report**

Create `docs/plans/2026-04-11-d1-completion.md`:

```markdown
# D1 — Startup Floor Cuts: Completion Report

**Date completed:** <YYYY-MM-DD>
**Plan:** `docs/plans/2026-04-11-d1-floor-cuts-plan.md`
**Design:** `docs/plans/2026-04-11-context-discipline-design.md`

## Shipped

- Task 1: baseline measurement captured (`docs/plans/measurements/2026-04-11-baseline.txt`)
- Task 2: cairn-internals content absorbed into `docs/operational-reference.md`
- Task 3: `CLAUDE.md` trimmed to ~400-token cheat sheet
- Task 4: global plugins relocated — `~/.claude/settings.json` emptied, `claude-md-management` added to cairn project scope
- Task 5: D1.2 superpowers hook override documented as deferred
- Task 6: post-D1 measurement captured (`docs/plans/measurements/2026-04-11-post-d1.txt`)

## Measurement

| | Turn-1 context |
|---|---|
| Baseline (avg of 5 sessions) | <fill in> |
| Post-D1 (avg of 3 sessions) | <fill in> |
| Delta | <fill in> tokens (<fill in>%) |

**Target:** 1,600–2,300 token reduction.
**Actual:** <fill in>
**Verdict:** <pass | investigate>

## Non-cairn changes recorded

- `~/.claude/settings.json`: `enabledPlugins` emptied. This file is outside cairn's git. Do not re-enable globally — move plugins to project scope if needed in other projects.

## Known follow-ups

- D1.2 (superpowers SessionStart hook) deferred. See `docs/plans/2026-04-11-d1-2-superpowers-hook-deferral.md` for revisit criteria.
- Other projects (`complex-rag-analysis`, etc.) lost the three global plugins. Each needs its own decision about which to re-enable at project scope. Not in D1's scope.

## Next step

Start Slice #2 (`handoff-catchup-protocol-rewrite`) via `/start-slice` in a fresh session. The D1 measurements establish the baseline for Slice #2's success criteria.
```

**Step 7.2: Fill in the measurement numbers**

Replace the `<fill in>` placeholders with the actual values from Task 6.

**Step 7.3: Commit**

```bash
git add docs/plans/2026-04-11-d1-completion.md
git commit -m "docs(plans): D1 completion report

Records the shipped changes, measured delta, and known follow-ups
for the D1 startup floor cuts. Closes the non-slice work phase and
hands off to Slice #2 (handoff-catchup-protocol-rewrite) via
/start-slice."
```

---

## DRY / YAGNI / TDD notes specific to this plan

- **DRY:** the cairn-internals content is moved, not copied. After Task 2 it exists only in `docs/operational-reference.md`, and after Task 3 it exists nowhere else.
- **YAGNI:** D1.2 stays deferred. Do not attempt the fork or cache-patch options just because "while we're here." Each is a separate change that needs its own risk assessment.
- **TDD-adapted:** this plan does not have runnable tests because cairn is a methodology repo with no test suite. The functional equivalent is Task 6's measurement comparison. Treat the measurement as the test and the target as the acceptance criteria — if the measurement misses, the plan has failed and needs to be reverted, not force-pushed through.
- **Frequent commits:** each task commits independently. A mid-plan failure leaves a clean rollback target. No squashing; each commit is its own reversible step.

## Rollback

If Task 6 shows the delta missed its target and the cause is not immediately obvious:

```bash
# revert in reverse order — most recent commit first
git log --oneline -8
# identify the D1 commits (Tasks 2, 3, 4, 5) by their messages
git revert <commit-sha>  # one at a time, in reverse order
```

`~/.claude/settings.json` rollback is manual — the user settings are outside git. Restore the three plugin entries if Task 4's effect needs to be undone.
