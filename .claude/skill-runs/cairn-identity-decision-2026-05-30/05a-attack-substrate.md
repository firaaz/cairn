# 05a — Attack: substrate-as-identity (C5–C8 prosecute-then-verify)

**Role:** Phase-3 adversarial skeptic-verifier. **Target:** the synthesis claim that cairn's durable identity is its cross-slice substrate (arc A's C5–C8). Arc A self-rated these "high" but `verified: null` — never skeptic-verified. This is the verification.

**Method:** prosecute each claim as aspirational, then verify against actual repo files (ran the validator, ran the test suite, grepped live dispatch + history). Verdicts: VERIFIED (live + load-bearing) / PARTIAL (half live, half aspirational) / ASPIRATIONAL (asserted, not wired).

---

## C5 — per-role, per-path, fail-closed write gating (`role_guard.py`) → **PARTIAL (the headline half is DEAD)**

**Prosecution:** the differentiator arc A claims over native deny-globs is *per-role* gating (Reader/Skeptic/Builder/Auditor each get a distinct write allowlist). If `AGENT_ROLE` is never injected, that half is dead and the only live enforcement is the session-global operator envelope — which is functionally equivalent to native session-wide deny-globs, i.e. NOT a differentiator.

**Verification — the per-role half is unreachable under live dispatch:**
- `checks/role_guard.py:137` reads `role = os.environ.get("AGENT_ROLE")`. The entire per-role branch (`:167–203`: static `ROLE_POLICIES` for phase-1/2/4, envelope-driven phase-3, envelope-grant escape, grant log) executes **only when `AGENT_ROLE` is set**.
- **Nothing live sets it.** The only injectors (`env["AGENT_ROLE"] = role`) live in `docs/plans/2026-04-18-…` and `…-04-20-…` — the design docs for `scripts/slice_orchestrator.py`, which **no longer exists** (deleted at `01a4cc3`, "lever-2-orchestrator-split"; `scripts/slice_orchestrator/` is now an empty `__pycache__` shell). Grep for live injectors across `scripts/ commands/ checks/ .claude/` returns only retired-orchestrator plan docs and skill-run journals — zero live producers.
- **The live dispatcher does not inject it.** `.claude/skills/cairn-tdd-feature/SKILL.md:8` dispatches "via the Agent tool"; steps 60–74 call `subagent_type: phase-{1..4}-tdd`. No `AGENT_ROLE`/`AGENT_ENVELOPE` anywhere in the skill (grep empty). Phase-3's write envelope is passed as **prompt text** ("the source-write envelope (JSON array of regex strings)", `:70`), NOT as the `AGENT_ENVELOPE` env var the hook reads at `:176`. So even phase-3's envelope-driven gate is unreachable under live dispatch.
- **Corroborates 00-F5 / 01-F5 exactly:** "AGENT_ROLE is dead code (role_guard reads it; dispatch never injects)." Verified independently here against the live SKILL.md, not just asserted.

**What IS live:** the operator-envelope branch (`:141–165`) — `AGENT_ROLE` unset → reads `.claude/active-envelope.yaml`, enforces `mode: operator` paths, fail-closed on malformed YAML/unknown mode (`:147–149`, `:105–108`). It is registered (`.claude/settings.json:39`, PreToolUse). This is **real and session-global** — but it is exactly the session-wide deny-glob equivalent the prosecution named, applied to a *normal operator session*, not per-subagent role isolation.

**Verdict: PARTIAL.** Fail-closed operator-envelope gating is VERIFIED-live. The *per-role* half — C5's actual differentiator — is ASPIRATIONAL: no live producer of `AGENT_ROLE`, dead since the orchestrator was deleted. Arc A's own C5 footnote conceded "per-role anchoring aspirational (AGENT_ROLE unset on dispatch)" but still graded the claim "still-load-bearing / high." That grade is **unearned for the per-role differentiator.**

---

## C6 — validator as fail-closed coherence checker (`validate_architecture.py`) → **VERIFIED (load-bearing)**

**Prosecution:** is it decorative — does it run, and does Check D actually execute assertions or just pretty-print?

**Verification:**
- **Runs, exits non-decoratively:** `uv run python scripts/validate_architecture.py` → `ALL CHECKS PASSED / Invariants verified: 12 / ADR files checked: 38`, exit 0. `main()` (`:930–947`) exits 1 on any failure, 2 on missing files.
- **Checks A/B/C are real graph-coherence:** A = every invariant references a valid non-superseded ADR (`:861–879`); B = every accepted-firm ADR has ≥1 invariant or FAIL (`:881–889`); C = no invariant references a superseded ADR (`:875–879`). A/B/C failure short-circuits before D (`:891–893`).
- **Check D executes assertions, not prose:** `_run_assertion` (`:728–743`) dispatches by type and runs real I/O — `git-log-walk` actually walks `git log base..HEAD` and classifies every commit's CC-prefix (`:384–435`, INV-001); `structural-parser` reads the target file and checks required/forbidden sections + token budget (`:641–725`); `test-ref`/`file-exists`/`grep`/`phase-topology` all hit the filesystem. arc A's evidence ("validator currently exits 1, Check D INV-001 FAIL on `3f0149d0`") is the right *kind* of evidence — a real coherence violation caught. It is GREEN now only because the corpus is currently coherent.
- **Honest limit (carry forward):** semantic drift is uncaught — prose meaning can shift while the structural cross-ref still passes. arc A admits this; it is a real ceiling, not a refutation of "fail-closed *structural* coherence."

