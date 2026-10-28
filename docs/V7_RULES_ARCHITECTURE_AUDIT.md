# V7 design audit — reusable rules, traits, and effect primitives

**Date:** 2026-10-28  
**Status:** Proposal only; no simulator code changed  
**Baseline:** `simulator/v5_four_player/simulation.py` and `simulator/v6_real_deck/integrated.py`, with `simulator/v3_magnus_modular/cards.json` as the earlier named-card metadata source. The v5/v6 calibration/narrative figures are diagnostic, not a validated Magnus win rate.

## Recommendation

Build a **shared, bounded, typed rules kernel** before completing the Magnus deck. Cards should store *what they are* and declarative *abilities*; the shared engine should determine whether an action is legal and how it changes game state. Use a small handler only when a genuinely unusual card cannot be composed from generic operations. Keep pilot strategy distinct from rules and deck identity. This is a deliberately scoped Commander simulator, **not a proposal to implement all Magic Comprehensive Rules**.

### Keep four layers separate

1. **Immutable card definition:** name, mana cost (all color pips and X), exact set of types/supertypes/subtypes, base characteristics, rules-defined keyword abilities, activated/triggered/static ability specifications, and data-quality/coverage status. These are data, never mutable board objects.
2. **Game object / state:** unique object ID, owner, controller, zone, tapped state, token/copy flags, counters, damage marked, attachments, summoning-sickness timestamp, and temporary effects. A token is a game object, not merely a `name == 'Token'` check. A creature can have a current type different from its printed type.
3. **Rules kernel:** targeting and protection; cost calculation and mana payment; zone transitions; event emission and trigger ordering; bounded stack, priority and countering; ability activation; damage and simultaneous state-based checks; continuous modifications; combat; commander-specific rules. All seats use it, whether their deck is detailed or synthetic.
4. **Agents and reporting:** a deck provider supplies exact cards or a stochastic category bag; its pilot chooses among **legal actions provided by the kernel**. The separate log/metrics layer records state changes, approximations, and unsupported interactions. Swap the provider/pilot without subclassing the table.

### Distinguish three concepts often all called “keywords”

| Concept | Examples | What it does |
| --- | --- | --- |
| **Card characteristics** | instant, sorcery, creature, artifact, enchantment, Wizard, Shaman, legendary | Tell effects which objects qualify; these are sets, not mutually exclusive categories |
| **Rule-defined keyword abilities** | flying, haste, reach, indestructible, hexproof, ward, vigilance, trample, lifelink, deathtouch | Invoke shared rule implementations; keyword may be added/removed dynamically |
| **Strategic/card-index tags** | `token_engine`, `counter`, `finisher`, `selection` | Help pilot preferences and card discovery; **must never determine spell legality or rules effects** |

Similarly, **+1/+1 counters** are persistent markers on objects, **countering a spell** is an action on an object on the stack, and **counters on a player** are yet another distinct state. Their shared English word must not conflate the implementations.

## Reusable capability inventory

Priority is for making the existing Magnus v1.6 deck meaningful, not for exhaustive coverage of every Magic keyword. `core` means implement before expanding cards, `next` when a named card needs it, `later` only if a deck/matchup requires it. An abstract opponent must use the same primitive when that primitive applies.

