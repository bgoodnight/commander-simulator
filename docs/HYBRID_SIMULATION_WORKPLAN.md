# Hybrid simulation and reusable behavior — implementation work plan

Status: **partially implemented identity/query/observation foundations; no executable hybrid dispatch yet**. Read with [ROADMAP.md](../ROADMAP.md), [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md), the binding [Progressive Ability-Composition Architecture](ABILITY_COMPOSITION_ARCHITECTURE.md), and [P0.5 engine review](P05_ENGINE_REVIEW.md). This document prioritizes value from an unfamiliar validated deck **before** full per-card rules coverage. Existing strict rules, validated metadata, and historical results remain the correctness baseline.

## Goal and non-goals

**Goal:** Given a legitimate new decklist (including the temporary Magnus Flameslinger v0.7 and, later, an authenticated mono-black list), represent every verified card as a **real interactable game object** with printed and derived characteristics, then produce meaningful opening-hand, mana, deployment, interaction-availability, resource, and turn-by-turn narrative diagnostics without implementing every individual ability. Reuse implemented rules and common effect/keyword templates, and label assumptions and the extent to which downstream decisions depend on them.

**Not goals:** a perfect Magic rules engine, autonomous interpretation/execution of Oracle prose, unqualified win-rate estimates, arbitrary cards automatically acquiring effects, hiding impossible plays, or modifying strict semantics to help approximate runs succeed.

Separately track **identity confidence**, **functional coverage**, and **outcome dependence**. A verified card identity is neither proof that the rules are implemented nor permission to guess the card's effect.

## Foundational requirement: an unfamiliar card is still a real game object

**Separate characteristics from abilities.** A verified creature whose special text is not implemented still has its actual mana cost/color, creature types, power/toughness, printed/recognized keywords, owner/controller, battlefield object ID, tap state, zone identity and relevant characteristics. A verified artifact is still an artifact; a verified land is still a land. These are typed entities in the **same authoritative game state**, not inert cards, fake tokens, anonymous generic 2/2s, or narrative-only projections.

This general characteristic layer must be **usable by other cards and opponents**, regardless of whether the target's own activated/triggered abilities are implemented:

- **Targeting and legality:** targeting by printed/derived type, subtype, color, controller, mana value, power/toughness, spell vs permanent and known restrictions; use correct zones and face-dependent values. Targetable by removal, bounce, counters and creature interaction only when targeting restrictions are verifiably satisfied. Ward/protection/hexproof/shroud or unknown applicable restrictions require actual support or a labeled abstention; **never silently ignore a known restriction**.
- **General game actions:** source-paid casting, entering the battlefield, tapping, attacking/blocking, damage, dying, sacrifice, bouncing, exiling, returning, and reanimation where the relevant shared rules are implemented. Applying these actions to an unfamiliar card must not require a card-name branch.
- **Queries and tutors:** an implemented tutor searching for a creature, Zombie, an artifact, an instant of a specified mana value/color, or a creature with power <= 2 must recognize *all* eligible verified library objects, including cards whose own effects are absent. Apply the actual tutor's search/filter/reveal/destination rules; a familiar *role* does not itself authorize a search or grant an ability.
- **Recognized keywords:** if flying, deathtouch, lifelink, haste, vigilance, trample or similar generic behavior is implemented, unfamiliar cards declaring that keyword receive the same validated mechanic. A keyword with unimplemented behavior remains printed metadata and an explicit interaction gap, not a fictional approximation.

**Hybrid body-only casting:** if a verified ordinary permanent has correct costs/characteristics and the common casting lifecycle supports it, hybrid mode may allow it to resolve as the verified body/land/artifact **with a registered explicit omission of unimplemented abilities**. This remains an approximation of the *full card* and downstream decisions depending on the omitted effect are flagged. Strict mode does not claim the full card is implemented. Unsupported mandatory enters-the-battlefield effects, prohibitions or replacement effects that change whether casting/entering is legal or safe must block or require a specifically reviewed approximation; no silent ignoring.

