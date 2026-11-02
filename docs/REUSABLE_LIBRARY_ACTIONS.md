# Reusable library action recipes (M2 import + bounded physical simulator)

**Status:** Implemented as a shared typed action executor with explicitly limited
admission. This is a rules-reuse milestone, not a complete Oracle-text parser,
four-player priority system or validated deck-power model.

## One action container, many registered cards

The kernel is the sole authority for real card IDs, zone moves, deck order,
cast events and source payments. `commander_sim/library_actions.py` accepts
ordered `LibraryAction(kind, count)` values. This is the only executor for
the following newly composed library-action sequences:

| Operation | Arguments | What the shared executor physically does |
|---|---|---|
| `draw` | count 1–7 | Move the actual top cards of the library to hand |
| `scry` | count 1–7; selected bottom IDs, top order | Inspect the exact top cards and reorder/put chosen cards on library bottom |
| `surveil` | count 1–7; selected inspected IDs | Move chosen cards to graveyard as **surveil**, not mill, without shuffling |
| `reorder_top` | count 1–7; ordered top IDs | Rearrange the seen top cards without putting cards on the bottom |
| `shuffle` | explicit Boolean selection | Optionally shuffle the physical library with the seeded RNG |
| `discard` | count 1–7; chosen hand IDs | Discard legal hand cards to graveyard, respecting object transitions |
| `put_back` | count 1–7; chosen hand IDs in top-first order | Put chosen cards on library top, preserving selected order |

Library effects do **not** authorize spell casts on their own. Source-pinned
reviewed wrappers and conservative import profiles own permissions, timing and
mana payment. All steps are recorded in JSON with cards actually seen/moved.
There is no synthetic hand or artificial mana.

Examples of parameter-only card mappings:

| Card and context | Registered action recipe | Remaining limitation |
|---|---|---|
| Ponder · hand cast | `reorder_top(3) → shuffle(optional) → draw(1)` | Bounded card-selection policy |
| Preordain · hand cast | `scry(2) → draw(1)` | Bounded card-selection policy |
| Consider · hand cast | `surveil(1) → draw(1)` | Bounded card-selection policy |
| Brainstorm · hand cast | `draw(3) → put_back(2)` | Bounded card-selection policy |
| Faithless Looting · hand cast / reviewed flashback | `draw(2) → discard(2)` | Flashback uses separate reviewed permission and exile replacement |
| Quick Study / Think Twice · hand cast | `draw(N)` | Think Twice flashback still needs its own explicit review |
| Viscera Seer / Woe Strider · sacrifice activation | `scry(1)` | Costs/timing remain in reviewed sacrifice engine |
| Ayara / Yawgmoth · sacrifice activation | `draw(1)` | Costs/targets remain in reviewed sacrifice engine |
| Hidden Grotto · land enters | `surveil(1)` | Additional funded mana mode remains independently unsupported |

The default bounded policy uses only the current pilot's hand, battlefield
and the cards **legally revealed by the operation**. It makes a basic land
development decision. It is deterministic for a fixed seed and deliberately
not presented as an optimal Magic pilot. Higher-quality card evaluation can
be added by passing a `select(kind, available, count, zones, seat)` callback
without changing source verification or zone mechanics.

## Automatic functionality on new import

With `provisional_mode="safe"`, an exact *complete* card-text sentence can
compile into a `library_sequence`, for example:

- `Scry 2, then draw a card.`
- `Surveil 1.` followed by `Draw a card.`
- `Draw two cards, then discard a card.`
- `Scry 1.` or `Surveil 2.`

These are strict, stand-alone patterns; additional mandatory clauses, reminder
text, overloaded or alternative costs, targeting, replacement effects, and
complex trigger timing do not become executable just because the text looks
similar. Cards such as Preordain and Consider that contain extra reminder text
require their exact reviewed registrations. The unchanged strict default
(`provisional_mode="off"`) remains available for historical comparisons.

The import audit now exposes each recognized sequence as structured action
arguments. The simulation event JSON records the actual step sequence and
object identities on source-paid resolution.

## Measure current coverage

Run:

```bash
python tools/audit_library_recipes.py --all --output /tmp/library-recipes.json
python -m unittest tests.test_library_actions -v
python run_all_tests.py
```

The audit reports *admitted* reviewed hand casts, reviewed flashback, activated
scry/draw, and additional provisional standalone spells separately. It does
not claim an ability was activated in a particular seed, that a card is fully
implemented, or that broad win rates are meaningful. A card included in two
versions counts twice in a per-deck rollup; unique Oracle IDs distinguish
distinct cards. Use seeded physical-trace comparisons for incremental gains.

## Next reusable effect families

Extend **the same typed action recipe principle**, not card-name branches:

1. Add configurable land untap, mana/life side costs, and safe post-draw cleanup
   so Frantic Search / other common spell sequences can be modeled accurately.
2. Compose universal triggered-event subscriptions with configurable source,
   victim, ownership, timing and once-per-turn caps; this advances Gisa,
   Mortarion and Necrons through shared death/sacrifice recipes.
3. Add generalized graveyard lookup, reanimation, exile replacement and
   cast-from-zone permission descriptors; leave under-specified combo interactions
   flagged until reviewed.
4. Compose common token and ramp batches while retaining existing real
   counters, mana sources and deck snapshots.

Every new grammar shape requires a positive tested card, dangerous near-miss
rejection and full physical zone/mana conservation tests before promotion.
