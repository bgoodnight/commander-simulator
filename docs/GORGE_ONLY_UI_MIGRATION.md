# Gorge-only migration: replay UI contract

## Active engine decision

Gorge is the target **sole** rules engine and AI pilot for new Commander
simulations. The Python rules/pilot code and old simulation artifacts are
**legacy** and should be frozen, not used for new win-rate comparisons.
They are not deleted in this migration: the gorge replacement still lacks
authoritative object identities and full turn-end zone snapshots. A destructive
cutover before those exist would remove features without a verified replacement.

## Actual recorded fixture source

The Nov 3 gorge benchmark (32 completed/replay-verified games) produced native
JSON logs for seeds 100 and 101. They use `gorge-native-trace-v1` with
`log.events` and `log.intents`. The raw logs are developer-only artifacts
because they contain hidden card information.

Generate public, source-evidenced UI records with:

```bash
python -m tools.gorge_ui_export /path/to/gorge-seed-100.json \
  /path/to/gorge-seed-101.json --out /tmp/gorge-ui
```

This creates `gorge-ui-replay-v1` files for the Deck Lab's existing
**Native four-player game replay** file picker. The browser displays
recorded turns, highlights, named cast cards, mana color counters,
tokens, and expandable event evidence. It never infers missing snapshots.
It deliberately strips all `secret` events and does not copy native
decision payloads. Do not publish the native log or the opt-in
`--include-hidden` export.

## Crosswalk and state design

- Permanent, versioned card crosswalk: compiled gorge card identity ->
  Oracle/Scryfall ID, display name, image and characteristics. Must be
  pinned to the gorge corpus version.
- Per-game object map: object ID -> card identity; this export can
  partially establish mappings from explicit native casting-event text.
  Unknown objects remain unknown; tokens and copies need explicit records.
- Authoritative per-turn snapshots: life totals, hands, lands,
  creatures, artifacts, enchantments, graveyards, mana, counters,
  tapped status and visibility. **Not available in current native log.**
  Add them in the gorge Go driver before enabling the corresponding UI
  cards. Do not reconstruct these from incomplete events.

## Archive/cutover acceptance criteria

1. Gorge event export + permanent card crosswalk + per-game object
   identities verified against native replay hashes.
2. Four-seat end-of-turn snapshots with hidden-information visibility
   tested against authoritative engine state.
3. UI renders the above without relying on Python rules or AI pilots.
4. All benchmark decks load and run with verified replays; new deck
   matchup and win-rate reports reference only gorge batches.
5. Move legacy rules/pilots and old simulation data into a dated,
   read-only archive with a provenance manifest, then remove active
   imports and UI links. Do not silently mix old and new run data.

The v1 export is the **first populated UI fixture**, not a claim that
the full gorge-only migration is finished.
