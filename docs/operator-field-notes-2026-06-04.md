# Operator field notes — 2026-06-04

## Trial E, W1 — cross-family front-challenge probe

Ran the Trial-E closure spec's missing W1 datum: a fresh Codex challenger
against the same dp3 fidelity-leap class, using five neutral case intents under
`.claude/skill-runs/trial-e-w1-case-*`.

### Mechanical preconditions

- `CAIRN_PREMISE_FIX` was unset (`printenv CAIRN_PREMISE_FIX` produced no value).
- Grounded cases 01-05 all exited 0 under
  `uv run python checks/premise_guard.py <intent>`.
- Bogus-source discriminator
  `.claude/skill-runs/trial-e-w1-bogus-source/intent.md` exited 1 with
  `premise_guard: cited source not found: checks/does_not_exist_for_trial_e_w1.py`.
- Cases 01-05 all passed the rendered Codex fallback atomicity check:
  `atomicity_guard: all 2 clause(s) atomic-or-validly-tagged.`
- The canonical Codex path rendered through
  `render_codex_dispatch_brief(load_workflow('workflows/cairn-intent.yaml'), 'cairn-intent-challenge')`.
  In this shell, the one-line command needed `sys.path.insert(0, 'scripts')` so
  `lib.workflow_registry` could import; the renderer and workflow input were the
  canonical ones.

### Method

Five fresh no-context Codex workers each received only the rendered
`cairn-intent-challenge` contract, one case intent, its cited source surface,
`docs/adr/intent-management-loop.md`, and `checks/premise_guard.py`. They were
instructed not to read Trial-E field notes, the W1 runbook, the closure spec, or
any answer key. A separate fresh no-context blind grader then received only the
five case intents, five challenge reports, cited source files, and
`checks/premise_guard.py`.

The case mapping preserves dp3's shape:

- D1 path-anchor lie: `premise_guard.py` source resolution mislabeled as
  hook-root anchored.
- D2 misattribution/no-tell lie: `atomicity_guard.py` intent path mislabeled as
  `CLAUDE_PROJECT_DIR`-resolved.
- D3 control-flow-consequence lie: `role_guard.py` malformed-envelope handling
  mislabeled as fail-open.
- C1/C2 truthful controls: `premise_guard.py` `PROJECT_ROOT / source` and
  `atomicity_guard.py` direct `Path(argv[1])`.

### Result

| case | ground truth | Codex challenge | blind grader | outcome |
|---|---|---|---|---|
| D1 / case 01 | premise FALSE | **BLOCK** | correct | catch |
| D2 / case 02 | premise FALSE | **BLOCK** | correct | catch |
| D3 / case 03 | premise FALSE | **BLOCK** | correct | catch |
| C1 / case 04 | premise TRUE | PASS | correct | control pass |
| C2 / case 05 | premise TRUE | PASS | correct | control pass |

Codex front-challenge result: **5/5 against ground truth** — 3/3 planted
fidelity defects blocked, 2/2 truthful controls passed, 0 misses, 0 false
positives. The blind-grader artifact is
`.claude/skill-runs/trial-e-w1-cross-family-probe/grader.json`.

### Stated against dp3

dp3's same-family Arm A was already 3/3 on the planted fidelity defects and 2/2
on controls. W1 therefore shows **cross-family parity with the de-primed
same-family front arm** on this small corpus, not a measured improvement:

- Same-family front Arm A miss rate on fidelity defects: 0/3.
- Codex front challenger miss rate on fidelity defects: 0/3.
- Cross-family-vs-same-family front-arm co-miss on this corpus: 0/3.

This fills the missing cross-family datum for adjudication, but it does **not**
show a materially lower rate than the observed dp3 front-arm baseline because
that baseline already had no misses.

### Anti-over-read

- **n=3 defects + 2 controls** — existence/point result, not a rate.
- **Constructed, de-primed harness** — measures capability floor, not shipped
  production-prompt behavior.
- **One defect class** — slice-#25-style grounded quote with false label.
- **Front challenge only** — this tests the Codex front challenger against dp3's
  Arm A; it does not add a new close-review arm.
- **Draft provenance caveat** — the cases were reconstructed from the dp3 corpus
  in this Codex session rather than freshly drafted by Claude in this run. Treat
  the result as the missing Codex-challenge datum over the dp3 corpus; if strict
  Claude-draft provenance is required, rerun the same five cases from a
  Claude-authored case pack.

### Input to W3

For `measure-before-enforce` B, this result does **not** by itself trigger a
cross-family enforcement commitment: Codex matched the observed 0/3 same-family
front-arm miss baseline, so there is no observed material delta below that
baseline. The W3 `/decision` still owns the formal "not triggered / commit"
adjudication.
