# Magnus simulator — opponent-only v4 threat escalation prototype

This is a **standalone prototype opponent layer**, not integrated yet with the detailed modular Magnus v3 card engine. It has three active opponents sampled from seven play types and a fourth **passive Magnus seat**, with 40 starting life and no cards, plays, or blocks. The passive seat is *deliberately not a realistic Magnus game*: it is an interface placeholder for future integration.

## Run it

Python 3.10+ standard library only.

```bash
python tests.py
python run.py --goldfish 600 --tables 350 --turns 10 --seed 20261028
python make_traces.py
python snowball.py
```

## Modules / customization

- `profiles.json`: seven play types. Each defines **one synthetic 99-card deck composition**, play priority, willingness to attack, and mana held for potential counterspells. Deck type and piloting style are deliberately unified.
- `templates.json`: **generic action costs and impact distributions**, not named MTG cards.
- `engine.py`: `AbstractCard` keeps its category and mana cost once drawn. `Player` has a shuffled 99-card abstract library, opening hand and one simple free redraw, life, drawn hand, mana, persistent creature/engine states, history. `Table` governs turns, multi-action mana budgets, counter responses, threat ranks, stochastic targets, one-to-one combat blocks, removal, board wipes, and opponent elimination by damage. Deck draws and targeting RNG use separate seed streams.
- `run.py`: 600 independent *no-interaction* draws per archetype plus two sets of 350 same-seed random-table matchups (with and without table interactions). Reports P10/P50/P90 turn-level differences.
- `snowball.py`: observational compare of turn-8 strength between better and worse turn-4 mana or engine development; **association not a randomized causal intervention**.
- `tests.py`: rules smoke tests and reproducibility checks.
- `trace_*.md`: two complete 10-round traces, each with a matched no-interaction counterfactual.

## Design decisions

1. No hand-wavy "fast start" bonus. An opponent has to draw and pay for actual generic land, ramp, card-draw or engine categories to accelerate.
2. Each abstract card is sampled into the 99-card category bag and given a **fixed** generic mana cost at deck construction; a true flood or mana shortage can persist.
3. Early resource plays compound: ramp remains available next turn; persistent engines have probabilistic extra card-draw/token production. Early engine creatures can die and lose that capacity.
4. Three opponents use separate life bars, decks and state; an active opponent can remove another opponent's creature or permanent, counter spells, wipe creatures, or attack. An attacked opponent can make simple single-block decisions; passive Magnus never blocks.
5. The public threat *score* weights board power, bodies, engines, mana, combo pieces, hand size, and life. **Ordinal position** (first/fourth) influences *randomized* target selection. Attack opportunity separately values lack of blockers and low life. Target exposures are logged so rank-one targeting isn't incorrectly compared with rank two when the current attacker is itself first.
6. Only currently available mana can be spent. An opponent can play multiple affordable generic actions in one turn or reserve mana for a counterspell response.
7. Goldfish first, opponent-on-opponent second: the exact same initial decks are used across paired interference scenarios. Once interaction removes a draw engine, later draws diverge intentionally.

## Crucial limitations and next engineering tasks

- **Not empirically calibrated** to a sample of real Commander tables. The curves are *internal qualitative checks*, not metagame forecasts.
- **Not a win-rate or power-level metric**. The arbitrary threat score is an ordering aid, not a probability. It especially UNDERVALUES Control (counters/answers in hand) and Combo (hidden win proximity). A combo `finisher` can register an **abstract win attempt**, but does not automatically win the table.
- Draw composition and mulligan are synthetic; the extra redraw doesn't bottom a card, no deck-specific color costs or two-/three-color mana problems, no opponent commander, no extra-turn sequences, no lifegain.
- Simplified single-creature blocks and simultaneous lethal combat; no multiple blockers, protection, first strike, trample, commander damage, or combat tricks. Buff spells give lasting power counters to creatures present at cast time.
- Only a shallow counter response is modeled; no full stack/priority and no counter-counter exchanges. Removal is generic and may hit artifacts/engines only for the appropriate fraction of cards.
- A generic board wipe destroys creatures only; artifact/enchantment-like engines remain. Real wipes differ, and their effects need tagged definitions.
- No opponent-to-opponent political memory, no sophisticated forecasting, no targeting by hidden hand composition; only hand size is public.
- Engine token generation/draw probabilities, action costs, and archetype mixes remain unvalidated assumptions. Some curves (notably token snowball) may run too hot and require future adjustment.
- **Our actual Magnus deck isn't yet taking actions**. To join with v3, expose each opponent action as an event (`cast_spell`, `declare_attackers`, `targeted_removal`, `board_wipe`) and pass it to Magnus's shared legal-response engine. Threat state is then updated after Magnus's reply. Do **not** make a second hard-coded database of Magnus card abilities.

## What to validate before using the model to choose a deck card

1. Are all seven curves plausibly shaped? In particular, separate early combat threats from late combo/control threat capabilities.
2. Is a good early draw actually persistent but not irrevocable? Test forced mana-screw, early engine destruction, and recovery draws.
3. Do opponent win attempts produce realistic game termination/avoidance, and does Control visibly prevent them?
4. Calibrate opponent draw budgets and play priorities with anecdotal or recorded actual Commander games.
5. Integrate the Magnus v3 card catalog and real response costs; only then compare deck versions using paired random seeds and matched opponent archetypes.
