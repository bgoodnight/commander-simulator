# Mortarion physical — composed-effect and opponent stress audit

Codebase: `bgoodnight/commander-simulator`.
Physical deck: `mortarion_physical_final`, unchanged from locked list.
Verified rules/build: regression and opponent stress workflow at `c535cea9`.
The 37-suite regression runner observes **1,337 tests** at this revision.

## Scope and caveat

These trials execute the pinned physical deck and its **reviewed** card
effects in the existing kernel. The three opponents are seeded **abstract
pressure archetypes** on independent player seats, not legal 100-card decks.
Opponent creatures are physical battlefield tokens; some reviewed effects
(Pestilence, death triggers, target removal, combat blocker legality) can
interact with them. Opponent creature development, removal and combo pressure
are external stress policies, not invented card casts or a full priority
stack. Do not interpret 'survived 10 turns' as a real Commander win rate.

All matchup samples use **24 paired seeds per scenario, 10 turns**.

| Scenario | Survival at 10* | Mean seat-0 life | Blocks/seed | Unblocked damage/seed | Opponent exiles/seed | Mortarion paid X end steps/seed |
| --- | --- | --- | --- | --- | --- | --- |
| Goldfish | 24/24 | 37.54 | 0 | 0 | 0 | 1.33 |
| Balanced (aggro/control/value) | 24/24 | 33.12 | 7.62 | 7.08 | 2.33 | 0.54 |
| Aggressive (aggro/aggro/value) | 24/24 | 29.67 | 10.04 | 10.42 | 0.46 | 1.38 |
| Control (control/control/value) | 24/24 | 36.42 | 4.75 | 3.12 | 4.08 | 0.25 |
| Combo (value/control/combo) | 24/24 | 15.75 | 6.42 | 2.50 | 2.33 | 0.50 |

*Survival has only the narrowly implemented pressure/elimination model;
opponents have no decks, their own win conditions or complete combat.

**Main finding:** Mana development and early body deployment appear robust
in bounded trials. Control removes recurring engine pieces and sharply
reduces useful Mortarion X triggers, while abstract combo clocks create
late-game life pressure that normal blocks do not solve. Real win
probabilities, bracket estimates, effective attack clock and actual
matchup ranking remain **unestablished**.

Turn-10 hand contains an average of about 3 *unavailable or unimplemented*
actions in this simulator across scenarios. A high number of unsupported
hand actions is an engine coverage limitation, not a deck-quality verdict.

## Reusable mechanics newly implemented or connected in this milestone

- **Physical opponent stress:** shared kernel battlefield for three seeded
  opponent seats, roles shuffled per seed; finite opponent removal budget.
- **Physical blocking/damage:** block using the kernel's legal blocker list,
  simultaneous creature damage, normal state-based actions, death triggers,
  deathtouch lethal, cleanup at each player end. Still no first-strike,
  trample assignment, menace double-blocking, full combat triggers, etc.
- **Threat-aware hand removal:** previously reviewed instant/sorcery removal
  cards now admitted by the physical loader and executed on actual
  opponent objects. The same generic pilot compares intended board impact
  with friendly casualties, rather than firing blindly.
- **Composed upkeep:** Dreadhorde Invasion's loss/amass Zombie Army with
  proper +1/+1 counters; Plague Spitter's global damage on upkeep.
- **Restricted-variable mana:** Crypt Rats' black-only X payment and
  X-damage uses generic composed payment and damage. Shared pilot chooses
  X only for sufficiently good physical board trades.
- **Death reactions:** Sangromancer's life gain when opposing creatures die
  uses the existing reviewed death-trigger executor.
- **Generic end-of-turn P/T change:** shared batch modifier, LKI snapshot,
  SBA/death resolution and cleanup. Massacre Wurm uses this primitive for
  -2/-2 to opposing creatures and its existing death-drain trigger.
- **Source cost and sequencing:** same authoritative mana, graveyard, stack
  and token operations as existing card work. No text-inferred permissions.

## Narrative review: bugs/misplays identified and addressed

1. **Entire opponent attack treated as unblocked life loss.** An earlier
   pressure model killed 23/24 aggressive samples. This was misleading
   because seat zero could not block. Replaced with physical attackers,
   legal blockers and real damage/trades. Rerun: all 24 sampled games
   survive ten bounded turns; do **not** treat either figure as a real
   matchup estimate.
2. **Deathtouch ignored in block choices.** Tokens such as Ophiomancer's
   Snake would decline worthwhile trades. Generic blocker policy now
   recognizes lethal deathtouch damage; tested against 2/2 attackers.
3. **Marked damage persisted between turns.** Call existing kernel cleanup
   at each end-turn, so partial damage and temporary stat modifiers expire.
4. **Opponent control removal was unbounded and free.** Finite per-seat
   abstract interaction charges now prevent infinite removal from the
   pressure policy. Actual card costs/hand information remain unknown.
5. **Reviewed removal recipes were not marked as castable cards.** Physical
   card admission now checks those source-pinned recipes; the pilot can
   legally cast them when real opponent objects provide valid targets.
6. **Bounded mana planner could exhaust on speculative, unsupported card
   previews and crash a simulation.** Speculative lookahead now fails
   closed and logs inconclusive previews; it never guesses a mana payment.
7. **Low-life generic spell policy skipped zero-life-loss spells and
   rejected small beneficial X values.** Repaired, covered by regression.

The sample narratives show early land development, occasional Mortarion
casts by turn 4, control opponents frequently spending removal on the
commander, and board-clearing uses of Mandate of Abaddon by turn 7.
These observations align with the aggregate control/combo stress signals.
No physical opponent deck pilots, true APNAP stack or response priority
are available to verify strategic lines at full Commander fidelity.

## Still inaccessible or only partially modeled

This milestone **does not finish every printed ability** in the locked
physical deck. Relevant remaining families include:

- **Equipment/attachments and continuous effects:** Skullclamp,
  Basilisk Collar, Swiftfoot Boots, Eldrazi Monument, Whip of Erebos.
- **Complex zone changes and replacements:** Nurgle's Conscription,
  Nurgle's Rot aura/attachment, Whip temporary reanimation/exile,
  Undying Malice's delayed return.
- **Life-gain replacement and damage subscription:** Plague Drone,
  Stuffy Doll; Plague Spitter's death trigger is still distinct from its
  newly implemented upkeep trigger.
- **Triggered combat, spells from unusual zones, cascade:** Sloppity
  Bilepiper; Dreadhorde Invasion's 6-power Zombie attacking lifelink;
  some of Syr Konrad's nonbattlefield graveyard movement triggers.
- **Extra player and opponent effects:** opponent discard trigger on
  Sangromancer, full target-choice and priority handling.
- **True battle objectives:** player attacks/blocks both ways, enemy mana,
  hands, libraries, full action legality, combat damage details, lethal
  damage/elimination, APNAP stack and response policies.

These should be implemented by extending typed primitives, registered
source rules and tests, not card-specific gameplay loops. Until those
pieces exist, bracket/win-rate claims are unsupported.

## Reproduce

```sh
python run_all_tests.py
python -m unittest tests.test_opponent_stress tests.test_composed_upkeep tests.test_reviewed_enter_effects -v
python tools/run_mortarion_opponent_stress.py --seeds 24 --turns 10 --output mortarion-opponent-stress.json
```

CI: `Mortarion physical opponent stress and narrative audit`. Its artifact
contains the exact summaries and per-turn narrative samples for every
scenario, preserving seed, opponent role, life and reviewed action events.
