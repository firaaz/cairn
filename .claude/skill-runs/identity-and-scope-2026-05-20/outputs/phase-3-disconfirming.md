# Phase 3 — Disconfirming Search on Approach 3

## Orthogonality verification

**Claim 1: `checks/role_guard.py` survives without `AGENT_ROLE` (dispatch context).**
- Status: VERIFIED — When `AGENT_ROLE` is unset, the hook falls through to operator-envelope mode (`.claude/active-envelope.yaml`). Line 137–167 of `checks/role_guard.py` documents the two paths explicitly. The comment at line 43–45 states phase-3-tdd "has no static entry; envelope-driven (preserves the asymmetry that phase-3-tdd established)." The hook is orthogonal to dispatch.

**Claim 2: `scripts/validate_architecture.py` does not require dispatch pipeline artifacts.**
- Status: VERIFIED — Validator references phase names (phase-1-tdd, phase-2-tdd, phase-3-tdd, phase-4-tdd) at lines 443–445 only to map roles, not to read `.claude/skill-runs/` state. No `.claude/skill-runs/` path appears in the validator. Orthogonal.

**Claim 3: `tests/unit/test_handoff_contract.py` does not require dispatch artifacts to exist.**
- Status: VERIFIED — The test reads `.claude/handoff.md` and verifies pointer resolution (GitHub issues, file paths, commits). It makes no assumption about where the handoff came from (dispatch or direct edit). Orthogonal.

**Verdict on Claim: ORTHOGONALITY HOLDS.** The three-layer separation (hooks, validators, tests) does not mechanically depend on the four-phase machinery existing as a named preset.

---

## Naming collisions

- **"preset"**: Not found in docs/, .claude/, or commands/. One reference in phase-2-approaches.md line 63 ("formalize the three existing execution paths as named modes without a fourth tier above") — but "modes" not "presets." No collision with existing load-bearing terms.

- **"mode"**: Heavy load-bearing use in `.claude/active-envelope.yaml` (mode: operator | off). A3's naming of presets would **collide directly** here — operator envelope already uses "mode:" to select behavior (operator enforcement vs. off). Grep result: docs/operational-reference.md:24–25 and 36 show `mode: operator | off`. **CRITICAL: A3 should NOT call the three paths "modes" because operator envelope already claims that term.**

- **"tier"**: Found in A2's direction doc and several cliff-defense / vision docs, but not in committed load-bearing design. No collision at the committed level, but the direction doc (Phase 0 constraints line 49) explicitly questions whether Tier 0/1 should exist. A3 sidesteps this by avoiding tiers entirely.

- **"level"**: Scattered in documentation (e.g., "high-consequence level," "component level") but not a system term. No collision.

- **"contracted"**: Only appears in phase-2-approaches.md A3 section (line 26, 40) as proposed name for `/decision` arc. No prior load-bearing use in docs/ or code.

**Verdict: COLLISION FOUND.** A3 proposes three "presets" (ad-hoc | contracted | formal) but does not address that `mode:` is already the operator-envelope decision point. If A3 uses "preset" instead of "mode" for the three paths, there is NO collision. If A3 calls them "modes," it creates naming ambiguity with `.claude/active-envelope.yaml`'s `mode: operator | off`.

---

## Hidden spec-v1 §1 dependencies

- **Search**: `docs/spec-v1.md` §1 asserts "It is not for simple software" at line 27. grep for explicit code/test references to this clause.
- **Results**: 
  - `docs/spec-v1.md` line 27 (declarative only).
  - `docs/adoptable-disciplines.md` line 3 references it for consumer framing.
  - `docs/reviews/2026-04-23-from-portfolio-evaluation.md` line 34 cites it to justify "half-adoption is worse than non-adoption."
  - No mechanical hook or script tests the scope clause; no code path branches on "is this simple software?"

**Verdict: NO MECHANICAL DEPENDENCY FOUND.** The scope clause exists as design guidance and policy statement, not as an enforced system boundary. A3's claim "no spec-v1 §1 amendment" is safe — the clause is documentary, not executable.

---

## phase-lock-and-role-declaration collision check

Read `docs/adr/phase-lock-and-role-declaration.md` Context section (line 21–31):

> Commitment #5 marks the four-phase pipeline as "plastic through v1" — Phase rethink runs through `/decision` and may produce 3, 4, or 5 phases. Commitment #6 commits to explicit roles. This ADR resolves both.

**D1 assertion** (line 37–39): "Cairn commits to the following four claims. The slice pipeline has exactly four phases, locked in order and name... No phase is added, removed, renamed, or reordered without a superseding ADR."

**INV-003** (line 86–88): "Every slice runs through exactly four phases in order — Intent (Reader), Validation (Skeptic), Implementation (Builder), Integration (Auditor)... locked at four; the names are locked as listed."

**Verdict: COLLISION EXISTS, BUT DOES NOT FALSIFY A3.** The ADR asserts that *every slice* runs four phases and that the phase shape is locked. A3 preserves this by naming the four-phase machinery as ONE PRESET CALLED "formal," not by abandoning the four phases. The ADR does NOT assert "the four phases IS Cairn's identity" — it only locks the shape. A3's framing ("infrastructure is identity; methodology is one preset") is compatible with phase-lock-and-role-declaration if the "formal preset" is the dispatch-skill invocation path. However, **A3 must explicitly state that "formal" preset = `cairn-tdd-feature` dispatch skill; otherwise the naming is cosmetic and the phase-lock remains unanchored.**

