# Declarative continuous creature statistics — November 3, 2026

The generic physical kernel now evaluates a strictly bounded subset of
continuous static modifiers, rather than adding counters or permanent stat
changes to recipients.

## Universal mechanism

Each source CardDefinition can declare a `static` ability with operation
`creature_stat_modifier` and typed arguments:

- `scope`: `all` or `controller`
- `color`: optional exact printed color predicate
- `subtype`: optional derived subtype predicate, or `chosen`
- `power` and `toughness`: signed integer deltas

The same `GameKernel.static_stat_adjustment` calculates both P/T values on
demand from the **current** battlefield, controller and selected subtype.
Cards entering/leaving, controller changes and additive subtype changes are
reflected without modifying any printed card, creating phantom counters, or
maintaining a shadow battlefield. Multiple static sources compose additively.

The host provides an explicit `choose_creature_subtype` for effects requiring
an as-enters choice; until chosen, a chosen-subtype effect does not silently
guess one. The bounded pilot derives a preferred creature type from its
source-pinned decklist, without commander-name special cases.

## Actual reviewed cards

- **Bad Moon** — +1/+1 to ALL verified black creatures, including opponents.
  Source owner is not a predicate.
- **Liliana's Mastery** — +1/+1 to the source controller's Zombies; its two
  physical 2/2 black Zombie ETB tokens are created via the existing shared
  token blueprint and immediately receive the ongoing +1/+1.
- **Patchwork Banner** — +1/+1 to creatures the controller owns of the
  explicit chosen type. Its ordinary mana ability uses the existing reviewed
  commander-color source modes. Entering choice is deck-derived by policy.

All three are admitted only on exact verified Oracle ID, printed text,
mana cost and type. Their static behavior is registered in
`named_effect_coverage` as a reviewed **suboperation**, not full-card proof.

## State-based action behavior

After a continuous source enters/leaves the battlefield, the physical kernel
rechecks lethal toughness. An active creature at **zero or negative toughness**
goes to the graveyard as a state-based action, without being destroyed or
dealt damage. **Indestructible, damage prevention, shield counters and
regeneration cannot save it through those mechanisms.** Non-targeted
continuous effects also do not target, so ordinary hexproof/shroud does not
stop them. This does NOT grant a targeted spell permission to ignore hexproof,
ward or protection.

The check repeats until stable, including cascading deaths after a stat
source leaves. It takes a simultaneous lethal-ID snapshot for each pass.
Stale prior-zone object views no longer query modifiers from obsolete kernel
object IDs.

## Fidelity limits

This is a constrained additive, typed stat system, NOT a comprehensive
Magic continuous-effect layer engine. It does not yet implement timestamps,
dependencies, characteristic-defining abilities, arbitrary color-changing
layers, dynamic type-changing interactions beyond the already-reviewed subtype
query, or comprehensive replacement/shield/regen rules. Unknown colors are
not guessed and unreviewed printed static effects remain unavailable.

The updated bounded pilot still has abstract opponent seats, and a fully
timed multiplayer priority/stack host remains outstanding.

## Testing

`python -m unittest tests.test_static_creature_effects -v`

The new tests verify global vs controller scope, black vs other colors,
stacked effects, physical Zombie ETB tokens, selected creature types,
source removal, exact Oracle identity, and a two-stage lethal cascade.
They include an indestructible/hexproof/shield-marked creature whose
toughness drops below zero, ensuring it dies as a **state-based** movement,
not destruction. CI also runs existing removal, phase, life, opponent
pressure and effect-coverage regressions plus both precon smoke games.

After merging this branch, rerun the observed 20-game precon rules audit
and compare support-event changes on matched seeds; avoid interpreting any
small win-share change as a realistic head-to-head result.
