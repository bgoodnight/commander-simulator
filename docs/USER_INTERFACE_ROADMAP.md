# User interface roadmap — deck testing before exhaustive card implementation

**Status: planned, not implemented.** Product order: [Multi-deck MVP](MULTI_DECK_MVP.md) and [ROADMAP.md](../ROADMAP.md). This is an **independent UI milestone track** that starts when a useful core read-model exists, then grows alongside real-game interoperability. The UI must not become an additional rules engine or a prerequisite to the M0 shared Scryfall catalog.

## Product goal

Make it practical to **select a real deck, understand what the simulator supports, run or inspect meaningful first-turn experiments, revise a deck, import unfamiliar cards explicitly, and compare changes** without requiring terminal commands. Prioritize **deck usability and truthful simulation** over visual polish or exact implementation of every named card.

**User-priority sequence:** (1) deck viewer after M1; (2) **deck modifications**; (3) **explicit local-first card imports**; (4) **meaningful simulation visualization and comparisons**; (5) **single-deck** event-backed battlefield/zone replay. Actual source-paid runs become available in this same UI after M3. **Two detailed decks playing one another is not a UI dependency and remains optional.**

## Interface milestones and timing

| UI milestone | Dependency and priority | Deliverable and acceptance |
|---|---|---|
| **U0 — Thin read-only deck & run viewer** | **Implement immediately after M1**, displaying imported deck data and labeled observations; enrich with real run events once M3 ships | Local browser page or similarly simple UI listing saved deck variants, commander, 100-card legality, cache status, capability gaps; select seed/turn horizon/mode; display real vs **observation** traces distinctly. No new rules or fictional action resolutions; deterministic export as JSON/text |
| **U1 — Versioned deck workspace / modifications** | **First interactive feature after U0**, before broad individual card batches; M1 imported identity catalog required | Search/select cards already in offline catalog; add/remove quantities; validate Commander/identity/count/color constraints; display live diff, curve and changed capabilities; **Save As** new deck variant with immutable provenance and distinct deck SHA/manifest; never silently edit original Magnus/Mortarion/precon fixtures. Keep “ideal” vs “ordered/owned” tags independent of rules legality |
| **U2 — Explicit new-card lookup and Scryfall import** | After **M0 cache** and U1 editing; prioritize above decoration | User enters card name; **search local catalog first**; if absent, clear explicit “Fetch from Scryfall” action uses existing import/refresh service, with ambiguity/face/legality review, validation, cache persist and manifest update **on save**. Preview errors and API/cache status. **No network on page load, simulation, deck selection, run/replay or automatic typing/autocomplete unless explicitly approved as an import action** |
| **U3 — Clearer simulation visuals, deck comparison** | After U0–U2; use M1 metadata/observations and M3 actual traces as supported. **No M4 dependency** | Mana curve and card-type summary; first six turn timeline; hand/mana/land/action summaries, side-by-side before/after deck comparison and seed-paired differences; supported/simplified/unsupported *per ability* and uncertainty highlights; optional card art from separately cached images or provider links, with source attribution/usage compliance. Never invent a board state or win rate from observation-only data |
| **U4 — Single-deck board and replay** | After M3 exposes authoritative per-turn objects/zones/events for one detailed deck; **no M4 dependency** | Battlefield/stack/graveyard/command zone views and object inspector plus deterministic timeline replay for one deck with clearly abstract opposing seats. Consume existing engine state without another mutable rules/priority implementation. A later optional two-deck extension can reuse these views |
| **U5 — Optimization workflow** | After reliable paired runs / calibration and sufficient M5 rules fidelity | Propose card substitutions, compare curve, mulligan/turn-access distributions and *supported* decision metrics. Show effect coverage/uncertainty, never label approximate win rates as real validated strength |

**Priority rule:** after M1, build U0 read-only and add U1 deck editing and U2 explicit card import in bounded slices, while M2/M3 actual single-deck gameplay advances. After these, deliver **U3 useful analysis visuals and U4 single-deck replay** from actual engine output. Do **not** begin M4 head-to-head by default or make it a dependency of U0–U4. Broad individual card mapping follows the usable Deck Lab, except focused mechanics necessary to support it; label observation versus real events clearly.

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
