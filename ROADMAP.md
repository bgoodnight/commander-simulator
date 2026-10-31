# Development roadmap — reusable Commander simulator

Updated October 31, 2026 following the v35 [architecture audit](docs/ARCHITECTURE_AUDIT.md) and deck-provider implementation. Use [DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md) and the new [Hybrid Simulation Work Plan](docs/HYBRID_SIMULATION_WORKPLAN.md) as the execution contract. **Universal interactions with verified unfamiliar cards, reusable keywords and typed effects, and transparently qualified simulation are now higher priority than individual premium-deck cards.**

Current entry point: `run_simulation.py` -> `CopyTable`. Default deck: committed `decklists/magnus_thousand_sons_v1_14_premium.txt`, updated in `b9b3ba0abcd19676ec4f32cc9f427e52c1f55d8b`; Training Center and Otawara are pending and represented by basics. Preserve v1.13 budget and historical lists. Do not silently substitute trial/pre-delivery lists from other work.

Status: shared zones, source payments, stack/priority, combat and selected cards work. All 37 suites pass (824 observed tests); v35's recorded 200-game sweep has no safety stops. Coverage: 41 supported subsets, 6 partial, 35 unsupported distinct names. This does not certify deck strength. Normal mono-black and multiple-real-deck configurations are not yet supported.

## Priority and working rules

- Complete P0.5 metadata/coverage readiness, deliver **P0.6 universal interactable card objects + observation mode** and **P0.7 hybrid MVP**, then deepen shared keyword/effect/archetype services before any broad named-card batch. Coordinate with P1/P2/P3 extraction rather than waiting for total engine rewrite.
- Keep state/zone/priority foundations; extract incrementally. **A verified card remains a fully typed game object regardless of its effect coverage**: other cards and opponents must query, tutor, target, damage, block, sacrifice or move it through common rules, subject to supported legality. Do not add another active card-specific inheritance layer or rewrite everything at once.
- Preserve historical fingerprints and freeze strict-mode behavior for comparison. Add opt-in observation/hybrid modes with per-ability fidelity, unknown-restriction safety and downstream decision/dependence logs. Document intentional correctness changes separately.
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

1. **Started:** `commander_sim.decks.DeckProvider` validates both named presets and local files against bundled identity snapshots and feeds them to the CLI. Complete the deck parsing/validation extraction into one `DeckProvider` with a stable explicit path/config argument. Preserve canonical v1.14 premium and v1.13 budget as named presets, and permit `--deck-file` for an identified local decklist. Validate command zone, quantity, 100-card total, singleton/basic-land exceptions, and color identity using trustworthy available metadata; fail closed when verification is unavailable. Never silently accept unverified cards as supported.
2. **Started:** both CLI presets and compatible deck files use the same v35 engine with injected composition; historical engines remain regression fixtures. Baseline checks cover injected premium parity and budget inventory/Frostboil. Continue separating **deck composition** from **engine/rules implementation**. Construct the same active engine for both presets, rather than selecting historical `CopyTable` versus `AltarTable` as the meaning of a deck choice; preserve the historical engines only as explicit regression fixtures. Use one documented commander/Magnus pilot for initial acceptance, with a clear error for unsupported commanders until P2.
3. Provide a coverage-aware card loading path: verified names/types/mana values/colors where known; mark absent effects as unsupported and uncastable in full-rule mode. Support a separately labeled **observation-only** early-game analysis mode that includes unsupported cards in draws, tracks possible interaction by verified conditions, and never pretends their effects resolved.
4. Acceptance fixture: load the user's actual **Flameslinger v0.7 temporary list** from an authoritative saved file only; do not invent or reconstruct the deck. Compare premium/budget initialization and opening-hand replay with fixed seeds. Demonstrate a six-turn trace with draws, sources, playable actions, reserved mana, and opponent threat assumptions clearly labeled. Do not claim a win rate or complete card simulation.
5. Add CLI/loader contract tests, card-count and zone-conservation checks, provider registration tests, fixed-seed reference runs and a short measured runtime report (p50/p95 if sample supports it). Ensure P1 extraction can migrate the adapter unchanged rather than re-implementing deck parsing.