---

## /decision arc mapping check

Read `commands/claude-code/decision.md` (lines 1–23):

> Make an architectural decision with structural safeguards. Use for decisions that become ADRs — invariants, boundaries, data ownership, module structure. (Phase 0 through Phase 6 described.)

**Finding**: `/decision` is described as a *protocol* for decision-making work, not as a preset or routing mode. Line 9 says "Use for decisions that become ADRs," which is a scope rule, not an execution mode.

**A3's claim**: `/decision` arc is named as "contracted" preset. But the skill doc does not use "preset" language; it uses "use for X" guidance.

**Verdict: MISMATCH, NOT FALSIFICATION.** A3 proposes that "/decision is the contracted preset," but `/decision` today is a *protocol*, not a *preset name*. The mapping is unclear: 
- Does invoking `/decision` count as "using the contracted preset"? 
- Or is "contracted preset" a new name for the `/decision` protocol?
- Or is the preset the operator's *declaration* at session start ("I'm doing contracted work"), independent of whether they invoke `/decision` or edit directly?

**This ambiguity is A3's weakest point.** A3 should clarify: is "contracted preset" a NAME for the `/decision` protocol, or a DECLARATION that the operator makes independently of using `/decision`?

---

## Cosmetic-preset failure mode

**Scenario**: Operator declares at session start "using formal preset" (per A3's framing) but then edits code without invoking the `cairn-tdd-feature` dispatch skill.

**Detection mechanism in A3**: NONE NAMED. A3 proposes the preset as a documentation label (optional slash cmd `commands/claude-code/preset.md` mentioned at line 90–92 of phase-2-approaches.md), but does NOT propose any hook that checks `FORMAL preset declared == cairn-tdd-feature skill invoked`.

**Current state**: 
- `.claude/active-envelope.yaml` can enforce write paths (mode: operator).
- No global "active-preset" signal exists; no hook checks preset consistency.
- The only signal that a slice ran through four phases is the presence of four commits with phase-phase prefixes (Intent/Validation/Implementation/Integration).

**Verdict: PARTIAL COSMETIC RISK.** If the preset label is purely documentary (for `/catchup` readout or operator memory), then cosmetic-ness is acceptable — presets are a naming and coordination tool, not an enforcement point. But A3 should explicitly state: *"Preset declaration is advisory. Enforcement remains via commit structure (four phases exist) and invariant binding (INV-003). A declared preset that is not matched by commit structure is a discipline failure, not a detectable error."*

---

## Summary of disconfirming findings

| Finding | Severity | Impact on A3 |
|---------|----------|-------------|
| Orthogonality holds (three-layer separation is real) | — | **Supports A3** — the core structural insight is sound. |
| Naming collision: "mode" already claimed by operator envelope | Medium | **Requires amendment:** A3 should use "preset" (not "mode") or rename the three paths to avoid confusion with `mode: operator\|off`. |
| No hidden spec-v1 §1 dependencies | — | **Supports A3** — "no amendment" claim is safe. |
| phase-lock-and-role-declaration asserts four phases locked, not "IS identity" | Low | **Supports A3 with caveat:** A3 must explicitly map "formal preset" ↔ `cairn-tdd-feature` dispatch skill, or the phase lock floats. |
| /decision protocol lacks "preset" framing; mapping to "contracted" is unclear | Medium | **Requires clarification:** A3 should state whether "contracted preset" is (a) a name for the `/decision` protocol, or (b) a session-level declaration independent of which execution method is used. |
| No detection mechanism for preset-declaration ↔ execution-method mismatch | Low | **Expected design:** A3 should document that preset is advisory and enforcement is via commit structure. |

---

## Verdict

**A3 survives Phase 3 with two amendments required:**

1. **Naming clarification (mode vs preset).** A3 uses "preset" (good) and avoids "mode" (necessary), but should explicitly state: *"The three execution paths are named presets: `ad-hoc`, `contracted`, `formal`. This is distinct from operator-envelope's `mode: operator|off` setting."*

2. **Preset-to-mechanism mapping.** A3 should explicitly state:
   - "The `formal` preset corresponds to invoking the `cairn-tdd-feature` dispatch skill."
   - "The `contracted` preset corresponds to running `/decision` (or operator override via direct ADR write + manual `/refresh-architecture`)."
   - "The `ad-hoc` preset is direct editing under operator-envelope governance."

3. **Phase-lock anchoring.** Add one sentence to the one new ADR: *"The `formal` preset embodies phase-lock-and-role-declaration D1–D4 as a named execution path. The other presets (ad-hoc, contracted) operate outside the four-phase machinery but consume its infrastructure (hooks, validators, ADRs)."*

**Cost to revert**: Trivial — only the new ADR is added; no amendments to phase-lock or spec-v1.

**Orthogonality finding is solid.** The separation between infrastructure (hooks, validators, handoff) and methodology (four-phase machinery) is real and testable. A3 can ship with these three amendments.

