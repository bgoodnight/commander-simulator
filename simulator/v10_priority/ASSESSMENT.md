# V10 priority assessment — October 28, 2026

## Outcome and preservation

V10 uses one typed LIFO stack for physical spells, triggered abilities and
registered activated abilities, with a four-seat priority loop. The old
counter-only resolver is not active in these games. V9c source-ID payment and
v9b physical zones remain authoritative; no second card or mana inventory is
introduced. Card-specific activations are declared outside the generic stack.

The rollback point is `e66c06f7526802ea1b60db38d73bd416923f8c90`. V10 adds a new
directory and an optional excluded-source argument to the existing mana planner.
That argument reserves sources that must tap/sacrifice for nonmana activation
costs. Its default is empty, preserving standalone v9c payment behavior. All
271 historical tests pass; previous milestone manifests remain checkpoint
records, and this milestone hashes current changed files and diagnostics.

## Validation

- **322 tests across ten suites pass**, including **51 new v10 checks**.
- **400 twelve-round games**, seeds 0–99 in all four Magnus seats and three
  rotating opponent groups, passed conservation, zone/view, mana and physical
  spell/frame consistency checks. There were **no safety stops**.
- The sweep exercised **20,437 spell/counter payments**, **58,362 source mana
  activations**, **1,395 resolved triggered frames**, **11 resolved nonmana
  activated frames** and **218,373 priority passes**. Maximum stack depth was
  **11**. The mana planner's peak successful search visited **4,228 states**.
- Four reproducible narrated games include machine-readable priority histories;
  one opening is explicitly forced. Fizzled objects are distinguished from
  successful resolutions in the histories.
- Acceptance cases cover APNAP placement/controller ordering, separate doubled
  triggers, full consecutive pass cycles, pass resets, actor-retained priority,
  active-player priority after each resolution, offturn instants/activations,
  newly drawn instant responses, source-independent abilities, stale targets,
  counters below triggers, counter/counter-counter exchanges and ability counters
  with explicitly synthetic registered fixtures.
- Mind Stone tests cover cost reservation, other-source funding, tap/sacrifice
  before responses, source-independent draw and the distinction between an
  activation and a spell cast. Unsupported operations and malformed policies
  fail closed. Guard tests retain unresolved results rather than forced losses.

Reproduce with `python run_all_tests.py` and
`python simulator/v10_priority/validate.py`. `validation_results.json` records
exact counts and local timings. `--narratives-only` regenerates the four replay
pairs without replacing the recorded sweep report. These checks do not establish
real Commander win rates or complete printed-card correctness.

## Bugs and boundary fixes found

1. Cast triggers previously resolved before responses. They now become separate
   queued frames after state-based actions and APNAP placement; opponents can
   respond before the effects occur.
2. The old resolver chose one counter per top and drained the chain. V10 waits
   for each living player to pass, resolves one object, then reopens priority.
3. Counter/removal targets that left or changed zones previously risked normal
   resolution/rider effects. Stable frame/object IDs and resolution-time target
   checks now fizzle those objects without normal effects.
4. A player reaching zero life during payment could lose their physical spell
   before its newly created frame was pruned. A cast-completion SBA checkpoint
   now removes departed players' frames before priority or consistency checks.
   The issue was found in the larger sweep and has a targeted regression test.
5. Mind Stone cannot generate the one mana for its draw ability and then pay
   the same tap cost again. The planner excludes its reserved source; sacrifice
   occurs as a cost, and its independent activated frame later draws the card.
6. Trigger ordering policies are validated before consuming waiting triggers.
   Rejected orders cannot silently delete queued abilities or substitute forged
   frame data. State-based waves finish before waiting triggers are placed.
7. Hand-size cleanup was moved out of the main phase into the exposed end/cleanup
   boundary, retaining the historical discard preferences.

## Efficiency review

The recorded local medians over 40 ten-round games were **89.881 ms for v9c**
and **200.630 ms for v10** (about 2.2x). The 400-game sweep took 89.741 seconds.
Machine load and changed legal trajectories limit direct comparisons; this is
an exploratory diagnostic, not a performance guarantee.

Priority requires many more legal-choice/source queries and checkpoints than a
single counter-chain window. Existing source-signature caches/grouped planning
remain in use. Priority actions/passes, repeated SBA checks, stack depth, object
count and overall actions/time are bounded. Performance work should profile
choice/projection caching while retaining independent full state audits.

## Remaining correctness gates

The shared priority layer is operational for implemented effects; it does not
supply every timing window. The driver still combines upkeep/draw/land development
and serializes combat rather than exposing every official attack/block/damage
step and response opportunity. Cleanup timing is improved but not a complete
step-state machine.

Only the current named trigger/effect subset and Mind Stone's added nonmana
activation are live. Other activations require explicit registered descriptors
and supported operations. Creature tap abilities, arbitrary activation cost
choices, intervening-if conditions, delayed/meta-triggers and comprehensive
mana replacement/prevention/triggered effects remain unsupported. Source
reservation is conservative for descriptors with sacrifice-only costs; no claim
of arbitrary cost-sequencing coverage is made.

One detailed deck only. Selection/scry and some land/utility behavior remain
approximate. Other mana colors/cost forms, commander damage, copies, buyback and
verified Magnus loops are still incomplete. Synthetic opponents and finishers
remain declared approximations. Default priority choices are bounded heuristics,
not optimal play. Do not draw deck-power conclusions from changed trajectories.

Next: a finer phase/step and combat driver, broader verified effect/activation
coverage, then several detailed decks.

## Rules references consulted

Official [Comprehensive Rules effective September 25, 2026](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.pdf):
117.3–117.5 (priority, passes and checkpoints), 603.3 (APNAP trigger placement),
113.7a (source-independent abilities), 601/602 (casting/activation), 605.3 (mana
abilities), and 608 (resolution/targets). The limited Mind Stone descriptor is
separate from the generic stack; it does not mark the entire deck fully covered.
