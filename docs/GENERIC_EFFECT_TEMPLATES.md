# Composable effect templates: mana rocks, ramp and tutoring

**Status (October 31, 2026): implemented as bounded backend functionality.** Reusable mana source and search descriptors are in `commander_sim/effect_templates.py`; exact card review mappings are in `reviewed_rocks.py` and `reviewed_tutors.py`. This is an intermediate approximation architecture, not a second full Magic engine.

## The model

An effect is composed as **generic default + typed field overrides + pinned review + implementation capability**. Generic templates include `rock_colorless_one`, `rock_colorless_two`, `rock_commander_identity`, `rock_black_tapped`, `signet_ur`, and `tutor_to_hand`. The source card records its immutable Oracle ID and exact source Oracle text; admission fails if either changes. Simplified behavior requires a recorded assumption and the status is never labeled complete/full fidelity.

Typed mana modes describe output pips, activation generic/colored costs, tapping, life, damage and sacrifice as distinct fields. Search templates describe eligible printed card types, subtypes, colors, mana-value limits, destination, reveal and shuffle. Overrides can replace only fields belonging to that effect family; they cannot execute arbitrary Python or silently infer rules from Scryfall text.

## One default, several variants

```python
from commander_sim.effect_templates import ReviewedEffect, ManaMode, compose_effect

# Conceptual examples: not executable until pinned Oracle identity/text is
# reviewed and the host authorizes the cast or activated ability.
generic = ReviewedEffect("verified-oracle-id", "exact reviewed text",
    "tutor_to_hand",
    overrides=(( "search_types", frozenset({"instant", "sorcery"})),
               ("max_mana_value", 2), ("reveal", True)),
    assumptions=("Only reviewed printed card characteristics are considered",))
effect = compose_effect(generic)
```

Once reviewed and attached to an actual card, the **same generic tutor target predicate** can handle Fabricate (artifact), Solve the Equation (instant/sorcery), Merchant Scroll (blue instant), and Spellseeker (instant/sorcery, MV <= 2). The template for Mystical Tutor has a different `library_top` destination: the current search-to-hand executor correctly refuses to execute that destination.

## Actual mana rock integration

`commander_sim/template_resources.py` is a bounded six-color, physical source-ID payment bridge on the existing kernel. It can pay spells using approved basics, Command Tower and verified mana rocks. It models two colorless mana from Sol Ring, floating unused mana within the current main phase, basic source tapping, commander-identity choices for Arcane Signet/Commander's Sphere, entry-tapped Charcoal Diamond, and the one-generic funding requirement before Izzet Signet produces U/R. Mind Stone provides its reviewed colorless tap ability. Talisman of Creativity's damage-paying colored modes are described but **not activated** until life/damage accounting is integrated; only its safe colorless mode is available to the bounded pilot. Unknown rocks yield no mana.

The existing `cast_reviewed_permanent` action handles approved creatures and mana-rock artifacts via the same hand -> stack -> battlefield kernel transitions. No duplicate battlefield inventory or new rules engine is maintained. The prototype is intentionally not plugged into the historical v35 multiplayer turn driver.

```sh
python -m commander_sim.early_game_runner --deck wretched_ranks --seed 7 --turns 6
python -m commander_sim.bounded_batch --deck magnus_premium --seeds 20 --turns 6
```

The batch now separates **lands**, **approved rocks in play**, **creatures in play**, and observed hand/cast statistics. A land plus an unfunded Signet is not equivalent to two unconditional mana: the actual source planner handles funding and colors. These are bounded real-action diagnostics, not real deck win probabilities.

## Tutor execution boundary

`commander_sim/template_search.py` can validate printed restrictions and, at resolution of an explicitly reviewed and pending **cast** tutor spell, move the selected physical library object to hand and shuffle the same authoritative library index. It does not pay for or cast that spell; the parent game driver must do so first. Search target preview is available for a reviewed Spellseeker battlefield source, but no ETB trigger or activation is automatically created by this module. Library-top tutors, tutors with extra random discard costs, and arbitrary search/destination/trigger timing remain unimplemented.

**Important:** The new generic tutor executor is a callable backend capability, **not yet invoked by the bounded six-turn pilot**. Tutor cards do not therefore improve the pilot's key-card access or milestone statistics yet. It should be connected only after the driver can cast reviewed search spells and resolve them at appropriate windows. Neither printed card metadata nor a strategy profile grants an executable tutor.

## Next extensions

Use the same descriptors to support land-search ramp (`basic land` -> battlefield tapped), mana-rock alternative modes, cost reducers, conditional/power-limited tutors, and optional/discard/sacrifice side costs. Review the *differences from the default* rather than writing each card from scratch. Prioritize actually hooking mana rocks and generic search to a normal source-paid turn driver; add event-backed tutor reachability, ability fidelity and calibrated opponent interactions before win-rate estimates. UI Work can consume the Python outputs but should not reimplement their mechanics in JavaScript.
