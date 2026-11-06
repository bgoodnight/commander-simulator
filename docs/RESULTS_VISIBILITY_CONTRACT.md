# Results visibility contract (staging design)

## Separation of responsibilities

- **R2 / Worker** decides if a viewer may access a snapshot and whether an approved cohort is current. Do not trust a frontend toggle, a query parameter, or local state as authorization.
- **Published snapshot** identifies a deck revision and cohort version. Its summaries and replay references must agree with those identifiers.
- **Frontend** has one readiness state for the selected deck: `loading`, `unavailable`, or `ready`. It never infers that a private snapshot is public.
- **Optional metrics** are displayed only when supported by recorded data. Incomplete insight coverage never hides the entire Key Insights panel or invalidates available outcomes and replays.

## Rendering rules

| Data state | Results | Key Insights | Turn Reviewer |
| --- | --- | --- | --- |
| No authorized approved snapshot | One "R2 results not available" message | Hidden | Hidden |
| Approved snapshot, card insights unavailable | Summary / valid metrics | Visible with explicit unavailable explanation | Valid recorded games |
| Approved snapshot, recorded game evidence | Summary / valid metrics | Source-backed ranked cards labeled by observed-game coverage; use verified full-cohort rankings when published | Valid recorded games |
| Query error or deck mismatch | One unavailable/error message | Hidden | Hidden |

Loading is transient and clears stale deck-specific panels. Partial data never creates invented rankings. A full-cohort report is acceptable only if its game totals, coverage and (for materialized reports) cohort version match the selected snapshot.

## Future visibility toggle

A future `public/private` toggle should change **server-enforced access to a snapshot** (or create/delete a public immutable snapshot), not alter these UI conditions. The Worker must enforce read and simulation permissions independently; GitHub Pages JavaScript remains public. Private native recordings, credentials and unapproved cohorts must not be exposed through public assets.

The R2 source may contain omniscient simulated game state for authorized viewers; this does **not** imply public access to every recording. The existing separate replay privacy formatting is out of scope for this change.

## Shared section visibility

When one approved result is ready, **Results**, **Key Insights**, and **Turn Reviewer** all remain visible. A missing card-insight report is not a separate permission switch: the browser displays the actual card observations from the approved Worker batch, clearly stating their denominator, or an unavailable explanation when none exist. Card findings must never include opposing players' cards or claim whole-cohort coverage without complete evidence. Authorization and deck/cohort identity are still enforced at the data boundary.
