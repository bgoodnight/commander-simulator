# User interface roadmap — deck testing before exhaustive card implementation

**Status: U0 local read-only Deck Lab implemented** (October 31, 2026), with all six pinned decks, printed card details, reproducible observation-only turns, and offline autocomplete against **35,533 Scryfall card names**. [Launch guide](DECK_LAB_U0.md). The **U2 backend preflight already supports automatic first-run import of exact missing card identities** via [card discovery](CARD_DISCOVERY_AND_THEORYCRAFT.md), but **U1 editing and the U2 browser integration remain unimplemented**; U3/U4 remain planned. Product order: [Multi-deck MVP](MULTI_DECK_MVP.md) and [ROADMAP.md](../ROADMAP.md). This is an **independent UI milestone track** that starts from verified metadata and grows alongside real-game interoperability. The UI must not become an additional rules engine or a prerequisite to the M0 shared Scryfall catalog.

## Product goal

Make it practical to **select a real deck, understand what the simulator supports, run or inspect meaningful first-turn experiments, revise a deck, import unfamiliar cards explicitly, and compare changes** without requiring terminal commands. Prioritize **deck usability and truthful simulation** over visual polish or exact implementation of every named card.

**User-priority sequence:** (1) deck viewer after M1; (2) **deck modifications**; (3) **explicit local-first card imports**; (4) **meaningful simulation visualization and comparisons**; (5) **single-deck** event-backed battlefield/zone replay. Actual source-paid runs become available in this same UI after M3. **Two detailed decks playing one another is not a UI dependency and remains optional.**

## Interface milestones and timing

| UI milestone | Dependency and priority | Deliverable and acceptance |
|---|---|---|
| **U0 — DONE: initial read-only Deck Lab** | `tools/deck_lab.py` local-only stdlib server, `web/deck_lab.html` static view and `commander_sim/deck_lab_api.py` read-only endpoints, all after M1 | All six decks selectable; commander, quantity/type/mana-value, provenance labels, reproducible observation timelines, seed/horizon and copyable JSON. No real spells/combat, deck editing or Scryfall calls. Enrich same UI with real M3 events when available |
| **U1 — Versioned deck workspace / modifications** | **First interactive feature after U0**, before broad individual card batches; M1 imported identity catalog required | Search/select cards already in offline catalog; add/remove quantities; validate Commander/identity/count/color constraints; display live diff, curve and changed capabilities; **Save As** new deck variant with immutable provenance and distinct deck SHA/manifest; never silently edit original Magnus/Mortarion/precon fixtures. Keep “ideal” vs “ordered/owned” tags independent of rules legality |
| **U2 — Backend import preflight DONE; browser editing pending** | `prepare_theorycraft_deck()` already fetches exact missing identities automatically on first deck preparation (unless offline), preserves per-deck pinned snapshots, and refuses invalid names. `card_name_catalog.py` caches the full Scryfall names list in one explicit refresh | **UI wiring still needed:** U1 draft edits and Save As must use the existing preflight and local suggestions (including names lacking full cached metadata); show preview and legality/identity errors. Never fetch on each keystroke, page load, or during simulation. Full names-only suggestions do not grant rules or establish ownership |
| **U3 — Clearer simulation visuals, deck comparison** | After U0–U2; use M1 metadata/observations and M3 actual traces as supported. **No M4 dependency** | Mana curve and card-type summary; first six turn timeline; hand/mana/land/action summaries, side-by-side before/after deck comparison and seed-paired differences; supported/simplified/unsupported *per ability* and uncertainty highlights; optional card art from separately cached images or provider links, with source attribution/usage compliance. Never invent a board state or win rate from observation-only data |
| **U4 — Single-deck board and replay** | After M3 exposes authoritative per-turn objects/zones/events for one detailed deck; **no M4 dependency** | Battlefield/stack/graveyard/command zone views and object inspector plus deterministic timeline replay for one deck with clearly abstract opposing seats. Consume existing engine state without another mutable rules/priority implementation. A later optional two-deck extension can reuse these views |
| **U5 — Optimization workflow** | After reliable paired runs / calibration and sufficient M5 rules fidelity | Propose card substitutions, compare curve, mulligan/turn-access distributions and *supported* decision metrics. Show effect coverage/uncertainty, never label approximate win rates as real validated strength |

**Priority rule:** **U0 is implemented; next build U1 deck editing**, followed by U2 explicit card import in bounded slices, while M2/M3 actual single-deck gameplay advances separately. Do not redo U0 or add unrequested card effects merely to enable versioned deck editing. After these, deliver **U3 useful analysis visuals and U4 single-deck replay** from actual engine output. Do **not** begin M4 head-to-head by default or make it a dependency of U0–U4. Broad individual card mapping follows the usable Deck Lab, except focused mechanics necessary to support it; label observation versus real events clearly.

