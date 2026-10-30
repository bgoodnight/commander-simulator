# V27 assessment

Fabricate searches for an artifact. Step Through's wizardcycling pays 2 and discards the card before its activated ability goes on the stack; it searches for a Wizard card. Both support failing to find and shuffling. The full Step Through sorcery mode is not implemented.

Fourteen tests cover artifact and Wizard search, derived Wizard types, response and counterability, mana and discard costs, timing and Young Pyromancer interactions. A source-paid narrative finds Phyrexian Altar and Spellseeker; their effects are not yet implemented. The complete suite of 692 tests passed. A 200-game v1.13 sweep across all seats passed consistency checks without safety stops. Median eight-round runtime was 315.264 ms over 12 games; host and game trajectory differences limit comparisons. No new caching.

General cycling triggers, reveal visibility, full continuous layers, simultaneous token entry, Spellseeker and Phyrexian Altar remain unsupported. These games do not establish deck strength.
