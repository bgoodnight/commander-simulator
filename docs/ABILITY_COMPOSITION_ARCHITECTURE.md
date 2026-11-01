# Architecture decision: progressive card definitions and ability-level fidelity

**Status:** Adopted architecture; **G1 per-ability composition core implemented (partial integration)**. Last reviewed 2026-10-31. Full per-event live dispatch, generalized trigger lifecycle, and multi-deck support remain pending. Authoritative plan: [ROADMAP.md](../ROADMAP.md); execution gates: [HYBRID_SIMULATION_WORKPLAN.md](HYBRID_SIMULATION_WORKPLAN.md) and [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md).

## Implemented G1 foundation (October 31, 2026)

`commander_sim/ability_composition.py` now supplies immutable reviewed
`AbilitySlot`, `AbilityHandler`, and `ComposedCard` types. Slots have stable
(Oracle ID, face ID, ability ID) keys, pinned printed source text and revision,
typed operation declarations, and required shared capabilities. They are
constructed from **reviewed registrations**, never from guessed card roles
or arbitrary Oracle prose. Each slot can have **at most one exact and one
simplified implementation**. Promotion may replace the earlier bounded
operation's *parameters* within the same reviewed typed effect family
(e.g. impose a maximum tutor mana value) without affecting the other
ability slots; the source revision must remain pinned. The `strict` policy only selects exact;
`hybrid` prefers exact and selects simplified only when explicitly reviewed,
while `observation` never executes an ability. Missing capabilities and
unregistered slots fail closed. Only the selected slot is promoted;
unrelated abilities remain present.

`AbilityDispatcher` invokes a caller-provided, authoritative kernel operation
for the selected ability and records source object ID, slot identity, fidelity,
revision, outcome and omissions **only after the executor returns**.
`TriggerSubscriptions` provides an object-instance/slot/event deduplication
registry with explicit cleanup on zone departure. These are initially
separate contracts, not yet hooked to every event in v35; no separate
mutable game state or global trigger bus was created.

`inspected_search_card` composes the five pinned tutors from
`reviewed_tutors.TUTORS`; historical search handlers now retrieve their
exact-reviewed **search suboperation** through the ability-slot resolver
while retaining the existing timing, stack, triggers and zone movement.
This precise historical search suboperation is **not** a blanket claim
that the entire printed card is exactly simulated. `inspected_rock_card`
composes known mana modes from the reviewed rocks catalog and declares
Mind Stone/Commander's Sphere sacrifice-to-draw as **unsupported separate
slots**, rather than accidentally treating a mana-only model as a fully
implemented card.

This milestone is gated by additional independent tests for slot identity,
promotion/exact-first selection, multiple independent abilities, missing
capabilities, observation-mode refusal, false-event suppression on rejected
actions, trigger deduplication, unsupported rock side abilities and parity
with the historical tutor registries. The v3–v35 and frozen replay suites
must also remain green. Existing descriptive design sketches further below
remain relevant to the remaining G2–G5 integration work.

## First live trigger integration — M2.11 (narrow, regression-gated)

`commander_sim/live_trigger_bridge.py` now binds two **pinned** historical
triggered abilities to the previously implemented per-slot dispatcher:

- **Baral, Chief of Compliance**: the optional draw-one, discard-one
  trigger after a controlled spell/ability counters a spell; its cost
  reduction remains in the historical static-cost engine.
- **Archmage Emeritus**: its Magecraft draw-one effect, with both
  spell-cast and spell-copy trigger hooks mapped to the **same slot**.

The existing v13–v35 `GameKernel.triggers` still determines eligibility,
Harmonic Prodigy trigger multiplicity and controller. The existing priority
stack creates independent frames, handles responses/counters and calls the
same historical effect resolution code. Only the approved trigger **effect
dispatch** is routed through `AbilityDispatcher`; its provenance is recorded
after the host callback succeeds, not when the event is merely queued.
The bridge's `TriggerSubscriptions` registers by object ID + slot + hook
without suppressing distinct trigger events, and keeps a departed source's
registration while its pending triggered frames await resolution. It prunes
registrations after their stack work has resolved. Direct old synthetic
`TriggerResult` tests for unregistered objects retain their previous
behavior but acquire **no false reviewed provenance**.

