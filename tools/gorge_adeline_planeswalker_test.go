package effects

import (
  "testing"
  "github.com/adams-shaun/gorge/engine/cards"
  "github.com/adams-shaun/gorge/engine/state"
)

// In the Adeline selector, the legal choices are that remembered opponent
// and only the planeswalkers controlled by that same opponent. A fake host
// without a decision tape chooses the printed player fallback.
func TestExperimentalAdelineOffersRememberedOpponentAndTheirWalker(t *testing.T) {
  h,c:=fixtureHostWithTokens(t)
  pw:=enteringDefenderWalker(t,h)
  c.Remembered=[]state.Target{{Player:1,IsPlayer:true}}
  Resolve(h,c,&cards.SA{Kind:"DB",API:"Token",Params:map[string]string{
    "TokenScript":"r_1_1_goblin","TokenTapped":"True",
    "TokenAttacking":"RememberedPlayer & Valid Planeswalker.ControlledBy Remembered",
  }})
  if h.askCount!=1||h.lastAsk==nil{
    t.Fatalf("Adeline ask count %d, decision %+v; want one defender choice",h.askCount,h.lastAsk)
  }
  opts:=h.lastAsk.Options
  if len(opts)!=2||opts[0].Kind!="player"||opts[0].Player!=1||
      opts[1].Kind!="card"||opts[1].Obj!=pw||opts[1].Player!=1{
    t.Fatalf("Adeline options %+v; want remembered player and their walker %d",opts,pw)
  }
  bf:=h.Game().Zone(state.ZBattlefield,c.Controller)
  if len(bf)!=1{t.Fatalf("tokens %v; want exactly one",bf)}
  tok:=h.Game().Obj(bf[0])
  if tok==nil||!tok.IsToken||!tok.Tapped||!tok.IsAttacking||
      tok.Attacking!=1||tok.AttackingBattle!=0{
    t.Fatalf("Adeline fallback token %+v; want tapped attack on player 1",tok)
  }
  if n:=notesContaining(h,"planeswalker arm is not implemented");n!=0{
    t.Fatalf("unexpected unsupported choice notes: %d",n)
  }
}
