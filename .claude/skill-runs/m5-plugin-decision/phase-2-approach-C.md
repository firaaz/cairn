# Phase 2 — Approach C (steel-man)

Decision: "How does cairn ship as a consumer-installable methodology, replacing the `.slice-system → .` symlink consumption pattern?"

Author: Phase 2 forced-enumeration teammate, Approach C (the conservative path).

**Approach C in one sentence.** Cairn does not ship as a plugin in M5. The `.slice-system → .` symlink stays as the transitional self-consumption mechanism; the M5 work is reframed as a *consumer-doc surface* — `CONSUMER.md`, README reading order, comprehensive templates, `docs/phase-skill-mapping.md`, `docs/adoptable-disciplines.md` — and the README explicitly recommends consumers **copy** relevant files. Plugin packaging is deferred until two preconditions hold: (a) the six amendment ADRs close to v1 firmness, and (b) at least two distinct consumers have completed end-to-end adoption via the copy-then-customize path manually. M6 (complex-rag-analysis migration) is reframed: complex-rag-analysis chooses between staying on a deprecation-flagged symlink or copying to its own tree.

---

## 1. Boundary coverage

The Phase 0.5 trace enumerated twelve cross-role boundaries (`phase-0.5-journey.md:64-79`). Under Approach C, **most of those boundaries are not crossed at all** — they remain handled by the existing symlink + canonical-checkout mechanics, which already work for the maintainer (Role 3) and the one existing symlink consumer (Role 2).

**Boundaries that become non-issues under C (because there is no plugin install):**

- **Hook-script delivery + invocation path** — handled today by `$CLAUDE_PROJECT_DIR/.slice-system/checks/...` for the symlink consumer, and by the canonical checkout for the copy consumer. No plugin-cache relocation, no `${CLAUDE_PLUGIN_ROOT}` indirection to invent.
- **Agent-registry resolution** — `.claude/agents/*.md` resolve through the existing symlink (Role 2/3) or are copied into the consumer's repo verbatim. No registry-discovery contract changes.
- **Slash-command discovery** — same: copied or symlinked, no plugin-resolved path.
- **Skill discovery** — `.claude/skills/cairn-tdd-feature/SKILL.md` is reachable via the symlink today; remains reachable.
- **Python-runtime boundary** — copy-consumers add `uv` to their own project just as they would have under plugin install; symlink consumers already have `uv run python` working through the symlink. No new contract.
- **Settings.json hook-string boundary** — not changed. Today's `$CLAUDE_PROJECT_DIR/.slice-system/checks/...` strings stay valid; copy-consumers replace `.slice-system/` with their own copy path manually (a one-shot edit, documented in `CONSUMER.md`).
- **Symlink-stripping logic** — `reversibility-guard.sh:48,76` keeps doing what it does; the `CLAUDE.md:11` rule "edit canonical paths only" remains accurate.
- **Cairn self-consumption circularity** — Path A vs Path B (`brainstorm-decisions.md:25`) does not need resolving in M5. Cairn keeps its self-symlink (Path B). The `__file__`-anchored `CAIRN_ROOT` at `checks/role_guard.py:28` continues to resolve correctly through the self-loop.
- **Versioning + pinning boundary** — copy-consumers pin by tracking the SHA they copied from; symlink-consumers pin by checking out a SHA in their cairn checkout. The `README.md:33` "post-v1 git submodule" commitment stays as-is.
- **Consumer-owned `.claude/` state** — no plugin install means zero clobber risk on `handoff.md`, `active-envelope.yaml`, `skill-runs/<id>/`, `learning.md`, `adr-editorial-fixes.log`.

**Boundaries that DO arise under C (the doc-surface boundaries):**

