---
id: codex-hook-parity
name: "Codex hook parity — automatic consumer enforcement via wrapper adapters"
status: accepted
contract:
  must-satisfy:
    - "codex plugin adapters mirror the claude-code hook surface (carrier: tests/unit/test_codex_hook_adapters.py + test_codex_plugin_manifest.py)"
  evidence:
    - "tests/unit/test_codex_hook_adapters.py passes"
firmness: provisional
supersedes: null
superseded-by: null
topic: architecture
invariants-touched: []
date: 2026-06-01
---

# Codex hook parity — automatic consumer enforcement via wrapper adapters

## Status

Accepted, provisional. This changes the Codex consumer contract from
"skills plus explicit guard commands" to "skills plus hook-backed enforcement
where Codex supports plugin hooks." The Claude hook surface remains unchanged.

## Date

2026-06-01

## Context

Cairn already ships three consumer-facing Claude enforcement hooks:
`reversibility-guard.sh`, `role_guard.py`, and `reality-check.sh`. The Codex
plugin initially exposed only skills, references, templates, and explicit guard
commands. That posture was honest while Codex hook registration was not part of
the plugin contract, but it left Codex consumers with a weaker default: the
agent had to remember to run guards manually at workflow boundaries.

Codex can now carry a plugin hook registration. The mechanical payloads are not
Claude payloads, especially for `apply_patch`: one tool call may touch multiple
files and has patch text rather than a single `file_path` plus `old_string`.
Changing the Claude hook scripts directly would couple two hosts with different
tool shapes and risk regressing the already-shipped Claude path.

The `using-cairn` SessionStart carrier is a different mechanism. It is a
navigation/orientation aid for Cairn dogfood, not one of the three enforcement
guards. `using-cairn-carrier-contract` D6 keeps it Cairn-internal until a future
distribution ADR promotes it.

## Decision

**D1 — Codex hooks become consumer contract.** The Codex plugin declares a
`hooks` manifest. Consumers who install and trust the Cairn Codex plugin get
automatic enforcement for the current three enforcement classes: reversible
shell operations, write-envelope/ADR/env/lock-file checks for `apply_patch`, and
Python reality checks after `apply_patch`.

**D2 — Wrapper adapters are the compatibility boundary.** Codex hook entries
invoke `plugins/cairn/checks/codex_pretool_guard.py` and
`plugins/cairn/checks/codex_posttool_reality.py`. The existing Claude scripts
remain the behavior reference and are not edited for Codex payload shapes.
Adapters normalize Codex and Claude-like payload keys defensively, then enforce
the Codex surface directly.

**D3 — PreToolUse coverage.** The Codex PreToolUse adapter covers shell command
tools and `apply_patch`. Shell commands retain the destructive-operation deny
set from `reversibility-guard.sh`: recursive force deletes, `git reset --hard`,
plain force-push, `git clean -fd`, and database drops. `--force-with-lease`
remains allowed. `apply_patch` is checked per touched file and denies the whole
patch if any file violates policy.

**D4 — Write policy for `apply_patch`.** The adapter blocks edits to env files
and lock files. Existing ADR bodies remain append-only: frontmatter-only edits
to `status:`, `superseded-by:`, `superseded_by:`, or `firmness:` are allowed;
body changes require a superseding ADR. The adapter also enforces
`.claude/active-envelope.yaml` in `mode: operator` when no role-specific
environment is set, using repo-relative paths from the patch.

**D5 — PostToolUse coverage.** The Codex PostToolUse adapter extracts Python
files touched by `apply_patch` and applies the existing reality-check behavior:
`ruff format --quiet` followed by `ruff check --fix --quiet`, skipped when the
file no longer exists or `ruff` is unavailable.

**D6 — Claude hooks stay stable.** `.claude-plugin/hooks-template.json`,
`checks/reversibility-guard.sh`, `checks/role_guard.py`, and
`checks/reality-check.sh` keep their existing Claude-facing contract. Shared
bugs may still be fixed in shared scripts, but Codex payload normalization does
not belong there.

**D7 — Carrier remains Cairn-internal in this slice.** This ADR does not ship a
consumer SessionStart carrier through `plugins/cairn/hooks/hooks.json`. Cairn's
own repository may dogfood a repo-local `.codex/hooks.json` SessionStart entry,
but that file is not part of the Codex plugin payload.

## Consequences

### Easier

- Codex consumers get mechanical enforcement by default instead of a documented
  manual guard habit.
- Claude and Codex host differences are isolated in small adapters.
- Multi-file `apply_patch` calls fail atomically when any touched path violates
  env, lock-file, ADR, or envelope policy.

### Harder

- Codex hook behavior now has its own adapter test surface.
- Shell write-path parsing remains intentionally narrow: this slice checks
  destructive shell commands, not arbitrary Bash file writes.
- Consumers must review and trust plugin hook registration during install.

## Alternatives Considered

- **Keep Codex explicit-only.** Rejected. It preserves the weakest consumer
  posture even when hook registration is available.
- **Reuse Claude hook scripts directly.** Rejected. `apply_patch` does not map
  cleanly to Claude `Write`/`Edit` payloads, and multi-file patches need
  whole-call denial.
- **Ship the `using-cairn` carrier to Codex consumers now.** Rejected for this
  slice. The carrier is orientation, not enforcement, and its consumer
  distribution is governed by `using-cairn-carrier-contract` D6/D7.
