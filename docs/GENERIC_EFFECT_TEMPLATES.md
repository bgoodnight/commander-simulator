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

## Migrating the older v17–v35 card implementations (first completed slice)

The historical simulator formerly repeated library-search logic across separate
card-specific table classes. The first migration replaces those routines
with **one** `commander_sim/legacy_tutor_ops.py` resolver driven by the existing
`EffectTemplate` data structure. Its declarative registrations cover Mystical
Tutor (instant/sorcery -> library top), Personal Tutor (sorcery -> library top),
Merchant Scroll (blue instant -> hand), Solve the Equation (instant/sorcery ->
hand), Fabricate (artifact -> hand), Step Through wizardcycling (Wizard subtype
-> hand) and Spellseeker (instant/sorcery with MV <= 2 -> hand).

Five of these tutor profiles now use the **same reviewed `TUTORS` registrations** as the new backend (Mystical Tutor, Merchant Scroll, Solve the Equation, Fabricate and Spellseeker): they do not maintain duplicate type, color, mana-value or destination configuration. Personal Tutor and wizardcycling retain historical-only declarations pending separate Oracle-verified promotion.

The v17, v25, v26, v27, v28 and premium v31 table handlers now call this
single implementation. They still own spell casting, timing, priority and
Spellseeker/cycling triggers; the new resolver owns **only** eligibility,
ranked/policy selection, fail-to-find, exact physical card moves, shuffle,
library-top ordering and logging. Unknown required target colors or mana
values fail closed. Older verified cards are covered by fixed historical
declarations; this layer does **not** automatically parse or authorize an
arbitrary new tutor from card text. New cards can reuse a template by
registering reviewed fields instead of adding another search algorithm.

The original historical v9c+ mana provider also routes its **five previously
supported rock definitions** (Sol Ring, Izzet Signet, Talisman of Creativity,
Mind Stone, Arcane Signet) through `commander_sim/legacy_mana_adapter.py`,
which converts the same pinned reviewed `ManaMode` declarations into the
old U/R/colorless `Ability/Cost` API. It does **not** replace the old mana
planner or grant newly unreviewed cards mana. Colored ability order is
canonical WUBRG to preserve deterministic replay behavior.

Regression gates include eight new search tests and seven new rock adapter
tests, plus all prior versioned gameplay suites and the historical frozen
reference fingerprints. The migration is complete only when the **whole**
regression matrix passes; existing engine behavior is not supposed to change.

**Remaining migrations:** generic draw/discard, counters, token creation,
sacrifice, recursion, cost reductions, copy/target changes and conditional
triggers. Prefer adding one typed reusable operation or an explicit parameter
when a card exposes a new mechanic; maintain a custom handler only for
genuinely irreducible behavior. Add original-versus-migrated replay fixtures
before changing any of these older implementations.

## M2.8: Common effect operations migrated from historical cards

`commander_sim/legacy_common_ops.py` now holds **typed, card-independent
effect parameters** and shared execution calls over the already-authoritative
table services:

| Operation | Parameters | Existing implementation sites migrated |
|---|---|---|
| `DrawDiscard` / `apply_draw_discard` | `draw`, `discard`, `discard_kind` | Consider draw, Preordain, Brainstorm draw, Frantic Search draw+discard, Baral optional loot, Fiery Islet draw |
| `TokenBatch` / `apply_token_batch` | count, P/T, token name, verified definition | Ral's Reinforcements (two 1/1 U/R Elementals) |
| `GenericDiscount` / `apply_generic_discount` | reduction amount, printed color filter, source name | Sapphire Medallion's generic-cost reduction |
| `SacrificeRequirement` / `legal_sacrifice_victims` / `sacrifice_physical_object` | source/victim types, controller, token permission, source tap requirement | Phyrexian Altar's creature sacrifice as a source-backed mana ability |
| `ZoneTransfer` / `transfer_physical_object` | source/destination zones, source types, owner/controller restrictions, historical move reason | Mystic Sanctuary's instant/sorcery graveyard return to library top, Riptide Laboratory Wizard bounce and Step Through creature bounce |

These are **shared mechanics, not a newly-created state engine**. The
historical table continues to own costs, priority, stack frames, event order,
source references, choices, live zones and dependency validation. Any
unimplemented spell/activated/triggered effect remains unimplemented; moving
its description to a template does not authorize new unknown-card effects.

Some old behavior requires **composed steps** rather than replacing the
whole effect: Consider still surveils before drawing; Frantic Search still
untaps lands after drawing and discarding; Baral's draw/discard remains
conditional on the existing optional trigger; Mystic Sanctuary's target must
be legally selected and survives its existing fizzle checks; Phyrexian Altar
still uses the existing mana planning/commit code and correct event emission.
As with all historical migrations, regression suite and deterministic
fingerprints are the acceptance gate.

**Next**: share token-creation configurations across spell and triggered
providers; lift more of the static/dynamic reduction predicates into typed
declarations; extend generic zone operations to graveyard-to-hand and
graveyard-to-battlefield recursion with reviewed eligibility, timing and
replacement-effect checks; extract copy-source targeting and delayed exile
into reusable primitives. Avoid card-specific condition branches in the
shared executor. Preserve the existing exact fidelity before promoting
unknown cards to reviewed hybrids.

## M2.9 — recurring token, recursion and spell-copy composition

The historical v7 trigger resolver and v34 Mage Siege token effect now use
the shared `spawn_repeated_tokens` operation from
`commander_sim/legacy_common_ops.py`. The existing v24 Ral's Reinforcements
already uses the same token batch abstraction. The kernel/table callback
still creates each real object with its original printed identity, colors,
controller and event rules; **no generic trigger registration is invented**.

Graveyard-to-library recursion is now explicitly constrained through
`ZoneTransfer(allowed_types_any=frozenset({'instant','sorcery'}),
require_owner=True)` for Mystic Sanctuary. This check is deliberately
shared with other zone transfers and fails closed for ineligible object
IDs; the old trigger policy/targeting and fizzle checks remain intact.
Other possible destinations such as graveyard→hand and graveyard→battlefield
use the same typed zone-move structure, but must still be authorized by a
reviewed card effect and the full timing/permission rules. They are not
automatically enabled in the bounded six-turn pilot.

The large duplicated Reiterate implementations in historical v33 and v35
now call `commander_sim/legacy_spell_copy.py` for **one** virtual-copy
lifecycle and configurable retargeting. `CopyTargetRule` supports original
target retention, a single legal permanent target, counterspell spell-type
restrictions, a target spell for copying Reiterate, and Step Through's
two distinct creature targets. The game table remains responsible for
deciding whether a spell is copyable, paying for Reiterate, choosing legal
priority and applying copied-effect resolution. A virtual copy is **not**
cast and does not create a physical hand or library card; the existing
spell-copied event and triggers still fire once.

Regression requirements include explicit tests for preserved original
targets, illegal retarget refusal, copied counterspells, two-target copies,
repeated token identity/order, Mystic Sanctuary eligibility, and the
historical frozen replay fingerprints. New cards reuse these operations by
registering verified parameters and authorization; no broad text-based
ability inference is introduced.

Still pending: multi-card token-trigger **declaration registration** and
stable ability-slot dispatcher, arbitrary graveyard-to-hand/battlefield
recursion with actual cost/permission/replacement handling, complex delayed
effects, and the first multi-deck cross-color turn-driver integration.
