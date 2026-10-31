# Internal development guide

Implementation contract for subsequent work. Follow [ROADMAP.md](../ROADMAP.md) and the [Hybrid Simulation Work Plan](HYBRID_SIMULATION_WORKPLAN.md); the [audit](ARCHITECTURE_AUDIT.md) explains the priorities. These are future design targets, not components claimed to exist already.

## Dependency direction

`GameConfig + DeckDefinitions -> composed Engine -> rules/services -> effect primitives`

Card/keyword definitions depend on stable domain types and registered capabilities. The core must not import a deck, commander name, card-specific table or pilot. Pilots consume observations and legal choices; they do not own rules. Reports consume events/results. Complex cards may need a registered extension, but may not replace a shared service or add another table subclass.

Use a normal Python package, provisionally `commander_sim/`, separating domain types, state/queries, engine/stack, costs, effects, keywords, card definitions and pilot/reporting adapters. Exact module names can change during extraction. Public API: construct game, load deck/registry, enumerate legal actions, commit choice, advance priority/steps, obtain results.

## Three reuse levels

1. **Rule primitives:** authoritative zone changes, source/target identity, payment, damage versus life changes, priority, state-based actions and events.
2. **Effect blocks:** draw, choose, search, reveal, reorder, move-zone, create-token batch, add-mana, deal-damage, lose/gain-life, modifier, counter, copy-spell and grant-permission. Compose with explicit sequencing, quantities, predicates and destinations.
3. **Keyword/ability templates:** expand into costs, permissions, targeting, effects, continuous restrictions and replacements. A keyword is not necessarily a resolution effect. Cards parameterize templates.

Begin with typed Python dataclasses/functions and small registries, not an unrestricted language or runtime Oracle-prose parser. Validate schemas and unsupported capabilities at load time.

| Mechanic | Shared pieces | Preserve these distinctions |
|---|---|---|
| Tutors | Query, choice, reveal, move, shuffle/top placement | Search restrictions, destinations, order, declining versus failing to find |
| Scry / surveil | Look, partition/order choice, move/reorder | Bottom versus graveyard and distinct keyword events |
| Buyback | Additional cost + successful-resolution destination replacement | Countered/fizzled spells do not return through buyback |
| Flashback / escape / Adventure | Cast permission, face/zone choice, costs, destination policy | Different permissions, extra costs and destination rules; share parts, not semantics |
| Convoke / sacrifice-for-mana | Payment planning, reservations, dependencies | No double-spending a creature; total costs fixed at the right point |
| Cast/copy triggers | Event predicate + effect sequence | Copying is not casting |
| Damage / drain / life payment | Recipients, quantities, event infrastructure | Damage, losing/gaining life and paying life are separate operations |
| Flying / deathtouch / lifelink | Blocking, damage and SBA rule hooks | These are not all on-resolution modifiers |

## Universal card interactions and fidelity contracts

**Every verified card is a typed physical game object before its special abilities are implemented.** A card with unknown effect text does not lose its actual card types, subtypes, mana value, color, power/toughness, recognized keywords, zone identity, owner or controller. Printed traits must come from verified face-sensitive data; do not guess them from name or role tags.

**Separation of responsibilities**

- `CardIdentity/FaceCharacteristics`: authoritative printed card data; verified cost, type line, subtypes, color, P/T, keyword declarations and provenance.
- `DerivedCharacteristics/TargetPredicate`: read-only, zone-sensitive queries including face, type, subtype, mana value, power/toughness, controller, color, known restrictions and stack/battlefield/graveyard/library. Operates identically whether the target card's own ability is supported or unsupported. Recompute on mutations/copies/transforms instead of maintaining parallel maps.
- `AbilityRegistration/EffectTemplate`: optional executable functionality, exact or reviewed simplified, with timing/target/cost/zone restrictions and explicit prerequisites. An unsupported ability must not prevent a verified creature from being recognized by a supported tutor or removal effect.
- `RoleProfile`: descriptive pilot-facing archetype such as ramp source, Zombie, token maker, counter, removal, spell-trigger damage, sacrifice or recursion. **A role alone never grants an ability or a targeting permission.**
- `FidelityRecord`: per-component `verified_characteristic | exact_subset | simplified | unsupported | unknown_legality`, approximation assumptions, omitted behaviors, and downstream-dependent choices. Printed identity confidence is separate from modeled effect fidelity.

**Targeting/query contract:** An implemented tutor that finds an artifact, Wizard, creature with power <= 2, instant with mana value <= 2, or other verified legal candidate must find unfamiliar qualifying cards. Similarly, a supported removal spell, opponent spell or block/combat rule must interact with the same target's verified characteristics without a card-specific handler. Tutors have their own actual search rules; an unfamiliar card need not have its own effects implemented to be found. Missing target restrictions (e.g., ward, hexproof, protection, conditional static/continuous effects) are not silently treated as absent; block the action or mark its legality conditional until supported.

**Hybrid permanent body contract:** Only when real casting/payment/priority/permanent zone handling is supported, an explicitly registered hybrid behavior may put a verified creature/permanent body onto the battlefield, with printed P/T/types/recognized keywords, even when its separate special abilities are omitted. Log omissions and dependent events. Do not silently ignore mandatory cast/ETB/replacement/prohibitive abilities that may alter legality, costs or zone outcomes. Strict mode retains its established semantics; observation mode does not pretend any unsupported action actually resolved.

