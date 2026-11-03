# Shared effect catalog

All imported Commander decks use **one shared rules kernel**, with reviewed
card abilities composed from reusable effects. There is no deck-owned effects
engine and no separate mutable state for individual deck variants.

## Locations

| Responsibility | Module |
|---|---|
| Discover shared operation names and their family | `commander_sim/shared_effect_registry.py` |
| Per-card Oracle ID / source-text review and typed parameters | `commander_sim/reviewed_*.py` and other reviewed source modules |
| Immutable card-ability slots and strict/hybrid/observation policy | `commander_sim/ability_composition.py` |
| Authoritative physical zones, counters, hand, mana, life | `IndexedKernel`, `LiveZones`, and existing `commander_sim` physical services |
| Cross-deck registration and limitations report | `python -m commander_sim.named_effect_coverage --summary` |
| Source-text mechanic candidates (not executable) | `python -m commander_sim.deck_effect_audit` |

The catalog is a **read-only index** of reviewed suboperations, not a new
effect interpreter or an automated permission system. Its operation-family
groups are organizational: actual actions remain in the common physical
handlers, including mana payment, draw/mill, tokens, counters, sacrifice,
graveyard transfers, triggers, combat and zone moves.

## Adding another card or importing a deck

1. Load a pinned, validated Oracle snapshot. Treat text-only discoveries as
   *candidates*, not implemented abilities.
2. Find an existing operation in `operation_index()` (and its shared family).
   If it applies, register the card's **own** pinned Oracle ID and source
   excerpt with parameters in the existing reviewed effect module.
3. If none applies, implement a generic operation against existing kernel
   primitives; do not add card-name conditionals to the central pilot or
   create a parallel game state. Add the new operation registry to
   `registered_sources()` and classify it in exactly one `EFFECT_FAMILIES`
   entry.
4. Preserve separately reviewed slots on multi-ability cards. Report
   exact/simplified/unsupported at ability level and do not promote entire
   cards to complete support from a single registry hit.
5. Add source-pin regression tests, zone/life conservation tests, and
   tests showing at least one other deck or card can use the same operation.
   Run the full versioned Python suites and bounded audit workflows.

## Discovery versus execution

`named_effect_coverage()` lists each registered suboperation by pinned ID,
then summarizes the number of deck variants sharing each effect family. A
registry hit means a *reviewed suboperation exists*, not that its full
printed card, timing, or priority rules are implemented. There is no
text-to-code execution, card-name-only admission, or runtime API fetch.

Current limits remain explicit: incomplete APNAP ordering, player priority,
replacement effects, and card-specific interactions stay unsupported until
they have independently reviewed source-backed handlers.
