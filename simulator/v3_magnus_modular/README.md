# Magnus the Red — modular early-game simulator v3

This is a **partial, explicitly limited Magic: The Gathering simulator** built around the unchanged 100-card Magnus v1.6 deck. It is a research prototype—not a rules engine, win-rate calculator, or competitive AI.

## Files

| File | Responsibility |
|---|---|
| `deck_v16.json` | **Deck membership only**: commander and card counts. Changing this changes which cards can be drawn, without altering card behaviors. |
| `cards.json` | **Reusable rules catalog**, indexed by exact card name. Mana costs, permanent types, creature subtypes, tags, trigger events, triggered effects, mana abilities, and supported-status flag. |
| `combos.json` | **Standalone combo recipes** with required battlefield/hand pieces, rank, conditional level, per-iteration cost, how generated resources pay for another iteration, and intended output. |
| `engine.py` | State: library, hand, battlefield, graveyard, exile, lands, tap state, floating colored/restricted mana, tokens, events and dispatch, triggered effects, spell resolution, and payments. |
| `pilot.py` | Shared priority policy: draw, play land, cast rocks/cheap card selection/Wizards, choose when to cast Magnus, check combo readiness. No deck-specific hard-coded creature/trigger lists. |
| `combos.py` | Specific evaluators for the three currently supported loop patterns; bounded 3-iteration tests optionally execute the loop using the ordinary mana+cast system. |
| `run.py` | CLI producing per-turn traces, plus an optional small **smoke-test** batch—not a reliable win-rate estimate. |
| `tests.py` | Unit/regression tests for deck, independent swapping, event triggers, buyback, restricted mana, Signet, Altar, Stormsplitter, Breach, and combo repetition. |
| `COVERAGE.md` | List of cards whose printed abilities are not simulated or only partially simulated. |
| `game1_mana_poor.md`, `game2_engine_setup.md` | Two selected and labeled eight-turn gameplay traces. |
| `combo_lab.md` | Three **constructed initial boards**, each followed by three real modeled buyback casts. |

## Run (Python 3.10+, standard library only)

```bash
python tests.py -v
python run.py --seed 20261028 --turns 8
python run.py --seed 20261028 --trials 60
```

`run.py` produces two paired traces with the same initial seed (rush versus one-turn-delay plus removal). The provided *illustrative* `game2_engine_setup.md` instead uses seed `20261073`, selected to show an early rock and cabal development. **Selected examples must never be presented as representative draws.**

## Adding or swapping a card

1. Copy `deck_v16.json` to `deck_v17.json`. Remove one entry (or reduce its count) and add the replacement. Always keep 99 cards in the library and one commander.
2. If the replacement already has a `cards.json` entry, **nothing else is needed** for existing implemented abilities. The removed card's definitions remain reusable in the catalog, but it no longer appears in games.
3. If it is a new card, add `cards["Exact Card Name"]` to `cards.json` with `type`, `cost: [generic,blue,red]` (null if unknown), `status`, optional `tags`, `subtypes`, and `effects` entries.
4. Existing trigger handlers use `event` and `op`. For example, a Wizard that makes a token whenever you cast an instant or sorcery uses:

```json
{
  "event": "cast_instant_sorcery",
  "op": "create_token",
  "token": "Wizard",
  "amount": 1
}
```

5. For a **new kind** of ability, implement one generic new `op` in `engine.py`, then write an isolated regression test. Don't silently assume all cards have working behaviors because their costs are known.
6. Define a new multi-card combination in `combos.json`, with a per-cycle cost/resource description. For genuinely new loop mechanics, add an evaluator in `combos.py` and tests with a constructed state. Explicitly check that the loop restores resources after three iterations.
7. Instantiate `Catalog(deck_path="deck_v17.json")` and pass it to `Pilot`. Or change the default deck path after promoting the new version.

## Play priorities, and what isn't modeled

The simple pilot tries high-priority affordable actions until no worthwhile action remains: early rocks and selection, inexpensive Wizards, commander according to policy, mana/token/control engines, and low-priority utility. **It does not blindly spend all mana** when no meaningful legal play exists, and counters remain in hand for opponents. That is deliberate; spending mana just to reach zero would inflate spell counts.

Only certain inexpensive instants/sorceries have actual `resolve` handlers; other named spells may be deliberately held and logged as unmodeled rather than given invented targets. Buyback recipes have a higher priority in the separate combo checker, which can optionally run three actual casts. To turn that on, use `Pilot(simulate_combos=True)`. It is **off** for the ordinary goldfish traces.

For now the model makes a number of simplifying assumptions: one free mulligan, artificial opponent removal on turn 5 when requested, no blockers in combat, unmodeled timing/stack cases, no opponent land colors for Fellwar Stone (assumes U/R available), simplified dual lands and life, limited tutors/flashback/escape, and some static abilities of expensive creatures omitted. It cannot determine win rates. `COVERAGE.md` is mandatory when interpreting results.
