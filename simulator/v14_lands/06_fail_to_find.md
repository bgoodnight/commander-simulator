# Failing to find still shuffles and does not refund the sacrifice

Forced conserved setup; real deck cards and source payments.

The explicit search policy chose no basic, which is legal for the hidden-zone search. Passage remained in the graveyard, no land entered, and the library was shuffled. The activation was not a spell or a draw.

## Branch 1

```text
FORCED DIAGNOSTIC: conserved actual cards, declared battlefield/hand setup; not a natural opening.
    LAND ENTERS P0: Fabled Passage #469; tapped=False; life_paid=0; cause=land_play.
    STACK +1 [activated] P0: Fabled Passage: fabled_passage_fetch.
    BASIC FETCH P0: source #469; fetched #None; lands=0; untapped=False; shuffled.
```
