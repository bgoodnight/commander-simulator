# V14 — land entry, basic types and explicit Passage fetch

October 28, 2026. The next bounded land batch replaces entry/fetch adapters with
explicit choices and stack timing. Mystic Sanctuary's graveyard trigger, other
utility activations and channel remain deferred. No additional caching is added.

## Added behavior

| Land/rule | Implemented | Important boundary |
|---|---|---|
| Island/Mountain | Basic supertype and matching land subtype in all zones | Producing U/R alone does not give a land either type |
| Steam Vents | Island/Mountain types; optionally pay 2 affordable life as it enters | Payment is not damage; decline means tapped; another forced-tapped instruction still applies |
| Training Center | Untapped with at least two current opponents | Eliminated players do not count |
| Stormcarved Coast | Untapped with at least two other lands | Incoming land does not count itself |
| Spirebluff Canal | Untapped with at most two other lands | Tapped from the fourth land onward |
| Sulfur Falls | Untapped if an already controlled land has Island/Mountain subtype | Tapped Steam Vents or Sanctuary can qualify; Command Tower/blue Pathway cannot |
| Mystic Sanctuary | Island subtype; untapped with three other Islands | Nonbasic; its graveyard-to-library trigger is still absent |
| Riverglide Pathway | Explicit U/R mana-face choice on entry | Full modal double-faced characteristics remain partial |
| Fabled Passage | Tap/sacrifice activation; basic search, tapped entry, shuffle, four-land untap check | Costs paid before priority; land count checked on resolution; can fail to find |

Land plays remain special actions: own main phase, priority, empty stack, once
across both main phases. Entry checks are not triggered abilities and do not create
an entry-choice response window. `enter_land` provides the shared effect-entry
path; it does not consume a land drop. The tested scope is individual land entry,
not simultaneous Scapeshift-style entry or a general replacement-effect system.

Passage is not sacrificed merely by playing it. Its ability uses the existing
registered activated-frame stack. Opponents can respond after tap/sacrifice, and
the ability survives the source leaving. A countered activation keeps its paid
costs. Ordinary Counterspell cannot target it; ability-countering is exercised by
an explicitly synthetic registered ability in unit tests, not an enabled printed
Stifle card.

Only cards with the basic supertype in the controller's library are eligible;
Steam Vents and Mystic Sanctuary are not basic despite their land types. A search
may choose no card even when basics exist, then still shuffles. A selected basic
enters tapped first, then untaps if the resulting controlled land count is at
least four. The fetched land counts, sacrificed Passage does not. No player gets
priority between entry, shuffle and the condition check. This neither draws nor
casts a card and does not trigger cast engines.

## Policies and use

```bash
python run_all_tests.py
python simulator/v14_lands/land_coverage.py
python simulator/v14_lands/validate_lands.py
```

Import LandTable from land_table with this directory on Python's path. Policies
receive immutable requests:

- shock_land_policy(EntryChoice) returns a boolean. True pays 2 life if affordable.
  The default pays above 2 life unless another instruction already forces tapped.
- pathway_policy(EntryChoice) returns U or R. The default uses a simple color-balance
  heuristic; it is not an optimal pilot.
- fetch_policy(FetchChoice) returns an offered basic's object ID or None. It runs
  during resolution, with no priority. Default selection balances typed U/R lands.

The default development pilot chooses a legal Passage activation at an empty-stack
priority opportunity. Custom priority policies can wait or activate in another
player's turn. Mana and life costs still use actual source/object state.

## Validation and coverage

**547 tests across fourteen suites**, including **56 new checks**, cover boundary
counts, payments, basic versus typed nonbasic lands, source sacrifice, responses,
activation countering, immediate source availability, cast-trigger separation,
all-seat conservation and reference hashes. Historical suites remain unchanged.

Seven [interaction narratives](INTERACTION_REPORT.md) use actual conserved cards
and source payments. Entry-boundary stories contain independently conserved
branches. The validator defaults to 200 twelve-round games across all four Magnus
seats and three synthetic opponent groups, plus 12 eight-round timing samples per
engine. These are infrastructure checks, not deck win rates.

[CARD_COVERAGE.md](CARD_COVERAGE.md) and JSON cover all 100 cards/83 names:
**38 supported subsets, 10 partial, 35 unsupported** distinct names. Physical
counts with basics are 55/10/35. Six partial lands advanced; Sanctuary/Pathway stay
partial and no unsupported named card was enabled. Supported subset is not full
Oracle certification.

## Runtime tracking and later caching

V13 remains a normal rollback checkpoint and comparative timing engine. V14 adds
no new caches or optimization. Historical kernel/mana-planner caches already
existed and remain unchanged; this is the baseline before *additional* caching.

PERFORMANCE_HISTORY.json preserves historical v12/v13 measurements and the current
same-invocation v13/v14 comparison. Different rules, pilots and host load affect
trajectories and timing, so cross-version medians are descriptive, not isolated
causal estimates. Reference serialization is outside benchmark measurements.

REFERENCE_CASES.json stores seed, providers, rounds and SHA-256 reference digests
for every swept game. reference_state.py canonicalizes objects/card descriptors,
ordered zones, players, rules/movement events, mana payments/activations, priority,
steps/combat, selection/engine/land decisions, delayed effects and RNG state.
Runtime, cache-hit counts and other performance counters are excluded. Reproduce
the exact input with LandTable and compare fingerprint(table) against its case.
Future caching should preserve these hashes for unchanged semantics. Intended rule
changes need an explicitly versioned new baseline instead of matching old outputs.
The module is fingerprinting infrastructure; no cached candidate engine is built.

## Remaining scope

Mystic Sanctuary's targeted ETB trigger, Fiery Islet draw, Riptide Laboratory bounce,
Otawara/Sokenzan channel, full double-faced characteristics, broad replacement and
land-entry trigger systems, general control changes and simultaneous multi-land
entry remain deferred. Existing spell-copy/Commander/attachment and combat limits
also remain. One detailed Magnus deck plus synthetic opponents is still the model.

Rollback: a1d4e4263eb79a9dad255b1907606a8477926c31 (v13). V14 is an isolated
provider/table/validation directory and test-runner/README update; no historical
rules file or cache implementation is changed. Historical manifests record their
original checkpoint bytes.

## References

- [Bloomburrow notes](https://magic.wizards.com/en/news/feature/bloomburrow-release-notes): Passage's tapped entry, post-shuffle untap and land count.
- [Throne of Eldraine notes](https://magic.wizards.com/en/news/feature/throne-eldraine-release-notes-2019-09-20): Sanctuary, basic land types versus basic lands, pre-entry checks and forced tapped entry.
- [Commander Legends notes](https://magic.wizards.com/en/news/feature/commander-legends-release-notes-2020-11-06): multiplayer dual-land cycle counts current opponents.
- [Crimson Vow notes](https://magic.wizards.com/en/news/feature/innistrad-crimson-vow-release-notes-2021-11-10): two-other-lands cycle and entry checks.
- [Lorwyn Eclipsed notes](https://media.wizards.com/2026/downloads/ECL_Release_Notes_06HVqa76yI/AIuLLXK62r_EN_MTGECL_ReleaseNotes_20260106.pdf): Steam Vents entry-life choice.
- [Comprehensive Rules](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.pdf): land special actions, activated costs/source independence, search, shuffle, life payment and SBA timing.
