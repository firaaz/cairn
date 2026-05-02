"""Re-export ROLE_POLICIES from checks/role_guard.py for test import compat.

The sentinel test in test_inv_003_phase_topology.py imports this module to
verify that phase-3-implementer is absent from ROLE_POLICIES (option-b
asymmetry). The load-bearing assertion is the _via_text companion test;
this module exists solely to make the import succeed.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ROLE_GUARD_PATH = Path(__file__).resolve().parent.parent / "checks" / "role_guard.py"
_spec = importlib.util.spec_from_file_location(
    "_checks_role_guard_impl", _ROLE_GUARD_PATH
)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("_checks_role_guard_impl", _mod)
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

ROLE_POLICIES: dict = _mod.ROLE_POLICIES  # type: ignore[attr-defined]
