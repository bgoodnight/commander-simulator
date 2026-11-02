# Generic partial rules for newly imported Commander decks

## Goal

New cards should immediately receive a conservative, useful simulation profile where their pinned card data supports one. An inferred profile is always **provisional**, not an exact implementation or a replacement for explicit, source-reviewed rules.

## Import workflow

After obtaining a complete pinned Scryfall card snapshot, run:

```sh
python tools/audit_provisional_import.py --snapshot simulator/card_data/NEW_DECK_m1_scryfall.json --output import-review.json
```

The import report provides card name, Oracle identity, provisional category, fidelity, missing abilities and a queue of cards requiring review. The audit accepts a new snapshot path even before that deck is registered as a historical fixture. It does not modify source cards, game state, or historical results.

To run a registered deck using the fallback (the original default remains off for historical compatibility):

```sh
python -m commander_sim.early_game_runner --deck wretched_ranks --turns 6 --seed 2 --provisional-mode safe
```

Host callers can pass `provisional_mode="safe"` to `run_bounded_early_game`. The flag propagates into the shared physical mana planner and card admission checks. Manually reviewed card implementations always take precedence.

## Supported generic import profiles

| Category | Recognized subeffect | Important caveats |
|---|---|---|
| Ordinary creature bodies | Legal fixed-cost cast into the physical battlefield with printed base power, toughness, type and keyword metadata | No inferred ETB, death, activated or complex static effects; combat keywords only as well supported by kernel |
| Artifact bodies | Physical battlefield presence, sacrifice and artifact-count eligibility | Unknown abilities do nothing |
| Simple mana land or artifact | Tap produces the exact printed W/U/B/R/G/C pips, with plain enters-tapped handling | No inferred conditions, mana spending restrictions or unusual activation costs |
| Fixed draw/life spell | Exact Draw N, You draw N and lose M, gain N or each opponent loses N | No additional clauses, opponent priority or unreviewed optional costs |
| Fixed creature-token spell | Exact Create N [tapped] P/T color Type creature tokens | No additional clauses, keyword-bearing tokens or other targets unless explicitly added |

All physical effects use the existing kernel: actual mana payment, real hand/stack/graveyard movement, zone identity and token object IDs, life ledger changes, and reviewed trigger connections. They are never independent imaginary approximations.

The classifier deliberately rejects unknown layouts, X/hybrid/Phyrexian casting costs, ETB text, alternative and additional casting costs, convoke/delve/improvise, conditional cast restrictions, nontrivial spell clauses, and unsupported multi-action spell recipes. Rejected cards are placed in the manual review queue.

An omitted effect is recorded as an omission, not treated as zero value. A provisional body may still materially understate a deck's power because its printed triggers are inactive.

## Scaling rule development

1. Add or refine a typed parameterized primitive when multiple cards require a new behavior.
2. Extend the generic recognizer only if the pattern is unambiguous and its required costs/targets can be honored.
3. Include a positive test, one or more dangerous near-miss rejection tests, and a physical zone/mana regression.
4. For exceptional cards, use pinned Oracle-specific descriptors while reusing the underlying primitive.
5. Promote the profile from provisional to reviewed only after gameplay tests and narrative review, retaining a list of unsupported interactions.

## Quality checks

- `tests/test_provisional_import.py` checks body and keyword admission, mandatory ETB rejection, generic mana, source-pinned source payment, simple spells, token spells, four Commander deck families, and baseline isolation.
- `.github/workflows/provisional-import-audit.yml` audits all registered decks and executes a short physical smoke run with provisional mode enabled.
- `run_all_tests.py` continues to validate the existing reviewed and historical behavior.

The CLI is a working backend entrypoint. Showing the report automatically on the UI's import page is a separate integration task, best coordinated with the chat currently working on deck visualization and frontend changes.