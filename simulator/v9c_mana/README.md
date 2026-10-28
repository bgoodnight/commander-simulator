# V9c — live source-backed mana

October 28, 2026. All four live seats pay through the same ordered source-ID
resource service on the v9b physical-card kernel. This is a mana migration, not
a general priority or complete printed-card milestone.

## What changed

`Resources` reads existing battlefield objects; it never creates replacement
lands or keeps a second mana-source inventory. Source tap flags and each seat's
C/U/R pool live on the same kernel as card zones and combat. Immutable provider
`Ability` values describe production, activation costs, life payments, damage and
sacrifice. Card-specific declarations are in `provider.py`, outside the planner.

Every main spell and counterspell pays through `SourcePayment`. Plans contain
ordered physical source IDs and chosen mana modes. Planning is read-only and
bounded; stale or altered plans are rejected before any payment. A source can
activate once per tap cycle. Identical abilities are grouped by remaining counts,
while the committed plan still identifies individual objects. Pending states
are deduplicated; repeated affordability queries cache an exact resource-state
signature. Budget exhaustion leaves the game unresolved.

Supported live behavior:

- Izzet Signet requires funding before producing U/R; it cannot fund itself.
- Cascade Bluffs needs U or R for a filtered output; colorless mana alone cannot
  pay that activation. Its ordinary colorless mode remains separate.
- Excess production remains in the kernel pool between payments. Pools empty at
  the current driver's main/combat/end/turn boundaries, for all players.
- Treasures tap and sacrifice their actual token objects. The modeled output
  choices are U/R, not colorless; other Treasure colors are outside this engine's
  current cost/color subset. A cast-trigger Treasure can fund a later spell,
  never the spell that would create that trigger.
- Shivan Reef/Talisman colored production deals damage; their colorless modes do
  not. Fiery Islet pays life, which is distinguished from damage. Costs cannot
  pay more life than available. A player reaching zero life while paying for a
  spell leaves at the subsequent cast boundary, removing their spell objects.
- Newly resolved noncreature rocks enter untapped and can be used immediately.
- Opponent sources cannot pay another player's costs. Untapping one player
  leaves opponents' source tap flags intact.
- Fellwar Stone and Exotic Orchard derive colors from opposing modeled lands,
  including tapped lands' potential output. Neither produces colorless mana.
  Recursive Orchard dependencies do not invent a color without a grounded land.

Synthetic lands explicitly produce one colorless mana; synthetic ramp produces
its declared approximate amount. This is the same source/tap/payment machinery,
with synthetic provider metadata. Those lands supply no color to Fellwar Stone
or Exotic Orchard. The former unconditional U/R assumption is removed.

`player.mana`, `ready_sources`, `floating`, `treasures` and source counts are
read-only pilot/reporting projections. `mana` is a capacity upper bound for
heuristics; actual affordability always uses the planner. The v6 payment policy
and isolated v9a DFS are not used in v9c live payment.

## Running

From repository root:

```bash
python run_all_tests.py
python simulator/v9c_mana/validate.py
```

There are **271 tests in nine suites**, including 49 v9c checks. The validation
script writes four narrated replay pairs and `validation_results.json`, checks
400 twelve-round games, audits physical-card conservation and resource
consistency, and times 40 ten-round games per engine.

Programmatic use, with this directory on the Python path:

```python
from game import ManaTable
from resources import Cost

table = ManaTable(['control', 'aggro', 'magnus', 'combo'], seed=104).run(10)
assert table.assert_consistent()
# Inspect table.resources.payments / activations for physical source IDs.
```

## Boundaries and next work

Only U/R/colorless pools and U/R/generic costs are implemented. W/B/G, explicit
colorless requirements, hybrid spell costs, restricted mana, alternative/additional
spell costs and arbitrary mana text remain unsupported. Creature tap abilities,
replacement/prevention effects and general triggered mana abilities are not
implemented. Existing selection/scry and some land ETB/utility behavior are
still approximations; Frantic Search does not yet untap lands.

The inherited driver still combines upkeep/draw/land development and uses
precombat hand-size cleanup. Pool clearing is correct at its exposed boundaries,
not a claim that every official step or priority window exists. The stack is
counter-only and cast triggers still settle before responses. Multiple real
decks, commander damage, copying, buyback and verified Magnus loops remain gated.

See `ASSESSMENT.md` for validation, performance costs and the rules references.
Next: general triggered/activated frames and priority, then finer phase timing
and additional detailed decks/card coverage. Replays are engineering diagnostics,
not validated deck win rates.
