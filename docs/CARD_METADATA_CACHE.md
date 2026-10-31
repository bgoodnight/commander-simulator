# Shared offline Scryfall card catalog (M0)

Status as of 2026-10-31: **import/cache implementation and regression tests are committed and passing**. The shared catalog itself is **created when the importer runs**, not yet a checked-in database containing all user deck identities. M1 still needs to import Mortarion Current/Ideal and Necron Dynasties using matching manifests. This is **metadata**, not executable Magic rules.

## What was added

- `commander_sim/card_cache.py` stores Scryfall records by **Oracle ID and immutable content SHA-256 revision** and resolves verified names/face aliases conservatively. A shared catalog file indexes the current revision; old revisions remain available for existing deck manifests.
- `tools/fetch_deck_identities.py` checks the local cache first and sends **only unresolved names** in batched collection API calls during an explicit import. It writes the existing fully embedded snapshot format plus a **per-deck .manifest.json** naming the exact cards/versions used by that deck.
- `pinned_deck_entries(deck_path, manifest_path, catalog_path)` reads an immutable deck revision offline, rejecting a mismatched deck hash, card name or missing/modified record. Existing `validate_snapshot` and historical snapshots remain compatible.
- A saved deck manifest remains authoritative after an explicit refresh, even when the catalog points at newer versions of the same Oracle IDs. Using `--refresh` to change cards requires a **new output path** so the old replay is not silently rewritten.
- Each file write is atomic; the importer validates cards and conflicts before writing. A failed HTTP import does not persist partial card identities.

## Import flow: explicit network boundary

```text
User invokes deck import / explicit refresh
    -> Parse decklist, compute deck SHA
    -> Match existing pinned manifest (when present)
    -> Lookup aliases -> current Oracle ID -> immutable revision in local catalog
    -> Only if needed and import is online: batch request missing card names
    -> Validate exact card/face names and immutable raw record
    -> Write shared catalog, per-deck pinned manifest, compatible snapshot
    -> All later game runs / observations read local immutable data, no API
```

**This is not runtime game-state memoization.** No API request is made by `CardCatalog`, `validate_snapshot`, `pinned_deck_entries`, the game driver or normal tests. Only executing the explicit import script may call Scryfall (or an explicit UI Fetch action in the future, through this importer).

## Example: bootstrap from checked-in historical snapshots without using Scryfall

Run from the repository root. This creates an output snapshot, a companion manifest, and a shared catalog using three hash-matched fixtures entirely offline:

```sh
python tools/fetch_deck_identities.py \
  decklists/wretched_ranks_foundations_precon_2026.txt \
  simulator/card_data/wretched_ranks_cached.json \
  --catalog simulator/card_data/shared_scryfall_catalog.json \
  --offline \
  --seed-pair decklists/fixtures/magnus_flameslinger_v0_7_pre_delivery.txt simulator/card_data/flameslinger_v0_7_scryfall.json \
  --seed-pair decklists/wretched_ranks_foundations_precon_2026.txt simulator/card_data/gisa_scryfall.json \
  --seed-pair decklists/mortarion_purchase_reconciled_candidate_2026_10_27.txt simulator/card_data/mortarion_scryfall.json
```

Follow with explicit imports of **Mortarion Current**, **Mortarion Ideal** and **Necron Dynasties** using the same `--catalog` path and distinct output names. Existing names are reused; uncached names are fetched only if the command is run without `--offline`. Card data is fetched once per missing distinct identity, **not once per appearance across decks**.

To revalidate known cards against Scryfall, use `--refresh` with **a distinct output snapshot/manifest filename**. Old pinned manifests stay valid if their revisions remain in the catalog. Do not force-refresh at simulation startup.

## Key tests in tests/test_card_cache.py

- First import fetches one record per distinct new identity; second import fetches zero.
- Importing a second deck with a shared Sol Ring retrieves only its missing cards.
- Offline misses, ambiguous identities, wrong deck hashes, missing/corrupt revisions and failed network requests fail closed.
- Old deck manifests replay unchanged after another import explicitly refreshes shared records.
- Existing Flameslinger, Gisa and Mortarion purchase-only snapshots seed a shared catalog **with zero network access**, and valid generated legacy snapshots still pass `validate_snapshot`.
- The complete existing regression harness checks this separately from full card-effect execution.

## Next milestone

**M1:** use this shared catalog to prepare authentic per-deck pinned manifests for Magnus Premium/Budget, Wretched Ranks, Mortarion Current/Ideal and Necron Dynasties. Build a catalog-driven deck listing and accurate six-turn observation panel; immediately afterward, an initial U0 read-only Deck Lab may expose these data. Actual B-mana, ordinary casts and shared engine turns remain M2/M3. Preserve strict v35 replays and per-ability exact/simplified/unsupported distinctions.
