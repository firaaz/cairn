"""Lesson extractor — parses docs/lessons.md L-NNN entries."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from cairn_query.extractors.base import ExtractedEdge, ExtractedNode
from cairn_query.models import Lesson, PathAnchor

# Matches headings like: ## L-001: Some title
LESSON_HEADING_RE = re.compile(r"^## (L-\d{3}):\s*(.+)$", re.MULTILINE)
DISCOVERED_RE = re.compile(r"\*\*Discovered\*\*:\s*(.+?)(?:\.|,|\n)", re.IGNORECASE)
PATTERN_RE = re.compile(
    r"\*\*Pattern\*\*:\s*(.+?)(?=\*\*[A-Z]|\Z)", re.DOTALL | re.IGNORECASE
)
CONCRETE_INSTANCE_RE = re.compile(
    r"\*\*Concrete instance\*\*:\s*(.+?)(?=\*\*[A-Z]|\Z)", re.DOTALL | re.IGNORECASE
)
RULE_RE = re.compile(
    r"\*\*Rule for future.+?\*\*:\s*(.+?)(?=\*\*[A-Z]|\Z)", re.DOTALL | re.IGNORECASE
)
ANTI_PATTERN_RE = re.compile(
    r"\*\*Anti-pattern signals\*\*:\s*(.+?)(?=\*\*[A-Z]|\Z|\Z)",
    re.DOTALL | re.IGNORECASE,
)
COMMIT_HASH_RE = re.compile(r"\b([0-9a-f]{7,40})\b")
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


class LessonExtractor:
    def __init__(self, lessons_path: Path):
        self.path = lessons_path

    def extract(
        self, snapshot_id: str | None = None
    ) -> tuple[list[ExtractedNode], list[ExtractedEdge]]:
        if not self.path.exists():
            return ([], [])

        text = self.path.read_text()
        nodes: list[ExtractedNode] = []
        edges: list[ExtractedEdge] = []

        # Split text into lesson sections
        headings = list(LESSON_HEADING_RE.finditer(text))
        for i, heading_m in enumerate(headings):
            lesson_id = heading_m.group(1)
            title = heading_m.group(2).strip()
            start = heading_m.end()
            end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
            body = text[start:end]

            lesson = self._parse_lesson_body(lesson_id, title, body)
            if lesson is None:
                continue

            nodes.append(ExtractedNode(entity=lesson))
            edges.append(
                ExtractedEdge(
                    predicate="BINDS",
                    from_path=str(self.path),
                    to_node_type="Lesson",
                    to_id=lesson_id,
                )
            )

        return (nodes, edges)

    def _parse_lesson_body(
        self, lesson_id: str, title: str, body: str
    ) -> Lesson | None:
        # Discovered date
        discovered_m = DISCOVERED_RE.search(body)
        discovered: date = date(2000, 1, 1)
        if discovered_m:
            date_m = DATE_RE.search(discovered_m.group(1))
            if date_m:
                try:
                    discovered = date.fromisoformat(date_m.group(1))
                except ValueError:
                    pass

        # Pattern
        pattern_m = PATTERN_RE.search(body)
        pattern = pattern_m.group(1).strip() if pattern_m else ""

        # Concrete instances — extract commit hashes
        instance_m = CONCRETE_INSTANCE_RE.search(body)
        instances: list[str] = []
        if instance_m:
            instances = COMMIT_HASH_RE.findall(instance_m.group(1))

        # Rule
        rule_m = RULE_RE.search(body)
        rule = rule_m.group(1).strip() if rule_m else ""

        # Anti-pattern signals — split by comma or bullet
        anti_m = ANTI_PATTERN_RE.search(body)
        anti_patterns: list[str] = []
        if anti_m:
            raw = anti_m.group(1).strip()
            # Split on "," followed by optional space+quote
            parts = re.split(r'[,;]\s*"?', raw)
            anti_patterns = [
                p.strip().strip('"').strip("'").rstrip('."') for p in parts if p.strip()
            ]

        try:
            lesson = Lesson(
                id=lesson_id,
                title=title,
                discovered=discovered,
                pattern=pattern or title,
                instances=instances,
                rule=rule or "See lesson body.",
                anti_patterns=anti_patterns,
                body_anchor=PathAnchor(path=str(self.path)),
            )
        except Exception:
            return None

        return lesson
