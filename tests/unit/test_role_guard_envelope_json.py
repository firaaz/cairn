"""Phase 2 RED — compression/slice-2-state-machine §B7.

`checks/role_guard.py::_envelope_patterns(raw)` MUST parse
`AGENT_ENVELOPE` via `json.loads` returning `list[str]`. On
`JSONDecodeError`, fall back to the legacy `:`-split path with one stderr
warning line (back-compat). Patterns containing `:` (Windows paths,
regex anchors) MUST survive round-trip.

Expected at Phase 2: FAILS — current _envelope_patterns uses colon-split.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = CAIRN_ROOT / "checks" / "role_guard.py"


def _run_hook(tool_input: dict, role: str, envelope: str) -> tuple[int, str]:
    env = {
        k: v for k, v in os.environ.items() if k not in {"AGENT_ROLE", "AGENT_ENVELOPE"}
    }
    env["AGENT_ROLE"] = role
    env["AGENT_ENVELOPE"] = envelope
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(tool_input),
        text=True,
        capture_output=True,
        env=env,
        cwd=CAIRN_ROOT,
    )
    return proc.returncode, proc.stderr


def test_b7_json_envelope_with_colon_in_path_allows_write():
    envelope = json.dumps(["scripts/a:b.py", "tests/c.py"])
    code, stderr = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "scripts/a:b.py"}},
        role="phase-3-implementer",
        envelope=envelope,
    )
    assert code == 0, (
        f"JSON envelope with colon path must allow write; stderr={stderr!r}"
    )


def test_b7_json_envelope_non_matching_denies():
    envelope = json.dumps(["scripts/other.py"])
    code, _ = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "scripts/a:b.py"}},
        role="phase-3-implementer",
        envelope=envelope,
    )
    assert code == 1


def test_b7_legacy_colon_split_envelope_still_works_with_warning():
    # Legacy format: colon-separated list of regex patterns. Must succeed
    # (back-compat) and emit exactly one stderr warning.
    legacy = r"^scripts/a\.py$:^tests/b\.py$"
    code, stderr = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "scripts/a.py"}},
        role="phase-3-implementer",
        envelope=legacy,
    )
    assert code == 0, (
        f"legacy colon-separated envelope must still allow matching writes; "
        f"stderr={stderr!r}"
    )
    warning_lines = [ln for ln in stderr.splitlines() if "legacy" in ln.lower()]
    assert len(warning_lines) == 1, (
        f"expected exactly one legacy-format warning; got {warning_lines!r}"
    )
