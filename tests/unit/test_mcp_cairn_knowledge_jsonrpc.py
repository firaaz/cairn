"""Phase 2 RED — compression/lever-Y-mcp-substrate-fixup §S1 + §S2 + §S5.

Asserts the cairn-knowledge MCP server ships a real JSON-RPC 2.0 stdio
dispatcher (not the boot-only stub) per intent.md §S1, ADR
``cairn-substrate-and-fastmcp`` D1/D6, and INV-010.

Round-trip black-box coverage: spawn ``python -m mcp_servers.cairn_knowledge``,
write JSON-RPC requests to stdin, read newline-delimited JSON responses from
stdout, assert protocol-level behaviour.

Also covers:
  - §S2 ``fastmcp`` is a project dependency (declared in pyproject.toml +
    importable inside the project venv).
  - §S5 INV-010 prose in ``docs/ARCHITECTURE.md`` names Grep and Glob in
    the deny surface alongside Read and Bash.

Expected at Phase 2: FAILS — the existing ``server.py:_stdin_reader`` stub
discards stdin, ``fastmcp`` is absent from pyproject dependencies, and
INV-010 prose still reads "Direct Read/Bash access ...".
"""

from __future__ import annotations

import json
import os
import re
import select
import subprocess
import sys
import time
import tomllib
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent

# Repo root must be on sys.path so the `mcp_servers` package is importable.
if str(CAIRN_ROOT) not in sys.path:
    sys.path.insert(0, str(CAIRN_ROOT))

EXPECTED_TOOL_NAMES = {"lookup", "search", "path_bindings", "cypher"}

# Generous boot timeout: subprocess eagerly rebuilds the kuzu corpus before
# answering JSON-RPC. Override via env for slow CI hosts (CLAUDE.md guidance).
_BOOT_TIMEOUT = float(os.environ.get("CAIRN_MCP_BOOT_TIMEOUT_SEC", "45"))
_LINE_TIMEOUT = float(os.environ.get("CAIRN_MCP_LINE_TIMEOUT_SEC", "15"))


# ---------------------------------------------------------------------------
# JSON-RPC subprocess helpers
# ---------------------------------------------------------------------------


def _spawn_server(env_extra: dict | None = None) -> subprocess.Popen:
    env = {
        **{k: v for k, v in os.environ.items() if k != "AGENT_ROLE"},
        "AGENT_ENVELOPE": '{"paths":[],"cairn_query_snapshot":"HEAD"}',
        "PYTHONUNBUFFERED": "1",
    }
    if env_extra:
        env.update(env_extra)
    return subprocess.Popen(
        [sys.executable, "-m", "mcp_servers.cairn_knowledge"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=CAIRN_ROOT,
        env=env,
        text=True,
        bufsize=1,
    )


def _send(proc: subprocess.Popen, payload: dict) -> None:
    """Write a JSON-RPC request as a single newline-terminated JSON line."""
    assert proc.stdin is not None, "subprocess stdin not piped"
    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()


def _read_response(proc: subprocess.Popen, timeout: float) -> dict:
    """Read one line from stdout within ``timeout`` and parse as JSON.

    Uses select() so we don't deadlock if the server crashes mid-handshake.
    """
    assert proc.stdout is not None, "subprocess stdout not piped"
    deadline = time.monotonic() + timeout
    buf = ""
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            stderr = ""
            try:
                if proc.stderr is not None:
                    # Drain whatever stderr we can without blocking.
                    rfd, _, _ = select.select([proc.stderr], [], [], 0)
                    if rfd:
                        stderr = proc.stderr.read() or ""
            except Exception:  # noqa: BLE001 — diagnostic best-effort
                pass
            pytest.fail(
                f"timeout waiting {timeout}s for JSON-RPC response; "
                f"buf={buf!r} stderr={stderr!r}"
            )
        rfd, _, _ = select.select([proc.stdout], [], [], min(remaining, 0.5))
        if not rfd:
            if proc.poll() is not None:
                stderr = proc.stderr.read() if proc.stderr else ""
                pytest.fail(
                    f"server exited rc={proc.returncode} before responding; "
                    f"stderr={stderr!r}"
                )
            continue
        chunk = proc.stdout.readline()
        if not chunk:
            # EOF; surface stderr to aid diagnosis.
            stderr = proc.stderr.read() if proc.stderr else ""
            pytest.fail(f"stdout EOF before response; stderr={stderr!r}")
        buf += chunk
        # Try parsing a single JSON object; the server may legitimately
        # emit multiple newline-delimited responses but Phase 2 expects
        # one-per-request.
        try:
            return json.loads(buf)
        except json.JSONDecodeError:
            # Continue reading — partial line.
            continue


def _terminate(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        try:
            proc.stdin.close()  # type: ignore[union-attr]
        except Exception:  # noqa: BLE001
            pass
        try:
            proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2.0)


# ---------------------------------------------------------------------------
# §S2 — fastmcp standing dep
# ---------------------------------------------------------------------------


def test_s2_fastmcp_listed_in_pyproject_dependencies():
    """intent §S2 — pyproject [project].dependencies includes fastmcp."""
    pyproject = CAIRN_ROOT / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text())
    deps = data.get("project", {}).get("dependencies", [])
    names = {re.split(r"[<>=!~ ]", d, 1)[0].strip().lower() for d in deps}
    assert "fastmcp" in names, (
        f"intent §S2 / ADR D1 — fastmcp missing from pyproject [project].dependencies; "
        f"current: {sorted(names)}"
    )


