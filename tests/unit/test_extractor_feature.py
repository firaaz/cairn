"""RED tests — FeatureExtractor against .claude/features/*.yaml.

Asserts: each feature YAML becomes one Feature node; the `compression`
feature is present with non-empty slice_ids; BINDS edges emit from the
feature file path.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cairn_query.extractors.feature import FeatureExtractor


@pytest.fixture
def extractor():
    return FeatureExtractor(features_dir=Path(".claude/features"))


def test_extracts_compression_feature(extractor):
    nodes, _edges = extractor.extract()
    compression = next((n.entity for n in nodes if n.entity.id == "compression"), None)
    assert compression is not None
    assert compression.entity_type == "feature"
    assert compression.slice_ids  # non-empty list


def test_extracts_at_least_one_feature(extractor):
    nodes, _edges = extractor.extract()
    assert len(nodes) >= 1


def test_emits_binds_from_feature_yaml(extractor):
    _nodes, edges = extractor.extract()
    binds_to_compression = [
        e
        for e in edges
        if e.predicate == "BINDS"
        and e.to_node_type == "Feature"
        and e.to_id == "compression"
    ]
    assert binds_to_compression
    assert any(
        e.from_path and e.from_path.endswith(".claude/features/compression.yaml")
        for e in binds_to_compression
    )


def test_handles_missing_features_dir(tmp_path):
    extractor = FeatureExtractor(features_dir=tmp_path / "nope")
    nodes, edges = extractor.extract()
    assert nodes == []
    assert edges == []
