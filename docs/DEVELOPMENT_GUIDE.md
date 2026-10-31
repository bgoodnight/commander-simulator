# Internal development guide

Implementation contract for subsequent work. Follow [ROADMAP.md](../ROADMAP.md); the [audit](ARCHITECTURE_AUDIT.md) explains the priorities. These are future design targets, not components claimed to exist already.

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

## Domain contracts

- **Characteristics:** immutable printed definitions/faces plus zone-sensitive derived values. Views, search, costs, tokens and copies use one service; no parallel color/mana-value maps in handlers.
- **Identity:** source object and zone incarnation, stable action/stack IDs, distinct owner/controller. Copy snapshots capture modes, targets, X and relevant paid choices. Do not select physical sources by card name or identify actions with Python `id()`.
- **Choices:** immutable target groups with domain, cardinality, distinctness and retain/reselect rules; typed optional choices and quantities. No dynamic action attributes such as `step_targets`.
- **Lifecycle:** validate intent/permissions; choose modes/targets; compute total cost; plan/validate payments; commit costs and stack entry; emit cast; resolve/recheck targets; apply destination policy. Copies use snapshots without casting/payment.
- **Mutation:** validate a choice before mutating that operation. Do not undo previously legal casting costs because a later resolution choice fails. Errors must leave a diagnosable, consistent state.
- **Events:** typed source/target/cause and last-known snapshots. Separate history from dispatch; batch simultaneous operations before proper SBA and APNAP placement. Do not recursively dispatch arbitrary triggers midway through costs/effects.
- **Strategy:** definitions contain rules; pilots rank legal actions using supported observations without hidden-library leakage. Frozen frames wrapping mutable actions are insufficient isolation.
- **Capabilities:** reject missing operations/predicates/keywords at load. Unknown behavior fails closed and is reported. Generate coverage from registrations plus explicit limitations.

## Workflow for each new card

1. Identify authoritative card/deck data and the exact supported behavior.
2. Inventory components. Reuse a primitive/template first; change the engine only for a missing rule.
3. Define characteristics, faces, costs, abilities and limitations in the registry.
4. Test new primitives independently, then card wiring and invalidating interactions. Prefer a second card exercising reuse to a test that mirrors implementation.
5. Cover costs, timing, targets, countering, zone identity and cast/copy distinctions as applicable; include a source-paid current-engine scenario.
6. Verify existing providers remain registered and another deck loads without this card. No instance-method patching or unrelated definition changes.
7. Run relevant contracts/integration/historical checks and justified conservation sweeps; regenerate coverage.
8. Measure matched performance if hot paths changed. Commit complete milestones and continue under existing authorization.

**Development-efficiency gate:** the second card with the same behavior should need a definition and focused integration checks, not a core name branch or table/service subclass. Document any genuinely missing rule that prevents this.

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
