# V15 assessment

October 29, 2026. Mystic Sanctuary, Fiery Islet and Riptide Laboratory have the
bounded utility behavior described in README.md. No additional caching is added.

## Validation and runtime

- **585 tests** passed across fifteen suites; **38 new tests** cover the batch.
- All **six forced narratives** passed using conserved inventories and source
  payments. The target-exile response is an explicitly synthetic fixture; it does
  not claim a newly supported printed graveyard-exile card.
- **200 twelve-round games**, with Magnus in each seat and three opponent groups,
  passed physical-card, zone-index, battlefield-view, spell-frame and mana-pool
  consistency checks. **No safety stops**. The sweep recorded 100,710 steps,
  11,021 payments and 23 utility-event records in 121 seconds.
- Exploratory median milliseconds per eight-round game across 12 samples per
  engine: v14 LandTable **394.733**, v15 UtilityTable **415.247**. Host load and
  new decisions change game trajectories; this is not a controlled causal
  benchmark. Performance history is preserved without additional caching.
- Four existing v14 reference cases, one per Magnus seat, regenerated with exact
  fingerprints after the shared stack hook was added. The v14 suite remains intact.

## Observed interactions

1. Three Islands allowed Sanctuary's untapped entry. Its trigger put Ponder from
   graveyard on top, enabling a later draw and source-paid second cast; Young
   Pyromancer produced one Elemental for each cast.
2. A target moving out of the graveyard while Sanctuary's trigger waited caused
   that trigger to fail. The response was a declared synthetic fixture.
3. Fiery Islet paid one life for U without damage; after a declared next-turn
   untap, another source paid one mana and Islet was tapped/sacrificed to draw.
4. Brainstorm resolved in response to Islet's paid draw ability; the Islet draw
   occurred after Brainstorm's draw/put-back instructions completed.
5. Arcane Adaptation made Iconoclast a Wizard for Riptide. Capsize bounced that
   target in response, causing Riptide to fail on recheck. Iconoclast's already
   triggered ability was doubled by Harmonic and produced two Soldiers.
6. Bouncing Adaptation instead left Iconoclast on the battlefield but removed its
   Wizard type; Riptide's waiting ability then failed its target recheck.

Unit checks cover target selection at trigger placement after the current action,
no legal target, optional decline, target identity after zone changes, source
independence, forced-tapped entry, costs and source reservation, 1U versus other
costs, noncreature Wizard permanents, shroud/control/type checks, token bounce,
empty-library loss, response timing and all-seat conservation.

## Coverage and limits

The updated audit covers 100 physical cards across 83 names: **41 supported
subsets, 7 partial and 35 unsupported names**, or **58/7/35 physical cards**.
Supported subset is not a complete Oracle certification. Riptide's correct
activation cost is **1U**, and its target is any Wizard permanent controlled by
the activator; these cases have explicit tests.

General graveyard protection, arbitrary control changes, comprehensive continuous
layers/replacement effects, Otawara/Sokenzan channel, full modal double-faced
behavior, spell-copy producers, commander damage and verified loops remain out of
scope. One detailed Magnus deck with synthetic opponents does not support empirical
deck win-rate inference. V14 reference cases and historical performance history
remain available for future caching comparisons; v15's rules deliberately change
some trajectories, so v14 hashes apply to unchanged v14 semantics only.

Next: Otawara and Sokenzan channel, then spell-copy and tutor/creature activation
support. Continue tracking runtime and defer additional caching until functionality
is established.

Rollback: b0b0237ee915532b4d2f4ca3b089999671294b27. V15 adds its own provider,
table and diagnostics plus a backward-compatible stack target-preparation seam.
Historical manifests remain checkpoint records.
