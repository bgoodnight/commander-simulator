# Four-player replay: Spellslinger Burst
**Seed:** 55007 · **Seats:** P0 spellslinger, P1 spellslinger, P2 spellslinger, P3 spellslinger
**Result:** P1 wins (spell_burst) in round 17

## Elimination order
- Round 10: P0 (spellslinger) eliminated by combat
- Round 17: P2 (spellslinger) eliminated by spell_burst
- Round 17: P3 (spellslinger) eliminated by spell_burst

## Board-state timeline
Life is the actual game resource; public threat is an arbitrary target-selection proxy.
| Round | P0 life / power / mana | P1 life / power / mana | P2 life / power / mana | P3 life / power / mana | Public leader |
|---:|---|---|---|---|---|
| 1 | 40 / 0 / 1 | 40 / 3 / 1 | 40 / 0 / 1 | 40 / 0 / 1 | P1 |
| 2 | 37 / 0 / 2 | 40 / 3 / 3 | 40 / 0 / 3 | 40 / 2 / 2 | P3 |
| 3 | 35 / 3 / 3 | 40 / 0 / 5 | 40 / 2 / 5 | 40 / 3 / 3 | P0 |
| 4 | 35 / 0 / 6 | 40 / 0 / 5 | 38 / 2 / 8 | 38 / 2 / 5 | P3 |
| 5 | 27 / 2 / 7 | 40 / 1 / 6 | 38 / 8 / 8 | 38 / 2 / 6 | P3 |
| 6 | 22 / 6 / 8 | 40 / 1 / 7 | 34 / 8 / 8 | 36 / 9 / 7 | P0 |
| 7 | 17 / 2 / 9 | 39 / 3 / 7 | 34 / 6 / 9 | 35 / 5 / 8 | P3 |
| 8 | 4 / 0 / 10 | 25 / 2 / 9 | 21 / 10 / 10 | 35 / 3 / 9 | P2 |
| 9 | 4 / 4 / 12 | 19 / 15 / 10 | 21 / 10 / 10 | 35 / 2 / 10 | P1 |
| 10 | OUT | 15 / 18 / 12 | 17 / 18 / 10 | 31 / 3 / 11 | P1 |
| 11 | OUT | 11 / 16 / 15 | 15 / 18 / 10 | 24 / 0 / 12 | P1 |
| 12 | OUT | 11 / 9 / 17 | 15 / 17 / 11 | 19 / 2 / 15 | P1 |
| 13 | OUT | 11 / 19 / 18 | 15 / 11 / 12 | 15 / 8 / 17 | P1 |
| 14 | OUT | 11 / 9 / 19 | 15 / 6 / 12 | 12 / 3 / 20 | P1 |
| 15 | OUT | 9 / 7 / 20 | 11 / 11 / 12 | 6 / 6 / 20 | P1 |
| 16 | OUT | 8 / 8 / 21 | 11 / 9 / 12 | 6 / 16 / 21 | P3 |
| 17 | OUT | 4 / 13 / 22 | OUT | OUT | P1 |

## Detailed action log
This is a simplified Commander model, not a rules-accurate MTG game.

========== ROUND 1 ==========
  P0 land -> 1 lands.
  P3 land -> 1 lands.
  P1 land -> 1 lands.
  P1 (spellslinger) casts small creature [creature] cost 1, mana left 0.
  P2 land -> 1 lands.
  End round: P1 spellslinger life=40 power=3 mana=1 threat=8.1, P0 spellslinger life=40 power=0 mana=1 threat=5.6, P2 spellslinger life=40 power=0 mana=1 threat=5.6, P3 spellslinger life=40 power=0 mana=1 threat=5.6

