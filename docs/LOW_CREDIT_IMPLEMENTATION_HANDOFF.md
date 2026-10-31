# Low-credit implementation handoff — cache-first multi-deck MVP

Updated October 31, 2026. **Priority is an early usable multi-deck simulator**, not exhaustive card effects. This is a work-session handoff; follow [MULTI_DECK_MVP.md](MULTI_DECK_MVP.md) for acceptance gates, [ROADMAP.md](../ROADMAP.md) for current progress, and [AGENTS.md](../AGENTS.md) / [ABILITY_COMPOSITION_ARCHITECTURE.md](ABILITY_COMPOSITION_ARCHITECTURE.md) for architectural rules.

## Verified work already in the repository

- Deck injection for premium/budget and compatible verified Magnus lists; comment-tolerant deck parser (`commander_sim/decks.py`) and tests.
- Offline Scryfall snapshot and identity validation, immutable `CardRegistry`, tri-state `Query`, narrow U/R live-library verified creature bridge, deterministic **observation only** (not gameplay).
- **New pure `commander_sim.abilities` seam**: immutable `AbilityKey(oracle_id, face_id, slot_id)`, reviewed `AbilitySlot` and `AbilityHandler` declarations, frozen `AbilityCatalog`, `Mode.STRICT/OBSERVATION/HYBRID`, and deterministic exact-first one-handler-per-slot selection. It **does not execute effects**; selection-level tests live in `tests/test_abilities.py`. Future implementation should extend this interface rather than add a competing resolver.
- The ability slots **must not be inferred automatically from Scryfall text or role tags**. A reviewed definition/ability catalog is still missing.
- Package-test expected-count contract lives in `run_all_tests.py`. **When adding tests, update the package_tests expected count and final total**, then verify the CI run; do not mistake count mismatch for a rules regression.

**Current completed milestones:** M0 metadata cache, **M1 six-deck import** (official one-time Scryfall import run, all six 100-card decks pinned and validated, commit `b204f36`), and initial **U0 read-only Deck Lab** (local static browser UI and Python standard-library server, verified offline deck details and observation endpoints). See [DECK_LAB_U0.md](DECK_LAB_U0.md). **U1 one-for-one editor and immutable Save As are now implemented; the next high-value action is real-browser visual inspection, followed by U2 first-run import integration**, independently of M2 source-paid black gameplay. M2/M3 can progress as a separate engine track, but do not claim an observation is a played game. Do not redo completed M0/M1/U0 work.

## Bounded next Work sessions — execute in priority order

**Do not begin with the old Slice A per-card directory.** The pure `commander_sim.abilities.AbilityCatalog` already exists and is adequate as the starter ability-selection seam. Defer broad named-card definitions while we deliver actual basic gameplay for two different commanders. Complete one coherent slice per Work session; stop at a passing commit with coverage and the next handoff.

### Slice 0 — DONE: shared offline card catalog implementation (M0)

**Goal achieved at code/test level (851 total suite tests):** `commander_sim.card_cache` + cache-first importer and revision-pinned manifests are committed; overlapping deck/replay/no-network regressions pass. **Do not redo the cache architecture.** M1 still must **populate** a real shared local catalog by seeding already checked-in snapshots, then import missing names only via explicit commands. [Usage guide](CARD_METADATA_CACHE.md). The steps below remain historical acceptance details.

1. Inspect existing `tools/fetch_deck_identities.py`, `commander_sim/snapshots.py`, `commander_sim/identities.py` and checked-in snapshots. The present per-deck snapshots hash the exact deck; do not destroy that invariant or fetch again when a card appears elsewhere.
2. Implement a **shared, immutable, versioned offline Scryfall record store keyed by Oracle ID**, with a name/face-alias index. Import code checks this store **before** any optional network request. Fetch unresolved names in batches only on explicit import/refresh, normalize and validate the exact identity; save a pinned **deck file SHA-256 → Oracle ID + record revision** manifest. An absent cached Oracle ID is allowed only in offline mode with an explicit diagnostic, not a silent guess.
3. Preserve old snapshot fixture validation and strict replay. Keep metadata cache read-only during a run; separate explicit refresh from normal load. Do **not** implement runtime action/target memoization.
4. Write mocked-network tests for: first missing fetch; second identical import **zero requests**; another overlapping deck fetches **only new identities**; unchanged hashes and immutability; ambiguities/revisions fail closed; zero network in a six-turn observation and game-start/replay path.
5. Run targeted tests and the 37-suite regression runner, update expected test count, commit and stop. A runtime card effect implementation is **out of scope**.

**Exit achieved for implementation/tests:** the API is used only on explicit import/refresh, repeated and overlapping imports reuse local verified records, and simulations read only offline data. A populated catalog covering all real deck variants is M1 work.

### Slice 1 — DONE: all six decks are imported with honest observations (M1)

