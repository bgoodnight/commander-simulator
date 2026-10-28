# Simulated game
**Seed:** 20261028 · **Pilot:** delay_one · **Scenario:** one_removal_t5
**First Magnus:** 7 · **Selection spells cast:** 3 · **Total instant/sorcery casts:** 3 · **First combo-ready turn:** none
**Mulligan:** 0 · **Mana spent:** 19 · **Generic mana discounted:** 0

## Turn-by-turn trace


TURN 1 [opening hand=7 cards]
    Draw: Muddle the Mixture
  Land: Island.
  End: lands 1, rocks 0, engines 0, tokens 0, hand 7, grave 0.

TURN 2
    Draw: Twincast
  Land: Mountain.
  End: lands 2, rocks 0, engines 0, tokens 0, hand 7, grave 0.

TURN 3
    Draw: Telling Time
    Pay Telling Time: 1 generic + 1U + 0R; sources [L0:1, L1:1]; float (0, 0, 0, 0, 0).
  Cast Telling Time.
    Telling Time: hand ['Sokenzan, Crucible of Defiance'], top ['Brainstorm'], bottom ['Preordain']
  End: lands 2, rocks 0, engines 0, tokens 0, hand 8, grave 1.

TURN 4
    Draw: Brainstorm
  Land: Sokenzan, Crucible of Defiance.
    Pay Brainstorm: 0 generic + 1U + 0R; sources [L0:1]; float (0, 0, 0, 0, 0).
  Cast Brainstorm.
    Draw: Comet Storm, Island, Impulse
    Brainstorm put back: ['Comet Storm', 'Spellseeker']
  End: lands 3, rocks 0, engines 0, tokens 0, hand 8, grave 2.

TURN 5
    Draw: Comet Storm
  Land: Island.
    Pay Impulse: 1 generic + 1U + 0R; sources [L0:1, L1:1]; float (0, 0, 0, 0, 0).
  Cast Impulse.
    Impulse: took Mountain
  End: lands 4, rocks 0, engines 0, tokens 0, hand 8, grave 3.

TURN 6
    Draw: Pongify
  Land: Mountain.
  POLICY: could cast Magnus, deliberately develop cabal this turn instead.
    Pay Voidmage Prodigy: 0 generic + 2U + 0R; sources [L0:1, L3:1]; float (0, 0, 0, 0, 0).
  Cast Voidmage Prodigy [partial behavior].
    Pay Dualcaster Mage: 1 generic + 0U + 2R; sources [L1:1, L2:1, L4:1]; float (0, 0, 0, 0, 0).
  Cast Dualcaster Mage.
  End: lands 5, rocks 0, engines 1, tokens 0, hand 6, grave 3.

TURN 7
    Draw: Island
  Land: Island.
    Pay Magnus the Red: 3 generic + 1U + 1R; sources [L0:1, L1:1, L2:1, L3:1, L4:1]; float (0, 0, 0, 0, 0).
  Cast MAGNUS THE RED from command zone.
  End: lands 6, rocks 0, engines 1, tokens 0, hand 6, grave 3.

TURN 8
    Draw: Step Through
    Pay Storm-Kiln Artist: 3 generic + 0U + 1R; sources [L0:1, L1:1, L2:1, L3:1]; float (0, 0, 0, 0, 0).
  Cast Storm-Kiln Artist.
  COMBAT assumption: Magnus connects unblocked, creates Spawn.
    Trigger: create 1 Spawn token(s); total tokens 1.
  End: lands 6, rocks 0, engines 2, tokens 1, hand 6, grave 3.
