"""RED tests — SnapshotLRU(maxsize=8) + sources_changed_since (mtime fingerprint).

LRU semantics: cache up to N, evict oldest on overflow, recency-bump on get.
mtime helper: any source whose mtime differs from the recorded manifest, or
that has been deleted, must report changed=True.
"""

from __future__ import annotations

import os
import time

from cairn_query.storage import SnapshotLRU, sources_changed_since


def test_lru_caches_eight_snapshots():
    cache = SnapshotLRU(maxsize=8)
    for i in range(8):
        cache.put(f"sha-{i}", {"data": i})
    for i in range(8):
        assert cache.get(f"sha-{i}") == {"data": i}


def test_lru_evicts_oldest_when_full():
    cache = SnapshotLRU(maxsize=2)
    cache.put("sha-1", "a")
    cache.put("sha-2", "b")
    cache.put("sha-3", "c")  # evicts sha-1
    assert cache.get("sha-1") is None
    assert cache.get("sha-2") == "b"
    assert cache.get("sha-3") == "c"


def test_lru_reorders_on_get():
    cache = SnapshotLRU(maxsize=2)
    cache.put("sha-1", "a")
    cache.put("sha-2", "b")
    cache.get("sha-1")  # marks sha-1 as recent
    cache.put("sha-3", "c")  # should evict sha-2 instead
    assert cache.get("sha-1") == "a"
    assert cache.get("sha-2") is None


def test_sources_changed_since_detects_modification(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("v1")
    manifest = {str(f): f.stat().st_mtime}
    assert not sources_changed_since(manifest, [f])
    time.sleep(0.01)
    f.write_text("v2")
    os.utime(f, (f.stat().st_atime, f.stat().st_mtime + 1))
    assert sources_changed_since(manifest, [f])


def test_sources_changed_since_handles_missing_file(tmp_path):
    """Deleted source counts as changed."""
    f = tmp_path / "doc.md"
    f.write_text("v1")
    manifest = {str(f): f.stat().st_mtime}
    f.unlink()
    assert sources_changed_since(manifest, [f])
