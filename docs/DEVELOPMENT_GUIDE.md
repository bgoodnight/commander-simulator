# Internal development guide

Implementation contract for subsequent work. Follow [ROADMAP.md](../ROADMAP.md), the [Hybrid Simulation Work Plan](HYBRID_SIMULATION_WORKPLAN.md), and the **[Progressive Ability-Composition Architecture](ABILITY_COMPOSITION_ARCHITECTURE.md)**; the [audit](ARCHITECTURE_AUDIT.md) explains the priorities. These are future design targets, not components claimed to exist already.

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

## Binding implementation contract: progressive composition, not whole-card replacement

**P0.65 is the next architecture gate.** Before adding large numbers of card-specific handlers, create a **declarative per-ability registry** independent of execution and test it with pure data. The immutable Scryfall-derived `CardIdentity` describes printed characteristics; the derived runtime view describes actual properties in context; shared Magic keyword/rules engines provide generic behavior; reviewed typed `AbilitySlot` declarations provide individual effects. Named-card handlers may configure, extend or supersede their **own slot**, not the printed base object or unrelated slots.

**Specific implementation rules:**

1. Assign stable IDs by Oracle ID, face and ability slot. Include source revision, timing, targeting/predicate, costs, mode, resolution operation, applicable restrictions, event hook, capability prerequisites, `exact|simplified|unsupported` coverage and explicit omissions. Roles remain pilot-only until a reviewed ability declaration binds an actual operation.
2. Resolve **one selected handler per ability slot**: strict = exact only; hybrid = exact if available, else reviewed simplified if prerequisites present, else unsupported; observation = no actual unsupported or simplified resolution. The exact handler **supersedes** the simplified handler for the same slot. Unrelated printed keywords or separate effects continue independently. If part of an effect is exact, do not run an overlapping proxy on that part; split into disjoint typed suboperations and test independence or abstain.
3. Reuse global keyword/rules engines for basic combat and printed abilities, including double strike's two combat-damage steps, flying, haste, vigilance, trample, lifelink, deathtouch; do not implement one keyword anew for every card. Keyword detection from verified printed data authorizes **recognition**, not execution until the relevant rules engine is ready.
4. Reuse typed effect primitives for draw, search, shuffle, movement, token creation, targeted removal, counterspells, damage/life changes and recursion. E.g. a tutor implementation is a composition of actual search predicates, choices, reveal, destination and shuffle, with explicit restrictions—not a blanket “tutor always fetches any creature”.
5. Every unfamiliar verified card remains a real game object available to other cards' tutor, removal, combat and graveyard predicates irrespective of its own named ability support. When a known static effect/protection/ward/ETB/replacement restriction is unsupported, target legality or body-only casting must return UNKNOWN/blocked, not assume absence.
6. Keep the Scryfall API confined to **explicit offline import/refresh**. Cache hash-validated raw records; parse identities/keyword declarations from those records; store reviewed structured abilities in a versioned directory/registry keyed to Oracle identity. Do not fetch per turn, per card cast, per run, or in a test. Do not auto-execute Oracle prose or guess from roles.
7. Replay, fidelity and semantic reports must record: selected ability slot/handler version, exact vs simplified, original typed costs/targets/choices, assumptions and omitted behaviors, resulting event/object IDs, and the first approximation affecting each requested outcome. Prevent duplicate triggers or overlapping subscriptions; preserve source identity and conservation.
8. Strict premium/budget results and all historical tests remain valid. Introduce hybrid only behind an opt-in mode flag. Do not add named table subclasses or global monkey patches merely to make imported cards work.

**Required promotion regression:** An unfamiliar creature with recognized **double strike** and an independent ETB trigger can be drawn, legally targeted, and later cast when core prerequisites permit. Upgrading the ETB trigger from simplified to exact changes only that trigger; it must not remove double strike, duplicate ETB events, or change the creature's identity. Independently upgrade a reviewed simplified tutor to a constrained exact search and assert only one search/reveal/move/shuffle occurs. Repeat with a creature from a different deck and with an opponent acting as source.

**Review rejection criteria:** silent role-to-effect inference, whole-card exact-mode switch, two handlers for one ability slot, unknown restriction treated as false, fabricated costs/colors/P/T, card-name branching in central rules, introducing a second mutable game state, API requests during games, or reporting win rates as validated while unsupported material effects remain.

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
- **Capabilities:** reject missing operations/predicates/keywords at load in strict mode. Hybrid handlers are explicit **per-slot** reviewed opt-ins with exact-first supersession and never bypass needed rule legality; observation tracks candidate actions without executing them. Unknown effects fail closed or are visibly omitted in body-only approximations. Printed characteristics and independently supported keyword mechanics remain usable for generic queries/interactions where legality is known. Generate coverage from registrations plus explicit limitations.

## Workflow for each new card

1. Identify authoritative card/deck data, **its universally usable printed characteristics**, and exact supported behavior. Register a verified unfamiliar card as a target/query/combat object independently of its abilities.
2. Inventory printed keyword declarations, separate ability slots and their dependencies. Reuse a global primitive/keyword/effect template first; change the engine only for a missing shared rule. Every new exact implementation must identify the **one simplified slot it supersedes**, if any.
3. Define characteristics, faces, costs, abilities and limitations in the registry.
4. Test pure composition/override semantics first, then new primitives independently, card wiring and invalidating interactions. Prefer a second card **from another deck** exercising reuse to a test that mirrors implementation; ensure unrelated keyword and separate-ability dispatch survive exact promotion.
5. Cover costs, timing, targets, countering, zone identity and cast/copy distinctions as applicable; include a source-paid current-engine scenario. **Test another card or opponent targeting/querying the new object**, especially when the new object's own abilities are unsupported.
6. Verify existing providers remain registered and another deck loads without this card. No instance-method patching or unrelated definition changes.
7. Run registry/slot uniqueness tests, behavior promotion and no-duplicate trigger tests, source-paid current-engine examples, relevant historical checks and justified conservation sweeps; regenerate per-slot coverage and dependency reports. Confirm no API/network calls during repeated seeded runs.
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
