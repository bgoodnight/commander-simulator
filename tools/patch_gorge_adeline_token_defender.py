"""Isolated pinned Gorge rule fix: Adeline defender choice includes walkers.

The engine already supports a first-party AskTape defender choice for generic
TokenAttacking True; the named-opponent selector lost the Planeswalker arm.
Constrain the menu to precisely that remembered opponent and planeswalkers
controlled by them, never other opponents or battles.
"""
from __future__ import annotations
import argparse
from pathlib import Path

IMPORT='import (\n\t"strings"\n'
IMPORTED='import (\n\t"slices"\n\t"strings"\n\n\t"github.com/adams-shaun/gorge/engine/decision"\n'
TARGET='''	if objectArm {
		h.Emit(events.Event{Kind: events.Note, Obj: c.Source, Player: c.Controller,
			Text: "TokenAttacking$ " + attack + ": the planeswalker arm is not implemented; the " + noun + " attacks the named player"})
	}
	return true, seats[0], 0
}'''
REPLACEMENT='''	if objectArm {
		// The printed selector names one remembered opponent OR a
		// planeswalker THAT opponent controls. Reuse the existing
		// entering-defender choice mechanism, but never offer unrelated
		// opponents, battles, or a planeswalker of another controller.
		fb := enteringDefender{Player: seats[0]}
		choices := []enteringDefender{fb}
		for _, candidate := range enteringDefenders(h, controller, true) {
			if candidate.Player == fb.Player && candidate.Obj != 0 &&
				slices.Contains(h.Chars(candidate.Obj).Types, "Planeswalker") {
				choices = append(choices, candidate)
			}
		}
		if len(choices) > 1 {
			g := h.Game()
			d := &decision.Decision{Player: controller, Kind: decision.KChoose,
				Source: c.Source, Min: 1, Max: 1,
				ResumeKind: "entering_defender",
				Prompt: "Choose the player or a planeswalker they control for this attacking " + noun}
			for _, candidate := range choices {
				option := decision.Option{Index: len(d.Options), Kind: "player",
					Player: candidate.Player, Label: g.SeatFacingName(candidate.Player)}
				if candidate.Obj != 0 {
					option.Kind = "card"
					option.Obj = candidate.Obj
					option.Label = objName(g, candidate.Obj)
				}
				d.Options = append(d.Options, option)
			}
			if ans, ok := AskTape(h, d); ok && len(ans) == 1 {
				defender := enteringDefender{Player: ans[0].Player, Obj: ans[0].Obj}
				if slices.Contains(choices, defender) {
					return true, defender.Player, defender.Obj
				}
			}
		}
	}
	return true, seats[0], 0
}'''
TEST_OLD='''	if planeNotes != 1 {
		t.Fatalf("%d planeswalker-arm notes, want exactly 1; log=%+v", planeNotes, e.L.Events)
	}'''
TEST_NEW='''	if planeNotes != 0 {
		t.Fatalf("%d unsupported planeswalker-arm notes; the named-opponent choice must be supported", planeNotes)
	}'''

def replace_exact(src,old,new):
    if src.count(old)!=1 or new in src:
        raise ValueError("Pinned Gorge source mismatch; manual review needed")
    return src.replace(old,new,1)

def patch(root):
    source=root/"engine/effects/token.go"
    test=root/"engine/rules/adeline_token_attacking_test.go"
    a=source.read_text()
    b=test.read_text()
    a=replace_exact(a,IMPORT,IMPORTED)
    a=replace_exact(a,TARGET,REPLACEMENT)
    b=replace_exact(b,TEST_OLD,TEST_NEW)
    source.write_text(a)
    test.write_text(b)
    print("Enabled named-opponent player/planeswalker token defender choice")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--gorge",type=Path,required=True)
    patch(p.parse_args().gorge)
