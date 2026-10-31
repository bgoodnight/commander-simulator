# Commander Deck Lab — GitHub Pages static companion

**Status (October 31, 2026): code, visual frontend, static export and build workflow are committed and tested. GitHub Pages hosting remains DISABLED in the current private repository.** The build workflow produces a downloadable preview artifact even before Pages is activated. Deployment runs automatically on a relevant push once Pages is enabled.

This is a separate **original fantasy tabletop** front end (carved stone, brass, rune light, gentle animations and Web Audio synthesizer). It is **aesthetically adjacent to fantasy card-game interfaces**, not a use of another game's UI art, sound effects or trademark.

## Live site setup — one-time repository setting

1. Open [repository settings: GitHub Pages](https://github.com/bgoodnight/commander-simulator/settings/pages).
2. If GitHub permits Pages for this **private repository**, under **Build and deployment**, select **GitHub Actions** as the source. A private repository needs an eligible GitHub plan (GitHub Pro, Team or Enterprise); GitHub Free generally requires a public repository for Pages.
3. Go to [Actions: Build and (when enabled) publish Deck Lab Pages](https://github.com/bgoodnight/commander-simulator/actions/workflows/deck-lab-pages.yml), choose **Run workflow** on `main`. Later relevant commits also trigger this workflow.
4. Confirm that both **Export sanitized static Deck Lab** and **Deploy static Deck Lab** completed. GitHub will display the actual Pages URL in its deployment summary. The expected ordinary project URL is `https://bgoodnight.github.io/commander-simulator/`, but do **not** assume the URL works before GitHub confirms a deployment.
5. If your GitHub plan does not allow Pages with a private repository, keep the simulator repo private. Consider creating **a separate public, static-only site repository** or upgrading GitHub; don't expose the full Python source just to publish a preview.

**Visibility:** A GitHub Pages site from a private repository can still be **public**. This build intentionally publishes **only six canonical deck variants, card metadata needed by the UI, cached first-six-turn observations, the full Scryfall name index, HTML/CSS/JS and a build manifest**. It does not publish any private workspace builds, local saved decks, raw full Scryfall cache, test suite, source repository contents or GitHub credentials. Decide whether sharing the six decklists publicly is acceptable before enabling Pages.

## Preview before Pages is enabled

The same workflow passes the build and attaches `deck-lab-static-preview` as a downloadable [GitHub Actions artifact](https://github.com/bgoodnight/commander-simulator/actions/workflows/deck-lab-pages.yml) (7-day retention). Download/unzip it, then serve the extracted directory locally:

```sh
python -m http.server 8765 --directory path/to/extracted-preview
```

Open `http://127.0.0.1:8765/` on the same computer. Browser `file://` opening may not load `decks.json` due to web security, so use the local server. Alternatively, use **Work** to build from the checked-out repo:

```sh
python tools/build_pages_deck_lab.py --output ./_pages_dist
python -m http.server 8765 --directory ./_pages_dist
```

Then open `http://127.0.0.1:8765/` in Work's cloud browser to visually inspect desktop/mobile, animation, card artwork, charts and interactions. This does **not** require Pages activation.

## What the static version already supports

- **Commander summoning chamber:** six deck variants displayed as art-backed draggable cards; drag a portrait onto the central rune or tap/click it (keyboard focusable) on touch devices. The chosen deck fades in.
- **Original sounds:** opt-in toggle (OFF by default). Synthesized stone/glyph cues through Web Audio on summon, page change and successful/invalid actions. No borrowed game soundtrack or sound assets; respects user/browser audio policies.
- **Fantasy tabletop styling:** layered stone/basalt backgrounds, warm brass detail, original rune shapes, subdued cyan magical light, accessible controls, responsive layouts and `prefers-reduced-motion` support.
- **Card art:** derives official Scryfall CDN artwork references from cached printing IDs for all cards when available; otherwise shows a themed fallback. Images are loaded remotely by the browser and are not re-hosted from our repo. Commander art is prominent; all available card art can be viewed in card details. Copyright remains with respective owners; Scryfall is credited.
- **Deck composition:** six 100-card lists and associated commanders, color restrictions and pinned original card metadata. Search cards by name/type/Oracle text, inspect types, mana values, Oracle text and Scryfall links.
- **D3-adjacent visualization:** original native-SVG bar charts for card categories and printed mana curve (no D3 dependency).
- **Cached results:** exactly the previously generated **11 seeds per deck** (`0,1,2,3,4,5,7,11,21,42,99`, **66** fixed-seed observations in all). View up to six turns, opening hand, basic land model, draws, mana-value candidates and limitations; export the underlying JSON. No browser simulation or extrapolated win rates.
- **Static Deck Workshop:** one-for-one card swaps, real card color identity and Commander singleton/100-card checks using exported cached details. Undo/revert; Save As a named **localStorage** browser version and reload/delete versions; export a version as a plain-text `.txt` list compatible with the Python deck importer. Canonical deck files stay untouched. Browser storage is **local to that device/browser**, not GitHub or a cross-device account.
- **35,533-name typeahead:** all Scryfall names filtered **offline**, no request per keystroke. Existing cached full identity can be used immediately. If a name is only in the names index, a deliberate **Fetch card details** action can request its full Scryfall JSON over HTTPS (subject to network/CORS) and store the returned record in browser storage. It remains metadata, not executable rules. Strict names and color checks apply before editing.

## Honest boundaries / safety

- **No new Magic simulation** in a hosted browser. All 66 observations are generated by the repository's Python `observe()` during the GitHub Actions build. That observation only tracks a deterministic starting hand, basic-land/Command Tower modeled sources and total-mana-value candidates—not legal casting, colored costs, combat, spells, ETB triggers or win rates.
- **Edited decks do NOT have cached simulation results.** Only the unchanged six canonical hashes have observation records. The Workshop does not attach an original deck's observations to a changed list. Export modified decks and run `tools/theorycraft.py` locally for new observations.
- **No Python backend, live game engine, shared local workspace, GitHub writes or server persistence.** Only user-initiated Scryfall detail fetches leave the static app, plus remote Scryfall artwork and optional Google Fonts.
- **No automatic API calls from autocomplete.** The 35,533-name catalog is generated/validated separately in the GitHub repository. Explicit Scryfall lookup calls can fail due to network, cross-origin restrictions or rate limiting, in which case the UI reports that failure without modifying the deck.
- **No claim of full Commander legality** for exceptional deck-construction rules or fully executable card abilities. The static editor enforces ordinary Commander 100-card, singleton, documented card legality, identity and immutable commander, but must not replace the authoritative Python simulator's deep validation.

## Build mechanics

`tools/build_pages_deck_lab.py` uses the existing `DeckFixture`, `deck_detail()`, pinned manifests and `observe()` in Python 3.11, producing a separate allowlisted `dist/pages` artifact with:

- `index.html`, `style.css`, `app.js`, `.nojekyll`
- `decks.json`: six canonical verified decks with only UI-relevant printed card metadata/printing image URLs
- `observations.json`: fixed seed → deck observation data with hashes and explicit limitations
- `names.json`: complete verified names-only index
- `build-manifest.json`: counts and SHA-256s of every included asset

The artifact **does not contain** the full repository. Build integrity is covered by `tests/test_pages_export.py`, the existing full 37-suite regression harness and `node --check`. Workflow `.github/workflows/deck-lab-pages.yml` always builds/tests and uploads a preview artifact; it publishes only when Pages is enabled. This preserves the Python backend/Work path alongside the static Pages companion.

## Next iteration

Use Work's browser to check the actual rendered mobile and desktop layouts, art cropping, drag/drop vs tap, sound-on/off, reduced-motion, SVG legibility, card modal, seed switch, invalid and valid swap and `localStorage` persistence. Then prioritize visual fixes and card art caching (respecting artist/copyright/provider terms), version-compare visualizations and explicitly requested improvements; real generic Magic gameplay remains a separate engine milestone.
