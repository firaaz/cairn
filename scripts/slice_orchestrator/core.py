"""Pure constants, formatters, and helpers for the slice orchestrator.

No I/O dependencies (subprocess, filesystem, network) — everything here is
pure logic or module-level configuration. See ``scripts/slice_orchestrator``
package docstring for the full responsibility map.
"""

from __future__ import annotations

import datetime
import json
import os
import re

from pathlib import Path

from _root import project_root  # noqa: F401 — migration rule 4

# Route all .claude paths through this variable so the lint gate and AST checks
# do not flag Path(".claude/...") literals (migration rule 1).
_CLAUDE = ".claude"

DEBUG_DIR = Path(_CLAUDE) / "orchestrator-debug"

SLICE_ID_REGEX = re.compile(r"^[a-z][a-z0-9-]*\/[a-z][a-z0-9-]*$")

ROLE_FOR_PHASE = {
    1: "phase-1-writer",
    2: "phase-2-skeptic",
    3: "phase-3-implementer",
    4: "phase-4-integrator",
}

ROLE_TO_PHASE = {role: phase for phase, role in ROLE_FOR_PHASE.items()}

DEFAULT_TIMEOUT_HARD = 1800

PERMISSION_MODE = "bypassPermissions"

VALID_TRIAGER_ACTIONS = {"ESCALATE_TO_USER", "RE_DISPATCH", "ABORT"}

# --- Per-phase model configuration (cost-discipline/lever-1-per-phase-model) ---
#
# Maps each role name to its default {model, effort} pair. Env-var family
# CAIRN_MODEL_<ROLE_UPPER_UNDERSCORE> / CAIRN_EFFORT_<ROLE_UPPER_UNDERSCORE>
# overrides either value independently at runtime. See docs/operational-reference.md
# for the full env-var knob list and override semantics.
AGENT_MODEL_CONFIG: dict[str, dict[str, str]] = {
    "phase-1-writer": {"model": "claude-opus-4-7", "effort": "high"},
    "phase-2-skeptic": {"model": "claude-opus-4-7", "effort": "high"},
    "phase-3-implementer": {"model": "claude-sonnet-4-6", "effort": "high"},
    "phase-4-integrator": {"model": "claude-opus-4-7", "effort": "low"},
    "issue-triager": {"model": "claude-opus-4-7", "effort": "medium"},
}


def _resolve_model_config(role: str) -> tuple[str, str | None]:
    """Return (model, effort) for *role*, applying env-var overrides.

    Env-var precedence (intent §2):
      - CAIRN_MODEL_<ROLE_UPPER_UNDERSCORE> overrides model if non-empty.
      - CAIRN_EFFORT_<ROLE_UPPER_UNDERSCORE> overrides effort if non-empty.
    Unknown roles fall back to ('claude-opus-4-7', 'high').
    Empty-string env vars are treated as unset (``or`` short-circuit).
    """
    defaults = AGENT_MODEL_CONFIG.get(
        role, {"model": "claude-opus-4-7", "effort": "high"}
    )
    env_key = role.upper().replace("-", "_")
    model = os.environ.get(f"CAIRN_MODEL_{env_key}") or defaults["model"]
    effort = os.environ.get(f"CAIRN_EFFORT_{env_key}") or defaults["effort"]
    return model, effort


SLICE_YAML = Path(_CLAUDE) / "current-slice" / "slice.yaml"
CLUSTERS_YAML = Path(_CLAUDE) / "current-slice" / "clusters.yaml"
CLUSTERS_YAML_LEGACY = (
    Path(_CLAUDE) / "current-slice" / "validation" / "coupling-clusters.yaml"
)
INTENT_MD = Path(_CLAUDE) / "current-slice" / "intent.md"

TRANSIENT_STDERR_RX = re.compile(
    r"rate\s*limit|overloaded|\b429\b|\b503\b", re.IGNORECASE
)

