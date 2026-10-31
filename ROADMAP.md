# Development roadmap — reusable Commander simulator

Updated October 31, 2026 after the v35 [architecture audit](docs/ARCHITECTURE_AUDIT.md). Use [DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md) as the implementation contract. This supersedes the old card-first ordering.

Current entry point: `run_simulation.py` -> `CopyTable`. Default deck: committed `decklists/magnus_thousand_sons_v1_14_premium.txt`, updated in `b9b3ba0abcd19676ec4f32cc9f427e52c1f55d8b`; Training Center and Otawara are pending and represented by basics. Preserve v1.13 budget and historical lists. Do not silently substitute trial/pre-delivery lists from other work.

Status: shared zones, source payments, stack/priority, combat and selected cards work. All 37 suites pass (801 observed tests); v35's recorded 200-game sweep has no safety stops. Coverage: 41 supported subsets, 6 partial, 35 unsupported distinct names. This does not certify deck strength. Normal mono-black and multiple-real-deck configurations are not yet supported.

## Priority and working rules

- Fix the confirmed provider regression, introduce the P0.5 deck-configuration seam, then consolidate architecture before broad card batches.
- Keep state/zone/priority foundations; extract incrementally. Do not add another active card-specific inheritance layer or rewrite everything at once.
- Preserve historical fingerprints and freeze current behavior for comparison. Document intentional correctness changes separately.
- No new runtime caching until replay/invalidation gates exist. Never reduce legality/safety checks for speed.
- Commit each complete milestone after checks pass and continue under existing authorization. Update this plan with actual completed gates.

## P0 — Stabilize providers and establish a baseline

Dependencies: none. Audit findings A1, A9, A10.

1. **Completed:** reproduced and fixed Frostboil Snarl losing U/R mana in the assembled budget engine by registering its abilities in the shared provider catalog. The Altar integration regression verifies source-paid blue mana. Broader provider-composition contracts and premium integration remain to be completed.
2. **Initial baseline complete:** four eight-round premium cases include deck hash, engine revision, seed/seat, resulting state, RNG and semantic fingerprints. These are end-state references, not resumable snapshots or a complete choice transcript. Three additional forced interaction fixtures record explicit decisions for tutor, copy/buyback, and Adventure/Harmonic paths. Expand cases and retain corrected bug expectations before claiming comprehensive equivalence.
3. **Initial benchmark complete:** reproducible initialization, 8/12-round, token-target and stack/payment diagnostics are recorded in `simulator/p0_baseline/`. Timing is unprofiled, host-dependent, and does not change safety budgets.
4. **Initial checks complete:** the runner verifies actual test counts, and assembled budget/premium provider checks join historical suites. Broaden capability coverage as providers are extracted.

**Exit gate:** Frostboil works with Altar, premium behavior remains correct, unrelated providers cannot vanish silently, and the comparison corpus/benchmark protocol exists.

## P0.5 — DeckProvider seam and temporary-deck smoke test (new immediate priority)

Depends on the P0 provider fix and baseline; runs **before or alongside P1 extraction**, without assuming P2's general card registry or B-mana support is complete. This is a narrow portability milestone, not a claim that every deck's effects are executable.

1. **Started:** `commander_sim.decks.DeckProvider` validates both named presets and local files against bundled identity snapshots; it is not yet connected to either live engine or CLI. Finish extraction of deck parsing/validation into one `DeckProvider` with a stable explicit path/config argument. Preserve canonical v1.14 premium and v1.13 budget as named presets, and permit `--deck-file` for an identified local decklist. Validate command zone, quantity, 100-card total, singleton/basic-land exceptions, and color identity using trustworthy available metadata; fail closed when verification is unavailable. Never silently accept unverified cards as supported.
2. Separate **deck composition** from **engine/rules implementation**. Construct the same active engine for both presets, rather than selecting historical `CopyTable` versus `AltarTable` as the meaning of a deck choice; preserve the historical engines only as explicit regression fixtures. Use one documented commander/Magnus pilot for initial acceptance, with a clear error for unsupported commanders until P2.
3. Provide a coverage-aware card loading path: verified names/types/mana values/colors where known; mark absent effects as unsupported and uncastable in full-rule mode. Support a separately labeled **observation-only** early-game analysis mode that includes unsupported cards in draws, tracks possible interaction by verified conditions, and never pretends their effects resolved.
4. Acceptance fixture: load the user's actual **Flameslinger v0.7 temporary list** from an authoritative saved file only; do not invent or reconstruct the deck. Compare premium/budget initialization and opening-hand replay with fixed seeds. Demonstrate a six-turn trace with draws, sources, playable actions, reserved mana, and opponent threat assumptions clearly labeled. Do not claim a win rate or complete card simulation.
5. Add CLI/loader contract tests, card-count and zone-conservation checks, provider registration tests, fixed-seed reference runs and a short measured runtime report (p50/p95 if sample supports it). Ensure P1 extraction can migrate the adapter unchanged rather than re-implementing deck parsing.

