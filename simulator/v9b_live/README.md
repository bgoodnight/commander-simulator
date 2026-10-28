# V9b — authoritative card zones in live games

October 28, 2026. This milestone connects the zone migration to actual gameplay.
It reuses v8's table, battlefield rules, turn driver and counterspell stack, and
v9a's zone interface. It is not a complete Magic rules or mana migration.

## Live behavior

- All four players initialize their decks directly in the same `IndexedKernel`
  registry used by combat and battlefield projections: 99 cards per synthetic
  seat and 99 plus a commander for Magnus.
- Opening draws and the historical single free mulligan operate on those cards.
  Mulligans shuffle the same inventory; no replacement deck is minted. Diagnostic
  fixed openings are explicitly labeled.
- `hand` and `library` are immutable tuples of ID-bearing read-only projections;
  definition parameters are immutable. Graveyard names and land counts are
  projections. Zone order contains IDs, never a second authoritative card list.
- Draw, discard, mill, search/shuffle, Brainstorm returns, Frantic Search discards,
  land play and spell movement use explicit zone operations. Excess hand cards
  enter the graveyard instead of disappearing. Printed selection effects remain
  the inherited approximations.
- Physical spells stay on stack through responses. Resolved permanent spells
  create their battlefield views from the moved spell object; they do not mint
  another physical card. Each zone change creates a fresh game-object ID.
- Counters and nested counters move their actual cards; countered Magnus returns
  to command and retains cast-count tax. Death, bounce, exile, token cessation and
  cleanup preserve registry/index/view consistency.
- Eliminated players' owned objects leave every zone without false death events.
  Two optional checks in the existing shared stack skip removed spell frames.
- Fabled Passage now sacrifices its actual card, moves a searched basic and
  shuffles. Its tapped test uses the land count. An unfetched Passage produces
  no invented mana. Other land abilities still retain declared approximations.

## Use and validation

From the repository root:

```bash
python run_all_tests.py
python simulator/v9b_live/validate.py
```

For programmatic use, run with this directory on the Python path:

```python
from live import LiveTable
table = LiveTable(['control', 'aggro', 'magnus', 'combo'], seed=104).run(10)
assert table.assert_consistent()
assert table.details.seat == 2
```

`tests.py` adds 34 acceptance/edge-case checks, bringing the aggregate to 222.
`validate.py` writes four replay pairs and a machine-readable conservation,
consistency and timing report. Synthetic persistent clock effects are explicit
synthetic tokens and do not count as physical cards. Earlier v9a outputs remain
historical; these new replays can differ due to actual shuffles and state fixes.

## Remaining boundaries

Only one detailed deck is supported. Payment still uses legacy `ColoredPayment`
and synthetic fungible mana, not v9a's source-ID `TypedMana`; kernel mana-source
tap state is not yet authoritative for payment. Ready-source names and floating
mana are temporary resource adapter state. Land and rock inventories themselves
are derived from the registry; a chosen Pathway face is object-keyed metadata.

The shared stack still offers counter-only responses. Cast triggers settle
before response selection. Land play still happens in the historical upkeep
approximation and hand-size cleanup remains precombat. Selection/scry, some land
abilities, commander damage, copying, buyback, multiblock and real Magnus combo
execution are incomplete. Unsupported spells remain unavailable. No reported
result is a validated deck win rate.

Next: migrate source-ID mana and activation costs; then general stack/priority,
several real decks and expanded named-card coverage. See `ASSESSMENT.md` for the
review and measured performance cost.
