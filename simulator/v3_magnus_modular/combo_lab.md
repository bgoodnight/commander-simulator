# Controlled combo tests (synthetic initial boards)

These are **constructed** test states, not naturally drawn games. Three repetitions use the same cost and trigger engine. Infinite viability is inferred from a continuing resource state, not from a complete MTG rules engine.

## Searing Touch + Storm-Kiln Artist

{'iterations': 3, 'sustainable': True, 'note': 'Simulated bounded repetitions; not a full proof of an infinite loop.'}

    Trigger: create 4 Spawn token(s); total tokens 4.
    Pay Searing Touch: 0 generic + 0U + 1R; sources [L0:1]; float (0, 0, 0, 0, 0).
  Cast Searing Touch with buyback.
    Trigger: Storm-Kiln Artist creates 1 Treasure(s); total 1.
    Utility target/effect not fully adjudicated (searing_touch).
    Pay Searing Touch: 0 generic + 0U + 1R; sources [X0:1]; float (0, 0, 0, 0, 0).
  Cast Searing Touch with buyback.
    Trigger: Storm-Kiln Artist creates 1 Treasure(s); total 1.
    Utility target/effect not fully adjudicated (searing_touch).
    Pay Searing Touch: 0 generic + 0U + 1R; sources [X0:1]; float (0, 0, 0, 0, 0).
  Cast Searing Touch with buyback.
    Trigger: Storm-Kiln Artist creates 1 Treasure(s); total 1.
    Utility target/effect not fully adjudicated (searing_touch).

Final: {'tokens': 4, 'treasure': 1, 'casts': 3, 'spell_in_hand': True}

## Mystic Speculation + Young Pyromancer + Altar

{'iterations': 3, 'sustainable': True, 'note': 'Simulated bounded repetitions; not a full proof of an infinite loop.'}

    Trigger: create 2 Spawn token(s); total tokens 2.
    Pay Mystic Speculation: 0 generic + 1U + 0R; sources [L0:1]; float (0, 0, 0, 0, 0).
  Cast Mystic Speculation with buyback.
    Trigger: create 1 Elemental token(s); total tokens 3.
    Scry 3: kept ['Island', 'Mountain', 'Island'], bottomed [].
    Altar sacrificed 1 token(s) for mana; 2 remain.
    Pay Mystic Speculation: 0 generic + 1U + 0R; sources [T1:1]; float (0, 0, 0, 0, 0).
  Cast Mystic Speculation with buyback.
    Trigger: create 1 Elemental token(s); total tokens 3.
    Scry 3: kept ['Island', 'Mountain', 'Island'], bottomed [].
    Altar sacrificed 1 token(s) for mana; 2 remain.
    Pay Mystic Speculation: 0 generic + 1U + 0R; sources [T2:1]; float (0, 0, 0, 0, 0).
  Cast Mystic Speculation with buyback.
    Trigger: create 1 Elemental token(s); total tokens 3.
    Scry 3: kept ['Island', 'Mountain', 'Island'], bottomed [].

Final: {'tokens': 3, 'treasure': 0, 'casts': 3, 'spell_in_hand': True}

## Mystic Speculation + Stormsplitter + Sorcerer Class

{'iterations': 3, 'sustainable': True, 'note': 'Simulated bounded repetitions; not a full proof of an infinite loop.'}

    Trigger: create 2 Spawn token(s); total tokens 2.
    Pay Mystic Speculation: 0 generic + 1U + 0R; sources [L0:1]; float (0, 0, 0, 0, 0).
  Cast Mystic Speculation with buyback.
    Trigger: create 1 Stormsplitter token(s); total tokens 3.
    Scry 3: kept ['Island', 'Mountain', 'Island'], bottomed [].
    Pay Mystic Speculation: 0 generic + 1U + 0R; sources [C:Magnus the Red:1]; float (0, 0, 0, 0, 0).
  Cast Mystic Speculation with buyback.
    Trigger: create 1 Stormsplitter token(s); total tokens 4.
    Trigger: create 1 Stormsplitter token(s); total tokens 5.
    Scry 3: kept ['Island', 'Mountain', 'Island'], bottomed [].
    Pay Mystic Speculation: 0 generic + 1U + 0R; sources [C:Stormsplitter:1]; float (0, 0, 0, 0, 0).
  Cast Mystic Speculation with buyback.
    Trigger: create 1 Stormsplitter token(s); total tokens 6.
    Trigger: create 1 Stormsplitter token(s); total tokens 7.
    Trigger: create 1 Stormsplitter token(s); total tokens 8.
    Trigger: create 1 Stormsplitter token(s); total tokens 9.
    Scry 3: kept ['Island', 'Mountain', 'Island'], bottomed [].

Final: {'tokens': 9, 'treasure': 0, 'casts': 3, 'spell_in_hand': True}
