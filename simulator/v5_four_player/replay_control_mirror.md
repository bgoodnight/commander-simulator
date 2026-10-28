# Four-player replay: Control Mirror
**Seed:** 55000 · **Seats:** P0 control, P1 control, P2 control, P3 control
**Result:** Unresolved at round 30 (turn_limit)

## Elimination order
- Round 23: P3 (control) eliminated by persistent_finisher
- Round 29: P2 (control) eliminated by persistent_finisher

## Board-state timeline
Life is the actual game resource; public threat is an arbitrary target-selection proxy.
| Round | P0 life / power / mana | P1 life / power / mana | P2 life / power / mana | P3 life / power / mana | Public leader |
|---:|---|---|---|---|---|
| 1 | 40 / 0 / 1 | 40 / 0 / 1 | 40 / 0 / 1 | 40 / 0 / 1 | P0 |
| 2 | 40 / 0 / 3 | 40 / 0 / 4 | 40 / 0 / 3 | 40 / 0 / 4 | P1 |
| 3 | 40 / 0 / 5 | 40 / 0 / 5 | 40 / 0 / 4 | 40 / 0 / 4 | P3 |
| 4 | 40 / 0 / 7 | 40 / 8 / 6 | 40 / 2 / 5 | 40 / 0 / 4 | P1 |
| 5 | 40 / 3 / 8 | 40 / 14 / 7 | 40 / 3 / 6 | 38 / 1 / 5 | P1 |
| 6 | 40 / 3 / 9 | 40 / 12 / 8 | 38 / 6 / 6 | 38 / 0 / 5 | P1 |
| 7 | 40 / 3 / 9 | 40 / 8 / 8 | 38 / 1 / 8 | 34 / 2 / 6 | P1 |
| 8 | 40 / 3 / 9 | 40 / 2 / 9 | 38 / 8 / 9 | 34 / 3 / 6 | P2 |
| 9 | 39 / 0 / 10 | 40 / 2 / 10 | 38 / 14 / 10 | 28 / 4 / 6 | P2 |
| 10 | 39 / 0 / 10 | 40 / 0 / 11 | 38 / 0 / 11 | 28 / 1 / 8 | P3 |
| 11 | 39 / 0 / 11 | 40 / 0 / 12 | 38 / 1 / 11 | 28 / 3 / 9 | P3 |
| 12 | 37 / 0 / 12 | 40 / 0 / 11 | 38 / 0 / 12 | 28 / 2 / 10 | P3 |
| 13 | 37 / 0 / 13 | 40 / 0 / 11 | 36 / 0 / 13 | 28 / 3 / 12 | P3 |
| 14 | 32 / 0 / 14 | 40 / 0 / 12 | 34 / 0 / 13 | 28 / 5 / 13 | P3 |
| 15 | 32 / 0 / 14 | 39 / 1 / 13 | 34 / 0 / 13 | 23 / 13 / 14 | P3 |
| 16 | 31 / 0 / 15 | 37 / 0 / 14 | 34 / 0 / 13 | 18 / 0 / 15 | P3 |
| 17 | 31 / 1 / 15 | 37 / 1 / 14 | 34 / 0 / 13 | 13 / 0 / 17 | P1 |
| 18 | 31 / 2 / 16 | 37 / 1 / 14 | 34 / 0 / 13 | 8 / 1 / 19 | P3 |
| 19 | 26 / 2 / 17 | 37 / 7 / 15 | 34 / 0 / 15 | 8 / 2 / 20 | P1 |
| 20 | 26 / 1 / 18 | 37 / 12 / 16 | 27 / 0 / 15 | 3 / 1 / 21 | P1 |
| 21 | 21 / 1 / 18 | 37 / 8 / 16 | 21 / 2 / 15 | 3 / 5 / 22 | P3 |
| 22 | 16 / 0 / 19 | 37 / 1 / 17 | 21 / 2 / 16 | 3 / 0 / 23 | P3 |
| 23 | 16 / 0 / 20 | 37 / 0 / 19 | 21 / 3 / 17 | OUT | P2 |
| 24 | 16 / 0 / 20 | 37 / 1 / 21 | 16 / 12 / 18 | OUT | P2 |
| 25 | 16 / 1 / 21 | 36 / 0 / 22 | 11 / 2 / 20 | OUT | P0 |
| 26 | 16 / 1 / 23 | 36 / 4 / 22 | 6 / 3 / 21 | OUT | P1 |
| 27 | 11 / 7 / 24 | 36 / 4 / 23 | 6 / 12 / 23 | OUT | P2 |
| 28 | 11 / 0 / 25 | 36 / 0 / 24 | 1 / 6 / 24 | OUT | P2 |
| 29 | 11 / 0 / 26 | 36 / 0 / 24 | OUT | OUT | P0 |
| 30 | 6 / 1 / 27 | 36 / 0 / 24 | OUT | OUT | P0 |

