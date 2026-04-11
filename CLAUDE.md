# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Cairn is a **methodology repository**, not a runnable application or library. It contains the protocols, shell-script hooks, slash commands, and documentation that implement a four-phase slice pipeline (Intent → Validation → Implementation → Integration), a decision protocol for architectural work, and a substrate validator. It is consumed by *other* projects, which symlink it as `.slice-system/` and reference its scripts/docs from their own `.claude/` configuration. Cairn also consumes itself the same way — a `.slice-system → .` self-symlink lets the same pipeline run on cairn's own development (see ADR-001 for the bootstrap exception that put this in place).

Status: solo, pre-v1. See `docs/roadmap.md` for the work required to reach v1, and `CHANGELOG.md` for the delta since v0.1.0.

## Critical: always edit canonical paths, never via `.slice-system/`

The slash command files in `commands/claude-code/` reference paths like `.slice-system/scripts/validate_architecture.py` and `.slice-system/docs/operational-reference.md`. Those resolve two ways: in *consumer* projects, through a symlink to this repo; in cairn itself, through the self-symlink back to `.`. Both work. But when you make edits during a cairn slice, **always target canonical paths** (`checks/reality-check.sh`, `commands/claude-code/start-slice.md`, `scripts/validate_architecture.py`), **never the `.slice-system/` prefix**.

Why: `scope-guard.sh` line 53 strips `$PROJECT_ROOT` as a literal prefix to produce `REL_FILE`. If the tool-input file path comes in as `<root>/.slice-system/checks/foo.sh`, the stripped relative path is `.slice-system/checks/foo.sh` — which matches no allowlist entry (`.claude/current-slice/*`, `docs/adr/*`, etc.) and no envelope glob that any sane slice would declare. The edit gets denied during an active slice. This is latent today (no slice is active), but will bite the moment slice #1 runs. A proper scope-guard canonicalization fix is deferred to a later slice.

## Hook dependencies

All three hooks require `jq`; `reality-check.sh` additionally requires `ruff`. Each script no-ops with a stderr warning if its dependency is missing, so a fresh contributor without either silently loses enforcement — the scripts pass without running. Install both before doing any work in cairn:

```
brew install jq && uv tool install ruff
```

## Symlink recursion hazard

`.slice-system → .` is an infinite-depth loop for any tool that follows symlinks recursively. No current tool in this repo walks the root that way, so it's latent. If you add one — a `find`, a `glob("**/*")`, anything — exclude `.slice-system` explicitly.

## Repo layout

- `checks/` — POSIX shell hooks. PreToolUse / PostToolUse handlers that read JSON from stdin. Three hooks: `reversibility-guard.sh` (blocks destructive ops, enforces ADR append-only), `scope-guard.sh` (blocks edits outside the current slice envelope), `reality-check.sh` (runs `ruff format` + `ruff check --fix` on Python edits). All require `jq`; `reality-check.sh` additionally requires `ruff`. Each gracefully no-ops with a warning if its dependency is missing.
- `commands/claude-code/` — Markdown slash commands (`/start-slice`, `/decision`, `/catchup`, `/handoff`, `/integration-sweep`, `/new-adr`, `/refresh-architecture`, `/status`). These are the canonical agent-facing protocols. A `commands/windsurf/` mirror is roadmapped but does not exist yet.
- `docs/` — Three layers of documentation:
  - `operational-reference.md` (Layer 1) — quick reference, intended to be loaded at the start of any slice.
  - `spec-v1.md` (Layer 2) — canonical spec with full theory, failure modes, empirical support, and adversarial framing. **Deliberately not auto-loaded** — load on demand when working on a question the operational reference does not answer.
  - `vision.md`, `roadmap.md` — what v1 commits to and the ordered slice sequence to get there.
- `scripts/validate_architecture.py` — single-file validator. Checks consistency between `docs/ARCHITECTURE.md` invariants and the `docs/adr/` corpus (Check A: every invariant references valid non-superseded ADRs; Check B: every firm accepted ADR has at least one invariant; Check C: no invariant references a superseded ADR). Runs against the *consumer* project's docs, not this repo's.
- `templates/` — currently empty. Template extraction (`intent.md`, `slice.yaml`, ADR frontmatter) is a may-land-before-v1 item.

## Working on cairn itself

There is no build, no package manifest, and no test suite in this repo. Common operations:

- **Lint a hook script:** `shellcheck checks/<name>.sh` (if shellcheck is installed).
- **Smoke-test a hook locally:** the hooks read JSON from stdin. Example:
  ```
  echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | bash checks/reversibility-guard.sh
  ```
  Exit code 2 + JSON on stdout = blocked. Exit 0 = allowed.
- **Run the validator:** `python3 scripts/validate_architecture.py` (uses only stdlib). It will fail in this repo until the meta-dogfood `docs/ARCHITECTURE.md` and `docs/adr/` exist — that is expected, not a bug.

When doing non-trivial work on cairn, the intended flow is meta-dogfood: use cairn's own slice pipeline (via the slash commands) to develop cairn. Per CHANGELOG, this is not yet wired up — the first cairn slice is supposed to set it up. Until then, treat changes here like ordinary edits but stay aligned with the spec in `docs/spec-v1.md`.

## Editing rules that matter

- **ADRs are append-only.** This is enforced in consumer projects by `reversibility-guard.sh`. Even when editing the hook itself or related docs here, preserve that property in the design — the only legitimate way to change a decision is a new superseding ADR. The escape hatch for typo/formatting fixes is `ADR_EDITORIAL_FIX=1`.
- **Scope-guard goes dormant when slice status is `complete` or `failed`** and always allows writes under `.claude/current-slice/`, `.claude/handoff.md`, `.claude/sweep.yaml`, `docs/adr/`, `docs/ARCHITECTURE.md`, `docs/lessons.md`. Auto-includes test mirrors of envelope source files. The override is `EXPAND_ENVELOPE=1`, which logs to `.claude/current-slice/envelope-expansions.log`.
- **`reversibility-guard.sh` allow-list quirks:** `git push --force-with-lease` is allowed, `git push --force` / `-f` is blocked. ADR file *creation* via Write is allowed; overwriting an existing ADR via Write is blocked; Edit on an ADR is allowed only if `old_string`'s first line begins with `status:`, `superseded-by:`, `superseded_by:`, or `firmness:`. Preserve the "first-line only" check — a multiline `old_string` with a frontmatter keyword on a later line is intentionally treated as a body edit.
- **Six v1 commitments** (`docs/vision.md`) are the spec for cairn's own development: agent-portable, parallelism-native, soft agent-split, meta-dogfoodable from slice #1, plastic phase shape through v1, explicit cognitive roles per phase. Don't lock in designs that contradict these — especially not a global "one active slice" pointer (parallelism is a v1 commitment, not a future feature).

## Documentation tiers — load on demand

If a question is operational ("what does Phase 2 receive as input?", "what does scope-guard allow?"), `docs/operational-reference.md` is sufficient. If a question is about the *why* (failure modes, the dual context-engineering / role-reset thesis, empirical support, what the system does and does not claim), read `docs/spec-v1.md`. The spec is long and intentionally kept out of default context — pull it in deliberately when needed.