This is not a replacement for the whole event/priority subsystem or a
generic Oracle-text trigger interpreter. Expansion should first move more
previously-tested abilities into pinned declarations, then replace the
historical card-name registration boundary only when authoritative
object identity, ability-slot lifecycle and legal target/permission layers
are available. The new core never subscribes unknown card roles.
See `tests/test_live_trigger_bridge.py` and v13 real-game tests for
doubling, Archmage copied-spell triggers, source departure and provenance.

## Decision in one sentence

**A card always retains one immutable, verified identity; it acquires reusable rules and explicitly registered behaviors; later exact implementations replace only their matching simplified behavior while preserving unrelated abilities and universal interactions.** No card-specific game-engine subclass. One authoritative game state and action lifecycle.

## What actually exists at the decision date

- `tools/fetch_deck_identities.py` obtains full Scryfall collection records in **offline, hash-checked** card snapshots. No network requests are made by a game turn.
- `commander_sim.identities.CardRegistry` offers immutable face/identity records for supported layouts. Face-specific mana values and keyword sets are **unknown** for certain multi-face cards; printed dynamic P/T remains unsupported. A raw Scryfall keyword or Oracle text is **not** executable behavior.
- `commander_sim.queries.Query` offers conservative YES/NO/UNKNOWN characteristics predicates; `target_legality` only checks a subset of restrictions, and UNKNOWN cannot authorize a cast/target.
- `commander_sim.observation` models opening seven, basic land plays and a mana-value screen, but no color payment, actual spell casts, resolving events, or real opponents.
- `commander_sim.legacy_verified.add_library_creature` can register a verified, ordinary U/R creature in the live library but cannot cast it in strict mode; this is **not** general unknown-card execution.
- Current `run_simulation.py` still uses historical Magnus v35 rules. Mono-black source-paid casting, mixed real decks, generalized keywords and progressive per-ability dispatch are **not** implemented.
- The repository reports 830 tests in 37 suites, and the latest inspected GitHub Actions run (commit `d0de7d9`) passed; CI success does not certify hybrid correctness.

## Information and behavior boundaries

| Layer | Canonical representation | Lifecycle and responsibilities |
|---|---|---|
| A. Identity / faces | `CardIdentity`, `FaceIdentity` keyed by Oracle ID, with snapshot source, layout, printed text and component faces | Immutable offline metadata: names/aliases, mana costs/values, color vs color identity, type/subtype, base P/T (including variable expressions explicitly), keyword declarations, Commander legality; updated only by a deliberate, versioned snapshot refresh |
| B. Runtime characteristics | `DerivedCharacteristics` / `ObjectView` over authoritative objects | Zone/face/context-sensitive types/colors/P/T/abilities/restrictions, owner/controller, tapping, counters, copies, continuous effects; no separate card-name maps or hidden guessed values |
| C. Shared Magic rules | typed rules, keyword and effect templates, legal target/query predicates | Mana/colorless, timing, stack, cost/payment, combat (including double strike), death/events, search/draw/discard, sacrifice, triggered/replacement behavior; **one implementation for all eligible cards** |
| D. Ability declarations | `CardDefinition` holding stable `AbilitySlot` IDs | Reviewed mapping of actual printed abilities to mechanic/template descriptors with parameters, targets, modes, costs, trigger conditions and omissions. Names/roles alone never grant an effect |
| E. Implementations | `AbilityImplementation` per slot: `exact`, `simplified`, or `unsupported` | Chooses exactly one behavior for a **single ability slot** in a given simulation mode. Different abilities and inherited keywords continue operating independently |
| F. Strategy + reporting | `RoleProfile`, pilots, `FidelityEvent`/provenance journal | Roles guide pilot utility only; every approximation identifies ability/behavior, assumption, resulting state changes and downstream metric dependency |

**Printed data versus ability declarations:** The Scryfall snapshot can support direct typed characteristics and reviewed standard keyword **declarations**. Oracle prose is source evidence, **not** a runnable rules program. Tutors, mana abilities and unusual triggers require a reviewed structured declaration or explicit supported parser of a narrow, proven template; unrecognized text remains unsupported. A role tag such as `tutor`, `mana rock`, `aristocrat`, or `pinger` is descriptive and grants no behavior.

## Ability-level composition, precedence and promotion