========== ROUND 2 ==========
  P0 land -> 2 lands.
  P0 (spellslinger) casts engine enchantment [engine] cost 2, mana left 0.
  P3 land -> 2 lands.
  P3 (spellslinger) casts engine enchantment [engine] cost 2, mana left 0.
  P1 land -> 2 lands.
  P1 (spellslinger) casts ramp artifact [ramp] cost 2, mana left 0.
    COMBAT: P1 attacks P0 unblocked for 3; before=40 life.
  P2 land -> 2 lands.
  P2 (spellslinger) casts ramp artifact [ramp] cost 2, mana left 0.
  End round: P3 spellslinger life=40 power=2 mana=2 threat=10.9, P1 spellslinger life=40 power=3 mana=3 threat=9.2, P0 spellslinger life=37 power=0 mana=2 threat=8.6, P2 spellslinger life=40 power=0 mana=3 threat=6.7

========== ROUND 3 ==========
  P0 land -> 3 lands.
  P0 (spellslinger) casts engine enchantment [engine] cost 3, mana left 0.
  P3 land -> 3 lands.
  P3 (spellslinger) casts draw sorcery [draw] cost 2, mana left 1.
  P3 (spellslinger) casts small creature [creature] cost 1, mana left 0.
    COMBAT: P3 attacks P0 unblocked for 2; before=37 life.
  P1 land -> 3 lands.
  P1 (spellslinger) casts ramp artifact [ramp] cost 3, mana left 1.
    COMBAT: P1 3/1 attacks P3; P3 blocks with 1/1.
  P2 land -> 3 lands.
  P2 (spellslinger) casts ramp artifact [ramp] cost 2, mana left 2.
  P2 (spellslinger) casts small creature [creature] cost 2, mana left 0.
  End round: P0 spellslinger life=35 power=3 mana=3 threat=15.3, P3 spellslinger life=40 power=3 mana=3 threat=13.2, P2 spellslinger life=40 power=2 mana=5 threat=9.6, P1 spellslinger life=40 power=0 mana=5 threat=7.5

========== ROUND 4 ==========
  P0 land -> 4 lands.
  P0 (spellslinger) casts ramp artifact [ramp] cost 3, mana left 1.
    COMBAT: P0 1/1 attacks P3; P3 blocks with 1/1.
  P3 land -> 4 lands.
  P3 (spellslinger) casts ramp artifact [ramp] cost 3, mana left 1.
    COMBAT: P3 attacks P2 unblocked for 2; before=40 life.
  P1 (spellslinger) casts draw sorcery [draw] cost 3, mana left 2.
  P1 (spellslinger) casts removal instant [remove] cost 2, mana left 0.
  P2 land -> 4 lands.
  P2 (spellslinger) casts ramp artifact [ramp] cost 3, mana left 3.
  P2 (spellslinger) casts draw sorcery [draw] cost 3, mana left 0.
    COMBAT: P2 attacks P3 unblocked for 2; before=40 life.
  End round: P3 spellslinger life=38 power=2 mana=5 threat=12.8, P2 spellslinger life=38 power=2 mana=8 threat=11.5, P0 spellslinger life=35 power=0 mana=6 threat=11.2, P1 spellslinger life=40 power=0 mana=5 threat=7.8

========== ROUND 5 ==========
  P0 land -> 5 lands.
  P0 (spellslinger) casts draw sorcery [draw] cost 2, mana left 5.
  P0 (spellslinger) casts draw sorcery [draw] cost 3, mana left 2.
  P0 (spellslinger) casts engine enchantment [engine] cost 2, mana left 0.
  P3 land -> 5 lands.
  P3 (spellslinger) casts draw sorcery [draw] cost 2, mana left 4.
  P3 (spellslinger) casts engine enchantment [engine] cost 2, mana left 2.
  P3 (spellslinger) casts draw sorcery [draw] cost 2, mana left 0.
    COMBAT: P3 attacks P0 unblocked for 2; before=35 life.
  P1 land -> 4 lands.
  P1 (spellslinger) casts draw sorcery [draw] cost 3, mana left 3.
  P1 (spellslinger) casts small creature [creature] cost 2, mana left 1.
  P2 (spellslinger) casts tokens sorcery [tokens] cost 3, mana left 5.
  P2 (spellslinger) casts medium creature [creature] cost 3, mana left 2.
  P2 (spellslinger) casts burn instant [burn] cost 2, mana left 0.
    COMBAT: P2 2/2 attacks P0; P0 blocks with 2/3.
  End round: P3 spellslinger life=38 power=2 mana=6 threat=16.6, P0 spellslinger life=27 power=2 mana=7 threat=16.5, P2 spellslinger life=38 power=8 mana=8 threat=16.5, P1 spellslinger life=40 power=1 mana=6 threat=9.8

