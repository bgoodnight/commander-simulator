# Commander bracket evidence (provisional)

The Deck Lab summary uses a **read-only** bracket screener. It does not modify the Magic engine, game outcomes, replay state, or simulation batches.

## Data and refresh boundaries

- `web/pages/game-changers.json` is a reviewed, dated 53-card snapshot of Wizards' official Game Changers list (last updated February 9, 2026; verified November 1, 2026). The published Pages copy ships from the same source at build time.
- The normal Scryfall card import/refresh already pins Oracle identities and printed text. This scorer reads those pinned card records and the small reference table. It never calls Scryfall during simulation or while rendering a game.
- On each deck selection or edit, `brackets.js` compares every visible card to the official table by canonical name and face aliases. Unresolved identities are reported, not silently assumed non-Game-Changers. The UI separately displays the list of matches.
- On future updates, verify Wizards' published list; update only the reference table and its update date, adjust its count test, and rebuild Pages. Do not change old pinned Scryfall snapshots merely to flag a Game Changer.

## Classification

0 Game Changers -> starting estimate 2 (Core); 1–3 -> 3 (Upgraded); 4+ -> 4 (Optimized). These are **minimums implied by the Game Changers list**, not a full bracket assessment; the numeric estimate is expressly *provisional*. Obvious printed mass-land-denial text can raise the starting estimate to 4. Printed searches and extra-turn text are shown as inspectable flags, not automatic judgments, because card text alone cannot determine plan, two-card combos or actual gameplay.

Bracket 1 (Exhibition) and Bracket 5 (cEDH) must never be inferred merely from the card list; both depend especially on intent and play environment. For Brackets 2/3 the evaluator cannot currently prove an absence of early combinations, chained extra turns or resource locks. Even fully identified decks have incomplete strategic evidence.

## UI and further work

The summary displays a compact estimate and Game Changer count, with an expandable list of matching clickable cards, deck search/extra turn/land denial signals, metadata gaps, sources and limitations. Edited versions are rescored in the browser without changing the precomputed simulation reports.

**Next scope (not implemented):** maintain a human-reviewed structured combo registry, tie its identified enablers to deck identities, and use calibrated four-player finished-game and turn-to-threat distributions for a *separate* performance-based recommendation. Do not infer win percentages from six-turn observations, bounded action traces or keyword counts. Consider user override/intent annotation for sanctioned exhibition games or cEDH pods.

Reference: https://magic.wizards.com/en/formats/commander
