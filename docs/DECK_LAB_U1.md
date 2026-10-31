# Deck Lab U1 — editable local deck variants (MVP milestone)

**Status:** U1 first vertical slice implemented. This is a local browser tool backed by the six M1 validated decklists, shared Scryfall offline catalog and the immutable deck-hash metadata importer. It is **not a live-game simulator** and does **not** edit canonical/precon decks.

## Launch and inspect in Work mode

From a local checkout of the GitHub repository, run:

```bash
python tools/deck_lab.py
```

Open `http://127.0.0.1:8765/` in the **same** computer/browser environment. Work mode can run the project and use its cloud browser to interact with the interface; the local server on your personal computer is not automatically visible in Work's cloud browser. The first visual review should inspect desktop and phone-sized layouts and actually try one valid and one invalid swap.

## U1 workflow

1. Select any of the six authenticated Commander lists. Its canonical file stays untouched.
2. Under **Theorycraft a new version**, select a card to remove and type an exact card name to add. Scryfall's **35,533-name** local index helps with spelling; however, **U1 swaps require the selected card's detailed Oracle record to already be cached**. An uncached name displays an error rather than secretly contacting Scryfall.
3. Click **Try swap**. The Python backend revalidates a 100-card singleton Commander deck with the original commander and its color identity; invalid swaps are not added to the draft. Multiple successive swaps can be stacked, undone or reverted. The display shows the signed card-count difference for each changed name.
4. Enter a title and click **Save validated copy**. The system writes an entirely new immutable local `workspace/deck_lab/<title>-<deck-hash>.txt`, a metadata record and a matching deck-hash-pinned offline snapshot and manifest under `workspace/deck_lab/metadata/`. A saved variant is never written over a canonical fixture or an existing saved version.
5. Under **Saved local versions**, use **Observe version** to run the existing deterministic observation using the saved deck's own snapshot. The result labels the saved copy explicitly. The editor search supplies its own offline suggestions and distinguishes names requiring metadata import. A failed swap preserves the previous valid draft. These are opening-hand and mana-value candidate observations—not legal casting or resolved Magic abilities.

The server binds only to `127.0.0.1` by default. U1 preview/save POST requests require same-origin local HTTP JSON and bounded payloads; no Scryfall requests occur on typing, preview, save or observation.

## Current boundaries

- U1 has **one-for-one swaps only**: Commander remains fixed; quantities are conserved at 100; singleton and color restrictions are checked on every preview. It supports multiple swaps and undo/revert until Save As.
- The full name index provides suggestions for **uncached** cards, but those names cannot be added in this U1 slice until they are imported via the existing `tools/theorycraft.py` first-run preflight or U2 future UI integration. This separation makes the cache/legality boundary explicit and prevents accidental network calls.
- The six canonical presets remain **immutable**. Saved versions live only in the local workspace unless the user deliberately commits/uploads them separately.
- No new card ability is implemented by importing printed Oracle text; metadata coverage is not effect fidelity.
- Comparison currently consists of card-count differences and deterministic same-seed observations of saved versions. More visual curve and per-seed comparison tools are U3.
- Full interactive board and source-paid actual mono-black gameplay remain separate engine milestones M2/M3; two-detailed-deck head-to-head is optional.

## Validation

```sh
python -m unittest tests.test_deck_workspace -v
python run_all_tests.py
```

Regression tests cover legal and illegal swaps, unchanged source fixtures, strict singleton and color identity, offline missing-card failures, hash-pinned Save As, duplicate-save protection, tampering detection, deterministic saved-version observation and path validation.

## Next milestones

**U2** connects the same existing `prepare_theorycraft_deck()` cache-first service to an explicit new-card import action at deck editing time, with a preview of fetched metadata and full Commander legality before saving. It should not call Scryfall per keystroke or during gameplay.

**U3** adds mana-curve visuals, readable version comparisons, hand and turn timelines. Use Work mode to visually inspect this first interface before polishing or adding elaborate tabletop interactions.

The observation settings optionally apply one free multiplayer mulligan under a conservative land-count policy. Basic lands and Command Tower are the only currently modeled sources; candidate spells remain a total-mana-value screen, not legal actions.
