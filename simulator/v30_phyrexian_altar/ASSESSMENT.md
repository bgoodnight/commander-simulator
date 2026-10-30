# V30 assessment

The current U/R mana pool supports Phyrexian Altar as a repeatable immediate sacrifice-for-blue-or-red ability. The source-paid interaction shows Reinforcements and Pyromancer creating tokens, Altar consuming one to fund Consider, and Pyromancer creating a replacement. The proxy is treated as a normal card.

All 722 tests passed locally; the canonical v1.13 200-game conservation sweep had no safety stops. Twelve eight-round samples had median 452.362 ms, versus 340.598 ms in the v29 run. These are exploratory measurements with different host load and game trajectories, so the difference does not isolate Altar overhead. Four saved v14 fingerprints match. No additional caching was added.

The mana pool cannot produce W/B/G; other payment dependency, sacrifice/death trigger, convoke and general Magic rules remain incomplete. Altar is partial in the coverage audit. These runs are not a deck-strength study.
