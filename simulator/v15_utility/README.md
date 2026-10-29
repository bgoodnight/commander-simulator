# V15 — Sanctuary, Fiery Islet and Riptide Laboratory

October 29, 2026. This batch implements the next three utility lands on the v14
source/zone/priority engine. Existing land entries, selection, combat and prior
reference fingerprints remain available. No additional caching is introduced.

## Added behavior

| Card | Implemented behavior | Timing and interaction |
|---|---|---|
| Mystic Sanctuary | Untapped entry triggers; target an instant or sorcery card in your graveyard; optionally put it on your library top | Target chosen at stack placement after the current action/SBAs; no legal target means no ability on the stack; invalid target on resolution causes failure; source departure does not cancel it |
| Fiery Islet | Existing U/R mana ability pays one life; **1, tap, sacrifice: draw a card** | The source is reserved from paying its own tap cost. Cost paid before priority; opponents can respond; empty-library loss is checked after resolution |
| Riptide Laboratory | Colorless mana; **1U, tap: return target Wizard you control to its owner's hand** | Can target any Wizard permanent, including a noncreature Wizard; derived Wizard types apply; target controller/type/shroud and identity rechecked on resolution |

The generic stack now permits an optional trigger-preparation hook at placement,
so Sanctuary's target is selected when the trigger actually goes on the stack,
not prematurely while an effect is still resolving. Existing tables without the
hook retain their previous behavior. APNAP placement and trigger ordering remain
in the shared stack; target choice is distinct from the optional return decision.

Set `sanctuary_target_policy(request)` to select one of its `eligible` object IDs.
If no eligible target exists, the trigger cannot be placed. Set
`sanctuary_return_policy(controller, source_id, target_id)` to return a boolean
when the trigger resolves; the default returns the selected card. A graveyard
object that changes zones has a new ID and cannot be followed by the old target.

Riptide choices are exposed through the normal priority interface. The activation
reserves the land from paying the tap cost, requires one generic and one blue mana,
and validates its target before payment. A target that leaves or loses Wizard
status before resolution becomes illegal. A Wizard token returned this way ceases
as it changes zones. This milestone handles the relevant targeting subset; general
graveyard protection, replacement effects, control changes and layer interactions
remain outside scope.

## Validation

```bash
python run_all_tests.py
python simulator/v15_utility/coverage.py
python simulator/v15_utility/validate.py
```

**585 tests across fifteen suites**, including **38 new checks**, cover Sanctuary
target timing, no-target and optional outcomes, changed-zone identities, Riptide's
exact 1U cost and legal noncreature Wizard targets, self-reserved mana, responses,
and Islet's source costs, mana/life mode and empty-library draw. Historical suites
pass. Four saved v14 reference cases, one per Magnus seat, reproduced exactly.

The validator writes six narrated interaction scenarios and JSON priority/payment
records, then checks 200 twelve-round games and 12 eight-round timing samples per
engine by default. See [INTERACTION_REPORT.md](INTERACTION_REPORT.md). The scenario
moving a Sanctuary target to exile uses a clearly labeled synthetic response;
other described spells use actual cards and source mana. Results remain
infrastructure diagnostics, not empirical Commander win rates.

[CARD_COVERAGE.md](CARD_COVERAGE.md) covers all 100 physical cards/83 names:
**41 supported subsets, 7 partial, 35 unsupported** distinct names (58/7/35
physical cards including repeated basics). Supported subset is not full Oracle
certification. Channel and full modal double-faced behavior remain unimplemented.

The prior v14 REFERENCE_CASES.json remains available; the v15 PERFORMANCE_HISTORY.json extends the runtime series
for later caching work. Historical kernel/mana-planner caches remain as before;
this batch adds no new cache. Changed rules intentionally produce different v15
trajectories, so v14 hashes are a reference for unchanged v14 semantics, not an
expected match for new v15 behavior.

Rollback: b0b0237ee915532b4d2f4ca3b089999671294b27. V15 adds a bounded utility
provider/table and a backward-compatible stack target-preparation seam. Historical
manifests remain checkpoint records. One detailed Magnus deck plus synthetic
opponents and prior broader rules limitations remain.

Rule references: [Throne of Eldraine release notes](https://magic.wizards.com/en/news/feature/throne-eldraine-release-notes-2019-09-20)
for Mystic Sanctuary, and the [Comprehensive Rules](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.pdf)
for targeting, activation costs, stack placement and state-based actions. Utility
card text is verified against card references; the model remains a bounded subset.
