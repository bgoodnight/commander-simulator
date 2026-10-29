# V14 assessment

October 28, 2026. Land entry conditions/basic types and Passage's activated fetch
are implemented as the approved bounded batch. No additional caching is introduced.

## Observed validation

- **547 tests** passed across fourteen suites, including **56 new land/reference
  tests**. All 491 historical tests remain passing.
- All **seven targeted narratives** passed with actual conserved cards and source
  payments. Shock/type and entry-boundary stories include separate conserved
  branches; forced setups are labeled rather than presented as natural openings.
- **200 twelve-round games**, 50 seeds in every Magnus seat and three synthetic
  opponent groups, passed physical-card, zone-index, battlefield-view, spell-frame
  and mana-pool checks. **No safety stops**.
- The sweep exposed 100,682 steps, 11,013 source payments, 6,899 land entries and
  48 fetch resolutions. Simulation time was 134.781 seconds; total with reference
  serialization/checking was 142.757 seconds.
- Exploratory medians over 12 eight-round samples: v13 EngineTable **430.368 ms**;
  v14 LandTable **549.671 ms**, about **28% higher** in this invocation. Rules,
  source availability, decisions and resulting trajectories differ. This is a
  tracked cost, not an isolated estimate of a particular function's overhead.
  Reference serialization is excluded from these benchmark measurements.

## Interaction results

Read INTERACTION_REPORT.md and the Markdown/JSON story pairs for full evidence.

1. Declining Steam Vents payment left it tapped without life loss. Its types still
   let Sulfur Falls enter untapped and pay for Ponder. Paying for Vents in another
   branch enabled immediate mana at 38 life with zero damage taken.
2. Coast/Canal entry boundaries used other lands, Sanctuary counted Steam Vents
   as an Island, and Training Center counted remaining opponents. Sanctuary's
   graveyard trigger remains explicitly absent.
3. Playing Passage did not fetch. Activating paid tap/sacrifice before responses;
   the source was in the graveyard while its ability waited. An early fetched
   Island stayed tapped, then paid for Ponder after a declared next-turn untap.
4. Three sources paid for Adaptation. Passage's fourth resulting land entered
   tapped, then untapped and immediately paid for Ponder with that exact source ID.
5. Capsize responded to the fetch ability by bouncing another land. The fetched
   basic arrived, but the three-land result failed the untap condition.
6. Explicit fail-to-find produced no land, still shuffled and retained Passage's
   paid sacrifice. The activation neither drew nor cast a card.
7. Passage play/fetch did not trigger Pyromancer. Ponder paid by the fourth fetched
   Island did trigger it, creating exactly one additional Elemental.

Other focused checks cover life affordability/exact payment, forced tapped entry,
nonbasic Islands versus basics, subtype persistence across bounce, Pathway mana
choice, no automatic Passage mana, tapped/foreign-source rejection, no double
activation, opponent-turn priority, ordinary counterspells versus activated frames,
synthetic ability-countering without cost refunds, failed searches/empty libraries,
land-drop accounting, current land counts and immediate source availability.

## Reference and runtime policy

REFERENCE_CASES.json stores **200 versioned deterministic output digests** with
providers, seeds and rounds. reference_state.py hashes canonical object/card/zone
state, player state and turns, RNG state, movements/rules events, source payments,
priority/step/combat history, selection/engine/land decisions and delayed effects.
Timing and cache-hit statistics are excluded. Unit checks verify repeatability,
insensitivity to runtime/cache counters and sensitivity to changed outcomes.
A separate regeneration check reproduced four saved cases exactly, one from every
Magnus seat.

The preserved v13/v14 implementations and normal Git history form the comparison
reference for later optimization. No cached candidate is built now. Existing
historical kernel/mana-planner caches remain unchanged; 'before additional caching'
is the precise baseline description. PERFORMANCE_HISTORY.json retains historical
measurements and this same-invocation comparator. Host load and rule trajectories
vary, so historical medians should not be treated as a controlled benchmark series.
Future caching should match these hashes for unchanged semantics. New rule changes
need a new versioned reference rather than forced agreement with old outcomes.

## Implementation and scope

V14 adds a named metadata provider and LandTable subclass. Entry predicates use
current other-land/type/opponent counts. The common entry path serves land plays
and effect entries while keeping once-per-turn land-play accounting separate.
Passage registers a nonmana tap/sacrifice descriptor with the existing activated
stack; its resolver chooses a basic from the controller's library, enters it tapped,
shuffles and checks the resulting land count. No priority is inserted inside that
resolution. All changes are isolated from historical rules/cache implementations.

The audit advances six partial names: **38 supported subsets, 10 partial, 35
unsupported** distinct names; physical counts are **55/10/35** across 100 cards.
No formerly unsupported named card is enabled. Basic subtypes improve land checks
without treating every U-producing source as an Island. Supported subset is not
full Oracle certification.

Mystic Sanctuary's targeted graveyard trigger, Fiery Islet/Riptide utility abilities,
Otawara/Sokenzan channel, full modal double-faced characteristics, simultaneous
multi-land entry, general control-change/replacement/land-trigger systems and the
previous broader engine limits remain deferred. The ability-counter unit fixture
is synthetic and does not enable a printed Stifle card. One detailed Magnus deck
plus synthetic opponents still cannot support empirical deck-win-rate inference.

Next: Sanctuary's targeted ETB trigger and the remaining utility/channel batch,
then spell copying and relevant creature activations/tutors. Continue tracking
runtime; defer added caching until the intended functionality is established.

Rollback point: a1d4e4263eb79a9dad255b1907606a8477926c31. V14 changes only its
own directory, the test runner and root README. Historical manifests retain their
checkpoint bytes; the new manifest covers current changed files and artifacts.