========== ROUND 6 ==========
  P0 land -> 6 lands.
  P0 (spellslinger) casts combo_piece artifact [combo_piece] cost 3, mana left 5.
  P0 (spellslinger) casts tokens sorcery [tokens] cost 3, mana left 2.
  P0 (spellslinger) casts removal instant [remove] cost 2, mana left 0.
    COMBAT: P0 attacks P3 unblocked for 2; before=38 life.
  P3 land -> 6 lands.
  P3 (spellslinger) casts tokens sorcery [tokens] cost 3, mana left 4.
  P3 (spellslinger) casts small creature [creature] cost 2, mana left 2.
  P3 (spellslinger) casts small creature [creature] cost 2, mana left 0.
  P1 land -> 5 lands.
  P1 (spellslinger) casts engine enchantment [engine] cost 4, mana left 3.
  P1 (spellslinger) casts burn instant [burn] cost 3, mana left 0.
    COMBAT: P1 attacks P0 unblocked for 1; before=27 life.
  P2 (spellslinger) casts draw sorcery [draw] cost 3, mana left 5.
  P2 (spellslinger) casts burn instant [burn] cost 3, mana left 2.
  End round: P0 spellslinger life=22 power=6 mana=8 threat=22.4, P3 spellslinger life=36 power=9 mana=7 threat=21.2, P2 spellslinger life=34 power=8 mana=8 threat=16.5, P1 spellslinger life=40 power=1 mana=7 threat=12.7

========== ROUND 7 ==========
  P0 land -> 7 lands.
  P0 (spellslinger) casts large creature [creature] cost 6, mana left 3.
  P0 (spellslinger) casts small creature [creature] cost 2, mana left 1.
    COMBAT: P0 2/3 attacks P3; P3 blocks with 3/1.
    COMBAT: P0 2/2 attacks P3; P3 blocks with 3/2.
  P3 land -> 7 lands.
  P3 (spellslinger) casts tokens sorcery [tokens] cost 4, mana left 4.
  P3 (spellslinger) casts removal instant [remove] cost 2, mana left 2.
  P3 (spellslinger) casts burn instant [burn] cost 2, mana left 0.
    COMBAT: P3 attacks P1 unblocked for 1; before=40 life.
  P1 (spellslinger) casts engine enchantment [engine] cost 4, mana left 3.
    COMBAT: P1 attacks P3 unblocked for 1; before=36 life.
  P2 land -> 5 lands.
  P2 (spellslinger) casts large creature [creature] cost 6, mana left 3.
    P1 counters spellslinger:large:1 (cost 2).
    COMBAT: P2 2/2 attacks P0; P0 blocks with 2/2.
  End round: P3 spellslinger life=35 power=5 mana=8 threat=18.2, P1 spellslinger life=39 power=3 mana=7 threat=17.2, P0 spellslinger life=17 power=2 mana=9 threat=15.8, P2 spellslinger life=34 power=6 mana=9 threat=14.9

========== ROUND 8 ==========
  P0 land -> 8 lands.
  P0 (spellslinger) casts removal instant [remove] cost 3, mana left 7.
    COMBAT: P0 2/2 attacks P2; P2 blocks with 4/5.
  P3 land -> 8 lands.
  P3 (spellslinger) casts removal instant [remove] cost 3, mana left 6.
  P3 (spellslinger) casts finisher sorcery [finisher] cost 6, mana left 0.
    P3 spell burst: 13 to EACH opponent.
    COMBAT: P3 1/1 attacks P1; P1 blocks with 2/3.
    COMBAT: P3 attacks P1 unblocked for 1; before=26 life.
  P1 land -> 6 lands.
  P1 (spellslinger) casts draw sorcery [draw] cost 3, mana left 5.
  P1 (spellslinger) casts ramp artifact [ramp] cost 2, mana left 3.
    COMBAT: P1 2/3 attacks P2; P2 blocks with 4/5.
  P2 land -> 6 lands.
  P2 (spellslinger) casts large creature [creature] cost 7, mana left 3.
  End round: P2 spellslinger life=21 power=10 mana=10 threat=17.4, P3 spellslinger life=35 power=3 mana=9 threat=16.1, P1 spellslinger life=25 power=2 mana=9 threat=14.6, P0 spellslinger life=4 power=0 mana=10 threat=13.3

