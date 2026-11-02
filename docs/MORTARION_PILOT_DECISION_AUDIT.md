# Mortarion physical — pilot decision audit and archetype baseline

Updated 2026-11-02. Scope: locked `mortarion_physical_final` deck,
physical bounded runner and abstract three-opponent stress model.
**Rules coverage and strategic use are not the same claim.**

## Evidence inspected

- `decklists/mortarion_physical_final_v1_0_2026_11_01.txt`: actual 100-card
  mono-black deck. It prominently includes creature sacrifice outlets,
  sacrifice rewards, death triggers, token production, commander life-loss
  conversion, and recursion.
- Source-pinned identity snapshot
  `simulator/card_data/mortarion_physical_final_m1_scryfall.json`: 69 distinct
  named entries. Heuristic deck discovery (NOT executable ability registration)
  finds roughly 20 sacrifice/death mentions, 11 death-trigger candidates and
  12 token-creation candidates. The generic `aristocrats` archetype scores
  above tokens, graveyard and other common plans with these printed traits.
- Previously saved bounded replay
  `docs/deck-lab/replay-data/mortarion-opponent-pressure.v1.json`: 14 sampled
  games over 139 observed rounds (three each for balanced, aggressive, control
  and combo; two goldfish). These are historical replays, **not reruns of this
  new archetype policy**.

Observed player event counts in that saved replay:
- 21 reviewed commander casts, 17 equipment attaches, 13 composed ability
  activations and 2 generic activations.
- **Zero recorded** discretionary sacrifice, precast sacrifice-to-mana,
  reviewed utility activation or temporary reanimation events.
- Ashnod's Altar was present in 40 sampled end-of-round battlefield
  snapshots; Blood Artist in 45, Morbid Opportunist in 12, and Pitiless
  Plunderer in 6. Those counts do **not** prove an affordable or strategically
  profitable activation was legal on any specific turn. In particular,
  the saved sample never had Viscera Seer on the end-of-round battlefield.

Interpret these as **utilization warnings requiring action-by-action replay**,
not proof that all four omitted action families should have fired.

## Confirmed weaknesses from code review

| Decision boundary | Problem before this branch | First change / next work |
| --- | --- | --- |
| Main-phase spell ordering | Shared scorer, but generic base weights ignore sacrifice/death deck plan | Auto derive `aristocrats`; apply role weights only to *already legal* candidates |
| Discretionary creature sacrifice | First matching outlet and cheapest victim could fire even if only scrying and losing a useful body | Select a beneficial reviewed opportunity using real death predicates, once-per-turn usage and victim cost; otherwise pass |
| Fixed global damage | Optional damage-all activation could be selected just because a life-loss-to-token engine existed, without estimating own casualties | Require a positive net board sweep, or a safe engine line with reserves for the eventual end-step X payment |
| Temporary reanimation | Explicit bonus for four named cards, including effects not necessarily executed in this path | Score current legal combat power, toughness, evasion and lifelink; no named-card or unimplemented ETB credit |
| Combat | Separate static cap/reserve rather than deck posture | Existing pilot branch varies attack cap/reserve with personality and observed combat density |
| Opponents | Synthetic pressure policies with bounded budgets, not deck casts | Keep simple and seat-neutral for now; do not tune their behavior to force particular player outcomes |

## Important rule-versus-pilot distinction

The reviewed Whip-like temporary reanimation execution currently moves a real
creature into play, gives haste and applies an exile-at-end replacement, but
does not itself run a generic triggered ETB chain. Improving the pilot cannot
make that unavailable trigger magically execute. Flag this as **effect/host
coverage**, not a reason to privilege particular resurrection targets.

The older `docs/MORTARION_OPPONENT_STRESS_AUDIT.md` explicitly describes
several partial/unavailable printed abilities. An inventory of registered
effects, actual activation legality, and turn-by-turn trigger execution is
required before asserting **all** printed Mortarion cards are fully handled.

## The new decision policy

**Deck inference:** `pilot_policy.infer_deck_signals` derives printed
quantities, and `infer_pilot_archetype` identifies the dominant general
strategy. The style axis (`adaptive`, `balanced`, `engine`, `tempo`,
`conservative`) stays separate from the archetype axis (`auto`,
`aristocrats`, `spellslinger`, `graveyard`, `tokens`, `artifacts`,
`combat`, `control`, `midrange`). Neither confers execution permission.

**Tactical sacrifice:** `pilot_tactics.choose_discretionary_sacrifice`
consumes only actual registered outlet operations, existing battlefield
creatures and reviewed matching trigger predicates. It checks tap readiness,
colored payment, once-per-turn trigger history, available draws, current
life and the cost of sacrificing a token versus a real body. It can **pass**
when the payoff does not justify the cost. The shared physical executor
retains sole authority to sacrifice and resolve triggers.

**Life-loss conversion:** fixed global damage evaluates predicted casualties
before activating. Existing variable-X and end-step policies remain bounded
and should be unified with the action scorer next.

**Outputs:** `pilot_archetype` is additive to run/batch/audit metadata;
`pilot_decisions` records a chosen sacrifice and its realized decision
factors. No new claims of full opponent stack or combat fidelity.

## Immediate next steps (P2)

1. Capture **candidate lists including declined actions** at each relevant
   window. A printed reviewed ability does not prove a legal opportunity:
   record blockers such as tapped source, not enough mana, timing, wrong zone,
   no target, exhausted once-per-turn trigger, life reserve or negative payoff.
2. Move more optional abilities (`reviewed_utility`, equipment, temporary
   reanimation, buyback, graveyard casting and tutor targeting) into the same
   typed utility scoring interface instead of fixed phase-specific ordering.
   Shared targets, payments and effects must remain owned by existing rules.
3. Account for mana opportunity cost, pending commander end-step X,
   number of live death/ETB/spell triggers and favorable sacrifice chains.
   Do not sacrifice a creature to create mana unless an executable payoff
   is actually unlocked.
4. Run paired Mortarion seeds (same pinned deck, opponent shuffle, rules
   mode and horizon) under `auto` vs explicit archetypes and review each
   newly chosen or refused ability. Separate rules bugs from pilot choices.
5. Keep opponent pressure abstract, with finite interaction budgets and
   legal physical blockers. Do not over-engineer opponent pilot personalities
   before the player pilot has coherent effect-based choices.

### Reproduce

```bash
python -m commander_sim.early_game_runner \
  --deck mortarion_physical_final --seed 5 --turns 12 \
  --provisional-mode safe --pilot-style adaptive --pilot-archetype auto

python tools/audit_pilot_narratives.py \
  --deck mortarion_physical_final --seeds 2 --rounds 12 \
  --scenario mixed --pilot-archetype auto --output /tmp/mortarion-pilot.json

python tools/build_game_outcomes.py \
  --deck mortarion_physical_final --seeds 12 --rounds 20 \
  --scenario balanced --pilot-archetype aristocrats \
  --output /tmp/mortarion-aristocrats.json
```

Data-driven tactical policy is a first pass. Validate against actual CI
narratives and do not declare that any particular win rate improved until
matched, reproducible samples have been reviewed.
