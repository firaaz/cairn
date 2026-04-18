#!/usr/bin/env bash
# render_status.sh — emit the five-line /status dashboard.
#
# Consumed by commands/claude-code/status.md. Reads CLAUDE_PROJECT_DIR (or
# current working directory) for slice.yaml, sweep.yaml, handoff.md, and
# features/*.yaml. Degrades every missing field to "—" rather than failing,
# so the renderer always exits 0 on a well-formed fixture even if the
# working tree is not a git checkout.
#
# Output ceiling: ≤1500 characters (INV-004 progressive-disclosure budget).

set -eu

ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
SLICE_YAML="$ROOT/.claude/current-slice/slice.yaml"
SWEEP_YAML="$ROOT/.claude/sweep.yaml"
HANDOFF_MD="$ROOT/.claude/handoff.md"
FEATURES_DIR="$ROOT/.claude/features"
VALIDATION_DIR="$ROOT/.claude/current-slice/validation"
INTEGRATION_DIR="$ROOT/.claude/current-slice/integration"

dash="—"

yaml_field() {
  sed -n "s/^$2:[[:space:]]*\(.*\)$/\1/p" "$1" 2>/dev/null \
    | head -n1 | tr -d '"' | tr -d "'" | awk '{$1=$1;print}'
}

phase_name_for_status() {
  case "$1" in
    1-intent|intent) echo "Intent" ;;
    2-validation|validation) echo "Validation" ;;
    3-implementation|implementation) echo "Implementation" ;;
    4-integration|integration) echo "Integration" ;;
    complete) echo "Complete" ;;
    failed) echo "Failed" ;;
    *) echo "$dash" ;;
  esac
}

phase_num_for_status() {
  case "$1" in
    1-intent|intent) echo "1" ;;
    2-validation|validation) echo "2" ;;
    3-implementation|implementation) echo "3" ;;
    4-integration|integration) echo "4" ;;
    *) echo "$dash" ;;
  esac
}

# --- Line 1: Slice / Phase / HEAD ------------------------------------------
slice_id="$dash"
phase_num="$dash"
phase_name="$dash"
head_sha="$dash"
if [ -f "$SLICE_YAML" ]; then
  sid=$(yaml_field "$SLICE_YAML" id); [ -n "$sid" ] && slice_id="$sid"
  ss=$(yaml_field "$SLICE_YAML" status)
  if [ -n "$ss" ]; then
    phase_num=$(phase_num_for_status "$ss")
    phase_name=$(phase_name_for_status "$ss")
  fi
fi
if command -v git >/dev/null 2>&1; then
  gs=$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || true)
  [ -n "$gs" ] && head_sha="$gs"
fi
printf 'Slice: %s · Phase: %s %s · HEAD: %s\n' "$slice_id" "$phase_num" "$phase_name" "$head_sha"

# --- Line 2: Last test run --------------------------------------------------
last_artifact=""
newest_mtime=0
for d in "$VALIDATION_DIR" "$INTEGRATION_DIR"; do
  [ -d "$d" ] || continue
  for f in "$d"/*; do
    [ -f "$f" ] || continue
    m=$(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f" 2>/dev/null || echo 0)
    if [ "$m" -gt "$newest_mtime" ] 2>/dev/null; then
      newest_mtime=$m
      last_artifact=$f
    fi
  done
done
if [ -n "$last_artifact" ]; then
  ts=$(date -r "$newest_mtime" '+%Y-%m-%d %H:%M' 2>/dev/null || echo "$newest_mtime")
  verdict="$dash"
  if grep -qi 'fail' "$last_artifact" 2>/dev/null; then
    verdict="fail"
  elif grep -qiE 'pass|ok|green' "$last_artifact" 2>/dev/null; then
    verdict="pass"
  fi
  printf 'Last test run: %s %s\n' "$ts" "$verdict"
else
  printf 'Last test run: %s\n' "$dash"
fi

# --- Line 3: Sweep ----------------------------------------------------------
sweep_state="$dash"
slices_since="$dash"
if [ -f "$SWEEP_YAML" ]; then
  last_sweep=$(yaml_field "$SWEEP_YAML" last-sweep-at-slice-id)
  interval=$(yaml_field "$SWEEP_YAML" sweep-interval)
  if command -v git >/dev/null 2>&1 && [ -n "$last_sweep" ] && [ "$last_sweep" != "null" ]; then
    count=$(git -C "$ROOT" log --oneline --grep='^slice: .* — complete$' 2>/dev/null | wc -l | tr -d ' ')
    slices_since="$count"
    if [ -n "$interval" ] && [ "$count" -ge "$interval" ] 2>/dev/null; then
      sweep_state="due"
    else
      sweep_state="up-to-date"
    fi
  else
    sweep_state="up-to-date"
    slices_since="0"
  fi
fi
printf 'Sweep: %s (%s slice-complete since last)\n' "$sweep_state" "$slices_since"

# --- Line 4: Features -------------------------------------------------------
features_line="$dash"
if [ -d "$FEATURES_DIR" ]; then
  pairs=""
  for f in "$FEATURES_DIR"/*.yaml; do
    [ -f "$f" ] || continue
    fid=$(yaml_field "$f" id)
    fname=$(yaml_field "$f" name)
    [ -n "$fid" ] || continue
    [ -n "$fname" ] || fname="$fid"
    entry="$fid:$fname"
    pairs=${pairs:+$pairs, }$entry
  done
  [ -n "$pairs" ] && features_line="$pairs"
fi
printf 'Features: %s\n' "$features_line"

# --- Line 5: Next -----------------------------------------------------------
next_line="$dash"
if [ -f "$HANDOFF_MD" ]; then
  nl=$(awk '
    /^## Next/ { capture=1; next }
    capture && /^## / { exit }
    capture && NF { print; exit }
  ' "$HANDOFF_MD" 2>/dev/null)
  [ -n "$nl" ] && next_line="$nl"
fi
printf 'Next: %s\n' "$next_line"