def test_s2_fastmcp_dep_has_version_constraint():
    """ADR D1 — Slice 2 pins FastMCP to a minor version (narrow-pin)."""
    pyproject = CAIRN_ROOT / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text())
    deps = data.get("project", {}).get("dependencies", [])
    for d in deps:
        if re.split(r"[<>=!~ ]", d, 1)[0].strip().lower() == "fastmcp":
            constraint = d[len("fastmcp") :].strip()
            assert constraint, (
                f"intent §S2 / ADR D1 — fastmcp must have a version constraint "
                f"(narrow-pin per D1 risk register); got bare {d!r}"
            )
            return
    pytest.fail(
        "fastmcp not present — see test_s2_fastmcp_listed_in_pyproject_dependencies"
    )


def test_s2_fastmcp_importable_in_project_venv():
    """Closes-when #1 — `python -c 'import fastmcp'` exits 0 in .venv.

    Skips with a clear marker only if the test is being run outside any
    Python with site-packages (unlikely); otherwise asserts.
    """
    proc = subprocess.run(
        [sys.executable, "-c", "import fastmcp"],
        capture_output=True,
        text=True,
        cwd=CAIRN_ROOT,
    )
    assert proc.returncode == 0, (
        f"intent §S2 / closes-when #1 — `import fastmcp` failed; "
        f"stderr={proc.stderr!r}. Phase 3 must add fastmcp to pyproject "
        f"AND run `uv sync` so the lockfile + venv reflect the new dep."
    )


def test_s2_existing_standing_deps_preserved():
    """ADR D1 — pyyaml, pydantic, kuzu, mistune, typer remain in standing set."""
    pyproject = CAIRN_ROOT / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text())
    deps = data.get("project", {}).get("dependencies", [])
    names = {re.split(r"[<>=!~ ]", d, 1)[0].strip().lower() for d in deps}
    for required in ("pyyaml", "pydantic", "kuzu", "mistune", "typer"):
        assert required in names, (
            f"intent §S2 boundary — pre-existing standing dep {required!r} "
            f"removed; ADR D1 requires the five v1 deps remain unchanged. "
            f"current: {sorted(names)}"
        )


# ---------------------------------------------------------------------------
# §S1 — JSON-RPC dispatcher round-trip
# ---------------------------------------------------------------------------


def test_s1_dispatcher_replaces_stub_in_server_source():
    """intent §S1 — ``_stdin_reader`` stub that 'discards input' is gone.

    Black-box source presence assertion: the prior stub's defining string
    ``discards input`` (server.py:67) and bare keep-alive ``time.sleep(1)``
    polling loop must not survive Phase 3.
    """
    src = (CAIRN_ROOT / "mcp_servers" / "cairn_knowledge" / "server.py").read_text()
    assert "discards input" not in src, (
        "intent §S1 — server.py still contains the stub's 'discards input' "
        "marker; the JSON-RPC dispatcher has not replaced the stub."
    )
    # The keep-alive ``while True: time.sleep(1)`` polling loop must give
    # way to a blocking dispatcher loop (intent §S1 termination semantics).
    assert not re.search(r"while\s+True\s*:\s*\n\s*time\.sleep\(1\)", src), (
        "intent §S1 — the keep-alive `while True: time.sleep(1)` loop must "
        "be replaced by a blocking JSON-RPC dispatcher (stdin.read-driven)."
    )


