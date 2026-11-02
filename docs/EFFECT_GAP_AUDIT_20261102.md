# Cross-deck source-reviewed effect-gap audit

Snapshot: November 2, 2026. Generated from eight pinned physical/canonical deck
variants by \`python tools/audit_effect_gaps.py --output /tmp/effect-gaps.json\`.
The [effect gap audit workflow](../.github/workflows/effect-gap-audit.yml)
publishes the complete JSON with card names and recurring variant overlaps.

## What these categories mean

- **Reviewed partial**: a pinned exact card identity has at least one named
  reviewed suboperation. This does **not** mean that its full rules text,
  legal timing, alternative costs, triggered effects or interactions run.
- **Provisional only**: conservative import can recognize a subset such as
  an ordinary body or simple physical library/mana action, without a named
  reviewed registration. Complex printed text is not automatically executed.
- **No registered recipe**: neither kind of registration applies in this
  inventory. Generic kernel abilities may still work, so this is not a count
  of completely unplayable cards.
- **Candidate family**: a printed Oracle-text pattern suggests an operation
  to inspect. It never grants execution or establishes that a card is fully
  unsupported. Multiple families may match a single card.

| Pinned deck variant | Reviewed partial | Provisional only | No registered recipe |
| --- | ---: | ---: | ---: |
| Necron Dynasties | 22 | 26 | 23 |
| Wretched Ranks | 34 | 13 | 21 |
| Magnus Premium | 35 | 9 | 38 |
| Magnus Budget | 34 | 9 | 39 |
| Magnus physical trial | 21 | 12 | 42 |
| Mortarion current | 54 | 10 | 5 |
| Mortarion ideal | 38 | 19 | 19 |
| Mortarion physical final | 56 | 8 | 5 |

A source-registry expansion in this pass now includes land, draw, removal,
attachment, zone/graveyard, reactive and activated handlers that were omitted
from the previous named-effect count. These categories are not card-fidelity
scores or mutually comparable win-rate factors.

## Candidate unregistered-operation signals across eight variants

Card-selection/draw/mill: 41 variant occurrences; continuous modifiers: 37;
entry triggers: 31; removal: 27; sacrifice/death: 20; token creation: 19;
graveyard/recursion: 16; alternative costs: 13; spell copy: 6; combat: 5.
These counts overlap and are **not** numbers of distinct unimplemented cards.

## Newly composed, shared-effect examples

- **Necrons:** Canoptek Scarab Swarm's *Feeder Mandibles* uses a parameterized
  whole-graveyard exile, counted type union \`{artifact,land}\`, and dynamically
  sized physical 1/1 colorless flying artifact-Insect token batch. The same
  exile primitive is reused by Bojuka Bog. Both have separately verified
  source/entry permission, and every resulting physical ID is traceable.
- **Gisa:** Go for the Throat is a source-verified destruction registration
  over the existing removal service with a reusable
  \`nonartifact_creature\` target predicate, not a bespoke card script.
- **Magnus:** Meeting of Minds' normal mana-cost draw-two is legal without
  convoke and uses the physical library resolver. Deduce composes source-paid
  draw and a physical Clue-token batch; Clue's activated draw remains omitted.

## Candidate next operations (rules work, not pilot scripts)

1. **Graveyard alternatives and re-entry:** Tomb Fortress,
   Witch's Cottage, Living Death and Out of the Tombs need richer
   cost/tap/exile and multi-object movement permissions. Reuse the same
   typed graveyard search, transfer and ETB queue where possible.
2. **Conditional card draw, mana and triggered engines:** Of One Mind
   requires its *mandatory* conditional cost reduction when both creature
   kinds are controlled; do not simply pay its printed full cost when the
   reduction applies. Extend source-backed cost formulas with explicit,
   observed battlefield predicates. Meeting of Minds' optional convoke
   payment can use the same mana-payment API with legal tapped-creature
   contributions.
3. **Generalized response windows:** Rewind and Spell Snare cannot be
   safely represented as ordinary main-phase hand casts. This requires
   legitimate opposing stack objects, player windows and counterspell
   resolution rather than name-specific shortcuts.
4. **Multi-seat and continuous effects:** Canoptek graveyard counting now
   works, but combined commander damage, replacement effects, broad
   continuous layers, APNAP and complete opponent card-by-card policies
   still require independent verification.

## Regression gates

The normal \`python run_all_tests.py\` suite validates individual reviewed
mechanics. The eight-deck 12-round seeded narrative audit collects observed
physical actions, hand omissions and decisions and the 20-round outcome
preview remains explicitly modeled against abstract opponents. Green CI
proves only these tested bounds. It does not validate competitive win rates
or every printed card ability.
