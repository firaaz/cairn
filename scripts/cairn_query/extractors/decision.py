"""Decision extractor — parses docs/adr/*.md YAML frontmatter + body."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import yaml

from cairn_query.extractors.base import ExtractedEdge, ExtractedNode
from cairn_query.models import Decision, PathAnchor

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class DecisionExtractor:
    def __init__(self, adr_dir: Path):
        self.adr_dir = adr_dir

    def extract(
        self, snapshot_id: str | None = None
    ) -> tuple[list[ExtractedNode], list[ExtractedEdge]]:
        if not self.adr_dir.exists():
            return ([], [])

        nodes: list[ExtractedNode] = []
        edges: list[ExtractedEdge] = []

        for adr_file in sorted(self.adr_dir.glob("*.md")):
            if adr_file.name == "index.md":
                continue
            result = self._parse_adr(adr_file)
            if result is None:
                continue
            decision, file_edges = result
            nodes.append(ExtractedNode(entity=decision))
            edges.extend(file_edges)

        return (nodes, edges)

    def _parse_adr(self, path: Path) -> tuple[Decision, list[ExtractedEdge]] | None:
        text = path.read_text()
        m = FRONTMATTER_RE.match(text)
        if not m:
            return None
        try:
            fm = yaml.safe_load(m.group(1))
        except yaml.YAMLError:
            return None
        if not isinstance(fm, dict):
            return None

        adr_id = fm.get("id") or path.stem
        name = fm.get("name") or fm.get("title") or adr_id
        status_raw = str(fm.get("status", "draft")).lower()
        status_map = {
            "accepted": "accepted",
            "superseded": "superseded",
            "deferred": "deferred",
            "draft": "draft",
        }
        status = status_map.get(status_raw, "draft")
        firmness_raw = str(fm.get("firmness", "provisional")).lower()
        firmness = "firm" if firmness_raw == "firm" else "provisional"
        topic = str(fm.get("topic", "general"))
        raw_date = fm.get("date")
        if isinstance(raw_date, date):
            adr_date = raw_date
        else:
            try:
                adr_date = date.fromisoformat(str(raw_date))
            except Exception:
                adr_date = date(2000, 1, 1)

        inv_touched = self._to_str_list(
            fm.get("invariants-touched") or fm.get("invariants_touched")
        )
        supersedes_raw = self._to_str_list(fm.get("supersedes"))
        supersedes_ids = [s.split()[0] for s in supersedes_raw if s.split()]
        superseded_by = fm.get("superseded-by") or fm.get("superseded_by")
        if superseded_by == "null" or superseded_by is None:
            superseded_by = None
        else:
            superseded_by = str(superseded_by)

        try:
            decision = Decision(
                id=adr_id,
                name=name,
                status=status,  # type: ignore[arg-type]
                firmness=firmness,  # type: ignore[arg-type]
                topic=topic,
                date=adr_date,
                invariants_touched=inv_touched,
                supersedes=supersedes_ids,
                superseded_by=superseded_by,
                body_anchor=PathAnchor(path=str(path)),
            )
        except Exception:
            return None

        file_edges: list[ExtractedEdge] = []
        file_edges.append(
            ExtractedEdge(
                predicate="BINDS",
                from_path=str(path),
                to_node_type="Decision",
                to_id=adr_id,
            )
        )
        for sup_id in supersedes_ids:
            file_edges.append(
                ExtractedEdge(
                    predicate="SUPERSEDES",
                    from_node_type="Decision",
                    from_id=adr_id,
                    to_node_type="Decision",
                    to_id=sup_id,
                )
            )

        return (decision, file_edges)

    @staticmethod
    def _to_str_list(val: object) -> list[str]:
        if val is None:
            return []
        if isinstance(val, list):
            return [str(v) for v in val]
        if isinstance(val, str):
            return [val] if val else []
        return [str(val)]
