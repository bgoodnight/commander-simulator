# V7a/b implementation assessment — October 28, 2026

## Tests

- v3: 20 passing; v4: 15; v5: 21; v6: 21; **v7: 50** (total **127**). Re-run all suites from repository root as listed in README.
- New v7 rules checks cover individual and simultaneous eliminations, target legality, flying/reach, indestructible versus destroy/exile/sacrifice/lethal damage/zero toughness, temporary modifiers and +1/+1 counters, token cessation, zone-change object identity, commander choice and death triggers, color-pip-preserving cost reductions, Wizard/Shaman trigger multipliers, copy/cast distinction, and multi-seat rule reuse.
- Safety tests intentionally force unbounded identical actions, varying-state action storms, stack/trigger/object overload, unverified loops, open response windows and would-deck loops. These stop before infinite work or return unresolved/declined.

## Four replay diagnostics

| Replay | Opponents | Magnus life after 10 rounds | Casts | Creature tokens | V7 trigger instances | Outcome |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 01_mixed | Aggro / Control / Combo | 19 | 9 | 2 | 4 | no winner at limit |
| 02_pressure | Aggro / Tokens / Ramp | eliminated in round 9 | 4 | 0 | 4 | Ramp wins round 10 |
| 03_control_heavy | Control / Spellslinger / Midrange | 30 | 7 | 3 | 4 | no winner at limit |
| 04_forced_triggers | Control / Combo / Tokens (forced opening) | 28 | 7 | 7 | 9 | no winner at limit |

Replays are for QA only. The fourth opening is deliberately forced and is NOT a random observation.

## Comparison against unchanged v6

The same seeds ran under v6 and v7. Different outcomes are expected because the v7 bridge routes token generation, trigger doubling and blocking through shared traits and queries. The qualitative checks show repeated Magnus casts, counterspells, token creation, a combat elimination, and some extended nonterminal games. There were **no v7 safety stops** in any of the four narrated games.

A local 30-seed, 10-round, trace-disabled microbenchmark produced v6 median **5.91 ms/game** (mean 7.97 ms with a notable outlier) and v7 median **8.20 ms/game** (mean 8.59 ms); these are environment- and workload-dependent and not guarantees. The new kernel caches trigger lookups and cost calculations by state revision, and the bridge caches snapshots while the relevant battlefield is unchanged. A first-pass adapter introduces modest extra work but not catastrophic memory or compute growth.

## Key engineering observations

1. Modeling ordinary keyword/ability metadata is cheap. Repeated decision search, source combinations and triggered-effect chains—not a 100-card catalog—are the scaling risks.
2. The old v6 `block()` temporarily modified a player's live creature list. The new bridge delegates legal blockers to a nonmutating query.
3. Temporary copies are now removed without generating a spurious death event in the v7 bridge. Full exile zone accounting still needs kernel authority.
4. A new zone identity is mandatory for target correctness. The kernel now creates one, clears counters/modifiers for new objects, and preserves a death event if a commander chooses the command zone after hitting the graveyard.
5. Safety stops are reported as **unresolved**; no arbitrary player wins because of hitting a turn, action or wall-clock cap.
6. Rules and data are separate. `catalog.py` supplies typed characteristics; changing a card's controller, creature subtype or `indestructible` keyword changes generic behavior without a custom player class.
7. Loops may only be fast-forwarded after rule-specific verification of all required invariants and opponent responses. The current synthetic lethal example is **illustrative only**; it is not evidence that an actual Magnus combo is legal or available.

## Known issues / no overclaim

- v7 is a v7a/b **kernel + partial bridge**, not the promised complete single-source-of-truth multiplayer engine. V5/v6 legacy state and much combat/stack timing remain; migrating them is substantive future work.
- Indestructible testing is comprehensive at kernel level, but v7's bridge does not yet fully route real opponent removal/exile into the new zone kernel.
- The bridge's source-ID lookup for Magnus combat-damage triggers still relies on the legacy v6 current-attacker name, a migration seam for a future stable ID event. It is not yet correct for two independently named copies of that creature.
- Actual v3 combo recipes have **not** been ported. A `LoopCertificate(validated=True)` is an input contract, not proof automatically generated from a deck.
- Real deck coverage remains partial; unsupported spells stay inert rather than silently approximated.
- Real Magic game turns can be very long or end earlier; these results do not calibrate game duration.

**Decision:** Suitable as a reusable rules-core starting point and safe test harness; next priority is to make the same kernel authoritative for player/zone/stack actions before completing all 100 card definitions.
