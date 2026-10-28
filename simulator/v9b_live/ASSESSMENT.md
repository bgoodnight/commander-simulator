# V9b review — October 28, 2026

## Outcome

Live card-zone migration is installed for all four seats. One `IndexedKernel`
owns physical cards from deck construction through draw, hand, command, stack,
battlefield, graveyard and exile. Read-only pilot projections replace legacy
mutable card inventories. This finishes the live-zone gate described in v9a;
source-backed mana and general stack priority are separate unfinished gates.

Rollback point before this milestone: `e008778493d9ad93a9a534509e015caf17fe39a8`.
The implementation is under `v9b_live`; v3–v7 and v9a sources are unchanged.
The existing v8 shared stack receives two optional live-action existence checks,
so a spell removed when its owner leaves cannot subsequently resolve. V8's
`MANIFEST_SHA256.json` is retained as the original v8 checkpoint manifest;
`v9b_live/MANIFEST_SHA256.json` records the current changed files.

## Validation

- All 188 historical tests pass; 34 new tests pass: **222 total**.
- **400 twelve-round games**, seeds 0–99 in each Magnus seat, rotating three
  opponent groups, passed physical-card conservation and zone/view consistency.
  No execution-safety stops occurred. A surviving detailed seat retains exactly
  100 nontoken cards; each synthetic seat retains 99. Eliminated seats retain zero.
- Four reproducible narrated diagnostic games passed the same checks. Their
  records and transcripts are beside this assessment; one has a forced opening.
- Tests cover mulligans, immutable projections, real stack/graveyard timing,
  permanent adoption, counters/counter-counters, commander tax/death/recast,
  bounce, tokens, cleanup state-based deaths, fetch sacrifice/search/shuffle,
  Brainstorm returns, Frantic Search discards, excess-hand discards, unsupported
  actions, fabricated costs, elimination with pending spells and safety stops.

Reproduce with `python run_all_tests.py` and
`python simulator/v9b_live/validate.py`. Exact sweep/timing data are in
`validation_results.json`. These are engineering diagnostics, not statistical
deck-power validation.

## Efficiency review

The recorded 40-seed ten-round timing medians are **8.716 ms for v9a** and
**39.905 ms for v9b** in this local environment (about 4.6x). The migration
allocates all 397 physical cards at construction, changes IDs on zone moves,
builds immutable pilot views and checks the complete registry after actions.
Different legal state transitions also change stochastic game paths.

A separate cProfile inspection of 20 games found complete consistency checks
at roughly 37% of cumulative live run time. Repeated read-view construction and
initial card registration also contribute. Retaining exhaustive checks is an
intentional correctness choice here. This is not evidence that general mana
planning or large Monte Carlo batches are optimized. Incremental membership
checks/cached projections are future options, with independent full audits
retained to detect corruption.

## Edge cases found and corrected

1. Legacy casts placed instants in the graveyard before the response exchange;
   live physical spells now stay on stack until countered or resolved.
2. Permanent resolution previously minted a second battlefield object; the
   live battlefield creation boundary now adopts the physical spell.
3. Truncating a hand silently deleted cards; excess cards now move to graveyard.
4. A counterspell could remain in a frame after its owner left; the shared
   resolver now skips removed live spells.
5. Fabled Passage previously lost track of its sacrificed card and skipped
   shuffle; physical sacrifice, basic movement and shuffle are explicit. The
   tapped condition uses actual land count, and an unfetched Passage cannot
   generate invented mana.
6. Cleanup state-based zone changes now reconcile battlefield views. Commander
   redirects and token cessation update the same ordered zone index.

## Remaining correctness and scope limits

Payment is still the inherited detailed `ColoredPayment` and synthetic fungible
policy. Resource readiness/floating mana are not yet source-ID state; kernel
tap state is not authoritative for mana payments. The isolated `TypedMana`
planner is not installed. Izzet Signet activation, Treasure payment and source
abilities must be migrated together rather than half-attached.

The stack is still counter-only, and cast triggers settle before response
selection. General triggered/activated frames, true priority, several detailed
decks, commander damage, verified spell copies/buyback/loops and broader named
card coverage remain future work. Existing simplified selection, land ETB,
upkeep land play and precombat hand-size timing remain approximations. Synthetic
finishers remain explicitly synthetic, including token clock effects.

Do not infer Magnus win rates from changed replay outcomes. Changes in shuffling,
conservation and land behavior make trajectory differences expected.

## Next gate

Migrate mana-source IDs and payment atomically with tap/untap, floating mana,
Treasure sacrifice and source activation costs. Retain bounded planning and an
explicit synthetic resource policy. Then extend priority/trigger frames before
enabling multiple real decks and additional complex Magnus interactions.