## Detailed action log
This is a simplified Commander model, not a rules-accurate MTG game.

========== ROUND 1 ==========
  P0 land -> 1 lands.
  P3 land -> 1 lands.
  P1 land -> 1 lands.
  P2 land -> 1 lands.
  End round: P0 control life=40 power=0 mana=1 threat=5.6, P1 control life=40 power=0 mana=1 threat=5.6, P2 control life=40 power=0 mana=1 threat=5.6, P3 control life=40 power=0 mana=1 threat=5.6

========== ROUND 2 ==========
  P0 land -> 2 lands.
  P0 (control) casts ramp artifact [ramp] cost 2, mana left 0.
  P3 land -> 2 lands.
  P3 (control) casts ramp artifact [ramp] cost 2, mana left 0.
  P1 land -> 2 lands.
  P1 (control) casts ramp artifact [ramp] cost 2, mana left 0.
  P2 land -> 2 lands.
  P2 (control) casts ramp artifact [ramp] cost 2, mana left 0.
  End round: P1 control life=40 power=0 mana=4 threat=7.4, P3 control life=40 power=0 mana=4 threat=7.4, P0 control life=40 power=0 mana=3 threat=6.7, P2 control life=40 power=0 mana=3 threat=6.7

========== ROUND 3 ==========
  P0 land -> 3 lands.
  P0 (control) casts ramp artifact [ramp] cost 3, mana left 1.
  P3 (control) casts engine enchantment [engine] cost 3, mana left 1.
  P1 land -> 3 lands.
  P1 (control) casts draw sorcery [draw] cost 3, mana left 2.
  P2 land -> 3 lands.
  P2 (control) casts ramp artifact [ramp] cost 3, mana left 1.
    P1 counters control:ramp:0 (cost 2).
  End round: P3 control life=40 power=0 mana=4 threat=10.2, P1 control life=40 power=0 mana=5 threat=8.1, P0 control life=40 power=0 mana=5 threat=7.8, P2 control life=40 power=0 mana=4 threat=7.1

========== ROUND 4 ==========
  P0 land -> 4 lands.
  P0 (control) casts ramp artifact [ramp] cost 3, mana left 3.
  P3 (control) casts engine enchantment [engine] cost 3, mana left 1.
    P0 counters control:engine:0 (cost 2).
  P1 land -> 4 lands.
  P1 (control) casts medium creature [creature] cost 3, mana left 3.
  P1 (control) casts tokens sorcery [tokens] cost 3, mana left 0.
  P2 land -> 4 lands.
  P2 (control) casts engine enchantment [engine] cost 2, mana left 3.
  P2 (control) casts draw sorcery [draw] cost 2, mana left 1.
  End round: P1 control life=40 power=8 mana=6 threat=15.8, P2 control life=40 power=2 mana=5 threat=12.7, P3 control life=40 power=0 mana=4 threat=10.2, P0 control life=40 power=0 mana=7 threat=8.6

========== ROUND 5 ==========
  P0 land -> 5 lands.
  P0 (control) casts small creature [creature] cost 1, mana left 7.
  P0 (control) casts removal instant [remove] cost 3, mana left 4.
  P3 (control) casts ramp artifact [ramp] cost 3, mana left 1.
  P1 land -> 5 lands.
  P1 (control) casts medium creature [creature] cost 4, mana left 3.
  P1 (control) casts small creature [creature] cost 2, mana left 1.
    COMBAT: P1 attacks P3 unblocked for 2; before=40 life.
  P2 land -> 5 lands.
  P2 (control) casts engine enchantment [engine] cost 2, mana left 4.
  P2 (control) casts medium creature [creature] cost 3, mana left 1.
  End round: P1 control life=40 power=14 mana=7 threat=21.6, P2 control life=40 power=3 mana=6 threat=13.5, P3 control life=38 power=1 mana=5 threat=12.1, P0 control life=40 power=3 mana=8 threat=11.5

