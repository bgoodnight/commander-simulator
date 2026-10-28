# Exact selection across five spells

Forced conserved late-game fixture; actual source payments, declared library/hand choices. Not an unbiased opening.

Brainstorm: Abrade selected with exact requested top/bottom choices; Ponder: Abrade selected with exact requested top/bottom choices; Preordain: Abrade selected with exact requested top/bottom choices; Telling Time: Abrade selected with exact requested top/bottom choices; Impulse: Abrade selected with exact requested top/bottom choices. Brainstorm/Ponder/Preordain draw; Telling Time/Impulse put a looked-at card into hand.

## Branch 1

```text
FORCED DIAGNOSTIC: declared late-game source layout and chosen hand/library cards from actual conserved decks. No natural opening or win-rate claim.
FORCED LIBRARY TOP: ['Island', 'Mountain', 'Abrade']
    MANA P0: Island #434 -> (0, 1, 0)
  P0 (magnus) casts Brainstorm [instant] for 1; mana=12.
    STACK +1 [spell] P0: Brainstorm.
    CHOICE brainstorm_put_back P0: ['Mountain', 'Island']; {}.
```

## Branch 2

```text
FORCED DIAGNOSTIC: declared late-game source layout and chosen hand/library cards from actual conserved decks. No natural opening or win-rate claim.
FORCED LIBRARY TOP: ['Island', 'Mountain', 'Abrade']
    MANA P0: Island #434 -> (0, 1, 0)
  P0 (magnus) casts Ponder [sorcery] for 1; mana=12.
    STACK +1 [spell] P0: Ponder.
    CHOICE ponder_order P0: ['Abrade', 'Island', 'Mountain']; {}.
    CHOICE ponder_shuffle P0: []; {'shuffle': False}.
```

## Branch 3

```text
FORCED DIAGNOSTIC: declared late-game source layout and chosen hand/library cards from actual conserved decks. No natural opening or win-rate claim.
FORCED LIBRARY TOP: ['Island', 'Mountain', 'Abrade']
    MANA P0: Island #434 -> (0, 1, 0)
  P0 (magnus) casts Preordain [sorcery] for 1; mana=12.
    STACK +1 [spell] P0: Preordain.
    CHOICE scry P0: ['Island', 'Mountain']; {'top': [], 'bottom': [72, 88]}.
```

## Branch 4

```text
FORCED DIAGNOSTIC: declared late-game source layout and chosen hand/library cards from actual conserved decks. No natural opening or win-rate claim.
FORCED LIBRARY TOP: ['Island', 'Mountain', 'Abrade']
    MANA P0: Island #462 -> (0, 1, 0)
    MANA P0: Island #464 -> (0, 1, 0)
  P0 (magnus) casts Telling Time [instant] for 2; mana=11.
    STACK +1 [spell] P0: Telling Time.
    CHOICE look_to_hand P0: ['Abrade']; {}.
    CHOICE telling_top P0: ['Island']; {}.
```

## Branch 5

```text
FORCED DIAGNOSTIC: declared late-game source layout and chosen hand/library cards from actual conserved decks. No natural opening or win-rate claim.
FORCED LIBRARY TOP: ['Island', 'Mountain', 'Abrade', 'Capsize']
    MANA P0: Island #434 -> (0, 1, 0)
    MANA P0: Island #436 -> (0, 1, 0)
  P0 (magnus) casts Impulse [instant] for 2; mana=11.
    STACK +1 [spell] P0: Impulse.
    CHOICE look_to_hand P0: ['Abrade']; {}.
    CHOICE impulse_bottom P0: ['Capsize', 'Island', 'Mountain']; {}.
```