**Exit gate:** deck file/preset selection does not require a new table subclass; both canonical decks use the same current engine; a valid temporary list loads and yields honest coverage/early-turn observations; historical outcomes and known limitations are preserved. General commander identity, arbitrary colors (including B), two detailed seats, face-sensitive characteristics and complete card execution remain P2/P3 work.

## P1 — Normal package and composed engine services

Depends on P0. Findings A3, A7.

1. **Started:** `commander_sim` provides a normal package, dependency-validated service registry, and subprocess-isolated legacy adapter. Historical rules still use `sys.path` and shared module names; migrate their actual implementations before claiming import isolation.
2. Construct state/zones, queries, resources, stack/priority, events, effect registry and pilots once through a factory. Use narrow interfaces and explicit registration; reject duplicate capabilities.
3. Wrap existing handlers initially, then port one vertical slice at a time. Remove named-card table overrides without changing their semantics.
4. Keep historical engines/tests runnable but progressively remove them from active dependencies. Preserve milestones with git history/tags, not another superclass for every new card.

**Exit gate:** premium runs through the package with reference-equivalent results; two independent engines/registries coexist in one interpreter; adding a handler requires no table subclass or service replacement.

## P2 — Unified definitions and deck configuration

Depends on P1. Findings A2, A4. B-mana runtime tests finish in P3.

1. One immutable registry for characteristics, faces, costs, colors versus color identity, token templates, abilities and provenance. Keep network/Oracle fetching outside simulation.
2. A zone/face-sensitive characteristic service used by views, searches, costs and copies. Retire supplemental color/mana-value maps and setup-time object rewriting.
3. Commander-independent game/seat/deck/pilot configuration. Permit multiple detailed decks and basic-land multiplicity from metadata, including Swamp.
4. Generate capability coverage from definitions and explicit omissions. Unsupported cards may load but must not become fabricated generic effects.

**Exit gate:** every query sees Mage Siege as an instant on the stack and Lindblum as its normal land elsewhere; two real decks construct without Magnus installers; a black fixture validates/loads normally.

## P3 — Shared mana/costs and one action lifecycle

Depends on P2. Findings A2, A5.

1. Represent W/U/B/R/G/C production explicitly, separating generic from explicit colorless requirements. Add typed tap, sacrifice, discard, exile and life-payment costs. Fail closed for unsupported hybrid/Phyrexian restrictions initially.
2. Explicit source/action/stack identities and immutable modes, target groups, X and paid options. Retire source selection by name, Python `id()` and dynamic target attributes.
3. Centralize timing/zone permission, total cost, increases/reductions, payment planning/reservations, stack entry and destinations. Track cross-source dependencies; a creature cannot fund both sacrifice and convoke.
4. Port ordinary spells, buyback, overload and Mage Siege through one pipeline. Copies use snapshots without casting/payment and share target-validation rules.

**Exit gate:** B mana/repeated Swamps work; Altar can produce all five colors; existing cast/copy/buyback/Adventure stories pass through one lifecycle; a second card using each mechanism needs definition-level wiring. Bind/capture X before implementing X finishers.

## P4 — Events, batches and effect primitives

Depends on P3. Findings A6, A7. Required before graveyard/combo batches.

1. State-changing operations return typed results/events with old/new references, source/cause, controller and last-known information. Unify dispatch; the history list is not the trigger engine.
2. Batch simultaneous token creation, deaths, damage and movement. Collect triggers from correct snapshots and use proper SBA/APNAP boundaries. Keep replacements explicit.
3. Extract the guide's effect/query/choice primitives. Preserve draw/mill/discard/sacrifice/destruction distinctions and required ordering.
4. Port tutors to predicate/choice/reveal/move/shuffle compositions, tokens to templates/batches, and Mage Siege plus a black death/life-change fixture to common event/effect services.