| Family | Core reusable operations / characteristics | Magnus/deck examples | Priority |
| --- | --- | --- | --- |
| Card identity and typing | `types`, `subtypes`, `supertypes`, `is_spell`, `is_creature`, `is_instant_or_sorcery` derived queries | Magnus filters **instants and sorceries**; Harmonic Prodigy checks Wizard/Shaman; Arcane Adaptation changes types | core |
| Zones and game objects | library/hand/stack/battlefield/graveyard/exile/command; move/reveal/draw/discard/shuffle; owner/controller; object IDs; tokens and copies | Commander tax, Underworld Breach, spell countering, copying Stormsplitter | core |
| Cost and mana | colored pips, generic, X, optional/additional/alternative costs; restricted mana; rocks, Treasure, sacrifice, tap, reductions; cost computed before payment | Magnus only reduces **generic** instant/sorcery costs; Baral/Electromancer; Phyrexian Altar; buyback | core |
| Spell/ability actions | cast/activate/trigger/copy, cast-time modes, source and targets, cost choices, target legality, spell counter, fizzle for invalid legal targets | Counterspell vs Pongify vs Comet Storm; Patron Wizard; Sigil Tracer | core |
| Events/conditions | `spell_cast`, `spell_copied`, `permanent_entered`, `combat_damage_player`, `creature_died`, `leaves_battlefield`, `begin_step`, `end_step`, with structured source and controller | Young Pyromancer (cast), Storm-Kiln Artist (cast **or copy**), Magnus (combat damage), Stormsplitter (cast) | core |
| Activated/triggered/static abilities | condition/predicate, cost/effect, trigger source, trigger multiplier, continuous modifiers and duration | Harmonic Prodigy duplicates qualifying Wizard/Shaman triggered abilities, not just handpicked named cards | core |
| Creature state/combat | base and current power/toughness, marked damage, blocker legality, tap, summoning sickness; flying/reach/haste; defender, vigilance, trample where needed | Magnus flying, Spawn attacks, preserving fragile engine creatures | core |
| Keywords/protection/removal | indestructible, hexproof/shroud, ward, deathtouch/lifelink as needed; **destroy != exile != bounce != sacrifice != 0 toughness** | Pongify destruction; Chaos Warp shuffle; Cyclonic Rift bounce; future protection | core/next |
| Counters/modifiers | `add_counter`, `remove_counter`, temporary +X/+Y, static ongoing +X/+Y, set P/T, ability grants, expiration schedule | +1/+1 counters, pump effects, ongoing type-changing modifiers | core/next |
| Basic effects | damage to player/creature, draw, scry/look, discard, search/tutor, copy spell, create token, create Treasure, bounce/destroy/exile, counter spell | Brainstorm/Preordain; Spellseeker; Twincast; Counterspell; Pongify | core/next |
| Duration and delayed abilities | `until_end_of_turn`, `next_end_step`, `while_source_on_battlefield`, delayed replacement/trigger; cancel by effect ID | Stormsplitter copy exile at next end step; temporary haste/buffs | core |
| Commander/multiplayer | commander choice to command zone; tax, commander damage by source commander; multi-opponent targets, simultaneous damage/elimination | Magnus recasts and combat damage; Comet Storm | next |
| Specialist mechanics | X/multikicker, buyback, escape, Class levels, copying modal spells, alternative casting from graveyard | Comet Storm, Searing Touch/Mystic Speculation/Capsize, Underworld Breach, Sorcerer Class, Mathemagics | next/special |

**Important:** not every entry must receive full Magic-level generality immediately. Implement the *smallest tested operation* sufficient for an actual card, then expose it as a reusable rule. Some distinctive cards can use a custom callback, but callbacks must only invoke public rules-kernel operations, never reach into a particular table subclass's private arrays.

### Existing v3 metadata: measurable reuse opportunities

The v3 catalog has **83 named definitions** (the 82 unique Magnus library names plus commander). Types: 29 generalized `spell`, 22 `creature`, 13 generalized `permanent`, 18 `land`, 1 `commander`. The old fields do **not** reliably distinguish instant from sorcery or artifact from enchantment; this must be corrected before effects.

Declarative v3 effect operations repeat in useful ways: 7 `selection`, 6 `create_token`, 2 `discount_spells`, 2 `utility`, plus `discount_per_token`, `double_wizard_shaman_triggers`, `treasure`, `draw`, `tutor`, `additional_spell_triggers`, `escape_nonland_spells`, `sacrifice_for_mana`, `all_creature_types`, `choose_type`, and other unique entries. The old `modeled` label is not v6 coverage. V6 reports **38 unsupported unique nonland library cards**. These counts are from the current checked-in catalogs and should be recomputed after metadata changes.

The most beneficial first reusable effects are `create_token`, `draw/selection`, `cost_modifier`, `counter_spell`, `destroy_or_bounce`, `add_mana`, `copy_spell`, and trigger multipliers; they cover most recurring situations, including interactions between real and synthetic players.

## Proposed data shape (illustrative, not executable yet)

```json
{
  "id": "magnus_the_red",
  "name": "Magnus the Red",
  "type_line": { "types": ["creature"], "supertypes": ["legendary"], "subtypes": ["Demon", "Primarch"] },
  "mana_cost": { "generic": 3, "U": 1, "R": 1 },
  "base_pt": [4, 5],
  "keywords": ["flying"],
  "abilities": [
    {
      "kind": "static", "op": "reduce_generic_cost",
      "filter": { "controller": "you", "cast_types_any": ["instant", "sorcery"] },
      "amount": { "count": { "controller": "you", "zone": "battlefield", "is_token": true, "is_creature": true } }
    },
    {
      "kind": "triggered", "event": "combat_damage_to_player",
      "source": "this_object", "effects": [ { "op": "create_token", "token_id": "magnus_spawn_3_3", "quantity": 1 } ]
    }
  ],
  "coverage": { "status": "planned", "validated_against_oracle": false }
}
```

