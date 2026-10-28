# v6 narrated game: 03_unforced_magnus
**Seed:** 103  **Seats:** Magnus (real v1.6), control, spellslinger, midrange
**Opening:** random v1.6 opening
**Result:** turn_limit, winner seat None, 10 rounds
## Summary of the Magnus seat
- Life 27; 7 lands; 7 total spells cast; Magnus cast 2 time(s); 2 tokens on battlefield at end.
- Cards cast by coverage: {'supported': 6, 'approx': 1}; remaining unsupported in hand: ['Twincast', 'Capsize', 'Underworld Breach', 'Heralds of Tzeentch', "Jeska's Will"].
- Unsupported distinct nonland card definitions: 38.

## Board-state timeline
| Round | Magnus life / creatures / tokens / mana sources | P1 life/power | P2 life/power | P3 life/power |
|---:|---|---|---|---|
| 1 | 40 / 0 / 0 / 1 | 40 / 0 | 40 / 0 | 40 / 0 |
| 2 | 40 / 0 / 0 / 2 | 40 / 0 | 40 / 0 | 34 / 0 |
| 3 | 40 / 0 / 0 / 3 | 40 / 0 | 40 / 0 | 34 / 0 |
| 4 | 40 / 0 / 0 / 4 | 40 / 0 | 40 / 0 | 34 / 0 |
| 5 | 40 / 1 / 0 / 5 | 40 / 0 | 40 / 2 | 34 / 0 |
| 6 | 40 / 2 / 1 / 6 | 40 / 0 | 40 / 4 | 28 / 3 |
| 7 | 39 / 4 / 2 / 6 | 36 / 0 | 40 / 2 | 24 / 3 |
| 8 | 37 / 5 / 3 / 7 | 33 / 0 | 40 / 11 | 20 / 11 |
| 9 | 32 / 5 / 3 / 7 | 24 / 2 | 31 / 11 | 15 / 11 |
| 10 | 27 / 5 / 2 / 7 | 24 / 2 | 25 / 11 | 4 / 9 |

