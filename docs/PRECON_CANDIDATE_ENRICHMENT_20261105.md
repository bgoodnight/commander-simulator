# Commander precon candidate enrichment — 2026-11-05

## Scope

This read-only enrichment covers the precon-only candidate library in
`data/gorge_stock_precon_candidates_v1.json`. Source decklist metadata
originates from pinned `taw/magic-preconstructed-decks-data` at
`1b5a451d9146812160e27aee7c8a1e37f1395839`. The enrichment tool
`tools/enrich_gorge_candidate_precons.py` resolves card properties against a
timestamped Scryfall Oracle bulk file. The generated structured dataset and
source fingerprint are preserved as a GitHub Actions artifact rather than
committed megabytes of derived card data.

Successful run:
https://github.com/bgoodnight/commander-simulator/actions/runs/42035137117

## Verified inventory

- 175 catalog product entries.
- 171 released by November 5, 2026; four November 13 products excluded.
- 159 unique playable 100-card lists (12 identical duplicates/variants).
- All 159 named commanders resolved to Oracle color identity.
- 141 / 159 distinct decklists have all 100 card names matched exactly or
  via unambiguous face aliases.
- Seven distinct unresolved card names remain across the released catalog:
  `Savage Lands` (12 occurrences), `Unquenchable Fury` (1), and five
  specialized `(Prepared)` names (one occurrence apiece). The first two
  require source/printing disambiguation, not guessed nearest-name matches.

**Commander color-count distribution** on 159 unique lists:

| Colors | Decklists |
|---|---:|
| Colorless | 1 |
| Mono-color | 13 |
| Two-color | 54 |
| Three-color | 75 |
| Four-color | 7 |
| Five-color | 9 |

The wide color-combination coverage is a useful first input to the opponent
panel design; four-color and colorless strata are comparatively sparse.

## Enrichment dimensions

Generated artifact fields include:
- Original full decklist, set, release, and immutable source identifiers.
- Per-card Oracle identity, card types, mana value, keywords and color identity,
  with resolved/unresolved coverage explicitly reported.
- Per-deck commander color identity, color count, average nonland mana value,
  counts of card types and exploratory Oracle-text-derived mechanics.
- Compact functional proxies for draw, ramp, artifact mana, removal,
  counterspells, token creation, graveyard use, reanimation, tutors,
  sacrifices and life loss.
- Duplicate deck variant status, cards-per-list coverage, and source hash.
- `primary_archetype=null`, `archetype_status=requires_curated_review`,
  and `gorge_rules_compatibility=not_tested`. No candidate is admitted to
  the active Gorge opponent pool.

## Analysis guidance

1. **Use counts, not binary-any flags for common functions.** In the first
   pass all 159 decklists had at least one proxy matching draw, mana rock,
   removal, ramp, sacrifice, and token creation. These near-universal binary
   presence indicators are not useful for selection; numeric densities,
   timings, and more granular roles may distinguish decks.
2. **Do not treat text patterns as validated card-role annotations.**
   Search/ramp/removal proxies may include false positives and false negatives,
   and keyword lists are not exhaustive measures of functional support.
3. **Use only released, distinct decks for opponent coverage distributions.**
   The catalog retains variants and not-yet-released lists for provenance.
4. **Prioritize reviewed strategic classification and card-level metadata
   resolution next.** A selection algorithm should maximize coverage of
   color *and* mechanics, not composition novelty alone; reserve an archetype
   holdout set for testing generalization.
5. **Keep Gorge certification separate.** Successful parsing and successful
   game completion are necessary but insufficient: verify signature mechanic
   execution and pilot behavior before classifying a deck as a qualified
   benchmark opponent.
6. **Do not compare cohorts without recording deck, engine, pilot, metadata,
   Oracle-snapshot and opponent-selection versions.**

The generated full-enrichment artifact is available for 21 days from the run.
Before using these covariates in long-running modeling pipelines, publish an
immutable compact dataset in the versioned analytics store/R2 with its source
checksums, rather than assuming Actions artifacts are permanent.


## Quantitative certification-priority panel

The next stage is implemented in `tools/select_gorge_precon_panel.py` and
executed in the same read-only Oracle enrichment workflow. Successful run:
https://github.com/bgoodnight/commander-simulator/actions/runs/42036620107

The workflow generates `candidate-panel-60.json` alongside
`full-enrichment.json` and `summary.json`. These are attached to the
`commander-precon-oracle-enrichment` artifact. All 13 targeted unit tests
passed, and all dataset generation steps passed.

- **159 distinct released candidates** evaluated.
- **60 decks** provisionally selected for subsequent rules and pilot review.
- **32 observed commander color identities** all appear in the panel; rare
  identities have a minimum one-deck anchor where available.
- **18 unique decklists** have at least one unresolved card name. These
  remain staged with explicit completeness flags, not guessed substitutes.
- Numeric candidate/panel summaries include min, p10, median, p90, maximum,
  and positive-deck counts for 17 card-type and functional indicators plus
  average nonland mana value.
- Selection then applies a greedy max-min rank-normalized feature-distance
  criterion with modest adjustments for color, era and card-name completeness.
  This shortlist is **only a review priority ordering**, not a guarantee that
  the decks express distinct true gameplay archetypes.

The panel is designed for broad *observed composition* coverage, not
representative estimates of population frequencies. The active benchmark
design must record the panel selection mechanism and may need sampling
weights depending on the target estimand. We should add reviewed commander/
strategy archetypes and real Gorge rules capability before treating the
panel as a validated simulation opponent pool.