1. Make validated snapshots/catalog manifests for **Magnus premium/budget, Wretched Ranks, Mortarion current and ideal, Necron Dynasties**. Separate receipt-only Mortarion snapshots aren't valid for different deck SHA values. Reconcile ambiguous card faces/legality; no invented properties.
2. Generalize the deck provider's validated commander/color identity without selecting a Magnus-specific engine; preserve one composition interface and exact 100-card/legality/identity checks.
3. Provide seed-replayable six-turn deck/hand/source **observation** from each deck, including imported but unsupported cards, with first unmodeled action and counts. Do not label metadata-only candidates legal or resolved.
4. Add a simple CLI/listing command to enumerate all fixtures and their capabilities/metadata gaps; targeted and CI tests, commit and stop.

**Exit:** arbitrary reviewed decklists can be loaded and inspected offline; this **is not** actual multi-deck gameplay.

### Slice 2 — Shared mana, legal ordinary casting and interactable bodies (M2)

1. Parameterize the existing v35 authoritative engine for different commanders/decks; generalize mana source/payment for W/U/B/R/G/C including Swamps, **true colorless** and generic costs (do not confuse them). Reuse existing action/priority/stack/zone objects; no parallel simulation engine.
2. Load verified safe creatures/permanents with actual types/subtypes, colors, mana cost/value, P/T and recognized keywords. Keep an unfamiliar card's unique effects independently unsupported. Allow body-only hybrid casting only if known mandatory ETB/static/replacement/cost restrictions do not make the approximation illegal or unsafe.
3. Integrate shared type/subtype/color/mana/P/T queries for tutors/removal, including **opponent** interactions with unfamiliar objects. UNKNOWN target restrictions or missing mandatory rules must fail closed; supported flying/menace/double strike/etc. uses common rules once implemented, never card-name branches.
4. Validate Magnus strict replay parity and a **real Swamp-paid ordinary creature cast** from Wretched Ranks, with an ordinary attack/target/death; prove card/zone conservation and deterministic replay. Commit and stop.

**Exit:** source-paid simple early turns for both Magnus and a mono-black deck are possible under the same kernel.

### Slice 3 — MVP 1: practical first-six-turn multi-deck tests (M3)

1. Build one generic early-turn runner/pilot using shared legal-action enumeration. Keep existing abstract opponents if needed, explicitly labeled. It must not grant unimplemented effect text; unknown effects can be omitted with fidelity provenance or block actions when required.
2. Use current pure `AbilityCatalog` as the **single** per-slot selection mechanism; wire **only a few reviewed common templates** (draw, mana source, ordinary creature token/removal) needed for early utility and tests. Exact first; simplified fallback only for reviewed safe slots; no double-execution.
3. Produce a six-turn **actual game** narrative for Magnus and Wretched Ranks, then Mortarion current and Necrons as capabilities permit. Report draws, mana, legal source-paid casts, ordinary combat, supported effects, omissions, first materially changed choice and uncertain targets.
4. Run a focused 10–100-seed repeatability check after one source-paid narrative passes. No early win-rate or relative power claims. Commit and stop.

**Exit:** two authentic different commander lists generate meaningful reproducible turns under the same actual rules engine.

### UI Slice U0 — DONE: launchable offline read-only Deck Lab (U0)

Implement a thin local browser UI **as soon as M1 validates the deck catalog and observations**, not after M3: deck variant chooser, commander/legality/cache/ability-support summary, seed/horizon and **only currently supported modes**, observation timeline and export. When M3 actual actions exist, upgrade this **same viewer** with actual-versus-observation traces. No new game logic in UI, no Scryfall calls on navigation or run, no invented full-game outcomes. Compare a CLI run and UI result for exactly the same seed/deck/mode. Commit and stop. UI planning: [USER_INTERFACE_ROADMAP.md](USER_INTERFACE_ROADMAP.md).

### Ready-to-reuse discovery feature (U2 backend, not full UI)

`commander_sim/card_discovery.py`, `tools/theorycraft.py`, `commander_sim/card_name_catalog.py`, and `tools/refresh_card_names.py` are now implemented. **A first explicit deck preparation automatically imports missing exact card details into the shared catalog**, pins a new deck-hash snapshot, and reuses it with zero requests on rerun; `--offline` fails if a card isn't cached. The Deck Lab local typeahead uses cached detailed records and optionally the once-fetched complete Scryfall card-name list, not Scryfall requests per key. See [discovery guide](CARD_DISCOVERY_AND_THEORYCRAFT.md). Do **not** duplicate network logic or rewrite these services in U1/U2. The name-only catalog suggests canonical names but **does not assert rule coverage, Commander legality or card ownership**.

### UI Slice U1 — DONE: editable swaps and hash-pinned Save As (visual review pending)

Add/remove cards **already in the verified offline catalog**, perform Commander singleton/count/color-identity/commander legality validation via the shared `DeckProvider`, display before/after diff and mana/type summaries, and **Save As** a new version with an exact deck SHA/pinned catalog manifest. Keep canonical Magnus, Mortarion Current/Ideal and factory precon fixtures untouched. Never infer that a user owns a card just because it appears in an ideal or Scryfall-backed list. Commit with round-trip/invalid-save tests.