Notes: `token` alone is insufficient: Magnus counts creature tokens, not necessarily every token permanent such as Treasure. Cost-reduction predicates must inspect the spell on the stack *before* determining its payable cost. A source's trigger listens to its unique game-object ID and controls only its own controller's events. Card text/rulings must be verified during implementation. Avoid treating the prototype JSON as an Oracle-data source.

## Concrete code-review findings / migration hazards

All file/line references apply to the 2026-10-28 v6 GitHub baseline.

1. **Table subclass duplicated rule paths.** `v6_real_deck/integrated.py` overrides `upkeep`, `main`, `cast`, `respond`, `block`, `combat`, `damage`, `kill_creature`, and `run` from v5. As more detailed decks arrive, these overrides would diverge. Put all game-state transitions in shared modules, and inject deck providers and pilots instead.
2. **Name tests replace capability checks.** `MagnusPilot`, `action_for`, and `named_triggers` branch on names or short sets. A creature's changed subtype or another player's copy will not reliably participate. Supply typed source IDs and ability predicates; schedule triggers for **all** seats.
3. **Type fidelity is lost.** `named_spec()` maps all old `permanent` cards to artifact; e.g. Underworld Breach, Sorcerer Class, Arcane Adaptation and The Lost and the Damned become artifacts. The old `spell` category also uses name heuristics for instant vs sorcery. Add a validated full type line for every card.
4. **Indestructible is not supported.** Calling generic `kill_creature()` removes a 5/5 tagged `indestructible` in a direct diagnostic. Make `destroy`, `exile`, `sacrifice`, `bounce`, and zero-toughness state-based movement distinct actions. A destination event should specify the reason and zone.
5. **Damage, counters, and buffs are conflated.** V5 changes `c.power` permanently when a buff resolves; no temporary duration or layered characteristic derivation exists. Store base stats, damage, counters, and effects separately, and calculate current characteristics. Avoid implementing the full Magic layer system unless a card actually needs a tricky interaction.
6. **Zone transfers are incomplete.** Creature death and counters currently remove cards from play/hand but do not consistently move actual named cards to graveyard. Discard-to-seven in v6 truncates hand without a discard event. This makes recursion, death triggers, and Underworld Breach inaccurate; address before implementing those cards.
7. **Flying/blocking is implemented by temporarily rewriting the defender's live creature list.** Replace with `get_legal_blockers(context, defender, attacker)` without mutating game state, then let a pilot select from that list.
8. **Current cast-response window is not a stack.** V6 cannot handle arbitrary counter-counter interactions and currently runs some triggers eagerly. Implement stack objects with typed targets and bounded priority passes; test legal resolution order before copy/buyback cards.
9. **Mana solver is shared only by the detailed seat.** V5 opponents use fungible `p.mana`; v6 has `_best()` dynamic programming with source-mode tuples, but recalculates each candidate and changes resources in the detailed `Player`. Put a `ManaPolicy` behind the same legal-action interface for every player. Synthetic opponents may continue to use an explicitly declared simplified payment policy for speed, *without changing how external spells interact with their lands/permanents*.
10. **Reporting is coupled to the Magnus seat.** `self.details=self.players[0]` and name-based triggers prevent two detailed decks from behaving naturally. Replace with per-seat deck providers, state and logging.
11. **Stormsplitter token expiration is currently a `kill_creature` event.** Expiration via exile should not be represented as death/destruction; use zone-changing/delayed-action primitives. The code currently removes expiring copies at each player's end step, which is roughly the right *timing* but not the right *zone semantics*.
12. **A named mana-source snapshot counts colored modes by string parsing** (`'U' in str(...)`). Compute legal colors from structured mode data instead; string formatting is not rules state.

These are implementation audit findings, not claims that the existing 77 tests failed. Current tests mostly check the supported happy paths and do not yet cover the distinctions listed above.

## Computational audit

**Method:** short local development-container benchmark, no external libraries. Twelve seeded **ten-round** games per implementation, with trace disabled: v5 mean ~3.6 ms/game, v6 mean ~5.2 ms/game. One payment-feasibility check for a hypothetical {4}{U}{U}{R}{R} eight-mana spell with a repeating mix of U/R/dual/ramp sources: 7 sources ~0.13 ms, 12 ~0.67 ms, 20 ~3.8 ms, 35 ~17.9 ms. Another all-Island diagnostic was faster, since it explored fewer mana options. These are tiny, nonrepresentative samples; neither confirms full v7 throughput nor predicts large combo workloads.

**What actually scales:** ~400 card objects across four 100-card decks is trivial; runtime depends on number of available choices, mana-source combinations, continuous-effect queries, triggered abilities per event, stack depth, and pilot search horizon. A late-stage 35-source player or a generated token swarm can be slower than a typical turn. Long control mirrors need a configurable turn cap and a recorded *unresolved/censored* outcome, not a forced winner.