========== ROUND 9 ==========
  P0 land -> 9 lands.
  P0 (spellslinger) casts medium creature [creature] cost 3, mana left 8.
  P0 (spellslinger) casts ramp artifact [ramp] cost 2, mana left 6.
  P3 land -> 9 lands.
    COMBAT: P3 1/1 attacks P2; P2 blocks with 4/5.
  P1 land -> 7 lands.
  P1 (spellslinger) casts tokens sorcery [tokens] cost 4, mana left 6.
  P1 (spellslinger) casts medium creature [creature] cost 4, mana left 2.
  P2 (spellslinger) casts engine enchantment [engine] cost 3, mana left 7.
    P3 counters spellslinger:engine:6 (cost 2).
    COMBAT: P2 attacks P1 unblocked for 6; before=25 life.
  End round: P1 spellslinger life=19 power=15 mana=10 threat=27.7, P0 spellslinger life=4 power=4 mana=12 threat=17.9, P2 spellslinger life=21 power=10 mana=10 threat=17.4, P3 spellslinger life=35 power=2 mana=10 threat=15.2

========== ROUND 10 ==========
  P0 land -> 10 lands.
  P0 (spellslinger) casts medium creature [creature] cost 4, mana left 9.
  P0 (spellslinger) casts ramp artifact [ramp] cost 2, mana left 7.
    COMBAT: P0 4/3 attacks P1; P1 blocks with 4/5.
  P3 land -> 10 lands.
  P1 land -> 8 lands.
  P1 (spellslinger) casts medium creature [creature] cost 4, mana left 7.
  P1 (spellslinger) casts ramp artifact [ramp] cost 2, mana left 5.
    COMBAT: P1 1/1 attacks P0; P0 blocks with 4/5.
    COMBAT: P1 attacks P3 unblocked for 2; before=35 life.
    COMBAT: P1 attacks P3 unblocked for 2; before=33 life.
    COMBAT: P1 attacks P2 unblocked for 4; before=21 life.
  P2 (spellslinger) casts draw sorcery [draw] cost 2, mana left 8.
  P2 (spellslinger) casts tokens sorcery [tokens] cost 4, mana left 4.
  P2 (spellslinger) casts medium creature [creature] cost 3, mana left 1.
  P2 (spellslinger) casts small creature [creature] cost 1, mana left 0.
    COMBAT: P2 attacks P1 unblocked for 4; before=19 life.
    COMBAT: P2 attacks P0 unblocked for 6; before=4 life.
    ELIMINATED P0 (spellslinger) round 10: combat.
  End round: P1 spellslinger life=15 power=18 mana=12 threat=30.8, P2 spellslinger life=17 power=18 mana=10 threat=26.4, P3 spellslinger life=31 power=3 mana=11 threat=16.9

