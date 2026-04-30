"""Phase 2 RED tests for slice substrate/root-resolver — call-site migration audit.

Intent §Specification §"Call-site migration rules":
  - Replace every Path(".claude/...") / Path(".claude") literal in production
    code with project_root() / ".claude" / ...
  - Replace every Path.cwd() fallback in path construction with project_root().
  - Every subprocess.run([... "git" ...]) call gains cwd=project_root() (or a
    passed-in root for tests).
  - Tests under tests/ are exempt.

These tests perform AST scans on the post-migration tree (production code in
scripts/ and mcp_servers/) and assert the migration is complete. They are
intentionally redundant with the lint gate (tested separately) so that a
lint-gate bug cannot mask an incomplete migration.

Brief enumerates the migration targets:
  - scripts/slice_orchestrator/{core,lifecycle,dispatch,telemetry}.py
  - scripts/cairn_query/__init__.py
  - scripts/cairn_query/extractors/*.py
  - scripts/snapshot_diff.py
  - mcp_servers/cairn_knowledge/server.py
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = CAIRN_ROOT / "scripts"
MCP = CAIRN_ROOT / "mcp_servers"

# Files that are EXEMPT from the literal-".claude" ban.
# Per intent §Lint gate: "outside scripts/_root.py and tests/."
DOTCLAUDE_LITERAL_EXEMPT = {
    SCRIPTS / "_root.py",
}

# Migration targets explicitly named in slice brief.
#
# orchestrator-paths and mcp-server clusters did not land — the
# substrate/root-resolver slice was abandoned mid-phase-3 due to a
# concurrent-orchestrator state collision (firaaz/cairn#3 follow-up).
# Those entries are wrapped in pytest.param with strict xfail so the
# marker auto-fails when the follow-up cluster ships, forcing removal.
_ORCHESTRATOR_XFAIL_REASON = (
    "orchestrator-paths cluster pending follow-up (firaaz/cairn#3): "
    "substrate/root-resolver slice abandoned mid-phase-3"
)
_MCP_SERVER_XFAIL_REASON = (
    "mcp-server cluster pending follow-up (firaaz/cairn#3): "
    "substrate/root-resolver slice abandoned mid-phase-3"
)

MIGRATION_TARGETS = [
    SCRIPTS / "slice_orchestrator" / "core.py",
    SCRIPTS / "slice_orchestrator" / "lifecycle.py",
    SCRIPTS / "slice_orchestrator" / "dispatch.py",
    SCRIPTS / "slice_orchestrator" / "telemetry.py",
    SCRIPTS / "cairn_query" / "__init__.py",
    SCRIPTS / "cairn_query" / "__main__.py",
    SCRIPTS / "cairn_query" / "validators.py",
    SCRIPTS / "cairn_query" / "extractors" / "feature.py",
    SCRIPTS / "cairn_query" / "extractors" / "slice.py",
    SCRIPTS / "snapshot_diff.py",
    MCP / "cairn_knowledge" / "server.py",
]


# ---------------------------------------------------------------------------
# Helpers — AST visitors
# ---------------------------------------------------------------------------


def _iter_production_py_files():
    """Yield every production .py file under scripts/ and mcp_servers/.

    Excludes __pycache__, tests, and any .slice-system symlink loop.
    """
    for root in (SCRIPTS, MCP):
        if not root.exists():
            continue
        for f in root.rglob("*.py"):
            if "__pycache__" in f.parts:
                continue
            # Defensive: avoid walking into a .slice-system symlink loop if
            # one ever appears under scripts/.
            if ".slice-system" in f.parts:
                continue
            yield f


def _path_call_string_arg(node: ast.Call) -> str | None:
    """If node is `Path("...")`, return the string argument; else None."""
    if not isinstance(node.func, ast.Name) or node.func.id != "Path":
        return None
    if not node.args or not isinstance(node.args[0], ast.Constant):
        return None
    val = node.args[0].value
    if isinstance(val, str):
        return val
    return None


class _DotClaudeLiteralVisitor(ast.NodeVisitor):
    """Collect line numbers where Path(".claude...") literal appears."""

    def __init__(self):
        self.hits: list[tuple[int, str]] = []

    def visit_Call(self, node: ast.Call):  # noqa: N802
        s = _path_call_string_arg(node)
        if s is not None and (s == ".claude" or s.startswith(".claude/")):
            self.hits.append((node.lineno, s))
        self.generic_visit(node)


class _CwdVisitor(ast.NodeVisitor):
    """Collect line numbers where Path.cwd() appears."""

    def __init__(self):
        self.hits: list[int] = []

    def visit_Call(self, node: ast.Call):  # noqa: N802
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
    """Collect subprocess.run([..., 'git', ...]) call sites missing cwd= kwarg.

    Recognizes:
      subprocess.run(["git", ...], ...)
      subprocess.run(["git", *args], ...)
      _run(["git", ...], ...)  -- conservative: any *.run with first-arg list
                                  that begins with the literal "git".
    """

    def __init__(self):
        self.hits: list[int] = []

    def visit_Call(self, node: ast.Call):  # noqa: N802
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


# ---------------------------------------------------------------------------
# Migration assertions — Path(".claude/...") literal ban
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "target", MIGRATION_TARGETS, ids=lambda p: str(p.relative_to(CAIRN_ROOT))
)
def test_migration_target_has_no_dotclaude_literal(target: Path):
    """Each named migration target must contain zero Path('.claude/...') literals."""
    if not target.exists():
        pytest.fail(f"migration target missing: {target}")

    tree = ast.parse(target.read_text())
    v = _DotClaudeLiteralVisitor()
    v.visit(tree)

    rel = target.relative_to(CAIRN_ROOT)
    assert v.hits == [], (
        f"{rel}: residual Path('.claude/...') literals at lines "
        f"{[(ln, s) for ln, s in v.hits]} — must route through scripts/_root.project_root()"
    )


def test_no_dotclaude_literal_anywhere_in_production_code():
    """Project-wide: no Path('.claude/...') literal in scripts/ or mcp_servers/
    outside the exempt set (scripts/_root.py).
    """
    offenders: list[str] = []
    for f in _iter_production_py_files():
        if f.resolve() in {p.resolve() for p in DOTCLAUDE_LITERAL_EXEMPT}:
            continue
        try:
            tree = ast.parse(f.read_text())
        except SyntaxError:
            continue
        v = _DotClaudeLiteralVisitor()
        v.visit(tree)
        for ln, s in v.hits:
            offenders.append(f"{f.relative_to(CAIRN_ROOT)}:{ln} Path({s!r})")

    assert offenders == [], (
        "Path('.claude/...') literals found outside scripts/_root.py and tests/:\n  "
        + "\n  ".join(offenders)
    )


# ---------------------------------------------------------------------------
# Migration assertions — Path.cwd() ban in scripts/ and mcp_servers/
# ---------------------------------------------------------------------------


def test_no_path_cwd_in_production_code():
    """Path.cwd() must not appear in scripts/ or mcp_servers/ — replaced by
    project_root() everywhere per intent §Specification.
    """
    offenders: list[str] = []
    for f in _iter_production_py_files():
        # _root.py itself may legitimately reference cwd (e.g. as the cwd= arg
        # to subprocess.run). It does not appear in the lint-gate exemption
        # list because intent says "any scripts/ or mcp_servers/ module";
        # but subprocess.run(... cwd=os.getcwd() ...) uses os.getcwd, not
        # Path.cwd(). So no exemption needed here.
        try:
            tree = ast.parse(f.read_text())
        except SyntaxError:
            continue
        v = _CwdVisitor()
        v.visit(tree)
        for ln in v.hits:
            offenders.append(f"{f.relative_to(CAIRN_ROOT)}:{ln} Path.cwd()")

    assert offenders == [], (
        "Path.cwd() found in production code — replace with project_root():\n  "
        + "\n  ".join(offenders)
    )


# ---------------------------------------------------------------------------
# Migration assertions — subprocess.run([..., "git", ...]) cwd= kwarg
# ---------------------------------------------------------------------------


def test_every_git_subprocess_call_has_explicit_cwd():
    """Intent §Specification: 'Every subprocess.run([... "git" ...]) call
    gains cwd=project_root() (or a passed-in root for tests).'

    AST scans every production .py for subprocess.run-style invocation whose
    first-arg list literal starts with 'git' and asserts a cwd= keyword arg
    is present.
    """
    offenders: list[str] = []
    for f in _iter_production_py_files():
        try:
            tree = ast.parse(f.read_text())
        except SyntaxError:
            continue
        v = _GitSubprocessVisitor()
        v.visit(tree)
        for ln in v.hits:
            offenders.append(f"{f.relative_to(CAIRN_ROOT)}:{ln}")

    assert offenders == [], (
        "subprocess.run(['git', ...]) call sites missing explicit cwd= kwarg:\n  "
        + "\n  ".join(offenders)
        + "\nAdd cwd=project_root() per scripts/_root.py:project_root."
    )


# ---------------------------------------------------------------------------
# Specific call-site assertions named in the slice brief
# ---------------------------------------------------------------------------


def test_snapshot_diff_resolve_root_uses_project_root():
    """scripts/snapshot_diff.py:_resolve_root must delegate to project_root,
    not return Path.cwd(). Brief: 'replace Path.cwd() fallback in _resolve_root.'
    """
    src = (SCRIPTS / "snapshot_diff.py").read_text()
    tree = ast.parse(src)

    fn = next(
        (
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name == "_resolve_root"
        ),
        None,
    )
    assert fn is not None, "scripts/snapshot_diff.py:_resolve_root missing"

    body_src = ast.unparse(fn)
    assert "Path.cwd()" not in body_src, (
        f"_resolve_root still calls Path.cwd():\n{body_src}"
    )
    assert "project_root" in body_src, (
        f"_resolve_root must call project_root():\n{body_src}"
    )


def test_cairn_query_init_default_db_path_uses_project_root():
    """scripts/cairn_query/__init__.py:DEFAULT_DB_PATH must derive from
    project_root(), not a bare Path('.claude/...') literal. Brief: '_DEFAULT_DB_PATH
    and extractor entrypoints (currently take no root arg).'
    """
    src = (SCRIPTS / "cairn_query" / "__init__.py").read_text()
    # No bare literal in the module
    tree = ast.parse(src)
    v = _DotClaudeLiteralVisitor()
    v.visit(tree)
    assert v.hits == [], (
        f"cairn_query/__init__.py still has Path('.claude/...') literals at {v.hits}"
    )
    assert "project_root" in src, (
        "cairn_query/__init__.py must import/use project_root() for DEFAULT_DB_PATH "
        "and extractor entrypoints"
    )


def test_cairn_query_main_db_path_uses_project_root():
    """scripts/cairn_query/__main__.py:_db_path must derive from project_root()
    when CAIRN_QUERY_DB env override is unset.
    """
    src = (SCRIPTS / "cairn_query" / "__main__.py").read_text()
    tree = ast.parse(src)
    v = _DotClaudeLiteralVisitor()
    v.visit(tree)
    assert v.hits == [], (
        f"cairn_query/__main__.py still has Path('.claude/...') literals at {v.hits}"
    )


def test_feature_extractor_default_dir_uses_project_root():
    """FeatureExtractor's default features_dir must NOT be a hardcoded
    Path('.claude/features') literal. Brief: 'extractor entrypoints (currently
    take no root arg)'.
    """
    src = (SCRIPTS / "cairn_query" / "extractors" / "feature.py").read_text()
    tree = ast.parse(src)
    v = _DotClaudeLiteralVisitor()
    v.visit(tree)
    assert v.hits == [], (
        f"feature.py still hardcodes Path('.claude/...') at {v.hits}; "
        "must accept root or call project_root() internally"
    )


def test_slice_extractor_run_git_passes_cwd():
    """scripts/cairn_query/extractors/slice.py:_run_git currently invokes
    subprocess.run(['git', ...]) without cwd=. Brief: 'bare subprocess.run git
    calls without cwd='. Migration must add cwd= kwarg.
    """
    src = (SCRIPTS / "cairn_query" / "extractors" / "slice.py").read_text()
    tree = ast.parse(src)
    v = _GitSubprocessVisitor()
    v.visit(tree)
    assert v.hits == [], (
        f"slice.py:_run_git still has subprocess.run(['git', ...]) without cwd= "
        f"at lines {v.hits}"
    )


def test_orchestrator_modules_have_no_dotclaude_literals():
    """Brief enumerates orchestrator modules that must be clean."""
    orchestrator = SCRIPTS / "slice_orchestrator"
    targets = ["core.py", "lifecycle.py", "dispatch.py", "telemetry.py"]

    offenders: list[str] = []
    for name in targets:
        f = orchestrator / name
        tree = ast.parse(f.read_text())
        v = _DotClaudeLiteralVisitor()
        v.visit(tree)
        for ln, s in v.hits:
            offenders.append(f"{f.relative_to(CAIRN_ROOT)}:{ln} Path({s!r})")

    assert offenders == [], (
        "orchestrator modules still contain Path('.claude/...') literals:\n  "
        + "\n  ".join(offenders)
    )


@pytest.mark.xfail(strict=True, reason=_MCP_SERVER_XFAIL_REASON)
def test_mcp_server_does_not_use_file_dunder_for_root_inference():
    """mcp_servers/cairn_knowledge/server.py currently builds _REPO_ROOT via
    Path(__file__).resolve().parent.parent.parent for sys.path injection AND
    DB/corpus paths. Per intent's L-017 ban, project-root inference must
    instead route through scripts/_root.project_root().
    """
    src = (MCP / "cairn_knowledge" / "server.py").read_text()
    # The L-017 marker: a parent.parent.parent chain off __file__ that is
    # then used as a project-root surrogate.
    pattern = re.compile(r"Path\(__file__\)\.resolve\(\)\.parent\.parent\.parent")
    assert not pattern.search(src), (
        "mcp_servers/cairn_knowledge/server.py still uses "
        "Path(__file__).resolve().parent.parent.parent for project-root inference. "
        "This is the L-017 trap — replace with project_root()."
    )
    assert "project_root" in src, (
        "mcp_servers/cairn_knowledge/server.py must import/use project_root() "
        "for DB and corpus paths per slice brief."
    )


# ---------------------------------------------------------------------------
# Documentation contract
# ---------------------------------------------------------------------------


def test_operational_reference_documents_claude_project_dir_contract():
    """Intent §Docs: 'docs/operational-reference.md — append "Project-root
    resolution" subsection: contract, precedence, symlink rationale,
    test-exemption.'
    """
    doc = CAIRN_ROOT / "docs" / "operational-reference.md"
    assert doc.exists(), f"docs/operational-reference.md missing at {doc}"
    text = doc.read_text()

    # Subsection heading
    assert re.search(r"^#+\s+Project-root resolution", text, re.MULTILINE), (
        "docs/operational-reference.md missing 'Project-root resolution' "
        "subsection (intent §Docs)"
    )
    # Names the env var
    assert "CLAUDE_PROJECT_DIR" in text, (
        "Project-root resolution subsection must name CLAUDE_PROJECT_DIR"
    )
    # Names the git fallback
    assert "git rev-parse" in text or "rev-parse" in text, (
        "Project-root resolution subsection must document the git rev-parse fallback"
    )