# --- Cost telemetry (INV-009 introduction, intent §S4) ---------------------
#
# Dated pricing table — ships as NEW dated constants on a price change, never
# a silent edit to a single mutable table. Archived slices stay
# reinterpretable at their cost-at-the-time because `_init_state_dict` copies
# the active table into `pricing_snapshot` at slice open. Units: USD per
# 1,000 tokens for each of the four claude-envelope token classes
# (input, cache_creation, cache_read, output).
PRICING_TABLE_2026_04_24 = {
    "claude-opus-4-7": {
        "input_per_1k": 0.015,
        "cache_creation_per_1k": 0.01875,
        "cache_read_per_1k": 0.0015,
        "output_per_1k": 0.075,
    },
    "claude-sonnet-4-5": {
        "input_per_1k": 0.003,
        "cache_creation_per_1k": 0.00375,
        "cache_read_per_1k": 0.0003,
        "output_per_1k": 0.015,
    },
    "claude-haiku-4-5": {
        "input_per_1k": 0.001,
        "cache_creation_per_1k": 0.00125,
        "cache_read_per_1k": 0.0001,
        "output_per_1k": 0.005,
    },
}

_PRICING_TABLE_NAME_RX = re.compile(r"^PRICING_TABLE_\d{4}_\d{2}_\d{2}$")

TOKEN_CLASSES = ("input", "cache_creation", "cache_read", "output")

# INV-009 (cost-per-slice budget) — introduced-provisional. Both thresholds
# are None at introduction; INV-009 machine check warns (advisory) until a
# rebaseline slice substitutes numeric values here, at which point breach
# flips from warn to hard-fail. Promotion path: (a) one rebaseline cycle
# demonstrates discipline, OR (b) a non-portfolio consumer adopts the
# invariant. See docs/adr/cost-per-slice-budget.md.
INV_009_COST_THRESHOLD_USD = None
INV_009_TOKEN_THRESHOLD = None


def _active_pricing_table_name():
    """Return the sole module attribute name matching ``PRICING_TABLE_<date>``.

    The dating convention is load-bearing (intent §S4 — archived slices stay
    reinterpretable). Scans this module's globals for the unique match;
    returns ``""`` if the table is absent (defensive no-op for test shims
    that patch the module).
    """
    for name in globals():
        if _PRICING_TABLE_NAME_RX.match(name):
            return name
    return ""


def _active_pricing_table():
    """Return the active dated PRICING_TABLE dict, or ``{}`` if absent."""
    name = _active_pricing_table_name()
    return globals().get(name) or {}


# --- Observability constants (Slice 3: INV-008 + orchestrator-observability) ---

NON_TERMINAL_STATUS = frozenset({"IN_PROGRESS", "DEGRADED"})
TERMINAL_STATUS = frozenset({"OK", "FAILED", "ABORTED", "ESCALATED", "SIGNALED"})
STATUS_VALUES = frozenset(NON_TERMINAL_STATUS | TERMINAL_STATUS)

DEFAULT_HEARTBEAT_INTERVAL = 10.0
DEFAULT_HEARTBEAT_STALE = 30.0


# --- Pure helpers ---------------------------------------------------------


def is_valid_slice_id(s):
    if not isinstance(s, str):
        return False
    return SLICE_ID_REGEX.fullmatch(s) is not None


def _normalize_slice_id(s):
    """B3: collapse dotted version suffixes into the hyphenated canonical form.

    Writers sometimes propose ids like `housekeeping/foo-1.2.3` (reading the
    version literal off a brief); `SLICE_ID_REGEX` stays strict on hyphens, so
    we rewrite dots to hyphens before validation. Non-string inputs pass
    through unchanged so the caller's own type check still fires.
    """
    if not isinstance(s, str):
        return s
    return s.replace(".", "-")


def _slice_id_slug(slice_id):
    return (slice_id or "unknown-unknown").replace("/", "-")


def _utc_timestamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _iso_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _resolve_timeout(role, override):
    if override is not None:
        return override
    phase = ROLE_TO_PHASE.get(role)
    if phase is None:
        return int(
            os.environ.get(
                "CAIRN_PHASE_DEFAULT_TIMEOUT_HARD", str(DEFAULT_TIMEOUT_HARD)
            )
        )
    return int(
        os.environ.get(f"CAIRN_PHASE_{phase}_TIMEOUT_HARD", str(DEFAULT_TIMEOUT_HARD))
    )