========== ROUND 11 ==========
  P3 land -> 11 lands.
  P3 (spellslinger) casts draw sorcery [draw] cost 3, mana left 9.
    COMBAT: P3 1/1 attacks P1; P1 blocks with 1/3.
    COMBAT: P3 1/1 attacks P1; P1 blocks with 2/2.
    COMBAT: P3 1/1 attacks P1; P1 blocks with 2/2.
  P1 land -> 9 lands.
  P1 (spellslinger) casts engine enchantment [engine] cost 4, mana left 9.
  P1 (spellslinger) casts ramp artifact [ramp] cost 3, mana left 6.
    COMBAT: P1 2/2 attacks P2; P2 blocks with 3/4.
    COMBAT: P1 attacks P2 unblocked for 2; before=17 life.
    COMBAT: P1 attacks P3 unblocked for 2; before=31 life.
    COMBAT: P1 attacks P3 unblocked for 4; before=29 life.
  P2 (spellslinger) casts small creature [creature] cost 2, mana left 8.
    COMBAT: P2 attacks P1 unblocked for 4; before=15 life.
    COMBAT: P2 1/1 attacks P1; P1 blocks with 1/3.
    COMBAT: P2 1/1 attacks P1; P1 blocks with 2/2.
    COMBAT: P2 attacks P3 unblocked for 1; before=25 life.
  End round: P1 spellslinger life=11 power=16 mana=15 threat=33.0, P2 spellslinger life=15 power=18 mana=10 threat=25.7, P3 spellslinger life=24 power=0 mana=12 threat=13.5

========== ROUND 12 ==========
  P3 land -> 12 lands.
  P3 (spellslinger) casts engine enchantment [engine] cost 2, mana left 11.
  P3 (spellslinger) casts ramp artifact [ramp] cost 2, mana left 9.
  P1 land -> 10 lands.
  P1 (spellslinger) casts draw sorcery [draw] cost 2, mana left 14.
  P1 (spellslinger) casts engine enchantment [engine] cost 2, mana left 12.
  P1 (spellslinger) casts engine enchantment [engine] cost 4, mana left 8.
  P1 (spellslinger) casts medium creature [creature] cost 4, mana left 4.
  P1 (spellslinger) casts ramp artifact [ramp] cost 3, mana left 1.
    COMBAT: P1 2/2 attacks P2; P2 blocks with 2/3.
    COMBAT: P1 2/2 attacks P2; P2 blocks with 3/4.
    COMBAT: P1 2/2 attacks P3; P3 blocks with 2/3.
    COMBAT: P1 4/5 attacks P2; P2 blocks with 6/6.
  P2 land -> 7 lands.
    COMBAT: P2 1/1 attacks P1; P1 blocks with 1/3.
    COMBAT: P2 attacks P3 unblocked for 3; before=24 life.
    COMBAT: P2 attacks P3 unblocked for 2; before=21 life.
  End round: P1 spellslinger life=11 power=9 mana=17 threat=33.1, P2 spellslinger life=15 power=17 mana=11 threat=25.1, P3 spellslinger life=19 power=2 mana=15 threat=19.8

========== ROUND 13 ==========
  P3 land -> 13 lands.
  P3 (spellslinger) casts medium creature [creature] cost 4, mana left 12.
  P3 (spellslinger) casts ramp artifact [ramp] cost 2, mana left 10.
  P1 land -> 11 lands.
  P1 (spellslinger) casts draw sorcery [draw] cost 3, mana left 15.
  P1 (spellslinger) casts engine enchantment [engine] cost 2, mana left 13.
  P1 (spellslinger) casts large creature [creature] cost 5, mana left 8.
  P1 (spellslinger) casts small creature [creature] cost 1, mana left 7.
    COMBAT: P1 1/3 attacks P3; P3 blocks with 5/2.
    COMBAT: P1 1/1 attacks P2; P2 blocks with 4/5.
    COMBAT: P1 attacks P3 unblocked for 4; before=19 life.
    COMBAT: P1 3/5 attacks P2; P2 blocks with 6/6.
  P2 (spellslinger) casts ramp artifact [ramp] cost 3, mana left 8.
    COMBAT: P2 6/6 attacks P1; P1 blocks with 9/7.
  End round: P1 spellslinger life=11 power=19 mana=18 threat=45.0, P3 spellslinger life=15 power=8 mana=17 threat=26.2, P2 spellslinger life=15 power=11 mana=12 threat=20.8

