# intent — substrate/root-resolver

proposed_slice_id: substrate/root-resolver
feature: root-resolver
tracking: firaaz/cairn#3 (rank 2 of 22)
lesson: L-017
audit-findings: F-039, F-040, F-041, F-042, F-048, F-049, F-050, F-510, F-511, F-512, F-513, F-514, F-515

## What

Lift the canonical project-root resolver out of scripts/validate_architecture.py (_repo_root) into a new scripts/_root.py module, and migrate every cwd-coupled call site in scripts/, mcp_servers/cairn_knowledge/, and the slice orchestrator to use it. Add a CI-enforced lint gate that fails on Path(".claude") or Path.cwd() outside _root.py and tests/.

Public-interface surface (modification slice):

- scripts/_root.py exports project_root() -> pathlib.Path (CLAUDE_PROJECT_DIR env var -> git rev-parse --show-toplevel -> loud RuntimeError). No __file__-relative resolution — the .slice-system -> . symlink canonicalizes wrong.
- All subprocess.run([..., "git", ...]) call sites grow an explicit cwd=project_root() kwarg.
- mcp_servers/cairn_knowledge/server.py DB and corpus paths resolve through project_root().
- cairn_query extractor entrypoints accept (or internally resolve via) project_root() instead of literal Path(".claude/features").
- New lint check (added to checks/ or invoked from scripts/validate_architecture.py) rejects forbidden literal patterns project-wide.

## Why

~25 of 135 audit findings collapse to one root cause: ad-hoc cwd-relative path resolution. The CWD-trap is already live in the wild — 4 misrouted commits and divergent kuzu DBs between cairn and complex-rag-analysis are the empirical signal. Every downstream substrate slice (consumer tenancy, MCP boundary, AGENT_ENVELOPE rollout) assumes a single deterministic project root. Without this lift, those slices either re-derive their own resolver (drift) or inherit the trap. The correct pattern already exists at scripts/validate_architecture.py:_repo_root; this slice promotes it from private helper to project-wide contract and retrofits the consumers.

## Boundary

In scope: scripts/_root.py (new); migration of scripts/slice_orchestrator/{core,lifecycle,dispatch,telemetry}.py; scripts/cairn_query/__init__.py and extractors/*.py; scripts/snapshot_diff.py; mcp_servers/cairn_knowledge/server.py; new lint rule wired into arch-validate; docs/operational-reference.md subsection declaring the CLAUDE_PROJECT_DIR contract.

Out of scope (per brief): slash-command markdown drift (issue #20/#21); upgrade-doc env-var headers; MCP corpus tenancy model (issue #14); any behavioral change to extractor output, orchestrator phase wiring, or slice-pipeline semantics — this is a path-plumbing slice only.

## Specification

### scripts/_root.py contract

project_root() -> pathlib.Path

Resolution precedence:

1. os.environ["CLAUDE_PROJECT_DIR"] if set and non-empty -> return Path(value).resolve().
2. Else subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=os.getcwd(), check=True, capture_output=True, text=True) -> return Path(stdout.strip()).resolve().
3. Else raise RuntimeError with a loud, actionable message naming both env-var and git-toplevel paths and the originating CalledProcessError.

Banned in this module and downstream: Path(__file__).parent... chains for project-root inference. The .slice-system -> . symlink makes __file__-resolution canonicalize to the consumer-side path on downstream installs; this is the root of L-017.

### Call-site migration rules

- Replace every Path(".claude/...") / Path(".claude") literal in production code with project_root() / ".claude" / ...
- Replace every Path.cwd() fallback in path construction with project_root().
- Every subprocess.run([... "git" ...]) call gains cwd=project_root() (or a passed-in root for tests).
- Tests under tests/ are exempt — they may use tmp_path and synthetic roots.

### Lint gate

Extend arch-validate (or a sibling check on the same CI path) with a regex-or-AST scan that fails when:

- Path("\.claude literal appears outside scripts/_root.py and tests/.
- Path.cwd() appears in any scripts/ or mcp_servers/ module.
- subprocess.run([..., "git", ...]) appears without a cwd= kwarg.

Failure message names the offending file:line and points at scripts/_root.py:project_root.

### Docs

docs/operational-reference.md — append "Project-root resolution" subsection: contract, precedence, symlink rationale, test-exemption.

## Verification

1. Unit: tests/unit/test_root.py — env-var path, git-toplevel path, raise-on-neither path. tmp_path + monkeypatched env + stubbed subprocess.run.
2. Migration completeness: lint gate exits 0 against post-migration tree; non-zero with offending location against a deliberately-reverted fixture.
3. Behavioral parity: existing orchestrator and cairn_query tests pass unchanged — no fixture edits beyond root injection where tests already construct fake roots.
4. Symlink trap regression: project_root() invoked from a cwd inside .slice-system/ (tmp_path symlink) returns real toplevel, not the symlinked view.
5. Subprocess cwd audit: lint gate's own test confirms zero git subprocess calls without explicit cwd= in scripts/ and mcp_servers/.

## Risks / open questions

- Lint gate home (extend validate_architecture.py vs new checks/path-discipline.sh vs new scripts/lint_paths.py) is a Phase-2 design call; intent leaves it as "wired into the same CI path as arch-validate".
- cairn_query extractor entrypoint signatures: brief notes they currently take no root arg. Phase 2 decides explicit root: Path parameter (purer) vs internal project_root() call (smaller diff). Either is consistent with this intent.
