# Four-player replay: Mixed Archetypes
**Seed:** 55000 · **Seats:** P0 aggro, P1 control, P2 combo, P3 ramp_stompy
**Result:** P1 wins (combat) in round 16

## Elimination order
- Round 13: P2 (combo) eliminated by persistent_finisher
- Round 16: P3 (ramp_stompy) eliminated by combat
- Round 16: P0 (aggro) eliminated by combat

## Board-state timeline
Life is the actual game resource; public threat is an arbitrary target-selection proxy.
| Round | P0 life / power / mana | P1 life / power / mana | P2 life / power / mana | P3 life / power / mana | Public leader |
|---:|---|---|---|---|---|
| 1 | 40 / 3 / 1 | 40 / 0 / 1 | 40 / 0 / 1 | 40 / 0 / 1 | P0 |
| 2 | 40 / 5 / 2 | 37 / 0 / 4 | 40 / 0 / 3 | 40 / 0 / 2 | P0 |
| 3 | 40 / 4 / 3 | 33 / 0 / 5 | 37 / 0 / 5 | 40 / 0 / 4 | P0 |
| 4 | 40 / 1 / 3 | 29 / 8 / 6 | 37 / 0 / 6 | 40 / 0 / 6 | P1 |
| 5 | 40 / 5 / 4 | 29 / 12 / 7 | 36 / 0 / 6 | 40 / 6 / 7 | P1 |
| 6 | 40 / 2 / 5 | 29 / 6 / 8 | 34 / 1 / 6 | 40 / 6 / 9 | P2 |
| 7 | 40 / 2 / 6 | 29 / 8 / 8 | 30 / 1 / 8 | 38 / 3 / 10 | P1 |
| 8 | 35 / 6 / 6 | 29 / 9 / 10 | 28 / 7 / 9 | 38 / 9 / 10 | P2 |
| 9 | 33 / 1 / 7 | 29 / 14 / 10 | 20 / 15 / 10 | 38 / 3 / 11 | P2 |
| 10 | 27 / 0 / 8 | 29 / 22 / 11 | 15 / 13 / 11 | 35 / 0 / 12 | P2 |
| 11 | 24 / 0 / 9 | 29 / 18 / 13 | 10 / 15 / 13 | 35 / 1 / 12 | P2 |
| 12 | 22 / 0 / 10 | 26 / 20 / 14 | 5 / 13 / 15 | 22 / 1 / 13 | P2 |
| 13 | 15 / 5 / 11 | 26 / 20 / 15 | OUT | 22 / 0 / 13 | P1 |
| 14 | 15 / 0 / 11 | 26 / 18 / 16 | OUT | 3 / 0 / 14 | P1 |
| 15 | 10 / 8 / 11 | 26 / 25 / 17 | OUT | 2 / 0 / 14 | P1 |
| 16 | OUT | 26 / 30 / 18 | OUT | OUT | P1 |

## Detailed action log
This is a simplified Commander model, not a rules-accurate MTG game.

========== ROUND 1 ==========
  P0 land -> 1 lands.
  P0 (aggro) casts small creature [creature] cost 1, mana left 0.
  P3 land -> 1 lands.
  P1 land -> 1 lands.
  P2 land -> 1 lands.
  End round: P0 aggro life=40 power=3 mana=1 threat=8.1, P1 control life=40 power=0 mana=1 threat=5.6, P2 combo life=40 power=0 mana=1 threat=5.6, P3 ramp_stompy life=40 power=0 mana=1 threat=5.6

========== ROUND 2 ==========
  P0 land -> 2 lands.
  P0 (aggro) casts small creature [creature] cost 2, mana left 0.
    COMBAT: P0 attacks P1 unblocked for 3; before=40 life.
  P3 land -> 2 lands.
  P3 (ramp_stompy) casts draw sorcery [draw] cost 2, mana left 0.
  P1 land -> 2 lands.
  P1 (control) casts ramp artifact [ramp] cost 2, mana left 0.
  P2 land -> 2 lands.
  P2 (combo) casts ramp artifact [ramp] cost 2, mana left 0.
  End round: P0 aggro life=40 power=5 mana=2 threat=10.6, P1 control life=37 power=0 mana=4 threat=7.2, P2 combo life=40 power=0 mana=3 threat=6.7, P3 ramp_stompy life=40 power=0 mana=2 threat=6.3

