# Efficiency Program Part 8 — Compression Audit (Empirical)

**Date:** 2026-04-25
**Status:** Audit complete (N=1 slice). Replaces the unmeasured assumptions in Part 7 §10.9 with measured data. **Revised 2026-04-25 (post-operator-review):** added hexagonal-architecture framing for both docs and code (§4–§6), elevated per-slice orientation (M0), API digests (M0.5), doc-port layer (H1), and orchestrator package split (H2) above the original mechanical-intervention list, plus testing-side levers (H4–H5). New §10 recommends a sequencing of H2 → M0 → M0.5/M3/S3 → H1, with explicit counterarguments in §11.
**Series:** docs/plans/2026-04-18-efficiency-program (extends Parts -1 through 7)
**Trigger:** Part 7 `/decision` aborted at Phase 3 on operator critique that the §10.8 governance primitive is one abstraction layer above what's actually expensive. This audit measures *where the cost is* before structural commitments.
**Method:** Parse `.claude/orchestrator-debug/*.log` (claude `-p` stream-json output) → extract per-event `usage` data → aggregate per phase, per slice. Parser at `/tmp/cairn_audit_parse.py`.

---

## 1. Sample

**N=1 fully-instrumented slice:** `cost-discipline/lever-1-per-phase-model` (closed `23f1db0`, 2026-04-24).

