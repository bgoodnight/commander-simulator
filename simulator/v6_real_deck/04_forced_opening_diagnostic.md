# v6 narrated game: 04_forced_opening_diagnostic
**Seed:** 404  **Seats:** Magnus (real v1.6), control, combo, tokens
**Opening:** FORCED diagnostic, not a random opening
**Result:** turn_limit, winner seat None, 10 rounds
## Summary of the Magnus seat
- Life 27; 7 lands; 8 total spells cast; Magnus cast 2 time(s); 6 tokens on battlefield at end.
- Cards cast by coverage: {'supported': 6, 'approx': 2}; remaining unsupported in hand: ['Heralds of Tzeentch', "Jace, Vryn's Prodigy", 'Mathemagics', 'Mana Geyser', 'Reiterate', 'Underworld Breach'].
- Unsupported distinct nonland card definitions: 38.

## Board-state timeline
| Round | Magnus life / creatures / tokens / mana sources | P1 life/power | P2 life/power | P3 life/power |
|---:|---|---|---|---|
| 1 | 40 / 0 / 0 / 3 | 40 / 0 | 40 / 0 | 40 / 0 |
| 2 | 40 / 1 / 0 / 4 | 40 / 0 | 40 / 2 | 40 / 0 |
| 3 | 40 / 2 / 0 / 5 | 40 / 0 | 40 / 5 | 40 / 0 |
| 4 | 38 / 3 / 1 / 6 | 40 / 0 | 40 / 5 | 40 / 0 |
| 5 | 36 / 4 / 2 / 7 | 36 / 0 | 40 / 5 | 40 / 3 |
| 6 | 36 / 5 / 3 / 7 | 30 / 0 | 36 / 5 | 40 / 4 |
| 7 | 36 / 6 / 4 / 7 | 30 / 0 | 36 / 5 | 33 / 2 |
| 8 | 36 / 6 / 4 / 8 | 29 / 0 | 30 / 5 | 33 / 5 |
| 9 | 35 / 6 / 4 / 10 | 17 / 0 | 30 / 15 | 28 / 9 |
| 10 | 27 / 8 / 6 / 10 | 17 / 3 | 26 / 27 | 25 / 11 |

