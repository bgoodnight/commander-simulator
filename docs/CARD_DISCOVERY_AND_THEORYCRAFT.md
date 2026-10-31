# Card discovery and first-run theorycraft metadata import

**Status:** implemented in `commander_sim/card_discovery.py`, `commander_sim/card_name_catalog.py` and `tools/theorycraft.py`, with automated tests. The complete name list is a **separate names-only index**, not a guarantee that every card has detailed rules implemented.

## Desired behavior

When a new or modified Commander deck is prepared for its **first observation or game run**, identify all distinct cards using the existing shared, immutable Oracle-ID catalog.

- Already cached: use verified local printed metadata; make **zero Scryfall calls**.
- Not cached and online preflight enabled (default when invoking `tools/theorycraft.py`): batch-fetch the missing **exact names**, validate Scryfall identities, update the shared catalog, and pin the resulting immutable revisions to a snapshot for that **exact deck hash**.
- Not cached and `--offline` requested: fail with the missing names; never guess identity or an ability.
- On subsequent runs of the same deck hash: the existing manifest supplies the exact card revisions. **No extra API calls**. A changed deck receives a new hash and separate snapshot.
- A typo or ambiguous name is **not fuzzy-corrected silently**. Fail with an actionable error; autocomplete should help select canonical names before preparation.
- The fetched card type, costs, colors, printed keywords, power/toughness and Oracle text are source **metadata only**. They do not automatically activate unimplemented effects, grant targets or determine legal game actions.

## Command-line usage now

From the repository root:

```sh
# Automatically fetch missing exact card identities on the first preflight:
python tools/theorycraft.py path/to/my_new_deck.txt --commander "Ghoulcaller Gisa"

# Use only local metadata; error if a card has never been imported:
python tools/theorycraft.py path/to/my_new_deck.txt --commander "Ghoulcaller Gisa" --offline

# Explicitly refresh the full canonical Scryfall names-only index in ONE request:
python tools/refresh_card_names.py
```

The default per-deck snapshot location is a `.commander_metadata/` directory alongside the deck. You can supply `--output-dir` for a different local workspace or `--catalog` for a separate Oracle-ID data store. Use `--seed` and `--turns` for deterministic observation.

**This command currently produces observation, not actual source-paid Magic gameplay.** The same automatic preflight service is intended for the U1 deck-edit Save As and future M3 real-game runner. **Game turns, card casts, draw steps and simulations never call Scryfall.**

## Autocomplete strategy: zero API calls per keystroke

Scryfall provides a full English card-name catalog via `GET /catalog/card-names`. Instead of calling `/cards/autocomplete` every time the user types, the explicit `tools/refresh_card_names.py` command downloads and SHA-validates that list **once**. It is saved separately as `simulator/card_data/scryfall_card_names.json`.

- `GET /api/cards/suggest?q=midnight` in local Deck Lab searches the cached detailed identities and the **locally stored complete names list**. It returns the closest names, including existing cached **face aliases**, with an explicit `requires_metadata_import` Boolean and `source`.
- The current read-only Deck Lab already includes a name-suggestion input; it **does not edit decks or initiate a metadata fetch**.
- In future U1/U2, picking a recognized name inserts only the canonical choice into the **draft** deck. A name-only suggestion can be selected, but its full Oracle record must be resolved, legality-checked and pinned when the user saves or starts the first run. A typo remains invalid.
- Updating the full-name list is an **explicit refresh**, not automatic on every page load. Card names available in the detailed cached Oracle catalog remain searchable even before the full names index is downloaded.
- `online_name_suggestions` supports an explicitly requested single Scryfall autocomplete call as a fallback, but is **not connected to the typeahead endpoint**, keeping all routine typing offline.

## Future UI milestone boundary

**U1:** versioned, undoable local deck edits and Save As with local identity validation.

**U2:** the UI may use this same metadata preflight to fetch missing identities when the user adds a new card or explicitly prepares a new deck. Show what was fetched, missing names, Commander/color-identity legality, and the difference between printed characteristics and behavior coverage. Never change canonical ideal/current/precon fixture files.

**M3:** actual source-paid turns should call preflight **before beginning** and then load the saved pinned snapshot into one authoritative engine. Simulated gameplay cannot initiate network requests.

## Tests

`tests/test_card_discovery.py` verifies first-run fetch, overlap/reuse, changed deck SHA, exact-name fail-closed, offline mode, explicit online autocomplete and deterministic observation. `tests/test_card_name_catalog.py` verifies one download, offline autocomplete including uncached card names, catalog integrity and cached-metadata preference. `tests/test_deck_lab.py` verifies that the local suggestions endpoint never calls Scryfall.
