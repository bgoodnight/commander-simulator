# Hybrid simulation and reusable behavior — implementation work plan

Status: **approved planning direction; not yet implemented**. Read with [ROADMAP.md](../ROADMAP.md), [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md), and the [P0.5 engine review](P05_ENGINE_REVIEW.md). This document prioritizes value from an unfamiliar validated deck **before** full per-card rules coverage. Existing strict rules, validated metadata, and historical results remain the correctness baseline.

## Goal and non-goals

**Goal:** Given a legitimate new decklist (including the temporary Magnus Flameslinger v0.7 and, later, an authenticated mono-black list), produce meaningful opening-hand, mana, deployment, interaction-availability, resource, and turn-by-turn narrative diagnostics without implementing every card individually. Reuse implemented rules and common effect/keyword templates, and label assumptions and the extent to which downstream decisions depend on them.

**Not goals:** a perfect Magic rules engine, autonomous interpretation/execution of Oracle prose, unqualified win-rate estimates, arbitrary cards automatically acquiring effects, hiding impossible plays, or modifying strict semantics to help approximate runs succeed.

Separately track **identity confidence**, **functional coverage**, and **outcome dependence**. A verified card identity is neither proof that the rules are implemented nor permission to guess the card's effect.

## Three execution modes and fidelity contract

- **strict** (default for regression): same current exact/supported-subset rules; unsupported effects cannot execute; capabilities and omissions are reported. No hybrid fallback changes strict outcomes.
- **observation** (first useful milestone): draw/mulligan/land, hand, source, and prospective response reporting using verified characteristics. Do not resolve unsupported actions or claim they happened. In a lightweight observation trace, distinguish modeled mana from legal source-paid action execution. An opponent event is labeled a supplied scenario.
- **hybrid** (opt-in): exact validated mechanics take precedence; per-card or per-ability **registered** simplified behavior may run using the *same* authoritative state/zone, payment, target, priority, and event primitives; unsupported components remain inert and diagnosed. If those primitives are unavailable, abstain or fall back to observation-only, not invented gameplay.
- Future **exploratory statistical proxies** are out of the MVP; if ever added, keep them a separate explicit mode and prohibit interpreting resulting win rates as validated.

For each ability/component record `exact_subset | simplified | unsupported` (with method, owner of definition, verified source, assumptions, and exclusions). A multi-ability card can have different fidelity for mana, spell face, trigger, and replacement. Never advertise a single universal percent-accuracy score.

## Immediate order: prioritized gates

### H0 — Metadata and deck readiness (after P0.5, before card batches)

1. Expand offline authoritative card identity snapshots for *all* names in a requested deck, including aliases, faces, oracle IDs, mana cost/value, color identity versus actual spell colors, type/subtype, basic land exceptions, and Commander legality. Keep data acquisition offline/outside the run loop; review ambiguous and transformed faces. Do not infer card properties from list headings or name patterns. Report missing names as a complete import diagnostic.
2. Fix the known 50-name missing-snapshot blocker for the **actual recovered v0.7** file; include it in repository fixtures only from a verified source. Preserve existing premium and budget presets and their tests.
3. Add a card/ability capability matrix with strict status, simplified eligibility, and reason for unsupported status, generated from the assembled registry rather than hand-maintained version lists.
4. Cover generic Plains/Island/Swamp/Mountain/Forest/Wastes identity and any commander-color cases via metadata; do not claim functional black mana exists until the separate mana gate is met.

**Gate:** v0.7 parses with accurate metadata, names and unsupported effects are clearly accounted for, premium/budget remain regression-equivalent, and no unknown card is silently recast as a generic effect.

### H1 — Observation-only early-game instrument (can run alongside P1 extraction)

1. Expose an engine-independent `DeckProvider + CardRegistry + observation runner` that accepts a seed, deck, seat, scripted threat events, and turn horizon; report actual opening seven and draw order, mulligan decisions, land drops, recognized sources, hands, and observed opponent threats.
2. Offer separate fields: `in_hand`, `playable_now` (exact registered legality), `candidate_if_supported` (metadata-based potential), `reserved_mana`, `response_condition`, `not_modeled`. Never treat a possible response as a successfully countered threat.
3. Support a bounded scripted opponent threat vocabulary (type, mana value, spell/permanent, turn, target/urgency). Do not turn a probabilistic threat description into a fabricated opponent deck.
4. Emit fixed-seed six-turn narratives; begin with v0.7 and compare a strict premium trace. Record first unmodeled choice and censor outcome claims downstream when material.

