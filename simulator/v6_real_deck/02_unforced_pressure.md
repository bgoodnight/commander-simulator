# v6 narrated game: 02_unforced_pressure
**Seed:** 105  **Seats:** Magnus (real v1.6), aggro, tokens, ramp_stompy
**Opening:** random v1.6 opening
**Result:** turn_limit, winner seat None, 10 rounds
## Summary of the Magnus seat
- Life -1; 8 lands; 6 total spells cast; Magnus cast 1 time(s); 0 tokens on battlefield at end.
- Cards cast by coverage: {'supported': 4, 'approx': 2}; remaining unsupported in hand: [].
- Unsupported distinct nonland card definitions: 38.

## Board-state timeline
| Round | Magnus life / creatures / tokens / mana sources | P1 life/power | P2 life/power | P3 life/power |
|---:|---|---|---|---|
| 1 | 40 / 0 / 0 / 1 | 40 / 2 | 40 / 0 | 40 / 0 |
| 2 | 40 / 1 / 0 / 2 | 40 / 4 | 40 / 0 | 38 / 0 |
| 3 | 40 / 2 / 0 / 3 | 40 / 6 | 40 / 0 | 34 / 0 |
| 4 | 40 / 4 / 2 / 5 | 40 / 6 | 40 / 0 | 30 / 0 |
| 5 | 38 / 7 / 4 / 6 | 40 / 11 | 34 / 1 | 30 / 1 |
| 6 | 35 / 8 / 5 / 7 | 40 / 13 | 28 / 1 | 30 / 11 |
| 7 | 28 / 9 / 6 / 8 | 26 / 11 | 25 / 11 | 25 / 17 |
| 8 | 14 / 10 / 7 / 8 | 21 / 11 | 22 / 8 | 18 / 27 |
| 9 | -1 / 0 / 0 / 9 | 18 / 10 | 15 / 9 | 15 / 28 |
| 10 | -1 / 0 / 0 / 9 | 8 / 3 | 13 / 12 | 15 / 15 |