========== ROUND 6 ==========
  P0 land -> 6 lands.
  P3 (control) casts engine enchantment [engine] cost 3, mana left 2.
    P0 counters control:engine:7 (cost 2).
    COMBAT: P3 1/1 attacks P1; P1 blocks with 2/2.
  P1 land -> 6 lands.
  P1 (control) casts removal instant [remove] cost 2, mana left 6.
    P3 counters control:removal:8 (cost 2).
    COMBAT: P1 2/2 attacks P2; P2 blocks with 3/3.
    COMBAT: P1 attacks P2 unblocked for 2; before=40 life.
  P2 (control) casts draw sorcery [draw] cost 3, mana left 3.
  P2 (control) casts small creature [creature] cost 2, mana left 1.
  End round: P1 control life=40 power=12 mana=8 threat=19.9, P2 control life=38 power=6 mana=6 threat=16.8, P0 control life=40 power=3 mana=9 threat=11.9, P3 control life=38 power=0 mana=5 threat=10.5

========== ROUND 7 ==========
  P0 (control) casts removal instant [remove] cost 3, mana left 6.
  P3 land -> 3 lands.
  P3 (control) casts engine enchantment [engine] cost 4, mana left 2.
  P1 (control) casts engine enchantment [engine] cost 2, mana left 6.
    P3 counters control:engine:5 (cost 2).
    COMBAT: P1 attacks P3 unblocked for 4; before=38 life.
  P2 land -> 6 lands.
  P2 (control) casts ramp artifact [ramp] cost 2, mana left 5.
  P2 (control) casts removal instant [remove] cost 3, mana left 2.
    COMBAT: P2 3/3 attacks P1; P1 blocks with 4/5.
  End round: P1 control life=40 power=8 mana=8 threat=16.4, P3 control life=34 power=2 mana=6 threat=15.4, P2 control life=38 power=1 mana=8 threat=13.6, P0 control life=40 power=3 mana=9 threat=11.9

========== ROUND 8 ==========
  P0 (control) casts removal instant [remove] cost 2, mana left 7.
  P3 (control) casts engine enchantment [engine] cost 3, mana left 3.
    P2 counters control:engine:9 (cost 2).
    P3 counter-counters; original spell resolves.
  P1 (control) casts ramp artifact [ramp] cost 3, mana left 5.
    COMBAT: P1 2/2 attacks P3; P3 blocks with 2/3.
  P2 land -> 7 lands.
  P2 (control) casts large creature [creature] cost 6, mana left 3.
  End round: P2 control life=38 power=8 mana=9 threat=20.0, P3 control life=34 power=3 mana=6 threat=19.5, P0 control life=40 power=3 mana=9 threat=11.9, P1 control life=40 power=2 mana=9 threat=11.5

========== ROUND 9 ==========
  P0 (control) casts ramp artifact [ramp] cost 2, mana left 7.
    COMBAT: P0 3/1 attacks P2; P2 blocks with 6/9.
  P3 (control) casts draw sorcery [draw] cost 3, mana left 3.
    P2 counters control:draw:4 (cost 2).
  P3 (control) casts draw sorcery [draw] cost 3, mana left 0.
    COMBAT: P3 attacks P0 unblocked for 1; before=40 life.
  P1 land -> 7 lands.
  P2 land -> 8 lands.
  P2 (control) casts engine enchantment [engine] cost 2, mana left 8.
  P2 (control) casts large creature [creature] cost 6, mana left 2.
    COMBAT: P2 attacks P3 unblocked for 6; before=34 life.
  End round: P2 control life=38 power=14 mana=10 threat=28.0, P3 control life=28 power=4 mana=6 threat=21.0, P1 control life=40 power=2 mana=10 threat=12.2, P0 control life=39 power=0 mana=10 threat=9.7

