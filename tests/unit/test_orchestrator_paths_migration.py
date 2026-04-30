"""Phase 2 RED tests for slice substrate/orchestrator-paths.

Slice intent (.claude/current-slice/intent.md) — root-resolver follow-up 1/2:

  Migrate the orchestrator-paths cluster and three scope-overflow callers
  off CWD-coupled path resolution onto the canonical
  ``scripts/_root.project_root()`` resolver landed by the predecessor
  slice. Public-interface surface only (modification slice).

Targets in scope:

  * scripts/slice_orchestrator/core.py
  * scripts/slice_orchestrator/lifecycle.py
  * scripts/slice_orchestrator/dispatch.py
  * scripts/slice_orchestrator/telemetry.py
  * scripts/integration_gate.py
  * scripts/validate_architecture.py
  * scripts/dogfood_evaluate.py

Migration rules (intent §Specification, applied uniformly across all
seven modules):

  1. ``Path(".claude/...")`` / ``Path(".claude")`` literals → resolved
     via ``project_root() / ".claude" / ...``.
  2. ``Path.cwd()`` fallbacks for project-root inference → ``project_root()``.
  3. ``subprocess.run([..., "git", ...])`` (or check_output/Popen) →
     gains explicit ``cwd=project_root()`` kwarg.
  4. ``from scripts._root import project_root`` imported in each module
     (or package-internal equivalent the predecessor established).

Verification (intent §Verification):

  V1. ``uv run python scripts/lint_paths.py`` exits 0.
  V2. The four parametrized + module-level orchestrator-regression
      ``pytest.mark.xfail(strict=True)`` markers in
      ``tests/unit/test_root_resolver_migration.py`` are gone, and the
      single covering xfail in ``tests/unit/test_path_discipline_lint.py``
      is gone.
  V4. At least one orchestrator test exercises ``project_root()``
      resolution from a cwd inside a ``.slice-system`` symlink fixture
      and asserts the canonical toplevel is returned (L-017 trap
      regression).
  V5. No scope leak — diff touches only the seven production modules and
      the two existing test files, plus this new test file.

Phase-2 ambiguity notes (resolved in approach.md):

  * Slice brief says "Remove 4 strict-xfail markers" while intent §Test
    unmarks lists 5 (4 parametrized + 1 module-level orchestrator
    regression). Two further module-level xfails
    (test_no_path_cwd_in_production_code,
    test_every_git_subprocess_call_has_explicit_cwd) plus
    test_no_dotclaude_literal_anywhere_in_production_code and
    test_gate_passes_on_post_migration_cairn_tree would XPASS strict
    after this migration and would therefore fail the suite — they MUST
    also be unmarked. Phase-2 decision: enforce removal of every
    strict-xfail that XPASSes post-migration; leave only the
    MCP-cluster xfail (issue #25, out of scope).
  * scripts/slice_orchestrator/git.py is NOT in the named targets but is
    inside scripts/slice_orchestrator/ which the lint gate scans. Its
    subprocess.run uses a Name (``cmd``) not a list literal, so the
    AST-based lint gate does not flag it. Lint-exits-0 contract holds.
  * validate_architecture.py:_repo_root / _resolve_project_root may
    remain as a thin alias OR be deleted — both consistent with intent.
    Tests assert ``project_root`` is imported from ``scripts._root`` to
    force the migration path while leaving the alias choice open.

These tests intentionally OVERLAP with assertions in
``test_root_resolver_migration.py`` — once the predecessor xfails are
removed, both files should agree. Defence-in-depth: the slice-specific
file pins the seven-module surface explicitly and survives even if
``test_root_resolver_migration.py`` gets refactored.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = CAIRN_ROOT / "scripts"

ORCHESTRATOR_TARGETS: list[Path] = [
    SCRIPTS / "slice_orchestrator" / "core.py",
    SCRIPTS / "slice_orchestrator" / "lifecycle.py",
    SCRIPTS / "slice_orchestrator" / "dispatch.py",
    SCRIPTS / "slice_orchestrator" / "telemetry.py",
]

SCOPE_OVERFLOW_TARGETS: list[Path] = [
    SCRIPTS / "integration_gate.py",
    SCRIPTS / "validate_architecture.py",
    SCRIPTS / "dogfood_evaluate.py",
]

ALL_TARGETS: list[Path] = ORCHESTRATOR_TARGETS + SCOPE_OVERFLOW_TARGETS


def _rel(p: Path) -> str:
    return str(p.relative_to(CAIRN_ROOT))


# ---------------------------------------------------------------------------
# AST helpers (mirrors scripts/lint_paths.py visitors so suite catches gaps
# even if the lint gate is buggy or skipped).
# ---------------------------------------------------------------------------


def _path_call_string_arg(node: ast.Call) -> str | None:
    if not isinstance(node.func, ast.Name) or node.func.id != "Path":
        return None
    if not node.args or not isinstance(node.args[0], ast.Constant):
        return None
    val = node.args[0].value
    return val if isinstance(val, str) else None


class _DotClaudeLiteralVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.hits: list[tuple[int, str]] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        s = _path_call_string_arg(node)
        if s is not None and (s == ".claude" or s.startswith(".claude/")):
            self.hits.append((node.lineno, s))
        self.generic_visit(node)


class _CwdVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.hits: list[int] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        f = node.func
        if (
            isinstance(f, ast.Attribute)
            and f.attr == "cwd"
            and isinstance(f.value, ast.Name)
            and f.value.id == "Path"
        ):
            self.hits.append(node.lineno)
        self.generic_visit(node)


class _GitSubprocessVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.hits: list[int] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        f = node.func
        if isinstance(f, ast.Attribute) and f.attr == "run":
            if node.args and isinstance(node.args[0], (ast.List, ast.Tuple)):
                elts = node.args[0].elts
                if (
                    elts
                    and isinstance(elts[0], ast.Constant)
                    and elts[0].value == "git"
                ):
                    has_cwd = any(kw.arg == "cwd" for kw in node.keywords)
                    if not has_cwd:
                        self.hits.append(node.lineno)
        self.generic_visit(node)


def _ast_for(target: Path) -> ast.AST:
    if not target.exists():
        pytest.fail(f"migration target missing: {_rel(target)}")
    return ast.parse(target.read_text(encoding="utf-8"), filename=str(target))


# ---------------------------------------------------------------------------
# Migration rule 1 — no Path(".claude/...") literal in any of the seven
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("target", ALL_TARGETS, ids=_rel)
def test_target_has_no_dotclaude_literal(target: Path):
    """Intent §Specification rule 1: no Path('.claude/...') literal in
    any of the seven targets — every site routes through project_root().
    """
    tree = _ast_for(target)
    v = _DotClaudeLiteralVisitor()
    v.visit(tree)
    assert v.hits == [], (
        f"{_rel(target)}: residual Path('.claude/...') literals at "
        f"{v.hits} — must route through scripts/_root.project_root()"
    )


# ---------------------------------------------------------------------------
# Migration rule 2 — no Path.cwd() in any of the seven
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("target", ALL_TARGETS, ids=_rel)
def test_target_has_no_path_cwd(target: Path):
    """Intent §Specification rule 2: Path.cwd() used for project-root
    inference becomes project_root() in all seven targets.

    Intent allows Path.cwd() for "genuinely process-relative purposes"
    in principle, but none of the seven targets has such a use today —
    every Path.cwd() in the current tree is project-root inference.
    Phase 2 audited each call site (per intent rule 2) and confirms a
    blanket ban for these seven files.
    """
    tree = _ast_for(target)
    v = _CwdVisitor()
    v.visit(tree)
    assert v.hits == [], (
        f"{_rel(target)}: residual Path.cwd() at lines {v.hits} — "
        "use project_root() instead"
    )


# ---------------------------------------------------------------------------
# Migration rule 3 — every literal-list git subprocess has cwd=
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("target", ALL_TARGETS, ids=_rel)
def test_target_git_subprocess_calls_have_explicit_cwd(target: Path):
    """Intent §Specification rule 3: every subprocess.run([..., 'git', ...])
    call gains an explicit cwd=project_root() kwarg.

    This visitor only catches literal-list invocations. Calls that go
    through an indirection (e.g. ``cmd = ['git', *args]; run(cmd)``) are
    out of AST reach and rely on the higher-level lint gate +
    code-review.
    """
    tree = _ast_for(target)
    v = _GitSubprocessVisitor()
    v.visit(tree)
    assert v.hits == [], (
        f"{_rel(target)}: subprocess.run(['git', ...]) at lines {v.hits} "
        "missing cwd= kwarg — add cwd=project_root()"
    )


# ---------------------------------------------------------------------------
# Migration rule 4 — module imports project_root from scripts._root
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("target", ALL_TARGETS, ids=_rel)
def test_target_imports_project_root_from_scripts_root(target: Path):
    """Intent §Specification rule 4 + §Migration rule 1:
    'Import from scripts._root import project_root (or the
    package-internal equivalent the predecessor established).'

    Asserts every migrated module imports the canonical resolver.
    Accepts either ``from scripts._root import project_root`` or
    ``from _root import project_root`` (pyproject puts scripts/ on
    pythonpath, so both forms reach the same module).
    """
    tree = _ast_for(target)

    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod in {"scripts._root", "_root"} or mod.endswith("._root"):
                if any(a.name == "project_root" for a in node.names):
                    found = True
                    break

    assert found, (
        f"{_rel(target)}: must import project_root from scripts._root "
        "(or _root) per intent §Specification rule 4"
    )


# ---------------------------------------------------------------------------
# V1 — lint gate exits 0 against the post-migration cairn tree
# ---------------------------------------------------------------------------


def test_lint_paths_gate_exits_zero_against_real_tree():
    """Intent §Verification 1: ``uv run python scripts/lint_paths.py``
    exits 0 against the post-migration tree.

    Runs the same module the existing test_path_discipline_lint.py
    invokes against synthetic trees, but pointed at the real cairn
    checkout. After this slice ships, every violation site in
    scripts/ + mcp_servers/ that the gate scans is migrated, so the
    gate must be silent.

    NB: mcp_servers/cairn_knowledge/server.py uses
    ``Path(__file__).resolve().parent.parent.parent`` for project-root
    inference, which is an L-017 violation but NOT one of the three
    rules the gate scans for (.claude literal / Path.cwd / bare git
    subprocess). It is therefore not flagged today and is out of scope
    for this slice (issue #25 covers MCP).
    """
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(CAIRN_ROOT)
    env["PYTHONPATH"] = (
        str(CAIRN_ROOT / "scripts") + os.pathsep + env.get("PYTHONPATH", "")
    )
    result = subprocess.run(
        [sys.executable, "-m", "lint_paths"],
        cwd=CAIRN_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "scripts/lint_paths.py must exit 0 against the post-migration "
        f"cairn tree.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# V2 — predecessor strict-xfail markers gone (suite-green guarantee)
# ---------------------------------------------------------------------------


_PRED_MIGRATION_TEST = CAIRN_ROOT / "tests" / "unit" / "test_root_resolver_migration.py"
_PRED_LINT_TEST = CAIRN_ROOT / "tests" / "unit" / "test_path_discipline_lint.py"


def _xfail_decorators(node: ast.AST) -> list[ast.expr]:
    """Return the xfail decorator nodes attached to a function, if any."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return []
    out: list[ast.expr] = []
    for dec in node.decorator_list:
        # Strip Call() wrapping
        target = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(target, ast.Attribute) and target.attr == "xfail":
            out.append(dec)
    return out


def _funcdef_named(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


# Names that MUST be free of any pytest.mark.xfail decorator post-migration.
# Each would XPASS strict after this slice ships (verified by
# test_target_*/test_lint_paths_gate_exits_zero_against_real_tree above).
_UNMARKED_FUNCTIONS_MIGRATION_FILE = [
    "test_no_dotclaude_literal_anywhere_in_production_code",
    "test_no_path_cwd_in_production_code",
    "test_every_git_subprocess_call_has_explicit_cwd",
    "test_orchestrator_modules_have_no_dotclaude_literals",
]

_UNMARKED_FUNCTIONS_LINT_FILE = [
    "test_gate_passes_on_post_migration_cairn_tree",
]

# The MCP-cluster xfail STAYS (issue #25, out of scope).
_STILL_XFAIL_MIGRATION_FILE = [
    "test_mcp_server_does_not_use_file_dunder_for_root_inference",
]


@pytest.mark.parametrize("name", _UNMARKED_FUNCTIONS_MIGRATION_FILE)
def test_predecessor_migration_xfail_marker_removed(name: str):
    """Intent §Test unmarks (expanded — see module docstring): every
    strict-xfail that XPASSes post-migration MUST be unmarked, else the
    suite breaks at Phase 3 (Verification 3 'Full uv run pytest tests/unit/
    run is green').
    """
    tree = ast.parse(_PRED_MIGRATION_TEST.read_text(encoding="utf-8"))
    fn = _funcdef_named(tree, name)
    assert fn is not None, (
        f"expected to find {name!r} in test_root_resolver_migration.py — "
        "did the file shape change?"
    )
    decs = _xfail_decorators(fn)
    assert decs == [], (
        f"{name}: pytest.mark.xfail still present "
        f"(at lines {[d.lineno for d in decs]}); intent §Test unmarks "
        "requires removal — strict xfail XPASSes post-migration and "
        "will fail the suite."
    )


@pytest.mark.parametrize("name", _UNMARKED_FUNCTIONS_LINT_FILE)
def test_predecessor_lint_xfail_marker_removed(name: str):
    """Intent §Test unmarks: drop the single strict-xfail in
    test_path_discipline_lint.py covering this cluster
    (test_gate_passes_on_post_migration_cairn_tree).
    """
    tree = ast.parse(_PRED_LINT_TEST.read_text(encoding="utf-8"))
    fn = _funcdef_named(tree, name)
    assert fn is not None, f"expected to find {name!r} in test_path_discipline_lint.py"
    decs = _xfail_decorators(fn)
    assert decs == [], (
        f"{name}: pytest.mark.xfail still present "
        f"(at lines {[d.lineno for d in decs]}); intent §Test unmarks "
        "requires removal."
    )


def test_predecessor_orchestrator_param_xfails_removed():
    """The four parametrized ``pytest.param(... marks=pytest.mark.xfail)``
    entries for orchestrator modules in test_root_resolver_migration.py
    must lose their xfail marks (intent §Test unmarks).

    Asserts: in MIGRATION_TARGETS (the parametrize argument list), no
    pytest.param call wrapping an orchestrator module path carries any
    pytest.mark.xfail in its ``marks=`` kwarg.
    """
    src = _PRED_MIGRATION_TEST.read_text(encoding="utf-8")
    tree = ast.parse(src)

    orchestrator_module_names = {t.name for t in ORCHESTRATOR_TARGETS}

    offenders: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        # match pytest.param(...)
        f = node.func
        is_param = (
            isinstance(f, ast.Attribute)
            and f.attr == "param"
            and isinstance(f.value, ast.Name)
            and f.value.id == "pytest"
        )
        if not is_param:
            continue

        # Reconstruct the first positional arg as text and check whether
        # it references an orchestrator module name.
        if not node.args:
            continue
        arg_src = ast.unparse(node.args[0])
        if not any(name in arg_src for name in orchestrator_module_names):
            continue
        if "slice_orchestrator" not in arg_src:
            continue

        # Inspect marks= kwarg
        for kw in node.keywords:
            if kw.arg != "marks":
                continue
            kw_src = ast.unparse(kw.value)
            if "xfail" in kw_src:
                offenders.append(
                    f"pytest.param({arg_src}, marks={kw_src}) at line {node.lineno}"
                )

    assert offenders == [], (
        "Orchestrator param entries still carry pytest.mark.xfail in "
        "test_root_resolver_migration.py — intent §Test unmarks requires "
        "removal so the parametrized cases run as regular tests:\n  "
        + "\n  ".join(offenders)
    )


def test_predecessor_mcp_xfail_still_present():
    """Negative control — MCP-cluster xfail must NOT be removed in this
    slice (intent §Boundary out-of-scope; issue #25). Guards against an
    over-eager unmark that would break the suite when MCP server still
    has L-017 violations.
    """
    tree = ast.parse(_PRED_MIGRATION_TEST.read_text(encoding="utf-8"))
    for name in _STILL_XFAIL_MIGRATION_FILE:
        fn = _funcdef_named(tree, name)
        assert fn is not None, f"expected to find {name!r}"
        decs = _xfail_decorators(fn)
        assert decs, (
            f"{name}: pytest.mark.xfail unexpectedly removed — MCP "
            "cluster is out of scope for this slice (issue #25); "
            "removing this marker now will break the suite because "
            "mcp_servers/cairn_knowledge/server.py still uses "
            "Path(__file__).parent.parent.parent for root inference."
        )


# ---------------------------------------------------------------------------
# V4 — symlink-trap regression: project_root() resolves canonical from
# inside a .slice-system symlink (L-017)
# ---------------------------------------------------------------------------


def _git_available() -> bool:
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True, text=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


@pytest.mark.skipif(not _git_available(), reason="git not installed")
def test_project_root_resolves_canonical_from_inside_slice_system_symlink(
    tmp_path: Path,
):
    """Intent §Verification 4 (L-017 trap regression):

      'At least one orchestrator test exercises project_root()
      resolution from a cwd inside a .slice-system symlink fixture and
      asserts canonical toplevel is returned.'

    Construction:
      tmp_path/repo/                  (git init'd; canonical root)
      tmp_path/repo/.slice-system     (symlink → tmp_path/repo)
      cwd = tmp_path/repo/.slice-system

    With CLAUDE_PROJECT_DIR unset and git rev-parse as the resolution
    mechanism, project_root() must return tmp_path/repo (canonical),
    not tmp_path/repo/.slice-system (the symlinked view that
    canonicalizes wrong on consumers per L-017).
    """
    fake_root = tmp_path / "repo"
    fake_root.mkdir()
    subprocess.run(
        ["git", "init"],
        cwd=fake_root,
        check=True,
        capture_output=True,
    )

    # The L-017 trap: .slice-system → . inside the same repo.
    (fake_root / ".slice-system").symlink_to(fake_root)

    inside_symlink = fake_root / ".slice-system"
    assert inside_symlink.is_symlink()

    env = os.environ.copy()
    env.pop("CLAUDE_PROJECT_DIR", None)  # force git fallback path
    env["PYTHONPATH"] = (
        str(CAIRN_ROOT / "scripts") + os.pathsep + env.get("PYTHONPATH", "")
    )

    code = "from _root import project_root; print(project_root())"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=inside_symlink,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"project_root() crashed when invoked from inside .slice-system "
        f"symlink:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )

    resolved = Path(result.stdout.strip())
    canonical = fake_root.resolve()

    assert resolved == canonical, (
        f"L-017 trap regression: project_root() returned {resolved!r}, "
        f"expected canonical {canonical!r}. Resolution from inside a "
        ".slice-system → . symlink must return the real toplevel, not "
        "the symlinked view."
    )

    # Defence-in-depth: the resolved path must NOT contain ".slice-system".
    assert ".slice-system" not in resolved.parts, (
        f"resolved path {resolved!r} contains '.slice-system' — "
        "symlink was not canonicalized away"
    )


# ---------------------------------------------------------------------------
# V5 — scope leak guardrail (best-effort; lints the slice surface only)
# ---------------------------------------------------------------------------


def test_no_new_dotclaude_literals_in_other_scripts():
    """Intent §Verification 5: 'No scope leak. git diff --stat touches
    only the seven production modules and the two test files.'

    This isn't a diff check (Phase 3's purview), but a static guardrail:
    no production .py file under scripts/ outside the seven targets and
    the canonical exemption (scripts/_root.py) introduces a new
    Path('.claude/...') literal.

    Existing pre-slice violations (cairn-query already migrated;
    snapshot-diff already migrated) are reflected as the empty-baseline:
    a passing assertion. If Phase 3 spreads the migration into adjacent
    modules and accidentally injects a new literal, this catches it.
    """
    in_scope = {p.resolve() for p in ALL_TARGETS}
    in_scope.add((SCRIPTS / "_root.py").resolve())  # canonical exemption

    offenders: list[str] = []
    for f in SCRIPTS.rglob("*.py"):
        if "__pycache__" in f.parts:
            continue
        if ".slice-system" in f.parts:
            continue
        if f.resolve() in in_scope:
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        v = _DotClaudeLiteralVisitor()
        v.visit(tree)
        for ln, s in v.hits:
            offenders.append(f"{_rel(f)}:{ln} Path({s!r})")

    assert offenders == [], (
        "Production scripts/ modules outside the slice surface contain "
        "Path('.claude/...') literals — possible scope leak:\n  "
        + "\n  ".join(offenders)
    )


# ---------------------------------------------------------------------------
# Sanity: pre-conditions of this slice still hold
# ---------------------------------------------------------------------------


def test_lint_gate_module_present():
    """Sanity: scripts/lint_paths.py shipped in the predecessor slice and
    has not been removed (this slice does not touch it)."""
    gate = SCRIPTS / "lint_paths.py"
    assert gate.exists(), (
        "scripts/lint_paths.py missing — predecessor slice deliverable, "
        "this slice does not modify it"
    )


def test_root_module_present():
    """Sanity: scripts/_root.py shipped in the predecessor slice and has
    not been removed (this slice does not touch it)."""
    root_mod = SCRIPTS / "_root.py"
    assert root_mod.exists(), "scripts/_root.py missing"
    src = root_mod.read_text(encoding="utf-8")
    assert "def project_root" in src, "scripts/_root.py: project_root() must be defined"


def test_predecessor_test_files_present():
    """Sanity: predecessor test files exist (we mutate their xfail markers)."""
    assert _PRED_MIGRATION_TEST.exists(), (
        f"predecessor test missing: {_PRED_MIGRATION_TEST}"
    )
    assert _PRED_LINT_TEST.exists(), f"predecessor test missing: {_PRED_LINT_TEST}"


# Module-level smoke: every named target is a real file (catches typos in
# the ALL_TARGETS list before parametrize fans out).
def test_all_targets_exist():
    missing = [str(_rel(t)) for t in ALL_TARGETS if not t.exists()]
    assert not missing, f"migration targets missing: {missing}"
