# Four-player replay: Aggro Aggro Control Combo
**Seed:** 55000 · **Seats:** P0 aggro, P1 aggro, P2 control, P3 combo
**Result:** P2 wins (combat) in round 17

## Elimination order
- Round 9: P3 (combo) eliminated by burn
- Round 17: P1 (aggro) eliminated by combat
- Round 17: P0 (aggro) eliminated by combat

## Board-state timeline
Life is the actual game resource; public threat is an arbitrary target-selection proxy.
| Round | P0 life / power / mana | P1 life / power / mana | P2 life / power / mana | P3 life / power / mana | Public leader |
|---:|---|---|---|---|---|
| 1 | 40 / 3 / 1 | 40 / 0 / 1 | 40 / 0 / 1 | 40 / 0 / 1 | P0 |
| 2 | 40 / 5 / 2 | 37 / 1 / 2 | 40 / 0 / 3 | 40 / 0 / 4 | P0 |
| 3 | 39 / 7 / 3 | 33 / 4 / 3 | 40 / 0 / 5 | 37 / 0 / 4 | P0 |
| 4 | 38 / 8 / 3 | 33 / 4 / 5 | 40 / 2 / 6 | 30 / 0 / 4 | P0 |
| 5 | 38 / 12 / 4 | 33 / 4 / 6 | 39 / 5 / 7 | 22 / 1 / 6 | P2 |
| 6 | 38 / 11 / 5 | 29 / 2 / 8 | 39 / 7 / 8 | 16 / 3 / 6 | P2 |
| 7 | 38 / 6 / 6 | 25 / 5 / 9 | 39 / 8 / 9 | 13 / 4 / 7 | P3 |
| 8 | 38 / 5 / 6 | 25 / 5 / 10 | 39 / 12 / 10 | 7 / 2 / 9 | P2 |
| 9 | 36 / 3 / 7 | 19 / 2 / 11 | 39 / 12 / 10 | OUT | P2 |
| 10 | 36 / 3 / 8 | 17 / 3 / 12 | 39 / 12 / 11 | OUT | P2 |
| 11 | 27 / 0 / 9 | 17 / 7 / 13 | 39 / 13 / 12 | OUT | P2 |
| 12 | 24 / 0 / 10 | 17 / 8 / 13 | 36 / 6 / 12 | OUT | P1 |
| 13 | 20 / 5 / 11 | 11 / 4 / 14 | 36 / 6 / 12 | OUT | P2 |
| 14 | 18 / 3 / 11 | 6 / 6 / 14 | 34 / 7 / 13 | OUT | P1 |
| 15 | 12 / 8 / 11 | 6 / 3 / 15 | 32 / 6 / 14 | OUT | P2 |
| 16 | 6 / 10 / 11 | 4 / 2 / 16 | 24 / 11 / 14 | OUT | P2 |
| 17 | OUT | OUT | 20 / 12 / 15 | OUT | P2 |

## Detailed action log
This is a simplified Commander model, not a rules-accurate MTG game.

========== ROUND 1 ==========
  P0 land -> 1 lands.
  P0 (aggro) casts small creature [creature] cost 1, mana left 0.
  P3 land -> 1 lands.
  P1 land -> 1 lands.
  P2 land -> 1 lands.
  End round: P0 aggro life=40 power=3 mana=1 threat=8.1, P1 aggro life=40 power=0 mana=1 threat=5.6, P2 control life=40 power=0 mana=1 threat=5.6, P3 combo life=40 power=0 mana=1 threat=5.6

========== ROUND 2 ==========
  P0 land -> 2 lands.
  P0 (aggro) casts small creature [creature] cost 2, mana left 0.
    COMBAT: P0 attacks P1 unblocked for 3; before=40 life.
  P3 land -> 2 lands.
  P3 (combo) casts ramp artifact [ramp] cost 2, mana left 0.
  P1 land -> 2 lands.
  P1 (aggro) casts small creature [creature] cost 2, mana left 0.
  P2 land -> 2 lands.
  P2 (control) casts ramp artifact [ramp] cost 2, mana left 0.
  End round: P0 aggro life=40 power=5 mana=2 threat=10.6, P3 combo life=40 power=0 mana=4 threat=7.4, P1 aggro life=37 power=1 mana=2 threat=7.1, P2 control life=40 power=0 mana=3 threat=6.7

