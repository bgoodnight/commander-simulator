# Reusable battlefield-characteristic-scaled effects — November 3, 2026

The first implementation milestone from the Necron Dynasties / Wretched Ranks
observed rules-gap audit is **shared parameterized removal**, not new bespoke
card engines.

## Implemented

`RemovalRule.amount_basis` accepts `fixed` or `swamps_controlled`.
`reviewed_amount(kernel, seat, rule)` queries current physical battlefield
objects, requiring both a land type and the derived **Swamp** subtype. It
uses `kernel.subtypes` instead of checking land names, so source-backed
subtype changes can participate. It does not count an opponent's Swamps.

- **Mutilate** — printed profile checked by exact pinned Oracle identity,
  wording, mana cost and type. Uses the existing `debuff_all` operation
  with a variable amount from Swamps controlled. The kernel applies real
  end-of-turn stat modifiers, state-based deaths and the existing death
  engine. Includes friendly creatures.
- **Consuming Corruption** — same magnitude provider, composed with a
  shared creature-damage action and player life gain. Uses actual mana
  sources and a target-legal creature object. Damage and life gain are
  distinct kernel operations, and state-based deaths use real zones.

The generic pilot now considers a fixed-per-board `debuff_all` separately
from paid-X Toxic Deluge (whose X still comes from its life-cost decision)
and can choose a creature for a worthwhile `damage_gain` spell.

## Strict caveats

- Consuming Corruption currently targets **creatures only**, not
  planeswalkers. The latter printed alternative requires loyalty/damage
  support and remains missing. This is reviewed *partial* spell coverage.
- No universal instant response window or four-real-deck opponent priority
  is added here. Actions still resolve in the bounded physical runner.
- The source snapshot / printed text must match the registration exactly;
  Oracle text does not become executable from regex classification.
- This update does **not** address the static anthem and graveyard
  replacement gaps (Bad Moon, Patchwork Banner, Liliana's Mastery,
  Out of the Tombs, Living Death, etc.). Those need separate shared
  operations and should not be approximated by no-op effects.
- Do not compare updated win rates to historical cohorts as if they
  reflect real precon-vs-precon games.

## Reproduction

```sh
python -m unittest tests.test_reviewed_removal_spells -v
python -m unittest tests.test_resource_pilot tests.test_kernel_life \
  tests.test_physical_common_effects -v
```

The regression cases include a cross-seat Swamp that must not contribute,
a non-Swamp land that must not contribute, a nonlethal creature that retains
its debuff until cleanup, lethal creature deaths, actual source payment,
life gain, no-Swamps decline, and printed-metadata fail-closed behavior.

## Next general mechanism

Implement a **continuous source-dependent static modifier** with an explicit
typed filter (color, subtype, controlling seat and affected types). This can
support Bad Moon, Liliana's Mastery, and the subtype-choosing Patchwork Banner
without periodically stamping permanent +1/+1 counters or bespoke stat
changes. It must automatically recompute when the source enters or leaves,
when a creature changes zone/controller, or when creature type/color changes.
Liliana's Mastery also needs its independently reviewed two-Zombie ETB.

Then add symmetric batch zone movements / triggered recursion for the Necron
graveyard suite, followed by new matched-seed narrative audits.
