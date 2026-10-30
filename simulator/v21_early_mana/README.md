# V21 early mana: Frostboil Snarl

`EarlyManaTable` extends v20 using the canonical v1.13 deck. Frostboil Snarl is represented as a land before the opening hand and mulligan decision. As it enters, its controller may reveal an Island or Mountain card from hand; without a reveal it enters tapped. A forced-tapped entry stays tapped. Once on the battlefield it taps for U or R. A `snarl_reveal_policy` can decline or choose an eligible object; the default reveals the first eligible card. This is a bounded policy rather than an assessment of strategic desirability.

Focused tests cover both colors, basic and nonbasic reveal options, decline, invalid cards, forced-tapped entry, land play choices and Magnus's token discount interacting with Capsize buyback. The source-paid narrative uses Snarl to cast Mystical Tutor. The test suite and validation script retain the canonical v1.13 list; historical fixtures stay intact. No additional caching is introduced.

Other early mana and cost-reduction cards, general layers and replacement effects remain incomplete. Source: [Strixhaven release notes](https://magic.wizards.com/en/news/feature/strixhaven-school-mages-and-commander-2021-edition-release-notes-2021-04-16).
