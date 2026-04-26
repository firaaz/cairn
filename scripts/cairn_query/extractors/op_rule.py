"""OpRule extractor — parses docs/operational-reference.md Phase Skill Guide table."""

from __future__ import annotations

import re
from pathlib import Path

from cairn_query.extractors.base import ExtractedEdge, ExtractedNode
from cairn_query.models import OpRule, PathAnchor

# Match the Phase Skill Guide table rows:
# | N. Role | **Role** | anti-behavior | ... |
PHASE_TABLE_ROW_RE = re.compile(
    r"^\|\s*(\d+)\.\s+\w+\s*\|\s*\*\*(\w+)\*\*\s*\|([^|]+)\|",
    re.MULTILINE,
)


class OpRuleExtractor:
    def __init__(self, op_ref_path: Path):
        self.path = op_ref_path

    def extract(
        self, snapshot_id: str | None = None
    ) -> tuple[list[ExtractedNode], list[ExtractedEdge]]:
        if not self.path.exists():
            return ([], [])

        text = self.path.read_text()
        nodes: list[ExtractedNode] = []
        edges: list[ExtractedEdge] = []

        # Find the Phase Skill Guide section
        psg_start = text.find("## Phase Skill Guide")
        if psg_start == -1:
            psg_start = 0

        # Find the Role and anti-behaviors table within the Phase Skill Guide
        section_text = text[psg_start:]

        for m in PHASE_TABLE_ROW_RE.finditer(section_text):
            phase_num = m.group(1)
            role_name = m.group(2)
            anti_behavior = m.group(3).strip()

            # Skip header-like rows
            if role_name.lower() in ("phase", "role", "reader"):
                pass

            rule_id = f"phase-skill-guide/phase-{phase_num}"
            scope = "docs/operational-reference.md § Phase Skill Guide"

            try:
                op_rule = OpRule(
                    id=rule_id,
                    statement=anti_behavior,
                    scope=scope,
                    body_anchor=PathAnchor(path=str(self.path)),
                )
            except Exception:
                continue

            nodes.append(ExtractedNode(entity=op_rule))
            edges.append(
                ExtractedEdge(
                    predicate="BINDS",
                    from_path=str(self.path),
                    to_node_type="OpRule",
                    to_id=rule_id,
                )
            )

        return (nodes, edges)
