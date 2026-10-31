# Deck Lab U0 — local, read-only interface

**Status:** initial U0 implementation committed October 31, 2026. This is **not a hosted web app** and is not an interactive Magic game. It displays verified deck metadata and reproduces the existing offline observation runner. Deck editing (U1), explicit missing-card Scryfall import (U2), meaningful live turns (M2/M3), and interactive board replay (U4) remain future milestones.

## Start it

Clone the private GitHub repository on a computer with **Python 3.11 or later**, from its root directory run:

```sh
python tools/deck_lab.py
```

Open **http://127.0.0.1:8765/** in that computer's browser. The server defaults to local-only access, not the public internet, and requires **no third-party Python dependencies**. Stop it with Ctrl+C. Use `--port 8899` to change ports if necessary.

The browser has a responsive dark-themed deck selector, commander/inventory labels, 100-card composition, printed card types and mana values, seed/turn controls, and an observation timeline. You can copy the JSON observation to the clipboard. It does **not** let you change a cardlist or contact Scryfall.

## What is currently supported

- **Six authenticated snapshots**: Magnus Premium, Magnus Budget, Wretched Ranks (Ghoulcaller Gisa), Mortarion Current ordered-plus-owned, Mortarion Ideal, and original Necron Dynasties.
- Every deck has its exact file hash pinned to card identity revisions in a shared, immutable offline Oracle-ID catalog (M1).
- A reproducible observation includes opening hand, per-turn draws, first available basic land play, total modeled basic mana sources, and *potential* candidates passing only a mana-value screen.
- The selector distinguishes `owned_precon`, `ordered_plus_owned`, `budget` and `ideal` roles. These labels are not a complete inventory audit or evidence that ordered cards were received.
- Printed metadata is **not** evidence that a card's unique Oracle effects have been implemented. The UI says this explicitly.

## What is not modeled

Spells are **not cast**, no combat is resolved, no abilities/triggers run, color-payment and full cost legality aren't checked, nonbasic land abilities are not modeled, and opposing players are not actually played. Results are not game outcomes or valid win-rate estimates. `candidate_if_supported` is not a legal-action list. The present UI explicitly identifies its mode as **observation**, and `actual_gameplay_available` is false for all six decks.

## Read-only architecture and privacy

- `commander_sim/deck_lab_api.py` adapts existing offline validated metadata and `observe()` into a stable JSON boundary.
- `tools/deck_lab.py` is a **Python standard-library HTTP server**, bound to `127.0.0.1` by default; it only supports read-only GET endpoints.
- `web/deck_lab.html` is a static local page using no CDN, web framework, or external images. It requests only the local API, not Scryfall.
- `GET /api/decks`: all saved deck variants, metadata readiness, and explicit limitations.
- `GET /api/deck?key=mortarion_current`: verified card quantities and printed metadata.
- `GET /api/observation?key=mortarion_current&seed=0&turns=6`: unchanged deterministic observation output (max 20 turns from the UI).
- Input decks and manifests are read-only; no UI action writes to GitHub, mutates canonical decklists, fetches Scryfall, or enables unimplemented rules. The card-copy button only copies the returned JSON locally.

## U0 acceptance

```sh
python -m unittest tests.test_deck_lab -v
python run_all_tests.py
```

The U0 test suite confirms all six pinned decks can be inspected, card quantities sum to 100, observation replay is deterministic, unsupported rules remain visibly omitted, invalid API routes and inputs fail closed, and the UI code makes no metadata API requests.

## Planned incremental next steps

**U1:** Add a **separate editable deck workspace** with copy/Save As, card addition/removal from the local verified catalog, legality and color-identity checks, mana-curve and before/after diffs, undo/revert. Never overwrite canonical presets, ideal or precons.

**U2:** Add a deliberate **Fetch from Scryfall** action for cards absent from the local shared Oracle-ID catalog, using the cache-first importer. No API on typing, navigation or simulation.

**M2/M3:** Replace observation-only results with real source-paid ordinary turns from a shared multi-deck rules engine, then upgrade the **same** UI to show actual events rather than starting a separate interface.

**U3/U4:** More intuitive mana curves, card art if desired, event timelines, and single-deck board/zone replay using canonical game-state data. Detailed two-deck head-to-head remains optional, not a UI prerequisite.