## Event-by-event narrative
```text

========== ROUND 1 ==========
  P1 land -> 1 lands.
  P1 (aggro) casts small creature [creature] cost 1, mana left 0.
  P0 plays Mountain (1 lands).
  P3 land -> 1 lands.
  End round: P0 magnus life=40 board=0 sources=1, P1 aggro life=40 board=2 sources=1, P2 tokens life=40 board=0 sources=0, P3 ramp_stompy life=40 board=0 sources=1

========== ROUND 2 ==========
  P1 land -> 2 lands.
  P1 (aggro) casts small creature [creature] cost 2, mana left 0.
    COMBAT P1 aggro:small:2 attacks P3 unblocked for 2.
  P0 plays Island (2 lands).
  P0 (magnus) casts Young Pyromancer creature [named_creature] cost 2, mana left 0.
    Young Pyromancer enters battlefield (2/1).
  P3 land -> 2 lands.
  P3 (ramp_stompy) casts ramp artifact [ramp] cost 2, mana left 0.
  P2 land -> 1 lands.
  End round: P0 magnus life=40 board=2 sources=2, P1 aggro life=40 board=4 sources=2, P2 tokens life=40 board=0 sources=1, P3 ramp_stompy life=38 board=0 sources=3

========== ROUND 3 ==========
  P1 (aggro) casts small creature [creature] cost 2, mana left 0.
    COMBAT P1 aggro:small:2 attacks P3 unblocked for 2.
    COMBAT P1 aggro:small:3 attacks P3 unblocked for 2.
  P0 plays Mountain (3 lands).
  P0 (magnus) casts Third Path Iconoclast creature [named_creature] cost 2, mana left 1.
    Third Path Iconoclast enters battlefield (1/1).
  P3 land -> 3 lands.
  P3 (ramp_stompy) casts ramp artifact [ramp] cost 3, mana left 1.
  End round: P0 magnus life=40 board=3 sources=3, P1 aggro life=40 board=6 sources=2, P2 tokens life=40 board=0 sources=1, P3 ramp_stompy life=34 board=0 sources=5

========== ROUND 4 ==========
    COMBAT P1 aggro:small:3 attacks P3 unblocked for 2.
    COMBAT P1 aggro:small:19 attacks P3 unblocked for 2.
  P0 plays Island (4 lands).
  P0 (magnus) casts Talisman of Creativity artifact [named_rock] cost 2, mana left 2.
    Talisman of Creativity increases available mana next turn.
  P0 (magnus) casts Preordain sorcery [named_selection] cost 1, mana left 1.
    Cast triggers: 2 tokens/treasures/draw effects; token count=2.
    Preordain: partial card selection (1 cards drawn; exact look/scry not modeled).
  P3 land -> 4 lands.
  P3 (ramp_stompy) casts engine enchantment [engine] cost 3, mana left 3.
  P3 (ramp_stompy) casts engine enchantment [engine] cost 3, mana left 0.
  P2 land -> 2 lands.
  P2 (tokens) casts ramp artifact [ramp] cost 2, mana left 0.
  End round: P0 magnus life=40 board=5 sources=5, P1 aggro life=40 board=6 sources=2, P2 tokens life=40 board=0 sources=4, P3 ramp_stompy life=30 board=0 sources=6

========== ROUND 5 ==========
  P1 land -> 3 lands.
  P1 (aggro) casts medium creature [creature] cost 3, mana left 0.
    COMBAT P1 aggro:small:2 attacks P2 unblocked for 2.
    COMBAT P1 aggro:small:3 attacks P0 unblocked for 2.
    COMBAT P1 aggro:small:19 attacks P2 unblocked for 2.
  P0 plays Stormcarved Coast (5 lands).
  P0 (magnus) casts Magnus the Red creature [named_creature] cost 5, mana left 1.
    Magnus the Red enters battlefield (4/5).
  P0 (magnus) casts Telling Time instant [named_selection] cost 1, mana left 0.
    Cast triggers: 2 tokens/treasures/draw effects; token count=4.
    Telling Time: partial card selection (1 cards drawn; exact look/scry not modeled).
    COMBAT P0 Elemental attacks P2 unblocked for 1.
    COMBAT P0 Soldier attacks P2 unblocked for 1.
  P3 land -> 5 lands.
  P3 (ramp_stompy) casts ramp artifact [ramp] cost 2, mana left 5.
  P3 (ramp_stompy) casts engine enchantment [engine] cost 2, mana left 3.
  P3 (ramp_stompy) casts small creature [creature] cost 2, mana left 1.
  P2 (tokens) casts ramp artifact [ramp] cost 2, mana left 2.
  P2 (tokens) casts small creature [creature] cost 2, mana left 0.
  End round: P0 magnus life=38 board=11 sources=6, P1 aggro life=40 board=11 sources=3, P2 tokens life=34 board=1 sources=5, P3 ramp_stompy life=30 board=1 sources=8

========== ROUND 6 ==========
  P1 (aggro) casts medium creature [creature] cost 3, mana left 0.
    COMBAT P1 aggro:small:2 2/1 into P3 ramp_stompy:small:5 1/3.
    COMBAT P1 aggro:small:3 attacks P0 unblocked for 2.
    COMBAT P1 aggro:small:19 attacks P2 unblocked for 2.
  P0 plays Island (6 lands).
    COMBAT P0 Magnus the Red attacks P2 unblocked for 4.
    Blade of Magnus creates a 3/3 Spawn token.
  P3 land -> 6 lands.
  P3 (ramp_stompy) casts large creature [creature] cost 6, mana left 3.
  P3 (ramp_stompy) casts small creature [creature] cost 2, mana left 1.
  P2 (tokens) casts engine enchantment [engine] cost 4, mana left 1.
    COMBAT P2 tokens:small:3 attacks P0 unblocked for 1.
  End round: P0 magnus life=35 board=14 sources=7, P1 aggro life=40 board=13 sources=3, P2 tokens life=28 board=1 sources=5, P3 ramp_stompy life=30 board=11 sources=9

========== ROUND 7 ==========
  P1 (aggro) casts buff sorcery [buff] cost 3, mana left 0.
    COMBAT P1 aggro:small:3 attacks P0 unblocked for 3.
    COMBAT P1 aggro:small:19 attacks P0 unblocked for 3.
    COMBAT P1 aggro:medium:5 6/5 into P3 ramp_stompy:large:5 6/8.
    COMBAT P1 aggro:medium:4 attacks P3 unblocked for 5.
  P0 plays Island (7 lands).
    COMBAT P0 Elemental attacks P2 unblocked for 1.
    COMBAT P0 Soldier attacks P1 unblocked for 1.
    COMBAT P0 Magnus the Red attacks P1 unblocked for 4.
    Blade of Magnus creates a 3/3 Spawn token.
    COMBAT P0 Soldier attacks P2 unblocked for 1.
  P3 land -> 7 lands.
  P3 (ramp_stompy) casts large creature [creature] cost 7, mana left 3.
    COMBAT P3 ramp_stompy:small:5 attacks P0 unblocked for 1.
    COMBAT P3 engine token attacks P1 unblocked for 1.
    COMBAT P3 engine token attacks P2 unblocked for 1.
    COMBAT P3 ramp_stompy:large:5 attacks P1 unblocked for 6.
    COMBAT P3 ramp_stompy:small:3 attacks P1 unblocked for 2.
  P2 land -> 3 lands.
  P2 (tokens) casts tokens sorcery [tokens] cost 3, mana left 3.
  P2 (tokens) casts tokens sorcery [tokens] cost 3, mana left 0.
  End round: P0 magnus life=28 board=17 sources=8, P1 aggro life=26 board=11 sources=3, P2 tokens life=25 board=11 sources=6, P3 ramp_stompy life=25 board=17 sources=10

========== ROUND 8 ==========
  P1 (aggro) casts small creature [creature] cost 1, mana left 2.
  P1 (aggro) casts small creature [creature] cost 1, mana left 1.
    COMBAT P1 aggro:small:3 3/3 into P3 ramp_stompy:large:7 6/7.
    COMBAT P1 aggro:small:19 attacks P2 unblocked for 3.
    COMBAT P1 aggro:medium:4 attacks P3 unblocked for 5.
  P0 misses land drop.
    COMBAT P0 Magnus the Red attacks P1 unblocked for 4.
    Blade of Magnus creates a 3/3 Spawn token.
  P3 (ramp_stompy) casts medium creature [creature] cost 4, mana left 6.
  P3 (ramp_stompy) casts tokens sorcery [tokens] cost 4, mana left 2.
    COMBAT P3 ramp_stompy:small:5 attacks P1 unblocked for 1.
    COMBAT P3 engine token 1/1 into P1 aggro:small:16 2/3.
    COMBAT P3 ramp_stompy:large:5 attacks P0 unblocked for 6.
    COMBAT P3 ramp_stompy:large:7 attacks P0 unblocked for 6.
  P2 land -> 4 lands.
  P2 (tokens) casts tokens sorcery [tokens] cost 5, mana left 2.
  P2 (tokens) casts draw sorcery [draw] cost 2, mana left 0.
    COMBAT P2 tokens:small:3 1/1 into P3 Token 2/2.
    COMBAT P2 Token 1/1 into P3 Token 2/2.
    COMBAT P2 Token 1/1 into P3 Token 2/2.
    COMBAT P2 Token 1/1 into P3 Token 2/2.
    COMBAT P2 Token 1/1 into P3 ramp_stompy:medium:0 5/2.
    COMBAT P2 Token 2/2 into P3 ramp_stompy:small:3 2/1.
    COMBAT P2 Token attacks P0 unblocked for 2.
    COMBAT P2 Token attacks P3 unblocked for 2.
  End round: P0 magnus life=14 board=20 sources=8, P1 aggro life=21 board=11 sources=3, P2 tokens life=22 board=8 sources=7, P3 ramp_stompy life=18 board=27 sources=10

========== ROUND 9 ==========
  P1 (aggro) casts tokens sorcery [tokens] cost 3, mana left 0.
    COMBAT P1 aggro:small:19 attacks P2 unblocked for 3.
    COMBAT P1 aggro:medium:4 5/5 into P3 ramp_stompy:medium:0 5/2.
    COMBAT P1 aggro:small:16 attacks P0 unblocked for 2.
  P0 plays Island (8 lands).
    COMBAT P0 Magnus the Red attacks P2 unblocked for 4.
    Blade of Magnus creates a 3/3 Spawn token.
    COMBAT P0 Spawn attacks P3 unblocked for 3.
  P3 land -> 8 lands.
  P3 (ramp_stompy) casts large creature [creature] cost 6, mana left 5.
  P3 (ramp_stompy) casts removal instant [remove] cost 3, mana left 2.
    Magnus returns to the command zone (commander tax on next cast).
    COMBAT P3 engine token attacks P0 unblocked for 1.
    COMBAT P3 ramp_stompy:large:5 attacks P0 unblocked for 6.
    COMBAT P3 ramp_stompy:large:7 attacks P0 unblocked for 6.
    ELIMINATED P0 (magnus) round 9: combat.
    COMBAT P3 Token 2/2 into P2 Token 2/2.
    COMBAT P3 Token 2/2 into P2 Token 2/2.
  P2 land -> 5 lands.
  P2 (tokens) casts tokens sorcery [tokens] cost 5, mana left 3.
  P2 (tokens) casts buff sorcery [buff] cost 3, mana left 0.
    COMBAT P2 Token 3/2 into P3 ramp_stompy:large:11 8/7.
    COMBAT P2 Token attacks P1 unblocked for 3.
  End round: P1 aggro life=18 board=10 sources=3, P2 tokens life=15 board=9 sources=8, P3 ramp_stompy life=15 board=28 sources=11

========== ROUND 10 ==========
  P1 (aggro) casts small creature [creature] cost 1, mana left 2.
  P1 (aggro) casts removal instant [remove] cost 2, mana left 0.
    COMBAT P1 aggro:small:19 3/3 into P3 ramp_stompy:large:11 8/7.
    COMBAT P1 aggro:small:11 1/1 into P3 ramp_stompy:small:5 1/3.
    COMBAT P1 aggro:small:16 attacks P2 unblocked for 2.
    COMBAT P1 Token 1/1 into P2 Token 2/1.
    COMBAT P1 Token 1/1 into P3 Token 2/2.
    COMBAT P1 Token 1/1 into P3 Token 2/2.
    COMBAT P1 Token 1/1 into P3 engine token 1/1.
  P3 (ramp_stompy) casts small creature [creature] cost 2, mana left 9.
    COMBAT P3 ramp_stompy:small:5 attacks P1 unblocked for 1.
    COMBAT P3 engine token 1/1 into P2 Token 2/1.
    COMBAT P3 ramp_stompy:large:5 attacks P1 unblocked for 6.
    COMBAT P3 Token 2/2 into P2 Token 2/1.
  P2 (tokens) casts tokens sorcery [tokens] cost 5, mana left 3.
  P2 (tokens) casts removal instant [remove] cost 2, mana left 1.
    COMBAT P2 Token attacks P1 unblocked for 3.
  End round: P1 aggro life=8 board=3 sources=3, P2 tokens life=13 board=12 sources=8, P3 ramp_stompy life=15 board=15 sources=11
```

## Important limitations
This is a mixed-deck integration diagnostic, **not** a valid Magnus deck power or win-rate evaluation. Unsupported cards cannot resolve; some selection spells and the opponent stack remain simplified. See `ASSESSMENT.md` for supported interactions and missing mechanics.