**Example acceptance:** A verified unfamiliar `{3}{B}` 3/3 Zombie with deathtouch and unsupported triggered text can be cast using actual black mana, entered as a genuine creature object, found by a Zombie/creature/power-restricted tutor, targeted by legal removal, blocked and sacrificed through shared rules. Its unknown trigger is logged as omitted. An opponent's removal targeting it must not require the Zombie's own card implementation. If it has an unimplemented protection/ward restriction, target eligibility must be marked uncertain or blocked rather than incorrectly assumed legal.

**The trust boundary:** printed characteristics are verified data, not guessed from an archetype. Effects remain executable only when their rule operation is fully supported or an explicit simplified handler exists. Roles and archetypes are *descriptive annotations*, not sources of permission, keywords or targeting restrictions.

## Three execution modes and fidelity contract

- **strict** (default for regression): same current exact/supported-subset rules; unsupported effects cannot execute; capabilities and omissions are reported. No hybrid fallback changes strict outcomes.
- **observation** (first useful milestone): draw/mulligan/land, hand, source, and prospective response reporting using verified characteristics. Do not resolve unsupported actions or claim they happened. In a lightweight observation trace, distinguish modeled mana from legal source-paid action execution. An opponent event is labeled a supplied scenario.
- **hybrid** (opt-in): exact validated mechanics take precedence; per-card or per-ability **registered** simplified behavior may run using the *same* authoritative state/zone, payment, target, priority, and event primitives; unsupported components remain inert and diagnosed. If those primitives are unavailable, abstain or fall back to observation-only, not invented gameplay.
- Future **exploratory statistical proxies** are out of the MVP; if ever added, keep them a separate explicit mode and prohibit interpreting resulting win rates as validated.

For each ability/component record `exact_subset | simplified | unsupported` (with method, owner of definition, verified source, assumptions, and exclusions). A multi-ability card can have different fidelity for mana, spell face, trigger, and replacement. Never advertise a single universal percent-accuracy score.

## Immediate order: prioritized gates

### H0 — Metadata and deck readiness (after P0.5, before card batches)

1. Expand offline authoritative card identity snapshots for *all* names in a requested deck, including aliases, faces, oracle IDs, mana cost/value, color identity versus actual spell colors, type/subtype, basic land exceptions, and Commander legality. Keep data acquisition offline/outside the run loop; review ambiguous and transformed faces. Do not infer card properties from list headings or name patterns. Report missing names as a complete import diagnostic.
2. **Identity snapshot completed for v0.7:** the earlier 50-name missing-snapshot blocker has been addressed with a hash-checked, versioned Scryfall identity fixture covering all distinct names. The standalone observation path uses it; the live engine **does not** yet automatically load all its cards or execute unsupported effects. Preserve premium/budget presets and tests. Next obtain verified offline snapshots for *Mortarion current*, *Mortarion ideal*, and *Necron Dynasties*; Gisa and the older receipt-only Mortarion already have separate snapshots.
3. Add a card/ability capability matrix with strict status, simplified eligibility, and reason for unsupported status, generated from the assembled registry rather than hand-maintained version lists.
4. Cover generic Plains/Island/Swamp/Mountain/Forest/Wastes identity and any commander-color cases via metadata; do not claim functional black mana exists until the separate mana gate is met.

**Gate:** v0.7 parses with accurate metadata, names and unsupported effects are clearly accounted for, premium/budget remain regression-equivalent, and no unknown card is silently recast as a generic effect.

### H1 — Universal object participation, targeting/query and observation-only early-game instrument (can run alongside P1 extraction)

1. Introduce a canonical **card-characteristics / object-view / predicate interface** that works for every verified card, whether or not its own effect handler exists. Use one zone/face-sensitive view for both tutors, costs, targets, battlefield interactions and pilots. Expose owner/controller, object identity, types/subtypes, colors and identity, mana value, power/toughness, recognized keywords and known interaction restrictions.
2. Make shared actions query/target **unfamiliar** verified creatures, lands, artifacts and spells without depending on their own named effect handlers. Unit-test creature/artifact/color/subtype/mana-value/power predicates, destination zones and legal versus uncertain targets. Preserve all printed/derived restrictions; missing keyword rules produce an explicit gap.
3. Expose an engine-independent `DeckProvider + CardRegistry + observation runner` that accepts a seed, deck, seat, scripted threat events, and turn horizon; report actual opening seven and draw order, mulligan decisions, land drops, recognized sources, hands, and observed opponent threats.
4. Offer separate fields: `in_hand`, `playable_now` (exact registered legality), `candidate_if_supported` (metadata-based potential), `reserved_mana`, `response_condition`, `not_modeled`. Never treat a possible response as a successfully countered threat.
5. Support a bounded scripted opponent threat vocabulary (type, mana value, spell/permanent, turn, target/urgency). Do not turn a probabilistic threat description into a fabricated opponent deck.
6. Emit fixed-seed six-turn narratives; begin with v0.7 and compare a strict premium trace. Record first unmodeled choice and censor outcome claims downstream when material.