========== ROUND 14 ==========
  P3 land -> 14 lands.
  P3 (spellslinger) casts draw sorcery [draw] cost 2, mana left 16.
  P3 (spellslinger) casts engine enchantment [engine] cost 2, mana left 14.
  P3 (spellslinger) casts removal instant [remove] cost 2, mana left 12.
  P3 (spellslinger) casts ramp artifact [ramp] cost 3, mana left 9.
    COMBAT: P3 2/3 attacks P1; P1 blocks with 3/3.
  P1 land -> 12 lands.
    COMBAT: P1 2/3 attacks P2; P2 blocks with 3/4.
    COMBAT: P2 4/5 attacks P3; P3 blocks with 5/2.
    COMBAT: P2 1/1 attacks P1; P1 blocks with 3/3.
    COMBAT: P2 attacks P3 unblocked for 3; before=15 life.
  End round: P1 spellslinger life=11 power=9 mana=19 threat=35.4, P3 spellslinger life=12 power=3 mana=20 threat=23.8, P2 spellslinger life=15 power=6 mana=12 threat=16.2

========== ROUND 15 ==========
  P3 (spellslinger) casts engine enchantment [engine] cost 4, mana left 16.
  P3 (spellslinger) casts tokens sorcery [tokens] cost 5, mana left 11.
    P2 counters spellslinger:tokens:4 (cost 2).
  P3 (spellslinger) casts wipe sorcery [wipe] cost 6, mana left 5.
    P1 counters spellslinger:wipe:0 (cost 2).
  P1 land -> 13 lands.
  P1 (spellslinger) casts combo_piece artifact [combo_piece] cost 4, mana left 16.
    COMBAT: P1 attacks P2 unblocked for 4; before=15 life.
    COMBAT: P1 1/1 attacks P3; P3 blocks with 2/3.
    COMBAT: P1 attacks P3 unblocked for 3; before=12 life.
    COMBAT: P1 1/1 attacks P2; P2 blocks with 2/3.
  P2 (spellslinger) casts medium creature [creature] cost 4, mana left 8.
    COMBAT: P2 attacks P3 unblocked for 3; before=9 life.
    COMBAT: P2 attacks P1 unblocked for 2; before=11 life.
  End round: P1 spellslinger life=9 power=7 mana=20 threat=35.4, P3 spellslinger life=6 power=6 mana=20 threat=29.5, P2 spellslinger life=11 power=11 mana=12 threat=19.9

========== ROUND 16 ==========
  P3 land -> 15 lands.
  P3 (spellslinger) casts draw sorcery [draw] cost 2, mana left 19.
  P3 (spellslinger) casts tokens sorcery [tokens] cost 5, mana left 14.
  P3 (spellslinger) casts medium creature [creature] cost 3, mana left 11.
    COMBAT: P3 attacks P1 unblocked for 1; before=9 life.
    COMBAT: P3 2/3 attacks P2; P2 blocks with 5/5.
  P1 land -> 14 lands.
  P2 (spellslinger) casts removal instant [remove] cost 2, mana left 10.
    COMBAT: P2 2/3 attacks P1; P1 blocks with 3/3.
  End round: P3 spellslinger life=6 power=16 mana=21 threat=37.4, P1 spellslinger life=8 power=8 mana=21 threat=37.3, P2 spellslinger life=11 power=9 mana=12 threat=17.9

========== ROUND 17 ==========
  P3 land -> 16 lands.
  P3 (spellslinger) casts medium creature [creature] cost 4, mana left 18.
    COMBAT: P3 1/1 attacks P1; P1 blocks with 3/3.
    COMBAT: P3 1/1 attacks P1; P1 blocks with 4/4.
    COMBAT: P3 attacks P1 unblocked for 2; before=8 life.
    COMBAT: P3 attacks P1 unblocked for 2; before=6 life.
  P1 land -> 15 lands.
  P1 (spellslinger) casts small creature [creature] cost 2, mana left 20.
  P1 (spellslinger) casts finisher sorcery [finisher] cost 8, mana left 12.
    P1 spell burst: 24 to EACH opponent.
    ELIMINATED P2 (spellslinger) round 17: spell_burst.
    ELIMINATED P3 (spellslinger) round 17: spell_burst.
  End round: P1 spellslinger life=4 power=13 mana=22 threat=42.8
