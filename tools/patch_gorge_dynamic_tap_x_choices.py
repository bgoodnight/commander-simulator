"""Experimental pinned-Gorge correction for dynamic tap-X activation choices.

Keep rules/target legality intact. Withhold abilities whose tap-count-X has
no target-feasible count, choose a target-feasible tap count at announcement,
and prefer the smallest positive payable X for combined mana-X/tap-X abilities
rather than the largest (which can consume the needed mana-source artifacts).

This is a PILOT/offer policy experiment; full-cost choice search remains future work.
"""
from __future__ import annotations
import argparse
from pathlib import Path

def once(s: str, old: str, new: str) -> str:
    if s.count(old) != 1 or new in s:
        raise ValueError("Pinned Gorge dynamic-X source mismatch")
    return s.replace(old, new, 1)

def patch(root: Path) -> None:
    legal = root / "engine/rules/legal_targets.go"
    s = legal.read_text()
    s = once(s, '\t"github.com/adams-shaun/gorge/engine/effects"\n',
             '\t"github.com/adams-shaun/gorge/engine/effects"\n\t"github.com/adams-shaun/gorge/engine/rules/pay"\n')
    old = '''\tif !targetsReadXPending(ab) {
\t\t// xPending is never read for this shape (targetsReadXPending).
\t\treturn e.targetsAvailable(p, id, excludeSelf, ab, false)
\t}
\tcost := e.abilityCompiledCost(ab).Cost
'''
    new = '''\tcost := e.abilityCompiledCost(ab).Cost
\t// A tapXType<X/...> that announces X by tapping permanents must
\t// have SOME target-feasible count before it is offered. The generic
\t// pending-X shortcut can otherwise offer Aryel every priority window
\t// even when no choice of X has a legal target. This is a pure-read
\t// offer census, never an activation or target commitment.
\tif cost.X == 0 {
\t\tfor _, part := range cost.TapPermanent {
\t\t\tif part.Dyn != "X" {
\t\t\t\tcontinue
\t\t\t}
\t\t\tids := pay.TapCostCandidates(asPayer(e), p, id, part)
\t\t\tpossible := len(ids)
\t\t\tif cost.Tap {
\t\t\t\tfor _, oid := range ids {
\t\t\t\t\tif oid == id {
\t\t\t\t\t\tpossible--
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t\tprevious := e.cast
\t\t\tfound := false
\t\t\tfor x := 0; x <= possible; x++ {
\t\t\t\te.cast = &pendingCast{player: p, card: id, ability: -1, x: int32(x)}
\t\t\t\tif e.targetSAAvailable(p, id, excludeSelf, ab, int32(x), false) {
\t\t\t\t\tfound = true
\t\t\t\t\tbreak
\t\t\t\t}
\t\t\t}
\t\t\te.cast = previous
\t\t\tif !found {
\t\t\t\treturn false
\t\t\t}
\t\t\tbreak
\t\t}
\t}
\tif !targetsReadXPending(ab) {
\t\t// xPending is never read for this shape (targetsReadXPending).
\t\treturn e.targetsAvailable(p, id, excludeSelf, ab, false)
\t}
'''
    s=once(s,old,new)
    ask=root / "engine/rules/cast_asks.go"
    a=ask.read_text()
    old='''\t\t\tmin := int32(1)
\t\t\tif part.Dyn == "X" {
\t\t\t\tmin = 0
\t\t\t}
\t\t\td := &decision.Decision{Player: pc.player, Kind: decision.KChoose, Min: int(min), Max: len(candidates),
'''
    new='''\t\t\tmin := int32(1)
\t\t\tif part.Dyn == "X" {
\t\t\t\tmin = 0
\t\t\t\t// The bot ordinarily taps at least one helper even for Min=0.
\t\t\t\t// For target-bound X, that choice can be invalid (Aryel):
\t\t\t\t// find the first legal X rather than repeatedly announcing 1.
\t\t\t\tif sa := e.pcAbility(pc); sa != nil && effects.TargetsOf(sa).Targeted() {
\t\t\t\t\tfound := false
\t\t\t\t\tfor x := 0; x <= len(candidates); x++ {
\t\t\t\t\t\tif e.targetsAnnounceableAt(pc, int32(x)) {
\t\t\t\t\t\t\tmin = int32(x)
\t\t\t\t\t\t\tfound = true
\t\t\t\t\t\t\tbreak
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t\tif !found {
\t\t\t\t\t\te.abortCast(pc, "tap X has no feasible legal target; cast aborted", true)
\t\t\t\t\t\treturn true
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t\td := &decision.Decision{Player: pc.player, Kind: decision.KChoose, Min: int(min), Max: len(candidates),
'''
    a=once(a,old,new)
    xfile=root/"engine/rules/cast_subcounter.go"
    x=xfile.read_text()
    old='''\td := &decision.Decision{Player: pc.player, Kind: decision.KChoose, Min: 1, Max: 1,
\t\tPrompt: "Choose a value for X", Source: pc.card}
\tfor _, x := range vals {
'''
    # This exact anchor occurs in the normal xAsk final menu and may also
    # appear in the Shoal branch. Require precisely one final-position match.
    new='''\tprompt := "Choose a value for X"
\tif pc.isAbility() && pc.cost.X > 0 {
\t\tfor _, part := range pc.cost.TapPermanent {
\t\t\tif part.Dyn == "X" {
\t\t\t\tprompt = "Choose a value for X (pay X and tap X permanents)"
\t\t\t\tbreak
\t\t\t}
\t\t}
\t}
\td := &decision.Decision{Player: pc.player, Kind: decision.KChoose, Min: 1, Max: 1,
\t\tPrompt: prompt, Source: pc.card}
\tfor _, x := range vals {
'''
    x=once(x,old,new)
    policy=root/"bots/botpolicy/policy.go"
    p=policy.read_text()
    p=once(p,'''\\t\\tcase "x":\\n\\t\\t\\tin.Choices = []int{d.Options[len(d.Options)-1].Index} // the most it can pay for\\n'''.replace('\\t','\t').replace('\\n','\n'),
      '''\t\tcase "x":
\t\t\tif d.Prompt == "Choose a value for X (pay X and tap X permanents)" {
\t\t\t\t// Conservatively retain available artifacts/mana sources for
\t\t\t\t// the payment window. Prefer the lowest positive feasible X.
\t\t\t\tbest := 0
\t\t\t\tfor i, o := range d.Options {
\t\t\t\t\tif o.Amount > 0 {
\t\t\t\t\t\tbest = i
\t\t\t\t\t\tbreak
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tin.Choices = []int{d.Options[best].Index}
\t\t\t} else {
\t\t\t\tin.Choices = []int{d.Options[len(d.Options)-1].Index}
\t\t\t}
''')
    # Validate every source anchor before writing any file.
    legal.write_text(s)
    ask.write_text(a)
    xfile.write_text(x)
    policy.write_text(p)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--gorge", type=Path, required=True)
    patch(ap.parse_args().gorge)
