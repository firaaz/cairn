---
slice: compression/upgrade-doc-bug-fixes
phase: 2-validation
date: 2026-05-02
---

# Phase 2 Approach — Validation Suite

## Strategy

Single test module `tests/unit/test_upgrade_doc_consumer_setup.py` with 7
test functions, one per intent.md §Verification item. Tests are pure
disk reads + regex/JSON parsing, with two `subprocess.run(shell=True,
cwd=CAIRN_ROOT)` invocations for the runtime-invoke checks (Tests 5–6).
No fixtures, no conftest — `CAIRN_ROOT = Path(__file__).resolve().parents[2]`
follows the same pattern as `tests/unit/test_consumer_migration_doc.py`.

## Doc parsing helpers

Three small helpers handle the doc's structure without coupling to line
numbers:

- `_doc_text()` — reads `docs/upgrading-from-pre-compression.md` as
  UTF-8 text.
- `_section(heading_prefix)` — regex-extracts the H2 section starting
  with e.g. `"## 1."` and bounded by the next `^## ` heading or EOF.
  Used to scope JSON-block and Verify-snippet extraction so a future
  edit to one section can't accidentally widen the parse window.
- `_first_fenced_block(text, lang)` — extracts the first
  ```` ```<lang> ... ``` ```` block; used for both `json` (§2 config) and
  `sh` (Verify snippets).
- `_verify_snippet(section_text)` — finds `**Verify:**`, then reads the
  region up to the next `---` rule, then extracts the first `sh`
  fenced block from that region. Matches the intent's literal
  description ("between the **Verify:** heading of §N and the next
  --- rule").

## Ambiguity resolution log

Resolved at Phase 2 entry, before writing tests, except where noted.

| # | Ambiguity | Resolution |
|---|-----------|-----------|
| A | Intent says §1 has the bad path "in two places" — does the regex `scripts/role-cheatsheet\.sh` match both? | Yes — both the bullet (`scripts/role-cheatsheet.sh`) and the paragraph (`.slice-system/scripts/role-cheatsheet.sh`) match the substring `scripts/role-cheatsheet.sh`. Test 1 expects 0 matches post-fix; Test 2 expects ≥2 matches of `checks/role-cheatsheet\.sh` post-fix. |
| B | "Read the §2 JSON code-fence" — which code-fence, since §2 has prose snippets too? | Use `_section("## 2.")` then `_first_fenced_block(_, "json")` to grab only the first triple-backtick `json` block under that heading. The `env: {"PYTHONPATH": ...}` example later in §2 is inline prose, not a fenced block, so it cannot match. |
| C | "Stdout's first line parses as JSON" for Test 5 — does the corrected snippet `bash .slice-system/checks/role-cheatsheet.sh </dev/null \| head -1` actually produce JSON? | Verified at Phase 2 by running the snippet — it emits `{"hookSpecificOutput": {...}}` and exits 0. GREEN expectation valid. |
| D | "Between **Verify:** and next `---` rule" — exact extraction strategy? | Find `**Verify:**` index; find next `\n---` index; extract slice between; then `_first_fenced_block(_, "sh")` on that slice. Self-bounded by the fenced block; the `---` is just a region terminator. |
| E | `cwd=repo_root` — what is repo_root inside cairn's worktree? | `CAIRN_ROOT = Path(__file__).resolve().parents[2]` — same pattern as `test_consumer_migration_doc.py:22`. From cairn's worktree this resolves to the cairn checkout. `.slice-system → .` symlink makes the doc's `.slice-system/...` paths self-resolving. |
| F | Test 6 prereqs — `uv` on PATH and substrate venv populated? | Verified at Phase 2: `uv 0.11.8` on PATH; `.slice-system/.venv` populated; `uv run --directory .slice-system python -c "import mcp_servers.cairn_knowledge"` exits 0. GREEN expectation valid. |
| G | Test 7 SHA-256 baseline value — intent says "pinned at slice open" but does not pin it. | Captured at Phase 2 against the current pre-fix bytes of `## 3. Python dependencies`→EOF: `b136326efbe6be623e0c95df02cfe7c1e2cfcb77e04b3a715fea608ce9743d2b` (4009 bytes from byte 3524). Phase 3 must not edit Deltas 3/4/5; if a future edit is intentional, the baseline is re-pinned in a separate commit. |
| **H** (post-test-write surfacing) | **Tests 5 and 6 do not discriminate the bug inside cairn itself.** Cairn dogfoods its own hooks/MCP, so the OLD `jq -e ...` snippets succeed (rc=0; first stdout line is a valid JSON value — `"uv run python ..."` for §1, `true` for §2). Pure runtime-invoke assertions GREEN against the unfixed doc. | Resolved (operator-confirmed Option 1) by adding a `snippet == DELTA{1,2}_CORRECTED_SNIPPET` text-equality assertion *before* the runtime invocation. The corrected snippet text is given verbatim in intent.md §Specification Detail, so this is intent-faithful — the Skeptic is strengthening RED discrimination, not introducing new spec. The runtime-invoke leg remains as belt-and-suspenders so the test still catches a snippet that's textually correct but doesn't actually run. |

## RED verification (Phase 2 close state)

```
$ uv run pytest tests/unit/test_upgrade_doc_consumer_setup.py --tb=no -q
FFFFFF.                                                                  [100%]
6 failed, 1 passed in 0.02s
```

| Test | Status | Reason for failure (or pass) |
|------|--------|------------------------------|
| `test_delta1_bad_path_absent` | RED | Doc still contains 2 occurrences of `scripts/role-cheatsheet.sh`. |
| `test_delta1_good_path_present_at_least_twice` | RED | Doc contains 0 occurrences of `checks/role-cheatsheet.sh`. |
| `test_delta2_bare_python_command_eliminated` | RED | §2 JSON has `"command": "python"` with `["-m", "mcp_servers.cairn_knowledge"]`. |
| `test_delta2_uv_command_present_with_exact_args` | RED | §2 JSON `"command"` is `"python"`, expected `"uv"`. |
| `test_delta1_verify_snippet_runtime_invokes` | RED | §1 snippet text is the old `jq -e '...role_guard...'` form, not the corrected `bash .slice-system/checks/role-cheatsheet.sh ...`. |
| `test_delta2_verify_snippet_runtime_invokes` | RED | §2 snippet text is the old `jq -e '...mcpServers...'` form, not the corrected `uv run --directory .slice-system python -c ...`. |
| `test_deltas_3_4_5_bytes_unchanged` | GREEN (by construction) | Baseline pinned at slice open against current bytes. Turns RED if Phase 3 edits Deltas 3/4/5. |

All six RED failures are for the right reason (doc bug being discriminated), none are import errors or typos.

## Phase 3 envelope reminder

Per `slice.yaml`:

- `docs/upgrading-from-pre-compression.md` (the four edits — two prose + two snippet rewrites)
- `tests/unit/test_upgrade_doc_consumer_setup.py` (Phase 3 should not edit; only adjust the SHA-256 baseline if intentionally re-pinning, in a separate commit)

No source under `checks/`, `scripts/`, `mcp_servers/`, `.claude/agents/`, or `.claude/commands/` is in scope.
