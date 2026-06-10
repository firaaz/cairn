"""Cairn post-install validator.

Two stages:

1. Warn-only dependency probes for `jq` (reversibility-guard.sh,
   reality-check.sh) and `ruff` (reality-check.sh). Missing deps are
   non-fatal — the affected hooks just no-op with a stderr warning of
   their own.
2. Positive end-to-end envelope-enforcement self-test (load-bearing per
   ADR D5 / Pre-mortem Scenario 1). Writes a tmp `mode: operator`
   envelope under `CLAUDE_PROJECT_DIR`, invokes `role_guard.py` against
   an out-of-envelope path, asserts the deny lands. Silent-pass is
   FATAL: a green dep-check that doesn't exercise enforcement is
   theatre.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path


DEP_OWNERS: dict[str, str] = {
    "jq": "reversibility-guard.sh / reality-check.sh",
    "ruff": "reality-check.sh",
}


def check_dep(name: str) -> bool:
    if shutil.which(name) is not None:
        return True
    owner = DEP_OWNERS.get(name, "hook")
    print(
        f"WARN: {name} not found on PATH; {owner} hooks will no-op",
        file=sys.stderr,
    )
    return False


def _plugin_root() -> Path:
    env_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env_root:
        return Path(env_root)
    return Path(__file__).resolve().parent.parent


def _role_guard_path(plugin_root: Path) -> Path:
    return plugin_root / "checks" / "role_guard.py"


def check_envelope_enforcement(project_dir: Path) -> bool:
    """Write a sample operator envelope under project_dir and assert that
    role_guard.py denies an out-of-envelope write. Returns True iff the
    enforcement deny landed (rc=2 blocking, non-empty stderr)."""
    plugin_root = _plugin_root()
    role_guard = _role_guard_path(plugin_root)
    if not role_guard.is_file():
        print(
            f"role_guard.py not found at {role_guard}; cannot validate enforcement",
            file=sys.stderr,
        )
        return False

    claude = project_dir / ".claude"
    claude.mkdir(parents=True, exist_ok=True)
    envelope = claude / "active-envelope.yaml"
    envelope.write_text(
        textwrap.dedent(
            """\
            mode: operator
            paths:
              - ^docs/
            """
        )
    )

    tool_input = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "scripts/foo.py",
            "old_string": "x",
            "new_string": "y",
        },
    }
    env = dict(os.environ)
    env.pop("AGENT_ROLE", None)
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)

    try:
        proc = subprocess.run(
            [sys.executable, str(role_guard)],
            input=json.dumps(tool_input),
            text=True,
            capture_output=True,
            env=env,
        )
    finally:
        try:
            envelope.unlink()
        except OSError:
            pass

    return proc.returncode == 2 and bool((proc.stderr or "").strip())


def main() -> int:
    check_dep("jq")
    check_dep("ruff")

    with tempfile.TemporaryDirectory() as td:
        project_dir = Path(td) / "self-test"
        project_dir.mkdir(parents=True)
        ok = check_envelope_enforcement(project_dir)
    if not ok:
        print(
            "FATAL: envelope enforcement self-test failed — envelope "
            "enforcement did not deny out-of-envelope write; installation "
            "is not safe",
            file=sys.stderr,
        )
        return 1
    return 0


def _entry() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    _entry()
