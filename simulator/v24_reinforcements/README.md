# V24 Ral's Reinforcements

`ReinforcementTable` adds Ral's Reinforcements: a 1R sorcery that creates two 1/1 blue and red Elemental creature tokens. Its tokens carry both colors in the kernel at entry, enabling later color-aware mechanics. Existing definitions use `colors=None` for unknown color rather than assuming colorless; empty sets explicitly represent colorless. This does not implement general color layers or convoke.

A backwards-compatible creature-creation seam permits a complete token definition to be supplied before the creature-entered event. The two tokens are currently created sequentially during one resolution; effects depending on simultaneous entry are not yet supported. Coverage therefore remains partial. Magnus's generic reduction and Young Pyromancer's cast trigger interact with the new tokens. Sapphire Medallion does not reduce Ral's Reinforcements because the sorcery is red, even though the tokens it creates are blue and red.

Tests cover costs, colors at entry, timing, token identity, a Young Pyromancer interaction and Magnus reduction. The source-paid narrative traces those interactions and Capsize buyback. No additional caching is introduced. Source: [March of the Machine design article](https://magic.wizards.com/en/news/card-preview/a-battle-for-the-ages-leading-march-of-the-machine-set-design).

The initial 200-game sweep recorded one four-second wall-clock safety stop (seat 0, seed 48); an isolated rerun of the same game completed consistently in 0.895 seconds with no stop. `validation_initial.json` preserves the initial result. A second sweep had 21 time-limit stops; all 21 stopped cases passed on isolated retry. A third complete sweep passed with no stops. All results are retained; a wall-clock stop is not interpreted as a rules verdict.
