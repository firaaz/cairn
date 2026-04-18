---
slice: efficiency-program-afternoon-wins/all-seven
name: "Part -1 Afternoon Wins — 7-item bundle shipment"
date: 2026-04-18
phase: 1-intent
invariants-touched: [INV-002, INV-003, INV-004]
adrs-referenced: []
envelope:
  - "checks/*.sh"
  - "scripts/verify_handoff.sh"
  - "commands/claude-code/handoff.md"
  - "commands/claude-code/handoff.full.md"
  - "commands/claude-code/start-slice.full.md"
  - "commands/claude-code/status.md"
  - "commands/claude-code/status.full.md"
  - ".claude/settings.json"
  - ".gitmessage-phase-*"
  - "tests/unit/efficiency_program/*.py"
out-of-scope:
  - "Skill rewrites beyond the specific preconditions/verifier/allowlist additions named below"
  - "New ADRs (Part -1 is explicitly zero-ADR by program design)"
  - "Phase-role agent authoring (Part 3 scope)"
  - "Distillation or verification subagents (Part 1 scope)"
  - ".claude/settings.local.json (user-personal; untouched)"
  - "Non-cairn-shipped skills (Superpowers, third-party)"
---

### What and Why

Ship seven low-risk, ungated improvements from efficiency-program Part -1 as a single slice with seven parallel Phase-3 implementers. Together the seven items reduce per-slice ceremony friction — permission-prompt density, measurements-drift chronic `M`, Read-before-Write retries, commit-message parse divergence, cognitive role-load at session open, `/handoff` side-effect divergence (L-005 class), multi-step resume cost — without introducing ADR-level decisions. Every item is additive, reversible, and ports directly into later program parts (0, 1, 2, 5). Zero scope creep: no skill rewrites, no new agents, no `.claude/settings.local.json` changes.

### Specification Detail

All seven items, each with protocol-level commitments. Phase 3 dispatches seven parallel Builder subagents, one per item; each item's files partition cleanly from the others.

**Item 1 — Session-start role cheatsheet (SessionStart hook).**
A SessionStart hook reads `.claude/current-slice/slice.yaml`'s `status:` field, looks up the matching row in `docs/operational-reference.md § Phase Skill Guide`, and prints one line to the session:
```
Slice: <slice-name>. Phase: <N> <phase-name>. Role: <role>. Anti-behavior: <primary anti-behavior>.
```
If no active slice OR `status:` is `complete`/`failed`, print a generic "No active slice — /start-slice to open one" hint. If `slice.yaml` is missing, malformed, or the Phase Skill Guide cannot be parsed, hook exits 0 silently — never a session blocker. Hook registration is via `.claude/settings.json` `hooks.SessionStart` array.

**Item 2 — Measurements-drift hook idempotency.**
The session-start hook that currently rewrites `docs/plans/measurements/2026-04-12-slice-003.txt` on every session (producing chronic `M` in `git status` across all worktrees) MUST become idempotent. Two acceptable forms:
- **Form A (preferred):** read current contents, compute new contents, only `mv`/write if they differ.
- **Form B:** relocate the diagnostic artifact out of the tracked path (e.g., to `.claude/measurements/2026-04-12-slice-003.txt`, added to `.gitignore`).
Selection is a Phase 3 judgement call; either satisfies the exit criterion. Chronic `M` on an untouched worktree is the failure shape to eliminate.

**Item 3 — Read-before-Write preload prose.**
`commands/claude-code/handoff.full.md` and `commands/claude-code/start-slice.full.md` each gain a one-line preamble at the top of their phase-commit instruction sections. Exact string (verbatim, so a grep-based test can verify):
```
**Before writing `slice.yaml` / `sweep.yaml` / `handoff.md`, Read the file first (CC 2.1.110+ requires Read before Write).**
```
Prose-only change; no code; no new hook. Addresses the footgun at the point of trigger.

**Item 4 — `/handoff` post-check verifier.**
New file `scripts/verify_handoff.sh` (POSIX shell, `set -euo pipefail`, runnable as `bash scripts/verify_handoff.sh` with exit code conveying pass/fail). It performs three checks:
1. If in a pipeline phase: `slice.yaml.status` matches the expected next-phase state implied by the most recent commit subject.
2. If in a phase-commit: `.claude/current-slice/handoff-phase-<N>.md` exists for the completed phase.
3. `git log -1 --format=%s` subject starts with `handoff:` OR `phase-<N>:` OR `slice: .* — complete`.
Exit 0 = pass; non-zero = fail with `stderr` text naming the failing check (which expectation was violated, and the remediation command).
`commands/claude-code/handoff.md` (lite) gains one line instructing the skill to invoke the verifier as its final step; `commands/claude-code/handoff.full.md` gains a matching section documenting the verifier's contract (exit codes + error shape).

**Item 5 — Tier-1 read-only allowlist in `.claude/settings.json`.**
Add a `permissions.allow` list to `.claude/settings.json` (team-shared, checked-in) carrying narrow regex patterns for Tier-1 read-only operations. Deliberately specific — no unrestricted `python3 *` or `uv run *` wildcards. Minimum required patterns:
- `Bash(sed -n *)`
- `Bash(awk *)`
- `Bash(git diff *)`
- `Bash(git show *)`
- `Bash(git log *)`
- `Bash(git status *)`
- `Bash(uv run pytest *)`
- `Bash(uv run ruff *)`
- `Bash(shellcheck *)`
- `Bash(jq *)`
Phase 3 may add additional narrow patterns but MUST NOT add broad-wildcard entries. Shape mirrors what Feature 6's `permission-policy.yaml` will carry, so porting is 1:1 when F6 ships.

