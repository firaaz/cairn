#!/usr/bin/env bash
# prepare-commit-msg: prepend per-phase cairn template to the commit buffer
# when the active slice is in a pipeline phase. Silent no-op otherwise —
# never blocks `git commit`.
#
# Git contract: $1 is the path to the commit-message buffer.
# Activation: point core.hooksPath at checks/ (or shim from .git/hooks/).

set -eu

buffer="${1:-}"
[ -n "$buffer" ] || exit 0
[ -f "$buffer" ] || exit 0

project_dir="${CLAUDE_PROJECT_DIR:-$PWD}"
slice_yaml="$project_dir/.claude/current-slice/slice.yaml"

[ -f "$slice_yaml" ] || exit 0

status_line="$(grep -E '^status:' "$slice_yaml" 2>/dev/null | head -n 1 || true)"
[ -n "$status_line" ] || exit 0

status="${status_line#status:}"
status="${status# }"
status="${status%"${status##*[![:space:]]}"}"
status="${status#\"}"
status="${status%\"}"
status="${status#\'}"
status="${status%\'}"

case "$status" in
    1-intent|intent)         phase=1 ;;
    2-validation|validation) phase=2 ;;
    3-implementation|implementation) phase=3 ;;
    4-integration|integration) phase=4 ;;
    *) exit 0 ;;
esac

template="$project_dir/.gitmessage-phase-${phase}"
[ -f "$template" ] || exit 0

existing="$(cat "$buffer")"
{
    cat "$template"
    printf '\n'
    printf '%s' "$existing"
} > "$buffer.cairn-tmp"
mv "$buffer.cairn-tmp" "$buffer"

exit 0
