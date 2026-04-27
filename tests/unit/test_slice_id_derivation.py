"""Phase 2 RED tests for compression/infrastructure — slice-id regex.

Verifies intent.md V3 (slice-id regex): valid ids match, invalid ids do not.
Regex per intent.md:76 — `^[a-z][a-z0-9-]*\\/[a-z][a-z0-9-]*$`.

Assumes slice_orchestrator exposes `is_valid_slice_id(s) -> bool` as a
module-level predicate. Expected at Phase 2: all tests FAIL because
scripts/slice_orchestrator.py does not exist yet.
"""

from __future__ import annotations

import pytest


VALID_IDS = [
    "compression/infrastructure",
    "identifier-scheme/doc-sweep",
    "fleet-coordinator/push-protocol",
    "a/b",
    "foo-bar-baz/x1-y2",
]

INVALID_IDS = [
    "Compression/infrastructure",  # leading capital in namespace
    "compression/Infrastructure",  # leading capital in topic
    "compression",  # missing topic segment
    "compression/",  # empty topic
    "/infrastructure",  # empty namespace
    "com pression/foo",  # space in namespace
    "compression/foo bar",  # space in topic
    "-compression/foo",  # leading hyphen
    "1compression/foo",  # leading digit
    "compression//foo",  # double slash
    "compression/foo/bar",  # too many segments
    "",  # empty
]


@pytest.mark.parametrize("slice_id", VALID_IDS)
def test_valid_slice_ids_match(slice_id: str):
    import slice_orchestrator as so

    assert so.is_valid_slice_id(slice_id) is True


@pytest.mark.parametrize("slice_id", INVALID_IDS)
def test_invalid_slice_ids_rejected(slice_id: str):
    import slice_orchestrator as so

    assert so.is_valid_slice_id(slice_id) is False
