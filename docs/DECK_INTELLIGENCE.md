# Deck Intelligence: automated and curated strategic tracking

Status: pure read-only reporting layer, not a game engine, auto-combo detector, or source of game events.

## Two complementary sources

1. Automatic printed features: `printed_features(catalog, quantities, profile)` counts verified Scryfall keywords, types and subtypes. Printed attributes describe cards; they do not establish rules support, synergy effectiveness or executable abilities.
2. Curated deck-specific profiles: optional `key_cards` (id/card/role), `groups` (id/cards), and `combos` (id/pieces). Cards must resolve to verified exact names in the supplied pinned catalog. Store profiles by deck version; do not change immutable canonical decklists.

Example illustrative profile (names below are placeholders, **not** a claim about a Magnus combo):

```json
{"key_cards":[{"id":"engine","card":"Engine","role":"engine"}],"groups":[{"id":"wizards","cards":["Wizard A","Wizard B"]}],"combos":[{"id":"sample_pair","pieces":["Wizard A","Engine"]}]}
```

## Live turn-state adapter contract

`analyze_game_turns(catalog, profile, states)` accepts only trusted engine-projected states with `source=authoritative_game`, monotonically increasing `turn`, and verified names in `battlefield`, `hand`, `graveyard`. It never simulates game objects. The M3 adapter must project these fields from authoritative kernel zones and controller-specific objects, not maintain an independent battlefield.

An optional `verified_tutor_access` record includes `tutor`, `target`, `destination` (`hand` or `battlefield`) and `verified:true` **only when the engine has proven the tutor can be used, the target is searchable in the appropriate zone, and all relevant restrictions, costs and timing permit the access**. Merely owning a tutor or drawing it does not prove access.

A curated combo can report piece count on the battlefield and available in hand or via verified tutoring. Even if every piece is present, it is `all_pieces_present_unverified`, not operational. Only `engine_verified_combos` from the rules layer may declare `engine_verified_operational`; that still does not establish a win until a supported win condition actually resolves.

## Planned visualization tiers

- Universal: mana sources, lands played, effective ramp, card draw, board presence, type/subtype/printed-keyword categories and first unsupported decision.
- Strategy: per-turn counts from curated mechanic groups, first key-card draw, verified tutor access, on-battlefield turn and combo piece accessibility.
- Comparisons: percentage reaching milestones by turns 3/5/7/10 and paired-seed differences, with uncertainty intervals and coverage labels. Runs blocked by omitted rules should be censored rather than counted as losses.

## Boundaries and next steps

The new module is a reporting contract, not a production M3 adapter, persistent profile store, profile UI, or complete statistics pipeline. First integrate the actual multi-deck turn driver; then emit ID-backed snapshots and verified search/cost events, run milestone aggregations, and add Deck Lab U3 charts. Printed keywords may propose descriptive groups for user review, but never auto-classify card text as game mechanics or combos.
