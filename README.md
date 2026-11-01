# Commander Simulator

A reproducible, modular four-player **Magic: The Gathering Commander** simulation project. Current milestone: **v35**: copied-spell target handling, plus v34 Mage Siege Adventure, plus v33 bounded Reiterate spell copying, plus v32 Cyclonic Rift, plus v31 premium Magnus v1.14 deck configuration, plus v30 Phyrexian Altar’s bounded sacrifice-mana ability, plus v29 Step Through spell mode and battlefield cycling-trigger events, plus v28 Spellseeker ETB search, plus v27 Fabricate and Step Through wizardcycling, plus v26 Merchant Scroll and Solve the Equation, plus v25 Personal Tutor sorcery search, plus v24 Ral's Reinforcements and colored token metadata, plus v23 Sapphire Medallion and printed spell colors, plus v22 Consider surveil and draw, plus v21 Frostboil Snarl entry and mana with targeted Magnus cost tests, plus v20 verified v1.13 card identities and search types, building on the v19 card-data verifier and v18 budget deck adapter, plus v17 Mystical Tutor search and v16 Otawara and Sokenzan channel abilities, building on v15 Mystic Sanctuary's targeted graveyard-return trigger, Fiery Islet's draw activation, and Riptide Laboratory's 1U Wizard-return activation. V14 land rules and reference fingerprints, v13 selection/engines, v12 combat, live zones and source-ID mana remain active. **This is not a complete Magic rules engine, and the results are not validated deck win rates.**

Both saved presets and compatible local deck files now use the same active engine through the [deck provider](commander_sim/README.md). Local files must pass validation against the bundled identity snapshots; effect coverage remains incomplete.

## Current backend: six-deck shared-effect migration (M2.12–M2.13)

The backend now audits all six pinned Commander deck variants (**448 deck
entries, 299 distinct card names**) with
[`commander_sim.deck_effect_audit`](commander_sim/deck_effect_audit.py).
Oracle-text matching is only a candidate-effect inventory: it is **not**
evidence that an entire card is executable.

The physical bounded runner accepts all six decks for reviewed lands,
mana rocks and source-paid actions, and admits individually reviewed creature
bodies, instant/sorcery tutor spells, and fixed-count token sorceries as
applicable. Five reviewed token-spell recipes share one configurable
token-generation operation: Ral's Reinforcements, Hard Evidence, Strike It
Rich, Moan of the Unhallowed and Army of the Damned. Four separately pinned
cast/copy-trigger suboperations for Young Pyromancer, Talrand, Archmage
Emeritus and Storm-Kiln Artist use shared token/draw operations. Reusable
physical draw, mill, +1/+1 / -1/-1 counter placement, restricted
graveyard-to-hand, destroy/exile/bounce and per-opponent damage primitives
are independently regression-tested, but **not automatically legal or
integrated for every printed card**.

Historical Magnus v35 continues to own its own reviewed multiplayer stack
and trigger timing; the six-deck bounded run has **no opposing priority**.
Flashback, true comprehensive graveyard recursion, death/sacrifice payoff
triggers, Clue/Treasure activations, general replacement and continuous
rules, commander casting, and full all-deck multiplayer gameplay remain
incomplete. No simulated win-rate claim is made.

See the [six-deck common-effect coverage ledger](docs/DECK_COMMON_EFFECT_COVERAGE.md)
for implemented families, test boundaries and the remaining roadmap.
Backend-only migration; the Deck Lab UI is maintained separately.

## Launch Deck Lab — three-page fantasy website

