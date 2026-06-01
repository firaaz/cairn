# Guard References

Codex plugin registers automatic hooks for Cairn's current enforcement surface where Codex supports it. The bundled Codex plugin exposes skills, workflow references, templates, scripts, checks, and hook adapters for shell command and `apply_patch` events.

Guards are hook-backed where supported and script-backed as fallback. Hook denials are boundary evidence when the host has loaded and trusted the plugin hook manifest. Explicit guard commands remain the manual fallback for unsupported hosts, hook-trust review gaps, and non-hooked checks such as premise and atomicity gates.

The Claude plugin path remains hook-backed where supported. Claude hooks use the existing scripts directly; Codex hooks use wrapper adapters because Codex `apply_patch` payloads can touch multiple files in one tool call.

Known limitations:

- Codex write-envelope enforcement focuses on `apply_patch`, the primary Codex edit surface.
- Shell hooks block destructive command patterns; they do not parse arbitrary Bash writes such as redirects, `tee`, or heredocs.
- The `using-cairn` SessionStart carrier is not shipped through the Codex plugin hook manifest.

## Repo Commands

From this repo, use the repo paths:

```bash
uv run python checks/premise_guard.py <intent.md>
uv run python checks/atomicity_guard.py <intent.md>
uv run python scripts/validate_architecture.py
```

## Bundled Plugin Commands

From the bundled Codex plugin payload, use the plugin paths:

```bash
uv run python plugins/cairn/checks/premise_guard.py <intent.md>
uv run python plugins/cairn/checks/atomicity_guard.py <intent.md>
uv run python plugins/cairn/scripts/validate_architecture.py
```

## Reversibility

For reversibility checks, pass a tool-call JSON payload on stdin:

```bash
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"<candidate command>"}}' | bash checks/reversibility-guard.sh
```

## Write Envelope

For write-envelope checks, prefer the active intent or `.claude/active-envelope.yaml`. Use `checks/role_guard.py` only with a concrete tool-call JSON payload and the intended `AGENT_ROLE` or operator envelope environment.

## Boundary Rule

If automatic hooks are active, their allow/deny result is evidence for the corresponding boundary. If hooks are unavailable or the boundary is not hook-backed, run the corresponding explicit guard command before crossing that workflow boundary.
