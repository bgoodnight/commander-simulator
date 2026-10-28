# V13 assessment

October 28, 2026. Exact selection and the focused live-engine text batch are
implemented on the v12 rules/priority/combat foundation. Nine partial names move
to supported subsets; no formerly unsupported named card is enabled.

## Validation results

- **491 tests** passed across thirteen versioned suites, including **69 new
  v13 checks**. All 422 historical tests remain passing.
- Seven source-paid narratives passed. The first has five separately conserved
  branches for Brainstorm, Ponder, Preordain, Telling Time and Impulse.
- **200 twelve-round seeded games** across every Magnus seat and three synthetic
  opponent groups passed physical-card, indexed-zone, battlefield-view, spell-frame
  and mana-pool checks. **No safety stops**.
- The sweep exposed 100,652 steps, 10,948 source payments, 454 selection-choice
  records and 234 engine events. Sweep elapsed time: 110.341 seconds.
- Exploratory median milliseconds per eight-round game over 12 samples/engine:
  v12 CombatTable 331.252; v13 EngineTable 448.467, about 35% higher. Additional
  choices/triggers and dynamic-power projection checks add work; changed game
  trajectories also affect the comparison. No wall-clock guard fired. This is
  a recorded performance cost, not evidence for a deck-power change.

The later Archmage copy-event descriptor is tested with a synthetic copied-spell
event. No live copy producer exists, so it does not change natural-game trajectories
or the recorded sweep's events. It closes an adjacent metadata gap before the
future spell-copy milestone; it does not enable Twincast or Reiterate.

## Observed interactions

1. Exact look/draw choices selected Abrade in all five selection branches, while
   preserving requested top/bottom order. Telling Time/Impulse put into hand
   without drawing; Brainstorm/Ponder/Preordain perform their actual draw sequence.
2. Harmonic gave itself one prowess pump per noncreature cast, not two. Its
   Pyromancer doubling worked before Adaptation; Iconoclast doubled after Wizard
   types applied. Four Elementals/four Soldiers resulted; the three prowess pumps
   expired in cleanup.
3. Artist went from 4 to 7 power as artifacts entered, immediately to 6 when an
   actual Treasure was activated for U, then to 9 after that mana paid for
   Preordain and its artifact-creating triggers resolved.
4. Counterspell actually countered a spell; Harmonic produced two optional Baral
   triggers. One loot was accepted and one declined independently.
5. With Harmonic, two casts produced 2 then 6 additional Stormsplitter tokens.
   Exactly eight delayed exile abilities queued at the next end-step beginning;
   Harmonic did not double those delayed abilities. Tokens left on resolution,
   not at cleanup.
6. An instant cast during end-step priority created a token after that beginning.
   It survived cleanup and expired at the following player's end step.
7. A pumped Stormsplitter was bounced with older copy triggers waiting. Tokens
   still entered with base 1/4 copiable values, using last-known values when the
   source was gone; counters, pumps and tapped state were not copied.

The tests also cover shorter/empty libraries, scry partitions, selection privacy,
invalid choices, no priority during resolution, Frantic discard choices, other
Prodigies/self-Shaman qualification, cast-trigger survival through countering,
artifact creatures/opposing artifacts, dynamic combat power, source-independent
loot, counters from a registered synthetic ability, countered counterspells,
illegal-target failure versus countering, delayed exile countered or with its
object gone, copying without cast-only triggers, all-seat conservation and
reproducible live games.

## Architecture and rules boundaries

Selection uses the authoritative ID-only library index, not a duplicate deck.
Reordering preserves identity; zone movements create fresh IDs. Immutable requests
expose only the relevant looked-at/hand options. Explicit policies choose ordering,
scry partitions, shuffle, discard and optional loot. The default pilot remains a
simple deterministic heuristic. Invalid policies fail at their choice point;
prior completed instructions of a resolving spell are not rolled back.

The generic kernel adds descriptor-driven controlled-type power and a descriptor
flag for excluding a doubling source's own Wizard trigger. Older descriptors keep
their old behavior; only v13 named metadata opts into the corrected text.
Successful stack counters now carry the countering controller through a separate
event. This covers both spells and registered counter abilities without treating
fizzles or countered triggered abilities as countered spells.

Stormsplitter tokens use copied base descriptors with the correct Otter/Wizard
subtype and their own cast triggers. End-step serials schedule separate delayed
exile frames before priority; cleanup no longer expires these tokens. Last-known
copiable descriptors survive source departure. The implementation is a bounded
copy subset, not a general layer engine.

General draw/scry triggers, replacement effects, live spell-copy producers,
comprehensive copiable-value/layer changes, full legend/Commander rules and
special-land entry/utility text remain outside the batch. Magecraft copy-event
plumbing is tested synthetically; no printed copy spell is claimed live. Other
v12 combat/card limits remain. One detailed deck plus synthetic opponents still
cannot support empirical win-rate or card-power inference.

## Coverage and next triage

The current audit classifies 83 distinct names: **32 supported subsets, 16 partial,
35 unsupported**. Repeated basics make physical counts **49/16/35** across 100
cards including the commander. Supported subset is not full Oracle certification.
The v12 audit remains preserved as a historical checkpoint.

Next P1: special-land entry/utility behavior. Then prioritize spell copies and
relevant creature activations/tutors, followed by graveyard casting, broader
replacement/layer support and verified combos. Keep source-paid interaction
narratives, independent consistency checks and measured runtime limits.

Rollback point: d15da6c9ee641b4743c916ab39ff591bd0e9d4f8. Historical manifests
retain their original bytes; the v13 manifest covers the current changed files.