========== ROUND 10 ==========
  P0 (control) casts draw sorcery [draw] cost 3, mana left 7.
  P0 (control) casts draw sorcery [draw] cost 3, mana left 4.
  P0 (control) casts wipe sorcery [wipe] cost 4, mana left 0.
    Board wipe removes 8 creatures.
  P3 land -> 4 lands.
  P3 (control) casts draw sorcery [draw] cost 3, mana left 4.
  P3 (control) casts draw sorcery [draw] cost 2, mana left 2.
  P3 (control) casts ramp artifact [ramp] cost 2, mana left 0.
  P1 (control) casts draw sorcery [draw] cost 2, mana left 8.
  P1 (control) casts draw sorcery [draw] cost 3, mana left 5.
  P1 (control) casts ramp artifact [ramp] cost 2, mana left 3.
  P2 land -> 9 lands.
  End round: P3 control life=28 power=1 mana=8 threat=16.6, P2 control life=38 power=0 mana=11 threat=16.3, P1 control life=40 power=0 mana=11 threat=12.0, P0 control life=39 power=0 mana=10 threat=10.6

========== ROUND 11 ==========
  P0 land -> 7 lands.
  P0 (control) casts ramp artifact [ramp] cost 2, mana left 9.
    P1 counters control:ramp:2 (cost 2).
  P3 land -> 5 lands.
  P3 (control) casts medium creature [creature] cost 4, mana left 5.
    P0 counters control:medium:3 (cost 2).
  P3 (control) casts tokens sorcery [tokens] cost 4, mana left 1.
  P1 land -> 8 lands.
  P1 (control) casts medium creature [creature] cost 4, mana left 8.
  P1 (control) casts large creature [creature] cost 7, mana left 1.
  P2 (control) casts removal instant [remove] cost 2, mana left 9.
  P2 (control) casts removal instant [remove] cost 3, mana left 6.
  P2 (control) casts removal instant [remove] cost 3, mana left 3.
  End round: P3 control life=28 power=3 mana=9 threat=18.7, P2 control life=38 power=1 mana=11 threat=17.6, P1 control life=40 power=0 mana=12 threat=11.8, P0 control life=39 power=0 mana=11 threat=10.7

========== ROUND 12 ==========
  P0 land -> 8 lands.
  P3 land -> 6 lands.
  P3 (control) casts removal instant [remove] cost 2, mana left 8.
  P3 (control) casts removal instant [remove] cost 2, mana left 6.
  P3 (control) casts removal instant [remove] cost 3, mana left 3.
    COMBAT: P3 1/1 attacks P2; P2 blocks with 1/1.
    COMBAT: P3 attacks P0 unblocked for 2; before=39 life.
  P1 land -> 9 lands.
  P2 land -> 10 lands.
  End round: P3 control life=28 power=2 mana=10 threat=17.2, P2 control life=38 power=0 mana=12 threat=11.4, P0 control life=37 power=0 mana=12 threat=11.3, P1 control life=40 power=0 mana=11 threat=11.1

========== ROUND 13 ==========
  P0 land -> 9 lands.
  P0 (control) casts engine enchantment [engine] cost 4, mana left 9.
  P3 land -> 7 lands.
  P3 (control) casts removal instant [remove] cost 2, mana left 9.
  P3 (control) casts ramp artifact [ramp] cost 3, mana left 6.
    COMBAT: P3 attacks P2 unblocked for 2; before=38 life.
  P1 (control) casts engine enchantment [engine] cost 3, mana left 8.
  P1 (control) casts finisher sorcery [finisher] cost 5, mana left 3.
    P1 establishes persistent 5-damage/turn finisher.
  P2 land -> 11 lands.
  End round: P3 control life=28 power=3 mana=12 threat=19.9, P1 control life=40 power=0 mana=11 threat=16.6, P2 control life=36 power=0 mana=13 threat=11.9, P0 control life=37 power=0 mana=13 threat=11.7

========== ROUND 14 ==========
  P0 land -> 10 lands.
  P3 land -> 8 lands.
    COMBAT: P3 attacks P2 unblocked for 2; before=36 life.
  P1 land -> 10 lands.
  P2 (control) casts engine enchantment [engine] cost 4, mana left 9.
    P1 counters control:engine:7 (cost 2).
  End round: P3 control life=28 power=5 mana=13 threat=23.2, P1 control life=40 power=0 mana=12 threat=17.3, P0 control life=32 power=0 mana=14 threat=12.0, P2 control life=34 power=0 mana=13 threat=11.8

