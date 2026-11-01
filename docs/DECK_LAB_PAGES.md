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

## Interpretive Results: evidence-first scrollytelling

The Results landing page now starts with an **automatically generated interpretation of all cached seeds for the chosen canonical deck**, rather than a single seed's raw trace. This is computed in client-side `web/pages/results_insights.js` using the exact Python observations exported in `observations.json`. No commander-specific narrative or arbitrary performance score is hard-coded.

- The first screen shows three observed summaries with counts and percentages: **2–5 modeled lands in the initial seven**, **at least three modeled sources by turn three**, and **any mana-value-only candidate on turn four**. The archive size, exact numerator and denominator, and limitations are displayed.
- Scroll through three findings describing **opening modeled-land distribution**, **turn-three modeled-source distribution**, and **candidate-screen availability by turn**. Each finding has a numerical summary generated from the selected deck's archive, a conditional interpretation and a prominent "what this does not show" note.
- Bar charts are **clickable, touch-friendly and keyboard-focusable**. Selecting a bar shows its exact observed numerator, relevant seed identifiers and a button to inspect a matching archived run. The original individual-seed trace remains available in an expandable section at the bottom rather than occupying the main results screen.
- Chart bars animate using D3 on scroll entry and reset when leaving the viewport. Native SVG still renders if D3 does not load; `prefers-reduced-motion` disables transitions. Unlike decorative motion, every bar is tied to real saved observations.
- **Sample limitations:** only eleven preselected seeds per canonical deck. These are not independent Monte Carlo outcome samples, do not include colored-cost spell casting or unmodeled nonbasic lands, and cannot estimate game win rates or actual card castability. The opening "land" measure specifically counts modeled basics and Command Tower, not all printed lands. Narratives use measured values and avoid declaring a deck strong or weak.
- Saved/edited browser versions have **no matched cached observations**. The page shows that absence instead of applying a baseline deck's aggregate results to modified cards. To evaluate a new saved deck, export it, run it through Python and publish its pinned results in a future export.

Node test cases in `tests/pages_insights.test.cjs` verify aggregate denominators, seed-level drilldown correctness, variable data and dynamically changing interpretations. Python release tests verify the extra JS file and interactive evidence controls are included in the allowlisted Pages output. The Pages workflow runs both JavaScript behavior tests and the Python artifact regression tests.

**Future real-game analytics:** as M2/M3 adds verified game events, this report can add actual cast timings, mana-color failures, interaction windows and engine milestones; after sufficiently broad randomized completed games, real outcome/seat/variance statistics may become meaningful. Do **not** interpret these observation-only dashboards as gameplay statistics before then.

## Three-page navigation and results-first landing

The static build now has **three real HTML entrypoints** (shared source/assets), each supporting an optional `?deck=magnus_premium` query parameter:

- **Simulation Results** — `results.html`, linked from the top navigation. Select a cached seed, inspect six-turn observations, then scroll through **three D3-animated visualizations** of modeled sources, observed hand size and mana-value candidate counts. The charts derive exclusively from the fixed-seed Python observations and are clearly labeled as **not real played spells**. D3 is progressive enhancement: local SVG bars remain visible without the CDN, and reduced-motion settings disable the animation.
- **Deck Summary** — `index.html` (also available at `summary.html`), the **default home page**. Commander portrait/art, card composition, printed mana curve, pinned metadata and limitations.
- **Card List & Editor** — `editor.html`. Search the verified cardlist, open card art/details, use offline full-name autocomplete, try a one-for-one swap, undo/revert, save browser-local versions and download a decklist. A user-triggered fetch can retrieve missing printed card details from Scryfall.

The top brass-and-stone navigation is shared by all pages; the selected commander **and its selected saved deck version** travel between pages via the query string. A **compact circular commander medallion** is positioned above the results and deck content. Click or tap it to open a four-commander chooser (rather than taking up the initial screen with six large portraits). The last selected commander and deck are remembered in the same browser; if no previous selection is recorded, the most recently saved browser deck is preferred, otherwise a built-in deck is used. The Card List & Editor has a separate **Load a deck or saved version** selector listing all original variants and named saved browser versions under that commander.

**GitHub Pages publishing works with either setting:**

- **Branch-based Pages (main / root):** root `index.html` redirects to the generated `docs/deck-lab/index.html`. The static export workflow also publishes its limited generated site into `docs/deck-lab/`, where `summary.html` and `editor.html` live beside the data. Jekyll has no Python requirement.
- **GitHub Actions Pages:** the release workflow publishes the **same** generated files directly as the Pages artifact, with `index.html` at the deployment root. The source branch and repo visibility need not change to use the built companion.

In either mode, ensure the latest Pages build actually completed before assuming a public URL works. Do not use the repository's `web/pages/index.html` directly as a hosted page—it is **source HTML** without adjacent generated `decks.json`, `observations.json` and `names.json`. The static build is the deployable website.

