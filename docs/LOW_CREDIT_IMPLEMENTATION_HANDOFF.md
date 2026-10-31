# Low-credit implementation handoff — P0.6 / P0.65 / P0.7

Updated October 31, 2026. This is a **work-session handoff**, not a statement that the full architecture is implemented. Use [AGENTS.md](../AGENTS.md), [ROADMAP.md](../ROADMAP.md), and [ABILITY_COMPOSITION_ARCHITECTURE.md](ABILITY_COMPOSITION_ARCHITECTURE.md) as authoritative design constraints.

## Verified work already in the repository

- Deck injection for premium/budget and compatible verified Magnus lists; comment-tolerant deck parser (`commander_sim/decks.py`) and tests.
- Offline Scryfall snapshot and identity validation, immutable `CardRegistry`, tri-state `Query`, narrow U/R live-library verified creature bridge, deterministic **observation only** (not gameplay).
- **New pure `commander_sim.abilities` seam**: immutable `AbilityKey(oracle_id, face_id, slot_id)`, reviewed `AbilitySlot` and `AbilityHandler` declarations, frozen `AbilityCatalog`, `Mode.STRICT/OBSERVATION/HYBRID`, and deterministic exact-first one-handler-per-slot selection. It **does not execute effects**; selection-level tests live in `tests/test_abilities.py`. Future implementation should extend this interface rather than add a competing resolver.
- The ability slots **must not be inferred automatically from Scryfall text or role tags**. A reviewed definition/ability catalog is still missing.
- Package-test expected-count contract lives in `run_all_tests.py`. **When adding tests, update the package_tests expected count and final total**, then verify the CI run; do not mistake count mismatch for a rules regression.

## Bounded next Work sessions — execute in order

### Slice A: Finish the pure registry and characteristic contract

Scope: `commander_sim/abilities.py`, `identities.py`, `queries.py` and focused tests; avoid editing the historical v35 table.

1. Fetch and review the **latest main** SHA, read relevant files once, and run targeted tests. Review already present `AbilityCatalog` semantics before reimplementing it.
2. Define a **reviewed ability-directory schema** that maps stable Oracle ID / face / ability slot to typed descriptors and canonical effect-template names, with source revision and capability prerequisites. Prefer a small versioned definition file per **exceptional named card**, plus a shared template catalog; never duplicate common combat/card-characteristic definitions per card. Model per-card declared keywords and multiple independent triggered/activated/static slots.
3. Add safe immutable storage or freezing of registered records, explicit duplicate/alias detection, missing-capability reporting, and a **per-slot coverage manifest**. Implement exact-over-simplified exclusivity and distinct-slot persistence tests before runtime changes.
4. Add minimal synthetic fixtures: two creatures sharing double strike; one independent ETB ability that promotes from simplified to exact; one simplified creature tutor whose exact version changes its search predicate/destination. Each must resolve to at most one handler for each slot. **Do not claim actual game-event behavior** until integrated.
5. Preserve strict replay fingerprints and clear diagnostics. Commit one reviewed, passing milestone.

Acceptance: stable slot identity and provenance, no duplicate declarations, exact-first selection, no API calls, reusable definition registration; pure tests. No actual card casting is required in Slice A.

### Slice B: Universal derived card characteristics and cross-card interactions

Scope: one runtime object-view/query path; no new card/deck inheritance subclasses.

1. Bridge every safely representable verified card body into the **same** authoritative zone object system, not a separate observation engine; preserve actual characteristics and source-incarnation IDs.
2. Make current tutor/removal/other-seat predicate logic use the shared characteristics and tri-state restrictions. Test unfamiliar creature/artifact-creature in library/battlefield/graveyard; type/subtype, mana value and P/T; hexproof/shroud/ward unknown legality; modal face semantics only when verified.
3. Maintain token, copy, control, face/zone change identity with explicit known limits and conservative fail-closed fallback.
4. Ensure existing strict premium/budget semantics remain fixed. Commit after focused suite and CI.

Acceptance: an unfamiliar verified target is found by an **already implemented** tutor and recognized as legal or explicitly UNKNOWN for opposing removal, while its own unusual trigger remains unsupported.

### Slice C: Single-engine hybrid vertical slice

Scope: opt-in `strict|observation|hybrid` on the shared kernel and existing P0.65 catalog.

