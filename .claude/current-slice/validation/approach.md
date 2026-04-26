# Phase 2 — Skeptic approach

## Ambiguities (resolved)

1. **`ts` format.** Spec: `isoformat()` → `+00:00`. t1b also accepts legacy `Z`; parses via `fromisoformat(ts.replace("Z","+00:00"))`.
2. **`count` for `redispatch_cap_exceeded`.** Stash carve: `redispatch_count.get(phase,0)+1` → 2 on the cap-tripping attempt. t2b asserts `count >= 2`.
3. **Cost / token threshold seam.** `INV_009_*` both `None` (`core.py:116-117`); no detection site today. Prior slice marked behavioural tests "encouraged" — the gap. Resolution: t2c/t2d bind via call-site presence — `event_type` token + helper invocation + required-field names (`threshold_usd`/`observed_usd`; `threshold_tokens`/`observed_tokens`). Same brittleness trade-off intent §Verification accepts for the prompt cluster. Phase 3 introduces a guarded detection hook; threshold values stay `None` (advisory-only per ADR cost-per-slice-budget).
4. **`agent_timeout` site.** `dispatch.py:174` `TimeoutExpired` catch. t2e pins by call-site presence + `timeout_seconds`.
5. **t4b "optional" marker.** Spec: same line or immediate framing. t4b accepts heading-line OR next non-empty line; canonical `## Learnings observed (optional)` passes.
6. **Loop termination in t2a/t2b.** Monkeypatch `close_slice` to no-op so RE_DISPATCH branch is exercised without sweep-notes/git wiring.

## Coverage map

- **t1a–d** — helper contract.
- **t2a/b** — lifecycle wiring; mirrors `test_redispatch_cap.py`. No subprocess.
- **t2c/d/e** — call-site presence for emissions whose detection seam is not cleanly mockable. Closes prior vacuous-GREEN gap.
- **t2f** — token-count >=6 (1 def + 5 sites) per §closes-when.
- **t3a** — `_ARTIFACT_RELPATHS` membership.
- **t3b** — events file archived byte-identically.
- **t3c** — F5-tolerance forward-compat (GREEN).
- **t4a/b** — heading + `optional` marker; the retry'''s gap-closing tests, brittleness explicitly accepted.

## Cluster RED discipline

Directly addresses the prior `cluster-no-RED-test` failure — every cluster has a RED progress signal beyond GREEN suite status:

- **`orchestrator-events`**: t1a–d, t2a–f, t3a–b.
- **`phase4-prompt-amendment`**: t4a, t4b.

## Confirmed RED

`uv run pytest tests/unit/test_orchestrator_events_capture.py tests/unit/test_phase_4_integrator_prompt.py -q` → **14 failed, 1 passed** (t3c forward-compat F5 guard). INV-008 / INV-003 untouched; stdlib-only.