========== ROUND 3 ==========
  P0 land -> 3 lands.
  P0 (aggro) casts buff sorcery [buff] cost 2, mana left 1.
    COMBAT: P0 attacks P1 unblocked for 4; before=37 life.
    COMBAT: P0 attacks P2 unblocked for 3; before=40 life.
  P3 land -> 3 lands.
  P3 (ramp_stompy) casts ramp artifact [ramp] cost 3, mana left 0.
  P1 land -> 3 lands.
  P1 (control) casts draw sorcery [draw] cost 3, mana left 2.
  P1 (control) casts removal instant [remove] cost 2, mana left 0.
  P2 land -> 3 lands.
  P2 (combo) casts ramp artifact [ramp] cost 3, mana left 1.
  End round: P0 aggro life=40 power=4 mana=3 threat=9.7, P1 control life=33 power=0 mana=5 threat=7.6, P2 combo life=37 power=0 mana=5 threat=7.6, P3 ramp_stompy life=40 power=0 mana=4 threat=7.4

========== ROUND 4 ==========
  P0 (aggro) casts small creature [creature] cost 2, mana left 1.
    COMBAT: P0 attacks P1 unblocked for 4; before=33 life.
  P3 land -> 4 lands.
  P3 (ramp_stompy) casts ramp artifact [ramp] cost 3, mana left 2.
  P3 (ramp_stompy) casts removal instant [remove] cost 2, mana left 0.
  P1 land -> 4 lands.
  P1 (control) casts medium creature [creature] cost 3, mana left 3.
  P1 (control) casts tokens sorcery [tokens] cost 3, mana left 0.
  P2 (combo) casts ramp artifact [ramp] cost 3, mana left 2.
  P2 (combo) casts engine enchantment [engine] cost 2, mana left 0.
  End round: P1 control life=29 power=8 mana=6 threat=15.1, P2 combo life=37 power=0 mana=6 threat=10.8, P3 ramp_stompy life=40 power=0 mana=6 threat=8.2, P0 aggro life=40 power=1 mana=3 threat=7.4

========== ROUND 5 ==========
  P0 land -> 4 lands.
  P0 (aggro) casts medium creature [creature] cost 4, mana left 0.
    COMBAT: P0 attacks P2 unblocked for 1; before=37 life.
  P3 land -> 5 lands.
  P3 (ramp_stompy) casts large creature [creature] cost 7, mana left 0.
  P1 land -> 5 lands.
  P1 (control) casts medium creature [creature] cost 4, mana left 3.
  P1 (control) casts small creature [creature] cost 2, mana left 1.
    COMBAT: P1 2/2 attacks P3; P3 blocks with 6/5.
  P2 (combo) casts engine enchantment [engine] cost 3, mana left 3.
  P2 (combo) casts combo_piece artifact [combo_piece] cost 3, mana left 0.
  End round: P1 control life=29 power=12 mana=7 threat=18.7, P2 combo life=36 power=0 mana=6 threat=15.2, P3 ramp_stompy life=40 power=6 mana=7 threat=13.7, P0 aggro life=40 power=5 mana=4 threat=11.3

========== ROUND 6 ==========
  P0 land -> 5 lands.
  P0 (aggro) casts draw sorcery [draw] cost 2, mana left 3.
  P0 (aggro) casts buff sorcery [buff] cost 3, mana left 0.
    COMBAT: P0 attacks P2 unblocked for 2; before=36 life.
    COMBAT: P0 5/2 attacks P1; P1 blocks with 2/2.
  P3 land -> 6 lands.
  P3 (ramp_stompy) casts ramp artifact [ramp] cost 2, mana left 6.
  P3 (ramp_stompy) casts removal instant [remove] cost 3, mana left 3.
  P1 land -> 6 lands.
  P2 (combo) casts engine enchantment [engine] cost 2, mana left 4.
    P1 counters combo:engine:0 (cost 2).
  P2 (combo) casts draw sorcery [draw] cost 2, mana left 2.
  End round: P2 combo life=34 power=1 mana=6 threat=17.0, P3 ramp_stompy life=40 power=6 mana=9 threat=14.5, P1 control life=29 power=6 mana=8 threat=13.5, P0 aggro life=40 power=2 mana=5 threat=9.2

