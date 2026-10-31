# P0.5 implementation review

The roadmap's sequence remains appropriate; a second full audit is not needed before the deck-injection slice. The existing v35 table and zone system can accept a validated composition through a detailed-player factory. The default premium engine remains the same; budget now intentionally uses v35 rather than the historical v30 AltarTable, so budget outcomes need a new comparison baseline rather than an assumption of old-engine equivalence. Historical tables remain callable for regression.

The factory seam is transitional. Existing card installers still mutate shared tables and assume definitions for cards absent from a given deck. The player registers definitions from the two existing presets without adding physical cards; fixed-seed premium comparisons, zone conservation, sparse-deck initialization, and budget Frostboil/Altar tests protect this boundary. Do not treat these definitions as evidence that the effects are supported.

The actual saved Flameslinger v0.7 list uses descriptive section headings and the full Oracle name for Lindblum. The parser accepts these without using the headings as card-type evidence and checks declared section counts. Fifty distinct names in that list are absent from the bundled identity reports, so the current loader must reject it. This count describes missing bundled metadata, not necessarily nonexistent or unsupported cards.

## Remaining P0.5 order

1. Ingest a versioned, trustworthy identity snapshot separately from gameplay, preserving exact Oracle identity, faces, printed colors, mana value, type and Commander legality. Report every missing or ambiguous identity, fail closed on validation, and keep provenance. Do not infer identity or card types from a list's section headings.
2. Build an explicit capability inventory from the current assembled engine, with distinct supported subsets, partial behavior, and unsupported effects. Ensure unknown or unsupported land/spell cards cannot acquire fabricated abilities. Query/search paths must use the same verified definitions; consider face-sensitive searches explicitly.
3. Introduce an observation-only mode as a separate analysis path with no claim of resolved unsupported effects. Document its policy assumptions and which rules it does and does not apply.
4. Run the authoritative v0.7 list through that path, with a fixed-seed six-turn trace, zone counts, stated mana reservations and opponent assumptions. Benchmark compared runs on the same host, preserving the existing uncached reference.
5. Continue migrating card installers and metadata into package services; avoid introducing more table subclasses, global deck mutation, or caching before invalidation tests exist.