### UI Slice U2 — Explicit local-first fetch for new cards (after U1 and M0)

First search names and face aliases in M0's local Oracle-ID catalog. If absent, present a **user-triggered** `Fetch from Scryfall` flow, reviewed card identity/face/legality details and error handling; update cache and a **new** deck manifest only after appropriate confirmation/save. No API on typing/autocomplete, page load or simulation. Test cached lookups use zero calls, missing import makes bounded calls and network failure leaves deck unchanged. Commit and stop. **U0/U1/U2/U3 and the solo portion of U4 are more important than detailed head-to-head or exhaustive unique-card rules.**

### UI Slices U3/U4 — Better visualization and single-deck board replay (higher priority than M4)

**U3 (after U2):** compact mana curve, card types, coverage/fidelity and early-turn timeline; compare deck variants at matched seeds, explicitly distinguishing observation/proxy from actual engine effects. Support readable light/dark, keyboard/mobile layout; no custom table animations required. **Requires no head-to-head engine.**

**U4 (after M3 actual events):** for **one detailed deck** show battlefield, stack, zones, card/object details and replay controls from the **authoritative** event/state output. Mark abstract opponent seats explicitly. UI actions call existing legality/priority APIs; never mutate a parallel board model. Commit visuals in independently testable slices. **Requires no second detailed deck.**

### Optional deferred Slice 4 — Real cross-deck play (M4; NOT needed for usable UI)

Do not begin head-to-head by default. If it is reprioritized **after U0–U4 are useful**, give two **detailed** seats independently configured authentic decks with shared turn/priority, targets, attacks/blocks, stack and zone state. Preserve unsupported/approximation logs; keep original source-paid solo-replay correctness. Commit one repeatable mixed-deck scenario; no unique-card engine subclasses.

### Slice 5 — Deepen individual effects and performance (M5/M6; after practical U0–U4)


- Extend the card directory only for **observed high-impact missing behavior**, and compose shared effect templates. Test common keyword persistence across exact/simplified promotion and exclusive one-tutor-one-search events; add at least two independently named cards per reusable mechanic.
- Tune and compare with paired seeds and explicit fidelity/coverage reports before making deck-strength or optimization claims. Defer speculative mutable game-state caching to an invalidation/replay-tested phase.

## Efficient model allocation (heuristic, not a guaranteed credit price)

- **Fast/economical model, low reasoning**: inspect CI logs, update tests/README, compare fixture counts, small safe documentation edits.
- **Terra low or medium**, if offered: implement Slice A/B narrowly, pure registry, tests, mechanical extraction and simple fixtures. Demand a commit and proof of targeted tests.
- **Sol medium/high**, if offered: review ABI/handler semantics, strict/hybrid precedence, event/priority/zone invariants, performance calibration and architectural boundary crossings. Prefer targeted diff review after 2–4 coherent implementation commits rather than re-reading the full repository after each.
- **Astra low/medium** only when needed: investigate subtle Magic rules bugs, cross-service invariants, unsolved design conflicts or difficult regression failures. Use high reasoning only if lower effort demonstrably fails.
- Avoid **Fast/Ultrafast** unless latency matters more than allowance. Don't assume more reasoning always improves simple coding changes.
- Work/Codex model selection and credits are account-dependent; check **Settings > Usage** for actual remaining five-hour/weekly allowance. Model switches **do not** restore a shared usage pool. The user's Chat conversation can be used for planning without initiating a cloud Work coding task.

## Next Work session: visual review of Deck Lab

Use [Deck Lab U1](DECK_LAB_U1.md) and the current main branch. Run the local Deck Lab server and open it in the Work browser. Inspect the actual desktop/mobile layout, test valid and invalid Gisa card swaps, undo/revert, Save As and observing a saved version. Compare displayed data with the CLI and run the complete regression suite. Commit only observed defects and stop.

## Subsequent development milestone: U2 browser card import

Connect the existing offline name suggestions and `prepare_theorycraft_deck` first-run missing-card importer to U1 draft preparation. Only a user-submitted new deck preparation may trigger Scryfall, not typing or simulation. Confirm Commander legality, cache/version pinning and rollback on failure. No new special-card rule implementations.

## Stop conditions / avoiding wasted credits

- Stop and report if a key authoritative deck file or metadata is missing or ambiguous; do not guess Oracle rules or invent ownership.
- Stop after **one coherent slice and successful tests**; keep unresolved topics in a handoff rather than beginning another unrelated card batch.
- Do not run a giant 1,000+ game campaign before one convincing, source-paid seed narrative; leave performance optimization for measured hotspots.
- Use focused file paths and latest diffs rather than reading every historical engine version.
- On failing CI, inspect **the failing job log and targeted test first**. Distinguish test-count bookkeeping failures from semantic bugs and fix only the relevant issue.
