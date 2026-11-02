# Deck-derived deterministic pilot v1

The current pilot is **one shared physical action-ranking mechanism**. It does
not have commander-specific scripts, nor does it infer the legality of a card
from Oracle text. Reviewed handlers and the mana kernel first construct a set
of actually payable, target-legal actions. The pilot chooses **only among
those actions** and records its preference rationale.

## Decision sequence

1. The existing physical engine and source-pinned handlers determine legal
   card actions, costs, targets and timing.
2. `infer_deck_signals()` examines verified printed deck cards with actual
   quantities (not commander names). It counts potential spell-trigger,
   graveyard, sacrifice, token, artifact and combat-related synergies.
   These counts are *strategic signals only*.
3. `PilotContext` reads current life, land/mana availability, hand,
   creature/graveyard state and opponent board size.
4. `rank_legal_action()` applies bounded common-sense preferences. Examples:
   early mana development, refilling a small hand, urgent removal at low life,
   and prioritizing an engine that will benefit from repeated spells.
5. The highest score wins, with stable tie-breaking by payable source count,
   card name and physical object ID. No random learned parameters, no
   commander-name branches, and no use of unrevealed library cards.
6. The runner records `events[t].pilot_decisions` in the existing
   per-turn data with `card`, `kind`, `role`, `score`,
   `factors`, `candidate_count`, `personality` and actual source ID.

The default `adaptive` profile uses printed deck composition to adjust
weights. Manual styles are deterministic numeric preference presets:

| Style | General tendency |
|---|---|
| `adaptive` | Responds to verified spell, recursion, token, sacrifice, artifact and combat density |
| `balanced` | Fixed neutral default weights; no composition multipliers |
| `engine` | Slightly favors engine bodies, recursion and cards drawn |
| `tempo` | Slightly favors early board pressure and removal |
| `conservative` | Slightly favors defensive removal, mana and replenishing cards |

All five use the **same legal-action set**. Personalities only change
relative priorities; they do not bypass mandatory costs or missing rules.

## Execute and compare

```bash
# One reproducible traced run
python -m commander_sim.early_game_runner \
  --deck magnus_premium --seed 7 --turns 12 \
  --provisional-mode safe --pilot-style adaptive

# Compare the same opponent scenario and seeds by selected preference
python tools/build_game_outcomes.py \
  --deck necron_dynasties --scenario mixed \
  --rounds 20 --seeds 12 --pilot-style engine \
  --provisional-mode safe \
  --output /tmp/necron-engine-outcomes.json

# All eight deck variants, 2 seeds, 12 physical rounds
python tools/audit_pilot_narratives.py \
  --deck all --seeds 2 --rounds 12 --scenario mixed \
  --provisional-mode safe --pilot-style adaptive \
  --output /tmp/pilot-narratives.json
```

The narrative audit emits actual life, hand, card-action and pilot-decision
records, plus clearly **advisory** review flags (idle turns with unsupported
hands, draws before cleanup, late ramp, low-life pressure). These flags
are not unproven declarations that the play was illegal. The GitHub Actions
workflow publishes a downloadable copy for review without changing UI code.

## Important limits and next work

- The same strategy cannot reliably pilot *unsupported* triggered abilities,
  spells or combat interactions. Rule functionality must be improved and
  source-verified before judging the pilot's strategic performance.
- Main-phase action ordering uses the common scorer. Specific response-window,
  creature-combat, activation-targeting and sacrifice sequencing selectors
  are already generic rule-based policies but have not yet been fully
  consolidated into that scoring method. Future steps should feed those
  legal action options into the same scorer where possible.
- Turn-by-turn diagnostics must compare *identical* pinned deck revisions,
  seed ranges, opponent scenarios, provisional modes and horizons.
- Opponent players remain bounded abstract policies rather than complete
  piloted decks; outcome rates are modeled exploratory outputs, not validated
  Commander win probabilities.
- The static Deck Lab UI isn't modified by this PR. New `pilot_style`,
  `pilot_signals` and `pilot_decisions` are additive data fields for a
  future UI personality selector and decision-explanation panel.