- **`CONSUMER.md` audience boundary.** Handled by literal file split per Brainstorm decision #5: `CLAUDE.md` stays maintainer-shaped; `CONSUMER.md` is consumer-only and explicitly says "you are reading this because you copied or symlinked cairn into your repo." Addresses `Finding 1` (`docs/reviews/2026-04-23-from-portfolio-evaluation.md:60-66`) and constraint #6 (HARD).
- **README reading-order boundary.** Handled by adding the three-line block from `Finding 2` (`docs/reviews/2026-04-23-from-portfolio-evaluation.md:74-79`) verbatim. Addresses constraint #22 (SOFT).
- **Templates surface boundary.** Handled per Brainstorm decision #6: every phase-boundary contract gets a worked-example template. Addresses constraint #23 (SOFT) and `Finding 3`.
- **Phase-skill-mapping promotion.** Move it from buried prose into `docs/phase-skill-mapping.md` per `Finding 4`.
- **Adoptable-disciplines enumeration.** New `docs/adoptable-disciplines.md` per `Finding 5` (`docs/reviews/2026-04-23-from-portfolio-evaluation.md:101`), which directly names the three pieces — handoff-as-pointer, tiered catchup, role labels — that the portfolio reviewer flagged as standalone-portable. This *is* the minimum-viable-cairn answer to Open Question #1 in the review (`:105`).
- **Identifier-scheme boundary.** Already in `docs/adr/identifier-scheme.md`; CONSUMER.md links to it.

Net: under C, the only boundaries needing new design are documentation boundaries. Every system boundary stays as it is.

---

## 2. Pre-mortem responses

Of the six scenarios in `phase-1-pre-mortem.md`, **five evaporate or shrink dramatically under Approach C**, and one survives.

