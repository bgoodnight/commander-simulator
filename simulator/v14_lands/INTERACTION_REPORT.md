# V14 land interaction results

All 7 targeted narratives passed. Companion JSON includes actual source payments, land events, priority and final reference fingerprints.

| Scenario | Observed result |
|---|---|
| [Life payment and typed lands produce different legal mana](01_shock_and_types.md) | Branch 1 declined Steam Vents payment, leaving it tapped at 40 life. Its Island/Mountain types still let Sulfur Falls enter untapped and pay for Ponder. Branch 2 paid 2 life for Steam Vents, then used it for Ponder; life was 38 and damage taken stayed zero. |
| [Entry checks use current other lands, types and opponents](02_entry_boundaries.md) | Coast entered tapped with one other land and untapped with two. Canal entered tapped with three other lands. Sanctuary entered untapped with two basic Islands plus Steam Vents (an Island); its graveyard trigger remains deferred. Training Center entered tapped after the table dropped to one opponent. |
| [Passage costs are paid before responses; early basic stays tapped](03_early_fetch.md) | Playing Passage did not fetch. Activating it tapped/sacrificed it before anyone received priority; the ability then resolved without its source. The first fetched Island entered tapped and provided no immediate mana. After the next declared own-turn untap it paid for Ponder. |
| [Fourth fetched land enters tapped, then untaps and pays for a spell](04_fourth_land.md) | Three actual sources paid for Adaptation and were tapped. Passage was played and sacrificed. Its fetched Island entered tapped, then untapped because the resulting battlefield had four lands. That exact new source paid for Ponder immediately; Passage itself was not counted. |
| [A response changes the resolution-time untap threshold](05_fetch_response.md) | Passage began as the fourth land and was sacrificed as a cost. With its ability waiting, source-paid Capsize bounced another Island. The fetched basic still arrived, but the resulting three-land battlefield failed the untap condition, so it stayed tapped. |
| [Failing to find still shuffles and does not refund the sacrifice](06_fail_to_find.md) | The explicit search policy chose no basic, which is legal for the hidden-zone search. Passage remained in the graveyard, no land entered, and the library was shuffled. The activation was not a spell or a draw. |
| [Land play and fetch do not trigger cast engines](07_cast_interaction.md) | Preordain made one Pyromancer Elemental. Playing and activating Passage made none. The fourth fetched Island untapped and paid for Ponder, which made exactly one additional Elemental through the ordinary cast trigger. |

Sweep: 200 twelve-round games; 0 safety stops; 100682 steps; 11013 source payments; 6899 land entries; 48 fetch resolutions. All independent consistency/conservation checks passed.

Exploratory median milliseconds per eight-round game (12 samples/engine): {'EngineTable': 430.368, 'LandTable': 549.671}. No additional caching was introduced. Historical figures are preserved separately; rules and host load change trajectories/timing.

200 deterministic reference fingerprints are saved in REFERENCE_CASES.json for future optimization equivalence checks. Reference serialization is outside benchmark timing.

Infrastructure diagnostics with one detailed deck and synthetic opponents; no win-rate inference.