========== ROUND 15 ==========
  P0 (control) casts engine enchantment [engine] cost 3, mana left 11.
  P3 land -> 9 lands.
  P3 (control) casts engine enchantment [engine] cost 4, mana left 10.
  P3 (control) casts medium creature [creature] cost 3, mana left 7.
    COMBAT: P3 attacks P1 unblocked for 1; before=40 life.
  P1 land -> 11 lands.
  P2 (control) casts engine enchantment [engine] cost 4, mana left 9.
  End round: P3 control life=23 power=13 mana=14 threat=33.7, P1 control life=39 power=1 mana=13 threat=19.2, P0 control life=32 power=0 mana=14 threat=14.8, P2 control life=34 power=0 mana=13 threat=14.6

========== ROUND 16 ==========
  P0 land -> 11 lands.
  P0 (control) casts engine enchantment [engine] cost 2, mana left 13.
  P3 land -> 10 lands.
  P3 (control) casts medium creature [creature] cost 3, mana left 12.
    COMBAT: P3 1/1 attacks P0; P0 blocks with 2/3.
    COMBAT: P3 attacks P0 unblocked for 1; before=32 life.
    COMBAT: P3 attacks P1 unblocked for 2; before=39 life.
  P1 land -> 12 lands.
  P1 (control) casts medium creature [creature] cost 4, mana left 10.
  P1 (control) casts removal instant [remove] cost 2, mana left 8.
  P2 (control) casts medium creature [creature] cost 3, mana left 10.
  P2 (control) casts wipe sorcery [wipe] cost 5, mana left 5.
    Board wipe removes 10 creatures.
  End round: P3 control life=18 power=0 mana=15 threat=18.3, P1 control life=37 power=0 mana=14 threat=18.2, P0 control life=31 power=0 mana=15 threat=15.5, P2 control life=34 power=0 mana=13 threat=14.3

========== ROUND 17 ==========
  P3 land -> 11 lands.
  P3 (control) casts ramp artifact [ramp] cost 3, mana left 13.
  P2 (control) casts draw sorcery [draw] cost 2, mana left 11.
    P1 counters control:draw:7 (cost 2).
  End round: P1 control life=37 power=1 mana=14 threat=19.5, P3 control life=13 power=0 mana=17 threat=19.3, P0 control life=31 power=1 mana=15 threat=17.1, P2 control life=34 power=0 mana=13 threat=14.3

========== ROUND 18 ==========
  P0 land -> 12 lands.
  P0 (control) casts large creature [creature] cost 6, mana left 10.
  P0 (control) casts removal instant [remove] cost 2, mana left 8.
  P3 land -> 12 lands.
  P3 (control) casts ramp artifact [ramp] cost 2, mana left 16.
  P1 (control) casts removal instant [remove] cost 2, mana left 12.
  P2 (control) casts engine enchantment [engine] cost 3, mana left 10.
    P1 counters control:engine:5 (cost 2).
  End round: P3 control life=8 power=1 mana=19 threat=21.7, P1 control life=37 power=1 mana=14 threat=19.5, P0 control life=31 power=2 mana=16 threat=18.8, P2 control life=34 power=0 mana=13 threat=14.3

========== ROUND 19 ==========
  P0 land -> 13 lands.
    COMBAT: P0 1/1 attacks P1; P1 blocks with 1/1.
  P3 land -> 13 lands.
  P1 land -> 13 lands.
  P1 (control) casts large creature [creature] cost 6, mana left 9.
  P2 land -> 12 lands.
  P2 (control) casts ramp artifact [ramp] cost 3, mana left 11.
  End round: P1 control life=37 power=7 mana=15 threat=24.7, P3 control life=8 power=2 mana=20 threat=24.0, P0 control life=26 power=2 mana=17 threat=19.1, P2 control life=34 power=0 mana=15 threat=15.7