## Event-by-event narrative
```text

========== ROUND 1 ==========
  P1 land -> 1 lands.
  P2 land -> 1 lands.
  P3 land -> 1 lands.
  P0 plays Island (1 lands).
  P0 (magnus) casts Sol Ring artifact [named_rock] cost 1, mana left 0.
    Sol Ring increases available mana next turn.
  End round: P0 magnus life=40 board=0 sources=3, P1 control life=40 board=0 sources=1, P2 combo life=40 board=0 sources=1, P3 tokens life=40 board=0 sources=1

========== ROUND 2 ==========
  P2 land -> 2 lands.
  P2 (combo) casts engine enchantment [engine] cost 2, mana left 0.
  P3 land -> 2 lands.
  P0 plays Mountain (2 lands).
  P0 (magnus) casts Young Pyromancer creature [named_creature] cost 2, mana left 2.
    Young Pyromancer enters battlefield (2/1).
  End round: P0 magnus life=40 board=2 sources=4, P1 control life=40 board=0 sources=1, P2 combo life=40 board=2 sources=2, P3 tokens life=40 board=0 sources=2

========== ROUND 3 ==========
  P2 land -> 3 lands.
  P2 (combo) casts engine enchantment [engine] cost 3, mana left 0.
  P3 land -> 3 lands.
  P0 plays Spirebluff Canal (3 lands).
  P0 (magnus) casts Magnus the Red creature [named_creature] cost 5, mana left 0.
    Magnus the Red enters battlefield (4/5).
  End round: P0 magnus life=40 board=6 sources=5, P1 control life=40 board=0 sources=1, P2 combo life=40 board=5 sources=3, P3 tokens life=40 board=0 sources=3

========== ROUND 4 ==========
  P2 (combo) casts draw sorcery [draw] cost 2, mana left 1.
    COMBAT P2 combo:engine:7 attacks P0 unblocked for 2.
  P3 land -> 4 lands.
  P3 (tokens) casts engine enchantment [engine] cost 4, mana left 0.
  P0 plays Mountain (4 lands).
  P0 (magnus) casts Preordain sorcery [named_selection] cost 1, mana left 5.
    Cast triggers: 1 tokens/treasures/draw effects; token count=1.
    Preordain: partial card selection (1 cards drawn; exact look/scry not modeled).
  End round: P0 magnus life=38 board=7 sources=6, P1 control life=40 board=0 sources=1, P2 combo life=40 board=5 sources=3, P3 tokens life=40 board=0 sources=4

========== ROUND 5 ==========
  P2 land -> 4 lands.
  P2 (combo) casts draw sorcery [draw] cost 2, mana left 2.
  P2 (combo) casts ramp artifact [ramp] cost 2, mana left 0.
    COMBAT P2 combo:engine:2 attacks P0 unblocked for 2.
  P3 land -> 5 lands.
  P3 (tokens) casts engine enchantment [engine] cost 4, mana left 1.
  P3 (tokens) casts small creature [creature] cost 1, mana left 0.
  P0 plays Mountain (5 lands).
    COMBAT P0 Magnus the Red attacks P1 unblocked for 4.
    Blade of Magnus creates a 3/3 Spawn token.
  End round: P0 magnus life=36 board=10 sources=7, P1 control life=36 board=0 sources=1, P2 combo life=40 board=5 sources=6, P3 tokens life=40 board=3 sources=5

========== ROUND 6 ==========
  P2 land -> 5 lands.
  P2 (combo) casts ramp artifact [ramp] cost 3, mana left 4.
  P2 (combo) casts draw sorcery [draw] cost 2, mana left 2.
  P2 (combo) casts draw sorcery [draw] cost 2, mana left 0.
    COMBAT P2 engine token attacks P1 unblocked for 1.
  P3 land -> 6 lands.
  P3 (tokens) casts engine enchantment [engine] cost 3, mana left 3.
  P3 (tokens) casts buff sorcery [buff] cost 2, mana left 1.
    COMBAT P3 tokens:small:4 attacks P1 unblocked for 4.
  P0 misses land drop.
    COMBAT P0 Magnus the Red attacks P2 unblocked for 4.
    Blade of Magnus creates a 3/3 Spawn token.
    COMBAT P0 Elemental attacks P1 unblocked for 1.
  End round: P0 magnus life=36 board=13 sources=7, P1 control life=30 board=0 sources=1, P2 combo life=36 board=5 sources=8, P3 tokens life=40 board=4 sources=6

========== ROUND 7 ==========
  P1 land -> 2 lands.
  P1 (control) casts ramp artifact [ramp] cost 2, mana left 0.
  P2 land -> 6 lands.
  P2 (combo) casts draw sorcery [draw] cost 3, mana left 6.
  P2 (combo) casts ramp artifact [ramp] cost 2, mana left 4.
  P2 (combo) casts ramp artifact [ramp] cost 2, mana left 2.
  P2 (combo) casts combo_piece artifact [combo_piece] cost 2, mana left 0.
    COMBAT P2 combo:engine:2 attacks P3 unblocked for 2.
    COMBAT P2 engine token attacks P3 unblocked for 1.
  P3 (tokens) casts engine enchantment [engine] cost 4, mana left 2.
  P0 misses land drop.
  P0 (magnus) casts Ponder sorcery [named_selection] cost 1, mana left 6.
    Cast triggers: 1 tokens/treasures/draw effects; token count=4.
    Ponder: partial card selection (1 cards drawn; exact look/scry not modeled).
    COMBAT P0 Magnus the Red attacks P3 unblocked for 4.
    Blade of Magnus creates a 3/3 Spawn token.
    COMBAT P0 Spawn 3/3 into P3 tokens:small:4 4/2.
  End round: P0 magnus life=36 board=14 sources=7, P1 control life=30 board=0 sources=3, P2 combo life=36 board=5 sources=11, P3 tokens life=33 board=2 sources=6

========== ROUND 8 ==========
  P1 (control) casts ramp artifact [ramp] cost 3, mana left 0.
  P2 land -> 7 lands.
  P2 (combo) casts ramp artifact [ramp] cost 2, mana left 10.
  P2 (combo) casts draw sorcery [draw] cost 3, mana left 7.
  P2 (combo) casts draw sorcery [draw] cost 2, mana left 5.
  P2 (combo) casts combo_piece artifact [combo_piece] cost 3, mana left 2.
  P2 (combo) casts removal instant [remove] cost 2, mana left 0.
    Magnus returns to the command zone (commander tax on next cast).
    COMBAT P2 engine token 1/1 into P3 engine token 1/1.
  P3 (tokens) casts tokens sorcery [tokens] cost 3, mana left 3.
  P3 (tokens) casts draw sorcery [draw] cost 2, mana left 1.
  P3 (tokens) casts small creature [creature] cost 1, mana left 0.
    COMBAT P3 engine token attacks P1 unblocked for 1.
  P0 plays Cascade Bluffs (6 lands).
  P0 (magnus) casts Magnus the Red creature [named_creature] cost 7, mana left 1.
    Magnus the Red enters battlefield (4/5).
    COMBAT P0 Spawn attacks P2 unblocked for 3.
    COMBAT P0 Spawn attacks P2 unblocked for 3.
  End round: P0 magnus life=36 board=14 sources=8, P1 control life=29 board=0 sources=5, P2 combo life=30 board=5 sources=13, P3 tokens life=33 board=5 sources=6

========== ROUND 9 ==========
  P1 land -> 3 lands.
  P1 (control) casts engine enchantment [engine] cost 3, mana left 3.
  P1 (control) casts draw sorcery [draw] cost 2, mana left 1.
  P2 land -> 8 lands.
  P2 (combo) casts combo_piece artifact [combo_piece] cost 4, mana left 10.
  P2 (combo) casts medium creature [creature] cost 3, mana left 7.
  P2 (combo) casts large creature [creature] cost 6, mana left 1.
    COMBAT P2 combo:engine:2 attacks P3 unblocked for 2.
  P3 land -> 7 lands.
  P3 (tokens) casts tokens sorcery [tokens] cost 4, mana left 3.
  P3 (tokens) casts small creature [creature] cost 2, mana left 1.
    COMBAT P3 engine token attacks P1 unblocked for 1.
    COMBAT P3 engine token attacks P1 unblocked for 1.
    COMBAT P3 Token attacks P0 unblocked for 1.
    COMBAT P3 Token attacks P1 unblocked for 1.
    COMBAT P3 tokens:small:1 attacks P1 unblocked for 1.
  P0 plays Island (7 lands).
  P0 (magnus) casts Mind Stone artifact [named_rock] cost 2, mana left 7.
    Mind Stone increases available mana next turn.
    COMBAT P0 Elemental 1/1 into P3 engine token 1/1.
    COMBAT P0 Spawn attacks P1 unblocked for 3.
    COMBAT P0 Elemental attacks P1 unblocked for 1.
    COMBAT P0 Spawn attacks P3 unblocked for 3.
    COMBAT P0 Magnus the Red attacks P1 unblocked for 4.
    Blade of Magnus creates a 3/3 Spawn token.
  End round: P0 magnus life=35 board=16 sources=10, P1 control life=17 board=0 sources=6, P2 combo life=30 board=15 sources=14, P3 tokens life=28 board=9 sources=7

========== ROUND 10 ==========
  P1 (control) casts engine enchantment [engine] cost 4, mana left 2.
  P1 (control) casts draw sorcery [draw] cost 2, mana left 0.
    Cast triggers: 1 tokens/treasures/draw effects; token count=5.
    P0 counters control:draw:5 with Counterspell.
  P2 land -> 9 lands.
  P2 (combo) casts medium creature [creature] cost 3, mana left 12.
  P2 (combo) casts removal instant [remove] cost 2, mana left 10.
  P2 (combo) casts large creature [creature] cost 7, mana left 3.
    COMBAT P2 combo:large:1 attacks P0 unblocked for 6.
  P3 (tokens) casts tokens sorcery [tokens] cost 4, mana left 3.
  P3 (tokens) casts ramp artifact [ramp] cost 3, mana left 0.
    COMBAT P3 engine token 1/1 into P2 combo:engine:2 2/3.
    COMBAT P3 tokens:small:1 1/3 into P2 combo:medium:0 3/3.
    COMBAT P3 engine token 1/1 into P2 combo:engine:7 2/3.
    COMBAT P3 Token attacks P0 unblocked for 1.
    COMBAT P3 Token 1/1 into P2 combo:medium:2 4/3.
    COMBAT P3 tokens:small:3 attacks P0 unblocked for 1.
  P0 misses land drop.
    COMBAT P0 Spawn attacks P3 unblocked for 3.
    COMBAT P0 Magnus the Red attacks P2 unblocked for 4.
    Blade of Magnus creates a 3/3 Spawn token.
  End round: P0 magnus life=27 board=20 sources=10, P1 control life=17 board=3 sources=6, P2 combo life=26 board=27 sources=15, P3 tokens life=25 board=11 sources=8
```

## Important limitations
This is a mixed-deck integration diagnostic, **not** a valid Magnus deck power or win-rate evaluation. Unsupported cards cannot resolve; some selection spells and the opponent stack remain simplified. See `ASSESSMENT.md` for supported interactions and missing mechanics.