**Gate:** v0.7 produces one reproducible narrative with correctly labeled gaps, conservation of physical cards, and a measured single-run baseline; **an unfamiliar verified creature can be found with an implemented tutor and inspected as a valid removal target without its own effect implementation**; the same input is replayable.

### H1.5 — Per-ability composition, exact-first promotion and persistent shared keywords (P0.65; required before H2)

Use the **binding [ability composition contract](ABILITY_COMPOSITION_ARCHITECTURE.md)**. This is the immediate architectural milestone once P0.6's identity/queries are available; build the pure registry/dispatcher independently from the old runtime, then wire it into the single authoritative state.

1. Extend `CardIdentity` / face metadata with **verified source text, printed keywords, layout and characteristics** without treating Oracle prose as executable. Recognize that multi-face mana values, variable P/T and keyword declarations may still be unknown; flag rather than invent. Keep the Scryfall network fetch at an explicit **import/refresh time only**. Cached offline hash-checked snapshots are the only runtime data source.
2. Define reviewed typed `AbilitySlot` declarations keyed by **Oracle ID + face + ability slot**, independently from spell/creature bodies and global keyword rules. Include ability kind, timing, target/query predicate, costs, trigger/event hook, effect composition, source revision, needed engine capabilities and omitted text. Generic role labels are *not* permissions or effects.
3. Implement a deterministic **one-handler-per-slot resolver**: strict selects validated exact only; hybrid selects exact else an explicitly registered reviewed simplified implementation else unsupported; observation resolves no unsupported/simplified ability. A later exact handler **replaces only its matching simplified slot**. Separate abilities and shared double strike/flying/deathtouch/etc. remain active. Split partially exact behavior into disjoint typed suboperations only if proven non-overlapping; otherwise abstain. No double triggers/searches/damage/zone moves.
4. Keep standard Magic core and supported keyword mechanics globally shared: a creature with printed double strike uses the common two-damage-step engine when implemented, regardless of whether its unique ETB trigger is exact or simplified. Reusable effect compositions (draw, token creation, counter, search, sacrifice, damage/life, recursion) use common legality, payment, target, zones and events; individual named cards only parameterize or replace their **own** ability slots.
5. Maintain per-ability provenance and fidelity logs: source snapshot, slot/handler revision, exact/simplified/unsupported, assumptions, objects/events touched, downstream-dependent choices and per-metric uncertainty. Report available behaviors at card **and ability** granularity, not just “this card implemented.”
6. Write the **promotion regression** before modifying legacy gameplay: (a) a simplified creature tutor upgraded to its exact conditional destination without two searches/reveals/shuffles; (b) a creature with independent double strike + unique triggered ability retains double strike and every unrelated slot after exact trigger promotion; (c) two imported cards use one generic keyword/effect implementation without new card-specific engine code; (d) an unfamiliar creature remains targetable by implemented opponent removal/tutors even if its personal triggered ability is unsupported; (e) UNKNOWN restrictions never become legal.

**Gate:** pure ability-registry tests and at least one current-engine vertical slice prove exclusive slot-level override, persistent independent keywords and common objects, explicit unknown behavior, and unchanged strict seeded baselines. H2 cannot be called complete until this gate passes.

### H2 — Minimal hybrid effects on shared primitives (depends on H1.5/P0.65; work with P1/P2, no new table inheritance layer)

