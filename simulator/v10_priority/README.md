# V10 — typed stack and four-player priority

October 28, 2026. V10 replaces the counter-chain resolver in live games with one
LIFO stack for physical spells, triggered abilities and registered nonmana
activated abilities. It reuses v9c source payment, v9b physical zones and the v8
battlefield/cost/target rules. This is a priority milestone, not complete Magic.

## Live behavior

- All living players receive priority in the table's turn order. An action
  resets consecutive passes and its actor retains priority. After everyone
  passes, exactly one top object resolves; the active player then gets priority.
  Passing with an empty stack finishes the current exposed window.
- Spell-cast triggers wait for the state-based checkpoint and enter the stack
  in APNAP order. Controllers can order their own simultaneous triggers. Doubled
  triggers are separate frames with separate response opportunities.
- A queued ability keeps its controller and captured operation if its source
  dies, is bounced or is sacrificed. A departing player's controlled frames and
  waiting triggers leave the game. Frame IDs never follow new zone instances.
- Supported instants may be cast in response, not only counterspells. Counters
  can target any legal spell frame, including one underneath a trigger. Ordinary
  spell counters cannot target ability frames. A generic declared ability-counter
  operation is tested with explicitly synthetic fixtures; no new named Stifle
  implementation is claimed.
- Targets are checked before payment and again on resolution. A counter whose
  target has left, or a removal spell whose target has changed zones, fizzles
  without its normal resolution effects. Responses reopen after every resolution,
  including after a trigger draws a new instant.
- Sorcery timing requires the active player's main phase and an empty stack.
  Casting or nonmana activation during another object's resolution is rejected.
- Mana abilities remain immediate actions. They retain priority, reset passes
  and never create spell/ability frames. Source-backed automatic cost payment
  remains available during casting and activation.
- Mind Stone's draw ability is live: pay one mana, tap and sacrifice its actual
  source, then put an activated frame on the stack. Reserving its source prevents
  using it to pay the mana cost and then tapping it again. Its draw survives its
  source's sacrifice and can be responded to.
- Main-phase actions are selected within priority rather than bypassing empty-stack
  passes. Combat-damage triggers use the same stack at the serial combat driver's
  exposed checkpoints. Hand-size cleanup now occurs at end/cleanup, not precombat.

`PriorityStack` contains no card-name rules. `abilities.py` declares the limited
named activation catalog. Other behavior requires explicit registered descriptors
and implemented operations; unknown trigger/activation operations fail closed.

## Run and inspect

From repository root:

```bash
python run_all_tests.py
python simulator/v10_priority/validate.py
```

There are **322 tests across ten suites**, including 51 v10 checks. Validation
writes four narrated replay pairs, machine-readable priority histories and
`validation_results.json`, plus a 400-game conservation/resource/stack sweep.

With this directory on the Python path:

```python
from gameplay import PriorityTable

game = PriorityTable(['control', 'aggro', 'magnus', 'combo'], seed=104).run(10)
assert game.assert_consistent()
print(game.diagnostics()['v10'])
```

A deterministic policy can inspect `(seat, immutable_frame_tuple, legal_choices)`
and return a provided `Choice` or `None` to pass:

```python
game.priority_policy = lambda seat, frames, choices: None
# Optional controller ordering: must return the same trigger frame objects.
game.trigger_order_policy = lambda seat, frames: frames
```

The old counter-only `response_policy` is not the v10 policy API. Main pilots
still choose proactive development; default priority decisions provide bounded
heuristics for counters, occasional instant interaction and Mind Stone use.
They are simulation policies, not strategic optimality claims.

## Safety, scope and next gates

Source planning, objects, stack depth and actions retain execution guards. Priority
windows also bound actions/passes; state-based checkpoints have repeat budgets.
Safety stops remain unresolved, never scored as a loss. Partial stopped snapshots
can retain unfinished frames; they do not represent completed game states.

This remains one detailed Magnus deck plus three synthetic archetypes. Only the
existing named effect/trigger subset and Mind Stone's added activation are live.
Creature tap activations, arbitrary activation costs/operations, intervening-if
conditions, delayed/meta-triggers, copies, buyback, commander damage and verified
Magnus loops are not implemented. Activation descriptors currently reserve a
source with tap or sacrifice costs, a conservative supported-cost subset.

The turn driver is still coarse: upkeep/draw/land development are combined;
combat attacks/blocks/damage are serial approximations and do not expose every
official step or preattack/preblock response window. Some land and selection
rules remain approximate. Phase-specific restrictions, flash, split second,
replacement/prevention and broad card coverage are not implied by the new stack.

Next: finer phase/step and combat integration, more verified effect/activation
coverage, then multiple detailed decks. Replays are engineering diagnostics,
not validated deck win rates. See `ASSESSMENT.md` for the review and exact results.