========== ROUND 3 ==========
  P0 land -> 3 lands.
  P0 (aggro) casts buff sorcery [buff] cost 2, mana left 1.
    COMBAT: P0 attacks P1 unblocked for 4; before=37 life.
    COMBAT: P0 attacks P3 unblocked for 3; before=40 life.
  P3 (combo) casts engine enchantment [engine] cost 3, mana left 1.
  P1 land -> 3 lands.
  P1 (aggro) casts small creature [creature] cost 2, mana left 1.
    COMBAT: P1 attacks P0 unblocked for 1; before=40 life.
  P2 land -> 3 lands.
  P2 (control) casts ramp artifact [ramp] cost 3, mana left 1.
  End round: P0 aggro life=39 power=7 mana=3 threat=12.4, P1 aggro life=33 power=4 mana=3 threat=10.0, P3 combo life=37 power=0 mana=4 threat=10.0, P2 control life=40 power=0 mana=5 threat=7.8

========== ROUND 4 ==========
  P0 (aggro) casts small creature [creature] cost 2, mana left 1.
    COMBAT: P0 attacks P3 unblocked for 4; before=37 life.
    COMBAT: P0 attacks P3 unblocked for 3; before=33 life.
  P3 (combo) casts engine enchantment [engine] cost 2, mana left 2.
  P3 (combo) casts draw sorcery [draw] cost 2, mana left 0.
  P1 land -> 4 lands.
  P1 (aggro) casts ramp artifact [ramp] cost 2, mana left 2.
  P1 (aggro) casts draw sorcery [draw] cost 2, mana left 0.
    COMBAT: P1 attacks P0 unblocked for 1; before=39 life.
  P2 land -> 4 lands.
  P2 (control) casts engine enchantment [engine] cost 2, mana left 4.
  P2 (control) casts draw sorcery [draw] cost 2, mana left 2.
  End round: P0 aggro life=38 power=8 mana=3 threat=13.6, P2 control life=40 power=2 mana=6 threat=13.3, P3 combo life=30 power=0 mana=4 threat=12.6, P1 aggro life=33 power=4 mana=5 threat=11.4

========== ROUND 5 ==========
  P0 land -> 4 lands.
  P0 (aggro) casts medium creature [creature] cost 4, mana left 0.
    COMBAT: P0 attacks P3 unblocked for 4; before=30 life.
    COMBAT: P0 attacks P3 unblocked for 3; before=26 life.
    COMBAT: P0 attacks P2 unblocked for 1; before=40 life.
  P3 land -> 3 lands.
  P3 (combo) casts ramp artifact [ramp] cost 3, mana left 2.
  P3 (combo) casts engine enchantment [engine] cost 2, mana left 0.
  P1 land -> 5 lands.
  P1 (aggro) casts tokens sorcery [tokens] cost 5, mana left 1.
    COMBAT: P1 attacks P3 unblocked for 1; before=23 life.
    COMBAT: P1 3/2 attacks P3; P3 blocks with 2/3.
  P2 land -> 5 lands.
  P2 (control) casts engine enchantment [engine] cost 2, mana left 5.
  P2 (control) casts medium creature [creature] cost 3, mana left 2.
  End round: P2 control life=39 power=5 mana=7 threat=19.0, P0 aggro life=38 power=12 mana=4 threat=17.6, P3 combo life=22 power=1 mana=6 threat=14.1, P1 aggro life=33 power=4 mana=6 threat=12.9

