# CLAUDE.md

> Audience tags: `[both]` = consumers + maintainers; `[maintainer]` = cairn-internal. Untagged sections default to `[maintainer]`.

Cairn is a methodology repo — TDD-by-construction dispatch skill, hooks, slash commands, validator — consumed by other projects via a `.slice-system → .` symlink. No build step. Tests live under `tests/unit/`; run with `uv run pytest` (always inside the project venv — never `python3 -m pytest`). Bootstrap: `uv sync` creates `.venv` and `uv.lock`. For repo layout, working commands, expanded editing rules, and documentation tier guidance, load `docs/operational-reference.md` on demand. For the canonical spec (theory, failure modes, empirical support), load `docs/spec-v1.md` on demand.

## Identifier scheme [both]

Every ADR, slice, feature, and decision point carries both `id:` (immutable mechanical identifier) and `name:` (mutable human/LLM-facing label). Prose uses `name:`; cross-references, filenames, and hook inputs use `id:`. Full protocol: `docs/adr/identifier-scheme.md` and `docs/operational-reference.md`.

## Safety-critical rules

**Edit canonical paths only, never via `.slice-system/`.** [maintainer] Slice-system files are symlinked from consumers; editing through the symlink produces tool-input paths starting with `.slice-system/`. `reversibility-guard.sh:48,76` strips that prefix before its allow/deny check, but `role_guard.py` does NOT — the operator-envelope and per-role allowlists are anchored at the canonical repo root, so a `.slice-system/...` path matches no pattern and the edit gets denied. Always target `checks/...`, `commands/claude-code/...`, `scripts/...` directly.

**Hook dependencies.** [both] All three `checks/*.sh` hooks require `jq`; `reality-check.sh` also needs `ruff`. Missing deps cause the hook to no-op with a stderr warning — enforcement silently disabled. Install both before any work in cairn:
```
brew install jq && uv tool install ruff
```

**Symlink recursion hazard.** [maintainer] `.slice-system → .` is an infinite depth loop for any tool that follows symlinks recursively. If you add `find`, `glob("**/*")`, or similar, exclude `.slice-system` explicitly.

**ADRs are append-only.** [both] `reversibility-guard.sh` allows `Write` on new ADRs and blocks overwriting existing ones. `Edit` is allowed only if `old_string`'s first line begins with `status:`, `superseded-by:`, `superseded_by:`, or `firmness:` (frontmatter-only edits). Typo escape hatch: `ADR_EDITORIAL_FIX=1`.

**Force-push policy.** [both] `git push --force` / `-f` is blocked; `--force-with-lease` is allowed.

**Operator envelope** [both] (`.claude/active-envelope.yaml`). `checks/role_guard.py` enforces write paths against this file when `AGENT_ROLE` is unset — i.e., in a regular Claude Code session, not a dispatch-skill phase run. `mode: operator` + `paths:` (list of regexes) restricts writes to matching paths; `mode: off` disables enforcement. The file is worktree-scoped: each worktree has its own copy. Fail-closed: malformed YAML or an unrecognised mode denies the write. Set `mode: operator` when starting focused feature work; set `mode: off` (or delete the file) when returning to ad-hoc cross-cutting edits. The file must include a pattern matching itself (`.claude/active-envelope.yaml`) or you cannot edit it while enforcement is active.

## New-code guidance

**New code is Python, function-based, with the post-M4 standing dep set as the only allowed dependencies** (pydantic, typer, pyyaml — see superseding ADR `cairn-substrate-and-fastmcp-superseded`; kuzudb/mistune/fastmcp dropped with the substrate retirement). Surviving bash hooks (`reversibility-guard.sh`, `reality-check.sh`) stay until their own migration slices. No decorators or metaprogramming.

**No hardcoded timeouts/sizes in consumer-facing scripts.** Cairn is consumed downstream (e.g. complex-rag-analysis, ~917s pytest); use env-var override with cairn-friendly default (`int(os.environ.get("CAIRN_<KNOB>", <default>))`) and document the var in `docs/operational-reference.md`.

**Within-slice parallel subagents are allowed.** `parallelism-v1` D4 v2+ time-box applies only to concurrent-worktree/split-agent slices, not in-session subagent dispatch.