def test_s1_r1_initialize_handshake():
    """R1 — JSON-RPC `initialize` returns protocolVersion + capabilities + serverInfo."""
    proc = _spawn_server()
    try:
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "phase-2-skeptic", "version": "0"},
            },
        }
        _send(proc, req)
        resp = _read_response(proc, timeout=_BOOT_TIMEOUT)
        assert resp.get("jsonrpc") == "2.0", f"missing jsonrpc=2.0: {resp!r}"
        assert resp.get("id") == 1, f"id mismatch: {resp!r}"
        assert "error" not in resp, f"initialize errored: {resp!r}"
        result = resp.get("result")
        assert isinstance(result, dict), f"missing result dict: {resp!r}"
        assert "protocolVersion" in result, f"missing protocolVersion: {result!r}"
        assert "capabilities" in result, f"missing capabilities: {result!r}"
        server_info = result.get("serverInfo") or {}
        assert server_info.get("name") == "cairn-knowledge", (
            f"intent §S1 — serverInfo.name must be 'cairn-knowledge'; got {server_info!r}"
        )
    finally:
        _terminate(proc)


def test_s1_r2_tools_list_returns_four_tools():
    """R2 — `tools/list` returns exactly {lookup, search, path_bindings, cypher}."""
    proc = _spawn_server()
    try:
        _send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "phase-2-skeptic", "version": "0"},
                },
            },
        )
        _read_response(proc, timeout=_BOOT_TIMEOUT)

        _send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        resp = _read_response(proc, timeout=_LINE_TIMEOUT)
        assert resp.get("id") == 2, f"id mismatch: {resp!r}"
        assert "error" not in resp, f"tools/list errored: {resp!r}"
        result = resp.get("result") or {}
        tools = result.get("tools")
        assert isinstance(tools, list), f"result.tools must be a list: {result!r}"
        names = {
            t.get("name", "")
            for t in tools
            if isinstance(t, dict) and isinstance(t.get("name"), str)
        }
        assert names == EXPECTED_TOOL_NAMES, (
            f"intent §S1 / INV-010 — tools must be exactly "
            f"{sorted(EXPECTED_TOOL_NAMES)}; got {sorted(names)!r}"
        )
    finally:
        _terminate(proc)


def test_s1_r3_tools_call_routes_to_implementation():
    """R3 — `tools/call` for `lookup` with a known id returns the record."""
    proc = _spawn_server()
    try:
        _send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "phase-2-skeptic", "version": "0"},
                },
            },
        )
        _read_response(proc, timeout=_BOOT_TIMEOUT)

        _send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "lookup",
                    "arguments": {"entity_type": "invariant", "id": "INV-010"},
                },
            },
        )
        resp = _read_response(proc, timeout=_LINE_TIMEOUT)
        assert resp.get("id") == 2, f"id mismatch: {resp!r}"
        assert "error" not in resp, (
            f"intent §S1 R3 — known-id lookup must NOT error; got {resp!r}"
        )
        result = resp.get("result")
        assert result is not None, f"missing result: {resp!r}"
        # The tools/call result is opaque per MCP (content array with text or
        # structured items). We only assert the entity id appears somewhere
        # in the serialized response — the contract is "the record was returned".
        blob = json.dumps(result)
        assert "INV-010" in blob, (
            f"intent §S1 R3 — response must include INV-010 record; got {result!r}"
        )
    finally:
        _terminate(proc)


def test_s1_r4_tools_call_unknown_id_surfaces_jsonrpc_error():
    """R4 — KeyError from `lookup` becomes a JSON-RPC error, not a process crash."""
    proc = _spawn_server()
    try:
        _send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "phase-2-skeptic", "version": "0"},
                },
            },
        )
        _read_response(proc, timeout=_BOOT_TIMEOUT)

        _send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "lookup",
                    "arguments": {
                        "entity_type": "invariant",
                        "id": "INV-NONEXISTENT-999",
                    },
                },
            },
        )
        resp = _read_response(proc, timeout=_LINE_TIMEOUT)
        assert resp.get("id") == 2, f"id mismatch: {resp!r}"
        # Either a top-level JSON-RPC error object, or an in-result error
        # marker (MCP allows tools/call results with isError=true). Either
        # is acceptable per intent §S1: "valid JSON-RPC error response".
        has_top_level_error = "error" in resp and isinstance(resp["error"], dict)
        result = resp.get("result")
        has_inline_error = isinstance(result, dict) and bool(result.get("isError"))
        assert has_top_level_error or has_inline_error, (
            f"intent §S1 R4 — KeyError must surface as JSON-RPC error "
            f"(top-level error object or result.isError=true); got {resp!r}"
        )
        # The server must not have crashed.
        assert proc.poll() is None, (
            "intent §S1 R4 — KeyError must NOT crash the dispatcher; "
            f"subprocess exited rc={proc.returncode}"
        )
    finally:
        _terminate(proc)


