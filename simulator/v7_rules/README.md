# V7a/b — Reusable rules kernel, typed abilities and bounded loops

**Status: infrastructural alpha, not a complete Magic rules engine or a real-deck win-rate simulator.** The existing v3–v6 versions are unchanged; this folder adds an independent rules kernel (`rules.py`), composable example card definitions (`catalog.py`), a narrow real-Magnus/three-abstract-opponent bridge (`bridge.py`), and fail-closed loop protection (`loops.py`).

## Run it

Python 3.10+, standard library only. From the repository root:

```bash
python simulator/v7_rules/tests.py
python simulator/v7_rules/run_narratives.py
```

To reproduce ALL regression suites:

```bash
for v in v3_magnus_modular v4_abstract_opponents v5_four_player v6_real_deck v7_rules; do python "simulator/$v/tests.py"; done
```

The narrative runner replays **three seeded, natural-opening 10-round games and one explicitly forced-opening scenario**. It produces `01_*.md` through `04_*.md`, matching JSON traces and `narrative_results.json`. The generated traces are fixed evaluation fixtures, **not** performance estimates.

## Architecture

| Module | Purpose | Deck-specific branching? |
| --- | --- | --- |
| `rules.py` | Immutable `CardDefinition`, `Ability`, `Cost`, `Effect`; per-game `GameObject`, counters, modifiers; typed `GameKernel`; zone changes, targets, destruction/exile/sacrifice/bounce, keyword blocking, state-based damage, simultaneous player damage, cost reductions, trigger dispatch and custom effect registration | No |
| `catalog.py` | Data declarations for Magnus, Young Pyromancer, Harmonic Prodigy, Third Path Iconoclast, Storm-Kiln Artist, Archmage Emeritus, Stormsplitter, Goblin Electromancer, Baral and representative tokens | Yes, **data only** |
| `loops.py` | Configurable action/wall-clock/object/stack/trigger budgets; repeated state detection; fail-closed loop analysis and optional symbolic mana representation | No |
| `bridge.py` | Integrate v7 static/trigger/target queries into the v6 mixed four-player game. Translate v5/v6 creature IDs to temporary typed v7 game objects and back | A **temporary adapter** recognizes the original v6 game structure; not final migration |
| `tests.py` | Rules unit tests, safety tests, integration smoke tests across four seats | None in rules |

Objects have **stable card-definition IDs** but **new game-object instance IDs on zone moves**. Controller is distinct from owner. Types/subtypes, tokens, counters, temporary keyword/power modifiers, and damage are separate. For example, `indestructible` stops destruction and lethal marked damage but does not prevent exile, sacrifice or zero-toughness state-based movement. Flying's blocker restriction uses a pure, non-mutating legal-blocker query. Commander death can enter the graveyard, emit a `dies` event, and then move to the command zone if chosen.

The shared cost predicate for Magnus applies ONLY to instants and sorceries, subtracts ONLY generic mana, and counts ONLY creature tokens rather than Treasures. It applies to any pilot/seat controlling an appropriately defined source. Eligible Wizard/Shaman triggered abilities receive a further trigger from Harmonic Prodigy; non-Wizard/Shaman abilities do not. Spell-copy triggers are distinct from spell-cast events.

## Why finite and infinite loops must be handled differently

Each pilot operates under **hard budgets**. By default: 128 actions/player turn, 10,000 actions/game, 256 trigger instances/event, 64 stack frames, 1,000 game objects, three repetitions of the same full state/action signature, and four seconds wall clock. Exceeding any budget raises `SafetyStop`, and the table reports an **unresolved** game, NOT a loss or a made-up winner. These limits are configurable and are engineering safeguards rather than Magic rules.

`LoopResolver` can compress a **separately verified**, deterministic, response-cleared loop into a finite lethal count. Example: for three opponents at 12, 38 and 40 life, a verified 1-damage-per-player cycle needs exactly 40 iterations; represent the outcome mathematically rather than execute 40 trigger chains. A mana-only positive loop records **symbolic arbitrary finite mana**, never a huge number or literal infinity. An unresolved response window, unverified repeatability, unknown targets or lethal sequence that would draw through the pilot's reserved final card yields `unresolved`/`declined`.

**Critical caveat:** These are contracts and demonstrations; v7 does **not** recognize, validate or execute the actual Searing Touch/Mystic Speculation loops from the v3 Magnus combo catalog. Merely finding required cards in play is insufficient to certify any combo. A later rules-specific verifier must prove payment, repeatable game state, triggers, priority windows, and damage before issuing an accepted `LoopCertificate`. It must recheck real prevention/replacement effects before applying damage.

## What's deliberately not integrated yet

1. The bridge rebuilds a temporary kernel view from the old v6 battlefield. It does not yet make `GameKernel` the single authoritative state owner for the whole table; v6 still has independent turn/combat/priority and much zone handling.
2. The real Magnus player remains **seat 0 only** in `ModularTable`; the kernel itself supports any number of seats, including more than one detailed deck. Full `DeckProvider`/`Pilot` substitution is next-stage work.
3. The full stack, actual mana source activation, combat damage assignment, all card-specific effects, prevention/replacement layers and commander damage are not implemented. The old v6 partial card coverage remains unchanged (38 unsupported named nonlands).
4. The sample trigger resolver is a noninteractive diagnostic path. `bridge.py` currently dispatches cast triggers eagerly through the old engine; it is not a substitute for a triggered-ability stack with priority and response windows.
5. The abstract opponents still use v5 synthetic category cards and a fungible mana model. Simulated wins and timings are not real-world MTG benchmarks.

## Rollback

This folder is added as a new commit. Nothing in `simulator/v3_magnus_modular/`, `simulator/v4_abstract_opponents/`, `simulator/v5_four_player/` or `simulator/v6_real_deck/` is changed. Use normal Git `revert` for a reversal on `main` or `git switch --detach <prior-v6-sha>` to inspect the earlier checkpoint; no force push required.

## Next steps

- V7c: make the typed kernel authoritative for all four players' zones/actions; introduce standardized `DeckProvider` and independent `Pilot` protocols with no deck-specific `Table` overrides, unify mana policy and source activation.
- V7d: implement bounded stack and priority, replacement/prevention effects, legality rechecks, life/damage and death triggers on one path, with narrated behavior regression fixtures.
- V7e: add a validated combo verifier and remaining Magnus card effects, then examine qualitative game flow before running win-rate simulations.