========== ROUND 7 ==========
  P0 land -> 6 lands.
  P0 (aggro) casts tokens sorcery [tokens] cost 4, mana left 2.
    P2 counters aggro:tokens:0 (cost 2).
  P0 (aggro) casts removal instant [remove] cost 2, mana left 0.
    COMBAT: P0 attacks P3 unblocked for 2; before=40 life.
  P3 land -> 7 lands.
  P3 (ramp_stompy) casts medium creature [creature] cost 3, mana left 7.
  P1 (control) casts engine enchantment [engine] cost 2, mana left 6.
  P1 (control) casts finisher sorcery [finisher] cost 5, mana left 1.
    P1 establishes persistent 5-damage/turn finisher.
    COMBAT: P1 attacks P2 unblocked for 4; before=34 life.
  P2 land -> 4 lands.
  P2 (combo) casts draw sorcery [draw] cost 2, mana left 5.
  P2 (combo) casts ramp artifact [ramp] cost 2, mana left 3.
  P2 (combo) casts draw sorcery [draw] cost 3, mana left 0.
  End round: P1 control life=29 power=8 mana=8 threat=21.1, P2 combo life=30 power=1 mana=8 threat=18.7, P3 ramp_stompy life=38 power=3 mana=10 threat=12.5, P0 aggro life=40 power=2 mana=6 threat=9.3

========== ROUND 8 ==========
  P0 (aggro) casts tokens sorcery [tokens] cost 5, mana left 1.
    COMBAT: P0 attacks P2 unblocked for 2; before=30 life.
  P3 (ramp_stompy) casts large creature [creature] cost 6, mana left 4.
  P1 land -> 7 lands.
  P1 (control) casts ramp artifact [ramp] cost 3, mana left 6.
  P2 land -> 5 lands.
  P2 (combo) casts engine enchantment [engine] cost 3, mana left 6.
  P2 (combo) casts combo_piece artifact [combo_piece] cost 4, mana left 2.
  P2 (combo) casts small creature [creature] cost 2, mana left 0.
  End round: P2 combo life=28 power=7 mana=9 threat=29.3, P1 control life=29 power=9 mana=10 threat=23.8, P3 ramp_stompy life=38 power=9 mana=10 threat=17.5, P0 aggro life=35 power=6 mana=6 threat=14.2

========== ROUND 9 ==========
  P0 land -> 7 lands.
  P0 (aggro) casts removal instant [remove] cost 2, mana left 5.
    COMBAT: P0 2/3 attacks P2; P2 blocks with 3/3.
    COMBAT: P0 1/1 attacks P2; P2 blocks with 2/3.
    COMBAT: P0 1/1 attacks P3; P3 blocks with 3/5.
    COMBAT: P0 1/1 attacks P2; P2 blocks with 1/1.
  P3 land -> 8 lands.
    COMBAT: P3 attacks P2 unblocked for 3; before=28 life.
  P1 (control) casts draw sorcery [draw] cost 2, mana left 8.
  P1 (control) casts draw sorcery [draw] cost 3, mana left 5.
  P1 (control) casts medium creature [creature] cost 4, mana left 1.
    COMBAT: P1 attacks P0 unblocked for 2; before=35 life.
  P2 land -> 6 lands.
  P2 (combo) casts medium creature [creature] cost 3, mana left 7.
  P2 (combo) casts tokens sorcery [tokens] cost 3, mana left 4.
  End round: P2 combo life=20 power=15 mana=10 threat=37.9, P1 control life=29 power=14 mana=10 threat=29.6, P3 ramp_stompy life=38 power=3 mana=11 threat=13.2, P0 aggro life=33 power=1 mana=7 threat=8.5