========== ROUND 6 ==========
  P0 land -> 5 lands.
  P0 (aggro) casts draw sorcery [draw] cost 2, mana left 3.
  P0 (aggro) casts buff sorcery [buff] cost 3, mana left 0.
    COMBAT: P0 5/2 attacks P2; P2 blocks with 2/3.
    COMBAT: P0 attacks P1 unblocked for 4; before=33 life.
    COMBAT: P0 attacks P3 unblocked for 2; before=22 life.
  P3 (combo) casts engine enchantment [engine] cost 4, mana left 2.
  P3 (combo) casts draw sorcery [draw] cost 2, mana left 0.
    COMBAT: P3 1/1 attacks P2; P2 blocks with 3/3.
  P1 land -> 6 lands.
  P1 (aggro) casts ramp artifact [ramp] cost 3, mana left 4.
  P1 (aggro) casts draw sorcery [draw] cost 3, mana left 1.
    COMBAT: P1 attacks P3 unblocked for 1; before=20 life.
    COMBAT: P1 1/1 attacks P2; P2 blocks with 3/3.
    COMBAT: P1 1/1 attacks P3; P3 blocks with 2/3.
  P2 (control) casts draw sorcery [draw] cost 3, mana left 4.
  P2 (control) casts ramp artifact [ramp] cost 2, mana left 2.
  P2 (control) casts small creature [creature] cost 2, mana left 0.
    COMBAT: P2 attacks P3 unblocked for 3; before=19 life.
  End round: P2 control life=39 power=7 mana=8 threat=19.5, P3 combo life=16 power=3 mana=6 threat=19.2, P0 aggro life=38 power=11 mana=5 threat=17.0, P1 aggro life=29 power=2 mana=8 threat=11.4

========== ROUND 7 ==========
  P0 land -> 6 lands.
  P0 (aggro) casts tokens sorcery [tokens] cost 4, mana left 2.
  P0 (aggro) casts removal instant [remove] cost 2, mana left 0.
    COMBAT: P0 attacks P1 unblocked for 4; before=29 life.
    COMBAT: P0 attacks P3 unblocked for 2; before=16 life.
    COMBAT: P0 5/2 attacks P2; P2 blocks with 3/3.
  P3 (combo) casts ramp artifact [ramp] cost 2, mana left 4.
  P3 (combo) casts draw sorcery [draw] cost 2, mana left 2.
  P3 (combo) casts draw sorcery [draw] cost 2, mana left 0.
  P1 land -> 7 lands.
  P1 (aggro) casts medium creature [creature] cost 4, mana left 5.
  P1 (aggro) casts engine enchantment [engine] cost 2, mana left 3.
    COMBAT: P1 attacks P3 unblocked for 1; before=14 life.
    COMBAT: P1 1/1 attacks P3; P3 blocks with 2/3.
  P2 land -> 6 lands.
  P2 (control) casts removal instant [remove] cost 3, mana left 6.
  P2 (control) casts large creature [creature] cost 6, mana left 0.
  End round: P3 combo life=13 power=4 mana=7 threat=21.0, P2 control life=39 power=8 mana=9 threat=20.4, P1 aggro life=25 power=5 mana=9 threat=16.3, P0 aggro life=38 power=6 mana=6 threat=13.3

========== ROUND 8 ==========
  P0 (aggro) casts tokens sorcery [tokens] cost 5, mana left 1.
    COMBAT: P0 attacks P3 unblocked for 2; before=13 life.
    COMBAT: P0 2/2 attacks P3; P3 blocks with 2/3.
    COMBAT: P0 2/2 attacks P2; P2 blocks with 6/9.
  P3 land -> 4 lands.
  P3 (combo) casts ramp artifact [ramp] cost 3, mana left 5.
  P3 (combo) casts draw sorcery [draw] cost 3, mana left 2.
  P3 (combo) casts removal instant [remove] cost 2, mana left 0.
    COMBAT: P3 1/1 attacks P0; P0 blocks with 1/1.
  P1 land -> 8 lands.
    COMBAT: P1 attacks P3 unblocked for 4; before=11 life.
  P2 land -> 7 lands.
  P2 (control) casts large creature [creature] cost 6, mana left 4.
    COMBAT: P2 1/1 attacks P3; P3 blocks with 2/3.
    COMBAT: P2 1/1 attacks P3; P3 blocks with 1/1.
  End round: P2 control life=39 power=12 mana=10 threat=20.4, P3 combo life=7 power=2 mana=9 threat=19.3, P1 aggro life=25 power=5 mana=10 threat=17.0, P0 aggro life=38 power=5 mana=6 threat=13.1

