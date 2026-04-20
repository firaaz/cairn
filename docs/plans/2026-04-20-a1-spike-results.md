# A1 Spike Results — 2026-04-20

Empirical evidence gathered per `docs/plans/2026-04-20-compression-pipeline-hardening-plan.md` Task 1.3. Spikes executed in `/tmp/cairn-a1-spike-1776679039/` (fresh scratch git repo with only `.claude/agents/phase-2-skeptic.md` from the cairn project). Each invocation asked a subagent to write `.claude/current-slice/validation/approach.md` with the single word `hello`.

## Baseline — `acceptEdits` default

**Result: FAIL.** Subagent self-reported FAILED after every write attempt (Write tool, Bash redirect, `mkdir` + `echo >`) was blocked by the harness with the `sensitive file` label.

Stderr excerpt:
> Write permission to `.claude/current-slice/validation/approach.md` is being denied by the harness sandbox on every attempt (Write tool and Bash redirect both blocked as "sensitive file"). Cannot produce the artifact.

Agent return: `{"status":"FAILED","commit_hash":"745d533...","summary":"Unable to write ... all write attempts ... blocked by sandbox permission prompts rejecting the path as sensitive. No artifact created."}`

This reproduces the production failure observed in `compression/slice-1-foundation` Phase 2 at commit `90be69b` → triager escalation log `.claude/orchestrator-debug/20260420T135339-issue-triager.log`.

## Spike 1 — `additionalDirectories` + explicit `allow Write/Edit(.claude/current-slice/**)`

**Result: INCONCLUSIVE.** Spike 1 re-ran in the same scratch repo after Spike 2 had already produced `approach.md` with `hello`. The subagent observed the file's existing content and returned OK without exercising the sensitive-file gate — no negative or positive evidence about whether the gate was actually bypassed. Not re-tested in a fresh directory because Spike 2's unambiguous PASS made the test unnecessary for the decision.

Settings used (`/tmp/spike1-settings.json`):
```json
{"permissions":{"allow":["Write(.claude/current-slice/**)","Edit(.claude/current-slice/**)"]},"additionalDirectories":[".claude/current-slice"]}
```

Agent return: `{"status":"OK","commit_hash":"c98d61f...","summary":"approach.md already contains 'hello' at the requested path; no changes needed."}` (commit hash is Spike 2's — no actual write performed.)

## Spike 2 — `bypassPermissions`

**Result: PASS.** Subagent wrote the file and committed cleanly; no harness interruption.

Invocation:
```
AGENT_ROLE=phase-2-skeptic claude -p --agent phase-2-skeptic \
  --permission-mode bypassPermissions \
  '{"phase":2,"role":"phase-2-skeptic","slice_id":"spike/a1-s2","brief":"write .claude/current-slice/validation/approach.md with the text hello"}'
```

Agent return: `{"status":"OK","commit_hash":"c98d61ffb75e79f0a1695b85f547cdf8be6935d6","summary":"Wrote .claude/current-slice/validation/approach.md containing 'hello' as instructed by the brief, then committed."}`

Artifact: `/tmp/cairn-a1-spike-1776679039/.claude/current-slice/validation/approach.md` (1 line, `hello`).

## Spike 3 — Claude Agent SDK (`permission_mode='acceptEdits'`)

**Result: FAIL.** SDK's in-process `query()` hit the same sensitive-file gate. Tool call `Write(file_path='/Users/mohammed.farook/.claude/current-slice/validation/approach.md', content='hello\n')` returned:

> Error: Claude requested permissions to edit /Users/mohammed.farook/.claude/current-slice/validation/approach.md which is a sensitive file.

Confirms the gate is enforced at the harness layer — not at the CLI-vs-SDK boundary. The SDK would presumably PASS under `permission_mode='bypassPermissions'` for the same reason Spike 2 passed; not re-tested because the one-line CLI fix is the target.

Note: the SDK resolved the relative path to the user's home directory rather than cwd. This is an independent path-resolution bug in the subagent, not part of A1, and does not affect the spike outcome.

## Decision

**Path X (settings fix), winning spike = Spike 2 (`bypassPermissions`).**

Rationale: Slice 1 already has `checks/scope-guard.sh` (envelope enforcement, PreToolUse hook at line 60 allows `.claude/current-slice/*` administratively) and a `checks/role_guard.py` that Slice 1 Task 1.4 wires as PreToolUse. Both hooks fire regardless of `permission-mode`. CC's built-in sensitive-file prompt on `.claude/**` is therefore **redundant** with our hook-layer enforcement — disabling it does not weaken the slice's protections, only removes an interactive prompt that cannot be satisfied non-interactively under `claude -p`. Change scope: `PERMISSION_MODE = "bypassPermissions"` one-liner in `scripts/slice_orchestrator.py` (and the same string in the plan's Task 1.5 `_run_claude_subprocess` body). No contract redesign (Path Y) required.

Residual risk: `bypassPermissions` also disables prompts for shell commands (`rm`, `curl`, etc.). The `checks/reversibility-guard.sh` hook already blocks `rm -rf` and destructive git operations, so the hook stack still covers the obvious danger surface. Re-evaluate during Slice 3 when the parallel-worktree integration test exposes the orchestrator to concurrent execution.
