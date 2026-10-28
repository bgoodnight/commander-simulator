# V12 — card coverage audit and expanded combat

October 28, 2026. This milestone completes the agreed first three implementation
items: a card-by-card Magnus audit, multiple blockers/trample, and first/double
strike. It adds rule support, not additional named deck cards.

## Coverage and triage

[CARD_COVERAGE.md](CARD_COVERAGE.md) records all 100 physical cards (99 plus
commander), across 83 distinct names: **23 supported subsets, 25 partial, 35
unsupported**. Counting repeated basics gives 40/25/35 physical cards. A supported
subset certifies the stated behavior only; it is not full Oracle coverage.
Castable bodies or mana sources with missing text are explicitly partial.

The audit reads live registered specs and applies a reviewed omission list. It
is reproducible and machine-readable in CARD_COVERAGE.json. It supersedes using
historical supported/approx effect counters as a whole-card completion measure.
No new unsupported card silently becomes a generic spell.

After combat, prioritize exact selection/land behavior and missing live engine
text (prowess, artifact-count power, Baral loot, delayed expiry). Then implement
copying, relevant creature activations/tutoring, graveyard casting and validated
combo lines. This ordering favors effects already influencing the detailed deck.

## New combat rules

- Multiple creatures may block an attacker; each blocker still blocks only one
  attacker. Validate the full declaration before committing it. Flying/reach,
  tapping, defending-controller and duplicate-use restrictions remain enforced.
- There is **no damage assignment order**. A custom allocation can divide attack
  power freely among remaining blockers when damage is assigned. Assignment and
  damage occur together without a response window between them.
- Trample permits player damage after lethal damage is assigned to every remaining
  blocker. Marked damage reduces the threshold; indestructible does not. An
  attacker can overassign to blockers instead of trampling. When all blockers
  leave, trample can hit the player; without trample, blocked status prevents it.
- First/double strike schedule an extra damage step if present on a combat
  participant as the first damage step begins. Each batch is simultaneous, followed
  by state-based actions, trigger placement and priority. Pools empty between steps.
- The normal step uses a snapshot of which combatants initially had first/double
  strike, plus current double strike. Losing first strike does not grant a second
  hit; gaining it late does not suppress an ordinary hit. Losing double strike
  suppresses its second hit, and gaining it can enable the second hit.
- Every allocation in a batch is checked before damage mutation. Invalid targets,
  negative/noninteger amounts, incomplete assignments and illegal trample excess
  are rejected. Each per-source allocation is recorded for diagnosis.

The default blocker pilot can group blockers to reach lethal damage; the default
attacker allocates lethal amounts in stable ID/declaration order, then excess.
That is a pilot choice, not a rule requiring an assignment order. Policies can
choose other legal splits. Pilot strategy is not claimed to be optimal.

## Use and validate

Run from the repository root:

```bash
python run_all_tests.py
python simulator/v12_combat/audit.py
python simulator/v12_combat/validate_combat.py
```

There are **422 tests across twelve suites**, including 50 new tests. The validator
writes six explicitly forced narratives with JSON source payments/priority/damage
records, a 200-game twelve-round sweep across all four Magnus seats, and exploratory
8-round timings. See [INTERACTION_REPORT.md](INTERACTION_REPORT.md).

For programmatic use, import CombatTable from expanded with this directory on
Python's path. Optional policies:

- block_assignment_policy receives immutable (attacker ID, defender seat) pairs
  and returns (attacker ID, blocker ID) pairs.
- combat_damage_policy receives an immutable Allocation containing the attacker,
  power, blockers, their lethal thresholds, stage and whether player damage is
  allowed. Return a mapping from blocker IDs to damage, with optional 'player'.
  This policy chooses amounts; it must not mutate game state.

Keyword metadata uses first_strike, double_strike and trample. Direct combat
harnesses call begin_damage once before applying the scheduled batches; the turn
driver performs this automatically.

## Limits and preservation

Strike/trample narratives use declared synthetic tokens or a synthetic keyword
grant to the actual Magnus object. They do not claim a newly implemented printed
grant spell. Spell responses are real deck cards, paid with actual source IDs.
The unforced sweep exercises group blocking; it is not evidence of natural draws
of newly supported strike/trample cards.

Still absent: one blocker blocking multiple attackers, menace/banding, deathtouch,
lifelink, prevention/protection damage rules, planeswalker/battle attacks, commander
damage, Auras/Equipment, general control-change combat removal, copies and verified
loops. Other v11 card/land/selection limits remain. One detailed Magnus deck plus
three synthetic opponents is still the table model. No win-rate inference.

V11 is the rollback checkpoint at 12ea213bc140a84fcb917e26a8ed6c5104cff5f5.
Only a backward-compatible damage_steps hook is added to its driver; its default
behavior and all historical suites are preserved. Historical manifests remain
records of their original checkpoint bytes.

## Rule sources

Implemented against the September 25, 2026 [Comprehensive Rules](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.pdf):
509.1 (blockers), 510.1c/510.2 (division/simultaneity), 510.4 and 702.4/702.7
(strike steps), 702.19 (trample). The [Foundations update bulletin](https://magic.wizards.com/en/news/announcements/foundations-update-bulletin)
explains removal of damage assignment order. The card audit references local
implementation providers and known omissions; it is not a fresh Oracle-text audit.