========== ROUND 9 ==========
  P0 land -> 7 lands.
  P0 (aggro) casts removal instant [remove] cost 2, mana left 5.
    P2 counters aggro:removal:2 (cost 2).
    COMBAT: P0 2/3 attacks P3; P3 blocks with 2/3.
    COMBAT: P0 attacks P3 unblocked for 1; before=7 life.
    COMBAT: P0 1/1 attacks P1; P1 blocks with 1/3.
    COMBAT: P0 1/1 attacks P2; P2 blocks with 6/9.
  P3 land -> 5 lands.
  P3 (combo) casts draw sorcery [draw] cost 3, mana left 7.
  P3 (combo) casts draw sorcery [draw] cost 3, mana left 4.
    P2 counters combo:draw:1 (cost 2).
  P3 (combo) casts combo_piece artifact [combo_piece] cost 3, mana left 1.
  P1 land -> 9 lands.
  P1 (aggro) casts buff sorcery [buff] cost 3, mana left 8.
  P1 (aggro) casts burn instant [burn] cost 3, mana left 5.
    ELIMINATED P3 (combo) round 9: burn.
    COMBAT: P1 attacks P0 unblocked for 2; before=38 life.
    COMBAT: P1 5/5 attacks P2; P2 blocks with 6/9.
  P2 (control) casts engine enchantment [engine] cost 2, mana left 8.
    COMBAT: P2 attacks P1 unblocked for 6; before=25 life.
  End round: P2 control life=39 power=12 mana=10 threat=22.6, P1 aggro life=19 power=2 mana=11 threat=14.2, P0 aggro life=36 power=3 mana=7 threat=10.8

========== ROUND 10 ==========
  P0 land -> 8 lands.
    COMBAT: P0 attacks P1 unblocked for 2; before=19 life.
  P1 land -> 10 lands.
  P1 (aggro) casts small creature [creature] cost 1, mana left 11.
    COMBAT: P1 2/3 attacks P2; P2 blocks with 6/9.
  P2 land -> 8 lands.
  End round: P2 control life=39 power=12 mana=11 threat=23.3, P1 aggro life=17 power=3 mana=12 threat=15.5, P0 aggro life=36 power=3 mana=8 threat=11.5

========== ROUND 11 ==========
  P0 land -> 9 lands.
    COMBAT: P0 2/3 attacks P2; P2 blocks with 6/9.
    COMBAT: P0 1/1 attacks P2; P2 blocks with 6/7.
  P1 land -> 11 lands.
  P1 (aggro) casts medium creature [creature] cost 4, mana left 9.
    COMBAT: P1 attacks P0 unblocked for 3; before=36 life.
  P2 land -> 9 lands.
    COMBAT: P2 attacks P0 unblocked for 6; before=33 life.
  End round: P2 control life=39 power=13 mana=12 threat=25.6, P1 aggro life=17 power=7 mana=13 threat=20.0, P0 aggro life=27 power=0 mana=9 threat=8.2

========== ROUND 12 ==========
  P0 (aggro) casts draw sorcery [draw] cost 3, mana left 6.
  P0 (aggro) casts removal instant [remove] cost 3, mana left 3.
  P0 (aggro) casts ramp artifact [ramp] cost 3, mana left 0.
  P1 (aggro) casts small creature [creature] cost 2, mana left 11.
  P1 (aggro) casts tokens sorcery [tokens] cost 5, mana left 6.
    COMBAT: P1 attacks P0 unblocked for 3; before=27 life.
    COMBAT: P1 1/1 attacks P2; P2 blocks with 6/7.
    COMBAT: P1 attacks P2 unblocked for 3; before=39 life.
  P2 (control) casts removal instant [remove] cost 3, mana left 9.
    COMBAT: P2 1/1 attacks P1; P1 blocks with 1/2.
  End round: P1 aggro life=17 power=8 mana=13 threat=22.4, P2 control life=36 power=6 mana=12 threat=19.1, P0 aggro life=24 power=0 mana=10 threat=9.0

========== ROUND 13 ==========
  P0 land -> 10 lands.
  P0 (aggro) casts medium creature [creature] cost 3, mana left 8.
  P1 land -> 12 lands.
  P1 (aggro) casts small creature [creature] cost 1, mana left 13.
    COMBAT: P1 3/4 attacks P0; P0 blocks with 5/5.
    COMBAT: P1 attacks P0 unblocked for 1; before=24 life.
    COMBAT: P1 attacks P0 unblocked for 1; before=23 life.
    COMBAT: P1 attacks P0 unblocked for 1; before=22 life.
    COMBAT: P1 attacks P0 unblocked for 1; before=21 life.
    COMBAT: P1 1/1 attacks P2; P2 blocks with 6/7.
  P2 (control) casts removal instant [remove] cost 3, mana left 9.
    COMBAT: P2 attacks P1 unblocked for 6; before=17 life.
  End round: P2 control life=36 power=6 mana=12 threat=19.1, P1 aggro life=11 power=4 mana=14 threat=18.6, P0 aggro life=20 power=5 mana=11 threat=13.4

