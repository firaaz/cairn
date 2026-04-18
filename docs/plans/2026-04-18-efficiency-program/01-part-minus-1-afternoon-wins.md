# Part -1: Afternoon Wins

**Date:** 2026-04-18
**Effort:** ~4–5 hours total
**Gating:** None
**Ports to:** Parts 0, 1, 2, 5

## Intent

Ship fast relief before the structural program. Every item is additive, reversible, ports directly into later parts. Zero ADR-level decisions.

## Items

### 1. Role cheatsheet at session-start (~30 min)

**Problem:** Cognitive load — phase role + primary anti-behavior live in `docs/operational-reference.md § Phase Skill Guide` and have to be consciously recalled. `catchup.full.md:120` surfaces this at Tier 2 only, not at session open.

**Change:** Session-start hook reads `.claude/current-slice/slice.yaml.status`, looks up the phase row in the Phase Skill Guide, prints one line:
```
You are in Phase 3 of <slice-name>. Role: Implementer. Anti-behavior: do not modify tests.
```
If no active slice, prints a generic prompt. If slice.yaml is absent or malformed, no-op (never a blocker).

**Success criterion:** Every session opens with unambiguous role context. `/catchup phase N` still works but is rarely needed for the role-surface alone.

**Ports to:** Part 2 (session-start tip upgrade with state.json SHA).

---

### 2. Fix measurements-drift hook (~30 min)

**Problem:** Pain point #8 — session-start hook rewrites `docs/plans/measurements/2026-04-12-slice-003.txt` on every session, showing `M` in `git status` across all worktrees chronically. Per-worker "ignore" is workable; aggregate pollution is not.

**Change:** Make the hook idempotent. Read file; compute new content; only write if content differs. Alternative: move the file out of the slice envelope and into a scratch path if the rewrite is diagnostic-only.

**Success criterion:** `git status` is clean after a session-start on an untouched worktree.

**Ports to:** N/A — pure hygiene.

---

### 3. Read-before-Write preload on pipeline files (~15 min)

**Problem:** CC 2.1.110 requires Read before Write on any file. Every worker hit this 1–2 times per slice on `slice.yaml` / `sweep.yaml` / `handoff.md`. ~2–4 error-retry tool calls per slice.

**Change:** Add a one-line instruction at the top of the phase-commit sections in `handoff.full.md` and `start-slice.full.md`:
> **Before writing `slice.yaml` / `sweep.yaml` / `handoff.md`, Read the file first (CC 2.1.110+ requires it).**

Prose-only change; no code. Addresses the footgun at the point where it's triggered.

**Success criterion:** Zero Read-before-Write retries observed in the next dogfood run.

**Ports to:** Part 2 (code-not-prose side effects — this becomes a precondition the skill runs automatically).

---

### 4. `/handoff` post-check verifier (~1 hr)

**Problem:** L-005 — `/handoff` reproducibly skipped `slice.yaml.status` flip + `handoff-phase-N.md` archive on worker A at P2/P3/P4. Failure discovered days later during integration. Prose-described side-effects don't always fire.

**Change:** Small shell script `scripts/verify_handoff.sh` runs at the end of `/handoff`:
1. Read `slice.yaml.status`; compare to expected next-phase status.
2. `test -f .claude/current-slice/handoff-phase-N.md` for the completed phase.
3. `git log -1 --format=%s` — verify last commit subject starts with `handoff:`.

If any check fails, exit non-zero with specific error text. `/handoff` skill invokes the verifier as its last step. Failure is loud and local.

**Success criterion:** Any future `/handoff` divergence is caught within the session that produced it, not at sweep time.

**Ports to:** Part 2 (code-side-effects promotes this from verifier to the authoritative executor).

---

### 5. Tier-1 read-only allowlist in `.claude/settings.json` (~30 min)

**Problem:** Pain point #10 — dozens of `1 Enter` clicks per slice on routine reads (`cat`, `sed -n`, `awk`, `grep`, `rg`, `pytest`, `git diff/show/log`). Every worker pays this cost. `.claude/settings.local.json` has individual-user wildcards but they're personal and often too permissive.

**Change:** Add a curated `permissions.allow` list to `.claude/settings.json` (team-shared, checked in) with ~20 regex patterns covering Tier-1 read-only ops. Deliberately narrow; no `python3 *` or `uv run *`. Shape mirrors what Feature 6's `permission-policy.yaml` will carry, so porting is 1:1.

Example patterns:
```json
{
  "permissions": {
    "allow": [
      "Bash(sed -n *)",
      "Bash(awk *)",
      "Bash(grep *)",
      "Bash(git diff *)",
      "Bash(git show *)",
      "Bash(git log *)",
      "Bash(uv run pytest *)",
      "Bash(uv run ruff *)"
    ]
  }
}
```

**Success criterion:** Routine-read prompts drop to near-zero across all workers. Observable in the next dogfood.

**Ports to:** Part 2 (refined + unified with F6 when Layer 1 `permission-policy.yaml` ships).

---

### 6. Per-phase commit-message template (~30 min)

**Problem:** Pain point #11 — phase-commit message formats vary. C used `status: 2-validation` (numbered); A/B/D used bare names. Sweep parsers become fragile.

**Change:** Four templates `.gitmessage-phase-1` through `.gitmessage-phase-4`. A `prepare-commit-msg` hook reads `slice.yaml.status`, selects the right template, pre-populates the commit message body. Author can still edit.

Template shape (Phase 1 example):
```
phase-1: <slice-name> — intent

Envelope: <paste from intent.md>
ADRs touched: <from intent.md>
Next: /handoff → phase 2
```

**Success criterion:** Sweep parsers become deterministic. Status-label divergence impossible by construction for new slices.

**Ports to:** Part 5 S1 (continuous telemetry consumes these templates as its parse shape).

---

### 7. `/status` expansion to one-stop dashboard (~1 hr)

**Problem:** `/status` today is 18 lines of skill. Usually answers "where am I" partially. Users re-orient by re-reading slice.yaml + handoff.md + recent commits manually — 2–5 min per resume.

**Change:** Extend `/status` to print:
- Phase + commit SHA (`slice.yaml.status` + `git rev-parse HEAD`)
- Last test run status (if any — read from `.claude/current-slice/validation/` artifact or git log)
- Pending gates (if any — scan for known markers)
- Active feature index (`.claude/features/*.yaml` names + status)
- "Next:" line from handoff.md if present

One command answers "where am I?" completely.

**Success criterion:** Resume time (measured from session open to first intentional action) drops from 2–5 min to <30 s.

**Ports to:** Part 1 (feature-graph-explainer subagent) — `/status` can delegate to it once agents exist.

## Order of execution

Any order; all independent. Suggested:
1. #5 (allowlist) — biggest daily impact, shortest to ship.
2. #2 (measurements) — removes a chronic annoyance.
3. #1 (cheatsheet) — cognitive load relief.
4. #3 (Read preload) — prose-only, trivial.
5. #4 (verifier) — catches L-005 class going forward.
6. #6 (commit templates) — enables future parse reliability.
7. #7 (`/status`) — one sitting, noticeable payoff.

## Scope boundary

This part does NOT:
- Rewrite any skill. Only appends preconditions / verifiers / prose clarifications.
- Introduce new agents. Agents are Parts 1/3/4.
- Change `.claude/settings.local.json` behavior. Only adds to the shared `settings.json`.
- Touch ADRs. All changes live in hooks, scripts, and skill prose.

Anything that requires an ADR decision goes into Part 0 or later.
