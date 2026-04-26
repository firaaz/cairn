"""RED tests — typer CLI smoke tests for `python -m cairn_query`.

Validates the CLI exposes the 10 commands declared in the plan, that
`rebuild`/`stats`/`show`/`path-bindings` round-trip against a tmp-path db
selected via the CAIRN_QUERY_DB env var.
"""

from __future__ import annotations

from typer.testing import CliRunner

from cairn_query.__main__ import app


runner = CliRunner()


def test_cli_help_lists_commands():
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0
    for cmd in [
        "show",
        "path-bindings",
        "graph",
        "supersedes",
        "slices",
        "cypher",
        "dump",
        "stats",
        "rebuild",
        "validate",
    ]:
        assert cmd in r.output


def test_cli_stats_runs(tmp_path, monkeypatch):
    monkeypatch.setenv("CAIRN_QUERY_DB", str(tmp_path / "idx.kz"))
    r = runner.invoke(app, ["rebuild"])
    assert r.exit_code == 0
    r = runner.invoke(app, ["stats"])
    assert r.exit_code == 0
    assert "Invariant" in r.output


def test_cli_show_lookup(tmp_path, monkeypatch):
    monkeypatch.setenv("CAIRN_QUERY_DB", str(tmp_path / "idx.kz"))
    runner.invoke(app, ["rebuild"])
    r = runner.invoke(app, ["show", "invariant", "INV-008"])
    assert r.exit_code == 0
    assert "INV-008" in r.output


def test_cli_path_bindings(tmp_path, monkeypatch):
    monkeypatch.setenv("CAIRN_QUERY_DB", str(tmp_path / "idx.kz"))
    runner.invoke(app, ["rebuild"])
    r = runner.invoke(app, ["path-bindings", "docs/ARCHITECTURE.md"])
    assert r.exit_code == 0
    assert "INV-" in r.output
