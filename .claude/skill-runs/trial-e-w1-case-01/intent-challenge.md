# Intent Challenge Report

Registry: `cairn-intent`
Stage: `cairn-intent-challenge`
Intent: `.claude/skill-runs/trial-e-w1-case-01/intent.md`
Verdict: blocked

## premise-source-checks

### P1

Premise label: "premise source paths are resolved through the guard's hook-root anchor"

Source path: `checks/premise_guard.py`

Mechanical quote check: pass. The cited quote is live at `checks/premise_guard.py:98-100`:

```python
        source = premise.get("source")
        quote = premise.get("quote")
        resolved = PROJECT_ROOT / source
```

The project guard also accepts the intent when run from the repository root:

```text
uv run python checks/premise_guard.py .claude/skill-runs/trial-e-w1-case-01/intent.md
exit 0
```

Semantic source check: fail. The cited lines do not show a hook-root anchor. They show that premise sources are resolved through `PROJECT_ROOT`. The live definition and adjacent comment define that root as the environment project directory or invocation working directory, not the guard script root:

```python
PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
# Premise `source` paths resolve against PROJECT_ROOT (the consumer cwd); the
# shared matcher ships beside this script, so import it from cairn's own root -
# the two roots diverge when cairn is consumed downstream.
_CAIRN_ROOT = Path(__file__).resolve().parent.parent
```

Evidence:

- `checks/premise_guard.py:22` defines `PROJECT_ROOT` from `CLAUDE_PROJECT_DIR` or `os.getcwd()`.
- `checks/premise_guard.py:23-25` explicitly describes premise `source` resolution as `PROJECT_ROOT` / consumer cwd and distinguishes it from Cairn's own root.
- `checks/premise_guard.py:26` defines `_CAIRN_ROOT` from `__file__`, which is the script/hook-root-style anchor.
- `checks/premise_guard.py:27-28` use both roots only for import lookup, not for resolving premise sources.
- `checks/premise_guard.py:100` resolves cited premise sources as `PROJECT_ROOT / source`.
- `checks/premise_guard.py:101-107` preserves missing-source and unreadable-source failures after that `PROJECT_ROOT` resolution.

The ADR requires the front challenge to attack intent premises against live source before construction (`docs/adr/intent-management-loop.md:61-62`) and makes the slice-#25-style counterfactual blocking behavior an acceptance gate (`docs/adr/intent-management-loop.md:88-90`, `docs/adr/intent-management-loop.md:100-103`). This premise is mechanically grounded but semantically inverted.

## semantic-counterfactual-search

Attempted stale-docstring / wrong-model counterfactual:

```yaml
premises:
  - source: checks/premise_guard.py
    quote: |
      source = premise.get("source")
      quote = premise.get("quote")
      resolved = PROJECT_ROOT / source
    label: "premise source paths are resolved through the guard's hook-root anchor"
```

Result: this counterfactual passes verbatim grounding because the quoted lines are present. It contradicts live behavior because `PROJECT_ROOT` is the consumer project or cwd root, while `_CAIRN_ROOT` is the guard/script root. The current intent already has this shape, so construction would proceed from a wrong model of the source unless blocked here.

Related wrong-model risk: an intent could propose to "preserve" hook-root source resolution while actually changing current behavior from consumer-root resolution to hook-root resolution. The missing-source and unreadable-source checks would still exist, but they would run against a different root and therefore would not preserve the current failure surface for downstream consumers.

## verdict

Blocked.

Challenged premises:

- P1: "premise source paths are resolved through the guard's hook-root anchor"

Required intent revision:

Revise the intent so its premise and contract state the live behavior accurately: premise `source` paths currently resolve through `PROJECT_ROOT`, where `PROJECT_ROOT` is `CLAUDE_PROJECT_DIR` or `os.getcwd()`, not `_CAIRN_ROOT` / the guard script root. If the intended change is to move source resolution to the hook-root anchor, describe it as a behavior change rather than preservation, and explicitly specify how missing-source and unreadable-source failures should behave under the new root.