**Simple optimizations first:**

- Keep card definitions immutable and intern by card ID; store only mutable `GameObject` instances in zones.
- Cache derived board characteristics, mana feasibility, legal target sets, and continuous modifiers **per game-state revision** (invalidate on a relevant move, tap, counter, effect, or turn transition).
- Index triggered abilities by event name instead of scanning all cards/creatures every event; evaluate actual source validity at resolution.
- Bound mana source modes with dominance pruning and reuse feasibility/payment plans for repeated identical costs. Never trade correctness for an optimistic colored-cost approximation without labeling it.
- Keep pilots as simple scoring policies initially; optional bounded planning (beam search) can come later with measured impact.
- Represent *provably repeatable deterministic loops* symbolically after a few verified cycles, with response windows; don't iterate millions of spell/token casts. If a loop is not proven to be legal and profitable, report `unmodeled_combo`, not a win.
- Profile 10/20/35 mana-source cases, 10/50/200 token cases, and triggered-ability dense turns; set performance budgets **after** those checks rather than guessing.

## Migration sequence (small, rollback-safe commits)

1. **v7a — Contracts and characterization tests (no behavior changes):** freeze v6 replay seeds; define card definition vs game-object identity, enum of types/subtypes/keywords, action/event payloads, zone-move reasons; add tests for current behaviors and the known missing cases as expected failures.
2. **v7b — Shared kernel:** extract legal-target filtering, zone moves, precise `destroy`/`exile`/`sacrifice`/`bounce` and state-based checks; make combat legality shared and non-mutating; add simultaneous damage and elimination tests. Keep all four abstract archetypes working.
3. **v7c — Cost/mana and ability registry:** shared cost computation with generic-only discounts, colored payment policy, source-tap plan cache; typed event triggers, static effects, counters/durations. Move Magnus/Pyromancer/Harmonic Prodigy into card data as proof of reuse.
4. **v7d — Bounded stack and decision seam:** legal action enumeration, instant-speed response windows, counter-counter, triggered stack objects, legal target recheck. No player knows its seat's name. Re-run matched v5/v6 narratives and note expected differences.
5. **v7e — Card coverage expansion:** implement reusable selection, destruction/bounce, copying, tutor, additional cost and recursion ops; add one or more exceptional handlers only as required by printed text. Do not adjust Magnus's actual deck while testing these features.

### Tests that must pass before calling a card "fully supported"

- **Magnus:** creature-token count changes discount only for instants/sorceries and only generic; not creatures/artifacts/activated abilities; still produces its combat-damage trigger if damage is dealt, even when the opponent subsequently removes Magnus.
- **Harmonic Prodigy:** double qualifying Wizard/Shaman triggers but not unrelated non-Wizard/Monk triggers; type-changing effects can change eligibility.
- **Protection:** indestructible survives `destroy` and lethal damage, but not sacrifice/exile or 0 toughness; hexproof blocks opponent targeting but not nontargeted sweepers.
- **Counters and modifiers:** two +1/+1 counters persist; +2/+2 until end of turn expires; the two are not interchangeable.
- **Typed stack:** creature spells are counterable by broad counters but not by spells limited to instants/sorceries; cast triggers happen even if countered; target validity is rechecked on resolution; copied spells are not "cast" unless an effect explicitly says so.
- **Zones:** discarded and countered real cards go to correct zones; token objects cease to exist after leaving battlefield; commander replacement/tax is correct.
- **Multiplayer:** direct damage, combat, and simultaneous area damage can eliminate one or several distinct opponents, while surviving players continue acting.
- **Swapability:** two real deck providers and two abstract providers work without special-case code or incorrect seat-specific triggers.
- **Instrumentation:** every nonland card has an explicit `supported` / `approximated` / `unsupported` status and any special-case handler is documented; no unresolved effect is silently treated as a generic playable spell.

## Immediate next decision

**Do not broaden named-card coverage first.** Implement v7a then v7b while retaining v5/v6 replay baselines. Test actual cards as *capability consumers*: Magnus, Young Pyromancer, Harmonic Prodigy, Storm-Kiln Artist, Pongify, and a counterspell. Once those use the shared system correctly, other spells should mostly be metadata and small declarative effect combinations.

Reference: [Wizards of the Coast rules](https://magic.wizards.com/en/rules) and [official keyword glossary](https://magic.wizards.com/en/keyword-glossary). This audit is based primarily on the checked-in code and metadata; exact future card text should be checked individually.
