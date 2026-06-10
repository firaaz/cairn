# Cairn — Roadmap

*Re-anchored by `carrier-hierarchy-and-process-diet` (2026-06-10). The minimal mechanism set is: the cairn-intent loop with its two fresh-context checkpoints, `premise_guard.py`, the three liveness-tested hooks (`role_guard.py`, `reversibility-guard.sh`, `reality-check.sh`) plus the `using-cairn` carrier, the contract tests, and the validator. Everything here either measures that set or serves consumers of it. Work items live as gh issues; this file holds direction.*

## 1. Measure the production gate (top item)

Every "front gate works" datum so far used de-primed stand-ins; the shipped `intent-challenge` agent brief hard-codes the slice-#25 example (priming). De-prime the production brief and gather live, non-planted catch data across real intents. Until this lands, the loop's central empirical claim rests on stand-ins. Receipts to date (including this refocus's own five-round challenge: four real catches, one of them session-bricking) suggest the gate earns its cost — the measurement should confirm it without the training wheels.

## 2. Consumer surface

- Symlink validation / hook-installer doctor (gh#19), upgrade-doc ecosystem (gh#20), slash-command doc drift (gh#21).
- v0.1.0 release verification: tag converged; release smoke still unverified (handoff thread a18bca0).
- role_guard repair propagation note: consumers pulling past the gh#35 fix get *real* envelope enforcement — audit `active-envelope.yaml` before pulling (carrier-hierarchy-and-process-diet D4).

## 3. Kept-machinery defects

- gh#7 — role_guard Bash write-class parsing (heredoc gap).
- Anything surfaced by the liveness suite (`scripts/smoketest_hooks.sh` via pytest).

## 4. Codex parity

Codex plugin adapters + manifest tests are on dev (handoff thread 61afec4); keep the two `cairn-intent` surfaces (Claude Code skill, Codex plugin) agreeing on node ids and verdict statuses (`codex-hook-parity` contract).

## Gated

- **Agent-managed planning substrate** — was gated on knowledge-substrate Slices 1+2; the substrate retired (`cairn-substrate-and-fastmcp-superseded`), so this now requires a fresh decision (lean form) before any credentialed external dependency.
- **Concurrent-feature lifecycle** (`git-workflow-v1` D4/D5) — fires on the first real concurrent feature; until then single-feature `--no-ff` flow stands.

## Not now

Jira/Confluence integration, package-manager distribution, agent integrations beyond Claude Code + Codex, dependency-graph automation, cross-family verification automation. The pre-M4 slice/orchestrator roadmap (protocol extraction, state.json catchup, Windsurf port, dogfood-log infrastructure) is retired with its machinery — history in git.