**Exit gate:** deck file/preset selection does not require a new table subclass; both canonical decks use the same current engine; a valid temporary list loads and yields honest coverage/early-turn observations; historical outcomes and known limitations are preserved. General commander identity, arbitrary colors (including B), two detailed seats, face-sensitive characteristics and complete card execution remain P2/P3 work.

## P0.6 — Interactable unfamiliar cards, verified metadata and observation mode (immediate)

Depends on the P0.5 deck-injection seam and P0 provider fix, **not on completion of P1/P2**. Implements hybrid work-plan H0/H1.

1. **Started:** all 76 distinct names in the authoritative v0.7 file now have a versioned offline Scryfall snapshot, with exact-deck hash, Commander legality and identity validation. The live simulator and observation mode do not yet load it. Validate exact faces/printed types, subtypes, power/toughness, colors and color identity, mana value/cost, keywords, legality and data provenance. Do not guess identity from name/list headings or bypass missing identities to make a run pass.
2. **Started:** an immutable offline identity registry exposes normal and Adventure printed faces, with unreviewed face semantics explicitly blocked. A targeted live-engine test places verified Stormsplitter characteristics on an object and finds it with wizardcycling; general automatic loading and live views remain pending. Establish one universal **card characteristics and game-object view** for all verified cards, including unfamiliar ones: zone/incarnation IDs, owner/controller, printed and derived types/subtypes/colors, mana value, P/T, keyword declarations and target restrictions. A card with unsupported abilities is **not** an anonymous placeholder.
3. **Started:** `commander_sim.queries` provides conservative tri-state predicates over current kernel objects, and Fabricate/wizardcycling use shared type and subtype predicates. Full verified-card and targeting integration is pending. Establish common **target and query predicates** (creature, artifact, enchantment, Zombie/Wizard, color, mana value, P/T bound, controller, battlefield/graveyard/library/stack). An implemented tutor or removal spell must recognize eligible verified unfamiliar cards, independently of their own effect implementation. Validate target restrictions; known unimplemented protection/ward/replacement behavior must block or be flagged conditional, not silently ignored.
4. **Started:** a deterministic, separate observation projection runs the v0.7 fixture using snapshot data, basic Island/Mountain drops, candidate mana-value screens and optional scripted threats. It does not implement mulligans, nonbasic lands, spell resolution, counter legality or a complete object model. Complete a reproducible **observation** path: six-turn draws, mana/land and candidate spell access, prospective counter/develop choices and clearly scripted opponent threats. Distinguish `playable_now`, `candidate_if_supported`, `reserved_mana`, `target_legality_unknown` and unresolved effects. Do not mark a candidate counter as actually countering a spell.
5. Record seed, exact deck hash, snapshot revision, conservation and p50/p95 where measured; preserve strict premium/budget regressions. Ship one actual v0.7 six-turn trace before scaling.

**Exit gate:** v0.7 imports with verified metadata; one unknown-effect real creature is found by an implemented type/subtype/power-limited tutor and recognized as a legal or explicitly uncertain target of opponent interaction; all cards remain real game objects; six-turn observation is replayable with honest unsupported-effect limits.

## P0.7 — Hybrid fidelity vertical slice and archetype/keyword pilot (next high priority)

Depends on P0.6 plus the **specific shared primitives** needed from P1/P2/P3/P4, not completion of the entire architecture plan. Implements hybrid work-plan H2 and seeds H3.