1. The card is resolved by verified Oracle ID, face and zone; its **runtime instance** is one authoritative object. Layer C supplies common Magic rules wherever declarations and prerequisites justify them (creature targeting, combat, keyword mechanisms). Layers D/E supply its individual abilities; they never replace the base object.
2. Each printed ability gets a **stable, explicit slot identifier** within its Oracle ID/face/revision, e.g. `<oracle_id>/<face>/a2`. Separate mana, keyword, static, triggered and activated abilities are separate slots; automatically derived keyword behaviors are not duplicated as named-card triggers. Track the source ability version and link to the Oracle text fragment for audit.
3. Resolution policy by **slot** and mode:
   - `strict`: validated exact behavior for that slot, otherwise unsupported. Preserves existing strict replay and historical engine behavior.
   - `observation`: printed traits and candidate actions only; no unsupported/simplified effect resolves.
   - `hybrid`: validated exact behavior first; else **reviewed, explicitly registered** simplified behavior; else unsupported. A behavior may be used only when its necessary shared rules/legality primitives are supported.
4. When an exact behavior is added, **supersede the simplified handler for that same slot only**. Do not execute both; do not drop the card's other abilities, keyword implementation or base characteristics. For partial exact rules, split a slot into **explicit disjoint suboperations** with distinct IDs when legitimately independent; never “mix” overlapping handlers that both emit the same trigger/action.
5. Each resolved ability emits one logical event with source object, ability/handler ID, requested/committed action IDs, selected mode/targets, original costs, outcome, fidelity and dependency information. Deduplicate trigger subscriptions by (source instance, ability slot, event hook), with lifecycle cleanup on zone change.
6. Unsupported mandatory restrictions, cost changes, alternative casting permissions, replacement/entering effects or protection can change legality: **fail closed** or flag a non-executable conditional candidate. Body-only hybrid casting is allowed only after explicitly reviewing such risks. Never automatically turn unknown spells into “draw a card”, unknown tutors into unrestricted searches, or unknown permanents into fabricated mana producers.
7. A generalized effect (e.g. tutor) is a **typed composition** of search predicate, target zone, reveal, optional find, shuffle, destination and choice; uniqueness belongs in parameters or a custom suboperation, not a new table subclass. The approximation for a narrower exact tutor cannot be allowed to silently search more targets.
8. No mutation of registered identity or runtime rule classes on a deck swap; use explicit factories and per-game isolated state. Do not call Scryfall mid-game; record deck/snapshot/rules/handler-policy hashes for reproducibility.

### Composition illustration: unfamiliar double-strike creature

- Its Scryfall metadata confirms a normal creature, P/T, printed double strike and mana cost. The creature is a real object and participates in generic creature-based target/tutor queries.
- The **shared combat keyword** implements two combat-damage steps and associated triggers **once** for all creatures with the applicable derived ability. It is not a card-specific handler.
- Its unique ETB trigger may be unsupported or, if reviewed, simplified in hybrid mode, with fidelity noted. Casting its verified body does not remove double strike or other independent abilities.
- When the unique ETB trigger gets an exact handler, it replaces the old ETB approximation only. Double strike, targeting, payment and combat continue unchanged.

### Composition illustration: increasingly precise tutor

A reviewed card declaration contains a `search` ability slot and an initial simplified handler that searches using a **documented bounded predicate** and standard cost/target/permission/destination primitives. This is not automatic from “tutor” in Oracle text. Later, an exact handler adds the card's true conditional restrictions, optional choices and destination rules using the same search primitive. The exact handler occupies the same ability slot and supersedes the simplified one. Regression tests prove only one search/move/shuffle occurs, with the card/zone/card-count invariants preserved.

## Required interfaces (illustrative names; preserve one coherent API)

```python
@dataclass(frozen=True)
class AbilitySlot:
    oracle_id: str
    face_id: str
    slot_id: str
    kind: str                   # keyword/static/triggered/activated/spell/etc.
    declaration: object        # reviewed typed declaration
    prereqs: frozenset[str]     # required runtime capabilities

@dataclass(frozen=True)
class AbilityHandler:
    slot_key: tuple[str, str, str]
    fidelity: str               # exact or simplified
    operation: object           # typed canonical effect/cost/event composition
    limitations: tuple[str, ...]
    source_revision: str

def resolve_handler(slot: AbilitySlot, mode: str, capabilities: frozenset[str]) -> AbilityHandler | None:
    # Exact-first in strict/hybrid; reviewed simplified fallback only in hybrid.
    # Never return two handlers for one slot or a handler lacking required primitives.
    ...
```

These are **design sketches, not already implemented public APIs**. The preferred executable shapes should use typed data and validated schema, not Python string dispatch or new subclass chains.

## Migration and implementation sequence

