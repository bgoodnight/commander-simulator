# V13 — exact selection and missing live engine text

October 28, 2026. This batch upgrades six existing selection effects and four
engine cards, plus the missing Archmage Emeritus copy-event descriptor. It does not enable previously unsupported named cards. V12 combat,
shared zones, source-ID mana and four-seat priority remain active.

## Added behavior

| Card | Implemented behavior | Interaction boundary |
|---|---|---|
| Brainstorm | Draw three, then choose two from the whole hand and put them on top in chosen order | No priority between draw and put-back; failed draws still complete remaining instructions before SBA |
| Ponder | Look at three, order them, optionally shuffle, then draw | Short libraries, deterministic shuffle and explicit shuffle choice |
| Preordain | Scry two with ordered top/bottom choices, then draw | Bottoming every looked-at card can expose an unseen next card |
| Telling Time | Look at three; one to hand, one on top, one on bottom | Follow instructions in order for fewer than three; putting into hand is not drawing |
| Impulse | Look at four; choose one to hand and order the rest on the bottom | No draw or shuffle; empty library by itself does not lose the game |
| Frantic Search | Draw two, explicitly choose/discard two, untap up to three lands | Upgrades v11's default-only discard selection; same atomic resolution and land-only untap |
| Harmonic Prodigy | Prowess until cleanup, plus corrected trigger doubling | Its own Wizard prowess is not self-doubled; another Prodigy doubles it; a self-Shaman can qualify |
| Storm-Kiln Artist | Dynamic +1/+0 for each controlled battlefield artifact | Counts Treasure and artifact creatures, changes immediately on sacrifice; magecraft descriptors retained |
| Baral | Optional draw/discard when a controlled spell or ability actually counters a spell | Successful spell counters only; Harmonic doubles separate optional triggers; fizzling is not countering |
| Archmage Emeritus | Magecraft draw descriptors for casts and copies | Copy-event behavior is synthetic-event tested; no live copy producer enabled |
| Stormsplitter | Copiable-base tokens with their own triggers and next-end-step exile | Correct Otter/Wizard type; copies omit counters/pumps/tap state; queued trigger uses last-known base if source left |

## Resolution choices and state

Selection operates on the authoritative ordered library ID index. Storage is
bottom-to-top; all policy orders are top-first. Looking/reordering does not create
new objects. Moving cards between library/hand/graveyard uses normal fresh object
IDs. Policies receive immutable CardOption/SelectionRequest values containing only
the relevant looked-at or hand cards. They choose; they do not take game actions.

Set selection_policy(request) for explicit choices. Ordinary requests return the
required ordered tuple of object IDs. Scry returns a dictionary with top and
bottom tuples partitioning the looked-at IDs. Ponder's shuffle request returns a
boolean. Default choices use a deterministic, simple development heuristic.
Wrong counts, duplicates, foreign IDs and invalid partitions are rejected at the
choice point. This is not a transactional rollback of an already resolving spell.
Set loot_policy(controller, source_id) to accept/decline each optional Baral trigger.
The existing frantic_untap_policy remains available.

Cast triggers and counter-generated loot use the same LIFO stack and APNAP
placement as other abilities. Delayed exile is a separate registered trigger,
not an ability of the token, so Harmonic does not double it. At end-step beginning,
due triggers queue before priority. Tokens made after that beginning wait for the
following end step, including another player's. A countered exile trigger is not
retried at cleanup or subsequent end steps. No printed Stifle card is enabled by
that synthetic unit-test fixture.

Storm-Kiln power is derived by a generic self-bonus descriptor in the kernel. The
pilot projection refreshes at priority checkpoints. Actual combat/cost queries
read authoritative objects, including immediately after an artifact leaves.

## Validation

From the repository root:

```bash
python run_all_tests.py
python simulator/v13_engines/coverage_report.py
python simulator/v13_engines/validate_engines.py
```

There are **491 tests across thirteen suites**, including **69 new checks**.
The validator writes seven narratives (the selection story has five independently
conserved branches), corresponding JSON payment/selection/stack records, and a
200-game twelve-round sweep across all Magnus seats. Timings compare 12 eight-round
samples per engine. Read [INTERACTION_REPORT.md](INTERACTION_REPORT.md) and
[ASSESSMENT.md](ASSESSMENT.md).

[CARD_COVERAGE.md](CARD_COVERAGE.md) and JSON now classify 83 distinct names as
**32 supported subsets, 16 partial, 35 unsupported**. Physical counts with repeated
basics are 49/16/35. Nine names moved from partial; supported subset never means
full Oracle certification. Historical audits and tests remain available.

## Limits and next work

No live spell-copy producer, draw/scry trigger or replacement-effect system,
general copy-effect layers, or full legend/Commander rules are added. Magecraft's
copy-event descriptor is tested with a synthetic event; it does not claim that
Twincast/Reiterate already work. The copy implementation is the declared
Stormsplitter base-characteristic case. Unsupported effects remain excluded from
legal casts. Default pilots are heuristic rather than optimal.

Special-land entry/utility abilities remain the next P1 gap. Copying, relevant
creature activations/tutors, graveyard casting and validated combos follow.
One detailed Magnus deck and three synthetic opponents remain the table model.
No deck-power or win-rate inference is supported.

V12 rollback point: d15da6c9ee641b4743c916ab39ff591bd0e9d4f8. Shared changes add
only descriptor-driven power/self-exclusion and counter-controller event plumbing;
old descriptors retain their previous behavior. Historical manifests record their
original checkpoint bytes. V13's manifest records the current changed files.

## Rule references

- [Strixhaven release notes](https://media.wizards.com/2021/downloads/STX_Release_Notes/EN_MTGSTX_FAQ_04122021.pdf): Brainstorm's atomic resolution and magecraft.
- [Modern Masters 2015 notes](https://magic.wizards.com/en/news/feature/modern-masters-2015-edition-release-notes-2015-05-12): Telling Time and short libraries.
- [Time Spiral Remastered notes](https://media.wizards.com/2021/downloads/TSR_Release_Notes/EN_MTGTSR_FAQ_20210118.pdf): Baral's counter requirement and distinction from illegal-target failure.
- [Commander Masters notes](https://media.wizards.com/2023/downloads/CMM_Release_Notes/EN_MTGCMM_ReleaseNotes_20230616.pdf): Storm-Kiln Artist's artifact bonus and magecraft.
- [Bloomburrow notes](https://magic.wizards.com/en/news/feature/bloomburrow-release-notes): Stormsplitter's token base, last-known values and delayed exile.
- [September 25, 2026 Comprehensive Rules](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.pdf): ordered libraries, draw/SBA timing, scry, prowess, delayed triggers and copiable values. Local card-provider metadata supplies the declared card subset; this is not a fresh all-card Oracle audit.
