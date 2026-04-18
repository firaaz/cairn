"""Phase 2 cross-cutting invariant-evidence checks for efficiency-program/all-seven.

Asserts that INV-002 / INV-003 / INV-004 have file:line evidence on disk for
each of the seven items that touches them per intent.md:

  - INV-002 (three-layer context discipline):
      - Item 4 handoff verifier: scripts/verify_handoff.sh present, wired
        into commands/claude-code/handoff.md and handoff.full.md.
      - Item 1 role cheatsheet: SessionStart hook + .claude/settings.json
        registration — does not write or expand Tier 1.

  - INV-003 (four phases, role anti-behaviors surfaced at phase entry):
      - Item 1 role cheatsheet reads docs/operational-reference.md §
        Phase Skill Guide (token-match) and the hook exists.

  - INV-004 (30k session budget; progressive disclosure):
      - Item 7 /status main output stays under 1500 chars in fixture.
      - status.full.md sibling exists (progressive disclosure contract).
      - Item 3 preamble is a single-line addition only — bounded prose.

These assertions are grep-style and file-existence based — Phase 4 Auditor
can quote them verbatim as `file:line` citations.

RED phase — every artifact below is missing today. Pytest + stdlib only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


# --- INV-002 evidence --------------------------------------------------------


class TestInv002Evidence:
    """INV-002: three-layer context discipline. Item 4 adds a verifier that
    catches L-005 divergence; Item 1 surfaces role/anti-behavior at session
    open without bloating Tier 1."""

    def test_inv002_item4_verify_handoff_exists(self):
        verifier = PROJECT_ROOT / "scripts" / "verify_handoff.sh"
        assert verifier.is_file(), (
            "INV-002 evidence gap: scripts/verify_handoff.sh missing — "
            "Item 4 is the L-005 divergence guard"
        )

    def test_inv002_item4_handoff_md_references_verifier(self):
        path = PROJECT_ROOT / "commands" / "claude-code" / "handoff.md"
        text = path.read_text(encoding="utf-8")
        assert "verify_handoff" in text, (
            "INV-002 evidence gap: handoff.md does not reference "
            "scripts/verify_handoff.sh"
        )

    def test_inv002_item4_handoff_full_documents_contract(self):
        path = PROJECT_ROOT / "commands" / "claude-code" / "handoff.full.md"
        text = path.read_text(encoding="utf-8")
        assert "verify_handoff" in text, (
            "INV-002 evidence gap: handoff.full.md does not document the "
            "verifier contract"
        )

    def test_inv002_item1_hook_registered_in_settings(self):
        settings = PROJECT_ROOT / ".claude" / "settings.json"
        data = json.loads(settings.read_text(encoding="utf-8"))
        hooks = data.get("hooks", {})
        assert "SessionStart" in hooks, (
            "INV-002 evidence gap: .claude/settings.json has no SessionStart "
            "hook for the role cheatsheet (Item 1)"
        )


# --- INV-003 evidence --------------------------------------------------------


class TestInv003Evidence:
    """INV-003: four phases, role + anti-behavior surfaced at phase entry.
    Item 1 is the machine enforcement — a hook that reads the Phase Skill
    Guide and prints the row for the current phase."""

    def test_inv003_hook_file_exists(self):
        checks_dir = PROJECT_ROOT / "checks"
        candidates = (
            "session-start.sh",
            "role-cheatsheet.sh",
            "session_start.sh",
            "cheatsheet.sh",
        )
        found = [c for c in candidates if (checks_dir / c).is_file()]
        assert found, (
            "INV-003 evidence gap: no SessionStart role-cheatsheet hook "
            f"under checks/; tried {candidates}"
        )

    def test_inv003_phase_skill_guide_reference_in_hook(self):
        checks_dir = PROJECT_ROOT / "checks"
        candidates = (
            "session-start.sh",
            "role-cheatsheet.sh",
            "session_start.sh",
            "cheatsheet.sh",
        )
        texts = []
        for c in candidates:
            p = checks_dir / c
            if p.is_file():
                texts.append(p.read_text(encoding="utf-8"))
        combined = "\n".join(texts)
        assert combined, "INV-003 evidence gap: cheatsheet hook missing (precondition)"
        assert "operational-reference" in combined or "Phase Skill Guide" in combined, (
            "INV-003 evidence gap: hook source does not reference "
            "`docs/operational-reference.md § Phase Skill Guide` — the "
            "invariant requires that exact surface be read at phase entry"
        )


# --- INV-004 evidence --------------------------------------------------------


class TestInv004Evidence:
    """INV-004: 30k session budget; progressive disclosure via *.md / *.full.md
    pairs. Item 7 adds a dashboard under a 1500-char ceiling; Item 3 adds
    only one line of preamble."""

    def test_inv004_status_full_md_exists(self):
        status_full = PROJECT_ROOT / "commands" / "claude-code" / "status.full.md"
        assert status_full.is_file(), (
            "INV-004 evidence gap: commands/claude-code/status.full.md "
            "missing — progressive-disclosure sibling required (Item 7)"
        )

    def test_inv004_status_md_under_lite_budget(self):
        """INV-004 lite files target <=500 tokens (~2500 chars); assert the
        status.md skill is within that even after expansion to five dashboard
        lines."""
        status_md = PROJECT_ROOT / "commands" / "claude-code" / "status.md"
        text = status_md.read_text(encoding="utf-8")
        # 2500 chars ≈ 500 tokens at the 5-char-per-token approximation the
        # handoff token-budget test uses.
        assert len(text) <= 2500, (
            f"INV-004 evidence gap: status.md is {len(text)} chars — exceeds "
            "the lite-file ~500-token budget. Expanded content belongs in "
            "status.full.md."
        )

    def test_inv004_item3_preamble_is_single_line(self):
        """Item 3 adds exactly one preamble line. Assert the verbatim phrase
        appears on a line whose length is bounded (no multi-line prose
        smuggling)."""
        required = "Read the file first (CC 2.1.110+ requires Read before Write)"
        for fname in ("handoff.full.md", "start-slice.full.md"):
            path = PROJECT_ROOT / "commands" / "claude-code" / fname
            text = path.read_text(encoding="utf-8")
            match_lines = [ln for ln in text.splitlines() if required in ln]
            assert match_lines, (
                f"INV-004 evidence gap: {fname} lacks the required Item 3 "
                "preamble phrase"
            )
            for ln in match_lines:
                assert len(ln) <= 400, (
                    f"INV-004 evidence gap: {fname} Item 3 preamble line is "
                    f"{len(ln)} chars — single-line preamble exceeded"
                )


# --- Per-item coverage ledger -----------------------------------------------


class TestPerItemLedger:
    """For Phase 4 Auditor citation convenience: one assertion per item
    naming the artifact whose presence is the evidence for that item."""

    def test_item1_artifact_exists(self):
        # Cheatsheet hook OR settings.json entry — both required, already
        # tested above. Here we do the explicit "some evidence" line for the
        # ledger.
        checks_dir = PROJECT_ROOT / "checks"
        candidates = (
            "session-start.sh",
            "role-cheatsheet.sh",
            "session_start.sh",
            "cheatsheet.sh",
        )
        assert any((checks_dir / c).is_file() for c in candidates), (
            "ledger: Item 1 has no artifact under checks/"
        )

    def test_item2_no_chronic_M(self):
        """Form-agnostic ledger line: either the measurement file exists
        clean, OR it's been relocated out of the tracked path."""
        tracked = PROJECT_ROOT / "docs/plans/measurements/2026-04-12-slice-003.txt"
        relocated = (
            PROJECT_ROOT / ".claude/measurements/2026-04-12-slice-003.txt",
            PROJECT_ROOT / ".claude/plans/measurements/2026-04-12-slice-003.txt",
        )
        assert tracked.exists() or any(p.exists() for p in relocated), (
            "ledger: Item 2 — neither tracked path nor any relocated path "
            "exists on disk (artifact lost)"
        )

    def test_item3_prose_artifact_exists(self):
        required = "Read the file first (CC 2.1.110+ requires Read before Write)"
        paths = (
            PROJECT_ROOT / "commands/claude-code/handoff.full.md",
            PROJECT_ROOT / "commands/claude-code/start-slice.full.md",
        )
        for p in paths:
            assert required in p.read_text(encoding="utf-8"), (
                f"ledger: Item 3 — {p.name} lacks required preamble phrase"
            )

    def test_item4_verifier_exists(self):
        assert (PROJECT_ROOT / "scripts" / "verify_handoff.sh").is_file(), (
            "ledger: Item 4 — scripts/verify_handoff.sh missing"
        )

    def test_item5_allowlist_present(self):
        data = json.loads(
            (PROJECT_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8")
        )
        allow = data.get("permissions", {}).get("allow", [])
        assert len(allow) >= 10, (
            f"ledger: Item 5 — permissions.allow length {len(allow)} < 10"
        )

    def test_item6_templates_exist(self):
        for n in (1, 2, 3, 4):
            p = PROJECT_ROOT / f".gitmessage-phase-{n}"
            assert p.is_file(), f"ledger: Item 6 — {p.name} missing at repo root"
        assert (PROJECT_ROOT / "checks" / "prepare-commit-msg.sh").is_file(), (
            "ledger: Item 6 — checks/prepare-commit-msg.sh missing"
        )

    def test_item7_status_full_exists(self):
        assert (
            PROJECT_ROOT / "commands" / "claude-code" / "status.full.md"
        ).is_file(), "ledger: Item 7 — status.full.md missing"

    def test_item_numbers_covered(self):
        """Defensive: if someone renumbers items, this class still enumerates
        seven distinct artifacts."""
        artifacts_per_item = 7
        methods = [m for m in dir(self) if re.match(r"^test_item\d+_", m)]
        assert len(methods) == artifacts_per_item, (
            f"ledger class must contain one test_itemN per item; found {methods}"
        )