1. Wire H1.5's reviewed per-ability descriptors and **one selected handler per slot** into the live authoritative engine: an exact implementation supersedes only its own simplified implementation, with unrelated supported keywords, static rules, activated and triggered abilities intact. No whole-card replacement or duplicate event emission.
2. Support verified-body-only casting of ordinary creatures/permanents through the same legal action, mana, timing, zone and combat lifecycle in hybrid mode; never collapse them into effectless placeholders or silently drop mandatory restrictions. Track unsupported abilities that might alter resolution or choices, and allow interaction from opponents/other cards using the same predicates and game objects.
3. Build the first handful of **typed, parameterized** templates: ordinary colored land / conditional tapped land, mana rock, simple draw/filter, token creation, cast-triggered direct damage, conditional counterspell, and bounce/removal. Start only when real cost/timing and required effect primitives exist. Give all instances explicit restrictions and target validation; do not allow a counter to hit an illegal spell type or mana value.
4. Require shared zone transitions, source-specific mana, target validation and reaction windows. For primitives not yet supported, report a blocked simplified action rather than directly altering state in an ad-hoc shortcut.
5. For temporary cards, supply a small reviewed mapping from verified printed features **and individual ability declarations** to template parameters; no runtime Oracle parsing and no automatic effects granted by an archetype label. One template must serve at least two distinct cards, without a name branch or new table subclass. For tutors, encode known restrictions explicitly; never silently grant a broader search than the real rules permit.
6. Run `strict` and `hybrid` from identical starting seeds/snapshots. Ensure strict traces and stored fingerprints remain unchanged.

**Gate:** one v0.7 run makes more meaningful choices than observation alone while visibly labeling every approximate action; an unfamiliar creature/permanent can be *interacted with* by supported removal, a tutor and an opponent without its own card-specific handler; **a simplified tutor is replaced by exact text while independent keywords and other abilities remain active**; strict gameplay remains identical, and at least two cards reuse each new template.

### H3 — Generalized colors, reusable keywords, and archetype composition (promote ahead of additional premium-specific effects)

1. Fold all W/U/B/R/G/C production and payments into shared domain types and source-cost planning; separate colored mana from generic and explicit colorless. Validate basic Swamp and simple black spells before mono-black hybrid narratives. This remains the P3 rules work; observation-only can run sooner without claiming valid black source payments.
2. Expand reusable **effect primitives**: choose, draw, discard/loot/rummage, scry/surveil, mana, create tokens, deal damage versus lose/gain life, counter, bounce/destroy, search/reveal/shuffle, sacrifice, exile/return, and graveyard movement. Preserve actual objects and batch events where implemented.
3. Add declarative **keyword templates** prioritized by reuse: flying/vigilance/haste/trample/lifelink/deathtouch; flashback, adventure, escape, buyback, convoke, kicker, cycling, prowess, magecraft and cast/dies/ETB triggers. Use timing/cost/permission/event compositions rather than a keyword-as-spell shortcut. Unsupported complex layers/replacements explicitly fail closed.
4. Add **card-role archetypes** as composable profiles, not replacement card identities: mana dork/rock; cantrip/loot; counter/tax counter; targeted removal; token maker; spellslinger pinger; sac outlet; aristocrat drain; recursion/reanimation; finisher. Roles help pilots rank choices and choose documented simplified templates but must never grant unspecified effects, mana, targets or keywords.
5. Expand typed **target/query archetypes**, reusable across all cards: creature, nontoken creature, artifact, enchantment, instant/sorcery spell, subtype (Zombie/Wizard/etc.), controlled permanent, mana value bound, power/toughness bound, color, graveyard card and legal stack object. Ensure tokens, copies, faces and zone movement preserve or recompute relevant characteristics. A removal/tutor template consumes this predicate contract rather than card names.
6. Define commander-independent pilots (development-forward, threat-aware, defensive) driven by available legal/qualified actions, not hidden library contents or generic card-name guesses.

**Gate:** importing another legal card using existing primitives requires a definition/feature mapping and focused tests, not an engine/table change. Opponent creatures and imported unfamiliar cards are fully typed targets for already-supported interactions. Shared mechanisms demonstrate at least one blue/red and one mono-black use case. No divergence between exact services and simplified template execution on the same supported subcase.

### H4 — Measurement, calibration and narrative experiments

