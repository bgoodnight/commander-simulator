package rules

import (
  "testing"
  "strings"

  "github.com/adams-shaun/gorge/engine/decision"
  "github.com/adams-shaun/gorge/engine/events"
  "github.com/adams-shaun/gorge/engine/state"
)

// Diagnostic under the exact pinned Gorge rules version, with the real
// Mortarion corpus card; no fabricated script or game-state projections.
func TestMortarionGuaranteedLifeLossAndMana(t *testing.T) {
  e := newSeats(t, 2)
  // Enter the first main phase before placing Mortarion, so the fixture
  // cannot encounter an unrelated turn-0 optional trigger.
  driveToStep(t,e,1,0,state.StepMain1)
  card := corpusCard(t, "Mortarion, Daemon Primarch")
  id := onBoardCard(t,e,0,card)
  if e.G.Obj(id).Zone != state.ZBattlefield {
    t.Fatal("Mortarion not present")
  }
  e.emit(events.Event{Kind: events.Damage, Player: 0, Amount: 3})
  if loss:=e.LifeLostThisTurn(0); loss!=3 {
    t.Fatalf("life lost %d not 3",loss)
  }
  driveToStep(t,e,1,0,state.StepEnd)
  // Mana added at end step: pools empty on step transitions.
  e.G.Players[0].Pool[state.MC] = 3
  t.Logf("PRECONDITION life=%d loss=%d mana=%d",e.G.Players[0].Life,
    e.LifeLostThisTurn(0),e.G.Players[0].Pool.Total())
  t.Logf("AT_ENDSTEP turn=%d phase=%v stack=%d pending=%v",e.G.Turn,
    e.G.Step,len(e.G.Stack),e.Pending())
  sourceEventStart := len(e.L.Events)
  chosenX:=false
  paid:=false
  for i:=0;i<80;i++ {
    d:=e.Pending()
    if d==nil {
      e.Advance()
      d=e.Pending()
      if d==nil && len(e.G.Stack)==0 {break}
      if d==nil {continue}
    }
    if d.Kind==decision.KPriority {
      if paid && len(e.G.Stack)==0 {break}
      passPriorityOnce(t,e)
      continue
    }
    if d.Kind!=decision.KChoose {
      t.Fatalf("unexpected decision kind %v: %+v",d.Kind,d)
    }
    pick:=-1
    for _,opt:=range d.Options {
      switch opt.Kind {
      case "trigger_cost_x":
        if opt.Amount==3 {pick=opt.Index;chosenX=true}
      case "trigger_cost_pay":
        pick=opt.Index;paid=true
      }
    }
    if pick<0 {
      t.Fatalf("unexpected choice options: %+v",d.Options)
    }
    if err:=e.Submit(decision.Intent{Seq:d.Seq,Player:d.Player,
      Choices:[]int{pick}});err!=nil {t.Fatalf("choice %d: %v",pick,err)}
    t.Logf("CHOSEN kind=%s index=%d",d.Options[pick].Kind,pick)
  }
  if !chosenX || !paid {t.Fatalf("Did not choose X=3 and Pay: X=%v, pay=%v",chosenX,paid)}
  tokens:=0
  for _,o:=range e.G.Objs {
    if !o.IsToken {continue}
    if o.Face()!=nil && strings.Contains(strings.ToLower(o.Face().Name),"astartes") {tokens++}
    if o.Face()!=nil && len(o.Face().Name)>0 {
      t.Logf("TOKEN name=%q zone=%v owner=%v",o.Face().Name,o.Zone,o.Owner)
    }
  }
  for _,event:=range e.L.Events[sourceEventStart:] {
    t.Logf("POST_EVENT kind=%v obj=%d player=%d amount=%d text=%q to=%v",
      event.Kind,event.Obj,event.Player,event.Amount,event.Text,event.To)
  }
  t.Logf("RESULT token_count=%d life=%d loss=%d mana=%d",
    tokens,e.G.Players[0].Life,e.LifeLostThisTurn(0),e.G.Players[0].Pool.Total())
  if tokens!=3 {t.Fatalf("Created %d Astartes tokens, expected 3 after paying X=3",tokens)}
}
