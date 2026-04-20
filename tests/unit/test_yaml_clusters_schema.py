"""Phase 2 RED — compression/slice-2-state-machine §B6.

`_parse_clusters(text)` MUST use `yaml.safe_load` + explicit schema check:
top-level = list of dicts each with `name: str` and `files: list[str]`.
Schema violation raises ValueError naming the offending cluster index.

Expected at Phase 2: FAILS — current impl is line-based.
"""

from __future__ import annotations

import textwrap

import pytest


def test_b6_well_formed_yaml_with_comments_and_colons_parses():
    import slice_orchestrator as so

    text = textwrap.dedent(
        """
        # top-level comment
        - name: cluster-a
          files:
              - "scripts/a:b.py"   # colon in path
              - tests/foo.py
        - name: cluster-b
          files:
            - scripts/c.py
        """
    ).strip()

    clusters = so._parse_clusters(text)
    assert isinstance(clusters, list) and len(clusters) == 2
    assert clusters[0]["name"] == "cluster-a"
    assert clusters[0]["files"] == ["scripts/a:b.py", "tests/foo.py"]
    assert clusters[1]["name"] == "cluster-b"
    assert clusters[1]["files"] == ["scripts/c.py"]


def test_b6_list_of_strings_raises_valueerror_with_index():
    import slice_orchestrator as so

    text = textwrap.dedent(
        """
        - cluster-a
        - cluster-b
        """
    ).strip()

    with pytest.raises(ValueError) as exc:
        so._parse_clusters(text)
    msg = str(exc.value)
    # The error must name at least one offending index (0 or 1).
    assert "0" in msg or "1" in msg, (
        f"ValueError must name offending cluster index; got {msg!r}"
    )


def test_b6_cluster_missing_files_key_raises_valueerror():
    import slice_orchestrator as so

    text = textwrap.dedent(
        """
        - name: cluster-a
          files: [scripts/a.py]
        - name: cluster-b
        """
    ).strip()

    with pytest.raises(ValueError):
        so._parse_clusters(text)
