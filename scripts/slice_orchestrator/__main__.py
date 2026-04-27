"""CLI entry point for ``python -m slice_orchestrator`` and direct invocation.

Preserves the byte-identical ``--brief`` / ``--resume`` / ``--legacy`` arg
surface (intent §S4). Direct invocation (``python __main__.py``) ensures the
package is importable via the script's parent on ``sys.path`` so the relative
imports below resolve.
"""

from __future__ import annotations

import argparse
import os
import sys

# When invoked as a direct path (``python scripts/slice_orchestrator/__main__.py``)
# the package's parent is not automatically on ``sys.path`` — Python only adds
# the script's own directory. Detect that case and prepend the parent so the
# ``slice_orchestrator`` package itself resolves.
if __package__ in (None, ""):
    _here = os.path.dirname(os.path.abspath(__file__))
    _parent = os.path.dirname(_here)
    if _parent not in sys.path:
        sys.path.insert(0, _parent)
    from slice_orchestrator.lifecycle import (  # type: ignore[no-redef]
        init_new_slice,
        legacy_start_slice,
        run_phase_loop,
    )
else:
    from .lifecycle import init_new_slice, legacy_start_slice, run_phase_loop


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Cairn slice orchestrator — phase-by-phase agent dispatcher."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--brief",
        type=str,
        help="Brief text for a new slice (Phase 1 will derive an id from it).",
    )
    group.add_argument(
        "--resume",
        action="store_true",
        help="Resume the current slice from .claude/current-slice/slice.yaml.",
    )
    group.add_argument(
        "--legacy",
        action="store_true",
        help="Defer to commands/claude-code/start-slice-legacy.md (prose protocol).",
    )
    args = parser.parse_args(argv)

    if args.legacy:
        return legacy_start_slice()
    if args.brief:
        init_new_slice(args.brief)
    return run_phase_loop()


if __name__ == "__main__":
    sys.exit(main())
