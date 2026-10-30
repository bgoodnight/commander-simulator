# V23 Sapphire Medallion

`MedallionTable` extends v22. Sapphire Medallion costs two generic mana, enters as an artifact, and reduces the generic portion of its controller's printed blue v1.13 spells by one per Medallion. The colored mana floor remains unchanged. `CARD_COLORS.json` records printed colors from the same Scryfall snapshot and hash as v20; colors are distinct from color identities. This subset does not model continuous color-changing effects, general color indicators, spell copies or color metadata for synthetic opponent spells.

The v11 named-action constructor provides an optional table-specific cost adjustment hook. Historical tables have no hook and keep their previous behavior. Tests cover supported blue and multicolored spells, red spells, colored floors, priority choice availability and cost changes, Capsize buyback and a removed Medallion. A source-paid narrative tests Capsize plus buyback. Historical engines and reference cases remain intact; no new caching is added.

Source: [Modern Horizons 3 release notes](https://magic.wizards.com/en/news/feature/modern-horizons-3-release-notes).