**Item 6 — Per-phase commit-message templates + `prepare-commit-msg` hook.**
Four template files at repo root: `.gitmessage-phase-1`, `.gitmessage-phase-2`, `.gitmessage-phase-3`, `.gitmessage-phase-4`. Each follows this shape:
```
phase-<N>: <slice-id> — <phase-output-label>

<phase-specific preamble: envelope summary / ambiguities enumerated / decisions recorded / evidence cited>
Next: /handoff → phase <N+1>    (or: /start-slice complete)
```
Plus a `prepare-commit-msg` shell hook at `checks/prepare-commit-msg.sh`. Installation uses `core.hooksPath` pointing at `checks/`, or a shim in `.git/hooks/`. The hook reads `.claude/current-slice/slice.yaml`'s `status:` field, maps it to the corresponding template, and pre-populates the commit message buffer (first argument). If `slice.yaml` is missing, or `status:` is non-pipeline (`complete`, `failed`, or a non-phase value), the hook no-ops silently. Author retains full edit freedom after pre-population.

**Item 7 — `/status` expansion.**
`commands/claude-code/status.md` is extended from its current short form to a one-stop dashboard. Output lines (in order):
1. `Slice: <id> · Phase: <N> <phase-name> · HEAD: <short-sha>` — from `slice.yaml.status` + `git rev-parse --short HEAD`.
2. `Last test run: <timestamp> <pass|fail|—>` — from most-recent `.claude/current-slice/validation/` or `integration/` artifact mtime + pass/fail marker if discoverable; `—` if absent.
3. `Sweep: <due|up-to-date> (<N> slice-complete since last)` — read `.claude/sweep.yaml`, count `^slice: .* — complete$` commits since `last-sweep-at-slice-id:`.
4. `Features: <comma-list of id:name pairs>` — `ls .claude/features/*.yaml` → frontmatter `id:`/`name:`.
5. `Next: <line>` — from `.claude/handoff.md`'s `## Next` section first line if present.
Output fits within INV-004 context budget (target: ≤1500 characters for the dashboard output). Expanded registry/debug output lives in `commands/claude-code/status.full.md` (created if it does not exist) and is loaded only on the discrete predicate "user asks for the full registry view" — preserving progressive-disclosure INV-004.

### Boundary (out of scope)

- Rewriting any existing skill beyond the preconditions, verifier-invocation line, and allowlist additions explicitly enumerated above.
- Authoring new ADRs or amending existing ones. Part -1 is zero-ADR by program design.
- Authoring phase-role agents (Part 3 scope).
- Authoring distillation / verification subagents (Part 1 scope).
- Changes to `.claude/settings.local.json` — user-personal file, untouched.
- Edits to non-cairn-shipped skills (Superpowers plugin, third-party).
- Any work that would trigger a `/decision` run — if such a need surfaces mid-implementation, the slice fails and the item is deferred to Part 0 or its native program-part.

### Verification

Per-item acceptance assertions. Each becomes one or more Phase 2 tests in `tests/unit/efficiency_program/`.

**Item 1 (role cheatsheet).** A test that: (a) constructs a fixture `slice.yaml` with `status: 3-implementation`, (b) invokes the SessionStart hook with that fixture via subprocess, (c) asserts stdout contains `Phase: 3` AND `Role: Builder` AND an anti-behavior substring matching the Phase Skill Guide table. Also: a test with missing `slice.yaml` asserts the hook exits 0 silently.

**Item 2 (measurements idempotency).** A test that runs the session-start hook twice in succession on a clean worktree with no intervening file edits, then asserts `git status --porcelain` on the measurements artifact path is empty. Alternative form (if Form B selected): assert the old tracked path is gone and the new untracked path exists outside `git ls-files`.

**Item 3 (Read-before-Write prose).** `grep -c "Read the file first (CC 2.1.110+ requires Read before Write)" commands/claude-code/handoff.full.md` returns `≥1`; same grep on `commands/claude-code/start-slice.full.md` returns `≥1`.

**Item 4 (handoff verifier).** `test -x scripts/verify_handoff.sh` passes. Running the verifier on a fixture pass-state returns exit 0 with empty stderr. Running on a fixture fail-state (missing `handoff-phase-N.md` where the commit claims phase-N) returns exit non-zero with stderr text naming the missing file.

**Item 5 (allowlist).** `jq '.permissions.allow | length' .claude/settings.json` returns `≥10`. `jq -r '.permissions.allow[]' .claude/settings.json` output contains all ten explicitly-required patterns from the spec above. A regex test on each entry asserts no pattern matches `^Bash\((python3|uv run)\s\*\)$` (no unrestricted language/tool wildcards).

**Item 6 (commit templates).** The four `.gitmessage-phase-<N>` files exist at repo root. Each contains a `phase-<N>:` subject-line template AND a `Next:` trailer. A simulated `prepare-commit-msg` invocation with a fixture `slice.yaml.status: 2-validation` produces a commit-message buffer whose first non-empty line begins with `phase-2:`. A simulated invocation with `status: complete` leaves the buffer unchanged (no-op).

**Item 7 (/status).** A test that constructs a fixture pipeline state (slice.yaml, handoff.md, sweep.yaml, features/*.yaml, a recent validation artifact) and invokes the `/status` implementation; asserts output contains all five dashboard lines. Output character count stays under 1500 so INV-004's progressive-disclosure contract holds.

**Cross-item (Phase 4 only).** Invariant evidence table shows PASS for INV-002 (handoff verifier + role cheatsheet preserve three-layer discipline), INV-003 (role cheatsheet surfaces Phase Skill Guide at session open), INV-004 (/status output under ceiling; no new always-loaded prose exceeds the budget) — each with file:line citations.
