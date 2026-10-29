# V15 utility interactions

Six forced narratives passed; 200 twelve-round games passed consistency checks with 0 safety stops.

| Scenario | Result |
|---|---|
| [Sanctuary returns Ponder for a second cast](01_sanctuary_reuse.md) | Three other Islands let Sanctuary enter untapped. Its triggered ability targeted the previously cast Ponder in the graveyard and put it on top. The diagnostic draw and a second source-paid cast produced another Pyromancer Elemental: two in total. |
| [Sanctuary target leaving the graveyard causes the trigger to fail](02_target_lost.md) | The trigger chose Ponder when placed on the stack. A declared synthetic response moved that exact graveyard object to exile; on resolution the trigger had no legal target and did not return it. No printed graveyard-exile card was added by this scenario. |
| [Fiery Islet pays life for mana, then later sacrifices to draw](03_islet_modes.md) | An actual Fiery Islet mana activation produced U and paid one life without damage. After a declared next-turn untap, a different land paid the one-mana draw-ability cost; Islet was tapped and sacrificed before the card was drawn. |
| [A spell resolves before the waiting Islet draw](04_islet_response.md) | The Islet draw ability paid its source and mana costs. Brainstorm was cast in response, completing its draw and put-back choices before the Islet ability resolved and drew its card. |
| [Riptide, Adaptation, Harmonic and a response](05_riptide_response.md) | Adaptation made Iconoclast a Wizard, enabling Riptide. In response, Capsize bounced that same creature; the Riptide ability then failed its target check. Capsize had already triggered the adapted Iconoclast twice through Harmonic, creating two Soldiers. |
| [Removing Adaptation makes the Riptide target illegal](06_type_removed.md) | Capsize returned Adaptation while the Riptide ability waited. Iconoclast remained on the battlefield but lost the Wizard subtype; Riptide rechecked its target and failed without returning it. |

Median eight-round milliseconds (12 samples per engine): {'LandTable': 394.733, 'UtilityTable': 415.247}. Game trajectories differ; this is an exploratory comparison.

One detailed deck and synthetic opponents; no deck win-rate conclusions.
