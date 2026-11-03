# Two-precon narrative rules audit — November 3, 2026

This is an **observed gameplay and pinned-source gap audit**, not a legal
precon-versus-precon match. Each real precon was the seat-zero physical deck;
the other three seats were explicit abstract control/mixed opponents.

Source: `testdata/two-precon-rules-audit/precon-rule-gaps.json`.
Source engine: branch based on `main` revision
`8a4d18da0f736ecd5c0a212071151bc0d1459649`.
Workflow: https://github.com/bgoodnight/commander-simulator/actions/runs/41643766070

## Validation

- 5 seed values (0–4) x 2 scenarios x 2 pinned precons = **20** observed games
- Necron Dynasties: 10 completed, no exceptions; 9 losses / 1 win
- Wretched Ranks: 10 completed, no exceptions; 6 losses / 2 wins /
  2 censored, no exceptions
- Source-pinned inventories: Necron (22 reviewed partial, 26 provisional-only,
  23 no registered recipe); Wretched Ranks (34, 13, 21 respectively)
- **Do not use the win rates as precon head-to-head estimates**: abstract
  opponents, incomplete printed effects, and just ten games per deck.

## Highest observed unsupported hand actions

A repeated card in a player's hand counts **once per round** as an unsupported
hand action. This is a rough potential-impact indicator, not a proof that the
card was affordable or castable each time.

| Necron card | Games with observations | Hand-turn observations |
| --- | ---: | ---: |
| Tomb Fortress | 6 | 89 |
| Out of the Tombs | 6 | 72 |
| Mutilate | 5 | 66 |
| Darkness | 4 | 44 |
| Living Death | 4 | 44 |
| Lokhust Heavy Destroyer | 4 | 42 |
| Sculpting Steel | 6 | 38 |
| The War in Heaven | 3 | 37 |
| Their Number Is Legion | 3 | 36 |
| Necron Deathmark | 2 | 34 |

Lokhust Heavy Destroyer already has reviewed ETB/unearth suboperations;
its unsupported *hand action* doesn't erase that partial implementation.

| Wretched Ranks card | Games | Hand-turn observations |
| --- | ---: | ---: |
| Consumed by Greed | 6 | 85 |
| Consuming Corruption | 5 | 78 |
| Patchwork Banner | 6 | 78 |
| Liliana's Mastery | 5 | 65 |
| Bad Moon | 4 | 61 |
| Witch's Cottage | 4 | 56 |
| Champion of the Perished | 4 | 51 |
| Ayara, First of Locthwain | 6 | 47 |
| Open the Graves | 4 | 46 |
| Diregraf Colossus | 2 | 34 |

Ayara and Open the Graves have registered partial operations and must be
tested for missing **hand-cast entry points** separately from their abilities.

## Reusable implementation order

1. **Source-paid hand casting and actual static abilities.** Investigate
   Witch's Cottage, Tomb Fortress, Patchwork Banner, Bad Moon,
   Liliana's Mastery, and comparable battlefield/land-entry effects.
2. **Reusable destruction and damage recipes.** Mutilate, Darkness,
   Consumed by Greed, Consuming Corruption, and Necron Deathmark.
   Distinguish prevention from damage/life loss; do not grant artificial
   generalized removal when the printed costs, targets, or restrictions differ.
3. **Recursion and zone/simultaneous movement.** Out of the Tombs, Living
   Death, Their Number Is Legion, The War in Heaven. Test correct controller,
   graveyard ownership, timing, state-based actions, and death triggers.
4. **Creature-enter and static/tier effects.** Champion of the Perished,
   Diregraf Colossus, Gray Merchant of Asphodel, and Ayara; activate
   existing reviewed suboperations rather than reimplementing them.
5. **Copy and alternate keyword abilities.** Sculpting Steel, unearth,
   saga/loyalty-like sequential effects, and black creature recursion.

Before each implementation, reproduce the exact game/turn and establish the
current zone, legal mana payment, targets, action permission, and expected
typed effect. Add targeted seed regression tests, then rerun this 20-game
cohort. Only after four-seat physical-deck support is ready should these
specific precons play one another for actual matchup results.

## Coverage boundaries

- An action unsupported in hand may still have independently registered ETB,
  death, utility or recursion effects.
- Static inventory counts exclude generic kernel permissions where no named
  registration is required.
- The audit does **not** infer full rule semantics from Oracle text.
- The observed games are no substitute for manual turn-by-turn verification.
- Completed games here means the runner produced a valid result; it does not
  guarantee every printed interaction was implemented.