## Event-by-event narrative
```text

========== ROUND 1 ==========
  P2 land -> 1 lands.
  P3 land -> 1 lands.
  P1 land -> 1 lands.
  P0 plays Island (1 lands).
  End round: P0 magnus life=40 board=0 sources=1, P1 control life=40 board=0 sources=1, P2 spellslinger life=40 board=0 sources=1, P3 midrange life=40 board=0 sources=1

========== ROUND 2 ==========
  P2 land -> 2 lands.
  P2 (spellslinger) casts burn instant [burn] cost 2, mana left 0.
  P1 land -> 2 lands.
  P0 plays Island (2 lands).
  End round: P0 magnus life=40 board=0 sources=2, P1 control life=40 board=0 sources=2, P2 spellslinger life=40 board=0 sources=2, P3 midrange life=34 board=0 sources=1

========== ROUND 3 ==========
  P2 land -> 3 lands.
  P2 (spellslinger) casts ramp artifact [ramp] cost 3, mana left 0.
  P3 land -> 2 lands.
  P3 (midrange) casts ramp artifact [ramp] cost 2, mana left 0.
  P0 plays Mountain (3 lands).
  P0 (magnus) casts Third Path Iconoclast creature [named_creature] cost 2, mana left 1.
    P1 counters Third Path Iconoclast with control:counter:1.
  End round: P0 magnus life=40 board=0 sources=3, P1 control life=40 board=0 sources=2, P2 spellslinger life=40 board=0 sources=4, P3 midrange life=34 board=0 sources=3

========== ROUND 4 ==========
  P2 land -> 4 lands.
  P2 (spellslinger) casts ramp artifact [ramp] cost 3, mana left 2.
  P2 (spellslinger) casts removal instant [remove] cost 2, mana left 0.
    P0 counters spellslinger:removal:0 with Flusterstorm.
  P3 (midrange) casts ramp artifact [ramp] cost 2, mana left 1.
  P0 plays Exotic Orchard (4 lands).
  End round: P0 magnus life=40 board=0 sources=4, P1 control life=40 board=0 sources=2, P2 spellslinger life=40 board=0 sources=6, P3 midrange life=34 board=0 sources=4

========== ROUND 5 ==========
  P2 (spellslinger) casts ramp artifact [ramp] cost 3, mana left 3.
  P2 (spellslinger) casts tokens sorcery [tokens] cost 3, mana left 0.
  P3 (midrange) casts ramp artifact [ramp] cost 2, mana left 2.
  P3 (midrange) casts draw sorcery [draw] cost 2, mana left 0.
  P1 (control) casts removal instant [remove] cost 2, mana left 0.
  P0 plays Riptide Laboratory (5 lands).
  P0 (magnus) casts Magnus the Red creature [named_creature] cost 5, mana left 0.
    Magnus the Red enters battlefield (4/5).
  End round: P0 magnus life=40 board=4 sources=5, P1 control life=40 board=0 sources=2, P2 spellslinger life=40 board=2 sources=7, P3 midrange life=34 board=0 sources=5

========== ROUND 6 ==========
  P2 (spellslinger) casts combo_piece artifact [combo_piece] cost 2, mana left 5.
  P2 (spellslinger) casts tokens sorcery [tokens] cost 3, mana left 2.
    COMBAT P2 Token attacks P3 unblocked for 2.
  P3 land -> 3 lands.
  P3 (midrange) casts ramp artifact [ramp] cost 3, mana left 3.
  P3 (midrange) casts medium creature [creature] cost 3, mana left 0.
  P0 plays Mountain (6 lands).
  P0 (magnus) casts Pongify instant [named_pongify] cost 1, mana left 5.
    Pongify destroys midrange:medium:3; P3 gets a 3/3 Ape.
    COMBAT P0 Magnus the Red attacks P3 unblocked for 4.
    Blade of Magnus creates a 3/3 Spawn token.
  End round: P0 magnus life=40 board=7 sources=6, P1 control life=40 board=0 sources=2, P2 spellslinger life=40 board=4 sources=7, P3 midrange life=28 board=3 sources=7

========== ROUND 7 ==========
  P2 (spellslinger) casts engine enchantment [engine] cost 3, mana left 4.
    COMBAT P2 Token 2/2 into P3 Ape (Pongify) 3/3.
    COMBAT P2 Token attacks P1 unblocked for 1.
    COMBAT P2 Token attacks P0 unblocked for 1.
  P3 land -> 4 lands.
  P3 (midrange) casts draw sorcery [draw] cost 2, mana left 6.
  P3 (midrange) casts removal instant [remove] cost 3, mana left 3.
  P3 (midrange) casts removal instant [remove] cost 3, mana left 0.
  P1 land -> 3 lands.
  P1 (control) casts ramp artifact [ramp] cost 3, mana left 0.
  P0 misses land drop.
  P0 (magnus) casts Archmage Emeritus creature [named_creature] cost 4, mana left 2.
    Archmage Emeritus enters battlefield (2/2).
    COMBAT P0 Magnus the Red attacks P3 unblocked for 4.
    Blade of Magnus creates a 3/3 Spawn token.
    COMBAT P0 Spawn attacks P1 unblocked for 3.
  End round: P0 magnus life=39 board=12 sources=6, P1 control life=36 board=0 sources=4, P2 spellslinger life=40 board=2 sources=7, P3 midrange life=24 board=3 sources=8

========== ROUND 8 ==========
  P2 (spellslinger) casts large creature [creature] cost 7, mana left 0.
  P3 land -> 5 lands.
  P3 (midrange) casts tokens sorcery [tokens] cost 3, mana left 6.
  P3 (midrange) casts tokens sorcery [tokens] cost 4, mana left 2.
  P3 (midrange) casts small creature [creature] cost 1, mana left 1.
  P1 (control) casts engine enchantment [engine] cost 4, mana left 0.
  Steam Vents enters untapped; P0 pays 2 life.
  P0 plays Steam Vents (7 lands).
    COMBAT P0 Magnus the Red attacks P3 unblocked for 4.
    Blade of Magnus creates a 3/3 Spawn token.
    COMBAT P0 Spawn attacks P1 unblocked for 3.
  End round: P0 magnus life=37 board=15 sources=7, P1 control life=33 board=0 sources=4, P2 spellslinger life=40 board=11 sources=7, P3 midrange life=20 board=11 sources=9

========== ROUND 9 ==========
  P2 (spellslinger) casts engine enchantment [engine] cost 3, mana left 4.
    COMBAT P2 spellslinger:engine:6 attacks P3 unblocked for 2.
    COMBAT P2 spellslinger:large:1 attacks P1 unblocked for 9.
  P3 (midrange) casts removal instant [remove] cost 2, mana left 7.
    Magnus returns to the command zone (commander tax on next cast).
    COMBAT P3 Ape (Pongify) attacks P0 unblocked for 3.
    COMBAT P3 Token attacks P2 unblocked for 2.
    COMBAT P3 Token attacks P2 unblocked for 2.
    COMBAT P3 Token attacks P2 unblocked for 1.
    COMBAT P3 Token attacks P2 unblocked for 1.
    COMBAT P3 midrange:small:1 attacks P0 unblocked for 2.
  P1 land -> 4 lands.
  P1 (control) casts engine enchantment [engine] cost 4, mana left 1.
  P0 misses land drop.
  P0 (magnus) casts Magnus the Red creature [named_creature] cost 7, mana left 0.
    Magnus the Red enters battlefield (4/5).
    COMBAT P0 Spawn attacks P2 unblocked for 3.
    COMBAT P0 Spawn attacks P3 unblocked for 3.
  End round: P0 magnus life=32 board=15 sources=7, P1 control life=24 board=2 sources=5, P2 spellslinger life=31 board=11 sources=7, P3 midrange life=15 board=11 sources=9

========== ROUND 10 ==========
  P2 land -> 5 lands.
  P2 (spellslinger) casts removal instant [remove] cost 2, mana left 6.
    P3 counters spellslinger:removal:3 with midrange:counter:0.
    COMBAT P2 spellslinger:engine:6 attacks P3 unblocked for 2.
    COMBAT P2 spellslinger:large:1 attacks P3 unblocked for 9.
  P3 (midrange) casts medium creature [creature] cost 3, mana left 6.
    COMBAT P3 Ape (Pongify) attacks P0 unblocked for 3.
    COMBAT P3 Token 2/2 into P1 control:engine:2 2/3.
    COMBAT P3 Token attacks P2 unblocked for 1.
    COMBAT P3 midrange:small:1 attacks P2 unblocked for 2.
  P1 land -> 5 lands.
  P1 (control) casts engine enchantment [engine] cost 4, mana left 2.
    COMBAT P1 control:engine:2 attacks P0 unblocked for 2.
  P0 misses land drop.
  P0 (magnus) casts Storm-Kiln Artist creature [named_creature] cost 4, mana left 3.
    Storm-Kiln Artist enters battlefield (2/2).
    COMBAT P0 Spawn 3/3 into P3 midrange:medium:8 3/3.
    COMBAT P0 Spawn attacks P2 unblocked for 3.
  End round: P0 magnus life=27 board=14 sources=7, P1 control life=24 board=2 sources=6, P2 spellslinger life=25 board=11 sources=8, P3 midrange life=4 board=9 sources=9
```

## Important limitations
This is a mixed-deck integration diagnostic, **not** a valid Magnus deck power or win-rate evaluation. Unsupported cards cannot resolve; some selection spells and the opponent stack remain simplified. See `ASSESSMENT.md` for supported interactions and missing mechanics.