**Verdict: VERIFIED.** Live, fail-closed, load-bearing for structural coherence. The strongest of the four.

---

## C7 — `/decision` cross-session blind independent verification (Phase 5) → **PARTIAL (real mechanism, rarely exercised)**

**Prosecution:** is Phase-5 blind verification actually RUN, or narrated as protocol and skipped? If it's run once and cited forever, it's as aspirational as the reactivity headline.

**Verification:**
- **It is a real, codified protocol with at least one genuine, high-value run:** `docs/adr/phase-lock-and-role-declaration.md:114` documents a real Phase-5 run — fresh general-purpose subagent, given the constraint envelope + ADRs 001–003 + spec/lessons, explicit "do NOT read this ADR's body," independently re-enumerated four phase shapes and converged on the same lock. `docs/lessons.md:62` (L-003) and `:122–130` (the L-022-adjacent slice-close-contract lesson) document Phase-5 catching **real premise-level errors** — the blinded agent reading `scripts/slice_orchestrator.py:841` directly caught a mis-attributed commit (R3 was orchestrator-issued, not agent-issued) that all of Phases 0–4 inherited from the framing doc. This is the load-bearing core and it genuinely fired. (Note: arc A's "L-022" pointer is loose — the catch is the slice-close-contract lesson at lessons.md:122–130, not the manifest-round-trip L-022 at :428. Same mechanism, wrong lesson id.)
- **But it is structurally narrow and frequently skipped:** Phase 5 runs **only for `firmness: firm`** decisions; provisional decisions skip it by protocol (`docs/lessons.md:50,72`; `commands/claude-code/decision.full.md`). Grep for an actual documented Phase-5 *run* across all 38 ADRs returns exactly **one** (`phase-lock-and-role-declaration.md`) against **25 firm ADRs**. Even allowing that most runs live in `/decision` session artifacts rather than the ADR body, the in-corpus evidentiary footprint is one. So the *mechanism* is verified-live and demonstrably valuable when run; its *frequency* is low and its scope excludes every provisional ADR — including, ironically, the identity ADR if it lands provisional.

**Verdict: PARTIAL.** The cross-session blind-independence mechanism is VERIFIED (real protocol, real catch). The claim that it is a routinely-exercised pillar is ASPIRATIONAL: one documented run in-corpus, firm-only, skipped for provisional.

---

## C8 — pointer-only handoff (`test_handoff_contract.py`) → **VERIFIED (most solid)**

**Verification:**
- Test file exists; **5/5 pass** (`uv run pytest tests/unit/test_handoff_contract.py` → `5 passed in 15.08s`).
- Genuinely fail-closed and structural: `test_no_narrative_prose` (`:66–77`) rejects multi-sentence lines + >1 paragraph block; `test_pointers_resolve` (`:114–128`) resolves every `gh:`/file/commit pointer against the live repo and requires a state keyword; `test_coverage_open_issues` / `test_coverage_provisional_adrs` (`:166,211`) fail if any open issue or provisional ADR is missing from the handoff. These hit `gh` and `git` for real — not shape-mocked.
- Bound to the invariant: INV-002 carries `type: test-ref → tests/unit/test_handoff_contract.py` (`docs/ARCHITECTURE.md:24–28`), so Check D enforces the binding's existence and the suite enforces the contract.

**Verdict: VERIFIED.** Live, fail-closed, test-bound. As predicted, the most solid.

---

## Bottom line

| Claim | Verdict | Live + load-bearing? |
|---|---|---|
| C5 per-role write gating | **PARTIAL** | Operator-envelope half live; **per-role differentiator DEAD** (no live `AGENT_ROLE` producer since orchestrator deletion `01a4cc3`) |
| C6 coherence validator | **VERIFIED** | Yes — runs, fail-closed, real Check A–D |
| C7 Phase-5 blind verify | **PARTIAL** | Mechanism real + fired once; **rarely run** (1 documented / 25 firm ADRs; firm-only) |
| C8 pointer handoff | **VERIFIED** | Yes — 5/5 pass, test-bound, fail-closed |

**Is the substrate a sound identity anchor?** *Partly.* **C6 + C8 are genuinely better-evidenced than the unmeasured reactivity headline** — they are mechanized, fail-closed, and pass under live test today. The synthesis CAN lean on those two.

But the two claims that most resemble cairn's *distinctive* governance story — **C5's per-role isolation and C7's adversarial independence — are NOT better-evidenced than the reactivity headline.** C5's headline half is *dead code* with no live producer (the same "asserted-but-unwired" weakness 00-F3 named for the re-injection hook). C7's mechanism is real but exercised once in-corpus and skipped for every provisional ADR. Centering identity on "the substrate" *as a whole* therefore repeats arc A's error — promoting self-rated, never-verified claims (C5/C7) to load-bearing.

**Recommendation for the synthesis:** anchor on the **two VERIFIED substrate claims (append-only ADR coherence validator C6 + fail-closed pointer-handoff contract C8)** — these survive prosecution. Do NOT cite C5's per-role gating as a live differentiator (it is dead; if the ADR wants it, it must ship a live `AGENT_ROLE`/per-subagent-scope producer as a BUILD deliverable, exactly the 00-F5 open question). Do NOT cite C7 as a routinely-run pillar (firm-only, one documented run). The honest substrate identity is **narrower than C5–C8**: it is C6+C8 (live), with C5/C7 as *aspirational-but-buildable*, not *durable-and-proven*.
