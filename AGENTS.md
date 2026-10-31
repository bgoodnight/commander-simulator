# Coding-agent instructions — Commander simulator

Applies to implementation on this repository's active branch. Read, in this order:
1. [ROADMAP.md](ROADMAP.md) — current priorities and phase exit gates.
2. [docs/ABILITY_COMPOSITION_ARCHITECTURE.md](docs/ABILITY_COMPOSITION_ARCHITECTURE.md) — **binding progressive card architecture**.
3. [docs/DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md) — correctness and workflow contract.
4. [docs/HYBRID_SIMULATION_WORKPLAN.md](docs/HYBRID_SIMULATION_WORKPLAN.md) — vertical slices and acceptance fixtures.

## Non-negotiable architecture

- **One verified identity** (Oracle ID, face, type/subtype, mana cost/value, color/identity, P/T, keywords, source provenance) for each card; one derived/runtime object view for its context; one authoritative mutable game state. Unfamiliar cards with unsupported personal effects must still be available to correct generic targeting, tutor, combat and zone queries.
- **Shared Magic rules first.** Cast/cost/payment/priority, legal targets, events, double strike and other implemented keywords, damage, sacrifice, search, token/zone movement and standard abilities belong to common services. Add new named-card definitions by composing these primitives, not table subclasses or central card-name switches. Don't run Oracle rules text as code.
- **Reviewed per-ability registration.** Every specific ability has a stable Oracle ID + face + ability slot; tag prerequisites and `exact/simplified/unsupported` coverage. For a slot select at most one handler: strict = exact only; hybrid = exact if implemented, otherwise *explicitly registered reviewed simplified* if safe; observation = no effect resolutions. Exact replaces only the same slot's approximation, **never** the entire card or its other abilities. No double ETB, tutor searches, casting triggers, payments or moves.
- **Keyword persistence.** A card's supported generic flying/double strike/lifelink/etc. must remain when a card-specific ETB/activated ability is implemented, simplified, promoted or removed. Multi-ability cards may have mixed fidelity with independently logged omissions.
- **Safe uncertainty.** Metadata is not executable ability text. `role=creature/tutor/mana rock` grants no action. Unknown target/ward/protection, mandatory static/replacement effects, mana colors or special cost restrictions must block, be marked UNKNOWN or be handled by an explicitly reviewed approximation; never silently invent legality. A simplified tutor must have documented predicate, zone, destination and payment; never imply it implements the exact tutor text.
- **Offline API only.** `tools/fetch_deck_identities.py` uses Scryfall on explicit import/refresh, writing a versioned, hash-checked local snapshot. No network/API calls while loading a saved snapshot, advancing a turn, casting a card, running tests, or running a simulation batch.
- **Strict and history preserved.** No semantic changes to legacy strict engine except separately diagnosed correctness fixes with updated fixtures. Do not add another card-specific subclass, monkey-patch existing shared services, weaken legality/state checks, or add caching before replay/invalidation gates.

## Current development order

1. Finish P0.6: stable unified per-face characteristics and universal target/query integration from existing `commander_sim.identities`, `queries`, `snapshots` and narrow live-library bridge. The observation runner is a projection, not a valid gameplay implementation.
2. **P0.65 mandatory**: build pure per-slot ability declaration/dispatch registry, strict/hybrid/observation selection, provenance/fidelity and *promotion/no-duplication tests*. Do this **before** large named-card batches or claims of playable hybrid.
3. P0.7: wire opt-in hybrid into the **same** legal-action, cost, payment, stack, zone and event engine; implement verified-body-only casting for safe ordinary permanents and several reviewed shared templates, each demonstrated on at least two different cards.
4. Expand canonical W/U/B/R/G/C mana and event/keyword/effect primitives; compare Flameslinger, Mortarion current and ideal, Wretched Ranks, Necron Dynasties with an authentic offline snapshot for **each deck file**. Ensure the current/ideal Mortarion and Necron decks get their own snapshots; earlier receipt-only Mortarion snapshot does not validate them.
5. Then resume targeted named-card implementations as **reviews of reusable mechanics** rather than proliferating one-off handlers.

## Milestone completion checklist

- Document exactly what is implemented, partial, simplified or unsupported by **ability slot**, with provenance and any assumptions.
- Pure tests: exact-only strict, hybrid fallback, promoted exact superseding only its own simplified ability, independent keyword and other ability persistence, no duplicate trigger/zone/search/action events.
- Integration tests: source-paid current-game action, unfamiliar object targeted or found by an implemented card/opponent, UNKNOWN restrictions fail closed, proper object/zone conservation and deterministic replay.
- Run the relevant tests and `python run_all_tests.py` when a runnable checkout is available, and confirm GitHub Actions result before claiming CI passed. Use the existing reference fingerprints for premium/budget strict mode; explain intentional bug fixes separately.
- Commit each coherent, passing milestone with an example six-turn trace, coverage report, performance measurements where affected, limitations and updated roadmap status. Never mark a phase complete based on documentation alone.

**Review gate:** A simplified tutor upgraded to its exact effect must show exactly one search/destination/shuffle and leave its card's printed characteristics, standard double strike (if present), and unrelated abilities unchanged. New imported cards should obtain recognized generic behavior through shared definitions, not per-card engine edits.
