# V9c source-mana assessment — October 28, 2026

## Outcome and preservation

Live spells and counterspells in all four seats now pay through physical source
IDs and kernel-owned tap flags/pools. The v6 `ColoredPayment` policy and isolated
v9a DFS no longer pay live v9c costs. Detailed and synthetic providers supply
explicit ability descriptors to one generic ordered planner/executor.

The rollback point before this milestone is
`eb32c1153ca6793cc0a69d66f6bc6919dd7eb374`. V9c is a new directory. V9b receives
backward-compatible construction, resource-refresh/payment and cleanup hooks;
its standalone policy remains unchanged. The v8 battlefield and v9b projection
bridge skip legacy source-name mutations when the source-backed table is active.
All 222 historical tests pass. Earlier manifests remain dated checkpoint records;
this milestone's manifest hashes the current changed files and outputs.

## Validation

- **271 tests pass across nine suites**, including **49 new source-mana tests**.
- **400 twelve-round games** (seeds 0–99 in each Magnus seat; three rotating
  opponent groups) preserved physical-card counts, zone/view consistency and
  valid mana pools, with **no safety stops**.
- That sweep recorded **20,529 spell/counter payments** and **58,791 ordered
  source activations**. Each payment used distinct source IDs. The highest
  successful search visited **1,611 states**, below the configured 20,000-state
  limit. A separate test forces budget failure before any payment mutation.
- Four narrated diagnostics are reproducible; one has an explicitly forced
  opening. `validation_results.json` contains the exact records.
- Thirty seeded small source configurations matched an independent exhaustive
  reference search, including dependent Signet/filter funding and impossible
  colored costs. Unit tests also check stale/altered plans, source/controller
  legality, exact floating pools, Treasure sacrifice, life costs versus damage,
  trigger-created resources, phase clearing, portable seats and conservation.

Reproduce from root:

```bash
python run_all_tests.py
python simulator/v9c_mana/validate.py
```

These results validate infrastructure behavior, not Magnus deck power.

## Correctness review

Plans validate current source IDs, abilities, controllers/tap flags, life and
floating pool. Search is read-only; commit rejects stale or altered plans before
activating anything. Generic and colored activation costs are funded in order,
so Izzet Signet cannot use its own prospective output. Cascade Bluffs' filter
requires a colored input. Floating mana remains available for subsequent costs
in the same modeled phase, and every exposed boundary clears all players' pools.

Treasure's modeled choices are U/R, never colorless. Paying a generic cost can
spend that colored mana. Its actual token taps and sacrifices before output;
future cast triggers cannot finance their own spell. A Treasure from a completed
cast trigger can fund a later spell. Talisman/Shivan colored production marks
damage; Islet pays life. Reaching zero during casting removes the player's spell
at the subsequent cast boundary. This is limited casting/SBA integration, not
an assertion that general trigger/priority timing is complete.

Fellwar Stone and Exotic Orchard no longer assume U/R from synthetic opponents.
Their available colors derive from opposing modeled lands' possible output,
ignoring tap/activation-cost availability and breaking recursive Orchard cycles.
Both exclude colorless. Since synthetic lands currently produce only colorless,
neither gets a color from those lands. This is a deliberate consequence of the
explicit synthetic provider, not evidence that the real cards are weak.

## Efficiency review

The final local 40-game ten-round medians were **41.424 ms for v9b** and
**69.603 ms for v9c** (about 1.7x). The sweep took 35.133 seconds. Machine load and
different legal game trajectories limit comparisons; no formal performance or
statistical claim is made.

A separate cProfile run over ten games showed repeated source/projection queries,
full zone audits and payment planning as major costs. Identical-source grouping,
pending-state deduplication, immutable static metadata and state-signature caches
avoid source-order permutations and repeated affordability searches. The solver
still has a combinatorial worst case and fails closed on its budget. Keep the
independent full audits when adding faster projections or incremental indexes.

## Remaining gates

General spell/ability priority is still unfinished. The inherited counter-only
stack settles cast triggers before responses. The driver does not yet expose
every official step; it combines upkeep/draw/land development, clears pools at
its main/combat/end/turn boundaries and retains precombat hand-size cleanup.

Only U/R/colorless pools and U/R/generic costs are supported. Other colors,
explicit colorless requirements, hybrid spell costs, restricted mana, arbitrary
mana text, alternative/additional spell costs, creature tap abilities and mana
replacement/prevention/triggered effects remain unsupported. Treasure's other
colors are not represented. Existing selection/scry, some land ETB/utility
behavior and Frantic Search untapping remain incomplete. One detailed deck only;
no commander damage, spell copying, buyback or verified Magnus loops.

The next gate is general triggered/activated frames and priority, followed by
finer step timing and multiple detailed decks/card expansion. The README records
these boundaries; source-backed payment does not imply a complete rules engine.

## Rules references consulted

Official [Comprehensive Rules effective September 25, 2026](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.pdf), linked from the
[Wizards rules page](https://magic.wizards.com/en/rules): 106.4 (pools and
boundaries), 106.7 (possible source output), 111.10a (Treasure), 118.3 (payment),
601.2g–i (mana payment/cast completion), 605.3 (immediate mana abilities).
Card-specific outputs/costs are explicit limited provider metadata; unsupported
abilities are not silently treated as generic mana production.
