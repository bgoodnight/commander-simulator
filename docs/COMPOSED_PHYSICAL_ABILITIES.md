# Composed physical abilities (rules-only milestone)

`commander_sim/composed_abilities.py` extends the existing reviewed ability
architecture. It does **not** add a second battlefield, mana pool, stack,
library, card ownership model, or opponent AI.

## Reusable parts

Each card profile is assembled from:

- **Event:** `activate` or `end_step`.
- **Predicate:** `always`, `no_creatures`, `life_lost_this_turn`.
- **Payment:** fixed source-paid mana or a choice of generic X.
- **Effect steps:** `create_tokens`, `damage_all`, `sacrifice_source`.
- **Token parameters:** the existing `TokenBlueprint` (types, colors,
  keywords, power/toughness, count and tapped entry).

The executor routes reviewed profiles through the *existing*
`AbilitySlot` → `ComposedCard` → `AbilityDispatcher` contract.
The source Oracle UUID and complete quoted ability excerpt must match the
physical card's pinned metadata before any rule can execute. The shared
services perform payments, token creation, physical damage, state-based actions,
and last-known-information death triggers. No card-to-card references exist
in the composition executor.

## Implemented profiles

- **Mortarion, Daemon Primarch:** beginning-of-your-end-step optional X
  generic payment; X is bounded by the *total life lost during that turn*
  (life gains do not erase losses); creates X 2/2 black Astartes Warrior
  tokens with menace.
- **Pestilence:** repeatedly pay B for 1 simultaneous damage to each creature
  and unprevented damage to each player; sacrifice at beginning of end step
  when no creatures were on the battlefield as that step began.
- **Pestilence Demon / Thrashing Wumpus:** reuse the *same damage operation*
  and B payment, with different reviewed card profiles.

The resulting deaths use the existing `ReviewedDeathEngine`, which handles
reviewed **Pitiless Plunderer** Treasure triggers. The existing reviewed
sacrifice activation handles **Ashnod's Altar**, adding actual floating
colorless mana. No new Plunderer or Altar handler was introduced.

## Engine versus pilot boundary

`ComposedAbilityEngine.activate(source_id, turn=...)` is a *legal action*
executed when a caller chooses to activate it; it does not automatically
spend every spare B. `end_step(active_seat=..., turn=...,
life_start_index=..., x_choices={source_id: X})` requires the host to capture
the `KernelLife.life_changes` index at the beginning of the active turn.
Zero or absent X declines the optional payment. All beginning-of-end-step
conditions are snapshotted before effects resolve.

Current tests construct real physical objects with the existing live kernel,
exercise mana and life payments, simultaneous damage/SBA, Treasure death
triggers and Mortarion token output, then sacrifice a created Astartes using
Ashnod's Altar and verify the resulting Treasures and floating mana.

The **bounded early-game pilot does not yet choose activations or Mortarion X
values**. These profiles are callable engine capabilities, not assertions
of a fully autonomous Mortarion simulation. Existing published 100-seed
simulations should not be reinterpreted as including these new interactions.

## Explicit remaining limitations

- No opponent priority, APNAP triggered-stack ordering, damage prevention/
  replacement, protection, multiplayer combat or elimination.
- Damage is labeled as damage in `KernelLife` but uses a bounded unprevented
  life change for players. This is *not* a full damage rules implementation.
- No arbitrary Oracle ability parsing. New card profiles require a pinned
  source review and matching typed parameters. New mechanics require one new
  shared effect primitive and unit tests.
- No automatic commander casting from the command zone, no policy for choice
  of X or repeated Pestilence activations, no full opponent-turn driver.

## Adding new cards

1. Confirm Oracle ID and exact ability excerpt from the pinned snapshot.
2. Compose an `Ability` from existing `Predicate`, `Payment`, and `Step`
   descriptors; add new descriptors only for genuinely new mechanics.
3. Ensure the existing physical services can resolve all effects without
   fabricating a zone, player, source, token, or permission.
4. Add both a positive physical-kernel test and a fail-closed identity test.
5. Run `python -m unittest tests.test_composed_abilities -v` and
   `python run_all_tests.py`.

This preserves the project's code-reuse policy: a card is configuration
unless its mechanics add a truly reusable primitive.
