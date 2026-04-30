"""Path-discipline lint gate — scripts/lint_paths.py.

Invocable as ``python -m lint_paths`` (pyproject.toml puts scripts/ on pythonpath).

Scans ``scripts/`` and ``mcp_servers/`` of the project root (resolved via
CLAUDE_PROJECT_DIR → git rev-parse) and fails on any of:
  - Path(".claude/...") literal outside scripts/_root.py  (intent §Lint gate)
  - Path.cwd() call in scripts/ or mcp_servers/
  - subprocess.run(["git", ...]) without explicit cwd= kwarg

Failure output names file:line and points at scripts/_root.py:project_root.

Exit 0 if clean, non-zero if any violation found.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Root resolution (inline — _root.py may not be importable yet in some
# synthetic test trees; replicate the same precedence chain).
# ---------------------------------------------------------------------------


def _resolve_project_root() -> Path:
    val = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if val:
        return Path(val).resolve()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip()).resolve()
    except subprocess.CalledProcessError as exc:
        print(
            f"lint_paths: cannot resolve project root: {exc}",
            file=sys.stderr,
        )
        sys.exit(2)


# ---------------------------------------------------------------------------
# AST visitors
# ---------------------------------------------------------------------------


def _path_call_string_arg(node: ast.Call) -> str | None:
    """If node is Path("..."), return the string; else None."""
    if not isinstance(node.func, ast.Name) or node.func.id != "Path":
        return None
    if not node.args or not isinstance(node.args[0], ast.Constant):
        return None
    val = node.args[0].value
    return val if isinstance(val, str) else None


class _DotClaudeVisitor(ast.NodeVisitor):
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


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------

_REMEDIATION = "scripts/_root.py:project_root"


def _iter_py_files(root: Path):
    """Yield .py files under scripts/ and mcp_servers/ of root.

    Skips __pycache__ and .slice-system symlink loops.
    """
    for subdir_name in ("scripts", "mcp_servers"):
        subdir = root / subdir_name
        if not subdir.exists():
            continue
        for f in subdir.rglob("*.py"):
            if "__pycache__" in f.parts:
                continue
            if ".slice-system" in f.parts:
                continue
            yield f


def _is_exempt_from_dotclaude(filepath: Path, root: Path) -> bool:
    """scripts/_root.py and anything under tests/ are exempt from .claude ban."""
    try:
        rel = filepath.relative_to(root)
    except ValueError:
        return False
    parts = rel.parts
    # tests/ exemption
    if parts and parts[0] == "tests":
        return True
    # scripts/_root.py exemption
    if rel == Path("scripts") / "_root.py":
        return True
    return False


def _is_exempt_from_cwd_and_git(filepath: Path, root: Path) -> bool:
    """tests/ is exempt from cwd and git-subprocess bans."""
    try:
        rel = filepath.relative_to(root)
    except ValueError:
        return False
    return rel.parts[:1] == ("tests",)


def scan(root: Path) -> list[str]:
    """Scan root for path-discipline violations. Returns list of error strings."""
    errors: list[str] = []

    for filepath in _iter_py_files(root):
        try:
            src = filepath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        try:
            tree = ast.parse(src, filename=str(filepath))
        except SyntaxError:
            continue

        try:
            rel = str(filepath.relative_to(root))
        except ValueError:
            rel = str(filepath)

        # --- .claude literal ban ---
        if not _is_exempt_from_dotclaude(filepath, root):
            v = _DotClaudeVisitor()
            v.visit(tree)
            for ln, s in v.hits:
                errors.append(
                    f"{rel}:{ln}: Path({s!r}) literal — use {_REMEDIATION} instead"
                )

        if not _is_exempt_from_cwd_and_git(filepath, root):
            # --- Path.cwd() ban ---
            cv = _CwdVisitor()
            cv.visit(tree)
            for ln in cv.hits:
                errors.append(f"{rel}:{ln}: Path.cwd() — use {_REMEDIATION} instead")

            # --- git subprocess cwd= ban ---
            gv = _GitSubprocessVisitor()
            gv.visit(tree)
            for ln in gv.hits:
                errors.append(
                    f"{rel}:{ln}: subprocess.run(['git', ...]) missing cwd= — "
                    f"add cwd={_REMEDIATION}()"
                )

    return errors


def main() -> int:
    root = _resolve_project_root()
    errors = scan(root)
    if not errors:
        print("lint_paths: OK — no path-discipline violations found.")
        return 0

    print(
        f"lint_paths: {len(errors)} violation(s) found (remediation: {_REMEDIATION}):",
        file=sys.stderr,
    )
    for e in errors:
        print(f"  {e}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
