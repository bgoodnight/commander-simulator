# Pilot development plan — player decisions and abstract opponents

Updated: 2026-11-02. This is a **decision-policy** track for the bounded
physical runner, not a rewrite of the rules kernel and not a head-to-head
Commander-deck implementation. Maintain this plan separately from the UI and
shared-rules branches.

## Starting point (main)

- The eight pinned deck variants run the same reviewed physical legal-action
  generator and deck-derived `pilot_policy.choose_legal_option` scorer. Five
  styles exist: `adaptive`, `balanced`, `engine`, `tempo`, `conservative`.
- Deck signals come from verified Oracle identities and actual deck quantities,
  not a commander-name whitelist or unreviewed effect execution.
- Main-phase selections record factors, score, source, kind, and candidate count.
- Responses, utility activations, tutor targets, sacrifice payments and combat
  have distinct, partly rule-based selectors in `resource_pilot.py`,
  `early_game_runner.py` and `opponent_stress.py`.
- Opponents are **three bounded abstract pressure seats** with seed-shuffled
  aggro/control/value/combo roles, finite libraries and interaction budgets,
  real creature objects, limited blocking and combat, and some reviewed trigger
  interactions. They do not draw/play actual 100-card Commander decklists.

## Unchanging boundaries

1. The kernel and reviewed handlers establish actions, timing, targets,
   affordability, permissions and payments **before** policy ranking.
2. The pilot cannot cast a missing effect, assume unverified text is executable,
   target hidden information, invent a spell, or bypass priority/restrictions.
3. One general policy architecture across decks; adaptation uses observed
   position, verified deck composition or explicit style, **never commander
   identity**. Use a named-card exception only for a rules handler whose
   specific Oracle ability requires it, not for a pilot.
4. Separate rules correctness from choice quality. Label every decision or
   opponent event with its actual fidelity. Never present abstract simulated
   matches as measured human multiplayer win probability.
5. Preserve seed reproducibility and source manifests. Compare batches with
   matched deck hashes, scenario/roles, horizon, seed, provisional rules mode
   and pilot personality. A cohort UI fix is being reviewed in PR #40.

## P1 — initial improvement on this branch

**Implemented for review:**

- Do not score a legal non-mana artifact as the generic `other` role.
- Let the shared player `pilot_style` choose a bounded combat attack cap and
  defensive reserve. `adaptive` responds to verified combat density;
  `tempo` presses, `conservative` reserves, and `engine` preserves
  creatures under pressure where spell/sacrifice signals are dense.
- Make the limited control/value opponent attack selection prioritize capable
  legal attackers rather than physical insertion order.
- Emit an optional `events[t].pilot_combat` record (style, reasons, cap,
  reserve, candidates, selected and target seat) and include it in narrative
  audits. This is **not** a comprehensive combat decision trace.
- Cover scoring, posture, attacker choice and narrative compatibility with
  regression tests.

**Release gate:** all Python/JS regression tests pass on 3.11–3.13 and the
eight-deck, two-seed, twelve-round narrative audit produces valid output.
Inspect at least one turn-by-turn sequence each for Magnus, Mortarion,
Necrons and Wretched Ranks; escalate any unsupported rule behavior as a
separate kernel/card-coverage issue. No main merge before review.

## P2 — unify optional choices

Move remaining ad hoc decisions into **typed legal candidate producers**
with one shared preference interface and reason codes, in this order:

1. Main-phase casting and ramp/ritual sequencing (opportunity cost of mana,
   holding an instant for a live response, and spell-trigger engines).
2. Tutor targets and hand/graveyard resource use (choose a chain only if the
   reviewed sequence is actually reachable and its targets exist).
3. Once-per-turn utility/activated abilities, tokens and sacrifice payments
   (preserve relevant engines; avoid free or repeated unmodeled effects).
4. Response windows to removal/damage, then combat and blocking.

Acceptance: each candidate includes exact legality source, payable costs,
effect-fidelity flags, predicted immediate state impact if reviewed, and a
stable score explanation. Policy can return **pass** when nothing beneficial
exists. Avoid selecting spells only because they were listed first; ensure
deterministic ties without card-name strategy rules.

## P3 — tactical combat/interaction

Use actual legal blockers, P/T, tapped state, known evasion, live threats,
life totals and open resources to evaluate attacks and blocks. Preserve key
engines where sacrifice is not profitable, recognize lethal or favorable
trades, and decline obviously poor exchanges when not under lethal pressure.
Do not claim modeling of first/double strike, trample, stack tricks,
prevention or commander combat damage until corresponding rules are verified.
Maintain scenario fixtures for one good attack, one defensive hold, one
profitable trade and one refused action.

## P4 — improve abstract opponents without impersonating full decks

- Factor opponent threat, combat targets, blockers, removal targets and
  constrained action budgets through shared observable-state utilities.
- Keep aggro/control/value/combo profiles explicit **stress strategies**;
  actor selection must be seat-neutral, including attacks on other opponents.
- Record for each abstract opponent action its actor, eligible targets,
  strategic reason, resources/budget and `abstract` fidelity label.
- Calibrate seat balance, targeting diversity, pressure timelines and removal
  frequency with repeatable scenario/seed tests. Don't tune solely to make the
  physical pilot win more or less often.
- Only after M2/M3 rules cover both sides should a **separate optional mode**
  allow actual imported opponent decks using the same physical pilot.
  Never silently promote abstract pressure events to real spell casts.

## P5 — narrative evaluation and performance comparisons

Run matched-seed cohorts across all eight pinned variants, four pressure
scenarios plus goldfish, and the five styles as affordable. Record:

- Missed land drops and legal-but-unselected ramp; wasted unspent mana when
  useful legal actions existed; casts by turn; hand overflow/discards.
- Card draw, tutor chains, key engines deployed, recursion and token/sac
  resource usage; how often an action was unavailable because its effect
  was unimplemented.
- Combat attackers committed vs eligible, favorable trades, survival,
  actual life by seat, player/opponent eliminations and missed safe lethals.
- Opponent action frequency, per-seat target distribution, remaining
  interaction budget and attacks by role.
- First consequential decision per seed with alternatives, policy reasons,
  rule-fidelity caveats and a narrated turn/replay link.

Primary correctness gates: reproducibility, verified legal candidates,
zone conservation, no invented actions, no unsupported combat claim,
no seat-zero favoritism, stable export schema and matched-cohort reporting.
Compare *paired differences* and report uncertainty/small samples rather
than treating a higher modeled win fraction as proof of a better real deck.

## Integration contracts

- Runner: additive `pilot_style`, `pilot_signals`,
  `events[].pilot_decisions` and optional `events[].pilot_combat`.
- Opponent mode: `opponent_scenario`, `opponent_roles`, individually
  labeled `opponent_abstract_*` events and recorded life/zone changes.
- UI is a consumer of exported evidence. It must not infer missing
  actions, silently mix styles/provisional modes, or re-run pilots in JS.
- Concurrent rules and UI branches should cherry-pick/merge independently;
  rebase and rerun the matched regression suite before integration to main.

The first implementation is intentionally small. Full tactical coordination,
real opposing deck pilots, and calibrated win probabilities remain **open**.