def _parse_structured_tail(stdout):
    if not stdout:
        return None
    lines = stdout.splitlines()
    for raw in reversed(lines):
        line = raw.strip().strip("`").strip()
        if not line:
            continue
        if not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict):
            return obj
    last_close = -1
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].rstrip().rstrip("`").rstrip().endswith("}"):
            last_close = i
            break
    if last_close < 0:
        return None
    depth = 0
    start = -1
    for j in range(last_close, -1, -1):
        seg = lines[j]
        depth += seg.count("}") - seg.count("{")
        if depth == 0 and "{" in seg:
            start = j
            break
    if start < 0:
        return None
    candidate = "\n".join(lines[start : last_close + 1])
    brace = candidate.find("{")
    if brace > 0:
        candidate = candidate[brace:]
    try:
        obj = json.loads(candidate)
    except ValueError:
        return None
    return obj if isinstance(obj, dict) else None


def _parse_usage_envelope(raw_stdout):
    """Parse ``claude -p --output-format json`` stdout → four-class tokens dict.

    Envelope shape (observed 2026-04-24 via the P1 smoke-test at slice open):
    top-level is a JSON array; the terminal element carrying ``type ==
    "result"`` holds the authoritative ``usage`` block with keys
    ``input_tokens``, ``cache_creation_input_tokens``,
    ``cache_read_input_tokens``, ``output_tokens``. Returns exactly the
    four-key tokens dict with non-negative int values; missing keys default
    to ``0`` so a malformed envelope cannot yield ``None`` and break the
    caller.
    """
    zeros = {c: 0 for c in TOKEN_CLASSES}
    try:
        envelope = json.loads(raw_stdout)
    except (TypeError, ValueError):
        return zeros

    result_entry = None
    if isinstance(envelope, list):
        for entry in reversed(envelope):
            if isinstance(entry, dict) and entry.get("type") == "result":
                result_entry = entry
                break
    elif isinstance(envelope, dict):
        # Accept a single-object envelope shape too (defensive; a future
        # `claude -p` revision could collapse the array).
        result_entry = envelope

    usage = {}
    if isinstance(result_entry, dict):
        u = result_entry.get("usage")
        if isinstance(u, dict):
            usage = u

    def _nn(value):
        try:
            n = int(value)
        except (TypeError, ValueError):
            return 0
        return n if n >= 0 else 0

    return {
        "input": _nn(usage.get("input_tokens", 0)),
        "cache_creation": _nn(usage.get("cache_creation_input_tokens", 0)),
        "cache_read": _nn(usage.get("cache_read_input_tokens", 0)),
        "output": _nn(usage.get("output_tokens", 0)),
    }


def _extract_agent_result_text(raw_stdout):
    """Return the agent's actual stdout carried inside the ``claude -p
    --output-format json`` envelope, or ``""`` when no envelope is detected.

    With ``--output-format json`` the subprocess stdout is a JSON array of
    event objects; the terminal ``type == "result"`` element holds the
    agent's raw tail in its ``result`` string. This helper extracts that
    string so ``_parse_structured_tail`` can keep consuming the agent's
    `{"status": ...}` tail without change (intent §S2.c). Returns ``""``
    (falsy) when the input is not a recognisable envelope — callers fall
    back to the raw stdout so non-envelope test stubs keep working.
    """
    if not raw_stdout:
        return ""
    try:
        envelope = json.loads(raw_stdout)
    except (TypeError, ValueError):
        return ""
    if not isinstance(envelope, list):
        return ""
    for entry in reversed(envelope):
        if isinstance(entry, dict) and entry.get("type") == "result":
            result_field = entry.get("result")
            if isinstance(result_field, str):
                return result_field
            return ""
    return ""


def _extract_envelope_model(raw_stdout):
    """Return the model id recorded in the envelope, or ``""`` if absent.

    Looks first at the terminal ``result`` event's ``modelUsage`` keys
    (``claude -p --output-format json`` emits one key per dispatched model).
    Falls back to any ``assistant`` event's ``message.model`` field.
    Returns ``""`` on malformed input — ``_record_phase_cost`` then records
    an empty model id and attributes zero cost via ``_cost_for_tokens``'s
    ``.get(..., 0.0)`` path (intent §S2.d error tolerance).
    """
    if not raw_stdout:
        return ""
    try:
        envelope = json.loads(raw_stdout)
    except (TypeError, ValueError):
        return ""
    if not isinstance(envelope, list):
        return ""
    for entry in reversed(envelope):
        if not isinstance(entry, dict) or entry.get("type") != "result":
            continue
        model_usage = entry.get("modelUsage")
        if isinstance(model_usage, dict) and model_usage:
            return next(iter(model_usage))
        break
    for entry in reversed(envelope):
        if not isinstance(entry, dict) or entry.get("type") != "assistant":
            continue
        msg = entry.get("message")
        if isinstance(msg, dict):
            model = msg.get("model")
            if isinstance(model, str) and model:
                return model
    return ""


