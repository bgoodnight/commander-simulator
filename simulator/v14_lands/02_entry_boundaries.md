# Entry checks use current other lands, types and opponents

Forced conserved setup; real deck cards and source payments.

Coast entered tapped with one other land and untapped with two. Canal entered tapped with three other lands. Sanctuary entered untapped with two basic Islands plus Steam Vents (an Island); its graveyard trigger remains deferred. Training Center entered tapped after the table dropped to one opponent.

## Branch 1

```text
FORCED DIAGNOSTIC: conserved actual cards, declared battlefield/hand setup; not a natural opening.
    LAND ENTERS P0: Island #455; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Stormcarved Coast #457; tapped=True; life_paid=0; cause=land_play.
```

## Branch 2

```text
FORCED DIAGNOSTIC: conserved actual cards, declared battlefield/hand setup; not a natural opening.
    LAND ENTERS P0: Island #483; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #485; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Stormcarved Coast #487; tapped=False; life_paid=0; cause=land_play.
```

## Branch 3

```text
FORCED DIAGNOSTIC: conserved actual cards, declared battlefield/hand setup; not a natural opening.
    LAND ENTERS P0: Island #469; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #471; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #473; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Spirebluff Canal #475; tapped=True; life_paid=0; cause=land_play.
```

## Branch 4

```text
FORCED DIAGNOSTIC: conserved actual cards, declared battlefield/hand setup; not a natural opening.
    LAND ENTERS P0: Island #455; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Island #457; tapped=False; life_paid=0; cause=declared_fixture.
    LAND ENTERS P0: Steam Vents #459; tapped=False; life_paid=2; cause=declared_fixture.
    LAND ENTERS P0: Mystic Sanctuary #461; tapped=False; life_paid=0; cause=land_play.
```

## Branch 5

```text
FORCED DIAGNOSTIC: conserved actual cards, declared battlefield/hand setup; not a natural opening.
    ELIMINATED P2 (control): declared_fixture.
    ELIMINATED P3 (combo): declared_fixture.
    LAND ENTERS P0: Training Center #483; tapped=True; life_paid=0; cause=land_play.
```
