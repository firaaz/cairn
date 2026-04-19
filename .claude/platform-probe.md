---
slice: compression/infrastructure
date: 2026-04-19
phase: 3-implementation
purpose: V8 evidence — Pre-Task 0 platform probe per intent.md §5
---

## `claude -p --agent <role>` invocation

**Status:** confirmed working as assumed by intent.md.

`claude --help` (CLI version 2.1.114) lists both flags as separate, composable
options:

- `-p, --print` — "Print response and exit (useful for pipes). Note: The
  workspace trust dialog is skipped when Claude is run with the -p mode."
- `--agent <agent>` — "Agent for the current session. Overrides the 'agent'
  setting."

No alternative spelling (`--subagent`, `--role`) appears in the help output.
The orchestrator may invoke
`subprocess.run(["claude", "-p", "--agent", role, json.dumps(inputs)], ...)`
exactly as specified in intent.md §2 `dispatch_agent`.

Adjacent flags worth noting (informational; not blocking):

- `--agents <json>` accepts inline agent definitions, an escape hatch if a
  per-slice agent override is ever needed.
- `--bare` skips hooks/MCP/keychain and is useful for hermetic dispatch but is
  *not* used by the orchestrator (we want hooks active so `role_guard.py`
  fires inside the spawned session).
- `--allow-dangerously-skip-permissions` exists; the orchestrator never sets
  it.

## `tools:` frontmatter mechanical enforcement

**Status:** deferred — write-denial empirical check requires a live agent
dispatch, which is Slice B's dogfood.

The intent's probe asks for a "write-denial test" against a `tools:`
frontmatter that omits `Write`. Slice A ships role agent definitions whose
`tools:` arrays are *declared* per intent.md §3, but `AGENT_ROLE` is unset
during Slice A's own phases (intent.md §"What and Why" para 2), so the
spawned-session round-trip cannot be exercised here without manually invoking
`claude -p --agent` outside the slice pipeline. Doing so inside Slice A would
expand the envelope.

The compensating control is `checks/role_guard.py` — the inner gate operates
on the same write tools regardless of whether the outer `tools:` gate fires.
Slice B's first compressed dispatch is the empirical check on the outer gate;
if it fails, role_guard.py still denies the write, and the failure is
recoverable.

## Conclusion

No PAUSE/escalate condition triggered. Proceeding with implementation per the
intent as written.