## First screen: intentionally simple

A single local, browser-accessible **Deck Lab** (no complex card tabletop required):

- **Deck selector:** `Magnus Premium`, `Magnus Budget`, `Mortarion Current`, `Mortarion Ideal`, `Wretched Ranks`, `Necron Dynasties`, `Flameslinger`; show provenance, commander, legality and snapshot presence separately from effect coverage. The user's “actual cards/ordered” label is an **inventory assertion**, not inferred from a deck file or Scryfall.
- **Run controls:** seed, first-six-turn horizon, choose `strict` / `observation` / `hybrid` *only if that mode genuinely exists*. Disabled with a precise explanation if unsupported; no inert controls. One `Run` action uses an existing, testable engine/run API.
- **Results:** a clean timeline of cards drawn, lands/sources, **actual** casts and actions if supported, target legality, commander availability, hand/board/zone counts; show first unsupported restriction/ability and any approximations that affected choices. Quick export/replay.
- **Deck editor (U1):** show 100-card categories and diff, search the local card library, +/- quantities, explicit legality messages, Save As version, restore/copy/compare. A “try this substitution” preview does not overwrite canonical fixture data.
- **Add card (U2):** local search first, then a separate clearly labeled `Fetch from Scryfall` action with preview/confirmation. Handle typos, split/transform/Adventure faces, color identity, duplicates and unsupported rules transparently; saving a changed deck causes a fresh pinned deck manifest.

## UI / engine boundary and recommended implementation style

- Prefer a **minimal local browser UI** over a large graphics-heavy custom tabletop. Use a thin presentation adapter over a stable Python interface; choose the smallest maintainable web framework after testing how the engine exposes run/results. No premature React rewrite, authentication service or remote deployment. A CLI remains supported.
- Introduce a small `DeckCatalogService` / `DeckRevisionService`, `CardLookupService` (local-first, explicit fetch), and `RunService` with stable typed JSON payloads; these call the existing validated deck parser, offline card catalog, ability registry and **same** authoritative engine. The UI owns neither legality nor runtime state.
- Put **editable user decks in a separate workspace** from immutable canonical / historical fixtures. All edits are reversible, versioned, hash-checked and side-effect-free until Save. Never silently commit a user deck to GitHub or equate a card's inclusion with possession.
- A UI lookup is not permission for the simulator to contact Scryfall: network fetch may happen **only after a user-initiated import/refresh** and not in RunService, draw, game action, replay or page navigation. Source/rate-limit/error details remain visible.
- UI card art is optional, not a dependency of M3; remote image display follows an explicit image-fetch policy and never triggers card **metadata** API retrieval during a run. Keep cache and image links separated.
- Accessibility/efficiency: readable high-contrast light/dark layouts, keyboard-operable controls, compact default information, mobile-friendly responsive panels, clear badges/labels for limitations, and fast loading; no animated visuals required to demonstrate rules correctness.

## Verification and stop conditions

1. **U0:** deterministic seed in CLI and UI yields identical result fingerprints, card counts and fidelity report; unsupported mode controls are disabled. Opening a screen/network-off run makes **zero API requests**.
2. **U1:** a copied 100-card deck can be edited, validated, saved as a **new version**, reloaded and diffed; illegal singleton/commander color identity rejected; canonical precon and ideal/current fixtures unchanged; undo/revert works.
3. **U2:** cached card selection = zero Scryfall requests; an uncached lookup is **user-initiated**, bounded, stored once and reusable by a second deck; ambiguous faces require explicit choice; failed API call leaves the deck unchanged.
4. **U3:** visuals only display verified deck metadata, observations, or actual engine events with explicit labels; same-deck seed comparisons and before/after deck variants must reflect matching modes/coverage and must not invent win chances. No head-to-head implementation is needed.
5. **U4:** single-deck object inspector and replay never mutate game state; any action submission goes through the existing legal-action/priority APIs. Source/target/trigger event IDs match the engine trace; abstract opponents are visibly distinguished from detailed decks. No detailed second deck required.

## Examples worth prioritizing

- Compare **Mortarion Current** vs **Mortarion Ideal** via card diff and **first-six-turn mana development**, without pretending missing cards are owned or exact high-end abilities are implemented.
- Compare **Magnus Premium/Budget** by fixed seed, mana curve and tutoring *availability*, with missing card behavior flagged.
- Edit a **Wretched Ranks** deck copy by adding a card already in Mortarion's shared catalog, validate mono-black identity, and save a new fixture with no API call.
- Add an unfamiliar Zombie via the U2 import control, reuse its verified creature type/P/T from the catalog, and label its uncommon text unsupported until a reviewed ability is registered.