========== ROUND 20 ==========
  P0 land -> 14 lands.
  P0 (control) casts engine enchantment [engine] cost 2, mana left 16.
    COMBAT: P0 1/1 attacks P3; P3 blocks with 1/1.
    COMBAT: P0 1/1 attacks P1; P1 blocks with 7/5.
  P3 land -> 14 lands.
  P1 land -> 14 lands.
  P1 (control) casts draw sorcery [draw] cost 2, mana left 14.
  P1 (control) casts medium creature [creature] cost 4, mana left 10.
    COMBAT: P1 attacks P2 unblocked for 7; before=34 life.
  P2 (control) casts engine enchantment [engine] cost 2, mana left 13.
  End round: P1 control life=37 power=12 mana=16 threat=30.0, P3 control life=3 power=1 mana=21 threat=23.3, P0 control life=26 power=1 mana=18 threat=21.3, P2 control life=27 power=0 mana=15 threat=18.3

========== ROUND 21 ==========
  P0 (control) casts removal instant [remove] cost 3, mana left 15.
    P1 counters control:removal:2 (cost 2).
  P3 land -> 15 lands.
  P3 (control) casts draw sorcery [draw] cost 2, mana left 20.
    P2 counters control:draw:7 (cost 2).
  P3 (control) casts draw sorcery [draw] cost 3, mana left 17.
  P3 (control) casts small creature [creature] cost 1, mana left 16.
    COMBAT: P3 attacks P2 unblocked for 1; before=27 life.
  P1 (control) casts draw sorcery [draw] cost 2, mana left 14.
    COMBAT: P1 attacks P2 unblocked for 5; before=26 life.
  P2 (control) casts engine enchantment [engine] cost 4, mana left 11.
    P1 counters control:engine:9 (cost 2).
  P2 (control) casts removal instant [remove] cost 3, mana left 8.
  P2 (control) casts small creature [creature] cost 1, mana left 7.
  End round: P3 control life=3 power=5 mana=22 threat=28.1, P1 control life=37 power=8 mana=16 threat=27.0, P0 control life=21 power=1 mana=18 threat=21.3, P2 control life=21 power=2 mana=15 threat=19.6

========== ROUND 22 ==========
  P0 land -> 15 lands.
  P0 (control) casts wipe sorcery [wipe] cost 6, mana left 13.
    Board wipe removes 8 creatures.
  P0 (control) casts large creature [creature] cost 5, mana left 8.
  P3 land -> 16 lands.
  P3 (control) casts medium creature [creature] cost 3, mana left 20.
  P1 land -> 15 lands.
  P1 (control) casts removal instant [remove] cost 3, mana left 14.
  P2 land -> 13 lands.
  P2 (control) casts removal instant [remove] cost 2, mana left 14.
  End round: P3 control life=3 power=0 mana=23 threat=23.7, P1 control life=37 power=1 mana=17 threat=21.6, P2 control life=21 power=2 mana=16 threat=20.9, P0 control life=16 power=0 mana=19 threat=20.0

========== ROUND 23 ==========
  P0 land -> 16 lands.
  P3 land -> 17 lands.
    ELIMINATED P3 (control) round 23: persistent_finisher.
  P1 land -> 16 lands.
  P1 (control) casts ramp artifact [ramp] cost 2, mana left 16.
  P2 land -> 14 lands.
  P2 (control) casts removal instant [remove] cost 3, mana left 14.
  End round: P2 control life=21 power=3 mana=17 threat=22.9, P1 control life=37 power=0 mana=19 threat=21.7, P0 control life=16 power=0 mana=20 threat=20.7

========== ROUND 24 ==========
  P0 (control) casts draw sorcery [draw] cost 3, mana left 17.
  P0 (control) casts engine enchantment [engine] cost 4, mana left 13.
  P1 land -> 17 lands.
  P1 (control) casts ramp artifact [ramp] cost 3, mana left 17.
  P2 land -> 15 lands.
  P2 (control) casts draw sorcery [draw] cost 2, mana left 16.
  P2 (control) casts draw sorcery [draw] cost 2, mana left 14.
  P2 (control) casts draw sorcery [draw] cost 2, mana left 12.
  P2 (control) casts draw sorcery [draw] cost 2, mana left 10.
  P2 (control) casts draw sorcery [draw] cost 3, mana left 7.
  P2 (control) casts large creature [creature] cost 6, mana left 1.
  End round: P2 control life=16 power=12 mana=18 threat=32.6, P1 control life=37 power=1 mana=21 threat=24.4, P0 control life=16 power=0 mana=20 threat=23.8

