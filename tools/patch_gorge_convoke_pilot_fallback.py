"""Experimental generic Convoke pilot correction for stranded casts.

If the current floating pool cannot pay the remaining cost even after all
non-mana-producing helpers are tapped, the old bot returns an empty answer.
But tapped/untapped mana sources may still be available in the upcoming
mana window: current pool is not a complete potential-mana census.
Return the legal helper contributions rather than zero so the later engine
payment-stranded check can decide affordability. This changes pilot policy
only, not MTG cost rules, and requires seeded behavioral review.
"""
from pathlib import Path
import argparse

OLD='''	if !b.manaReaches(pips, generic) {
		return nil
	}
	var picks []int
'''
NEW='''	if !b.manaReaches(pips, generic) {
		// The floated pool is only part of what the 601.2g mana window
		// can generate. If the non-mana helpers alone cannot finish the
		// payment, keep those contributions: the engine will still check
		// real affordability after the remaining sources are used. The
		// old nil skipped all helpers and repeatedly reversed Convoke
		// spells that could use both creatures and lands.
		picks := make([]int, 0, len(helpers))
		for _, helper := range helpers {
			picks = append(picks, helper.option)
		}
		return picks
	}
	var picks []int
'''

def patch(path):
    s=path.read_text()
    if s.count(OLD)!=1 or NEW in s:
        raise ValueError("Pinned source anchor changed; refuse unreviewed pilot patch")
    path.write_text(s.replace(OLD,NEW,1))
    print("Applied experimental nonzero Convoke helper fallback to bot policy")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--policy",type=Path,required=True)
    patch(p.parse_args().policy)
