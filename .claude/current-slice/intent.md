# intent — substrate/orchestrator-paths

proposed_slice_id: substrate/orchestrator-paths
feature: orchestrator-paths
tracking: firaaz/cairn#24 (root-resolver follow-up 1/2)
predecessor: substrate/root-resolver (failed; surviving work at f9f8866)
lesson: L-017
audit-findings: F-039, F-040, F-041, F-042, F-048, F-049, F-050 (orchestrator-cluster subset)

## What

Migrate the orchestrator-paths cluster and three scope-overflow callers off CWD-coupled path resolution onto the canonical `scripts/_root.project_root()` resolver landed by the predecessor slice. Modification slice — public-interface surface only:

- `scripts/slice_orchestrator/core.py`, `lifecycle.py`, `dispatch.py`, `telemetry.py`: every `Path(".claude/...")` literal, every `Path.cwd()` fallback, and every bare `subprocess.run([..., "git", ...])` call routes through `project_root()` (or accepts an explicit `root: Path` argument and threads it).
- `scripts/integration_gate.py`, `scripts/validate_architecture.py`, `scripts/dogfood_evaluate.py`: same migration rules; these three are the scope-overflow callers the predecessor lint gate flagged outside the orchestrator package.
- Remove the four strict-xfail markers in `tests/unit/test_root_resolver_migration.py` (parametrized orchestrator entries plus the module-level orchestrator regression) and the one strict-xfail in `tests/unit/test_path_discipline_lint.py` covering this cluster.
- `scripts/lint_paths.py` exits 0 against the post-migration tree.

## Why

The predecessor slice (`substrate/root-resolver`) shipped `scripts/_root.py`, `scripts/lint_paths.py`, and the test scaffolding, but failed mid-phase-3 to a concurrent-orchestrator collision before the orchestrator and MCP clusters landed. Until those callers migrate, the lint gate is held back by xfail markers and the CWD-trap remains live in the very component (slice_orchestrator) that triggered the original collision — every future slice run risks repeating the four-misrouted-commit incident. This slice closes the orchestrator half of the deferred work; issue #25 covers the MCP half.

## Boundary

In scope: the seven Python modules listed above plus the five xfail-marker removals. Behavioral parity required — no change to orchestrator phase wiring, dispatch semantics, telemetry payloads, integration-gate decisions, arch-validate findings, or dogfood evaluation output. Path-plumbing only.

Out of scope: `mcp_servers/cairn_knowledge/server.py` and the cairn-query / snapshot-diff clusters (separate follow-ups, issue #25 for MCP). No changes to `scripts/_root.py` or `scripts/lint_paths.py` beyond what migration forces. No new lint rules. No docs edits. No fixture rewrites in tests beyond unmarking the listed xfails.

## Specification

### Migration rules (apply uniformly across all seven modules)

1. **`.claude` literals.** Replace `Path(".claude/...")` and `Path(".claude")` with `project_root() / ".claude" / ...`. Import `from scripts._root import project_root` (or the package-internal equivalent the predecessor established).
2. **`Path.cwd()` fallbacks.** Any `Path.cwd()` used for project-root inference becomes `project_root()`. `Path.cwd()` used for genuinely process-relative purposes stays — Phase 2 audits each.
3. **Bare git subprocess calls.** Every `subprocess.run([..., "git", ...])` (or `check_output`, `Popen`) gains an explicit `cwd=project_root()` kwarg. Tests that already construct synthetic roots pass `cwd=root` instead.
4. **Function signatures.** Prefer threading an explicit `root: Path` parameter through internal helpers when the call graph already crosses module boundaries; otherwise call `project_root()` at the entrypoint. Public callable signatures unchanged where possible — when a signature must grow a `root` kwarg, it defaults to `None` with internal `root or project_root()` resolution.

### Test unmarks

- `tests/unit/test_root_resolver_migration.py`: drop `pytest.mark.xfail(...)` from the parametrized orchestrator entries (`core.py`, `lifecycle.py`, `dispatch.py`, `telemetry.py` — four `pytest.param` entries) and the module-level orchestrator regression marker. MCP-cluster xfail stays (issue #25). Other cluster xfails (cairn-query, snapshot-diff) stay.
- `tests/unit/test_path_discipline_lint.py`: drop the single strict-xfail covering orchestrator + scope-overflow files.

### Lint-gate contract

`scripts/lint_paths.py` exits 0 against `scripts/slice_orchestrator/`, `scripts/integration_gate.py`, `scripts/validate_architecture.py`, `scripts/dogfood_evaluate.py`. Non-zero exits remain expected (and xfail-protected) for still-unmigrated clusters.

## Verification

1. **Lint gate green.** `uv run python scripts/lint_paths.py` exits 0 — confirmed by the unmarked `test_path_discipline_lint.py` test passing without xfail.
2. **Migration tests live.** The four unmarked entries in `test_root_resolver_migration.py` pass as regular tests, asserting (a) zero `Path(".claude")` literals per module, (b) zero bare `Path.cwd()`, (c) every git subprocess call carries `cwd=`.
3. **Behavioral parity.** Full `uv run pytest tests/unit/` run is green. No fixture edits beyond xfail removal; any new fixture pressure signals a Phase-2 review.
4. **Symlink-trap regression.** At least one orchestrator test exercises `project_root()` resolution from a cwd inside a `.slice-system` symlink fixture and asserts canonical toplevel is returned.
5. **No scope leak.** `git diff --stat` touches only the seven production modules and the two test files. No edits under `mcp_servers/`, `scripts/cairn_query/`, `scripts/snapshot_diff.py`, `scripts/_root.py`, `scripts/lint_paths.py`, or `docs/`.

## Risks / open questions

- **Concurrent-orchestrator collision (the predecessor killer).** Phase-3 dispatch must verify no foreign session is writing to this repo .claude/ tree before long-running operations. Operationally a Phase-3 concern, but flagged so the integrator does not repeat the 1800s-timeout death spiral.
- **`scripts/validate_architecture.py:_repo_root`.** Original donor of `project_root()` logic. Phase 2 decides whether to delete it outright (callers re-route to `project_root()`) or keep as a thin alias. Either consistent with this intent; deletion preferred if the call graph allows.
- **`dogfood_evaluate.py` scope.** Predecessor coupling-cluster yaml did not list this file; it surfaced from the lint gate post-migration. Confirm during Phase 2 that all three scope-overflow files are still flagged by the current `lint_paths.py` run before extending the slice surface.
