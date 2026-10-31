# Coding-agent instructions — Commander simulator

Applies to implementation on this repository's active branch. Read, in this order:
1. [ROADMAP.md](ROADMAP.md) and [docs/MULTI_DECK_MVP.md](docs/MULTI_DECK_MVP.md) — **active product order M0–M6**, multi-deck acceptance.
2. [docs/LOW_CREDIT_IMPLEMENTATION_HANDOFF.md](docs/LOW_CREDIT_IMPLEMENTATION_HANDOFF.md) — bounded next Work session, starting with M0 cache.
3. [docs/USER_INTERFACE_ROADMAP.md](docs/USER_INTERFACE_ROADMAP.md) — **U0–U4 UI milestones after usable MVP, before exhaustive named-card work**.
4. [docs/ABILITY_COMPOSITION_ARCHITECTURE.md](docs/ABILITY_COMPOSITION_ARCHITECTURE.md) — binding progressive card architecture.
5. [docs/DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md) and [docs/HYBRID_SIMULATION_WORKPLAN.md](docs/HYBRID_SIMULATION_WORKPLAN.md) — correctness and fidelity contracts.

## Non-negotiable architecture

- **One verified identity** (Oracle ID, face, type/subtype, mana cost/value, color/identity, P/T, keywords, source provenance) for each card; one derived/runtime object view for its context; one authoritative mutable game state. Unfamiliar cards with unsupported personal effects must still be available to correct generic targeting, tutor, combat and zone queries.
- **Shared Magic rules first.** Cast/cost/payment/priority, legal targets, events, double strike and other implemented keywords, damage, sacrifice, search, token/zone movement and standard abilities belong to common services. Add new named-card definitions by composing these primitives, not table subclasses or central card-name switches. Don't run Oracle rules text as code.
- **Reviewed per-ability registration.** Every specific ability has a stable Oracle ID + face + ability slot; tag prerequisites and `exact/simplified/unsupported` coverage. For a slot select at most one handler: strict = exact only; hybrid = exact if implemented, otherwise *explicitly registered reviewed simplified* if safe; observation = no effect resolutions. Exact replaces only the same slot's approximation, **never** the entire card or its other abilities. No double ETB, tutor searches, casting triggers, payments or moves.
- **Keyword persistence.** A card's supported generic flying/double strike/lifelink/etc. must remain when a card-specific ETB/activated ability is implemented, simplified, promoted or removed. Multi-ability cards may have mixed fidelity with independently logged omissions.
- **Safe uncertainty.** Metadata is not executable ability text. `role=creature/tutor/mana rock` grants no action. Unknown target/ward/protection, mandatory static/replacement effects, mana colors or special cost restrictions must block, be marked UNKNOWN or be handled by an explicitly reviewed approximation; never silently invent legality. A simplified tutor must have documented predicate, zone, destination and payment; never imply it implements the exact tutor text.
- **Offline API only.** `tools/fetch_deck_identities.py` uses Scryfall on explicit import/refresh, writing a versioned, hash-checked local snapshot. No network/API calls while loading a saved snapshot, advancing a turn, casting a card, running tests, or running a simulation batch.
- **Strict and history preserved.** No semantic changes to legacy strict engine except separately diagnosed correctness fixes with updated fixtures. Do not add another card-specific subclass, monkey-patch existing shared services, weaken legality/state checks, or add caching before replay/invalidation gates.

## Active product-first implementation queue

**Target:** usable multi-deck early-game experiments and a practical Deck Lab **before** mapping every individual card. Historical P0–P7 phase numbers document prerequisites; follow the active **M0–M6 and U0–U4** delivery order instead.

