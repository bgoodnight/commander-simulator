# V9a assessment — October 28, 2026

## Objective and outcome

Move the v8 shared battlefield architecture forward without creating a second rules engine. The scope is deliberately smaller than the entire v9 roadmap: (1) remove the seat-zero constraint for one real deck in live four-player games, (2) develop kernel-owned ordered card-zone operations separately, and (3) demonstrate typed source-specific mana with bounded cost planning. Earlier engines are untouched.

## Validation

- All **159 historical v3–v8 tests** passed unchanged.
- **29 new v9 tests** passed; **188 tests total** after updating the aggregate runner.
- **400** additional 12-round games: 100 seeds × Magnus seats 0, 1, 2 and 3. All retained v8 battlefield-view consistency and had no execution-safety stop. The smoke sweep is *not* a quantitative deck test.
- Four narrated diagnostic games reproduced their seeded event trajectories; cases include one explicitly forced opening.
- The standard-library single-process median runtime over 40 ten-round games was **17.550 ms for v8**, **18.521 ms for v9 seat 0**, and **19.473 ms for v9 seat 2** on the local runtime. Different stochastic paths and machine load make this an exploratory check only.

## Four game narratives

| Case | Seat for Magnus | Seed | Magnus remaining life | Cards cast | Kernel consistent |
| --- | ---: | ---: | ---: | ---: | --- |
| `01_original_seat` | 0 | 102 | 9 | 9 | Yes |
| `02_right_of_aggro` | 1 | 104 | -1 | 4 | Yes |
| `03_third_seat` | 2 | 103 | 20 | 7 | Yes |
| `04_forced_seat_three` | 3 | 404 | 35 | 8 | Yes |

A negative life total is a legal recorded game-state value after lethal damage, not evidence that an eliminated player remains active.

## Important distinctions

**Live integration:** Portability of the single detailed pilot across seats uses the actual v8 table and existing combat/counterspell kernel. A former hard-coded detailed `land_played` controller value is corrected at the event boundary. Existing seat-dependent random seeds and turn ordering cause expected trajectory differences.

**Standalone, testable abstractions:** `KernelZones` and `TypedMana` are reusable services on the v8 central kernel's `GameObject` registry. They do not replace v6's mutable `hand`, `library`, `graveyard`, commander/pilot state, or land/payment adapter in the live game. Calling them "fully migrated" would be incorrect. Countering a spell in `KernelZones` moves its physical object without invoking its normal resolution; cast and resolution events are separate. Their use in a real live game requires the existing table to route all card and resource transitions through them.

## Remaining significant correctness risks

1. Live deck hands, libraries, graveyards, command and land zones remain legacy data, and multiple real decks cannot coexist yet.
2. Source-backed mana production is tested in isolation. `ColoredPayment` and fungible abstract mana remain in gameplay; exact land abilities, Treasures, alternative costs, and floating mana are not migrated.
3. Live stack remains counter-only. Cast triggers still settle early; there is no general priority for spells/abilities and triggers on stack.
4. Physical battlefield transitions performed by a standalone `KernelZones` service are not automatically projected into v8's `Battlefield.views` (the service has no such connection). Never attach it to live `V9Table.rules` before that bridge exists.
5. Many named cards in the actual Magnus deck remain unsupported. Buyback, scry, copying, tutor and combo cases must not be assigned outcomes without explicit validated rules.
6. Isolated mana planning is fail-closed when its search exceeds a configurable state budget, but the current DFS has exponential worst-case cost. Memoized solver or constrained payment algorithms will be needed before full deck integration.
7. Older scripts may still label the first detailed player's land plays as P0 when not run through v9's event/report adapter. Generated v9 narratives use the corrected seat labels.

## Recommended next iteration (v9b)

Make a `ZonePlayer` / `DeckProvider` constructor that populates the shared kernel directly; migrate draw and mulligan first, then discard/search/land placement, then spell-stack object movement. All legacy Python cards must become read-only projections, never a second authoritative list. Ensure new spell objects resolve to the battlefield *and* v8 `WorldEntry` projections consistently. Only after testable cleanup of these mutation paths should two real named decks be enabled. Then adopt one source-specific mana policy for both kinds of deck (with explicit abstract policy where still approximate), and after that generalize trigger frames and priority.

## No deck-power conclusions

These games and timings cannot support a win-rate estimate, deck recommendation, or assertion that named-card interactions are complete. Fail-closed classifications take precedence over apparent wins.
