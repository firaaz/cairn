"""SpecSection extractor — parses docs/spec-v1.md section headings."""

from __future__ import annotations

import re
from pathlib import Path

from cairn_query.extractors.base import ExtractedEdge, ExtractedNode
from cairn_query.models import PathAnchor, SpecSection

# Match headings like: ## §13 Title, ### §13.1 Title
# OR the actual spec-v1.md format: ## N. Title or ## N.M Title
SECTION_HEADING_RE = re.compile(
    r"^#{1,6}\s+(?:(§[\d.]+)\s+(.+?)|(\d+(?:\.\d+)*)\.\s+(.+?))(?:\s+\[.*\])?\s*$",
    re.MULTILINE,
)


class SpecSectionExtractor:
    def __init__(self, spec_path: Path):
        self.path = spec_path

    def extract(
        self, snapshot_id: str | None = None
    ) -> tuple[list[ExtractedNode], list[ExtractedEdge]]:
        if not self.path.exists():
            return ([], [])

        text = self.path.read_text()
        nodes: list[ExtractedNode] = []
        edges: list[ExtractedEdge] = []
        seen: set[str] = set()

        for m in SECTION_HEADING_RE.finditer(text):
            if m.group(1):
                # §-prefixed format
                section_id = m.group(1).strip()
                title = m.group(2).strip()
            else:
                # N. format → convert to §N
                section_id = f"§{m.group(3).strip()}"
                title = m.group(4).strip()

            if section_id in seen:
                continue
            seen.add(section_id)

            try:
                section = SpecSection(
                    id=section_id,
                    title=title,
                    body_anchor=PathAnchor(path=str(self.path)),
                )
            except Exception:
                continue

            nodes.append(ExtractedNode(entity=section))
            edges.append(
                ExtractedEdge(
                    predicate="BINDS",
                    from_path=str(self.path),
                    to_node_type="SpecSection",
                    to_id=section_id,
                )
            )

        return (nodes, edges)
