# Four-seat physical-kernel / historical AI integration (alpha)

This branch combines the **old seven-archetype 99-card abstract deck recipes**
and priorities with the **current IndexedKernel / LiveZones / KernelLife /
TemplateManaService**. A single authoritative physical zone and object registry
now owns all four active seats. The same source-paid generic mana planner
operates on each seat's individual physical land and ramp IDs.

## What genuinely works

- Four independent 99-card abstract libraries, actual opening hands and draws,
  independent discard/graveyard/hand/land/permanent zones, full owner IDs
- Four-seat round loop with randomized seat order, per-seat untap, land play,
  bounded main-phase actions, combat and life-zero elimination
- Source-ID mana payments: no opponent can tap another seat's mana resources
- Common abstract action types supported by their own generic recipes:
  creatures, ramps, engine permanents, physical card draw, physical tokens,
  primitive targeted removal and wipe, burn and synthetic damage finishers
- Shared kernel target and blocker legality, object movement, damage and zone
  conservation checks; a named missing card effect is not silently imported
- Aggro, Control, Combo and Midrange have different *deck mixes / choice
  priorities* and all retain ordinary creatures and mana development
- Deterministic seeds and narrative action/turn-state JSON output

## What it does **not** establish

- **No actual Commander decklist competes in this alpha.** All four decks are
  labelled synthetic categories, not Mortarion / Magnus / Gisa / Necron cards.
- The synthetic costs are generic and colorless. It does **not** claim printed
  colored mana, card oracle effects, stack / priority, counterspells, keyword
  combat, official multiple blockers, protection, real combos or commander
  taxes. Each unsupported kind is omitted, rather than invented.
- 'Synthetic finisher' deals explicitly abstract damage; it cannot be read as
  a card-specific Magic win condition.
- Simple paired combat doesn't execute full rules timing or complete triggers.
- Do not use these results as competitive deck strength, bracket assignment,
  or actual Commander win-rate estimates. No output is published to the UI.

## Architecture

`commander_sim/four_seat_alpha.py` is a **separate experimental driver**;
the existing bounded physical deck engine and production Pages stay unchanged.

`SharedFourSeatTable` creates one set of authoritative objects; it does not
run v5's independent gameplay state alongside a cloned new state.
`AbstractSourceMana` supplies explicit generic mana modes for those objects
to the current `TemplateManaService` source-ID payment search. Physical
`LiveZones.cast` / `LiveZones.resolve` and `KernelLife` handle every
supported action. Different printed-card handling must be reviewed before
using the real DeckFixture loader in this table.

Run tests:
```sh
python -m unittest tests.test_four_seat_alpha -v
```

An isolated GitHub Actions workflow runs 40 games: all 24 seat permutations
of four primary archetypes and 4 mirrors of each primary archetype, with
per-round records stored as artifacts. This is a *smoke test*, not enough
games for narrow confidence intervals or full tier calibration.

## Next integration (avoid hardcoding commander names)

1. Extract the existing `early_game_runner` per-deck pinned identity/zone
   assembly into a `SeatDeckProvider` taking an arbitrary controller and
   registering its own printed 100-card library in this shared kernel.
2. Refactor the source-pinned action chooser to take `seat` explicitly
   rather than assume seat 0. Reuse existing reviewed effect dispatch.
3. Plug color-accurate mana and actual reviewed spell effects into shared
   priority; review triggers and replacement effects from any active seat.
4. Run mirror self-play and rotating four-physical-deck tests. Treat all
   unsupported resolution or nontermination as a separately recorded failure,
   not a deck loss. Only then fit tiers and publish matchup win rates.

This branch preserves the original v5 simulator and PR #69's independent
baseline so regression comparisons are possible.