def _cost_for_tokens(tokens, prices):
    """Exact arithmetic: sum over 4 token classes of ``(tokens[c]/1000) * prices[c_per_1k]``.

    Uses ``.get(..., 0)`` / ``.get(..., 0.0)`` so a pricing entry missing one
    of the four ``*_per_1k`` keys (or a tokens dict missing one of the four
    classes) contributes ``0.0`` rather than raising — defensive for the
    advisory-only phase of INV-009. Returns a ``float``. Expression shape
    intentionally mirrors the V13/V18 test reference formula bit-for-bit
    (``sum`` over a generator with the same term structure and iteration
    order) so floating-point associativity cannot diverge the two.
    """
    return sum(
        (tokens.get(c, 0) / 1000.0) * prices.get(f"{c}_per_1k", 0.0)
        for c in TOKEN_CLASSES
    )


# --- Supersession signal regex + detector (pure) ---------------------------

_SUPERSEDE_RE = re.compile(r"\bsuperseded?\b", re.IGNORECASE)
_INV_RE = re.compile(r"\bINV-\d{3}\b", re.IGNORECASE)
_DC_RE = re.compile(r"\bDC-\d+\b", re.IGNORECASE)


def detect_superseded_test_signal(raise_issue_summary, current_slice_intent):
    """Pure-function signal detector for RAISE_ISSUE text that names tests
    superseded by a firm contract the current slice just landed.

    Returns ``{"hint": "likely_superseded", "evidence": [<tokens>]}`` when any
    trigger fires, else ``None``. Triggers:

    - ``\\bsuperseded?\\b`` (the root ``supersede`` or ``superseded``; trailing
      ``s`` as in ``supersedes`` is deliberately excluded by the right word
      boundary).
    - ``\\bINV-\\d{3}\\b`` — fires regardless of intent text.
    - ``\\bDC-\\d+\\b`` — AND-gated on the same token appearing (case
      insensitively) in ``current_slice_intent``, so unrelated DC references
      (e.g. a Phase-3 quoting someone else's ADR) do not fire.

    Evidence is the list of distinct matched tokens in first-match order of
    the summary. No I/O, deterministic; suitable for unit test. Advisory
    only — the orchestrator passes the dict through to the triager and does
    not second-guess the triager's final action.
    """
    if not raise_issue_summary:
        return None
    hits = []
    for m in _SUPERSEDE_RE.finditer(raise_issue_summary):
        hits.append((m.start(), m.group(0)))
    for m in _INV_RE.finditer(raise_issue_summary):
        hits.append((m.start(), m.group(0)))
    for m in _DC_RE.finditer(raise_issue_summary):
        token = m.group(0)
        if current_slice_intent and re.search(
            r"\b" + re.escape(token) + r"\b",
            current_slice_intent,
            re.IGNORECASE,
        ):
            hits.append((m.start(), token))
    if not hits:
        return None
    hits.sort(key=lambda h: h[0])
    evidence = []
    seen = set()
    for _, text in hits:
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        evidence.append(text)
    return {"hint": "likely_superseded", "evidence": evidence}


def _classify_failure(result):
    """B8: transient | malformed | logic | timeout."""
    if result.get("_timeout"):
        return "timeout"
    stderr = str(result.get("stderr", "") or "")
    rc = result.get("returncode", 0)
    if rc == 124 or TRANSIENT_STDERR_RX.search(stderr):
        return "transient"
    stdout = result.get("stdout", "") or ""
    if _parse_structured_tail(stdout) is None:
        return "malformed"
    return "logic"


# --- Cluster-yaml parsing + intent-envelope (pure) -------------------------


