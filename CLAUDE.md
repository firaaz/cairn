# CLAUDE.md

Cairn is a methodology repo — slice pipeline, hooks, slash commands — consumed by other projects via a `.slice-system → .` symlink. No build step. Tests live under `tests/unit/`; run with `uv run pytest` (always inside the project venv — never `python3 -m pytest`). Bootstrap: `uv sync` creates `.venv` and `uv.lock`. For repo layout, working commands, expanded editing rules, and documentation tier guidance, load `docs/operational-reference.md` on demand. For the canonical spec (theory, failure modes, empirical support), load `docs/spec-v1.md` on demand.

## Identifier scheme

Every ADR, slice, feature, and decision point carries both `id:` (immutable mechanical identifier) and `name:` (mutable human/LLM-facing label). Prose uses `name:`; cross-references, filenames, and hook inputs use `id:`. Full protocol: `docs/adr/identifier-scheme.md` and `docs/operational-reference.md`.

## Safety-critical rules

**Edit canonical paths only, never via `.slice-system/`.** Slice-system files are symlinked from consumers; editing through the symlink produces tool-input paths starting with `.slice-system/`, which `scope-guard.sh:53` strips as a literal prefix. The resulting relative path matches no allowlist entry and the edit gets denied during an active slice. Always target `checks/...`, `commands/claude-code/...`, `scripts/...` directly.

**Hook dependencies.** All three `checks/*.sh` hooks require `jq`; `reality-check.sh` also needs `ruff`. Missing deps cause the hook to no-op with a stderr warning — enforcement silently disabled. Install both before any work in cairn:
```
brew install jq && uv tool install ruff
```

**Symlink recursion hazard.** `.slice-system → .` is an infinite depth loop for any tool that follows symlinks recursively. If you add `find`, `glob("**/*")`, or similar, exclude `.slice-system` explicitly.

**ADRs are append-only.** `reversibility-guard.sh` allows `Write` on new ADRs and blocks overwriting existing ones. `Edit` is allowed only if `old_string`'s first line begins with `status:`, `superseded-by:`, `superseded_by:`, or `firmness:` (frontmatter-only edits). Typo escape hatch: `ADR_EDITORIAL_FIX=1`.

**Force-push policy.** `git push --force` / `-f` is blocked; `--force-with-lease` is allowed.