**Gate:** v0.7 produces one reproducible narrative with correctly labeled gaps, conservation of physical cards, and a measured single-run baseline; the same input is replayable.

### H2 — Minimal hybrid effects on shared primitives (work with P1/P2; do not create another table inheritance layer)

1. Add opt-in ability descriptors and dispatch *at ability level* with exact-first selection: an exact handler overrides/blocks a simplified handler for that ability, while other unsupported abilities on the card remain independently reported.
2. Build the first handful of **typed, parameterized** templates: ordinary colored land / conditional tapped land, mana rock, simple draw/filter, token creation, cast-triggered direct damage, conditional counterspell, and bounce/removal. Start only when real cost/timing and required effect primitives exist. Give all instances explicit restrictions and target validation; do not allow a counter to hit an illegal spell type or mana value.
3. Require shared zone transitions, source-specific mana, target validation and reaction windows. For primitives not yet supported, report a blocked simplified action rather than directly altering state in an ad-hoc shortcut.
4. For temporary cards, supply a small reviewed mapping from verified printed features to template parameters; no runtime Oracle parsing. One template must serve at least two distinct cards, without a name branch or new table subclass.
5. Run `strict` and `hybrid` from identical starting seeds/snapshots. Ensure strict traces and stored fingerprints remain unchanged.

**Gate:** one v0.7 run makes more meaningful choices than observation alone while visibly labeling every approximate action, exact gameplay remains identical, and at least two cards reuse each new template.

### H3 — Generalized colors, reusable keywords, and archetype composition (promote ahead of additional premium-specific effects)

1. Fold all W/U/B/R/G/C production and payments into shared domain types and source-cost planning; separate colored mana from generic and explicit colorless. Validate basic Swamp and simple black spells before mono-black hybrid narratives. This remains the P3 rules work; observation-only can run sooner without claiming valid black source payments.
2. Expand reusable **effect primitives**: choose, draw, discard/loot/rummage, scry/surveil, mana, create tokens, deal damage versus lose/gain life, counter, bounce/destroy, search/reveal/shuffle, sacrifice, exile/return, and graveyard movement. Preserve actual objects and batch events where implemented.
3. Add declarative **keyword templates** prioritized by reuse: flying/vigilance/haste/trample/lifelink/deathtouch; flashback, adventure, escape, buyback, convoke, kicker, cycling, prowess, magecraft and cast/dies/ETB triggers. Use timing/cost/permission/event compositions rather than a keyword-as-spell shortcut. Unsupported complex layers/replacements explicitly fail closed.
4. Add **card-role archetypes** as composable profiles, not replacement card identities: mana dork/rock; cantrip/loot; counter/tax counter; targeted removal; token maker; spellslinger pinger; sac outlet; aristocrat drain; recursion/reanimation; finisher. Roles help pilots rank choices and choose documented simplified templates but must never grant unspecified effects, mana, targets or keywords.
5. Define commander-independent pilots (development-forward, threat-aware, defensive) driven by available legal/qualified actions, not hidden library contents or generic card-name guesses.

**Gate:** importing another legal card using existing primitives requires a definition/feature mapping and focused tests, not an engine/table change. Shared mechanisms demonstrate at least one blue/red and one mono-black use case. No divergence between exact services and simplified template execution on the same supported subcase.

### H4 — Measurement, calibration and narrative experiments

