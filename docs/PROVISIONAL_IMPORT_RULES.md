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
| Simple mana land or artifact | Single/multiple fixed W/U/B/R/G/C pips, either-or color choices, unrestricted any-color, commander-identity any-color, and **source-paid** `{1}`-to-activate Signet-style outputs; plain enters-tapped handling | Each mode is an independently legal activation. Commander-identity mana is limited by the **actual deck identity** at payment time; no other conditions, side costs or conditional mana are inferred |
| Fixed draw/life spell | Exact Draw N, You draw N and lose M, gain N or each opponent loses N | No additional clauses, opponent priority or unreviewed optional costs |
| Fixed creature-token spell | Exact Create N [tapped] P/T color Type creature tokens | No additional clauses, keyword-bearing tokens or other targets unless explicitly added |

For example, a newly imported land with exactly `{T}: Add {U} or {R}.` gets two different mana options; an artifact with exactly `{1}, {T}: Add {U}{R}.` needs another real source to pay that activation before producing both colors. `{T}: Add one mana of any color in your commander's color identity.` resolves available colors from the selected deck, never from a guessed card name. These additions are **opt-in only** with `provisional_mode="safe"`; reviewed cards still win over import inference.

All physical effects use the existing kernel: actual mana payment, real hand/stack/graveyard movement, zone identity and token object IDs, life ledger changes, and reviewed trigger connections. They are never independent imaginary approximations.

The classifier deliberately rejects unknown layouts, X/hybrid/Phyrexian casting costs, ETB text, alternative and additional casting costs, convoke/delve/improvise, conditional cast restrictions, nontrivial spell clauses, and unsupported multi-action spell recipes. Rejected cards are placed in the manual review queue.

An omitted effect is recorded as an omission, not treated as zero value. A provisional body may still materially understate a deck's power because its printed triggers are inactive.

## Existing-deck priority queue (November 2, 2026)

The six canonical decklists include 448 deck-card entries and 299 distinct card names. These provisional-review priorities count **Oracle-text candidate matches across the six decks** (including a card in both Magnus builds as two deck occurrences), not fully supported cards. Counts overlap across mechanisms. Strategic importance favors actions that unblock early turns or central deck engines; the presence of an existing reviewed handler means the actual unimplemented backlog can be smaller.

| Rank | Cross-deck candidate footprint | Why it matters / next safe extension |
|---|---|---|
| **1 — Mana development** | **114 deck occurrences**, **6 decks** | Delays to first real cast distort everything. **This slice:** choice/any-color/commander-identity mana and funded tap outputs; next audit conditional duals, counters and card-specific extra costs. |
| **2 — Card draw and filtering** | **91 occurrences**, **6 decks** | Mulligans, land development and tutor access depend on card flow. Next exact reviewed Scry/Surveil/loot primitives with a bounded library-choice policy; do not treat a multi-clause spell as a free draw. |
| **3 — Sacrifice/death effects** | **94 occurrences**, **6 decks** | Central to Gisa, Mortarion and Necrons; prioritize shared subscriptions and simultaneous-death/LKI correctness before adding more individual payoffs. |
| **4 — Graveyard movement/recursion** | **79 occurrences**, **6 decks** | Key to undead/artifact recursion and Magnus Breach chains; keep cast-from-zone permissions and replacement/exile rules explicit. |
| **5 — Token creation** | **68 occurrences**, **6 decks** | Fuels sacrifice engines, spell triggers and ramp; recognize only exact token descriptors, ensure token mana/abilities and trigger timing are verified. |
| **6 — Spell triggers/cost reduction** | **41 occurrences**, **6 decks** | Especially important to Magnus's early engine and combos; extend existing shared spell-cast subscriptions and paid cost-modifier pipeline. |
| **7 — Tutors/library search** | **32 occurrences**, **5 decks** | Strong game-plan influence; extend reviewed subtype/CMC predicates and physical destination/shuffle operations without guessing targets. |
| **8 — Targeted removal/interaction** | **23 occurrences**, **6 decks** | Required for realistic opponents; expand legal targets and responses as shared event/priority work proceeds. |

Numbers use printed text patterns from the published six-deck card catalog; they are **planning signals**, not precise unsupported-card counts or evidence of full mechanical execution. Existing exact registrations must retain priority. The next coding slice should measure incremental safe admissions per deck and any observed change in early-turn playable actions before claiming useful coverage progress.

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