========== ROUND 25 ==========
  P0 land -> 17 lands.
  P0 (control) casts draw sorcery [draw] cost 2, mana left 19.
  P0 (control) casts draw sorcery [draw] cost 2, mana left 17.
  P0 (control) casts removal instant [remove] cost 2, mana left 15.
  P0 (control) casts ramp artifact [ramp] cost 3, mana left 12.
  P1 (control) casts ramp artifact [ramp] cost 2, mana left 19.
    COMBAT: P1 1/1 attacks P2; P2 blocks with 1/1.
  P2 land -> 16 lands.
  P2 (control) casts removal instant [remove] cost 3, mana left 16.
  P2 (control) casts ramp artifact [ramp] cost 3, mana left 13.
  P2 (control) casts ramp artifact [ramp] cost 3, mana left 10.
    P0 counters control:ramp:3 (cost 2).
    COMBAT: P2 attacks P1 unblocked for 1; before=37 life.
  End round: P0 control life=16 power=1 mana=21 threat=26.4, P2 control life=11 power=2 mana=20 threat=24.5, P1 control life=36 power=0 mana=22 threat=24.0

========== ROUND 26 ==========
  P0 land -> 18 lands.
  P0 (control) casts ramp artifact [ramp] cost 3, mana left 19.
  P1 (control) casts medium creature [creature] cost 4, mana left 18.
  P2 land -> 17 lands.
  P2 (control) casts draw sorcery [draw] cost 3, mana left 18.
    P0 counters control:draw:5 (cost 2).
    COMBAT: P2 1/1 attacks P1; P1 blocks with 3/2.
  End round: P1 control life=36 power=4 mana=22 threat=28.4, P0 control life=16 power=1 mana=23 threat=27.5, P2 control life=6 power=3 mana=21 threat=26.1

========== ROUND 27 ==========
  P0 land -> 19 lands.
  P0 (control) casts medium creature [creature] cost 3, mana left 21.
  P0 (control) casts removal instant [remove] cost 3, mana left 18.
  P1 land -> 18 lands.
  P2 land -> 18 lands.
  P2 (control) casts medium creature [creature] cost 4, mana left 18.
  P2 (control) casts medium creature [creature] cost 4, mana left 14.
  P2 (control) casts ramp artifact [ramp] cost 3, mana left 11.
    COMBAT: P2 1/1 attacks P1; P1 blocks with 3/2.
  End round: P2 control life=6 power=12 mana=23 threat=35.1, P0 control life=11 power=7 mana=24 threat=33.5, P1 control life=36 power=4 mana=23 threat=29.1

========== ROUND 28 ==========
  P0 land -> 20 lands.
  P0 (control) casts draw sorcery [draw] cost 2, mana left 23.
  P0 (control) casts large creature [creature] cost 6, mana left 17.
  P0 (control) casts small creature [creature] cost 2, mana left 15.
    COMBAT: P0 1/1 attacks P1; P1 blocks with 3/2.
  P1 land -> 19 lands.
  P1 (control) casts wipe sorcery [wipe] cost 6, mana left 18.
    Board wipe removes 12 creatures.
  P2 land -> 19 lands.
  P2 (control) casts engine enchantment [engine] cost 2, mana left 22.
  P2 (control) casts medium creature [creature] cost 4, mana left 18.
  End round: P2 control life=1 power=6 mana=24 threat=31.8, P0 control life=11 power=0 mana=25 threat=27.6, P1 control life=36 power=0 mana=24 threat=25.4

========== ROUND 29 ==========
  P0 land -> 21 lands.
  P0 (control) casts small creature [creature] cost 1, mana left 25.
    ELIMINATED P2 (control) round 29: persistent_finisher.
  P1 (control) casts removal instant [remove] cost 3, mana left 21.
  End round: P0 control life=11 power=0 mana=26 threat=28.0, P1 control life=36 power=0 mana=24 threat=25.4

========== ROUND 30 ==========
  P0 land -> 22 lands.
  P1 (control) casts removal instant [remove] cost 3, mana left 21.
  End round: P0 control life=6 power=1 mana=27 threat=26.8, P1 control life=36 power=0 mana=24 threat=25.4