========== ROUND 14 ==========
  P0 (aggro) casts small creature [creature] cost 1, mana left 10.
    COMBAT: P0 attacks P1 unblocked for 5; before=11 life.
  P1 (aggro) casts engine enchantment [engine] cost 2, mana left 12.
    COMBAT: P1 attacks P2 unblocked for 1; before=36 life.
    COMBAT: P1 attacks P2 unblocked for 1; before=35 life.
    COMBAT: P1 attacks P0 unblocked for 1; before=20 life.
    COMBAT: P1 attacks P0 unblocked for 1; before=19 life.
  P2 land -> 10 lands.
  P2 (control) casts removal instant [remove] cost 2, mana left 11.
  End round: P1 aggro life=6 power=6 mana=14 threat=23.1, P2 control life=34 power=7 mana=13 threat=20.9, P0 aggro life=18 power=3 mana=11 threat=11.8

========== ROUND 15 ==========
  P0 (aggro) casts tokens sorcery [tokens] cost 5, mana left 6.
    COMBAT: P0 3/1 attacks P1; P1 blocks with 2/3.
  P1 land -> 13 lands.
    COMBAT: P1 1/1 attacks P2; P2 blocks with 6/7.
    COMBAT: P1 attacks P2 unblocked for 1; before=34 life.
    COMBAT: P1 1/1 attacks P2; P2 blocks with 1/1.
    COMBAT: P1 attacks P2 unblocked for 1; before=33 life.
  P2 land -> 11 lands.
  P2 (control) casts engine enchantment [engine] cost 4, mana left 10.
    COMBAT: P2 attacks P0 unblocked for 6; before=18 life.
  End round: P2 control life=32 power=6 mana=14 threat=23.0, P1 aggro life=6 power=3 mana=15 threat=17.9, P0 aggro life=12 power=8 mana=11 threat=16.7

========== ROUND 16 ==========
  P0 (aggro) casts small creature [creature] cost 1, mana left 10.
    COMBAT: P0 attacks P2 unblocked for 2; before=32 life.
    COMBAT: P0 attacks P1 unblocked for 2; before=6 life.
    COMBAT: P0 attacks P2 unblocked for 2; before=30 life.
    COMBAT: P0 attacks P2 unblocked for 2; before=28 life.
  P1 land -> 14 lands.
    COMBAT: P1 attacks P2 unblocked for 1; before=26 life.
    COMBAT: P1 1/1 attacks P0; P0 blocks with 2/3.
    COMBAT: P1 attacks P2 unblocked for 1; before=25 life.
  P2 (control) casts engine enchantment [engine] cost 4, mana left 10.
  P2 (control) casts medium creature [creature] cost 3, mana left 7.
    COMBAT: P2 attacks P0 unblocked for 6; before=12 life.
  End round: P2 control life=24 power=11 mana=14 threat=29.5, P0 aggro life=6 power=10 mana=11 threat=18.4, P1 aggro life=4 power=2 mana=16 threat=17.2

========== ROUND 17 ==========
  P0 (aggro) casts medium creature [creature] cost 4, mana left 7.
    COMBAT: P0 attacks P1 unblocked for 2; before=4 life.
    COMBAT: P0 2/2 attacks P2; P2 blocks with 5/4.
    COMBAT: P0 attacks P2 unblocked for 2; before=24 life.
    COMBAT: P0 attacks P1 unblocked for 2; before=2 life.
    ELIMINATED P1 (aggro) round 17: combat.
    COMBAT: P0 attacks P2 unblocked for 2; before=22 life.
  P2 (control) casts draw sorcery [draw] cost 2, mana left 12.
  P2 (control) casts engine enchantment [engine] cost 3, mana left 9.
  P2 (control) casts ramp artifact [ramp] cost 3, mana left 6.
    COMBAT: P2 attacks P0 unblocked for 6; before=6 life.
    ELIMINATED P0 (aggro) round 17: combat.
  End round: P2 control life=20 power=12 mana=15 threat=34.4
