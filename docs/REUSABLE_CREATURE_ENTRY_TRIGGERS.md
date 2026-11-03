# Reusable creature-entry trigger operations — November 3, 2026

This branch builds on the draft **continuous P/T effects** architecture
(PR #78) and extends the existing source-pinned reviewed ability inventory.
It is not a new Commander-specific pilot or hardcoded effect engine.

## Typed trigger anatomy

`CreatureEntryRule` describes the **event predicate** and the **shared physical
operation** separately:

- `trigger_subtype` / `trigger_color`: only verified subtype/color objects
  match; unknown card colors do not silently qualify
- `another`: excludes the source itself when printed
- `source_controller_only`: restricts the incoming creature to one controller
  or allows an opponent's entering creature
- `operation`: `counter_self`, `opponent_drain`, `temporary_debuff`
- `exclude_subtype`, `amount`: generic effect selection and magnitude

This is a validated **subset** of printed trigger effects. Registration
requires exact Oracle ID and Oracle text from a pinned deck snapshot.

## Shared physical dispatch

`ReviewedCreatureEntryEngine` reads one authoritative `LiveZones.operations`
stream. The zone adapter now also records direct battlefield/token creation
in that same stream; without this change, creature-token entries were
invisible to an event consumer. No shadow library, battlefield, or player
model is created.

Each entry is consumed at most once. The dispatch checks actual controller,
current physical creature subtypes and colors, and source object identity,
then calls the **already existing** primitive:

- `put_reviewed_counters`: source-owned +1/+1 physical counters
- `KernelLife.each_opponent_loses` / `gain`: one legitimate opponent loss
  per active seat, a separate one-point gain
- `change_reviewed_creature_stats`: temporary -1/-1, kernel state-based
  deaths and existing death-trigger engine

All of these can be reused for other cards through typed rules and the
verified printed-text registry, without new resolution branches.

## Source-reviewed cards

1. **Champion of the Perished**: +1/+1 counter when another Zombie under
   that Champion's controller enters; token entries work.
2. **Ayara, First of Locthwain**: own entry or another black creature under
   its controller causes each **active** opponent to lose 1 and its
   controller to gain 1. Ayara's separate sacrifice/draw activation remains
   governed by its existing review.
3. **Noxious Ghoul**: its own or **any** Zombie entering (including opponents')
   triggers -1/-1 until end of turn for every non-Zombie creature. The
   reduction is not damage or destruction; indestructible does not prevent
   death at zero or negative toughness.

## Current fidelity limitations

- **Timing**: This is a bounded **no-priority** event bridge. The game host
  drains completed physical zone operations at designated phase/action
  boundaries. It is not a replacement for an APNAP stack with responsive
  interactions, ordering of simultaneous triggers, or detailed last-known
  information when an entrant or source leaves before consumption.
- Counter and temporary-stat effects use source-backed game objects and
  existing state-based checks. They do not implement full replacement,
  protection, regeneration or dependency-layer logic.
- This is not full-card fidelity for any printed source and does not
  establish actual head-to-head precon games. The three other opponent
  seats in the pilot smoke run remain **abstract**.
- Static effects (PR #78) are a prerequisite for this branch; merge/rebase
  them as a single deliberate integration rather than blindly replacing
  the current production rules file.

## Validation

`python -m unittest tests.test_reviewed_creature_entry
tests.test_static_creature_effects tests.test_reviewed_enter_effects
tests.test_named_effect_coverage tests.test_kernel_life -v`

The CI suite checks own/enemy triggers, direct physical Zombie tokens,
multiple independent copies of a trigger source, source departure, false
Oracle identities, eliminated opponents, global non-Zombie debuffs,
zero-toughness indestructible deaths, temporary stat cleanup, and both
existing physical precon simulations on matched seeds.

Next: unify the entry bridge with the full four-seat timed event pipeline,
then add more parameterized ETB recipes (counter scaling, creature type
selection and token generation) and verify with per-turn narratives.
