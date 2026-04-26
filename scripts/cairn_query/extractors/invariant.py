"""Invariant extractor — parses docs/ARCHITECTURE.md `invariant-check INV-NNN` blocks."""

from __future__ import annotations

import re
from pathlib import Path

from cairn_query.extractors.base import ExtractedEdge, ExtractedNode
from cairn_query.models import Invariant, PathAnchor

# Matches the fenced code block info string: `invariant-check INV-NNN`
INVARIANT_FENCE_RE = re.compile(r"^```invariant-check\s+(INV-\d{3})\s*$", re.MULTILINE)
FENCE_END_RE = re.compile(r"^```\s*$", re.MULTILINE)


class InvariantExtractor:
    def __init__(self, architecture_path: Path):
        self.path = architecture_path

    def extract(
        self, snapshot_id: str | None = None
    ) -> tuple[list[ExtractedNode], list[ExtractedEdge]]:
        if not self.path.exists():
            return ([], [])
        text = self.path.read_text()
        nodes: list[ExtractedNode] = []
        edges: list[ExtractedEdge] = []

        # Find all invariant-check fenced blocks
        pos = 0
        while True:
            m = INVARIANT_FENCE_RE.search(text, pos)
            if not m:
                break
            inv_id = m.group(1)
            body_start = m.end() + 1  # skip the newline after the opening fence
            # Find closing fence
            end_m = FENCE_END_RE.search(text, body_start)
            if not end_m:
                break
            body = text[body_start : end_m.start()]
            fields = self._parse_body(body)

            # Map fields to Invariant fields
            target_path = fields.get("target", "").strip('"')
            grep_val = fields.get("pattern", fields.get("grep", ""))
            description = fields.get("description", "").strip('"')

            try:
                inv = Invariant(
                    id=inv_id,
                    statement=description or grep_val,
                    target=PathAnchor(path=target_path),
                    grep=grep_val,
                    architecture_anchor=PathAnchor(path=str(self.path)),
                )
            except Exception:
                pos = end_m.end()
                continue

            nodes.append(ExtractedNode(entity=inv))
            # BINDS from architecture file
            edges.append(
                ExtractedEdge(
                    predicate="BINDS",
                    from_path=str(self.path),
                    to_node_type="Invariant",
                    to_id=inv_id,
                )
            )
            # Also BINDS from the target path
            if target_path:
                edges.append(
                    ExtractedEdge(
                        predicate="BINDS",
                        from_path=target_path,
                        to_node_type="Invariant",
                        to_id=inv_id,
                    )
                )

            pos = end_m.end()

        return (nodes, edges)

    @staticmethod
    def _parse_body(body: str) -> dict[str, str]:
        """Parse key: value lines from an invariant-check block body."""
        out: dict[str, str] = {}
        for line in body.splitlines():
            line = line.strip()
            if ":" in line:
                k, _, v = line.partition(":")
                out[k.strip()] = v.strip()
        return out