1. For each run report: verified object/characteristic participation; successful legal targeting/search/combat; blocked or uncertain target eligibility; exact/simplified/unsupported **ability activations**; which choices consumed approximated state; first divergent turn; per-outcome dependence flags; unmodeled actions/choices; threat responses legal vs merely candidate; opponent assumptions.
2. Record metrics by fidelity: opening land/color availability, effective mana, turn commander becomes castable/actually cast, token generation, cards left in hand, answer availability, hold-up-versus-develop tradeoffs, and fraction of decisions with simplified dependencies. Do not treat an unsupported card as a blank if assessing real deck power.
3. Compare paired seeds across strict/observation/hybrid and policies. Where possible, replay a card's simplified template against its later exact implementation on equivalent states and calculate metric-specific error/coverage, rather than inventing a global accuracy percentage.
4. Run **one** engine smoke narrative and timing benchmark first, then **100** six-turn runs with 5–10 selected narratives; expand to **1,000** only after rules audits and p50/p95 timing. No 10,000-run campaign before establishing that sampled actions are sensible.
5. Present stratified narratives: fast setup, mulligan/color screw, threat-aware hold-up, flood, pressure, and combo potential. Preserve seed, deck hash, rules revision, mode and all input scenario assumptions.

**Gate:** narrative playback explains every notable action and assumption, new code reports honest confidence limits, and differences between strict and hybrid are attributable to logged simplified effects.

## Current implementation inventory (checked 2026-10-31)

**Present:** offline Scryfall snapshots for Flameslinger, Wretched Ranks and an earlier receipt-only Mortarion candidate; `CardRegistry` immutable identities for supported layouts; `Query` conservative YES/NO/UNKNOWN predicates; basic-land six-turn observation; a narrow live-library ordinary U/R verified-creature bridge (strict casting remains unimplemented). P0.5 shares the current historical Magnus-v35 engine for validated compatible deck composition. Latest observed CI at `d0de7d9` passed.

**Not yet present:** universal verified body casting, full face-sensitive characteristic/keyword handling, full B-mana source/payment in live engine, multiple real decks, complete cross-card targets, reusable ability-slot declarations and exact/simplified override resolver, or executable hybrid mode. Old documents describing H0/H1 as entirely future are therefore dated; their **full exit gates** remain open. Do not treat an observation projection as a played game.

**Missing snapshot fixtures:** obtain reviewed hash-checked identities for *Mortarion current ordered-plus-owned*, *Mortarion ideal*, and *Necron Dynasties* (different decks from the receipt-only Mortarion snapshot). All Scryfall calls happen outside game simulation.

## Implementation safeguards

- **No silent upgrade**: metadata-known + effect-unknown does not mean "creature = vanilla creature" or "instant = draw a card". A safe known creature body may exist independently of its ability; disclose the missing text.
- **No blanket accuracy numbers**: report dependencies per metric, per decision and per ability, not an unjustifiable fidelity percent.
- **No strategic leakage**: pilots see only current public/allowed private information; never reveal hidden cards to make a simplified card more useful.
- **No blanket pseudo-rules**: do not skip cost payment, timing, target legality, stack, priority, SBA, Commander identity restrictions, or conservation checks in the hybrid engine.
- **No separate shadow game state**: every executable approximation uses the shared authority; observation-only can make projections, visibly labeled.
- **No whole-card overwrite**: exact implementation replaces only the same ability slot's simplified handler, not printed identity, shared keywords or unrelated abilities. Never execute both exact and simplified handlers for the same slot or double-subscribe to events.
- **No role-to-rule shortcuts**: Oracle text and archetype labels guide reviewed registration, never automatically create unrestricted tutor, mana, attack, removal or trigger effects.
- **No unsupported infinite loops**: bounded execution and resource accounting remain mandatory.
- **Coverage is not win-rate validity**: arbitrary cards, unresolved opponent policies, and omitted triggered abilities can bias outcomes; performance results remain exploratory.

## Code structure and suggested interfaces (design targets, not currently shipped APIs)

