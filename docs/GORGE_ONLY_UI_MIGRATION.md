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

## 2026-11-03 cutover: active gorge-only path

The read-only predecessor snapshot is preserved at
`archive/python-rules-pilots-simulations-20261103`. Python game simulations,
legacy pilots/rules and pre-gorge analytics remain accessible there. The
automated legacy archive/refresh/audit workflows have been disabled from
ordinary pushes/PRs on main and are manual-only.

**Correction to prior benchmarks:** gorge's engine defaults to **20 starting
life**, even with `FormatCommander`. Earlier reported games and win rates
therefore cannot be treated as ordinary 40-life Commander results. The
active driver explicitly sets `StartingLife:40` and `Mulligans:7`. The
public-state exporter and source validator fail closed if a captured game
begins at another life total.

The corrected `gorge-native-smoke.yml` exercises eight real Commander deck
lists with gorge's built-in pilot and retains two complete source logs
(privately in Actions artifacts). It exports two `gorge-ui-replay-v1` files
with actual event highlights and **source-derived turn-entry snapshots**.
The snapshot boundary is `first_pending_decision_of_turn`; it is not an
end-of-turn frame.

Safe published fields: seat, turn, life, elimination, unspent mana,
hand/library **counts**, plus named battlefield, graveyard, exile and
command-zone objects. Hidden hand and library IDs, ordering and source
decision logs are NOT placed in static page assets. The complete source
game record is retained only in the Actions artifact, enabling further
replay verification.

When a successful main-branch smoke build publishes
`web/pages/data/gorge/manifest.json` and its allowlisted replay samples,
the existing Deck Lab native gorge panel loads the first one automatically;
the file chooser remains available for local full event logs.

**Remaining limitations:** state snapshots are at turn entry rather than
turn end; tapped status, historic +1/+1 counters, continuous effects and
full private hand identities are not yet present in this public projection.
The historical Python analysis panels remain collapsed as an archive;
they are not current gorge evaluations. Do not use old Python win rates for
comparison against corrected gorge runs.
