# V12 interaction results

All 6 targeted scenarios passed. See the linked Markdown stories and companion JSON for exact source payments, stack history and damage batches.

| Scenario | Observed result |
|---|---|
| [Multiple blockers: legal nonlethal split](01_free_assignment.md) | The 4/8 attacker assigned 1 and 3 damage to 2/3 and 3/4 blockers. Both survived; their simultaneous return damage marked 5 on the attacker. No damage assignment order was imposed. |
| [Trample recalculates after blocker bounce](02_trample_bounce.md) | After two blockers were declared, Capsize bounced the 3/3 token (it ceased to exist). The 8-power trampler assigned 2 to the remaining 2/2 and 6 to the defending player. Capsize paid from actual lands. |
| [Double strike uses damage marked in the first step](03_two_step_trample.md) | First-strike damage marked 4 on the 1/6 blocker. In the normal damage step, another 2 was lethal; the remaining 2 trampled through. The blocker dealt 1 back only in the normal step. |
| [Abrade between damage steps preserves blocked status](04_abrade_between_steps.md) | The double-striker marked 3 in the first step. Abrade then dealt 3 using actual source mana, killing the 1/5 blocker before it could retaliate. The attacker remained blocked and had no trample, so its second step dealt no player damage. |
| [Two damage steps create two Magnus triggers](05_magnus_two_hits.md) | Actual Magnus received an explicitly synthetic double-strike grant. Each 4-damage hit queued its own printed token trigger. Priority resolved one Spawn after each step: 8 player damage, 2 Spawn total. |
| [Capsize after first hit prevents the second hit](06_magnus_interrupted.md) | The first 4-damage hit resolved its Spawn trigger. Capsize then returned Magnus to hand using actual lands and the token discount. The scheduled normal damage step still occurred, but the departed attacker dealt nothing: 4 damage, 1 Spawn. |

Live sweep: 200 twelve-round games, all four Magnus seats; 0 safety stops; 100920 steps; 3864 damage batches including 295 with multiple declared blockers; 10900 source payments. Physical cards, zones, spell frames and mana pools passed consistency checks.

Exploratory median milliseconds per eight-round game (12 samples/engine): {'StepTable': 347.279, 'CombatTable': 314.807}. Changed blocking decisions change trajectories, so this is not an isolated microbenchmark.

Synthetic strike/trample fixtures validate mechanics; unforced detailed deck has no newly enabled keyword cards. No win-rate inference.
