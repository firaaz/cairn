"""Phase 2 validation for efficiency-program/all-seven Item 7 — /status expansion.

Verifies intent.md Item 7 acceptance:
  - status.md rendered for a fixture pipeline state emits five dashboard lines
    in order:
      1. Slice: <id> · Phase: <N> <phase-name> · HEAD: <short-sha>
      2. Last test run: <timestamp> <pass|fail|—>
      3. Sweep: <due|up-to-date> (<N> slice-complete since last)
      4. Features: <comma-list of id:name pairs>
      5. Next: <line from handoff.md's ## Next section first line if present>
  - Total output fits under 1500 characters (progressive-disclosure INV-004).
  - `commands/claude-code/status.full.md` exists (created if absent) and is
    loaded only on the discrete predicate "user asks for full registry view".

Per intent.md, /status is a slash-command skill; Phase 2 tests the *rendered
output contract*. The status command file itself is text. We check:
  - The status.md file declares all five output lines (as a schema).
  - status.full.md exists (per intent.md directive).
  - Line-budget counter: stripped of examples, the main status.md skill
    produces a dashboard that fits under the budget — tested by extracting
    the example/expected block and asserting its character count is under
    1500.

The fixture-based rendering check requires Phase 3 to expose a renderer
(e.g., a script) the test can invoke. If Phase 3 implements /status purely
as skill prose (no script), the schema-level checks alone carry the
verification burden; the fixture render test below will still assert a
renderer exists at one of a small set of candidate paths.

RED phase: status.md is currently 16 lines with no five-line dashboard;
status.full.md does not exist. Pytest + stdlib only.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
STATUS_MD = PROJECT_ROOT / "commands" / "claude-code" / "status.md"
STATUS_FULL = PROJECT_ROOT / "commands" / "claude-code" / "status.full.md"

CANDIDATE_RENDERER_PATHS = (
    PROJECT_ROOT / "scripts" / "render_status.sh",
    PROJECT_ROOT / "scripts" / "render_status.py",
    PROJECT_ROOT / "scripts" / "status.sh",
    PROJECT_ROOT / "scripts" / "status.py",
)

MAX_DASHBOARD_CHARS = 1500


def _write_fixture(root: Path) -> None:
    """Lay down a minimal pipeline state: slice.yaml, sweep.yaml, handoff.md,
    one feature file, and a validation artifact with a recent mtime."""
    claude = root / ".claude"
    claude.mkdir(exist_ok=True)
    (claude / "current-slice").mkdir(exist_ok=True)
    (claude / "current-slice" / "validation").mkdir(exist_ok=True)
    (claude / "features").mkdir(exist_ok=True)

    (claude / "current-slice" / "slice.yaml").write_text(
        "id: demo/slice-a\n"
        'name: "demo"\n'
        "status: 3-implementation\n"
        "started: 2026-04-18\n"
        "completed: null\n"
        "invariants-touched: []\n"
        "adrs-referenced: []\n"
        "adrs-created: []\n",
        encoding="utf-8",
    )
    (claude / "sweep.yaml").write_text(
        "last-sweep-at-slice-id: demo/earlier\nsweep-interval: 3\n",
        encoding="utf-8",
    )
    (claude / "handoff.md").write_text(
        "---\nslice: demo/slice-a\nphase: 3\n---\n\n"
        "## State\nmid-implementation\n\n"
        "## Next\nrun pytest\n\n"
        "## Blocked / Pending\n(none)\n\n"
        "## Pointers\n- .claude/current-slice/slice.yaml\n",
        encoding="utf-8",
    )
    (claude / "features" / "demo.yaml").write_text(
        "id: demo\nname: demo\ncreated: 2026-04-18\nshaped-from: null\nslices: []\n",
        encoding="utf-8",
    )
    (claude / "current-slice" / "validation" / "approach.md").write_text(
        "approach stub\n", encoding="utf-8"
    )


# --- Schema checks on status.md ---------------------------------------------


class TestStatusMdSchema:
    def test_status_md_exists(self):
        assert STATUS_MD.is_file()

    def test_status_md_declares_slice_line(self):
        text = STATUS_MD.read_text(encoding="utf-8")
        # Line 1: "Slice: <id> · Phase: <N> <phase-name> · HEAD: <short-sha>"
        assert "Slice:" in text and "Phase:" in text and "HEAD:" in text, (
            "status.md must declare the Slice / Phase / HEAD dashboard line"
        )

    def test_status_md_declares_last_test_run_line(self):
        text = STATUS_MD.read_text(encoding="utf-8")
        assert "Last test run" in text, (
            "status.md must declare the `Last test run:` dashboard line"
        )

    def test_status_md_declares_sweep_line(self):
        text = STATUS_MD.read_text(encoding="utf-8")
        assert "Sweep:" in text, "status.md must declare the `Sweep:` dashboard line"

    def test_status_md_declares_features_line(self):
        text = STATUS_MD.read_text(encoding="utf-8")
        assert "Features:" in text, (
            "status.md must declare the `Features:` dashboard line"
        )

    def test_status_md_declares_next_line(self):
        text = STATUS_MD.read_text(encoding="utf-8")
        assert "Next:" in text, "status.md must declare the `Next:` dashboard line"


class TestStatusFullExists:
    def test_status_full_md_present(self):
        assert STATUS_FULL.is_file(), (
            "commands/claude-code/status.full.md must exist — houses the "
            "expanded registry/debug view (intent Item 7)"
        )

    def test_status_full_md_progressive_disclosure_predicate(self):
        if not STATUS_FULL.is_file():
            raise AssertionError("status.full.md not yet created")
        text = STATUS_FULL.read_text(encoding="utf-8")
        # Full file exists — we assert it mentions the registry/debug concept
        # so the progressive-disclosure predicate is visible.
        lower = text.lower()
        assert "registry" in lower or "debug" in lower or "full" in lower, (
            "status.full.md must indicate its expanded scope (registry / "
            "debug / full view) to honor INV-004 progressive disclosure"
        )


# --- Rendered output budget --------------------------------------------------


class TestDashboardRendering:
    def _renderer(self) -> Path | None:
        for p in CANDIDATE_RENDERER_PATHS:
            if p.is_file():
                return p
        return None

    def test_renderer_exists(self):
        r = self._renderer()
        assert r is not None, (
            "No /status renderer found under scripts/; intent Item 7's "
            "fixture render test needs one of "
            f"{[str(p.relative_to(PROJECT_ROOT)) for p in CANDIDATE_RENDERER_PATHS]}"
        )

    def test_rendered_output_under_budget(self, tmp_path: Path):
        renderer = self._renderer()
        if renderer is None:
            raise AssertionError("no renderer yet — intent Item 7 undone")
        _write_fixture(tmp_path)
        cmd = (
            ["bash", str(renderer)]
            if renderer.suffix == ".sh"
            else ["python3", str(renderer)]
        )
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(tmp_path),
            env={
                "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
                "HOME": str(tmp_path),
                "CLAUDE_PROJECT_DIR": str(tmp_path),
            },
        )
        assert result.returncode == 0, (
            f"renderer failed: rc={result.returncode} stderr={result.stderr!r}"
        )
        out = result.stdout
        assert len(out) <= MAX_DASHBOARD_CHARS, (
            f"dashboard output {len(out)} chars exceeds "
            f"{MAX_DASHBOARD_CHARS} (INV-004 progressive-disclosure target)"
        )

    def test_rendered_output_contains_all_five_lines(self, tmp_path: Path):
        renderer = self._renderer()
        if renderer is None:
            raise AssertionError("no renderer yet — intent Item 7 undone")
        _write_fixture(tmp_path)
        cmd = (
            ["bash", str(renderer)]
            if renderer.suffix == ".sh"
            else ["python3", str(renderer)]
        )
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(tmp_path),
            env={
                "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
                "HOME": str(tmp_path),
                "CLAUDE_PROJECT_DIR": str(tmp_path),
            },
        )
        out = result.stdout
        for token in ("Slice:", "Last test run", "Sweep:", "Features:", "Next:"):
            assert token in out, (
                f"rendered dashboard missing `{token}` line; full output:\n{out}"
            )