1. Add mode selection `strict | observation | hybrid`. Preserve strict semantics exactly; hybrid is opt-in, exact-first, and tracks support at the **ability/keyword/effect level**, including assumptions, omitted effects, first approximation and consequences for later choices.
2. Permit explicitly registered **verified-body-only** casting of ordinary creatures/permanents through canonical mana, timing, stack, zone and combat rules. Unsupported ETB, static restrictions, replacement effects or other interactions must be disclosed; if they affect legality or safety, block rather than silently suppress them.
3. Register **reusable parameterized behaviors** (colored land/rock, cantrip/filter, token maker, cast-triggered damage, counter with predicate, targeted bounce/removal), each usable by at least two independent cards. All effects operate on authoritative game objects so an unfamiliar body can be targeted, blocked, sacrificed, tutored and interacted with.
4. Build small verified keyword templates and type/role profiles for relevant mechanisms. Roles such as Zombie creature, mana rock, counterspell, tutor, spellslinger pinger, sacrifice outlet and recursion guide pilot classification but **do not grant rules text or legal abilities**.
5. Add representative scripted opponent actions via the same targeting rules and available mana. Run paired-seed strict/observation/hybrid traces, profile one engine game first, then 100 six-turn games with stratified narratives. No deck-strength or win-rate inference from unknown abilities.

**Exit gate:** new verified creatures and permanents behave as correctly typed, interactable objects; reused keyword and effect templates support multiple distinct cards; current rules are unchanged in strict mode; hybrid reports where approximations materially change decisions. Upgrade the common rules/primitives rather than creating new named-card tables.

## P1 — Normal package and composed engine services

Depends on P0 and coordinates with P0.6/P0.7. Findings A3, A7.

1. **Started:** `commander_sim` provides a normal package, dependency-validated service registry, and subprocess-isolated legacy adapter. Historical rules still use `sys.path` and shared module names; migrate their actual implementations before claiming import isolation.
2. Construct state/zones, queries, resources, stack/priority, events, effect registry and pilots once through a factory. Use narrow interfaces and explicit registration; reject duplicate capabilities.
3. Wrap existing handlers initially, then port one vertical slice at a time. Remove named-card table overrides without changing their semantics.
4. Keep historical engines/tests runnable but progressively remove them from active dependencies. Preserve milestones with git history/tags, not another superclass for every new card.
5. Treat the canonical card-object views, universal targeting/query predicates, reviewed simplified effects and fidelity journal as services to preserve during extraction, not temporary parallel implementations.

**Exit gate:** premium runs through the package with reference-equivalent results; two independent engines/registries coexist in one interpreter; adding a handler requires no table subclass or service replacement.

## P2 — Unified definitions and deck configuration

Depends on P1. Findings A2, A4. B-mana runtime tests finish in P3.

1. One immutable registry for characteristics, faces, costs, colors versus color identity, token templates, abilities and provenance. Keep network/Oracle fetching outside simulation.
2. A zone/face-sensitive characteristic service used by views, searches, costs and copies. Retire supplemental color/mana-value maps and setup-time object rewriting.
3. Commander-independent game/seat/deck/pilot configuration. Permit multiple detailed decks and basic-land multiplicity from metadata, including Swamp.
4. Generate capability coverage from definitions and explicit omissions, recording independent status for printed characteristics, rules/keyword implementations, and named abilities. Unknown abilities may be omitted only in an explicitly labeled hybrid approximation; they must not become fabricated generic effects.
5. Promote **shared object interaction and keyword/role definitions**: type/subtype/keyword/value predicates, legal target/query operations, and descriptive role profiles reusable for existing or newly imported cards. Every other card and opponent sees the same characteristics; no target search depends on whether the target's own special ability is implemented.

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

## P5 — Shared keyword and archetype library, then card batches

Depends on P4; **general templates take priority over named premium cards**. Begin reusable partial templates in P0.7 wherever prerequisites exist. Small typed templates, not an Oracle-text interpreter. Test mechanisms once and card wiring/interactions separately.

**Template-first gate:** prove that at least two different cards share an effect/keyword implementation with no name-specific engine edit; verify that generic tutor/removal/combat/targeting applies to an imported card lacking its own implemented special abilities. Include flying/haste/vigilance/trample/deathtouch/lifelink; token creation, card draw/discard, scry/surveil, ETB/dies/cast, sacrifice, counter/bounce and search; progressively support cycling/flashback/adventure/escape/buyback/convoke where core prerequisites are ready. Do not attach unprinted effects based on role labels.

