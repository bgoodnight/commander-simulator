# Magnus the Red — v1.4 vs v1.5 simulation comparison

**Date:** October 27, 2026  
**Input lists:** `magnus_thousand_sons_v1_4.txt`, `magnus_thousand_sons_v1_5.txt`  
**Code:** `compare_magnus_v14_v15.py`  
**Raw output:** `magnus_v14_v15_comparison.json`

## Method

- 120,000 **paired randomized Commander draw sequences**. Each 99-card deck was shuffled with the same positional permutation, and the four v1.4→v1.5 substitutions occupied their original slots. Seven-card opening hand; one card drawn per turn (multiplayer Commander); no mulligans for raw-draw statistics.
- Another 18,000 **mana-only, no-opponent play sequences** using the identical land-and-ramp package in both versions. The heuristic plays a land each turn and up to one available ramp artifact per turn. It checks blue/red requirements and tapped-land conditions in a simplified way. No other spells are cast in this part. This is not a full gameplay simulation, and cannot estimate win rates.
- Draw-access figures mean the cards were **seen**, not necessarily cast or on the battlefield. The simulation does not model scry, tutors, additional card drawing, Jace/Kitsa looting, Scroll Rack activation, Underworld Breach, tutors, combat, counterspell responses, or opponents. The simplified mana model assumes colors are available from Fellwar Stone / Exotic Orchard when relevant and treats certain dual-land modes optimistically.

## What changed

| Out (v1.4) | In (v1.5) |
|---|---|
| Kitsa, Otterball Elite | Jace, Vryn's Prodigy |
| Stormcatch Mentor | Goblin Electromancer |
| Whispers of the Muse | Sigil Tracer |
| Scroll Rack | Cryptic Gateway |

Both lists contain **35 identical lands and six identical conventional mana rocks**, so mana-only deployment results are identical. All six Tzeentch creatures plus Stormsplitter are preserved.

## Mana development (identical in both versions)

| At turn | Enough mana for Magnus {3}{U}{R} | Enough for Magnus + 1 additional {U} | Enough for Magnus + 2 additional {U} |
|---|---:|---:|---:|
| 4 | 30.17% | 8.84% | 1.47% |
| 5 | 59.99% | 24.71% | 6.98% |
| 6 | 69.74% | 46.69% | 18.71% |
| 7 | 76.89% | 56.92% | 34.37% |

The extra blue comparison means capacity to leave blue mana available **in addition** to paying for Magnus; it does not establish you hold a counterspell. On turn five, 6.17% of mana-only trials had capacity for Magnus + {U} and had seen one of the three listed single-blue counterspells (Swan Song, An Offer You Can't Refuse, Flusterstorm). They are not full-game protection probabilities.

## Paired raw-draw comparisons

| Metric | By turn | v1.4 | v1.5 | Difference |
|---|---:|---:|---:|---:|
| Any low-cost Wizard (actual Wizard types; mana value 3 or less) | 5 | 70.36% | 74.33% | +3.97 pp |
| A low-cost Wizard **and** a conventional mana rock | 5 | 37.66% | 39.84% | +2.18 pp |
| At least one one-mana cantrip (Brainstorm/Ponder/Whispers) | 5 | 32.61% | 23.04% | −9.57 pp |
| At least two draw/filter/tutor cards (broad access category) | 5 | 39.71% | 29.95% | −9.76 pp |
| Any conventional counterspell | 5 | 55.09% | 55.09% | Unchanged |
| Any inexpensive spell-trigger engine | 5 | 55.11% | 55.11% | Unchanged |
| Any buyback spell | 8 | 48.92% | 39.37% | −9.55 pp |
| Any buyback spell and mana-conversion engine | 8 | 18.47% | 14.76% | −3.71 pp |
| Mathemagics and one relevant copy enabler | 8 | 7.08% | 8.28% | +1.20 pp |
| Mathemagics and two relevant copy enablers | 8 | 1.48% | 2.27% | +0.79 pp |

*The broad filtering/tutoring category contains Brainstorm, Ponder, Whispers of the Muse, Frantic Search, Kitsa, Jace, Scroll Rack, Sorcerer Class, Mystical Tutor, Muddle the Mixture, Spellseeker, and Step Through, as applicable to each deck. It treats potential access but not whether or how the abilities are usable. The low-cost Wizard group counts actual Wizard subtype cards, not Young Pyromancer or Third Path Iconoclast.*

## Gateway: promising theme, demanding assembly

By turn eight in v1.5, **5.54%** of raw draw sequences had seen Cryptic Gateway **and** one of Lord of Change, Mutalith Vortex Beast, or Heralds of Tzeentch. Just **1.35%** had also seen Arcane Adaptation or Maskwood Nexus. These are *card co-access rates*, not successful Gateway activations. Activation also requires a resolved five-mana artifact, the creature in hand, and two untapped creatures with a compatible type; two Demons could work without conversion. This suggests it is an occasional thematic payoff, not a reliable early-mana solution.

## Interpretation

1. **No change to casting Magnus on time:** both versions have the same mana base and rocks. This is still the main constraint.
2. **v1.5 offers modestly more Wizard utility and copying:** Sigil Tracer provides an additional real Wizard and a repeatable copy activation; Jace retains Kitsa's looting role but exchanges the copy ability for spell recursion after transformation.
3. **v1.5 materially weakens early card flow:** removing Whispers of the Muse and Scroll Rack changes an early one-mana instant and a two-mana library-filtering artifact into a three-mana creature and a five-mana artifact. Raw access drops; actual difference could be larger or smaller depending on ability use.
4. **More thematic, slightly more setup-heavy:** Cryptic Gateway offers the demon-summoning fantasy, but needs other cards and five mana.
5. **Control count unchanged:** first-order counterspell access does not improve. Protection *after casting Magnus* remains harder than simply casting Magnus.

## Recommendation before further changes

Keep v1.5 as the thematic foundation, but add back one or two low-cost card-selection/interaction spells in future iterations without cutting Stormsplitter, Sigil Tracer, Cryptic Gateway, Magnus, or the Tzeentch contingent. Consider 36 lands or an additional cheap ramp source only after modeling what is removed. In particular, do not mistake identical ramp for an improvement due to adding more Wizards.
