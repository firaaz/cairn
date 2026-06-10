#!/usr/bin/env bash
# Smoketest cairn's checks/*.py hooks under the system python3.
#
# Why: M4 shipped a regression where a top-level `import yaml` in
# checks/role_guard.py crashed any consumer invoking the hook via bare
# `python3` (no uv, no venv). The pytest suite missed it because it runs
# inside `uv run pytest`. This script reproduces a downstream consumer's
# invocation path: the python3 resolved by `command -v python3`, with no
# project venv on PATH.
#
# Per-hook PASS/FAIL is determined purely by whether the hook's import phase
# raises (ModuleNotFoundError / ImportError / SyntaxError on stderr). Non-zero
# exit codes from legitimate runtime behaviour (e.g., role_guard.py exiting 2
# on malformed stdin) are not treated as failures.

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CHECKS_DIR="$REPO_ROOT/checks"

PYTHON3="$(command -v python3 || true)"
if [ -z "$PYTHON3" ]; then
    echo "ERROR: python3 not found on PATH" >&2
    exit 1
fi

if [ ! -d "$CHECKS_DIR" ]; then
    echo "ERROR: checks directory not found: $CHECKS_DIR" >&2
    exit 1
fi

shopt -s nullglob 2>/dev/null || true

any_failed=0
hook_count=0

for hook in "$CHECKS_DIR"/*.py; do
    hook_count=$((hook_count + 1))
    base="$(basename "$hook")"

    err="$("$PYTHON3" "$hook" </dev/null 2>&1 >/dev/null || true)"

    if echo "$err" | grep -qE 'ModuleNotFoundError|ImportError|SyntaxError'; then
        echo "FAIL $base"
        echo "$err" >&2
        any_failed=1
    else
        echo "PASS $base"
    fi
done

if [ "$hook_count" -eq 0 ]; then
    echo "ERROR: no checks/*.py hooks found in $CHECKS_DIR" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Liveness (INV-013 D8): an enforcer without a test that proves it BLOCKS a
# known-bad input is documentation. Each surviving hook is fed a known-bad
# input and must respond — deny (blocking exit code / deny decision) for the
# enforcers, corrective action for reality-check, marker emission for the
# carrier. role_guard's gh#35 lesson: assert the ALLOW direction too, with an
# absolute path, so the deny assertion can't be satisfied by deny-everything.
# ---------------------------------------------------------------------------

# role_guard's envelope path needs pyyaml; prefer the project interpreter.
if command -v uv >/dev/null 2>&1 && [ -f "$REPO_ROOT/pyproject.toml" ]; then
    RG_PY=(uv run --project "$REPO_ROOT" python)
else
    RG_PY=("$PYTHON3")
fi

LIVE_TMP="$(mktemp -d)"
trap 'rm -rf "$LIVE_TMP"' EXIT
mkdir -p "$LIVE_TMP/.claude" "$LIVE_TMP/docs"
printf 'mode: operator\npaths:\n  - ^docs/\n' > "$LIVE_TMP/.claude/active-envelope.yaml"

live_fail() {
    echo "FAIL liveness $1" >&2
    any_failed=1
}

# role_guard: known-bad write blocked (exit 2)
rc=0
printf '%s' '{"tool_name":"Write","tool_input":{"file_path":"secrets/evil.txt"}}' \
    | CLAUDE_PROJECT_DIR="$LIVE_TMP" AGENT_ROLE= "${RG_PY[@]}" "$CHECKS_DIR/role_guard.py" >/dev/null 2>&1 || rc=$?
if [ "$rc" -eq 2 ]; then
    echo "PASS liveness role_guard.py deny"
else
    live_fail "role_guard.py deny (expected exit 2, got $rc)"
fi

# role_guard: known-good ABSOLUTE in-envelope write allowed (exit 0)
rc=0
printf '%s' "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$LIVE_TMP/docs/ok.md\"}}" \
    | CLAUDE_PROJECT_DIR="$LIVE_TMP" AGENT_ROLE= "${RG_PY[@]}" "$CHECKS_DIR/role_guard.py" >/dev/null 2>&1 || rc=$?
if [ "$rc" -eq 0 ]; then
    echo "PASS liveness role_guard.py allow-absolute"
else
    live_fail "role_guard.py allow-absolute (expected exit 0, got $rc)"
fi

# reversibility-guard: force-push payload denied (exit 2 + deny decision)
rc=0
out="$(printf '%s' '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"}}' \
    | bash "$CHECKS_DIR/reversibility-guard.sh" 2>/dev/null)" || rc=$?
if [ "$rc" -eq 2 ] && printf '%s' "$out" | grep -q '"permissionDecision": *"deny"'; then
    echo "PASS liveness reversibility-guard.sh deny"
else
    live_fail "reversibility-guard.sh deny (expected exit 2 + deny decision, got $rc)"
fi

# reality-check: known-bad (unformatted) Python file gets reformatted
printf 'x=1\n' > "$LIVE_TMP/bad.py"
printf '%s' "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$LIVE_TMP/bad.py\"}}" \
    | bash "$CHECKS_DIR/reality-check.sh" >/dev/null 2>&1 || true
if grep -q 'x = 1' "$LIVE_TMP/bad.py"; then
    echo "PASS liveness reality-check.sh reformat"
else
    live_fail "reality-check.sh reformat (file not reformatted)"
fi

# using-cairn-carrier: fires its marker, never gates
rc=0
out="$(printf '%s' '{}' | CLAUDE_PROJECT_DIR="$REPO_ROOT" bash "$CHECKS_DIR/using-cairn-carrier.sh" 2>/dev/null)" || rc=$?
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q 'CAIRN_CARRIER_FIRED'; then
    echo "PASS liveness using-cairn-carrier.sh fired"
else
    live_fail "using-cairn-carrier.sh fired (exit $rc)"
fi

if [ "$any_failed" -ne 0 ]; then
    exit 1
fi
exit 0
