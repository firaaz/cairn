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

if [ "$any_failed" -ne 0 ]; then
    exit 1
fi
exit 0
