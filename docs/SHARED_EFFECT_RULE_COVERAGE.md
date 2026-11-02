# Shared-effect expansion: death, graveyard, mill and paid recursion

Status: **incremental source-reviewed and provisional-suboperation coverage**, not
complete Oracle rules coverage or an accurate multiplayer win-rate engine.

## Reusable rule containers

| Container | Declarative parameters | Current sources / use cases |
|---|---|---|
| `death_recipes.py` | Controller relation, source exclusion, creature type/subtype, token restrictions, ordered steps and quantities | Existing reviewed death triggers + Midnight Reaper; small exact printed death clauses on new imported bodies in safe mode |
| `graveyard_recipes.py` | Graveyard owner, destination, type/subtype/supertype gates, new battlefield controller, tapped entry, counters, finite batch selection | Reassembling Skeleton, Persistent Specimen, Phyrexian Reclamation, Mortuary Mire, Oversold Cemetery, Lord of the Undead, Memorial to Folly, Lychguard, Nurgle's Conscription, Undying Malice |
| `library_actions.py` | Ordered draw/mill/scry/surveil/reorder/shuffle/discard/put-back, chosen physical IDs | Existing draw/filter cards; Flayed One, Undead Butler, Mire Triton milling; exact standalone mill spells and safe creature ETB-mill imports |
| `reviewed_utility_activations.py` | Source zone, mana/life/tap/sacrifice costs, printed target restrictions, condition, destination recipe | War Room, Mind Stone, Barren Moor and the graveyard sources above |

For example, a newly imported ordinary creature with exactly:

```text
Flying
When this creature enters, mill three cards.
```

can gain a basic physical body and source-paid cast and then mill three real
cards when `provisional_mode="safe"` is selected. The parser does not
accept additional mandatory ETBs, modal costs, delayed replacement effects,
or multi-clause transformations by approximating them away.

A source-reviewed card may use an effect container with stronger permissions.
For instance, `Mire Triton` is registered with
`mill(2) → gain_life(2)`; `Lychguard` has an explicit
`{3}{B} + sacrifice_self → return all eligible legendary creatures`
activation. Its effect's target is *not* guessed, and the paid mana must be
sourced from actual available cards.

### Safety and replay boundaries

- **One physical game state:** New effects use the existing zone kernel and
  source-backed mana service, never a second shadow deck or hand.
- **No accidental full-card claim:** A reviewed ETB or activation does not
  establish static bonuses, combat/attach rules or other printed abilities.
- **Fail-closed import:** Complex Oracle clauses and multi-face cards require
  explicit review. Opt-in `safe` mode reports a provisional fidelity level.
- **Death LKI and timing:** Observed death triggers use the existing pre-move
  battlefield snapshot. Full priority, simultaneous triggers ordering, APNAP,
  commander zone replacements, and player elimination remain limited.
- **Provenance:** Every visible activated/spell effect has a source card ID,
  source payment and physical zone transitions. Derived metrics should not
  be represented as exact win rates from the bounded pilot.

## Remaining effects in actual decks: prioritized review queue

These are **existing printed cards or effect families**, not invented cards or
claims that all subeffects are unimplemented. Prefer composing typed rules and
adjusting arguments over adding source-specific handlers.

| Priority | Cross-deck impact / examples | Reusable extension still needed |
|---|---|---|
| 1 | Necron artifact recursion: Technomancer, Beacon of Unrest, Dread Return, Their Number Is Legion; Wretched Ranks Victimize and Cemetery Recruitment | Multi-step mill → graveyard filter → reanimate/retrieve with aggregate mana-value caps, source-paid spell resolution, correct exile/shuffle |
| 2 | Shared death/sacrifice engines: Skullclamp, Nurgle's Rot, Undead Butler, Resurrection Orb, Necroskitter, Midnight Reaper and related triggers | Attachment-aware deaths, delayed return triggers, target legality and simultaneous event ordering. Existing parts are partially reviewed; do not double-trigger |
| 3 | Reusable paid utility: Hedron Archive, Commander's Sphere, Infernal Idol, Cemetery Reaper, Lychguard, Cryptbreaker, Graveborn Muse | Extend existing utility cost container with variable draw, sacrifice/discard costs, subtype/zone targets and optional/conditional selectors |
| 4 | Combat-triggered mill/recursion: Szarekh, Anrakyr, Necron Monolith, Canoptek Wraith, Grave Titan | Actual attack/defender/vehicle state and legal opponent choices, not just mock combat damage |
| 5 | Replacement and layer effects: Kalitas, Trazyn, Mikaeus, Shard of the Void Dragon, The War in Heaven, Out of the Tombs | Shared replacement/continuous-effect layers and priority-aware event processing, not a loose text regex |
| 6 | Spell-combo fidelity and copies: Underworld Breach, Magnus cost reducers, copied spells, flashback, buyback, cascade, conditional tutors | Central stack/priority and alternative-cost permissions reused by every deck; test finite loop bounds and actual resource conservation |

## Acceptance bar before declaring a card fully supported

Each registered source needs: verified pinned Oracle identity; all mandatory
on-cast/ETB effects handled; full timing/target legality; real payment;
complete zone events; replacement/trigger interaction tests; and representative
narrative games. Until then, label registered operations and known omissions
separately. This is why the current rule coverage is more useful than claiming
that every card with a recognized mechanic works perfectly.

Useful checks:

```bash
python -m commander_sim.named_effect_coverage --summary
python -m commander_sim.deck_effect_audit
python tools/audit_library_recipes.py --all
python -m unittest tests.test_shared_event_recipes tests.test_shared_mill_recipes tests.test_shared_recursion_activations -v
python run_all_tests.py
```
