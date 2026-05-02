---
slice: compression/upgrade-doc-bug-fixes
date: 2026-05-02
phase: 1-intent
invariants-touched: []
adrs-referenced: []
envelope:
  - "docs/upgrading-from-pre-compression.md"
  - "tests/unit/test_upgrade_doc_consumer_setup.py"
out-of-scope:
  - "Restructuring docs/upgrading-from-pre-compression.md beyond the two named deltas plus their two Verify snippets"
  - "Edits to any source under checks/, scripts/, mcp_servers/, .claude/agents/, or .claude/commands/"
  - "Versioning the upgrade doc (raised in design doc §7 risk; deferred)"
  - "The §2 'Open question — module resolution' framing (still accurate as written; PYTHONPATH escape hatch remains)"
  - "Any of Deltas 3/4/5's existing Verify snippets (already runtime-invoke or grep-based; only Deltas 1/2 are wrong)"
  - "Forward-port of compression/triager-superseded-test-heuristic (Slice 1 of this branch — separate)"
  - "Substrate consumer-corpus parameterization (Slice 3 of this branch — separate)"
---

### What and Why

Fix two consumer-breaking bugs in `docs/upgrading-from-pre-compression.md` that were discovered 2026-04-27 while migrating `complex-rag-analysis` onto post-compression cairn. Both bugs survived the original verify pass because the documented Verify snippets only check structural presence (`jq -e ...`) without runtime-invoking the wired path. Strengthening Deltas 1 and 2 to runtime-invoke closes the class of failure, not just the two instances.

### Specification Detail

Two doc edits + two Verify-snippet rewrites in `docs/upgrading-from-pre-compression.md`. No code edits in cairn itself.

**Delta 1 — `role-cheatsheet.sh` path correction.** The doc names this hook in two places:
- §1 prose (current line 30): `scripts/role-cheatsheet.sh (or the consumer's equivalent role-context banner)` → must read `checks/role-cheatsheet.sh ...`.
- §1 paragraph beneath the bullet list (current line 35-36): `.slice-system/scripts/role-cheatsheet.sh` → must read `.slice-system/checks/role-cheatsheet.sh`.

Authoritative location is `checks/role-cheatsheet.sh` (verified 2026-05-02 by `find . -name role-cheatsheet*`; `scripts/role-cheatsheet.sh` does not exist).

**Delta 2 — MCP server command correction.** The doc's §2 JSON example currently shows:

```json
{
  "mcpServers": {
    "cairn-knowledge": {
      "command": "python",
      "args": ["-m", "mcp_servers.cairn_knowledge"]
    }
  }
}
```

Bare `python` is not on PATH inside Claude Code's MCP subprocess environment, so the server silently fails to start. The corrected entry must invoke the server through `uv` so dependency resolution and Python interpreter selection both succeed:

```json
{
  "mcpServers": {
    "cairn-knowledge": {
      "command": "uv",
      "args": ["run", "--directory", ".slice-system", "python", "-m", "mcp_servers.cairn_knowledge"]
    }
  }
}
```

The `--directory .slice-system` argument is what makes `mcp_servers/` discoverable on `sys.path` in a self-symlinked consumer (since `.slice-system → .` resolves to the cairn root containing the package). The §2 "Open question — module resolution" PYTHONPATH escape hatch remains accurate for non-symlink layouts and is unchanged by this slice.

**Delta 1 Verify-snippet rewrite.** Current snippet (`jq -e '.hooks.PreToolUse[]?.hooks[]?.command | select(test("role_guard"))' .claude/settings.json`) only proves the file mentions `role_guard`. It must be replaced with a runtime invocation that proves the hook is wired correctly *and* the script exists at the documented path:

```sh
bash .slice-system/checks/role-cheatsheet.sh </dev/null | head -1
```

Expected outcome: prints a single JSON-shaped line (the role-cheatsheet's stdout envelope) and exits 0. In a consumer with `.slice-system → cairn-root`, this resolves to executing the file at the corrected path.

**Delta 2 Verify-snippet rewrite.** Current snippet (`jq -e '.mcpServers["cairn-knowledge"] | ...' .mcp.json`) only proves the JSON config mentions the right module name. It must be replaced with a runtime invocation that proves the documented command actually launches the package:

```sh
uv run --directory .slice-system python -c "import mcp_servers.cairn_knowledge"
```

Expected outcome: exit code 0 with no stderr. Confirms that (a) `uv` is on PATH, (b) `--directory .slice-system` resolves the cairn checkout, and (c) the package imports cleanly under the substrate venv.

**No-changes invariant for Deltas 3, 4, 5.** Their existing Verify snippets are already runtime-invoke or grep-based and remain correct. This slice does not touch them.

### Boundary

Out of scope items in the YAML envelope above. The slice is a doc fix plus one new test file; no production code path changes.

### Verification

Phase 2 validation lives in `tests/unit/test_upgrade_doc_consumer_setup.py` and asserts the following — every assertion must be a literal check against the on-disk doc or a subprocess invocation, never reasoning from memory:

1. **Delta 1 prose corrected.** `grep -nE "scripts/role-cheatsheet\.sh" docs/upgrading-from-pre-compression.md` returns zero matches.
2. **Delta 1 corrected path present.** `grep -n "checks/role-cheatsheet\.sh" docs/upgrading-from-pre-compression.md` returns at least 2 matching lines (one in §1 prose, one in the §1 paragraph beneath the bullets).
3. **Delta 2 prose corrected — bare-python eliminated.** Read the §2 JSON code-fence and assert it does not contain a `"command": "python"` key whose sibling `args` includes `"-m", "mcp_servers.cairn_knowledge"`.
4. **Delta 2 corrected command present.** Read the §2 JSON code-fence and assert `"command": "uv"` with args `["run", "--directory", ".slice-system", "python", "-m", "mcp_servers.cairn_knowledge"]` (exact args list, in order).
5. **Delta 1 Verify snippet runtime-invokes.** Extract the bash command between the `**Verify:**` heading of §1 and the next `---` rule. Run it via `subprocess.run(..., shell=True, capture_output=True, cwd=repo_root)`. Assert returncode == 0 and stdout's first line parses as JSON.
6. **Delta 2 Verify snippet runtime-invokes.** Extract the bash command between the `**Verify:**` heading of §2 and the next `---` rule. Run it via `subprocess.run(..., shell=True, capture_output=True, cwd=repo_root)`. Assert returncode == 0.
7. **Delta 3/4/5 verify snippets unchanged.** Compute a SHA-256 of the bytes between `## 3. Python dependencies` and the end-of-file, and assert it equals a pinned value captured at slice open. Any future edit to those sections fails this test, forcing the change to be intentional.

Phase 4 sweep produces `sweep-notes.md` covering: full `uv run pytest` GREEN (modulo pre-existing INV-004 OOS), `uv run python .slice-system/scripts/validate_architecture.py` PASS, empty `invariants-touched` table (this slice touches no architectural invariants — it is doc-only with a doc-coupled test).
