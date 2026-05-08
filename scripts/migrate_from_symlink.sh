#!/bin/bash
# shellcheck shell=bash
#
# scripts/migrate_from_symlink.sh
#
# Migration helper: takes a downstream consumer off the legacy
# `.slice-system -> cairn` symlink and onto the M5 plugin install path.
#
# Mechanical only — does NOT execute slash commands. The operator runs
# `/plugin marketplace add` and `/plugin install` after this script exits 0.
#
# Exit codes (per FLI-3 — protocol-level contract):
#   0  preflight passed; symlink unlinked; settings.json filtered; banner printed
#   2  quiescence failure (in-flight skill-run; Pre-mortem Scenario 6)
#   3  cairn-the-repo self-symlink detected (INV-011 / D8)
#
# Force overrides (asymmetric, dedicated env vars per refusal class):
#   CAIRN_MIGRATE_FORCE=1         bypasses exit 2 only (quiescence)
#   CAIRN_MIGRATE_BREAK_INV011=1  bypasses exit 3 only (cairn-self detection)
#
# POSIX-only surface (Bash 3.2 / dash compatible). No mapfile/readarray, no
# `[[`-extended-pattern matching, no GNU-only flags, no process substitution.

set -u

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

log_err() {
    # Print to stderr — POSIX-safe.
    printf '%s\n' "$*" >&2
}

log_out() {
    printf '%s\n' "$*"
}

print_banner() {
    log_out ""
    log_out "============================================================"
    log_out "Migration mechanical step complete. Next manual steps:"
    log_out "============================================================"
    log_out ""
    log_out "  1. /plugin marketplace add https://github.com/firaaz/cairn"
    log_out "  2. /plugin install cairn@cairn-marketplace"
    log_out "  3. Restart your Claude Code session (agent + hook registry"
    log_out "     reload requires a fresh session)."
    log_out "  4. Smoke test: re-run the post-install validator and"
    log_out "     dispatch a trivial cairn-tdd-feature run."
    log_out ""
}

# --------------------------------------------------------------------------
# Idempotent re-run guard
# --------------------------------------------------------------------------

if [ ! -e .slice-system ] && [ ! -L .slice-system ]; then
    log_out "Already migrated: .slice-system is absent. Nothing to do."
    print_banner
    exit 0
fi

# --------------------------------------------------------------------------
# Cairn-self detection (INV-011 / D8 — exit 3 default; CAIRN_MIGRATE_BREAK_INV011=1 override)
# --------------------------------------------------------------------------

is_cairn_self=0
if [ -L .slice-system ]; then
    link_target=$(readlink .slice-system)
    if [ "$link_target" = "." ]; then
        is_cairn_self=1
    fi
fi

if [ "$is_cairn_self" = "1" ]; then
    if [ "${CAIRN_MIGRATE_BREAK_INV011:-}" = "1" ]; then
        # Override path — emit a multi-line stderr block (>=3 lines) citing
        # INV-011, D8, and docs/ARCHITECTURE.md:91 by name. Then proceed.
        log_err "WARNING: CAIRN_MIGRATE_BREAK_INV011=1 — bypassing cairn-self refusal."
        log_err "  This violates INV-011 (cairn-the-repo bootstrap exception)."
        log_err "  ADR D8 of m5-plugin-distribution-and-symlink-retire forbids retiring"
        log_err "  cairn-the-repo's own .slice-system -> . self-symlink."
        log_err "  See docs/ARCHITECTURE.md:91 for the invariant prose."
        log_err "  Proceeding will unlink .slice-system and corrupt cairn-the-repo's"
        log_err "  self-consumption mechanism. This is intentional only if you are"
        log_err "  explicitly opting out of the bootstrap exception."
        # Fall through to the migration proper.
    else
        # Default refusal — exit 3, no state change. Stderr names INV-011, D8,
        # docs/ARCHITECTURE.md:91, and the literal env var name (so a typo'd
        # override is greppable in shell history per Risk Surface item 8).
        log_err "REFUSED: cairn-the-repo self-symlink detected (.slice-system -> .)."
        log_err "  This is INV-011 (the bootstrap exception). ADR D8 of"
        log_err "  m5-plugin-distribution-and-symlink-retire forbids retiring"
        log_err "  cairn-the-repo's own self-symlink via this helper."
        log_err "  See docs/ARCHITECTURE.md:91 for the invariant prose."
        log_err ""
        log_err "  If you are absolutely sure you want to corrupt cairn-the-repo's"
        log_err "  self-consumption mechanism, set CAIRN_MIGRATE_BREAK_INV011=1"
        log_err "  (note: CAIRN_MIGRATE_FORCE=1 alone does NOT bypass this refusal)."
        exit 3
    fi
