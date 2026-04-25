"""Cairn slice orchestrator — Python state machine driving the four-phase pipeline.

Replaces the prose `start-slice` protocol with a deterministic dispatcher that
spawns role-scoped Claude agents (`claude -p --agent <role>`) per phase, parses
their structured-return JSON tail, and routes on `status ∈ {OK, FAILED,
RAISE_ISSUE}`. Phase 3 fans out one agent per cluster declared in
`clusters.yaml`.

This package was split out of the single-file ``scripts/slice_orchestrator.py``
in slice ``compression/lever-2-orchestrator-split`` to reduce per-phase
read cost. Submodules:

- ``core``       — pure constants, formatters, helpers (no I/O).
- ``git``        — git wrappers (``_git``, ``_git_head_safe``, ``_head_subject_safe``).
- ``telemetry``  — observability state dict, atomic writes, heartbeat, cost.
- ``resume``     — slice-state read/write + the 13-state-triple resume matrix.
- ``dispatch``   — subprocess dispatch + Phase-3 fan-out.
- ``lifecycle``  — phase loop, slice init/close, signal/atexit integration.
- ``__main__``   — CLI entry (``python -m slice_orchestrator``).

The ``__init__`` re-exports the public surface (intent §S3) so every test and
external caller can keep using ``import slice_orchestrator as so; so.<name>``
without learning the new submodule layout.
"""

from __future__ import annotations

# --- core: constants + pure helpers -----------------------------------------
from .core import (
    AGENT_MODEL_CONFIG,
    CLUSTERS_YAML,
    CLUSTERS_YAML_LEGACY,
    DEBUG_DIR,
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_HEARTBEAT_STALE,
    DEFAULT_TIMEOUT_HARD,
    INTENT_MD,
    INV_009_COST_THRESHOLD_USD,
    INV_009_TOKEN_THRESHOLD,
    NON_TERMINAL_STATUS,
    PERMISSION_MODE,
    PRICING_TABLE_2026_04_24,
    ROLE_FOR_PHASE,
    ROLE_TO_PHASE,
    SLICE_ID_REGEX,
    SLICE_YAML,
    STATUS_VALUES,
    TERMINAL_STATUS,
    TOKEN_CLASSES,
    TRANSIENT_STDERR_RX,
    VALID_TRIAGER_ACTIONS,
    _active_pricing_table,
    _active_pricing_table_name,
    _classify_failure,
    _cost_for_tokens,
    _extract_agent_result_text,
    _extract_envelope_model,
    _intent_envelope,
    _iso_now,
    _normalize_slice_id,
    _parse_clusters,
    _parse_structured_tail,
    _parse_usage_envelope,
    _resolve_model_config,
    _resolve_timeout,
    _slice_id_slug,
    _utc_timestamp,
    detect_superseded_test_signal,
    is_valid_slice_id,
)

# --- git: wrappers + HEAD safety --------------------------------------------
from .git import _git, _git_head_safe, _head_subject_safe

# --- telemetry: state, observability, heartbeat, cost -----------------------
from .telemetry import (
    _HeartbeatDaemon,
    _append_index_entry,
    _atomic_write,
    _check_heartbeat_alive,
    _default_observability_errors,
    _final_persist_and_md,
    _generate_result_md,
    _handle_heartbeat_death,
    _init_state_dict,
    _observability_paths,
    _persist_state,
    _record_phase_cost,
    _register_atexit_terminal_writer,
    _start_heartbeat,
    _state,
    _update_state,
    _write_cluster_log,
    _write_phase_log,
    _write_result_md,
)

# --- resume: slice-state read/write + reconciliation matrix -----------------
from .resume import (
    _current_phase,
    _is_slice_complete_subject,
    _persist_current_phase,
    _persist_redispatch,
    _read_slice_state_strict,
    _reconcile_resume_state,
    _refuse_resume,
    _slice_brief,
    _slice_id,
    _write_slice_state,
    read_slice_state,
)

# --- dispatch: subprocess fan-out -------------------------------------------
from .dispatch import (
    _dispatch_once,
    _load_clusters,
    _log_retry_attempt,
    _phase3_dispatch_with_log,
    _resolve_phase_and_slice,
    _resolve_supersession_hint,
    _run_with_live_stderr,
    dispatch_phase_3,
    dispatch_phase_agent,
    dispatch_triager,
)

# --- lifecycle: phase loop, init, close, signals ----------------------------
from .lifecycle import (
    _abort_slice,
    _bundle_handoff_md,
    _clean_shutdown,
    _dispatch_for_phase,
    _is_slice_already_closed,
    _register_signal_handlers,
    _wipe_current_slice,
    close_slice,
    commit_phase_handoff,
    init_new_slice,
    legacy_start_slice,
    run_phase_loop,
)

# --- CLI entry --------------------------------------------------------------
# Avoid ``from .__main__ import main`` at package-init time — that triggers a
# RuntimeWarning when ``python -m slice_orchestrator`` later loads the same
# submodule a second time. Defer the import to a thin wrapper so
# ``slice_orchestrator.main`` still resolves (intent §S3) without pre-loading
# the ``__main__`` module.


def main(argv=None):  # noqa: D401 — re-export wrapper
    """Forward to :func:`slice_orchestrator.__main__.main` (lazy import)."""
    from .__main__ import main as _main

    return _main(argv)


# --- Stdlib re-exports (pre-split monkeypatch surface) ---------------------
# Tests reach for ``so.<stdlib>`` to swap stdlib primitives and the pre-split
# single-file module exposed these names at module top level. Post-split
# only the relevant submodule imports each; we re-export the load-bearing
# ones here so ``monkeypatch.setattr(so.<stdlib>, ...)`` keeps working.
import os  # noqa: E402,F401  (intentional public re-export)
import subprocess  # noqa: E402,F401
import time  # noqa: E402,F401
import yaml  # noqa: E402,F401


