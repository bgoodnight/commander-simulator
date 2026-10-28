# v8 — shared multiplayer transition kernel

**Status:** infrastructure milestone, not a card-perfect Commander implementation.

The single persistent `CentralKernel` owns battlefield objects, keyword/state-based actions, creature damage, zone transitions and object identity for **all four player seats**. `Battlefield` exposes read-side `Creature`/`Permanent` views to the legacy pilots while all new objects and removals pass through the kernel. `SharedStack` owns the single bounded counterspell/counter-counter exchange used by every seat. `TurnDriver` runs the same round loop regardless of seat type. The existing Magnus `MagnusPilot` and synthetic `PriorityPilot` are unchanged.

## Running and inspecting

From `simulator/v8_central`:

```bash
python tests.py
python run_narratives.py
```

The tests are standard-library only and the v3–v7 test suites remain unchanged. The narratives include three shuffled openings and one labeled forced-opening infrastructure diagnostic. None is an estimate of deck performance.

## Modules and boundaries

| Module | Responsibility |
|---|---|
| `kernel.py` | Persistent per-game rules kernel and one authoritative creature/permanent object identity; zone transitions, modifiers, destruction, combat damage, Treasure token identity and projection updates |
| `table.py` | Typed four-seat adapters for existing pilots, one damage pipeline, shared target legality, common effect dispatch and central battlefield lifecycle |
| `stack.py` | One LIFO stack of original spell and any nested counterspells, actual held cards and mana spent, bounded depth |
| `responses.py` | Declarative named counterspell type restrictions and on-resolution rider effects; no card-name cases inside the stack |
| `turns.py` | One four-player round/turn driver with phase hooks supplied by each pilot/deck provider |
| `tests.py` | 32 new tests spanning all four seats, target legality, commander, combat, stack chains, tokens, and stability |
| `run_narratives.py` | Four inspectable replay traces plus machine-readable round/diagnostic data |

### Shared operations versus remaining adapters

All `add_creature`, `add_permanent`, `kill_creature`, `remove_permanent`, `damage`, simultaneous damage, combat blocking, +1/+1 counters/modifiers and player elimination in this v8 table now route through the same kernel or its typed boundary. Creature and permanent IDs are no longer reconstructed at each rules query. Effects that create tokens, including Storm-Kiln Treasures, enter the persistent object registry. Printed counterspell riders are declared separately from their shared stack implementation.

**Not everything in Magic has migrated**. The real Magnus opening-hand/mulligan, individual named-card effect adapters, library manipulation and detailed land/mana-source mechanics still reuse the v6 implementations. Abstract opponents still have simplified fungible mana and synthetic card properties. Both use the shared casting/response pipeline but these resource policies remain different *by design*. Triggered abilities currently resolve after a cast event *before* the limited counterspell-response window: a true stack with priority around individual triggered abilities is still future work. Only counterspells are chosen as instant-speed responses. Some card-text effects, e.g. accurate scry, flash, replacement effects, sacrifice costs, Commander damage, buyback, spells copied, and verified loops, are unsupported or approximated. Synthetic finishers are still abstract and are not representations of printed cards.

**Fail-closed safety:** unimplemented detailed card effects cannot be cast; `ExecutionGuard` limits stack depth, actions, repeated states, objects and elapsed time. Safety stops label the game *unresolved*, not a loss. LoopResolver remains unmodified and only summarizes **separately verified** repeatable combo certificates; no actual Magnus loop is certified.

## Stable development and reproducibility

- v8 is an additive directory; v3–v7 source files are untouched.
- Preserve the prior v7 commit (`622ec87a6249ec7726af705c74084a31d993619b`) as a rollback point.
- Reproduce the behavioral checks using `python tests.py`; rerun paired narrated games after any rules change.
- `benchmark_diagnostic.json` is a small performance diagnostic (40 games for each engine, not a robust performance study).
- `ASSESSMENT.md` contains tracked risks, bugs discovered and priorities.

## Next milestone

Migrate library/hand/graveyard and mana sources into kernel-owned zone objects with typed `DeckProvider` and `ResourcePolicy` APIs, then extend priority to activated abilities and triggered stack objects. This should precede expanding all remaining Magnus cards.