1. Implement an execution adapter mapping the **selected** `AbilityHandler.operation_id` to an existing typed, supported common effect composition. Handler selection alone is **not execution**.
2. Gate behavior on legal costs, source-specific mana, timing, priority, stack, target restrictions, zone transitions, and known mandatory static/replacement/ETB semantics. If prerequisites are absent, block or label observation, never fabricate.
3. Permit reviewed body-only creatures/permanents; ensure ordinary targeted removal, keyword combat, and relevant generic triggers interact with them. Unknown personal effect is separately reported.
4. Add one executed **simplified tutor** and promote to its **exact tutor** in paired tests. Assert exactly one search/move/shuffle, no duplicated triggers and preserved independent keyword mechanics. Record action provenance, first simplification and dependent metrics.
5. Run a six-turn scripted narrative, then 100 seeds with honest coverage logs; defer win rates and larger sweeps. Commit one tested milestone.

Acceptance: one current engine, one handler per slot, no duplicate events, zero network calls per game, no strict replay regression.

### Slice D: Cross-deck data and mana

1. Cache Scryfall metadata **by Oracle ID** in one immutable versioned offline catalog, **deduplicated across decklists**, with individual deck-hash manifests. Reuse unchanged records offline; an explicit refresh may query only missing/changed names. Never fetch during simulation.
2. Build/check offline snapshots for **Mortarion ideal**, **Mortarion current ordered-plus-owned**, and **Necron Dynasties**; existing Gisa and earlier Mortarion candidate snapshots are **not** substitutes for differently hashed deck files. Report unresolved identities/face layouts.
3. Extend W/U/B/R/G/C mana sources and cost/payment, with source-specific legality and generic-versus-colorless distinction. Use basic Swamps and black nonbasics as first fixtures.
4. Run mixed-deck acceptance (Magnus, Mortarion current/ideal, Gisa, Necrons) only after core prerequisites pass. Make targeting artifact creatures and Zombies, sacrifice, recursion and multi-seat opponents the reusable-mechanism gates.

Acceptance: metadata refresh is explicit, common cards do not need repeated network fetches, and no black-mana game is claimed until actual source-paid turns execute.

## Efficient model allocation (heuristic, not a guaranteed credit price)

- **Fast/economical model, low reasoning**: inspect CI logs, update tests/README, compare fixture counts, small safe documentation edits.
- **Terra low or medium**, if offered: implement Slice A/B narrowly, pure registry, tests, mechanical extraction and simple fixtures. Demand a commit and proof of targeted tests.
- **Sol medium/high**, if offered: review ABI/handler semantics, strict/hybrid precedence, event/priority/zone invariants, performance calibration and architectural boundary crossings. Prefer targeted diff review after 2–4 coherent implementation commits rather than re-reading the full repository after each.
- **Astra low/medium** only when needed: investigate subtle Magic rules bugs, cross-service invariants, unsolved design conflicts or difficult regression failures. Use high reasoning only if lower effort demonstrably fails.
- Avoid **Fast/Ultrafast** unless latency matters more than allowance. Don't assume more reasoning always improves simple coding changes.
- Work/Codex model selection and credits are account-dependent; check **Settings > Usage** for actual remaining five-hour/weekly allowance. Model switches **do not** restore a shared usage pool. The user's Chat conversation can be used for planning without initiating a cloud Work coding task.

## A copyable starting prompt for the next Work session

> Read AGENTS.md, ROADMAP.md P0.6–P0.7, docs/ABILITY_COMPOSITION_ARCHITECTURE.md, and docs/LOW_CREDIT_IMPLEMENTATION_HANDOFF.md. Check the latest main commit and CI. Do not redo the existing deck parser, Scryfall snapshots, CardRegistry, observation runner, or pure commander_sim.abilities catalog. Perform **Slice A only**: add a reviewed per-ability definition schema and per-slot coverage reporting with tests; preserve the exact-first one-handler invariant and unrelated keyword/ability slots. Make one rollback-safe commit. Run targeted tests and the required full regressions; update test-count contract. Report SHA, tests, supported behavior and limitations. Do not begin Slice B or run an indefinite project-wide implementation loop.

## Stop conditions / avoiding wasted credits

- Stop and report if a key authoritative deck file or metadata is missing or ambiguous; do not guess Oracle rules or invent ownership.
- Stop after **one coherent slice and successful tests**; keep unresolved topics in a handoff rather than beginning another unrelated card batch.
- Do not run a giant 1,000+ game campaign before one convincing, source-paid seed narrative; leave performance optimization for measured hotspots.
- Use focused file paths and latest diffs rather than reading every historical engine version.
- On failing CI, inspect **the failing job log and targeted test first**. Distinguish test-count bookkeeping failures from semantic bugs and fix only the relevant issue.
