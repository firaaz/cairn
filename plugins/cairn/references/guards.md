# Guard References

Codex plugins currently do not register Cairn hooks. The bundled Codex plugin exposes skills, workflow references, templates, scripts, and checks; it does not install runtime hook enforcement for Codex.

Guards are scripts/commands, not agent promises. When a workflow boundary calls for a guard, run the corresponding command and treat its output as evidence for that boundary.

The Claude plugin path remains hook-backed where supported. This reference describes the Codex plugin contract until Codex has a supported hook registration mechanism.

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

If a workflow says a hook would have enforced something in Claude, Codex must run the corresponding explicit guard command before crossing that workflow boundary.
