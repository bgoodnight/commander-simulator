# V16 channel interaction report

Forced fixtures; actual land payments. The target removal is explicitly synthetic.

## Sokenzan creates Spirits

Four actual Mountains pay for channel; the discarded land remains in the graveyard and two hasty Spirit tokens enter.

```text
    LAND ENTERS P0: Mountain #455; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #457; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #459; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Mountain #461; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Mountain #455 -> (0, 0, 1)
    MANA P0: Mountain #457 -> (0, 0, 1)
    MANA P0: Mountain #459 -> (0, 0, 1)
    MANA P0: Mountain #461 -> (0, 0, 1)
    STACK +1 [activated] P0: channel_sokenzan.
```

## Otawara target removed

Four actual Islands pay for channel; a synthetic response removes the target and the waiting ability fails its legality check.

```text
    LAND ENTERS P0: Island #483; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #485; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #487; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #489; tapped=False; life_paid=0; cause=declared_fixture.
    MANA P0: Island #483 -> (0, 1, 0)
    MANA P0: Island #485 -> (0, 1, 0)
    MANA P0: Island #487 -> (0, 1, 0)
    MANA P0: Island #489 -> (0, 1, 0)
    STACK +1 [activated] P0: channel_otawara.
SYNTHETIC RESPONSE: target destroyed while the channel ability waits.
```

200 games: 0 safety stops; 6 channel activations. Median eight-round milliseconds: {'UtilityTable': 572.472, 'ChannelTable': 559.035}. Different game trajectories limit comparisons.

Token color is not represented in the current kernel.
