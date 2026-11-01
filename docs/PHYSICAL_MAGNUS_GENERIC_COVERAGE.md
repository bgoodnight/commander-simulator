# Physical Magnus v1.1 — reusable card coverage

## Scope and provenance

- The original owned starter and sideboard are **unchanged**.
- `decklists/magnus_physical_legal_trial_v1_1.txt` is an explicitly labeled simulation-only legality variant: the off-color `Narset's Rebuke` slot is replaced with one Island. Never imply the user made that swap in the physical deck.
- `simulator/card_data/magnus_physical_trial_m1_scryfall.json` and its manifest pin full Oracle-ID card records. The shared catalog was extended by **explicit cache-first import** in CI. Games, observations, and tests never call Scryfall.
- `EXPERIMENTAL_FIXTURES` is opt-in and separate from the six canonical public Deck Lab decks. The existing static publication and regression fixture count are preserved.

## Shared reusable behavior, not a new engine

The existing `run_bounded_early_game` and its `IndexedKernel`/`LiveZones` physical objects execute ordinary draw, reviewed land plays and tapped entry, generic fixed-cost mana payments and floating, reviewed artifact/creature casts, typed token spells, reviewed draw spells, and hand cleanup.

**Added reviewed data-only registrations:**
- Seven nonbasic lands: Great Hall of the Biblioplex, Hidden Grotto, Path of Ancestry, Shivan Reef, Stormcarved Coast, Swiftwater Cliffs, Tyrite Sanctum. Exact Oracle ID + full text guard every registration. Template settings include mana colors and normal/always tapped/two-other-land entry conditions.
- Two mana rocks via existing typed mana templates: Worn Powerstone (two colorless; enters tapped) and Chromatic Lantern (own any commander-identity color; other lands gaining any-color production unsupported).
- Four safe ordinary creature bodies using the existing source-paid generic creature cast: Elementalist Adept, Firebrand Archer, Reckless Scholar, Thermo-Alchemist. Activated and triggered abilities remain independently unsupported.
- Four reusable draw spells via `ReviewedCreatureCast` + `draw_physical_cards`: Quick Study (draw 2, reviewed); Think Twice (draw 1, flashback omitted); Ponder (draw 1, look/reorder/shuffle omitted); Preordain (draw 1, scry omitted). Their full identities and Oracle text are pinned.

**Non-executing universal fallback:** Every unknown normal-layout card with a fixed mana cost can appear as a `source_paid_candidate` after payment planning. It is explicitly a **preview** with no cast, mana spent, stack object, resolved effect or zone movement. Unsupported cards still participate as physical objects in draws, legal type queries, hand cleanup and zone conservation.

## Safe omissions

- Shivan Reef currently grants only colorless mana; the painful colored mana modes require separately reviewed damage costs.
- Hidden Grotto's mandatory surveil and Swiftwater Cliffs' life gain are omitted and disclosed.
- Other required effects, combat, opponents, targeting/replacement effects, commander casting, combos, win rate and calibration remain out of scope. The limited no-opponent pilot should not be used for bracket-performance inference.
- Other unregistered spells (including complex Brainstorm and additional-cost Seize the Spoils) are not cast just because they are recognized in the catalog.

## Run

```bash
python tools/run_physical_magnus_trials.py --seeds 100 --turns 6 --output physical-magnus-trials.json
python -m unittest discover -s tests -p test_physical_magnus.py -v
python run_all_tests.py
```

The trial report records deck hash, typed action counts, source-paid candidates, unsupported-card mentions, and five example turn traces. Full regression tests must pass before this work is merged.