**Exit gate:** Fabricate/Merchant Scroll/Solve/Spellseeker share searches; Pyromancer/Mage Siege share token and event components; simultaneous deaths and removed-source triggers work; damage and life loss are distinct in events/results.

## P5 — Keyword templates and important card batches

Depends on P4. Small typed templates, not an Oracle-text interpreter. Test mechanisms once and card wiring/interactions separately.

1. **Early development:** Springleaf Drum, Stormcatch Mentor, Faithless Looting, Gitaxian Probe, Hard Evidence, Strike It Rich, Of One Mind. Group by shared cost/draw/token needs. Consider and Ral's Reinforcements are migration examples, not still-missing cards.
2. **Graveyard casting:** flashback for Faithless Looting/Strike It Rich, then Underworld Breach's escape permissions/costs. Reuse lifecycle pieces instead of copying Adventure's special casting path.
3. **Buyback/X/convoke:** Searing Touch, Whispers of the Muse, Fanning the Flames, Spell Burst, Meeting of Minds, Artistic Refusal; then Crackle with Power and its copies using bound X and typed targets.
4. **Trigger/copy engines:** Veyran, Talrand, Improbable Alliance, Saheeli, Dualcaster Mage. Extend Reiterate by supported capabilities instead of more card-name lists.
5. **Remaining tutors:** Gamble, Muddle's transmute, Imperial Recruiter, preserving their different costs/choices/predicates. Existing tutors become component regressions.
6. Triage other premium cards by rule dependency and impact on real turns. Retain removed cards for regression. Require demonstrated legal resource accounting before any loop/combo claim.

**Per-batch gate:** a second card using the mechanism needs no core name branch; interactions and source-paid current-game narratives pass; coverage/limitations are updated.

## P6 — Mono-black and mixed-deck acceptance

Depends on P4 and applicable P5 templates; may overlap later card batches.

1. Through normal configuration, exercise Swamps/B costs, generic costs, sacrifice outlets, tokens, life payment/loss/gain, death triggers and graveyard return as new objects.
2. Check token/nontoken deaths, last-known power, simultaneous removal, source removal, control changes and reanimation timing/responses where supported.
3. Import the user's actual mono-black deck from an authoritative list; audit capabilities and implement necessary rule families first.
4. Run black versus Magnus and multiple detailed seats. Keep pilot quality separate from legality; replace synthetic opponents incrementally as needed.

**Exit gate:** mono-black needs no commander-specific engine edits; shared-effect contracts pass across decks. State remaining rules/opponent/pilot gaps. Portability is not a win-rate certification.

## P7 — Optimize hot paths and evaluate simulation quality

P7a depends on P4 and stable current references; full new caching waits for required functional baselines. P7b follows relevant P5/P6 coverage.

1. **Queries:** maintain zone/controller indexes at mutations; add type/subtype indexes only when measured. Compare indexes to slow reference queries across moves/tokens/control changes.
2. **Actions:** one generator per action family, lazy deterministic target/choice enumeration, no repeated build/filter layers. Separate complete legality from pilot candidate-search budgets.
3. **Payments/checkpoints:** share query context within a read, remove duplicate work, track search states; introduce dependency-aware invalidation only with tests. Never merge required priority/SBA windows.
4. **Batch mode:** summary versus full trace without semantic changes; release histories between games; share immutable registry data safely. Profile again before multiprocessing, with isolated game state and per-game seeds.
5. Only then add memoization with cached/uncached equivalence for identical deck/rules/seeds/choices and invalidation tests. Record p50/p95 runtime, peak memory, candidates, queries, payment states and safety stops; do not compare unmatched version medians as controlled evidence.
6. Review fixed opening-hand/turn replays against manually expected play, then evaluate pilots and real opponents. Unsupported cards and synthetic pods remain limits until separately validated.

**Exit gate:** semantic equivalence, a repeatable targeted performance gain and recorded memory/search budgets. Track development efficiency through core files touched per card and template reuse.

## Immediate next session

Prioritize **P0.5 DeckProvider** now, alongside P1 compatibility-safe package extraction (the registry and subprocess adapter are initial seams only): unify premium/budget deck choice on one active engine, add explicit deck-file loading and truthful unsupported-card coverage, then validate one real v0.7 six-turn trace and benchmark. Continue expanding P0 replay fixtures; preserve the baseline and avoid new historical table subclasses.