# ---------------------------------------------------------------------------
# Cross-module attribute mirroring.
#
# Pre-split, ``scripts/slice_orchestrator.py`` was a single module. Existing
# tests pervasively use ``monkeypatch.setattr(so, "X", value)`` to swap helpers
# (``_git``, ``_start_heartbeat``, ``_run_with_live_stderr``) and constants
# (``DEBUG_DIR``, ``SLICE_YAML``) at call time. Post-split each name lives in
# exactly one submodule's globals; a setattr against the facade alone would
# leave submodule code reading the unmodified original.
#
# To preserve the pre-split monkeypatch semantics by construction (intent §S6
# test invariance — every existing test must pass without source change), we
# install a custom module class whose ``__setattr__`` mirrors writes back into
# whichever submodule originally defined the name. Reads continue to resolve
# through the facade as ``slice_orchestrator.X`` (intent §S3 reachability
# contract). The mirroring is transparent for normal use; only test
# monkeypatches see the effect.
# ---------------------------------------------------------------------------

import sys as _sys
import types as _types


class _MirroringModule(_types.ModuleType):
    """Package-level module class that mirrors attribute writes to submodules.

    Any ``setattr`` against the facade is propagated to each submodule whose
    own ``__dict__`` already contains the same attribute name, keeping
    submodule globals in sync with facade-side patches. Attribute deletion is
    similarly mirrored so ``monkeypatch`` teardown restores all surfaces.
    """

    _SUBMODULE_NAMES = (
        "core",
        "git",
        "telemetry",
        "resume",
        "dispatch",
        "lifecycle",
        "__main__",
    )

    def _iter_submodules(self):
        for sub_short in self._SUBMODULE_NAMES:
            full = f"{self.__name__}.{sub_short}"
            mod = _sys.modules.get(full)
            if mod is not None:
                yield mod

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        # Skip dunder writes (module bookkeeping).
        if name.startswith("__") and name.endswith("__"):
            return
        for sub in self._iter_submodules():
            if name in sub.__dict__:
                sub.__dict__[name] = value

    def __delattr__(self, name):
        super().__delattr__(name)
        if name.startswith("__") and name.endswith("__"):
            return
        for sub in self._iter_submodules():
            if name in sub.__dict__:
                # Restore to whatever the submodule itself defined originally
                # is impossible without snapshotting; the safest behaviour is
                # to leave the submodule entry alone on delete (monkeypatch
                # uses setattr-back-to-original at teardown, not delattr).
                pass


_sys.modules[__name__].__class__ = _MirroringModule

__all__ = [
    # Public defs/classes (intent §S3 top-level group)
    "is_valid_slice_id",
    "read_slice_state",
    "dispatch_phase_agent",
    "dispatch_triager",
    "dispatch_phase_3",
    "detect_superseded_test_signal",
    "commit_phase_handoff",
    "run_phase_loop",
    "init_new_slice",
    "close_slice",
    "legacy_start_slice",
    "main",
    "_HeartbeatDaemon",
    # Module constants (intent §S3 constants group)
    "AGENT_MODEL_CONFIG",
    "INV_009_COST_THRESHOLD_USD",
    "INV_009_TOKEN_THRESHOLD",
    "PRICING_TABLE_2026_04_24",
    "ROLE_FOR_PHASE",
    "ROLE_TO_PHASE",
    "DEBUG_DIR",
    "DEFAULT_TIMEOUT_HARD",
    "PERMISSION_MODE",
    "VALID_TRIAGER_ACTIONS",
    "SLICE_ID_REGEX",
    # Underscore helpers (intent §S3 audit-by-grep group)
    "_resolve_model_config",
    "_classify_failure",
    "_parse_structured_tail",
    "_parse_usage_envelope",
    "_extract_agent_result_text",
    "_extract_envelope_model",
    "_cost_for_tokens",
    "_record_phase_cost",
    "_active_pricing_table",
    "_active_pricing_table_name",
    "_resolve_timeout",
    "_normalize_slice_id",
    "_slice_id_slug",
    "_utc_timestamp",
    "_iso_now",
    "_init_state_dict",
    "_default_observability_errors",
    "_update_state",
    "_observability_paths",
    "_atomic_write",
    "_persist_state",
    "_generate_result_md",
    "_write_result_md",
    "_append_index_entry",
    "_start_heartbeat",
    "_check_heartbeat_alive",
    "_handle_heartbeat_death",
    "_bundle_handoff_md",
    "_wipe_current_slice",
    "_is_slice_already_closed",
    "_reconcile_resume_state",
    "_is_slice_complete_subject",
    "_head_subject_safe",
    "_refuse_resume",
    "_final_persist_and_md",
    "_register_atexit_terminal_writer",
    "_write_phase_log",
    "_git",
    "_git_head_safe",
    "_run_with_live_stderr",
    "_resolve_phase_and_slice",
    "_dispatch_once",
    "_log_retry_attempt",
    "_resolve_supersession_hint",
    "_load_clusters",
    "_parse_clusters",
    "_intent_envelope",
    "_phase3_dispatch_with_log",
    "_write_cluster_log",
    "_dispatch_for_phase",
    "_current_phase",
    "_persist_current_phase",
    "_persist_redispatch",
    "_clean_shutdown",
    "_register_signal_handlers",
    "_slice_id",
    "_slice_brief",
    "_abort_slice",
    "_read_slice_state_strict",
    "_write_slice_state",
]