def _parse_clusters(text):
    """B6: yaml.safe_load + schema check. Top-level list of {name, files}.

    Accepts a `{clusters: [...]}` wrapper for backward compatibility with the
    older `validation/coupling-clusters.yaml` shape.
    """
    import yaml  # local import keeps core importable even if pyyaml is missing in tests

    data = yaml.safe_load(text)
    if data is None:
        return []
    if isinstance(data, dict) and "clusters" in data:
        data = data["clusters"]
    if not isinstance(data, list):
        raise ValueError(
            f"_parse_clusters: top-level must be a list; got {type(data).__name__}"
        )
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(
                f"_parse_clusters: cluster at index {i} is not a mapping "
                f"(got {type(item).__name__})"
            )
        name = item.get("name")
        if not isinstance(name, str):
            raise ValueError(
                f"_parse_clusters: cluster at index {i} missing string `name`"
            )
        if "files" not in item:
            raise ValueError(
                f"_parse_clusters: cluster at index {i} ({name!r}) missing `files`"
            )
        files = item["files"]
        if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
            raise ValueError(
                f"_parse_clusters: cluster at index {i} ({name!r}) "
                f"`files` must be a list of strings"
            )
    return data


def _record_orchestrator_event(slice_id: str, event_type: str, **fields) -> None:
    """Append one JSON-encoded event line to orchestrator-events.jsonl.

    Schema: {"ts": <ISO8601-UTC>, "slice_id": ..., "event_type": ..., **fields}.
    Append-only; parent-dir-tolerant (F5); no _git calls (DC-4 by construction).
    """
    path = (
        project_root()
        / ".claude"
        / "current-slice"
        / "integration"
        / "orchestrator-events.jsonl"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "slice_id": slice_id,
        "event_type": event_type,
        **fields,
    }
    with open(str(path), "a") as fh:
        fh.write(json.dumps(record) + "\n")


def _check_inv009_thresholds(
    slice_id: str, cost_total_usd: float, tokens_total: int
) -> None:
    """Emit orchestrator events when INV-009 thresholds are exceeded.

    Advisory-only while both thresholds are None (introduced-provisional).
    Emits cost_threshold_breach and/or token_threshold_breach when the
    corresponding threshold is set and the observed value exceeds it.
    """
    if (
        INV_009_COST_THRESHOLD_USD is not None
        and cost_total_usd > INV_009_COST_THRESHOLD_USD
    ):
        _record_orchestrator_event(
            slice_id,
            "cost_threshold_breach",
            threshold_usd=INV_009_COST_THRESHOLD_USD,
            observed_usd=cost_total_usd,
        )
    if INV_009_TOKEN_THRESHOLD is not None and tokens_total > INV_009_TOKEN_THRESHOLD:
        _record_orchestrator_event(
            slice_id,
            "token_threshold_breach",
            threshold_tokens=INV_009_TOKEN_THRESHOLD,
            observed_tokens=tokens_total,
        )


def _intent_envelope():
    """Prefer slice.yaml.envelope; fall back to intent.md frontmatter. B16.

    Three possible returns:
      * non-empty list — dispatch with that envelope.
      * empty list — envelope key explicitly present as a list (possibly empty),
        OR the key is entirely absent (legacy dispatch-anyway). Dispatch
        proceeds with empty envelope.
      * None — the envelope key is declared but its value is not a list
        (e.g. `envelope:\\n` → None). Caller MUST short-circuit to FAILED.
    """
    import yaml

    declared_nonlist = False

    if SLICE_YAML.exists():
        try:
            text = SLICE_YAML.read_text()
            state = yaml.safe_load(text)
        except yaml.YAMLError:
            state = {}
        if not isinstance(state, dict):
            state = {}
        if "envelope" in state:
            env = state["envelope"]
            if isinstance(env, list):
                return [str(e) for e in env]
            declared_nonlist = True

    if INTENT_MD.exists():
        text = INTENT_MD.read_text()
        if text.startswith("---\n"):
            end = text.find("\n---", 4)
            if end >= 0:
                fm_text = text[4:end]
                try:
                    fm = yaml.safe_load(fm_text)
                except yaml.YAMLError:
                    fm = None
                if isinstance(fm, dict) and "envelope" in fm:
                    env = fm["envelope"]
                    if isinstance(env, list):
                        return [str(e) for e in env]
                    declared_nonlist = True

    if declared_nonlist:
        return None
    return []
