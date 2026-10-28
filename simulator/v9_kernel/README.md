# V9a — portable real-deck seat and kernel-backed zone/resource services

**October 28, 2026.** This is an **incremental infrastructure milestone**, not a finished v9 rules migration. It keeps v3–v8 intact. The live `V9Table` extends v8's **one** `CentralTable`, `Battlefield`, `SharedStack`, and `TurnDriver`; it does not clone combat or stack implementation.

## What works in the live simulation

- `DeckProvider` describes the four seats. The current live adapter accepts **exactly one** detailed Magnus player (now in **any** seat 0–3) and three abstract archetypes. Unsupported provider/alternative pilot configurations fail visibly.
- Existing named/static rules and v8's central battlefield apply to the relocated Magnus. One v6 hard-coded detailed land-event seat identifier is corrected at the reporting boundary.
- The legacy v8 shared counter-only stack and cost rules remain in use. `run_narratives.py` generates four narrated seed-matched diagnostic games, one per detailed seat; runs can diverge after seat movement because turn order and random choices differ.

## Staged reusable interfaces (not yet wired into the legacy pilot)

| Module | Authority / scope |
| --- | --- |
| `adapter.py` | Single live v8-derived table with generic seat-plan descriptors. *One* detailed Magnus seat only. |
| `zones.py` | `KernelZones` owns ordered nonbattlefield physical card IDs via the existing central `GameKernel` object registry: deterministic draw/discard/mill/search/shuffle/cast/counter/resolve/play land/leave game; no duplicate CardSpec copies. Cast events and resolutions are distinguishable. Printed spell effects are **not** silently invented. |
| `mana.py` | `TypedMana` source IDs, tap/untap, U/R/generic mode choice, bounded payment planning, controller legality using `GameKernel` objects. No floating/activation-cost/treasure-sacrifice/alternative-cost modeling. |
| `tests.py` | 29 targeted acceptance and fail-closed checks. |
| `run_narratives.py` | Four short seeded live diagnostic games with machine-readable events, reporting and seat movement. |
| `benchmark.py` | 40-seed 10-round timing probe; not a formal power or performance study. |

**Critical migration gate:** `KernelZones` and `TypedMana` are *not used by the live `V9Table` yet*. The v6 pilot still mutates Python hand/library/graveyard lists and uses `ColoredPayment`; synthetic opponents still use fungible mana. Attaching a mirrored zone registry to those lists would create duplicated state and false correctness. The next migration must replace the legacy mutation sites with explicit zone transitions and one projection layer. `KernelZones` currently requires its object registry to include only service-owned objects; it cannot safely share a live v8 battlefield kernel until the unindexed battlefield-view transitions are replaced.

## Run

From repository root:

```bash
python run_all_tests.py
cd simulator/v9_kernel
python run_narratives.py
python benchmark.py
```

From `simulator/v9_kernel`:

```python
from adapter import V9Table
providers=('control','aggro','magnus','combo')
game=V9Table(providers, seed=104, trace=True).run(10)
assert game.details.seat==2
assert game.world.consistent()
```

Examples for isolated, reusable state services:

```python
from zones import KernelZones
from mana import TypedMana, ManaMode
from rules import CardDefinition,Cost

zones=KernelZones(seed=4)
card=CardDefinition('id:probe','Probe',frozenset({'instant'}))
zones.add(card,2,zone='library')
(hand_id,),success=zones.draw(2)
assert success and zones.kernel.get(hand_id).zone=='hand'

mana=TypedMana()
mana.add_source(2,'Island',[ManaMode(blue=1)])
assert mana.pay(2,Cost(blue=1))
```

## Correctness boundaries and future milestones

- A second detailed deck in a live v9 table **fails closed**, rather than silently using a synthetic policy. Separate `KernelZones` tests can represent four detailed deck inventories, including two simultaneously, but this is **not a multi-deck game**.
- A real spell can be moved through command/hand/stack/graveyard by `KernelZones`; only a provided, separately verified handler resolves a nonpermanent spell. There is no full Magic priority, trigger-stack ordering, land tap cost selection in the live game, permanent attachment rules, copy system, or commander damage.
- `KernelZones` distinguishes cast and resolve events; it does not invoke spell-cast triggers itself. Command-zone redirects on countering are supported in the isolated service; the old v8 live flow remains unchanged.
- All smoke/replay outputs are infrastructure diagnostics, **never Magnus win-rate estimates**.
- Next: eliminate Python list mutations from legacy draw/cast/selection via a `ZonePlayer` adapter, then attach `KernelZones` to the **same** live game kernel. Introduce a source-backed `ResourcePolicy` that uses the already tested planner; only then extend priority/trigger frames, multi-detailed seats, and named-card coverage.