fi

# --------------------------------------------------------------------------
# Quiescence preflight (Pre-mortem Scenario 6 — exit 2 default; CAIRN_MIGRATE_FORCE=1 override)
# --------------------------------------------------------------------------

non_quiesced=""
if [ -d .claude/skill-runs ]; then
    for run_dir in .claude/skill-runs/*/; do
        # Glob may yield literal `.claude/skill-runs/*/` if no matches — skip.
        if [ ! -d "$run_dir" ]; then
            continue
        fi
        if [ ! -f "${run_dir}integration/sweep-notes.md" ]; then
            non_quiesced="${non_quiesced}${run_dir}
"
        fi
    done
fi

if [ -n "$non_quiesced" ]; then
    if [ "${CAIRN_MIGRATE_FORCE:-}" = "1" ]; then
        log_err "WARNING: CAIRN_MIGRATE_FORCE=1 — bypassing quiescence preflight."
        log_err "  Pre-mortem Scenario 6: in-flight skill-run(s) detected without"
        log_err "  integration/sweep-notes.md. Proceeding will orphan in-flight"
        log_err "  dispatch state — the orphan-state risk is real."
        log_err "  Offending in-flight skill-run paths:"
        # Print each non-quiesced path on its own stderr line.
        printf '%s' "$non_quiesced" | while IFS= read -r p; do
            if [ -n "$p" ]; then
                log_err "    $p"
            fi
        done
        # Fall through to the migration proper.
    else
        log_err "REFUSED: in-flight skill-run detected (Pre-mortem Scenario 6)."
        log_err "  One or more .claude/skill-runs/<id>/ directories are missing"
        log_err "  integration/sweep-notes.md — those dispatches have not reached"
        log_err "  Phase 4 close. Migration mid-dispatch will orphan dispatch state."
        log_err "  Offending paths:"
        printf '%s' "$non_quiesced" | while IFS= read -r p; do
            if [ -n "$p" ]; then
                log_err "    $p"
            fi
        done
        log_err ""
        log_err "  Complete in-flight runs to Phase 4 first, or set"
        log_err "  CAIRN_MIGRATE_FORCE=1 to bypass (orphan-state risk acknowledged)."
        exit 2
    fi
fi

# --------------------------------------------------------------------------
# Migration proper
# --------------------------------------------------------------------------

# Step 1: unlink .slice-system (NOT rm -rf — the latter follows the symlink
# and deletes the target, which for a non-self symlink is the cairn checkout).
if [ -L .slice-system ]; then
    unlink .slice-system
fi

# Step 2: filter .claude/settings.json — drop any hook entry whose
# `command` field contains `$CLAUDE_PROJECT_DIR/.slice-system/`. Atomic
# write via .new + mv. The jq filter walks each hooks bucket
# (PreToolUse, PostToolUse, ...) and within each bucket each matcher's
# `hooks` array, dropping entries with the offending substring.
settings=".claude/settings.json"
if [ -f "$settings" ]; then
    if command -v jq >/dev/null 2>&1; then
        jq '
            if .hooks then
                .hooks |= with_entries(
                    .value |= map(
                        .hooks |= map(
                            select(
                                (.command // "")
                                | contains("$CLAUDE_PROJECT_DIR/.slice-system/")
                                | not
                            )
                        )
                    )
                )
            else . end
        ' "$settings" > "${settings}.new"
        mv "${settings}.new" "$settings"
    else
        log_err "WARNING: jq not on PATH; .claude/settings.json was NOT filtered."
        log_err "  Install jq and re-run the migration, or hand-edit settings.json"
        log_err "  to drop hook entries referencing \$CLAUDE_PROJECT_DIR/.slice-system/."
    fi
fi

# Step 3: success banner.
print_banner

exit 0
