"""F2.3 README reading-order test.

Per ``docs/plans/2026-05-08-cairn-m5-f2-consumer-doc-surface.md`` Section
F2.3 Step 1 / intent.md T3 line 27, ``README.md`` must contain a numbered
list naming the four docs in order: README.md (or "you are here"),
CONSUMER.md, docs/operational-reference.md, docs/spec-v1.md.

This test is RED at Phase 2: README.md currently uses an unordered list at
lines 31-37 with no explicit reading order.
"""

from __future__ import annotations

import re
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
README = CAIRN_ROOT / "README.md"


def test_readme_has_four_step_reading_order() -> None:
    """``README.md`` contains a numbered list with at least four entries
    naming, in order, README.md (or "you are here"), CONSUMER.md,
    ``docs/operational-reference.md``, ``docs/spec-v1.md``.
    """
    text = README.read_text()
    lines = text.splitlines()

    # 1. A "Reading order" heading is required by plan F2.3 Step 2.
    has_reading_order_heading = any(
        re.match(r"^#{1,3}\s+Reading\s+order\s*$", line, flags=re.IGNORECASE)
        for line in lines
    )
    assert has_reading_order_heading, (
        "README.md must contain a '## Reading order' heading per plan F2.3 "
        "Step 2 / intent.md line 27."
    )

    # 2. Collect numbered list items "1. ...", "2. ...", "3. ...", "4. ..."
    numbered_items: list[tuple[int, str]] = []
    for line in lines:
        m = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
        if m:
            numbered_items.append((int(m.group(1)), m.group(2)))

    assert len(numbered_items) >= 4, (
        f"README.md must contain a numbered list of ≥4 reading-order entries; "
        f"found {len(numbered_items)} numbered items."
    )

    # 3. Find the contiguous 1..4 sequence (allow other numbered lists later
    #    in the doc, but the reading-order block itself must run 1->2->3->4).
    sequence_start = None
    for i in range(len(numbered_items) - 3):
        nums = [n for n, _ in numbered_items[i : i + 4]]
        if nums == [1, 2, 3, 4]:
            sequence_start = i
            break
    assert sequence_start is not None, (
        "README.md must contain a contiguous 1->2->3->4 numbered sequence "
        "for the reading order per plan F2.3 Step 2."
    )

    block = [body for _n, body in numbered_items[sequence_start : sequence_start + 4]]

    # 4. Order content checks (case-insensitive substring).
    item1, item2, item3, item4 = block

    assert "readme.md" in item1.lower() or "you are here" in item1.lower(), (
        f"Reading-order item 1 must name README.md or 'you are here'; got {item1!r}"
    )

    assert "consumer.md" in item2.lower(), (
        f"Reading-order item 2 must name CONSUMER.md; got {item2!r}"
    )

    assert "operational-reference.md" in item3.lower(), (
        f"Reading-order item 3 must name docs/operational-reference.md; got {item3!r}"
    )

    assert "spec-v1.md" in item4.lower(), (
        f"Reading-order item 4 must name docs/spec-v1.md; got {item4!r}"
    )
