# Shared-effect coverage across six pinned Commander deck fixtures

**Status:** Execution work in progress. This is a fidelity/coverage ledger, not
a blanket promise of 299 full-card implementations. Update alongside
`ROADMAP.md` and the 37-suite regression runner.

## Inventory and methodology

Run:

```bash
python -m commander_sim.deck_effect_audit
python -m commander_sim.deck_effect_audit --details
python run_all_tests.py
```

The offline audit reads exact pinned Scryfall snapshots for:

| Deck fixture | Distinct names in pinned list | Common mechanics to prioritize |
|---|---:|---|
| Magnus premium | 82 | mana, instants/sorceries, token engines, tutors, copies |
| Magnus budget | 82 | mana, instants/sorceries, token engines, tutors, copies |
| Wretched Ranks | 68 | Zombies, tokens, sacrifice, death and graveyard |
| Mortarion current | 69 | sacrifice, damage, death payoffs, token engines |
| Mortarion ideal | 76 | counters, graveyard, damage, recursion |
| Necron Dynasties | 71 | artifact/graveyard recursion, mill, tokens, sacrifice |
| **Across lists** | **448 list entries / 299 distinct names** | Repeated operations, not repeated hardcoded effects |

The audit treats matches such as `graveyard` and `create ... token` as
**candidate categories only**. It does not interpret Oracle text as executable
Python, assign a whole-card fidelity score from a regex, or assume that a
simulated object has all its printed side abilities.

## Verified reusable operation families

| Operation family | Shared source code | Scope that is actually executable |
|---|---|---|
| Land and mana-rock payment | `effect_templates.py`, `template_resources.py`, `legacy_mana_adapter.py` | Actual tapped source IDs and floating U/R/B/etc. mana for admitted basic lands and reviewed rocks; side costs on unreviewed modes fail closed |
| Library search and tutor cast | `reviewed_tutors.py`, `template_search.py`, `reviewed_tutor_cast.py` | Pinned instant/sorcery tutors with paid hand→stack→graveyard; searched physical card to hand or shuffled library top |
| Fixed token batches | `legacy_common_ops.py`, `reviewed_token_spells.py` | Ral's Reinforcements, Hard Evidence, Strike It Rich, Moan of the Unhallowed and Army of the Damned hand-cast batches; count, colors, P/T, artifact subtype and tapped entry are reviewed |
| Triggered draw and tokens | `ability_composition.py`, `live_trigger_bridge.py` | Baral, Archmage Emeritus, Young Pyromancer, Storm-Kiln Artist in the historical live stack; doubled triggers and source departure remain kernel-owned |
| Draw/mill/counters | `physical_common_effects.py` | Physical library→hand/graveyard movement and real battlefield counters under a reviewed host callback; **not yet attached automatically to all printed effects** |
| Sacrifice and graveyard retrieval | `legacy_common_ops.py`, `physical_common_effects.py` | Physical sacrifice restrictions and owned, type-restricted graveyard→hand moves; paid source, permission and targets must be checked by host |
| Removal and bouncing | `physical_common_effects.py`, `legacy_common_ops.py` | Type/controller/target-checked targeted destruction, exile, bounce through existing kernel; unsupported replacement layers fail closed |
| Spell copying | `legacy_spell_copy.py` | Reviewed Reiterate virtual stack copies and restricted retargeting in v33/v35 only |
| Each-opponent damage | `legacy_common_ops.py` | Host-owned simultaneous damage, used by Mage Siege's wizard trigger; **not direct life loss** |
| Static cost reductions | `legacy_common_ops.py` plus v7 `rules.modified_cost` | Existing source-paid historical effects including generic cost floors and descriptor-driven reducers, not arbitrary continuous-effect layering |

All new state changes use the existing physical kernel / LiveZones / game
table. Unit tests verify the primitives, but those unit tests **do not prove
that every deck card invoking the mechanic is legally cast or fully resolves**.

## Confirmed limited turn-driver coverage

`run_bounded_early_game` now accepts all **six** pinned decks. It executes
reviewed land and mana-rock actions using a common physical resource planner.
The Magnus lists can additionally cast reviewed hand-based tutors and reviewed
fixed-token sorceries. Wretched Ranks can cast its approved subset of ordinary
creatures and fixed Zombie-token sorceries. Other deck creatures are not
authorized merely by their printed card type.

Tokens from the reviewed sorceries are physical battlefield token objects.
They do not replace any of the original 100 non-token cards. Unreviewed
Clue/Treasure activations, flashback, opposing priorities, other replacement
rules and nonlinear token synergies remain explicitly unavailable.

## Still incomplete — required for full-deck claims

1. **Unified event subscriptions across all six deck implementations.**
   Historical v35 still runs the detailed Magnus-specific engine; the bounded
   multi-deck runner is not a four-player priority/stack engine.
2. **Death and sacrifice triggers for Gisa/Mortarion/Necrons**, including
   simultaneous deaths, source last-known information, type-sensitive
   predicates, once-per-turn caps, sacrifices as additional costs and
   appropriate opponent life gain/loss.
3. **Graveyard casting and recursion permissions:** flashback, unearth,
   resurrection to battlefield, re-entry triggers, exile replacement,
   commander movement and graveyard-dependent dynamic costs.
4. **Full permanent effects and continuous layers:** counters with replacement,
   equipment/enchantments, triggered token doubling, tap and sacrifice
   activations, copy/characteristic layers and arbitrary mana abilities.
5. **Full opponent combat and legal priority for all decks.**
   Until this exists, apparent deck-engine consistency is not a validated
   multiplayer win rate or tier ranking.

The next effective step is attaching the already-tested generic effects to
reviewed ability slots and the single live event driver, **not** declaring
cards supported simply because their text shares a keyword.

## Regression acceptance

`run_all_tests.py` invokes all 37 suites, plus package-level tests for
reviewed mana, tutors, token batches, source movement, no invented effects,
physical inventory conservation, deterministic early-turn traces, ability
promotion and historical replay fingerprints. A passing suite certifies the
specific tested subset, not comprehensive Commander rules fidelity.