## What the static version already supports

- **Compact commander medallion:** the circular commander portrait sits near the top of the page; clicking/tapping it opens a small artwork picker grouping Magnus Premium/Budget and Mortarion Current/Ideal under their shared commander. The chosen deck is displayed immediately, allowing results and summaries to appear above the fold.
- **Original sounds:** opt-in toggle (OFF by default). Synthesized stone/glyph cues through Web Audio on summon, page change and successful/invalid actions. No borrowed game soundtrack or sound assets; respects user/browser audio policies.
- **Fantasy tabletop styling:** layered stone/basalt backgrounds, warm brass detail, original rune shapes, subdued cyan magical light, accessible controls, responsive layouts and `prefers-reduced-motion` support.
- **Card art:** derives official Scryfall CDN artwork references from cached printing IDs for all cards when available; otherwise shows a themed fallback. Images are loaded remotely by the browser and are not re-hosted from our repo. Commander art is prominent; all available card art can be viewed in card details. Copyright remains with respective owners; Scryfall is credited.
- **Deck composition:** six 100-card lists and associated commanders, color restrictions and pinned original card metadata. Search cards by name/type/Oracle text, inspect types, mana values, Oracle text and Scryfall links.
- **D3-adjacent visualization:** original native-SVG bar charts for card categories and printed mana curve (no D3 dependency).
- **Cached results:** exactly the previously generated **11 seeds per deck** (`0,1,2,3,4,5,7,11,21,42,99`, **66** fixed-seed observations in all). View up to six turns, opening hand, basic land model, draws, mana-value candidates and limitations; export the underlying JSON. No browser simulation or extrapolated win rates.
- **Static Deck Workshop:** one-for-one card swaps, real card color identity and Commander singleton/100-card checks using exported cached details. Undo/revert; Save As a named **localStorage** browser version and reload/delete versions; export a version as a plain-text `.txt` list compatible with the Python deck importer. Canonical deck files stay untouched. Browser storage is **local to that device/browser**, not GitHub or a cross-device account.
- **35,533-name typeahead:** all Scryfall names filtered **offline**, no request per keystroke. Existing cached full identity can be used immediately. If a name is only in the names index, a deliberate **Fetch card details** action can request its full Scryfall JSON over HTTPS (subject to network/CORS) and store the returned record in browser storage. It remains metadata, not executable rules. Strict names and color checks apply before editing.

## Named deck selection and save/load behavior

- The circular commander selector remembers the last-used commander and last-used deck selection in browser storage, including a named saved version. For a newly selected commander, it prioritizes that commander's last selection or newest saved deck, then its built-in deck.
- The editor's **Load a deck or saved version** dropdown groups built-in decklists separately from user-saved named versions. Built-in Magnus/Mortarion variants remain selectable. The **Start a new version** action creates a local draft, and **Save as named deck** creates a separate immutable named browser version. Duplicate names for the same commander are rejected rather than silently overwritten; old versions can be loaded or explicitly deleted.
- Browser versions are saved only in that browser/device. They are not committed to GitHub, synchronized between devices, or added to the site's Python-generated observation archives. A modified deck's Summary and Card List reflect its own saved card counts, but its Results page **clearly states that no new results exist** and offers a button to return to the corresponding original deck's cached results.
- Unsaved edits are visually flagged and require confirmation before switching decks through the commander picker or editor load selector. Export important deck versions as text so browser storage loss cannot erase your work.

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

### Reviewed-action batch snapshot (2026-11-01)

The Results page also displays 100 six-turn bounded-action runs for Magnus premium v1.14, Wretched Ranks, Mortarion current and Necron Dynasties, seeds 0–99, plus inspectable seeds 0–2. The separate `bounded-batches.json` pins each deck hash and records the prior base commit and SHA-256 hashes of the changed engine files. It is a fixed snapshot, not automatically recomputed when the engine changes; regenerate it to reflect later engine changes. Saved or edited deck versions must never inherit these results.

These runs use the limited source-paid single-player kernel and the reviewed action subset. Unsupported cards remain unavailable; commanders, combat, opponents and wins are not simulated. Unequal coverage prevents interpreting between-deck differences as relative strength. The sample runs are illustrative seeds, not statistically selected representatives. The observation archive below remains a separate model.

The simulation snapshot now carries compact turn and hand records for all 100 runs per deck. The slowdown diagnostic selects consecutive turns without one of its listed development/setup events, compares the card types and named cards in flagged and other hands, and shows matching examples ranked by proximity to the flagged group's average lands and unsupported-card count. Its hand comparisons describe association, not cause. Rebuild the dataset offline with `python tools/build_bounded_batches.py`; the Pages build validates matching deck hashes and complete distinct seed records before publication. The separate eleven-hand observation archive is collapsed below the simulation results.
