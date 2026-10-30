# V26 assessment

Merchant Scroll searches for a blue instant and Solve the Equation searches for an instant or sorcery. Both may fail to find, reveal and put a chosen card in hand, then shuffle. Tests check eligibility, costs, Sapphire Medallion and Magnus reduction, response timing and Young Pyromancer. A source-paid interaction demonstrates both searches and six Elemental tokens from Pyromancer and Ral's Reinforcements.

All 678 tests passed locally. A 200-game v1.13 sweep across all seats passed consistency checks with zero safety stops. Median eight-round runtime was 320.149 ms over 12 games; host and trajectory changes limit comparisons. No new caching was introduced.

Merchant Scroll uses verified printed colors. General color-changing effects and hidden-information visibility rules remain unmodeled. Selection defaults to a simple heuristic, and many other deck effects, simultaneous token-entry effects and graveyard mechanics remain incomplete. These games do not establish deck strength.
