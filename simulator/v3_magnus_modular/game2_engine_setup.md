# Simulated game
**Seed:** 20261073 · **Pilot:** delay_one · **Scenario:** one_removal_t5
**First Magnus:** 4 · **Selection spells cast:** 4 · **Total instant/sorcery casts:** 4 · **First combo-ready turn:** none
**Mulligan:** 0 · **Mana spent:** 41 · **Generic mana discounted:** 0

## Turn-by-turn trace


TURN 1 [opening hand=7 cards]
    Draw: Muddle the Mixture
  Land: Mountain.
    Pay Sol Ring: 1 generic + 0U + 0R; sources [L0:1]; float (0, 0, 0, 0, 0).
  Cast Sol Ring.
  End: lands 1, rocks 1, engines 0, tokens 0, hand 6, grave 0.

TURN 2
    Draw: Island
  Land: Island.
    Pay Telling Time: 1 generic + 1U + 0R; sources [L1:1, A:Sol Ring:2]; float (0, 0, 1, 0, 0).
  Cast Telling Time.
    Telling Time: hand ['Exotic Orchard'], top ['Archmage Emeritus'], bottom ['Dualcaster Mage']
  End: lands 2, rocks 1, engines 0, tokens 0, hand 6, grave 1.

TURN 3
    Draw: Archmage Emeritus
  Land: Exotic Orchard.
  POLICY: could cast Magnus, deliberately develop cabal this turn instead.
    Pay Impulse: 1 generic + 1U + 0R; sources [L1:1, A:Sol Ring:2]; float (0, 0, 1, 0, 0).
  Cast Impulse.
    Impulse: took Mountain
    Pay Sorcerer Class: 0 generic + 1U + 1R; sources [L0:1, L2:1]; float (0, 0, 1, 0, 0).
  Cast Sorcerer Class [partial behavior].
    Draw: Storm-Kiln Artist, Stormsplitter
    Draw/discard: ['Searing Touch', 'Muddle the Mixture']
  End: lands 3, rocks 1, engines 1, tokens 0, hand 5, grave 4.

TURN 4
    Draw: Ponder
  Land: Riptide Laboratory.
    Pay Magnus the Red: 3 generic + 1U + 1R; sources [L0:1, L1:1, L2:1, A:Sol Ring:2]; float (0, 0, 0, 0, 0).
  Cast MAGNUS THE RED from command zone.
  End: lands 4, rocks 1, engines 1, tokens 0, hand 5, grave 4.

TURN 5
    Draw: Mystic Speculation
  Land: Mountain.
    Pay Stormsplitter: 3 generic + 0U + 1R; sources [L0:1, L1:1, A:Sol Ring:2]; float (0, 0, 0, 0, 0).
  Cast Stormsplitter [partial behavior].
    Pay Ponder: 0 generic + 1U + 0R; sources [L2:1]; float (0, 0, 0, 0, 0).
  Cast Ponder.
    Trigger: create 1 Stormsplitter token(s); total tokens 1.
    Ponder ordered: ['Steam Vents', 'Mountain', 'Flusterstorm']
    Draw: Steam Vents
  COMBAT assumption: Magnus connects unblocked, creates Spawn.
    Trigger: create 1 Spawn token(s); total tokens 2.
  OPPONENT: casts targeted creature removal at Magnus the Red.
  RESULT: Magnus the Red removed.
  End: lands 5, rocks 1, engines 2, tokens 1, hand 4, grave 5.

TURN 6
    Draw: Mountain
  Land: Steam Vents.
    Pay Magnus the Red: 5 generic + 1U + 1R; sources [L0:1, L1:1, L2:1, L3:1, L4:1, A:Sol Ring:2]; float (0, 0, 0, 0, 0).
  Cast MAGNUS THE RED from command zone.
    Pay Mystic Speculation: 0 generic + 1U + 0R; sources [L5:1]; float (0, 0, 0, 0, 0).
  Cast Mystic Speculation.
    Trigger: create 1 Stormsplitter token(s); total tokens 2.
    Scry 3: kept ['Flusterstorm'], bottomed ['Mountain', 'Mountain'].
  End: lands 6, rocks 1, engines 2, tokens 1, hand 3, grave 6.

TURN 7
    Draw: Flusterstorm
  Land: Mountain.
    Pay Storm-Kiln Artist: 3 generic + 0U + 1R; sources [L0:1, L1:1, A:Sol Ring:2]; float (0, 0, 0, 0, 0).
  Cast Storm-Kiln Artist.
    Pay Archmage Emeritus: 2 generic + 2U + 0R; sources [L2:1, L3:1, L4:1, L5:1]; float (0, 0, 0, 0, 0).
  Cast Archmage Emeritus.
  COMBAT assumption: Magnus connects unblocked, creates Spawn.
    Trigger: create 1 Spawn token(s); total tokens 2.
  End: lands 7, rocks 1, engines 4, tokens 2, hand 1, grave 6.

TURN 8
    Draw: Pink Horror
    Pay Pink Horror: 3 generic + 0U + 1R; sources [L0:1, L1:1, A:Sol Ring:2]; float (0, 0, 0, 0, 0).
  Cast Pink Horror.
    Pay Sorcerer Class: 3 generic + 1U + 0R; sources [L2:1, L3:1, L4:1, L5:1]; float (0, 0, 0, 0, 0).
  Activate Sorcerer Class -> level 2.
  COMBAT assumption: Magnus connects unblocked, creates Spawn.
    Trigger: create 1 Spawn token(s); total tokens 3.
  End: lands 7, rocks 1, engines 4, tokens 3, hand 1, grave 6.