========== ROUND 10 ==========
  P0 land -> 8 lands.
    COMBAT: P0 1/1 attacks P2; P2 blocks with 2/3.
  P3 (ramp_stompy) casts ramp artifact [ramp] cost 3, mana left 8.
    COMBAT: P3 3/5 attacks P1; P1 blocks with 5/4.
  P1 land -> 8 lands.
  P1 (control) casts engine enchantment [engine] cost 3, mana left 8.
  P1 (control) casts large creature [creature] cost 7, mana left 1.
    COMBAT: P1 attacks P3 unblocked for 1; before=38 life.
    COMBAT: P1 attacks P0 unblocked for 5; before=33 life.
  P2 land -> 7 lands.
  P2 (combo) casts draw sorcery [draw] cost 2, mana left 9.
  P2 (combo) casts engine enchantment [engine] cost 3, mana left 6.
  P2 (combo) casts draw sorcery [draw] cost 2, mana left 4.
  P2 (combo) casts draw sorcery [draw] cost 3, mana left 1.
    COMBAT: P2 attacks P3 unblocked for 1; before=37 life.
    COMBAT: P2 3/3 attacks P1; P1 blocks with 4/4.
    COMBAT: P2 attacks P0 unblocked for 1; before=28 life.
    COMBAT: P2 1/1 attacks P1; P1 blocks with 2/3.
    COMBAT: P2 attacks P3 unblocked for 1; before=36 life.
  End round: P2 combo life=15 power=13 mana=11 threat=40.2, P1 control life=29 power=22 mana=11 threat=39.9, P3 ramp_stompy life=35 power=0 mana=12 threat=10.8, P0 aggro life=27 power=0 mana=8 threat=7.5

========== ROUND 11 ==========
  P0 land -> 9 lands.
  P3 (ramp_stompy) casts small creature [creature] cost 1, mana left 11.
  P1 land -> 9 lands.
  P1 (control) casts ramp artifact [ramp] cost 2, mana left 10.
    COMBAT: P1 attacks P0 unblocked for 2; before=27 life.
    COMBAT: P1 1/1 attacks P3; P3 blocks with 1/2.
    COMBAT: P1 attacks P0 unblocked for 1; before=25 life.
  P2 land -> 8 lands.
  P2 (combo) casts engine enchantment [engine] cost 3, mana left 9.
    P1 counters combo:engine:3 (cost 2).
  P2 (combo) casts medium creature [creature] cost 3, mana left 6.
    P1 counters combo:medium:1 (cost 2).
  P2 (combo) casts removal instant [remove] cost 3, mana left 3.
  P2 (combo) casts ramp artifact [ramp] cost 3, mana left 0.
  End round: P2 combo life=10 power=15 mana=13 threat=43.2, P1 control life=29 power=18 mana=13 threat=37.1, P3 ramp_stompy life=35 power=1 mana=12 threat=12.1, P0 aggro life=24 power=0 mana=9 threat=8.0

========== ROUND 12 ==========
  P0 (aggro) casts draw sorcery [draw] cost 3, mana left 6.
  P0 (aggro) casts removal instant [remove] cost 3, mana left 3.
  P0 (aggro) casts ramp artifact [ramp] cost 3, mana left 0.
  P3 (ramp_stompy) casts ramp artifact [ramp] cost 3, mana left 9.
    COMBAT: P3 attacks P0 unblocked for 1; before=24 life.
  P1 land -> 10 lands.
  P1 (control) casts medium creature [creature] cost 4, mana left 10.
    COMBAT: P1 2/3 attacks P2; P2 blocks with 2/3.
    COMBAT: P1 2/3 attacks P2; P2 blocks with 2/3.
    COMBAT: P1 attacks P3 unblocked for 5; before=35 life.
    COMBAT: P1 attacks P3 unblocked for 7; before=30 life.
    COMBAT: P1 attacks P3 unblocked for 1; before=23 life.
  P2 land -> 9 lands.
  P2 (combo) casts ramp artifact [ramp] cost 3, mana left 11.
    COMBAT: P2 1/1 attacks P1; P1 blocks with 3/3.
    COMBAT: P2 attacks P1 unblocked for 2; before=29 life.
    COMBAT: P2 attacks P0 unblocked for 1; before=23 life.
    COMBAT: P2 1/1 attacks P1; P1 blocks with 1/1.
    COMBAT: P2 attacks P1 unblocked for 1; before=27 life.
  End round: P2 combo life=5 power=13 mana=15 threat=43.4, P1 control life=26 power=20 mana=14 threat=39.1, P3 ramp_stompy life=22 power=1 mana=13 threat=11.9, P0 aggro life=22 power=0 mana=10 threat=8.8