- **Scenario 1 (silent envelope-enforcement bypass via `__file__`-anchored `CAIRN_ROOT`):** *Evaporates.* There is no plugin cache for `checks/role_guard.py` to relocate to. `Path(__file__).resolve().parent.parent` continues to resolve through the symlink (today's behavior, which works) or to the copy-consumer's own canonical `checks/role_guard.py` location (also works because the consumer's `.claude/` is sibling to `checks/`). Severity-blocks-ship scenario neutralised.
- **Scenario 2 (settings-merge drift across N consumers):** *Evaporates.* No plugin manifest, no merge semantics. Copy-consumers own their settings.json edits; symlink-consumers pin a SHA. Cross-consumer-version drift collapses into normal version-pin drift, which is exactly what constraint #3 (SOFT) sanctions.
- **Scenario 3 (self-consumption circularity, maintainer can't iterate on hooks):** *Evaporates.* Cairn keeps Path B (self-symlink). The maintainer continues editing canonical files; the next tool call invokes the freshly edited script. The Path A failure mode (running plugin-cached previous version while editing canonical next version) cannot occur. Vision commitment #1 (constraint #26) and amendment-velocity for the six open ADRs are preserved.
- **Scenario 4 (audience-split bisection still leaves consumers bouncing):** **Survives.** This is the one scenario Approach C must address head-on. C's defenses: implement `Finding 2` reading-order in README, write CONSUMER.md as a *graduated-adoption ramp* (start with three hooks + handoff-as-pointer per `docs/adoptable-disciplines.md`, escalate to full skill only after the reader demonstrates fluency), and ship templates with worked examples per Brainstorm decision #6. The portfolio review is treated as the spec for F2's deliverable, not as input to be summarised.
- **Scenario 5 (`.local/` leakage in plugin payload):** *Evaporates.* No plugin tarball means no payload-globbing step. Copy-consumers cherry-pick what they want; cairn cannot accidentally ship `/dev-mode` to anyone.
- **Scenario 6 (migration-orphan during M6 cutover):** *Evaporates.* M6 does not happen under C as a forced cutover. Complex-rag-analysis is offered the choice: stay on the deprecation-flagged symlink, or copy to their own tree on their own timeline. No "in-flight skill-run abandoned" failure mode because there is no synchronous symlink-to-plugin atomicity requirement.

Severity ledger after C: blocks-ship scenarios reduce from three (1, 3, 5) to **zero**; ongoing-pain scenarios reduce from three (2, 4, 6) to **one** (Scenario 4).

---

## 3. Why this beats the alternatives

**Axis 1 — The portfolio reviewer's actual choice is evidence, not opinion.** `docs/reviews/2026-04-23-from-portfolio-evaluation.md:32` reads literally "Partial adoption, cherry-picked; no symlink." `:52` says the portfolio "will copy concrete files rather than link." `:111` reframes that copying as "not a rejection of the methodology; it is a hedge against a pre-v1 upstream still reshaping its own substrate." The portfolio reviewer is exactly the audience cairn says it serves (constraint #8: complex / safety-critical / long-horizon, with the portfolio sitting just *below* that threshold and choosing partial adoption). Their copy-don't-symlink verdict is **n=1 evidence from the target population**. Approach A and B both build a plugin install for an audience whose exemplar already declined plugin-class consumption. Approach C makes the reviewer's choice the *recommended* path.

**Axis 2 — Avoids the most severe pre-mortem scenario entirely.** Scenario 1 is the *only* blocks-ship scenario that crosses a HARD constraint (#15) AND reproduces cairn's own most-criticised failure mode (silent enforcement no-op, the exact pathology `CLAUDE.md:13-16` already calls out for `jq`/`ruff`). Approach A and B both have to engineer around it (replace `__file__` anchoring, add positive enforcement tests, etc.); Approach C cannot create it because there is no plugin cache for `role_guard.py` to relocate to.

**Axis 3 — Honors constraint #7 by inverting the framing.** Constraint #7 (SOFT) is "one concrete prospective consumer chose copy-adoption over symlink-adoption, citing pre-v1 instability." Under A/B, copy-adoption is treated as a deprecated workaround we route consumers away from. Under C, copy-adoption *is the recommended path*; the symlink is the deprecated workaround we route consumers away from over time. This converts a constraint we have to apologise for into an asset we recommend.

**Axis 4 (bonus) — Doesn't lock in pre-v1 commitments.** Six amendment ADRs are open (constraint #3, SOFT). Plugin packaging is a *versioned contract surface*: every release after the first publishes a new shape consumers might depend on. Approach C defers that contract until v1, by which time (a) the amendment ADRs have closed and (b) at least two consumers have battle-tested the copy path manually, giving cairn empirical signal about what the plugin should actually package. When v1 lands, Approach A or B becomes possible *with* a consumer base that has lived the copy-then-customize path — a stronger position than shipping a plugin at v0.4 and discovering at v0.6 what consumers actually wanted.

---

## 4. Honest weaknesses

- **No automatic distribution.** Consumers manually pull updates by re-copying or re-pulling. There is no `claude plugin upgrade cairn` that notifies them of a new release. For consumers who adopt the three hooks (per `adoptable-disciplines.md`), this is fine — the hooks are stable. For consumers who adopt the full skill, manual update is friction that compounds over time.
- **The symlink mechanism keeps accumulating decisions until eventual retire.** Every M5+M6 follow-up item that brainstorm decision #20 (constraint #20 SOFT) wanted to absorb — `operational-reference.md` rewrite, `spec-v1.md` rewrite, `docs/upgrading-from-pre-compression.md` deletion, `scripts/_root.py` audit, `efficiency_program/` test cleanup — still has to happen *somewhere*. Approach C orphans them onto a future plugin-packaging program, leaving the symlink + canonical-checkout pattern as the load-bearing distribution mechanism for an indefinite period. Constraint #11 (HARD, dep set is `pydantic + typer + pyyaml`) and constraint #18 (HARD, ADR append-only) keep accumulating.
- **M6 doesn't happen.** Complex-rag-analysis stays on a deprecated symlink path indefinitely, getting "deprecation-warned but not retired" treatment. This is friction we are *deliberately deferring* rather than friction we are *fixing*. If complex-rag-analysis needs cairn to evolve in a way the symlink can't carry (e.g., a hook that requires plugin-resolved paths), Approach C has no answer.
- **CONSUMER.md still has to do the heavy lifting Scenario 4 demanded.** The single surviving pre-mortem scenario doesn't go away under C; it just becomes the entire scope of what M5 ships. If F2 doesn't deliver a genuinely first-time-consumer-friendly reading order with worked-example templates and a graduated-adoption ramp, Approach C ships *less* than A/B and *also* doesn't address the original adoption friction. The whole bet rides on F2 quality.
