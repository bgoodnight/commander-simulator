# V22 Consider

`ConsiderTable` extends v21 and supports Consider as a U instant. It looks at the top card, optionally moves it to its owner's graveyard, then draws one card. `consider_policy` selects whether to move that card; the default keeps it. Surveil is not treated as milling. The card is paid and cast through the existing source-backed stack, so normal spell-cast triggers apply. Drawing from an empty library uses the existing player-elimination handling.

Focused tests exercise both choices, invalid choices, the blue cost, empty library, Young Pyromancer, a Mystical Tutor chain and Mystic Sanctuary recovery. The source-paid narrative covers Mystical Tutor into Consider with Young Pyromancer. Existing fixtures remain versioned and no additional caching is introduced. Other spells, spell-color effects, layers, general graveyard mechanics and surveil-specific triggered abilities remain incomplete.

Source: [official release notes](https://magic.wizards.com/en/news/feature/reality-fracture-release-notes).