========== ROUND 13 ==========
  P0 land -> 10 lands.
  P0 (aggro) casts medium creature [creature] cost 3, mana left 8.
  P3 land -> 9 lands.
    COMBAT: P3 1/2 attacks P0; P0 blocks with 5/5.
    ELIMINATED P2 (combo) round 13: persistent_finisher.
  P1 land -> 11 lands.
  P1 (control) casts removal instant [remove] cost 2, mana left 13.
    COMBAT: P1 attacks P0 unblocked for 7; before=22 life.
  End round: P1 control life=26 power=20 mana=15 threat=40.1, P0 aggro life=15 power=5 mana=11 threat=13.1, P3 ramp_stompy life=22 power=0 mana=13 threat=10.6

========== ROUND 14 ==========
  P0 (aggro) casts small creature [creature] cost 1, mana left 10.
    COMBAT: P0 attacks P3 unblocked for 5; before=22 life.
  P3 (ramp_stompy) casts ramp artifact [ramp] cost 3, mana left 10.
  P1 land -> 12 lands.
  P1 (control) casts removal instant [remove] cost 2, mana left 14.
    COMBAT: P1 attacks P3 unblocked for 2; before=12 life.
    COMBAT: P1 attacks P3 unblocked for 7; before=10 life.
    COMBAT: P1 3/3 attacks P0; P0 blocks with 3/1.
  End round: P1 control life=26 power=18 mana=16 threat=39.3, P3 ramp_stompy life=3 power=0 mana=14 threat=10.0, P0 aggro life=15 power=0 mana=11 threat=8.8

========== ROUND 15 ==========
  P0 (aggro) casts tokens sorcery [tokens] cost 5, mana left 6.
  P3 (ramp_stompy) casts tokens sorcery [tokens] cost 4, mana left 10.
    P1 counters ramp_stompy:tokens:1 (cost 2).
  P1 land -> 13 lands.
  P1 (control) casts draw sorcery [draw] cost 2, mana left 15.
  P1 (control) casts large creature [creature] cost 6, mana left 9.
    COMBAT: P1 attacks P3 unblocked for 1; before=3 life.
    COMBAT: P1 1/1 attacks P0; P0 blocks with 2/2.
  End round: P1 control life=26 power=25 mana=17 threat=45.8, P0 aggro life=10 power=8 mana=11 threat=16.6, P3 ramp_stompy life=2 power=0 mana=14 threat=9.9

========== ROUND 16 ==========
  P0 (aggro) casts small creature [creature] cost 1, mana left 10.
    COMBAT: P0 attacks P3 unblocked for 2; before=2 life.
    ELIMINATED P3 (ramp_stompy) round 16: combat.
    COMBAT: P0 2/2 attacks P1; P1 blocks with 2/3.
    COMBAT: P0 2/2 attacks P1; P1 blocks with 2/3.
    COMBAT: P0 2/2 attacks P1; P1 blocks with 5/4.
  P1 land -> 14 lands.
  P1 (control) casts draw sorcery [draw] cost 2, mana left 16.
  P1 (control) casts medium creature [creature] cost 4, mana left 12.
    COMBAT: P1 attacks P0 unblocked for 7; before=5 life.
    ELIMINATED P0 (aggro) round 16: combat.
  End round: P1 control life=26 power=30 mana=18 threat=51.1
