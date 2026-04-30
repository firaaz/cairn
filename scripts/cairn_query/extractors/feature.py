"""FeatureExtractor — parses .claude/features/*.yaml files."""

from __future__ import annotations

from pathlib import Path

import yaml

from _root import project_root as _project_root
from cairn_query.extractors.base import ExtractedEdge, ExtractedNode
from cairn_query.models import Feature


class FeatureExtractor:
    """Extract Feature entities from .claude/features/*.yaml files."""

    def __init__(self, features_dir: Path | None = None) -> None:
        self._dir = (
            features_dir
            if features_dir is not None
            else _project_root() / ".claude" / "features"
        )

    def extract(
        self, snapshot_id: str | None = None
    ) -> tuple[list[ExtractedNode], list[ExtractedEdge]]:
        if not self._dir.exists():
            return [], []

        nodes: list[ExtractedNode] = []
        edges: list[ExtractedEdge] = []

        for yaml_file in sorted(self._dir.glob("*.yaml")):
            try:
                data = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                continue

            feature_id = data.get("id") or yaml_file.stem
            name = data.get("name") or feature_id
            intent = data.get("intent") or ""
            shaped_from = data.get("shaped-from") or data.get("shaped_from")

            # Collect slice IDs
            raw_slices = data.get("slices") or []
            slice_ids: list[str] = []
            for s in raw_slices:
                if isinstance(s, dict):
                    sid = s.get("id")
                    if sid:
                        slice_ids.append(sid)
                elif isinstance(s, str):
                    slice_ids.append(s)

            try:
                feature = Feature(
                    id=feature_id,
                    name=name,
                    intent=intent,
                    shaped_from=shaped_from,
                    slice_ids=slice_ids,
                )
            except Exception:
                continue

            nodes.append(ExtractedNode(entity=feature))
            edges.append(
                ExtractedEdge(
                    predicate="BINDS",
                    from_path=str(yaml_file),
                    to_node_type="Feature",
                    to_id=feature_id,
                )
            )

        return nodes, edges