**G0 — Independent characteristic snapshot (build on P0.6):** review normal and multi-face definitions, variable P/T and keyword declarations, and include text/source fields in immutable records when available. Keep zone-sensitive values separate. Add complete metadata diagnostics instead of hardcoded assumptions. Do not break current snapshot/replay tests.

**G1 — Ability slots and pure resolver (before hybrid gameplay):** build a declarative ability registry and exact/simplified/unsupported resolver, plus tests that are independent of a running game. Implement immutable per-slot coverage. Demonstrate a single ability promoted from simplified to exact while a separate double-strike keyword and another card ability remain intact.

**G2 — Common object/query interaction:** integrate the identity/derived view with the **same** runtime engine. Implement type, subtype, cost, P/T, controller, color/face and token predicates for unfamiliar cards. Real tutor/removal/other-seat targeting must use them; UNKNOWN never means legal. Do not reimplement the game engine in observation mode.

**G3 — Minimal executable hybrid:** with available canonical costs/payment/priority/stack/zone transitions, implement body-only casting and a small collection of *reviewed* shared abilities for multiple cards; record every approximation. Offer `strict|observation|hybrid`, with strict unchanged. Permit only supported primitive families, and explicit body-only omission audits.

**G4 — Template-first expansion:** implement **general rules once**: colored mana (W/U/B/R/G/C), combat and double strike/deathtouch/lifelink, draw/filter, small token creation, damage/life distinction, counters/bounce, source-specific casting, search/reveal/shuffle/destination, triggers, sacrifice, deaths/recursion. Keyed mechanic templates support multiple cards without new table subclasses. Richer effects built using these blocks, not named if/else chains.

**G5 — Calibration:** pair identical starting states/seeds between simplified and subsequently exact handlers; compare per-outcome errors, legal action sets, conservation and event traces. Never report global “X% correct” or deck strength based on omissions. Benchmark after a one-game narrative and 100 deterministic seeds before scaling.

Dependencies are **capability gated**, not a requirement to finish every historical phase first. Never introduce a provisional parallel game-state model merely to claim G3 completed.

## Acceptance tests (must block return to a card-first queue)

1. **Persistence:** printed characteristics and a generic double-strike/haste implementation remain after registering a unique exact ETB ability. Other slots on the card are unaffected.
2. **Exclusive replacement:** a simplified tutor and exact tutor share one slot. In hybrid mode before promotion, only simplification executes; after promotion, only exact executes. Strict mode never executes the simplified version; event count, library/shuffle/zone count are correct.
3. **Generic interaction:** unfamiliar verified 3/3 Zombie participates in power/type-filtered tutor queries, valid target selection, normal attack/block/damage and source-paid sacrifice without implementation of its personal trigger; restrictions that cannot be verified yield UNKNOWN/block.
4. **Across decks:** use at least two distinct imported cards with the same keyword/template (e.g. Necron artifact creature and Mortarion/Gisa creature) plus one Magnus spell. Test B payments, artifact+creature dual typing and graveyard predicates when the prerequisite runtime services exist.
5. **Faces/copies/tokens:** copying, Adventure/multi-face selection, zone changes and token creation recompute/retain characteristics and instance identities correctly; ability hooks register/unregister once.
6. **Safety:** unknown mandatory replacement/ETB/static cost modifications cannot silently execute ordinary-body approximation; no double triggers, double costs, duplicate targets or fabricated abilities.
7. **Determinism:** cold snapshot/registry load makes **zero API calls**; exact seed+deck+rules+mode+handler versions reproduce identical semantic traces. Reference premium/budget strict fingerprints and current regression suites remain intact.
8. **Performance:** paired microbenchmarks identify overhead from registry lookup/dispatch/queries; retain correctness checks and log p50/p95 rather than claiming a speedup without matched measurements.

## Anti-patterns (reject changes that do these)

- New subclasses for individual cards or per-deck rules; runtime monkey-patching of resource/stack services; silent import of decks into shared global state.
- Unreviewed regex rules parsing Oracle prose into executable actions; automatic ability inference from roles; card type alone granting draw/ramp/tutor.
- Reimplementing printed characteristics, combat or keywords inside each named card.
- Whole-card `if exact: disable all generic` replacement or both simple and exact executing the same effect.
- Missing identity/restriction treated as “not present” or UNKNOWN as legal.
- Additional network fetching during game simulation; inaccurate coverage labels or win-rate claims.
