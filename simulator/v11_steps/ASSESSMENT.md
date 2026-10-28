# V11 assessment — ordinary steps and focused card interactions

October 28, 2026. The pre-change rollback point is
`a1c3aa774b97708e5e16bd972255365ec82738f0`.

## Added scope

Three previously unavailable named cards are now castable: **Abrade**, **Capsize**
and **Arcane Adaptation** with the fixed Wizard choice. **Frantic Search** gains
its missing untap instruction and atomic draw/discard/untap execution. This is a
small declared batch, not a claim of full deck coverage or every choice of those
cards. The README contains a card-by-card rule/interaction table.

The driver now exposes the ordinary turn's steps, both main phases, legal main-
phase land drops, and priority before attacks, after attacks, after blocks and
after combat damage. Attacks and blocks are declared before damage. All ordinary
combat damage is then applied as one batch before state-based actions and queued
triggers. Empty combats skip blocker/damage steps. Untap gives no priority;
cleanup gives none unless a waiting trigger/SBA window requires a repeat.

Summoning sickness is based on the creatures controlled as the active player's
turn starts. Haste, vigilance, flying/reach, persistent blocked status and
simultaneous damage are covered within the single-blocker, ordinary-damage subset.

## Validation results

- **372 tests pass across eleven versioned suites**: 322 historical checks and
  **50 new v11 tests**.
- Five targeted interaction stories passed, preserving physical inventories and
  paying actual source costs. Starting boards/cards are deliberately forced and
  explicitly labeled. Two additional unforced seeded games have full transcripts.
- **200 twelve-round games** (50 seeds in each Magnus seat, rotating three
  opponent groups) passed card conservation, zone/battlefield projections,
  physical spell/frame consistency and mana-pool checks. **No safety stops**.
- The sweep visited **99,302 exposed steps**, **3,937 combat damage batches** and
  **10,692 source-backed payments**, with **220 expansion-rule events**.
- The exact machine-readable results are in `validation_results.json`; the
  concise observed interaction results are in `INTERACTION_REPORT.md`.

### Observed narratives

| Story | Observed outcome |
|---|---|
| Abrade modes, two separate conserved boards | Creature mode recorded 3 damage; artifact mode destroyed its announced ramp target. These use separate boards because Abrade is a singleton. |
| Capsize/buyback | A successfully resolved bought-back cast returned to hand. The next bought-back cast was countered and went to graveyard. |
| Adaptation + Harmonic + Iconoclast | Iconoclast became a Wizard. Preordain and responding Capsize each queued two Soldier triggers (4 total); bouncing Adaptation did not remove those queued triggers. A later Ponder made only 1 Soldier. |
| Frantic Search | Drew 2, discarded 2, untapped 3 actual lands. A subsequent Young Pyromancer payment reused an untapped source ID. |
| Response after blocks | Capsize bounced the declared blocker. The attacker remained blocked and dealt no player damage without trample. |

Tests additionally cover invalid mode/type targets, indestructible, accumulated
creature damage, buyback fizzling and countering, generic reductions applied after
buyback is added, colored-pip floors, land/token bounce, additive type effects in
all declared zones, removing an enchantment's continuous effect, opponent-land
untapping, nonland exclusion, no mid-resolution priority, both main phases,
no untap/ordinary-cleanup priority, one land across both mains, damage cleanup,
new-creature versus haste attack legality, flying/reach, blocked status after
removal, two simultaneous creature trades and simultaneous lethal player damage.

## Bugs found while integrating

1. Legacy creature artifacts can have a `Permanent` view and a separate creature
   projection with the same physical ID. Combat now obtains the creature view
   rather than assuming every battlefield entry is a `Creature` instance.
2. Real instant responses can remove synthetic combo setup before the finisher
   resolves. The old synthetic resolver raised an unknown-mode exception when
   setup was lost. It now produces no elimination and records setup loss.
3. The old pilot selected one default utility target, which could strand a legal
   own-target interaction. V11 exposes legal mode/cost/target choices for the
   new instants, including own permanents; default AI still avoids deliberately
   bouncing or destroying its own board.
4. The old attack-age check used a shared round number. The new per-turn ready
   set distinguishes creatures controlled at turn start from creatures entering
   later in the same multiplayer round.

## Efficiency and reproducibility

The recorded local medians over 20 eight-round games were **152.606 ms for v10**
and **308.300 ms for v11** (about 2x). The 200-game sweep took 92.999 seconds.
More priority windows, extra legal choices and second-main development change
both work and stochastic trajectories; this is not a controlled speed or power
study. Keep full audits while profiling source/choice/projection caching.

Reproduce from repository root:

```bash
python run_all_tests.py
python simulator/v11_steps/validate.py
```

`--narratives-only` regenerates the seven story/replay pairs without replacing
an existing sweep record. Assertions in the stories check their stated outcomes.
Earlier versions remain runnable. Shared changes are backward-compatible seams:
optional announced-action input, additive derived subtype queries and configurable
trigger-operation sets. Old manifests remain dated checkpoints; V11's manifest
hashes the current changed files and outputs.

## Remaining boundaries

One detailed deck only. Combat supports one blocker per attacker, not multiple
blocker ordering, first/double strike, trample, deathtouch/lifelink or attacks on
planeswalkers/battles. Control-changing effects are not added. The ordinary-step
sequence does not imply extra/skipped turns, all replacement effects or every
special combat rule.

Arcane Adaptation exposes only the declared Wizard choice and an additive subtype
effect, not a complete continuous-effect layer system. Capsize has buyback; other
buyback/copy/loop cards remain gated. Some existing named creatures/triggers and
selection effects are still subsets. Auras, Equipment, planeswalker loyalty,
commander damage and several real decks remain future work.

Fabled Passage and several land abilities remain adapters without every activation
window. Temporary-token expiry is still handled at cleanup, not a comprehensive
delayed end-step trigger implementation. Other colors/cost forms and general
prevention/replacement effects remain unsupported. These are engineering
narratives, not empirical Commander win rates or deck recommendations.

## Primary rules references

[Comprehensive Rules, September 25, 2026](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.pdf):
302.6 (summoning sickness), 500–514 (turn structure), 508/509 (declarations and
priority), 509.1h (remaining blocked), 510.2 (simultaneous damage), 601.2b/f–h
(modes/additional costs/reductions), 702.27 (buyback), and the existing
priority/target/zone primitives.

Official [Ixalan release notes](https://magic.wizards.com/en/news/feature/ixalan-release-notes)
cover Arcane Adaptation's scope across creatures, spells and owned cards.
Official [Dominaria Remastered release notes](https://magic.wizards.com/en/news/feature/dominaria-remastered-release-notes)
confirm Frantic Search's resolution order and untargeted choice of up to three
lands, including opponents' lands. Card data/costs are explicit provider metadata;
no rules text is fabricated for unsupported cards.
