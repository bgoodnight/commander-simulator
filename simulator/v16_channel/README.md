# V16 channel abilities

`ChannelTable` extends v15 with hand-based channel choices for Otawara, Soaring City and Sokenzan, Crucible of Defiance. Activation pays the reduced mana cost and discards the source before the ability goes onto the existing priority stack. Otawara targets an artifact, creature, enchantment or planeswalker and rechecks legality on resolution. Sokenzan creates two 1/1 Spirit creature tokens with haste. The default pilot may activate these during its own main phase; policy callbacks can choose them in other priority windows.

Each controlled legendary creature reduces the generic portion by one, to a minimum of zero; the colored requirement remains. V16 supplies missing legendary metadata for Baral. Other cards depend on the completeness of existing card metadata, and arbitrary type/layer effects are not fully modeled. Sokenzan's Spirit subtype and haste are modeled; the kernel does not model token color, so red is not represented. Channel therefore remains a bounded subset rather than full Oracle coverage.

Run `python simulator/v16_channel/tests.py` and `python simulator/v16_channel/validate.py`. The validator uses declared source-paid fixtures, an explicitly synthetic removal response and a 200-game conservation sweep. Timing comparisons are exploratory because decisions and game trajectories can change. No additional caching is introduced; the v14 reference cases remain intact.

Rules references: [Kamigawa: Neon Dynasty release notes](https://magic.wizards.com/en/news/feature/kamigawa-neon-dynasty-release-notes-2022-02-09) and [channel mechanics](https://magic.wizards.com/en/news/feature/kamigawa-neon-dynasty-mechanics-2022-01-27).