def test_s1_r5_stdin_eof_terminates_cleanly():
    """R5 — closing stdin terminates the subprocess cleanly (intent §S1)."""
    proc = _spawn_server()
    try:
        _send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "phase-2-skeptic", "version": "0"},
                },
            },
        )
        _read_response(proc, timeout=_BOOT_TIMEOUT)
        # Close stdin → dispatcher's blocking read returns EOF → exit.
        assert proc.stdin is not None
        proc.stdin.close()
        try:
            rc = proc.wait(timeout=10.0)
        except subprocess.TimeoutExpired:
            stderr = proc.stderr.read() if proc.stderr else ""
            proc.terminate()
            pytest.fail(
                f"intent §S1 — server did not exit within 10s of stdin EOF "
                f"(termination semantics); stderr={stderr!r}"
            )
        # Accept rc==0 (clean exit) or signal-equivalent negative rc on POSIX.
        assert rc == 0 or rc < 0, (
            f"intent §S1 — clean termination on stdin EOF expected; got rc={rc}"
        )
    finally:
        _terminate(proc)


def test_s1_snapshot_pinning_hook_preserved():
    """intent §S1 — `AGENT_ENVELOPE.cairn_query_snapshot` plumbing remains.

    Source-text presence (Phase 2 boundary): server.py reads AGENT_ENVELOPE
    and forwards `snapshot_id` to `rebuild_from_sources`. Behaviour is
    Phase-3 implementation detail; presence is verifiable from source.
    """
    src = (CAIRN_ROOT / "mcp_servers" / "cairn_knowledge" / "server.py").read_text()
    assert "AGENT_ENVELOPE" in src, "intent §S1 — server.py must consume AGENT_ENVELOPE"
    assert "cairn_query_snapshot" in src, (
        "intent §S1 — server.py must read cairn_query_snapshot from envelope"
    )
    assert "rebuild_from_sources" in src, (
        "intent §S1 — server.py must call rebuild_from_sources for snapshot pinning"
    )


def test_s1_dispatcher_uses_fastmcp_substrate():
    """intent §S1 / ADR D1 — server uses the `fastmcp` library.

    Phase 3 may import fastmcp under any alias, but the import statement
    naming the library must appear in server.py source. If Phase 3 chose a
    different library, intent §S1 mandates RAISE_ISSUE rather than silent
    substitution; this test enforces that constraint at the source level.
    """
    src = (CAIRN_ROOT / "mcp_servers" / "cairn_knowledge" / "server.py").read_text()
    assert re.search(r"\bfastmcp\b", src), (
        "intent §S1 / ADR D1 — server.py must use the fastmcp library "
        "(named by D1). Substitution requires an ADR amendment via /decision."
    )


# ---------------------------------------------------------------------------
# §S5 — INV-010 prose names Grep + Glob
# ---------------------------------------------------------------------------


def _inv010_prose() -> str:
    arch = (CAIRN_ROOT / "docs" / "ARCHITECTURE.md").read_text()
    # Locate INV-010 paragraph: from the bold "**INV-010**" marker up to the
    # next blank line or the invariant-check fence.
    m = re.search(r"\*\*INV-010\*\*[^\n]*\n(?:.*\n)*?(?=\n```invariant-check)", arch)
    assert m, "could not locate INV-010 prose block in ARCHITECTURE.md"
    return m.group(0)


def test_s5_inv010_prose_names_grep_in_deny_surface():
    """intent §S5 — INV-010 prose names Grep alongside Read/Bash."""
    prose = _inv010_prose()
    assert re.search(r"\bGrep\b", prose), (
        "intent §S5 — INV-010 prose must name `Grep` in the deny surface; "
        f"current prose: {prose!r}"
    )


def test_s5_inv010_prose_names_glob_in_deny_surface():
    """intent §S5 — INV-010 prose names Glob alongside Read/Bash."""
    prose = _inv010_prose()
    assert re.search(r"\bGlob\b", prose), (
        "intent §S5 — INV-010 prose must name `Glob` in the deny surface; "
        f"current prose: {prose!r}"
    )


def test_s5_inv010_invariant_check_target_unchanged():
    """intent §S5 boundary — invariant-check `target:` block stays at
    `ROLE_DENY_READ` literal grep (the constant's name does not change).
    """
    arch = (CAIRN_ROOT / "docs" / "ARCHITECTURE.md").read_text()
    m = re.search(
        r"```invariant-check INV-010\n(?:.*\n)*?```",
        arch,
    )
    assert m, "INV-010 invariant-check fence missing"
    block = m.group(0)
    assert 'pattern: "ROLE_DENY_READ"' in block, (
        "intent §S5 boundary — invariant-check pattern must remain "
        "`ROLE_DENY_READ` (slice does NOT touch this block)"
    )
    assert 'target: "checks/role_guard.py"' in block, (
        "intent §S5 boundary — invariant-check target must remain "
        "`checks/role_guard.py` (slice does NOT touch this block)"
    )