1. For each run report: exact/simplified/unsupported **ability activations**; which choices consumed approximated state; first divergent turn; per-outcome dependence flags; unmodeled actions/choices; threat responses legal vs merely candidate; opponent assumptions.
2. Record metrics by fidelity: opening land/color availability, effective mana, turn commander becomes castable/actually cast, token generation, cards left in hand, answer availability, hold-up-versus-develop tradeoffs, and fraction of decisions with simplified dependencies. Do not treat an unsupported card as a blank if assessing real deck power.
3. Compare paired seeds across strict/observation/hybrid and policies. Where possible, replay a card's simplified template against its later exact implementation on equivalent states and calculate metric-specific error/coverage, rather than inventing a global accuracy percentage.
4. Run **one** engine smoke narrative and timing benchmark first, then **100** six-turn runs with 5–10 selected narratives; expand to **1,000** only after rules audits and p50/p95 timing. No 10,000-run campaign before establishing that sampled actions are sensible.
5. Present stratified narratives: fast setup, mulligan/color screw, threat-aware hold-up, flood, pressure, and combo potential. Preserve seed, deck hash, rules revision, mode and all input scenario assumptions.

**Gate:** narrative playback explains every notable action and assumption, new code reports honest confidence limits, and differences between strict and hybrid are attributable to logged simplified effects.

## Implementation safeguards

- **No silent upgrade**: metadata-known + effect-unknown does not mean "creature = vanilla creature" or "instant = draw a card". A safe known creature body may exist independently of its ability; disclose the missing text.
- **No blanket accuracy numbers**: report dependencies per metric, per decision and per ability, not an unjustifiable fidelity percent.
- **No strategic leakage**: pilots see only current public/allowed private information; never reveal hidden cards to make a simplified card more useful.
- **No blanket pseudo-rules**: do not skip cost payment, timing, target legality, stack, priority, SBA, Commander identity restrictions, or conservation checks in the hybrid engine.
- **No separate shadow game state**: every executable approximation uses the shared authority; observation-only can make projections, visibly labeled.
- **No unsupported infinite loops**: bounded execution and resource accounting remain mandatory.
- **Coverage is not win-rate validity**: arbitrary cards, unresolved opponent policies, and omitted triggered abilities can bias outcomes; performance results remain exploratory.

## Code structure and suggested interfaces (design targets, not currently shipped APIs)

- `CardIdentity` / `FaceIdentity`: verified immutable printed characteristics/provenance.
- `AbilityDefinition`: typed capabilities and restrictions, independent of strategy.
- `EffectTemplate` / `KeywordTemplate`: bounded parameterized compositions of canonical operations.
- `RoleProfile`: reviewed strategic tags, separate from rules text and legality.
- `FidelityRecord`: per-ability execution level, assumptions, omitted sub-effects and provenance.
- `SimulationConfig(mode, deck, seed, threat_schedule, pilot)` and a single result/report pipeline.
- `ApproximationEvent`: ability, action/decision, created state IDs, affected metrics, and dependent later actions.

These names are illustrative; prefer the package's established domain conventions when implementing.

## First acceptance demonstrations

1. **v0.7 temporary Magnus** loads from the authoritative file; missing-snapshot identities are supplied offline; strict mode reports gaps, observation mode narrates six turns, hybrid makes at least one meaningful ordinary action with an explicit simplified handler.
2. **v1.14 premium** retains strict seed/reference parity, and the same current engine/registry accepts the deck without a premium-only class.
3. **Mono-black fixture** uses genuine Swamp/B payments once the common mana gate passes; demonstrate a draw creature, a simple sac outlet and a death/life-change template with recorded fidelity. Later import the user's actual mono-black list only from a verified decklist; do not infer its contents.
4. **Template reuse test**: two independently registered cards share a template with different parameters, each exposes correct timing, targets and costs and no new engine subclass is introduced.
5. **Audit/review report**: strict versus hybrid per-metric differences, censored outcomes, benchmark times and limitations for every demonstration.

## Terra implementation cadence

- Deliver H0/H1 first for immediate user value, then H2 slice while P1/P2 are extracted; prioritize H3 shared effects/keywords before another broad named-card batch.
- Commit each working gate independently with tests, an example narrative, updated coverage and a short performance record. Do not require an entire phase to finish before shipping a usable observation path.
- Escalate decisions that change priority, payments, identity, event batching, or reproducibility to architectural review. Keep historical implementations regression-accessible.
- Revisit individual-card queue only when a reusable template is missing or a high-impact card supplies a second independent validation of a mechanism.