1. **Early development:** Springleaf Drum, Stormcatch Mentor, Faithless Looting, Gitaxian Probe, Hard Evidence, Strike It Rich, Of One Mind. Group by shared cost/draw/token needs. Consider and Ral's Reinforcements are migration examples, not still-missing cards.
2. **Graveyard casting:** flashback for Faithless Looting/Strike It Rich, then Underworld Breach's escape permissions/costs. Reuse lifecycle pieces instead of copying Adventure's special casting path.
3. **Buyback/X/convoke:** Searing Touch, Whispers of the Muse, Fanning the Flames, Spell Burst, Meeting of Minds, Artistic Refusal; then Crackle with Power and its copies using bound X and typed targets.
4. **Trigger/copy engines:** Veyran, Talrand, Improbable Alliance, Saheeli, Dualcaster Mage. Extend Reiterate by supported capabilities instead of more card-name lists.
5. **Remaining tutors:** Gamble, Muddle's transmute, Imperial Recruiter, preserving their different costs/choices/predicates. Existing tutors become component regressions.
6. Triage other premium cards by rule dependency and impact on real turns. Retain removed cards for regression. Require demonstrated legal resource accounting before any loop/combo claim.

**Per-batch gate:** a second card using the mechanism needs no core name branch; interactions and source-paid current-game narratives pass; coverage/limitations are updated.

## P6 — Mono-black and mixed-deck acceptance

**Advance import and observation acceptance to P0.6/P0.7** once an authentic mono-black list and verified metadata are available. Actual black-mana execution depends on P3; death/graveyard and meaningful creature interactions depend on P4 and applicable P5 templates. Do not postpone all mono-black usefulness until every named effect is implemented.

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

## Additional authenticated deck fixtures (October 31, 2026)

- **Mortarion purchase-reconciled candidate:** `decklists/mortarion_purchase_reconciled_candidate_2026_10_27.txt` contains 100 cards derived from a specific Card Kingdom October 27 confirmation: 1 Mortarion, 67 other singleton cards and 32 Swamps. The receipt also contains one additional playable single, Soul of New Phyrexia, **provisionally excluded as the one deck-size cut**. Eight Astartes/Spawn token cards are accessories, not deck cards. This file is an **evidence-based candidate, not confirmed assembly or possession**; delivery was only reported as shipped at verification. The prior user-maintained 100-card Mortarion plan contains 24 names not accounted for by that receipt; some may be owned separately. Do not silently overwrite that older plan or assume those 24 are missing from the user's collection.
- **Official Wretched Ranks:** `decklists/wretched_ranks_foundations_precon_2026.txt` reproduces the Wizards of the Coast Foundations Commander precon (Ghoulcaller Gisa; 33 Swamps; 100 cards), source: https://magic.wizards.com/en/news/announcements/foundations-commander-decklists. No individual receipts are required to establish a manufacturer's precon composition; confirm any actual modifications before asserting identical physical ownership.
- **Acceptance priority:** These represent two distinct mono-black tests: a Pestilence/aristocrats/life-loss Mortarion deck and a Zombie-tribal Gisa precon. First report strict import failures honestly: current `DeckProvider` is Magnus-only, color-identity U/R and metadata-limited, and current engine lacks functional B-mana. Import/observation tests can progress independently of a valid source-paid black-mana game; do not claim they execute until P2/P3 and the hybrid gates pass. Add a pairwise test where Gisa's generic creature/Zombie tutor or removal sees a verified unfamiliar Mortarion card through shared characteristics; exercise sacrifice, death, and life-loss later as supported.

## Immediate next session

**Immediately implement P0.6**: integrate the newly retrieved v0.7 offline identity snapshot into a safe card registry and observation path; establish typed universal card characteristics and target/query predicates so unfamiliar creatures are still valid tutor/removal/opponent targets; deliver honest six-turn observation narratives. **Next implement P0.7** opt-in hybrid behavior using the same objects and registered keyword/effect templates, with ability-level fidelity and strict-mode regression parity. Advance reusable mechanics and generic mono-black compatibility before further isolated premium-only cards. Coordinate safely with the P1 service extraction; preserve P0 replay fixtures, premium/budget outcomes and historical tests.
