# Intent Challenge: trial-e-w1-case-02

Stage: `cairn-intent-challenge`
Registry: `cairn-intent`
Role: intent-challenger
Verdict: blocked

## Scope

Inspected only:

- `.claude/skill-runs/trial-e-w1-case-02/intent.md`
- `checks/atomicity_guard.py`
- `docs/adr/intent-management-loop.md`
- `checks/premise_guard.py`

No construction or close work was performed.

## Premise Source Checks

### P1 - `checks/atomicity_guard.py`

Intent citation:

- Source: `checks/atomicity_guard.py`
- Quoted line in intent: `intent_path = Path(argv[1])`
- Label in intent: "the intent argument is resolved under CLAUDE_PROJECT_DIR before readability checks"

Mechanical grounding:

- The quoted line is live at `checks/atomicity_guard.py:108`.
- The readability check immediately uses that raw `Path(argv[1])` value at `checks/atomicity_guard.py:109`.
- The file read immediately uses the same raw path at `checks/atomicity_guard.py:113`.

Semantic challenge:

- The live implementation does not resolve the intent argument under `CLAUDE_PROJECT_DIR`.
- `checks/atomicity_guard.py` contains `CLAUDE_PROJECT_DIR` only in a comment at `checks/atomicity_guard.py:22`; there is no executable project-root binding analogous to `PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())`.
- The premise label claims the opposite of the cited live code. `Path(argv[1])` reads the CLI argument directly and remains relative to the caller's current working directory.

Contract impact:

- The intent's `wrong-if` says the intent is wrong if "the cited source line reads the CLI argument directly rather than resolving it under CLAUDE_PROJECT_DIR".
- That wrong-if condition is satisfied by the live cited source.
- The specification says to "Preserve project-root-relative intent argument resolution", but the live source has no such behavior to preserve.

## Support File Checks

`checks/premise_guard.py` supports project-root resolution for premise `source` paths, not for its own intent argument:

- `checks/premise_guard.py:22` defines `PROJECT_ROOT` from `CLAUDE_PROJECT_DIR` or `cwd`.
- `checks/premise_guard.py:100` resolves premise source paths as `PROJECT_ROOT / source`.
- `checks/premise_guard.py:132` still reads its own intent argument as `Path(sys.argv[1])`.

So the allowed comparison file does not support the intent's claim that authoring-time guards generally resolve the intent argument under `CLAUDE_PROJECT_DIR`. It supports a narrower model: premise source citations are project-root-relative.

`docs/adr/intent-management-loop.md` requires this challenge to catch semantic misreads:

- `docs/adr/intent-management-loop.md:40` identifies the semantic-misread gap as serious and fixed by a front-loaded challenge.
- `docs/adr/intent-management-loop.md:61` says the front-loaded intent-challenge attacks premises against live source before construction.
- `docs/adr/intent-management-loop.md:88` says the slice-#25 counterfactual must block at the front-challenge.

## Semantic Counterfactual Search

Attempted stale-docstring/wrong-model counterfactual:

- A stale or wrong-model intent could quote `intent_path = Path(argv[1])` verbatim.
- That quote would be mechanically grounded because it is present at `checks/atomicity_guard.py:108`.
- The same intent could label the quote as `CLAUDE_PROJECT_DIR` resolution, even though the implementation performs direct CLI-path resolution.
- A verbatim-only grounding guard would pass that premise while the semantic claim contradicts live behavior.

This is a slice-#25-style failure mode: the premise is textually grounded but semantically false.

## Verdict

Blocked.

Challenged premise ids:

- P1

Blocking evidence:

- `checks/atomicity_guard.py:108` assigns `intent_path = Path(argv[1])`.
- `checks/atomicity_guard.py:109` checks readability on that raw path.
- `checks/atomicity_guard.py:113` reads that raw path.
- `checks/atomicity_guard.py:22` is only a comment mentioning `CLAUDE_PROJECT_DIR`; no executable resolution exists in the inspected guard.
- `checks/premise_guard.py:22` and `checks/premise_guard.py:100` resolve premise source paths under `PROJECT_ROOT`, while `checks/premise_guard.py:132` reads its own intent argument directly.
- `.claude/skill-runs/trial-e-w1-case-02/intent.md:41` declares the current live behavior as wrong-if.

Required intent revision:

Revise the intent so P1 and the contract state the live baseline accurately: `checks/atomicity_guard.py` currently reads the intent argument directly with `Path(argv[1])`, relative to the caller's current working directory. If the desired cleanup is to resolve relative intent arguments under `CLAUDE_PROJECT_DIR`, describe that as a behavior change, not as preservation of existing project-root-relative intent-argument resolution, and cite live source that supports any comparison to other guards.
