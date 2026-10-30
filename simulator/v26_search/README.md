# V26 Merchant Scroll and Solve the Equation

`SearchTable` adds Merchant Scroll (1U; search for a blue instant) and Solve the Equation (2U; search for an instant or sorcery). On resolution, a chosen card is revealed and moved into its owner's hand, then the library is shuffled; a policy can fail to find. Search uses v20 card types and v23 printed colors. Merchant Scroll fails closed if an instant's color is unknown; general color-changing effects and reveal visibility rules are not modeled. The default tutor policy is heuristic, not an optimized strategy.

Focused checks cover both selection restrictions and hand destinations, decline and shuffle, response timing, printed blue mana requirements, Sapphire Medallion, Magnus and Young Pyromancer. The source-paid narrative follows both searches through Consider and Ral's Reinforcements. General simultaneous token entry and other previously noted limitations remain. No additional caching was added.

Card text references: [Merchant Scroll](https://scryfall.com/card/8ed/91/merchant-scroll) and [Solve the Equation](https://scryfall.com/card/stx/54/solve-the-equation).