Older slices (compression/*, cost-discipline/track-0-telemetry) only have `result:` summary lines in their logs — the full event stream was not yet captured at dispatch time. Track-0-telemetry's `<slug>-result.json` instrumentation lands its first-fire on the *next* slice; at write-time of this audit, no `result.json` files exist yet. This audit is therefore an N=1 case study; cross-slice generalization needs at least two more measured slices.

The lever-1 slice is moderately representative: 4 phases, 1 RAISE_ISSUE → re-dispatch loop in Phase 4 (per L-008/L-009 incident), Phase 3 ran 4 successful builder invocations across clusters. Sample contains both a clean phase (Phase 1) and a problem phase (Phase 4 had the empty-handoff cascade).

---

## 2. Measured per-phase totals

All values from `assistant`-event `usage` fields summed across each phase's invocations. Models per Lever-1 config: P1/P2 = `claude-opus-4-7`, P3/P4 = `claude-sonnet-4-6`.

| Phase | Invocations | Turns | input_tokens | cache_creation | cache_read | output_tokens | TOTAL routed |
|---|---|---|---|---|---|---|---|
| **1 writer** (opus-high) | 1 | 27 | 33 | 105,951 | 636,388 | 324 | **742,696** |
| **2 skeptic** (opus-high) | 1 | 87 | 99 | 204,721 | 5,183,483 | 2,348 | **5,390,651** |
| **3 implementer** (sonnet-medium) | 4 succ + 4 dispatch | 79 | 97 | 203,297 | 1,671,824 | 859+285+767 | **1,877,129** |
| **4 integrator** (sonnet-low) | 5 (incl. retries) | 181 | 203 | 287,564 | 5,126,729 | 1,789+976+828 | **5,418,089** |
| **TOTAL** | | 374 | 432 | 801,533 | 12,618,424 | ~9,176 | **13,428,565** |

**Estimated dollar cost** (rough; uses public Anthropic-style rates: opus $15/$75/$18.75/$1.50 per M for input/output/cache-write/cache-read; sonnet $3/$15/$3.75/$0.30):

| Phase | Cost | Notes |
|---|---|---|
| 1 | ~$2.96 | dominated by 105k cache_creation on turn 1 |
| 2 | ~$11.79 | **largest single phase cost** — 87 turns × ~60k avg context |
| 3 | ~$1.29 | sonnet keeps it cheap; 4 cluster invocations |
| 4 | ~$2.67 | retries multiplied turns to 181; cache_creation 288k |
| **Total** | **~$18.71** | per slice; matches operator's prior ballpark |

**These numbers are billing-meter views.** The operator's "150k per phase" perception almost certainly refers to **single-turn context-window size** (input + cache_read at any given turn), which appears in the API response and Claude Code UI. Average per-turn context across Lever-1: P2 ≈ 62k/turn; P4 ≈ 30k/turn. Late-session turns are bigger than early ones because the cache grows.

---

## 3. Where the cost goes

Cumulative cost = **cache_creation × cost_per_M_write** + **cache_read × cost_per_M_read**, where cache_read scales as roughly **(cache_creation × num_turns)** because each turn re-feeds the accumulated cache.

This identifies two independent levers:

### Lever 1 — cut cache_creation (cut what the agent reads per session)

Static prefix per agent (system prompt + role frontmatter):
- `phase-1-writer.md`: 364 tokens
- `phase-2-skeptic.md`: 473 tokens
- `phase-3-implementer.md`: 319 tokens
- `phase-4-integrator.md`: 467 tokens
- `issue-triager.md`: 249 tokens

These are ~500 tokens combined. Negligible against 100-300k cache_creation per phase.

The Claude Code system prompt + tool schemas baseline (per INV-004 re-baseline, sweep #22): ~30k tokens. Out of cairn's control directly.

That leaves **~75-175k of cache_creation per phase that comes from the agent's own first-turn reads**: `intent.md`, `slice.yaml`, `ARCHITECTURE.md` (~6.3k), relevant ADRs (~3-5k each × N), the slice's design doc (~4-25k), `scripts/slice_orchestrator.py` (~19k), `docs/operational-reference.md` (~9.6k), `docs/lessons.md` (~8.9k), and the orchestrator-injected slice brief.

**Most-read files across the slice's logs:**

| File | Times read | Per-read cost (~tokens) |
|---|---|---|
| `scripts/slice_orchestrator.py` | **20×** | 19,236 |
| `.claude/current-slice/slice.yaml` | 8× | ~500 |
| `tests/unit/test_slice_orchestrator_model_config.py` | 5× | varies |
| `.claude/current-slice/intent.md` | 4× | ~1k |
| `docs/operational-reference.md` | 3× | 9,559 |
| ADRs (cost-per-slice-budget, phase-lock-and-role-declaration) | 2× each | 3-5k each |

The `slice_orchestrator.py` is read 20× across phases at ~19k tokens. Cumulatively that's ~380k tokens of read-amplification on a single file. Even if the agent reads only the same range each time, each fresh phase pays it once into cache_creation, then cache_read on every subsequent turn.

### Lever 2 — cut turns (cut iteration count)

cache_read scales linearly with turn count. Phase 2's 87 turns alone account for ~$5 of the phase's $11.79 cost.

| Phase | Turns | Likely cause |
|---|---|---|
| 1 | 27 | Reasonable; one-shot intent draft |
| 2 | 87 | **High** — Skeptic iteratively reads slice/orchestrator code while writing tests |
| 3 (per cluster) | ~10-15 | Expected (TDD edit→test→edit loop) |
| 4 | 181 (across 5 retries) | **Pathological** — L-008 empty-handoff cascade caused full re-runs |

Phase 4's turn count is inflated by retries (an L-008 incident). Even excluding retries, P4 averages ~36 turns/invocation, which suggests audit work itself is iterative.

---

## 4. Hexagonal lens — what the doc system actually needs

The audit's first-cut interventions (M1–S4 below) are surface-level. The deeper pattern, surfaced on operator review: cairn already has *some* hexagonal-style separation between doc-core and derived view (`/refresh-architecture` regenerates `ARCHITECTURE.md` from the ADR corpus), but it's implicit, patchy, and stops one layer too high. **Per-phase agents read the full derived view because there's no port/adapter layer below `ARCHITECTURE.md`.**

Mapping hex onto cairn's doc system:

- **Doc core** (immutable, contractual): ADR corpus, `docs/spec-v1.md`, the lesson catalog. No cross-refs to derived content.
- **Doc ports** (stable interface declarations): per-role context contracts — what each phase NEEDS, declared abstractly.
- **Doc adapters** (interchangeable implementations): `ARCHITECTURE.md`, per-slice `orientation.md`, `<module>.api.md`, subagent-dispatched digests.

### H1 — Doc port layer

A new `docs/ports/` directory with one file per role declaring abstract context requirements, e.g. `docs/ports/phase-1-context-port.yaml`:

```yaml
port: phase-1-context-port
needs:
  - invariants-touched: { format: "INV-NNN + 1-line summary", source: ARCHITECTURE.md }
  - adrs-referenced: { format: "Decision section, ≤150 words each", source: docs/adr/ }
  - envelope-glossary: { format: "path + 1-line", source: slice.yaml.envelope }
  - relevant-lessons: { format: "L-NNN headline only", source: lessons.md, count: 3 }
  - pipeline-context: { format: "last-shipped + blockers, 1 line each", source: handoff.md }
budget: 2000 tokens
```

Phase agents declare `context-port: phase-1-context-port` in their frontmatter. The orchestrator at dispatch time picks the cheapest available adapter that fulfills the port for the current slice and injects the result. **Adapter swaps don't touch agent prompts.**

**Why this is more than M0 alone:** M0 (per-slice orientation) is one adapter for one port. H1 makes the port explicit, lets multiple adapters compete (orientation file, subagent dispatch, future structured-query interface), and tightens the agent's contract — the agent depends on the port, not the file format.

**Cost to land:** 1 design slice + 1 implementation slice. Pays back ongoing churn every time a new context source is added or a cheaper adapter is invented.

## 5. Hexagonal lens — code layer

`scripts/slice_orchestrator.py` at ~19k tokens is read **20× per slice** (§3). The file mixes pure logic, subprocess dispatch, git I/O, filesystem I/O, lifecycle orchestration, and resume reconciliation. Hexagonal split:

```
scripts/slice_orchestrator/
  __init__.py        (re-exports for backward compat)
  core.py            ← pure functions: _resolve_model_config, _classify_failure,
                       detect_superseded_test_signal, _envelope_patterns, slug helpers (~3-4k tokens)
  dispatch.py        ← subprocess + retry classification (~3-4k)
  lifecycle.py       ← run_phase_loop + close_slice + boundary commits (~5k)
  resume.py          ← state-triple matrix + reconciliation (~3k)
  telemetry.py       ← .claude/orchestrator-debug/ writes + index.jsonl (~2k)
  git.py             ← git wrappers (~1k)
```

### H2 — Orchestrator package split

Reading needs by phase:
- P1 understanding context: reads `core.py` only (~3-4k vs 19k).
- P3 implementer editing dispatch: reads `dispatch.py` (~3-4k).
- P4 auditor verifying lifecycle: reads `lifecycle.py` (~5k).

**Estimated savings:** 20 reads × ~12-15k saved per read = **180-300k cache_creation per slice** when slice work touches the orchestrator. Stacks with M0/M0.5.

**Bonus:** tests get the same shape — `tests/unit/test_orchestrator_core.py` (pure-function, fast) ↔ `tests/integration/test_orchestrator_dispatch.py` (subprocess, slower). Agent looking for "is this behavior tested" reads one file.

### H3 — Invariant comments colocated in code

```python
def close_slice(...):
    """INV-008(a): idempotent close — early-return on four-signal precondition.
    INV-008(b): sole producer of the `slice: complete` commit.
    """
```

Reader sees the binding without bouncing to `ARCHITECTURE.md`. Currently invariant↔code links live in ARCHITECTURE.md's `invariant-check` blocks (out-of-band). Colocation reduces cross-file reads during audit phases. Small per-slice savings; meaningful for Phase 4 audit work.

## 6. Testing-side levers

| Lever | Mechanism | Why it cuts context |
|---|---|---|
| **H4** Test-name-as-spec discipline | `test_resolve_model_config_unknown_role_falls_back_to_opus_high` | Phase agent reading "how does X work" reads test names only (~200 tokens) instead of implementation |
| **H4** Mirror module structure | one test file per module file | "tests of X" → one read, not grep-then-read |
| **H5** Behavioral over enumeration tests (Shape A from Part 7) | tests assert behavior, not enumerated implementations | Smaller test files; F2 leakage prevented as side-effect |
| `@pytest.mark.parametrize` tables | one test fn → many cases | Test files densify; fewer lines per behavior |
| Fast/slow split | `-m "not slow"` default | Phase 3 RED→GREEN inner loop runs cheaper |
| Snapshot tests for derived artifacts | snapshot ARCHITECTURE.md, orientation.md against fixed inputs | Adapter regeneration regressions caught for ~50 lines of test code |
| Conftest-only fixtures | shared setup hoisted | Per-test-file size drops |
| One-paragraph module docstring | first thing in every module | Drives `.api.md` generation; serves as port-doc when needed |

H4–H5 are discipline + light refactor; gradual rollout, no single slice. Each catches a small fraction of cost but prevents future drift.

## 7. Per-slice orientation and API digests (the cheapest adapters for H1)

### M0 — Auto-generated per-slice orientation (mechanical, no LLM)

A new script `scripts/build_slice_orientation.py` runs at slice-open and on each phase-handoff commit. Output: `.claude/current-slice/orientation.md`, ~1.5–2k tokens, fulfilling the H1 port:

- Slice purpose (1-2 sentences from `slice.yaml.brief`)
- Envelope (file list)
- **Invariants Touched** — only the INV-NNN named in intent.md, each as a 1-2 line excerpt from ARCHITECTURE.md
- **ADRs Referenced** — only the ADRs in `adrs-referenced`, each as a ~150-word Decision-section excerpt
- **Relevant Lessons** — 3 picked by topic match against envelope/intent keywords (not the full 8.9k lessons.md)
- **Pipeline Context** — last-shipped + blockers (1 line each)

Phase agents instructed: **read `orientation.md` FIRST; only deep-read canonical sources when orientation explicitly cites them.**

**Estimated savings (vs. Lever-1 baseline):**
- Replaces full reads of: ARCHITECTURE.md (6.3k) + 2-3 ADRs (~10k) + lessons.md (~9k) + handoff.md residual = **~25-30k cache_creation per phase × 4 phases = 100-120k per slice**.
- At Lever-1 cache-cost ratios: **~$2-3 cache_creation + proportional cache_read = $4-6 per slice (20-30%)**.

Bigger than any single lever in the original audit (M1–S4) because most of what each phase reads is irrelevant to the specific slice but gets re-read because there's no projection layer between ARCHITECTURE.md and the agent.

### M0.5 — Source-file API digests (mechanical, AST-driven)

New script `scripts/build_api_digests.py` runs on commit:
- Each Python file >5k tokens: extract module docstring, def/class signatures, top-level constants → `docs/api/<module>.api.md` (~500 tokens).
- Each markdown file >10k tokens: extract h1/h2 outline + first sentence per section.

Phase agents read `.api.md` first; full source only when editing.

**Estimated savings:** if 10 of the 20 `slice_orchestrator.py` reads dropped to .api.md (500 vs 19k tokens): **~185k cache_creation reduction per slice. ~$3-4 saved.**

**Combined M0 + M0.5: ~$7-10 per slice = 35-55% reduction from these two alone**, above everything in the original M1-S4 stack.

---

## 8. Original mechanical interventions, ranked by measured leverage

Each intervention is a single slice or smaller. Estimates use the formula above and assume proportional cache_read reduction.

### M1 — Pre-built per-phase ARCHITECTURE.md projections (Shape AA, lite)

**Mechanism:** Extend `/refresh-architecture` to also emit `docs/projections/phase-{1,2,3,4}-architecture.md`, each ~1-2k tokens carrying only the section that phase actually needs (P1: invariants + scope; P2: invariants-touched + boundary contracts; P3: only touched-invariants; P4: full audit set). Agent prompts updated to read the projection, not the canonical.

**Measured impact:** ARCHITECTURE.md is ~6.3k tokens; if each phase's projection is ~1-2k, savings = ~4-5k cache_creation × 4 phases ≈ **16-20k cache_creation reduction per slice** (~$0.30-0.40 direct + proportional cache_read). Modest standalone; meaningful when stacked.

**Risks:** Projection drift (named in F2 of the prior /decision pre-mortem). Mitigated by mechanical regeneration tied to ADR/ARCHITECTURE changes.

**Cost to land:** 1 slice (refresh-architecture extension + projection schema + agent-prompt edits). No ADR; this is operational tooling.

### M2 — Bash output capping at orchestrator dispatch

**Mechanism:** Inject a Bash-result truncation policy into agent prompts: "tool results from Bash exceeding 200 lines are truncated to first 100 + last 100 with `... N lines elided ...` marker." Where the agent needs full output, it must explicitly request via `head -N` / `tail -N` / `grep`.

**Measured impact:** From log inspection, individual `pytest` runs in Phase 2 produced 5-15k token tool_result entries (already partially compressed by current prompts). Bash count per phase: P3 had 30-50 Bash calls; P4 had 60+. Cap impact estimated **~30-50k cache_creation per Phase-2/3/4** combined.

**Risks:** Agent loses signal it actually needs (e.g., a buried test failure). Mitigation: cap is generous (200 lines), and the agent can always re-run with grep.

**Cost to land:** 1 slice (orchestrator prompt-prefix change + agent-prompt update). No ADR.

### M3 — Read-tool default `limit` for known-large files

**Mechanism:** Orchestrator prompt prefix: "When reading `scripts/slice_orchestrator.py`, `docs/lessons.md`, `docs/operational-reference.md`, or `docs/plans/*.md`, default to `limit: 100` and target a specific line range; full reads require explicit operator-relevant justification."

**Measured impact:** `slice_orchestrator.py` was read 20× at 19k tokens each. If half those reads dropped to ~3k via `limit: 100`, savings = 20 × 8k = **160k cache_creation cumulative across the slice**. Largest single mechanical lever in the audit.

**Risks:** Agent under-reads a section it needed; bug missed. Existing system prompt already advises `Read` ranges for large files; this hardens it.

**Cost to land:** 1 slice — orchestrator prompt edit + 5 agent-prompt edits. No ADR.

### M4 — Per-phase output-token budget (Shape BB)

**Mechanism:** Each phase agent's system prompt declares a target output budget (P1: ≤1k, P2: ≤3k, P3: ≤2k per cluster, P4: ≤4k). Agents asked to stay under budget; orchestrator does not enforce mid-stream.

**Measured impact:** Output tokens were already small (P2: 2,348; P4: 3,593 across 5 invocations). Cost saving: ~$0.10-0.30 per slice. **Marginal — not worth a slice on its own; bundle with M1 or M2 if landed.**

### M5 — Cap retry count by phase

**Mechanism:** Orchestrator's B15 retry cap currently allows up to 15 redispatches per phase; Lever-1's Phase 4 hit the cap due to L-008. Lower the cap to 5 for Phase 4 specifically, or escalate to operator after 2 consecutive empty-handoff signals.

**Measured impact:** Phase 4 retries cost ~$1.50 over the actually-needed ~$1.20 single run. Saves **~$1.20-1.50 per L-008-style incident**, which is sporadic.

**Risks:** Legitimate retries get cut off. Mitigate by tying the lower cap to the empty-commit signal specifically.

**Cost to land:** Half a slice; ties to L-008 follow-on already queued.

---

## 9. Subagent-dispatch interventions, ranked by measured leverage

These pay LLM compute on the inner side but reduce the outer agent's context. The substrate (Claude Code subagents via `Agent` tool) already exists — what's missing is discipline.

### S1 — Constraint-harvest subagent (replaces Phase-0 / Phase-1 first-turn reads)

**Mechanism:** Phase 1 Reader and `/decision` Phase 0 dispatch a "Constraint-Harvest" subagent before doing any reasoning. Subagent reads `ARCHITECTURE.md` + `adr/index.md` + named ADRs + `lessons.md` (~30-40k tokens internally) and returns ≤300 words of "invariants relevant + ADR clauses binding + lesson patterns to honor."

**Measured impact:** P1's 105k cache_creation includes ~25-35k of these canonical reads. Subagent dispatch returns ~1k tokens. Net **~25-35k cache_creation reduction in P1 → ~$0.50-0.70 per slice; proportional cache_read drop ~$0.30-0.50.** Total ~$0.80-1.20.

**Independence note:** Subagent has fresh context, narrow prompt, returns digest. Same pattern as `/catchup` Tier 2 (firm-ADR-authorized).

### S2 — Code-survey subagent (replaces multi-file reads in Phase 2/3)

**Mechanism:** Before reading multiple source files to understand "where is X defined / called / tested," dispatch a code-survey subagent. Subagent runs grep + targeted reads internally; returns file:line list + 2-3 representative snippets.

**Measured impact:** Hardest to estimate without per-tool-result attribution. Conservative: **~30-50k cumulative cache_creation reduction across P2/P3** (~$0.60-1.00 per slice).

### S3 — Test-runner subagent (replaces direct pytest in Phase 2/3/4)

**Mechanism:** When agent wants to run tests, dispatch a test-runner subagent. Subagent runs `pytest` (cairn's full suite is 746 tests; output is large), returns ≤100-word failure summary + commit hash + exit code.

**Measured impact:** From log Bash counts (P3: 30-50, P4: 60+, many of which are pytest), subagent-mediation could save **~50-100k cache_creation per slice** (~$1-2). Largest subagent-side lever.

### S4 — Plan/research-doc digest subagent

**Mechanism:** When the slice references a plan doc (e.g., `docs/plans/2026-04-23-cost-discipline-design.md` was read 2× by Lever-1's phases at ~4.2k tokens; Part 7 doc is 23k), dispatch a digest subagent. Returns ≤300-word summary keyed to a question.

**Measured impact:** Per-slice highly variable. For slices that reference the 23k Part-7 doc: **~22k savings per phase that would otherwise read it**.

---

## 10. Refreshed unified lever ranking

Combined ranking across H-levers (hexagonal architectural moves), M-levers (mechanical), and S-levers (subagent-dispatch). Estimates assume each lever lands cleanly; composition effects discussed in §11/§14.

| # | Lever | Type | Est savings/slice | Slice cost to land |
|---|---|---|---|---|
| **H1** | Doc port layer (`docs/ports/`) — abstract context contracts per role | architectural | $4-8 (over time, via interchangeable adapters) | 1 design + 1 impl slice |
| **H2** | Split `slice_orchestrator.py` into module package (`core/dispatch/lifecycle/resume/telemetry/git`) | refactor | **$3-5** when slice touches orchestrator (180-300k cache_creation cut) | 1 slice |
| **M0** | Auto-generated per-slice orientation (one adapter for H1's port) | mechanical | **$4-6** (100-120k cache_creation cut) | 1 slice |
| **M0.5** | Source-file API digests (mechanical, AST-driven) | mechanical | **$3-4** (185k cache_creation cut on slice_orchestrator alone) | 1 slice |
| **H3** | Invariant comments colocated in code (`# INV-NNN: ...`) | discipline + edits | small per-slice; meaningful for Phase 4 audit | 1 slice |
| M3 | Default `Read limit: 100` for known-large files | orchestrator prompt prefix | $2-3 | 0.5 slice |
| **H4** | Test-name-as-spec discipline + module-mirror structure | discipline + light refactor | $1-2 | gradual |
| S3 | Test-runner subagent (replace direct `pytest`) | dispatch discipline | $1-2 | 0.5 slice |
| S1 | Constraint-harvest subagent (Phase 1 / `/decision` Phase 0) | dispatch discipline | $0.80-1.20 | 0.5 slice |
| M2 | Bash output cap (200-line truncation) | orchestrator prompt prefix | $0.60-1.00 | 0.5 slice |
| **H5** | Behavioral over enumeration tests (Shape A from Part 7) | discipline | varies; F2 prevention bonus | gradual |
| M1 | Per-phase ARCHITECTURE projections | extend `/refresh-architecture` | subsumed by M0 | — |
| S2 | Code-survey subagent | dispatch discipline | $0.60-1.00 | 0.5 slice |
| M4 | Per-phase output-token budget (Shape BB) | agent prompts | $0.10-0.30 | bundle only |
| M5 | Cap retry count by phase | orchestrator config | $1.20-1.50 per L-008 incident (sporadic) | 0.5 slice |

**Stacked H1+H2+M0+M0.5+M3+S3 estimate: ~$12-18 / slice = 65-95% cost reduction** off Lever-1's $18.71 baseline. Aggressive; assumes most levers compose, which is uncertain.

**Honest caveats:**
- Estimates assume independence between levers; real interactions may sub- or super-add.
- Per-turn context window (the operator's "150k") moves with cache_creation cuts on subsequent turns, but turn-1 still pays full creation cost.
- N=1 sample. Lever-1 was Python-orchestrator work (heavy `slice_orchestrator.py` reads); a different slice topic would have a different read profile.
- H1 in particular is a structural commitment that pays back over time, not in the first slice it lands on.

---

## 11. What the audit does NOT change about the Part-7 /decision

The Part-7 §10.8 unified primitive (declared per-phase READ envelope) remains a coherent **governance** move. It just isn't the load-bearing **cost** lever, and H1 (doc-port layer) supersedes most of its motivation in a more concrete form.

- **Cost wins** come from H2 + M0 + M0.5 + M3 + S3 + S1. Each is a regular slice; no ADR needed.
- **Governance** is now better expressed as H1 (port spec) than as an envelope-attribute on each agent definition. H1 is more abstract (the port declares need-shape; adapters fulfill) and gives the system room to evolve. Whether H1 needs an ADR or can land as plain protocol-skill plumbing is open.

Sequence preference (detail in §13):
1. **Now:** ship the highest-leverage mechanical lever (H2 — orchestrator split; pure refactor with measurable token impact and no doc-side architectural commitment).
2. **Next:** M0 (per-slice orientation) as the first concrete H1-port adapter.
3. **Then:** M0.5 + M3 + S3 layered.
4. **Last:** H1 once 2–3 adapters exist to abstract over.

---

## 12. Open questions for the operator (revised)

1. **Sample size:** ship the interventions on N=1 evidence, or measure 2-3 more slices first via the new `result.json` instrumentation that fires on the next close?
2. **Subagent independence concern:** S1-S4 introduce LLM-summarization between phases. Same risk profile as `/catchup` Tier 2 but more frequent. Acceptable?
3. **Cache pricing assumption:** my $-estimates assume opus-4 / sonnet-4 public-style rates. If actual contracts differ, scale all numbers.
4. **The 150k perception:** if "150k per phase" in the UI is per-turn context-window size, cutting cache_creation reduces per-turn size on subsequent turns (turn 1 still pays full creation cost). H2+M0+M3 stacked should drop average per-turn from ~62k to ~25-35k.
5. **H1 as ADR or as protocol-skill plumbing?** Doc-port layer is structural enough that an ADR is plausible; lightweight enough that a `/refresh-architecture`-style derived-view skill could carry it. Defer this until H1's design slice runs.
6. **H2 refactor risk:** splitting `slice_orchestrator.py` is the single biggest token win but touches a load-bearing 19k-token file with no test changes. Land under tightest test guard (existing 746-test suite must pass with zero net diff in behavior).

---

## 13. Recommended sequencing

**Five slices, no ADR (H1's ADR question deferred to its own design slice):**

1. **`compression/lever-2-orchestrator-split`** (H2) — Refactor `scripts/slice_orchestrator.py` into a module package: `core/dispatch/lifecycle/resume/telemetry/git`. Pure structural change; existing 746-test suite must pass green with no behavioral diff. Estimated savings: **$3-5 per slice (15-25%)** when slice work touches the orchestrator. **Lands first because** it's a pure refactor with the largest measured cache_creation cut and requires no doc-side architectural commitment.

2. **`compression/lever-3-slice-orientation`** (M0) — New `scripts/build_slice_orientation.py` mechanical generator + agent-prompt edits ("read orientation.md FIRST"). Output is `.claude/current-slice/orientation.md` regenerated at slice-open and on each phase-handoff commit. Estimated savings: **$4-6 per slice (20-30%)**. **Lands second because** it's the biggest single mechanical win and serves as the first concrete adapter for H1's eventual port layer.

3. **`compression/lever-4-api-digests`** (M0.5) — New `scripts/build_api_digests.py` AST-driven generator. Outputs `docs/api/<module>.api.md` for each Python file >5k tokens and markdown file >10k tokens. Agent prompts updated: prefer `.api.md` unless editing source. Estimated savings: **$3-4 per slice (15-20%)**.

4. **`compression/lever-5-read-limits-and-bash-cap`** (M3 + M2 bundled) — Orchestrator prompt prefix changes: default `Read limit: 100` for known-large files; Bash results above 200 lines truncated to first/last 100. One slice, two cheap changes. Estimated savings: **$2.60-4 per slice combined (13-21%)**.

5. **`compression/lever-6-subagent-discipline`** (S1 + S3 bundled) — Agent-prompt edits to dispatch subagents for: (a) constraint-harvest in Phase 1 / `/decision` Phase 0, (b) test-runner instead of direct `pytest`. Bundle because both are dispatch discipline edits to the same agent files. Estimated savings: **$1.80-3.20 per slice (10-17%)**.

After all five close, re-measure on the next 2 slices. If stacked savings ≥50% (vs Lever-1's $18.71 baseline), the structural compression goal is achieved — **defer H1 (doc-port layer) and the Part-7 §10.8 governance /decision indefinitely**. If wins decay, interventions fight each other, or context drift returns, **open H1's design slice** to make the port layer explicit.

**Per-slice validation event:** each slice records a before/after token measurement using the §12 audit method (or Track-0-telemetry's `result.json`, once the next slice has produced one). Numbers go into `sweep-notes.md` at close.

**Compression Slice C** remains blocked on F2 prevention — that's the **artifact-topology** question, orthogonal to cost. Slice C can proceed with the minimal Shape D move (P3-blind to `candidate-sets.yaml`) without waiting for these levers, as long as the Slice B Part 0 ADR is sequenced before Slice C ships.

**H3 (invariant comments), H4 (test-name-as-spec + module-mirror), H5 (behavioral tests)** are gradual disciplines, not single slices. Adopt opportunistically inside other slices' envelopes when the touch is small.

---

## 14. Counterarguments to the recommended sequencing

The §13 recommendation has known objections; recording them here so the choice is informed.

**Against H2-first:**
- H2 is a big refactor on a load-bearing 19k-token file with no test-behavior change. The kind of slice where L-008 / L-009 type incidents might land. Mitigation: explicitly scope test-behavior-must-be-identical as a Phase-2 invariant; require zero net diff in `tests/unit/test_slice_orchestrator_*` outputs.
- H2's measurable savings (~$3-5) are conditional on subsequent slices touching the orchestrator. If the next 5 slices touch agents/docs but not the orchestrator, the H2 win is deferred.

**Against M0-second (instead of H1-first):**
- M0 lands without H1's port spec, so its file format is *de facto* the port. Future port-spec work has to retrofit M0's choices. Counter: M0's structure (`Purpose / Envelope / Invariants / ADRs / Lessons / Pipeline-Context`) is small and reasonable; rewriting it as an H1-compliant adapter is cheap.
- Without a port spec, M0 may drift over time (new sections accreting). Counter: this is exactly what an `/integration-sweep` or future H1 design slice catches.

**Against bundling slices (lever-5, lever-6):**
- L-008 / L-009 cautions against multi-concern slices. Each bundle is two changes to the same agent prompts; risk of cross-interference is low but real. Mitigation: each lever's effect is independently measurable (M3 = file Read sizes; M2 = Bash result sizes), and they target different tool calls.

**Against the optimistic stacked estimate:**
- 65-95% reduction is aggressive. Realistic floor is probably 30-50% if levers compose poorly or if the operator's "150k" is dominated by something not modeled (e.g., MCP-server token cost or a Claude Code system-prompt component this audit didn't measure).
- The N=1 sample is biased toward orchestrator-touching work. Slices in pure-doc territory (e.g., a future ADR-rename) will have a different cost profile and the savings ratios may not hold.

**Against deferring H1:**
- Without an explicit port layer, M0 + M0.5 + future adapters all carry implicit interfaces. Each new adapter slice has to rediscover what the agents need. Counter: that rediscovery cost is small per-slice; H1's upfront cost is one design + one impl slice.

**Against deferring the Part-7 §10.8 governance /decision:**
- Without governance, mechanical wins drift over time. Counter: H4 + H5 + the discipline of measuring at every close (per the §13 validation event) is itself governance — softer than an ADR but enforceable via sweep notes.

---

## 15. References

- `.claude/orchestrator-debug/cost-discipline-lever-1-per-phase-model-phase-{1,2,3,4}-*.log` — primary evidence
- `/tmp/cairn_audit_parse.py` — parser used for this audit (ad-hoc; should be promoted to `scripts/audit_compression.py` if re-used)
- `docs/plans/2026-04-24-efficiency-program-part-7-candidate-set-discipline.md` §10.9 — promised this audit
- `docs/adr/cost-per-slice-budget.md` — INV-009; will become the threshold-update target if savings land
- `docs/lessons.md` L-008, L-009 — Phase-3/4 incident class that inflated retry counts in the sample
- `scripts/slice_orchestrator.py:1270-1303` — dispatch payload assembly (the `inputs` dict)
- `commands/claude-code/decision.md` — Phase 3 audit method matches this doc's evidence-grounding posture
- Hexagonal architecture (Cockburn 2005) — pattern source for §4–§6 (ports & adapters, dependency inversion); the cairn application is *core = ADR corpus + spec-v1; ports = per-role context contracts; adapters = ARCHITECTURE.md / orientation.md / `.api.md` / subagent dispatches*
- `.claude/agents/phase-{1,2,3,4}-*.md` — current `Writes:` declaration pattern; H1 adds a `context-port:` field declaring an abstract input contract per role
- `commands/claude-code/refresh-architecture.full.md` — existing live-derived-view skill; M0/M0.5/H1 generalize this pattern beyond ARCHITECTURE.md to per-slice and per-module derived views
