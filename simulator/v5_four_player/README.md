# Commander Simulator v5 — four-player abstract sandbox

A testable, configurable **four-active-seat** multiplayer Commander *approximation*. This version calibrates abstract archetype matchups before replacing a seat with an actual detailed deck such as Magnus the Red v1.6.

**Not a full Magic rules engine. No official/card-text engine is claimed.** Current abstract decks are synthetic 99-card category decks, not real Commander decklists. Actual v3 Magnus data is bundled for future reintegration, but **is not participating** in the v5 Monte Carlo results.

## Quick start

Python 3.10+; no external packages required.

```sh
python tests.py
python experiments.py --mixed 2800 --mirrors 120 --controlled 140 --limit 30 --seed 20261028
python replays.py
python integration_demo.py
python bridge_manifest.py
python make_report.py
```

`experiments.py` writes `results_v5.json`; `make_report.py` writes `CALIBRATION_REPORT.md`. To see new runs, change the counts/seed. 7 archetypes are listed in `archetypes.json`; the abstract card roll ranges live in `templates.json`.

## Architecture

- **Player**: own life, hand, 99-card library, land drops, permanent battlefield, reserved mana, creatures, and `Pilot` implementation.
- **CardSpec**: stable card identity, type (`creature`, `instant`, `sorcery`, etc.), mana value, effect key, parameters, optional colored-cost metadata.
- **Action**: a cast/request with card type, effect key, controller, resource cost, legal target and target object, and parameters. Both abstract and detailed source cards must use this shape.
- **Table**: all four seats act through the **same** public targeting, life, combat, elimination, removal and counterspell-response machinery. It does not special-case the Magnus seat.
- **Effect registry**: `Table.register_effect('effect_id', handler)` for card-specific effects not built in. `Table.on_event(listener)` provides hooks for `spell_cast`, `spell_countered`, `spell_resolved`, `damage`, `creature_entered`, `creature_died`, `combat_attack`, `land_played`, `turn_start`, `elimination`. Cast triggers fire even if the spell is later countered.
- **Response hooks**: `Table.add_response_hook(hook)` for reaction abilities such as Patron Wizard, with public action context. Built-in counters know the spell's type, and use actual held cards and mana.
- **Payment policy**: `Player.payment_policy` is an injectable seam for full colored mana and cost reducers. The current abstract model only spends fungible mana; detailed-deck payment adapters are **not implemented**.
- **Pilot**: protocol `select_action(table, player) -> Action | None`. Each abstract play type uses a priority pilot configured from `archetypes.json`. A future detailed deck can inject an entirely different pilot; `Table.with_players([...])` loads four custom players.
- **Blocking**: default efficient-trade policy; an injected detailed seat can set `block_policy='never'` to preserve the engine as requested.

## Archetype construction

Every play type is one unified deck-and-pilot profile, not personality × deck. `archetypes.json` contains the 99-card category recipe, main action priority, attack rate, counter reservation, finisher type, ramp rate, and reaction tendencies. Random draws and permanent engine survival drive good/bad starts. Samples use replacement, permitting identical archetypes in multiple seats.

The current abstract finishers are **types of synthetic effects** (not specific MTG cards): `combo_win`, `spell_burst`, `inevitability`, `overrun`, and `damage`. Combo requires three distinct persistent setup cards, one finisher drawn and cast, and seven mana sources; its spell can be countered. Spell burst damages all opponents simultaneously. Control finisher installs a removable clock that damages players each subsequent turn. Creature and burn damage can eliminate one or more players without forcing an arbitrary win.

## Replacing an abstract seat with a real deck

The important interface is already exercised by `tests.py::test_external_pilot_fourth_seat_runs`: a named cardlist with an independent pilot occupies an active seat and plays in the same game as three archetypes. `integration_demo.py` exercises three actual-card **examples**: Young Pyromancer (cast trigger), Preordain (simplified draw), and Pongify (targeted creature-to-Ape replacement). These are integration demonstrations, not a fully validated implementation of those cards. The full v3 `cards.json`, `deck_v16.json`, and `combos.json` are available under `v3_source/` with status inventory `v3_bridge_manifest.json`.

**Important remaining work:** color-accurate mana production, mana-cost reductions, timing/stack priority, creature keywords, per-card printed-text handler coverage, spell copying, tutors, buyback, combo execution, and detailed deck AI. The v5 framework has hooks for these but **does not yet implement them**. Do not compare Magnus decklists with v5 match results.

## Inspect replays

- `replay_control_mirror.md`: 4x Control, unresolved after 30 rounds.
- `replay_spellslinger_burst.md`: 4x Spellslinger, table-wide spell damage eliminates two players simultaneously.
- `replay_aggro_aggro_control_combo.md`: two Aggro players, Control and Combo; Control survives.
- `replay_mixed_archetypes.md`: Aggro, Control, Combo, Ramp/Stompy; multiple threat leaders/eliminations.

Each replay contains the round-level scoreboard and complete action narration. The JSON partner file contains machine-readable game state history.

## Fairness / caveats

All assumptions are synthetic and not fitted to a real Commander gameplay data set. Reported win rates and times are **properties of this model only**. Hold both configuration and seed constant for paired tests, and use independent validation against real play to calibrate speeds and attrition. A balance target of roughly 25% per occupied archetype seat in random four-player matchups is a *sanity check*, not a rule to impose on games.