**[Open Commander Deck Lab](https://bgoodnight.github.io/commander-simulator/)** · [Deck Summary](https://bgoodnight.github.io/commander-simulator/docs/deck-lab/index.html) · [Simulation Results](https://bgoodnight.github.io/commander-simulator/docs/deck-lab/results.html) · [Card List & Editor](https://bgoodnight.github.io/commander-simulator/docs/deck-lab/editor.html)

The default landing page is **Deck Summary**, featuring commander artwork, card composition and the printed mana curve. **Simulation Results** is its own page. A **small circular commander portrait at the top** opens a compact selection panel, allowing the cached results to appear much sooner. Your last-used commander and deck are remembered in the browser, with saved versions preferred for new commanders when available. Inspect **11 fixed-seed cached observations** for each of six built-in decks; scroll through charts of observed mana sources, opening hands and mana-value candidates. Select a point on the mana-source curve or use its turn buttons to inspect individual seeds and linked source cards. A second automated story compares first appearance of up to three detected card themes across the opening hand and six turns, with seed and card drill-down; it does not imply those cards were cast. Saved browser-edited decks are clearly marked **no cached observations** and offer a one-click return to the built-in deck's records. The **Deck Summary** page presents commander/card art, composition, mana curve and automatically detected card-type, creature-subtype and rules-text signals. Theme artwork and matching card names open the full cached card details and art; mana costs use Scryfall symbols with a text fallback, and commander color identity is shown by the portrait. The signals show cumulative first appearance in the 11 cached opening hands and draws through turns 3 and 6; they are overlapping metadata patterns, not verified synergies or executed effects. The **Card List & Editor** page offers name/type search, printed Oracle detail, browser-local validated swaps/versions and decklist export. A persistent top navigation carries the selected commander between these real HTML pages. The compact mobile-first design uses an arcane stone-and-brass theme, with synthesized UI sound on by default after interaction; the mute choice is remembered. Reduced-motion preferences are respected.

**Important:** these are **precomputed observations, not actual game simulation**. Edits do **not** get new cached results until processed by the Python simulator. Browser-local saves are not committed to GitHub. Scryfall card art loads remotely when available; explicit new-card metadata lookups are user initiated.

Pages supports **both publishing modes**: an `index.html` at repository root forwards branch-based Pages to the generated `docs/deck-lab/` site, while the [GitHub Pages Actions workflow](.github/workflows/deck-lab-pages.yml) also publishes the same tested static files as a Pages deployment. See [Pages setup, architecture and preview instructions](docs/DECK_LAB_PAGES.md). If Pages is rebuilding, the site may briefly show an older version.

**New bounded six-turn real-action development harness:** Wretched Ranks and Magnus Premium/Budget can now run through a deliberately restricted physical-card kernel: actual pinned 100-card libraries, one-free mulligan, draws, supported basic/Command Tower land plays, and mana-paid hand → stack → battlefield casts for a **small individually Oracle/text-reviewed creature subset**. The output includes per-turn authoritative board snapshots and omissions, **not** an executable full deck, multiplayer turns, or win-rate estimates. **New reusable effect templates** (`commander_sim/effect_templates.py`, `reviewed_rocks.py`, `template_resources.py`) now allow approved mana rocks to be cast and tapped for correct colored/multi-output mana, including Sol Ring, Arcane Signet, Mind Stone, Charcoal Diamond, Commander's Sphere and funded Izzet Signet. The bounded batch reports rocks separately from lands and creatures. A generic, reviewed library-search executor (`template_search.py`) now handles configurable tutor types/colors/mana-value limits and physical target movement, but **tutor spell casting is not yet connected to the six-turn runner**. See [composable templates and limits](docs/GENERIC_EFFECT_TEMPLATES.md). Run `python -m commander_sim.early_game_runner --deck wretched_ranks --seed 7 --turns 6`. For seeded turn-development metrics from those actual limited actions, run `python -m commander_sim.bounded_batch --deck wretched_ranks --seeds 20 --turns 6`. See [analysis contract and limitations](docs/DECK_INTELLIGENCE.md). **The existing public Deck Lab still displays observation-only results**, not these Python runs; Work mode can integrate their backend contracts later.

**M2 source-backed casting fixture (experimental):** `commander_sim.mana_kernel_bridge` plans fixed colored costs from live land object IDs, and `commander_sim.generic_cast` now has a narrowly reviewed creature-cast transaction through the existing indexed kernel zones and stack. The tests demonstrate an actual Swamp-paid hand → stack → battlefield creature transition, while unknown entry/cast effects remain gated. **This is not wired into the v35 gameplay turn driver, does not make Gisa/Mortarion playable, and does not implement full priority, trigger or casting rules.**

**Reproducible development diagnostics:** `python -m commander_sim.progress_metrics --deck wretched_ranks --seeds 100 --turns 6 --mulligan one-free` reports modeled land drops and fixed printed-cost payment preview rates across independent observation seeds (with intervals). These are **not legal casts, real-game progress, win probabilities, or validated deck-strength comparisons**. They establish an early-game measurement baseline while the M3 event-backed runner is developed.

**M2 development resumed:** `commander_sim/mana_costs.py` now parses fixed printed mana symbols in all five colors plus **true colorless** and generic mana, returning a deterministic, read-only feasible assignment of reviewed sources. The six-turn `commander_sim/observation.py` reports separate `source_paid_mana_preview` entries for known basic/Command Tower sources. These are **not legal casts**: timing, effects, alternative/extra costs, priority and other nonbasic sources are not modeled. Next integrate into the existing v35-derived live kernel and demonstrate a real Swamp-paid ordinary creature cast before labeling multi-deck play implemented.

**Historical card migration (M2.7):** Seven previously separate tutor/search implementations in the existing v17–v35 gameplay tables now delegate to one parameterized search operation, including Mystical Tutor, Personal Tutor, Merchant Scroll, Solve the Equation, Fabricate, Step Through wizardcycling and Spellseeker. Five previously hardcoded mana-rock abilities (Sol Ring, Izzet Signet, Talisman of Creativity, Mind Stone, Arcane Signet) now reuse the same pinned `ManaMode` definitions as the bounded early-game backend through a compatibility adapter. Five tutor profiles also share their exact reviewed parameter declarations across old and new engines. Timing, priority, triggers, payment, and live zones remain owned by the original engine; this is a reuse/refactoring milestone rather than full new-card support. See [template migration details](docs/GENERIC_EFFECT_TEMPLATES.md).

**Common effect migration (M2.8):** More historical cards now reuse typed operations in `commander_sim/legacy_common_ops.py` for drawing/discarding, creating tokens, reducing generic costs, sacrificing objects and transferring cards between zones. Reviewed examples include Consider, Brainstorm, Preordain, Frantic Search, Baral, Fiery Islet, Ral's Reinforcements, Sapphire Medallion, Phyrexian Altar, Mystic Sanctuary, Riptide Laboratory and Step Through. The existing kernel remains the only owner of physical cards, while each old card's triggers, choices and timing remain governed by its historical rules. See [M2.8 implementation and limits](docs/GENERIC_EFFECT_TEMPLATES.md).

**Trigger, recursion and copy migration (M2.9):** Shared token spawning now backs the v7 triggered-token kernel and Mage Siege, while Mystic Sanctuary's graveyard return uses an explicit instant/sorcery zone-transfer restriction. Historical v33 and v35 Reiterate use the same typed virtual spell-copy and retargeting operations, preserving full stack/priority ownership and copied-not-cast events. New-card effects are never inferred automatically; this is a validated refactor of existing implemented cards. See [M2.9 in the generic effect architecture](docs/GENERIC_EFFECT_TEMPLATES.md).

**Ability-level composition (M2.10):** The backend now has immutable reviewed card ability slots, separate exact/simplified/unsupported coverage per ability, exact-first promotion, capability checks, dispatch provenance and per-instance trigger subscription deduplication in [`commander_sim/ability_composition.py`](commander_sim/ability_composition.py). Five previously implemented historical tutors now obtain their reviewed search behavior via the slot resolver. Mind Stone and Commander's Sphere expose supported mana behavior separately from unimplemented sacrifice/draw behavior. This is a tested composition core, **not yet full live per-event dispatch or arbitrary new-card execution**. See the [ability composition architecture](docs/ABILITY_COMPOSITION_ARCHITECTURE.md).

**First live ability-slot trigger dispatch (M2.11):** `commander_sim/live_trigger_bridge.py` now integrates pinned Baral optional loot and Archmage Emeritus Magecraft draw triggers with the existing v13–v35 rules stack. Existing trigger creation, timing, Harmonic Prodigy doubling, responses, source-last-known information and actual state mutations remain kernel-owned; per-slot exact handlers record successful invocation provenance and avoid duplicate source/hook subscriptions. New and unsupported card effects are not inferred from Oracle text. See the [ability architecture](docs/ABILITY_COMPOSITION_ARCHITECTURE.md) and the full regression suite.

## Current priority: practical multi-deck MVP and Deck Lab

The active product order is **shared offline Scryfall cache → validated imports for Magnus/Mortarion/Gisa/Necrons → early read-only Deck Lab viewer → deck editing and explicit card imports**, while the core advances toward **source-paid basic turns for each deck**. Then deliver visual deck comparisons and **single-deck event-backed replay**. Full two-detailed-deck head-to-head is **optional and deferred** until the interface is useful; it is not required for a usable simulator. A read-only preview must label observations accurately, and only source-paid actions in the shared engine qualify as actual simulated turns. Exhaustive named-card implementations also remain later work.

**Theorycraft a new deck (cache-first):** `python tools/theorycraft.py my_deck.txt --commander "Ghoulcaller Gisa"`. This imports exact missing identities **once on first preflight** and runs a labeled offline observation. Add `--offline` to prohibit new Scryfall requests. For the full 35,533-name cached autocomplete index, see [card discovery guide](docs/CARD_DISCOVERY_AND_THEORYCRAFT.md); the separate one-shot refresh command is `python tools/refresh_card_names.py`.

**Use the U1 local Deck Lab editor:** preview a one-for-one cached-card swap, undo/revert, and Save As a separate immutable local variant without changing a canonical decklist. Saved copies can be observed with the same deterministic (not full-game) runner. [Editing and Work browser preview](docs/DECK_LAB_U1.md). Missing-card imports from the browser remain U2; the existing CLI theorycraft preflight already supports them.

**Launch the local Deck Lab:** from the repository root, run `python tools/deck_lab.py`, then open **http://127.0.0.1:8765/** on that computer. Requires Python 3.11+ and no third-party packages. [U0 usage and limitations](docs/DECK_LAB_U0.md).

- [Product-first roadmap](ROADMAP.md) and [Multi-deck MVP gates](docs/MULTI_DECK_MVP.md)
- [Deck Lab UI milestones](docs/USER_INTERFACE_ROADMAP.md): **U0 viewer**, **U1 versioned deck editing**, **U2 explicit local-first Scryfall lookup/import**, then **U3/U4 richer visuals and replay**
- [Bounded Work-session handoff](docs/LOW_CREDIT_IMPLEMENTATION_HANDOFF.md) and [coding-agent instructions](AGENTS.md)
- [Progressive per-ability architecture](docs/ABILITY_COMPOSITION_ARCHITECTURE.md)

**Status:** M0 offline caching and **M1 six-deck pinned imports are complete** ([import report](simulator/card_data/m1_import_report.json)). The local U0/U1 Deck Lab has six deck selections, printed metadata, deterministic observations, **offline typeahead against 35,533 Scryfall card names**, and a reversible one-for-one deck editor with strict validation, immutable Save As and observations of saved copies. New `tools/theorycraft.py` checks the shared Oracle-ID catalog before the **first preparation of a modified deck**, automatically fetches exact missing card metadata unless `--offline` is selected, and reuses a hash-pinned manifest on later runs. **This does not cast spells or implement new card abilities.** The pure `commander_sim.abilities` selector is not an executable hybrid engine; historical v35 gameplay is Magnus-oriented and source-paid black/mixed-deck play remain M2/M3 work. No metadata API requests occur during a turn, existing offline game/observation, page load or typing.

## V35 copied spell targets

[Copy target handling](simulator/v35_copy_targets/README.md) adds target changes for copied counterspells, two-target Step Through copies, Abrade and Reiterate copies. See the [coverage audit](simulator/v35_copy_targets/CARD_COVERAGE.md).

## V34 Mage Siege

[Mage Siege](simulator/v34_mage_siege/README.md) adds the Adventure, Wizard damage triggers, and Lindblum land play from Adventure exile. See [coverage](simulator/v34_mage_siege/CARD_COVERAGE.md) and the [interaction report](simulator/v34_mage_siege/INTERACTION_REPORT.md).

## V33 Reiterate

[Reiterate](simulator/v33_reiterate/README.md) copies selected supported spells with optional buyback. See [coverage](simulator/v33_reiterate/CARD_COVERAGE.md) and the [interaction report](simulator/v33_reiterate/INTERACTION_REPORT.md).

## V32 Cyclonic Rift

[Cyclonic Rift](simulator/v32_cyclonic_rift/README.md) supports both target and overload modes. See [coverage](simulator/v32_cyclonic_rift/CARD_COVERAGE.md) and the [source-paid interaction](simulator/v32_cyclonic_rift/INTERACTION_REPORT.md).

## V31 premium deck configuration

The current simulator defaults to the [v1.14 premium list](decklists/magnus_thousand_sons_v1_14_premium.txt), committed as `b9b3ba0abcd19676ec4f32cc9f427e52c1f55d8b`. [Configuration, validation, and limits](simulator/v31_premium_deck/README.md); [coverage audit](simulator/v31_premium_deck/CARD_COVERAGE.md). Run `python run_simulation.py`; select the preserved v1.13 version with `python run_simulation.py --deck budget`. Use `python run_simulation.py --deck-file PATH` for a list containing only cards covered by the bundled identity snapshots. The budget preset now uses the v35 engine; historical budget engines remain available for regression.

## V30 Phyrexian Altar

[Phyrexian Altar](simulator/v30_phyrexian_altar/README.md) casts and converts creature sacrifices to blue or red mana without tapping. The printed five-color ability is partial because the current mana pool is U/R/colorless only. See [coverage](simulator/v30_phyrexian_altar/CARD_COVERAGE.md) and the [interaction report](simulator/v30_phyrexian_altar/INTERACTION_REPORT.md).

## V29 Step Through and cycling

[Step Through and cycling triggers](simulator/v29_step_cycling/README.md) adds the two-target sorcery and a bounded cycling trigger event. See [coverage](simulator/v29_step_cycling/CARD_COVERAGE.md) and the [interaction report](simulator/v29_step_cycling/INTERACTION_REPORT.md).

## V28 Spellseeker

[Spellseeker](simulator/v28_spellseeker/README.md) adds its optional Wizard enter-the-battlefield search. See the [coverage audit](simulator/v28_spellseeker/CARD_COVERAGE.md) and [interaction narrative](simulator/v28_spellseeker/INTERACTION_REPORT.md).

## V27 artifact and Wizard searches

[Fabricate and wizardcycling](simulator/v27_wizard_tutors/README.md) add artifact and Wizard searches. At v27, Step Through’s sorcery mode remained unsupported. See [coverage](simulator/v27_wizard_tutors/CARD_COVERAGE.md) and the [interaction report](simulator/v27_wizard_tutors/INTERACTION_REPORT.md).

## V26 search to hand

[Merchant Scroll and Solve the Equation](simulator/v26_search/README.md) add two source-paid search paths. See the [current audit](simulator/v26_search/CARD_COVERAGE.md) and [interaction narrative](simulator/v26_search/INTERACTION_REPORT.md).

## V25 Personal Tutor

[Personal Tutor](simulator/v25_personal_tutor/README.md) searches for a sorcery with an explicit choice and fail-to-find handling. See [coverage](simulator/v25_personal_tutor/CARD_COVERAGE.md) and the [interaction report](simulator/v25_personal_tutor/INTERACTION_REPORT.md).

## V24 Ral's Reinforcements

[Reinforcements](simulator/v24_reinforcements/README.md) adds two blue/red Elemental tokens and a token-color seam. See the [coverage audit](simulator/v24_reinforcements/CARD_COVERAGE.md) and [interaction report](simulator/v24_reinforcements/INTERACTION_REPORT.md). Simultaneous-entry effects remain incomplete.

## V23 Sapphire Medallion

[Sapphire Medallion](simulator/v23_medallion/README.md) reduces generic costs of printed blue v1.13 spells. See the [coverage audit](simulator/v23_medallion/CARD_COVERAGE.md) and [interaction report](simulator/v23_medallion/INTERACTION_REPORT.md). Color-changing effects remain unsupported.

## V22 Consider

[Consider](simulator/v22_consider/README.md) adds a one-mana instant with surveil, draw and an explicit choice policy. See the [current coverage audit](simulator/v22_consider/CARD_COVERAGE.md) and [interaction report](simulator/v22_consider/INTERACTION_REPORT.md).

## V21 early mana

[Frostboil Snarl](simulator/v21_early_mana/README.md) now supports its reveal, entry and mana abilities. The [v1.13 coverage audit](simulator/v21_early_mana/CARD_COVERAGE.md) records remaining gaps.

## V20 verified identities

[VerifiedTable](simulator/v20_verified_types/README.md) checks v1.13 against an Oracle snapshot and supplies verified types for library searches. Other runtime characteristics and unsupported card effects remain incomplete; see [coverage](simulator/v20_verified_types/CARD_COVERAGE.md).

## V19 card-data verifier

The [Oracle snapshot verifier](simulator/v19_card_data/README.md) checks identities, types, color identities and Commander legality when supplied an authoritative snapshot. See v20 for the processed snapshot and remaining implementation gaps.

## V18 canonical budget deck

The preserved [v1.13 budget list](decklists/magnus_thousand_sons_v1_13_budget.txt) is loaded by [BudgetTable](simulator/v18_budget_deck/README.md). This historical v18 adapter retains 29 inert unverified placeholders; v20 adds verified card types. See the [v1.13 audit](simulator/v18_budget_deck/CARD_COVERAGE.md) and [assessment](simulator/v18_budget_deck/ASSESSMENT.md). Prior tables retain historical decks for regression.

## V17 tutor

[Mystical Tutor](simulator/v17_tutor/README.md) adds instant-speed search with resolution-time choice and shuffle; see [current coverage](simulator/v17_tutor/CARD_COVERAGE.md), [interaction narrative](simulator/v17_tutor/INTERACTION_REPORT.md), and [validation](simulator/v17_tutor/validation_results.json).

## V16 channel

[Channel implementation](simulator/v16_channel/README.md) adds Otawara and Sokenzan as a bounded subset, with known token-color and metadata limits. See its [interaction report](simulator/v16_channel/INTERACTION_REPORT.md) and [coverage audit](simulator/v16_channel/CARD_COVERAGE.md) for validation and remaining gaps.

## Current architecture and scope

- [V15 utility-land README](simulator/v15_utility/README.md) — Sanctuary target timing, Islet costs and Riptide target rechecks.
- [Historical v15 Magnus coverage](simulator/v15_utility/CARD_COVERAGE.md) — 41 supported subsets, 7 partial, 35 unsupported names.
- [V15 interaction report](simulator/v15_utility/INTERACTION_REPORT.md) — six narratives, live sweep and runtime.
- [V15 assessment](simulator/v15_utility/ASSESSMENT.md) — validation and remaining limits.

- [V14 land README](simulator/v14_lands/README.md) — individual entry checks, basic types, life/face choices and Passage costs/resolution.
- [Historical v14 Magnus coverage](simulator/v14_lands/CARD_COVERAGE.md) — 38 supported subsets, 10 partial and 35 unsupported names.
- [V14 interaction report](simulator/v14_lands/INTERACTION_REPORT.md) — seven source-paid stories, live sweep and timing.
- [V14 assessment](simulator/v14_lands/ASSESSMENT.md) — results, remaining scope and pre-optimization reference.
- [Reference cases](simulator/v14_lands/REFERENCE_CASES.json) and [performance history](simulator/v14_lands/PERFORMANCE_HISTORY.json) — deterministic outputs for later caching comparisons; no new caching yet.

- [V13 selection/engines README](simulator/v13_engines/README.md) — exact resolution choices and focused missing engine text.
- [Historical v13 Magnus card coverage](simulator/v13_engines/CARD_COVERAGE.md) — 32 supported subsets, 16 partial and 35 unsupported distinct names.
- [V13 interaction report](simulator/v13_engines/INTERACTION_REPORT.md) — seven source-paid stories, including five selection branches, plus the live sweep.
- [V13 assessment](simulator/v13_engines/ASSESSMENT.md) — validation, timing and remaining limits.

- [V12 combat/audit README](simulator/v12_combat/README.md) — allocation choices, trample and two damage steps.
- [Historical v12 card coverage and triage](simulator/v12_combat/CARD_COVERAGE.md) — all 100 cards: 23 supported subsets, 25 partial and 35 unsupported distinct names.
- [V12 interaction report](simulator/v12_combat/INTERACTION_REPORT.md) — six targeted narratives, source payments and the live sweep.
- [V12 assessment](simulator/v12_combat/ASSESSMENT.md) — validation, timing and remaining limits.

- [V11 steps/cards README](simulator/v11_steps/README.md) — ordinary turn windows, combat batch and the focused card/rule expansion.
- [V11 interaction report](simulator/v11_steps/INTERACTION_REPORT.md) — observed results from five targeted stories and the seeded sweep.
- [V11 assessment](simulator/v11_steps/ASSESSMENT.md) — validation, fixes, efficiency and remaining limits.
- [V10 priority README](simulator/v10_priority/README.md) — four-seat passes, APNAP triggers, instant responses and registered activated frames.
- [V10 assessment](simulator/v10_priority/ASSESSMENT.md) — stack/priority validation, conservation sweep, timing and remaining gates.
- [V9c source-mana README](simulator/v9c_mana/README.md) — live source objects and bounded ordered mana-ability payment for every seat.
- [V9c assessment](simulator/v9c_mana/ASSESSMENT.md) — acceptance tests, conservation/payment sweep, efficiency review and remaining boundaries.
- [V9b live-zone README](simulator/v9b_live/README.md) — authoritative live inventories, read-only card projections, physical spell/permanent identity and 34 migration tests.
- [V9b assessment](simulator/v9b_live/ASSESSMENT.md) — correctness review, 400-game conservation sweep, timings and next gates.
- [V9a README](simulator/v9_kernel/README.md) — portable Magnus seat, central object-zone operations, bounded source-specific mana prototype, 29 focused new tests and four narrated games.
- [V9a assessment](simulator/v9_kernel/ASSESSMENT.md) — validation, limitations, and next integration gates.
- [V8 README](simulator/v8_central/README.md) — persistent shared battlefield, four-seat turn driver, bounded counterspell stack, and baseline implementation.
- [V8 assessment](simulator/v8_central/ASSESSMENT.md) — original limitations and confidence boundaries.
- [V7 rules kernel](simulator/v7_rules/README.md) — reusable rule primitives and safe finite loop infrastructure.
- [Real Magnus deck integration](simulator/v6_real_deck/README.md) — original partial real 99-card adapter.
- [Magnus v1.6 decklist](decklists/magnus_thousand_sons_v1_6.txt), [v3 card catalog](simulator/v3_magnus_modular/cards.json), and [candidate combo lines](simulator/v3_magnus_modular/combos.json).

**Historical v15 limits:** one detailed Magnus deck plus synthetic opponents. Sanctuary, Fiery Islet and Riptide Laboratory join the prior individual land-entry rules and Fabled Passage. Channel, full double-faced/layer/replacement behavior, spell-copy producers, full legend/Commander rules, attachments and verified loops remain absent or partial as audited. No additional caching is introduced; v14 reference outputs are preserved for later optimization. No deck win-rate conclusions are supported.

## Progressive card-ability foundation (P0.65)

The new `commander_sim.abilities` pure catalog registers stable per-card-face ability slots and reviewed exact or simplified descriptors, then selects **at most one** implementation per slot for strict, observation or hybrid mode. This **does not execute the selected behavior or turn on hybrid mode in the live engine**. See the [progressive composition architecture](docs/ABILITY_COMPOSITION_ARCHITECTURE.md), [coding-agent contract](AGENTS.md), and [low-credit implementation handoff](docs/LOW_CREDIT_IMPLEMENTATION_HANDOFF.md). Full per-card rules and source-paid black mana remain future work.

## Package extraction

The new `commander_sim` package provides a deck-independent service registry and an isolated compatibility adapter for running existing engines. The live rules still run through the historical implementation; this is the first extraction seam, not a completed engine migration.

## Verified temporary-deck data

The authoritative [Flameslinger v0.7 list](decklists/fixtures/magnus_flameslinger_v0_7_pre_delivery.txt) has an [offline identity snapshot](simulator/card_data/flameslinger_v0_7_scryfall.json) with 76 verified distinct names. Run `python -m commander_sim.snapshots decklists/fixtures/magnus_flameslinger_v0_7_pre_delivery.txt simulator/card_data/flameslinger_v0_7_scryfall.json` to check the exact deck hash, count, singleton, color identity and legality. This validates identity only; v0.7 is not yet loadable into the live rules engine. A narrow [observation example](simulator/card_data/OBSERVATION.md) tracks draws, basic lands and Command Tower without resolving spells or pretending candidates are legal plays.

The authentic [Gisa precon](decklists/wretched_ranks_foundations_precon_2026.txt) and [Mortarion purchase-reconciled candidate](decklists/mortarion_purchase_reconciled_candidate_2026_10_27.txt) also have hash-matched offline identities and limited observation traces. The Mortarion file is a candidate, not a confirmed physical deck. These do not enable black-mana execution or mono-black play in the live engine.

## Current-engine baseline

The [P0 baseline](simulator/p0_baseline/README.md) contains four frozen premium-deck replay fingerprints, provider integration checks, and a reproducible diagnostic benchmark.

## Run all tests

Requires Python 3.10+ and only the standard library:

```bash
python run_all_tests.py
```

**891 tests across thirty-seven suites** (v3:20, v4:15, v5:21, v6:21, v7:50, v8:32, v9a:29, v9b:34, v9c:49, v10:51, v11:50, v12:50, v13:69, v14:56, v15:38, v16:14, v17:6, v18:5, v19:5, v20:4, v21:10, v22:8, v23:13, v24:9, v25:7, v26:12, v27:14, v28:11, v29:9, v30:11, v31:15, v32:11, v33:12, v34:14, v35:6, P0 baseline:11, package contracts:99). The GitHub Actions workflow tests on Python 3.11, 3.12, and 3.13.

Run historical v15 and reproduce validation:

```bash
python simulator/v15_utility/tests.py
python simulator/v15_utility/coverage.py
python simulator/v15_utility/validate.py
```

The v15 validator writes six targeted interaction stories, JSON diagnostics, an interaction report and validation_results.json. By default it checks 200 twelve-round games across all Magnus seats and compares 12 eight-round timing samples per engine. V14 reference fingerprints remain preserved. These are infrastructure diagnostics.

## Preservation and methodology

Milestones are versioned under `simulator/`. The pre-v15 rollback point is `b0b0237ee915532b4d2f4ca3b089999671294b27`. V15 adds a utility-land provider/table and backward-compatible trigger target-preparation seam; existing cache implementations remain untouched. Historical suites pass; dated manifests remain checkpoint records. Earlier engines remain standalone; old synthetic calibration reports are **not empirical Commander metagame data**. The user prioritizes rule correctness, consistent shared state, narrated diagnostics, card coverage accounting, bounded computation, and normal rollback-safe commits. The [Google Drive recovery folder](https://drive.google.com/drive/folders/1Jy4spPc58pOKSvDOAwQXaBVlj_4pVU5Y) retains dated checkpoints.

## Development roadmap

See the [architecture-first roadmap](ROADMAP.md) for ordered implementation phases and acceptance gates. The [October 31 architecture audit](docs/ARCHITECTURE_AUDIT.md) records confirmed defects, expansion limits and measured runtime pressure. The [internal development guide](docs/DEVELOPMENT_GUIDE.md) specifies reusable effects, keyword templates and the workflow for future cards. Stabilize provider composition and extract a deck-independent engine before another broad card batch; preserve historical engines and current premium references throughout.