**Shared keyword contract:** Implement flying, haste, vigilance, trample, deathtouch, lifelink, prowess, magecraft, cycling, flashback, adventure, convoke, buyback, escape and other features via reusable rule mechanisms when feasible. Keyword labels alone do not implement those mechanics. In addition to normal card tests, require a newly imported *second card* to exercise each template without a new table subclass.

**Acceptance tests:** An unfamiliar verified Zombie creature with unsupported triggered text can (in hybrid under allowed prerequisites) pay actual black mana, enter as a 3/3 with a registered keyword, be found by a creature/Zombie/power tutor, be targeted by legal removal from an opposing seat, be blocked, be sacrificed and die with correct zone/identity effects. An unimplemented protection restriction must prevent false certainty. Separately verify a blue/red unfamiliar creature, an artifact target, a token, a modal/Adventure face-sensitive query, and a candidate-only response against a scripted opposing spell. Check card conservation and strict-mode replay parity. Prerequisite black mana/event gates remain explicit; these tests do not justify fabricating missing capabilities.

## Domain contracts

- **Characteristics:** immutable printed definitions/faces plus zone-sensitive derived values. Views, search, **tutor predicates**, target legality, costs, tokens, generic combat, sacrifice, opponent interaction and copies use one service **even when target card abilities are unsupported**; no parallel color/mana-value maps in handlers.
- **Identity:** source object and zone incarnation, stable action/stack IDs, distinct owner/controller. Copy snapshots capture modes, targets, X and relevant paid choices. Do not select physical sources by card name or identify actions with Python `id()`.
- **Choices:** immutable target groups with domain, cardinality, distinctness and retain/reselect rules; typed optional choices and quantities. No dynamic action attributes such as `step_targets`.
- **Lifecycle:** validate intent/permissions; choose modes/targets; compute total cost; plan/validate payments; commit costs and stack entry; emit cast; resolve/recheck targets; apply destination policy. Copies use snapshots without casting/payment.
- **Mutation:** validate a choice before mutating that operation. Do not undo previously legal casting costs because a later resolution choice fails. Errors must leave a diagnosable, consistent state.
- **Events:** typed source/target/cause and last-known snapshots. Separate history from dispatch; batch simultaneous operations before proper SBA and APNAP placement. Do not recursively dispatch arbitrary triggers midway through costs/effects.
- **Strategy:** definitions contain rules; pilots rank legal actions using supported observations without hidden-library leakage. Frozen frames wrapping mutable actions are insufficient isolation.
- **Capabilities:** reject missing operations/predicates/keywords at load in strict mode. Hybrid handlers are explicit reviewed opt-ins and never bypass needed rule legality; observation tracks candidate actions without executing them. Unknown effects fail closed or are visibly omitted in body-only approximations. Printed characteristics remain usable for generic queries/interactions where legality is known. Generate coverage from registrations plus explicit limitations.

## Workflow for each new card

1. Identify authoritative card/deck data, **its universally usable printed characteristics**, and exact supported behavior. Register a verified unfamiliar card as a target/query/combat object independently of its abilities.
2. Inventory components. Reuse a primitive/template first; change the engine only for a missing rule.
3. Define characteristics, faces, costs, abilities and limitations in the registry.
4. Test new primitives independently, then card wiring and invalidating interactions. Prefer a second card exercising reuse to a test that mirrors implementation.
5. Cover costs, timing, targets, countering, zone identity and cast/copy distinctions as applicable; include a source-paid current-engine scenario. **Test another card or opponent targeting/querying the new object**, especially when the new object's own abilities are unsupported.
6. Verify existing providers remain registered and another deck loads without this card. No instance-method patching or unrelated definition changes.
7. Run relevant contracts/integration/historical checks and justified conservation sweeps; regenerate coverage.
8. Measure matched performance if hot paths changed. Commit complete milestones and continue under existing authorization.

**Development-efficiency gate:** the second card with the same behavior should need a definition and focused integration checks, not a core name branch or table/service subclass. An unfamiliar verified card's target/search/combat participation should require **zero new named-card code** after identity ingestion. Document any genuinely missing rule that prevents this.

## Performance/testing rules

- Never omit priority/SBA windows, prune legal actions silently, hide events or relax safety limits for speed.
- Compare identical deck/rules/seeds/choices/trace mode and semantic fingerprints; differing trajectories are not a caching control group.
- First consolidate action generation and queries, maintain zone/controller indexes at mutations, avoid full-history lookbacks/unnecessary views, and separate full trace from aggregate metrics.
- Retain complete legal iteration. Pilot search/ranking budgets are separate from legality and must be labeled.
- Delay new memoization until current baselines and invalidation tests exist. Keep existing caches visible.
- Use capability contracts plus pairwise card interactions; do not duplicate the kernel suite for every card. Keep historical compatibility runs during extraction.
- Require exact replay for semantic-preserving extraction. Known fixes such as Frostboil need documented new expectations instead of preserving buggy goldens.
- Track core files touched per card, template reuse, integration coverage, initialization/run time, p50/p95, peak memory, candidates, payment states, event/stack counts and safety stops.

## Mono-black acceptance

Use normal configuration to load a black fixture with repeated Swamps, pay B/generic costs and combine it with Magnus. Demonstrate sacrifice as a cost, token/nontoken deaths, last-known power, reanimation as a new object, distinct life operations and simultaneous death triggers. No commander-name branches or direct zone/pool fixtures in the core flow. Import the user's actual mono-black list only from an identified authoritative source; do not reconstruct a precon from memory.