1. **M0 FIRST — shared offline Scryfall catalog:** check a deduplicated immutable Oracle-ID/alias store **before** requesting missing card names on explicit import/refresh, write version-pinned per-deck SHA manifests, and prove zero API calls on repeated/overlapping cache-hit imports or game runs. Do not implement mutable game-state memoization.
2. **M1 — validated multi-deck import/observation:** load Magnus premium/budget, Wretched Ranks, Mortarion Current/Ideal and Necrons with exact manifests; support general commander identity without deck-specific table subclasses. Reproducible six-turn observation may omit unsupported actions but may not claim they resolved.
3. **M2 — minimum shared gameplay:** source-paid W/U/B/R/G/C mana incl. Swamp/B and true colorless, canonical safe ordinary creature/permanent casting, universal object typing, basic combat and cross-card legal target/query predicates in the same authoritative v35-derived kernel. Unknown legality must fail closed.
4. **M3 — usable early-turn MVP:** one shared generic runner executes real legal actions with Magnus and one mono-black deck for six turns, with per-action fidelity/omission and replay. The **pure, non-executing** `commander_sim.abilities.AbilityCatalog` is already present; extend it for a **small reviewed** hybrid template set without replacing the selector or requiring a broad named-card directory. P0.65's full promotion/integration gates are still required before calling hybrid complete.
5. **U0 → U1 → U2 — user-facing functionality before broad card mapping:** simple local Deck Lab viewer with deck/seed/turn results (optionally read-only *observation* preview after M1); then versioned **deck editing and Save As**; then explicit **local-first Fetch from Scryfall** for missing cards. The UI is thin presentation over existing deck/import/engine APIs, not an independent state or rules engine. Never edit canonical fixture files or auto-fetch while navigating, typing or simulating. Follow [USER_INTERFACE_ROADMAP.md](docs/USER_INTERFACE_ROADMAP.md).
6. **M4 — two different detailed deck seats**, alongside U1/U2 where feasible. **U3/U4 — visuals and richer replay** once source-paid real events exist. Only then **M5 — broad unique-card effects** and M6 performance/calibration; fix individual cards earlier only when they block an MVP core mechanic.

**Do not let individual-card completeness block M1/M2/M3/U0/U1/U2.** Imported = identity recognized; castable = permitted by validated current rules; fully supported = independent per-ability coverage. Keep these different in all reports.

## Usage-efficient working procedure

- Start with [LOW_CREDIT_IMPLEMENTATION_HANDOFF.md](docs/LOW_CREDIT_IMPLEMENTATION_HANDOFF.md) and the latest commit/CI. Scope a single current **Slice 0/1/2/3 or UI U0/U1/U2**; do not re-audit the entire historical engine, redo already committed foundations, or prioritize the former Slice A card directory over M0 caching.
- Run **targeted** tests during edits, then the complete 37-suite `python run_all_tests.py` once at a coherent commit. When adding package tests, update both `('package_tests', N)` and the final reported total in `run_all_tests.py` without removing the count gate. Inspect failing CI job logs rather than blindly retrying full tasks.
- Prefer a smaller coding model on low/medium reasoning for self-contained mechanical changes, and reserve more expensive reasoning for cross-engine priority/event correctness, architectural review and difficult failures. No unbounded "continue until complete" instructions.
- Fetch card metadata only on explicit **import/refresh** after consulting the shared immutable Oracle-ID cache; never re-fetch cached identities because another deck uses them. UI U2 may expose an explicit user-initiated fetch control; browser navigation, typing, deck selection and simulation are **not** import requests.
- Keep UI services thin: one canonical deck validator, shared card catalog and simulation/run API; editable revisions separate from canonical historical fixtures; results display whether they are observation versus real legal actions and which abilities are simplified/unsupported.

## Milestone completion checklist

- Document exactly what is implemented, partial, simplified or unsupported by **ability slot**, with provenance and any assumptions.
- Pure tests: exact-only strict, hybrid fallback, promoted exact superseding only its own simplified ability, independent keyword and other ability persistence, no duplicate trigger/zone/search/action events.
- Integration tests: source-paid current-game action, unfamiliar object targeted or found by an implemented card/opponent, UNKNOWN restrictions fail closed, proper object/zone conservation and deterministic replay.
- Run the relevant tests and `python run_all_tests.py` when a runnable checkout is available, and confirm GitHub Actions result before claiming CI passed. Use the existing reference fingerprints for premium/budget strict mode; explain intentional bug fixes separately.
- Commit each coherent, passing milestone with an example six-turn trace, coverage report, performance measurements where affected, limitations and updated roadmap status. Never mark a phase complete based on documentation alone.

**Review gate:** A simplified tutor upgraded to its exact effect must show exactly one search/destination/shuffle and leave its card's printed characteristics, standard double strike (if present), and unrelated abilities unchanged. New imported cards should obtain recognized generic behavior through shared definitions, not per-card engine edits.