- `CardIdentity` / `FaceIdentity`: verified immutable printed characteristics/provenance.
- `AbilitySlot` / `AbilityDefinition`: stable Oracle ID+face+slot identifiers, reviewed typed capabilities and restrictions, independent of strategy; one exact-first implementation selected per slot, preserving other slots.
- `EffectTemplate` / `KeywordTemplate`: bounded parameterized compositions of canonical operations.
- `RoleProfile`: reviewed strategic tags, separate from rules text and legality.
- `FidelityRecord`: per-ability execution level, selected handler/version, assumptions, omitted sub-effects, downstream dependencies and provenance.
- `SimulationConfig(mode, deck, seed, threat_schedule, pilot)` and a single result/report pipeline.
- `ApproximationEvent`: ability, action/decision, created state IDs, affected metrics, and dependent later actions.

These names are illustrative; prefer the package's established domain conventions when implementing.

## Reusable interaction acceptance matrix (required before broad named-card batches)

| Situation | Expected observation/execution | Confidence boundary |
|---|---|---|
| Unknown-effect 3/3 Zombie battlefield permanent | Has real type/subtype, P/T, owner/controller, zone identity; is targetable by eligible removal and blockable as an ordinary creature | Unknown trigger omitted with dependencies; known targeting restrictions must not be silently ignored |
| Implemented creature tutor searches unfamiliar card | Finds it by creature/Zombie/printed power or mana-value predicate; reveals, shuffles and places it correctly | Tutor effect and metadata verified; target card's own effects not needed |
| Implemented removal vs unfamiliar permanent | Uses verified artifact/creature/enchantment predicates, costs, target legality and zone transition | Distinguish targetable, target conditional, unmodeled protection or replacement |
| Printed keyword on new creature | Registered shared flying/haste/deathtouch/etc. behavior activates without card-specific code | Unimplemented keyword explicitly marked; body remains typed |
| Opponent targets user's unfamiliar creature | Same target filters and priority apply to both seats; no named-card special case | Scripted opponent assumptions separately flagged |
| Mono-black unfamiliar creature | Swamp pays black cost, object is cast/targeted/sacrificed/dies correctly | Only after P3 all-color mana/event gates pass |

**Test standards:** include a new card with its own ability unsupported, a second newly imported card sharing a keyword, an existing implemented tutor, removal from an opponent seat, a token copy, a double-faced/Adventure characteristics check, and a card with an interaction restriction that must fail closed. Use deterministic fixtures. Confirm no hypothetical target is reported as a resolved answer.

## First acceptance demonstrations

1. **v0.7 temporary Magnus** loads from the authoritative file; missing-snapshot identities are supplied offline; strict mode reports gaps, observation mode narrates six turns, hybrid makes at least one meaningful ordinary action with an explicit simplified handler.
2. **v1.14 premium** retains strict seed/reference parity, and the same current engine/registry accepts the deck without a premium-only class.
3. **Mono-black fixture** uses genuine Swamp/B payments once the common mana gate passes; demonstrate a draw creature, a simple sac outlet and a death/life-change template with recorded fidelity. Later import the user's actual mono-black list only from a verified decklist; do not infer its contents.
4. **Template/override reuse test**: two independently registered cards share a template with different parameters, each exposes correct timing, targets and costs and no new engine subclass is introduced. An exact version replaces a simplified tutor **only on its own ability slot**; a separate triggered ability and common combat keyword remain unchanged; event/zone operations occur exactly once.
5. **Audit/review report**: strict versus hybrid per-metric differences, censored outcomes, benchmark times and limitations for every demonstration.

## Terra implementation cadence

- Continue the partially built H0/H1 identity, observation and universal object/query layer; **complete H1.5/P0.65 declarative ability composition and promotion tests before calling H2 executable hybrid complete**. Then implement a small H2 slice on real rules services while P1/P2 are extracted; prioritize H3 shared effects/keywords before any broad named-card batch.
- Commit each working gate independently with tests, an example narrative, updated coverage and a short performance record. Do not require an entire phase to finish before shipping a usable observation path.
- Escalate decisions that change priority, payments, identity, event batching, or reproducibility to architectural review. Keep historical implementations regression-accessible.
- Revisit individual-card queue only when a reusable template is missing or a high-impact card supplies a second independent validation of a mechanism.
