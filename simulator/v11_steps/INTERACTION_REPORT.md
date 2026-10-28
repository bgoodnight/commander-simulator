# V11 interaction results

Five forced-board scenarios passed. Each preserves inventories and pays from actual source objects.

| Scenario | Observed result |
|---|---|
| Abrade: announced modes, damage and artifact destruction | Creature mode marked 3 damage on a 1-toughness creature (survived=False); artifact mode destroyed its chosen ramp permanent. |
| Capsize: successful buyback, then a countered recast | First cast returned the target and Capsize to hand. After an explicitly advanced untap, the second bought-back cast was countered; Capsize entered the graveyard. |
| Arcane Adaptation: live Wizard types and captured triggers | Adaptation made Iconoclast a Wizard. Harmonic Prodigy doubled triggers from Preordain and the responding Capsize (4 Soldiers). Capsize bounced Adaptation; already queued triggers survived. A later Ponder produced only 1 Soldier. |
| Frantic Search: atomic selection, untap and source reuse | Drew 2, discarded 2, untapped 3 actual lands. Young Pyromancer then reused restored source IDs [434] in the same main phase. |
| Combat: response after blocks and persistent blocked status | Goblin Electromancer was blocked. Capsize bounced the blocker in the post-block priority window. The attacker remained blocked and dealt zero player damage (no trample). |

Seeded sweep: 200 twelve-round games; 0 safety stops; 99302 exposed steps; 3937 combat batches. Physical cards, zones, spell frames and mana pools passed consistency checks.

Exploratory median milliseconds per eight-round game: {'PriorityTable': 152.606, 'StepTable': 308.3}.

Ordinary timing and the declared card subsets are covered. Multiple blockers, first/double strike, trample, copied spells, broad buyback/choice/layer coverage and multiple real decks remain out of scope. No deck-power inference.
