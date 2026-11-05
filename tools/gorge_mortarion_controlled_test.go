package rules

import (
  "fmt"
  "testing"

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
  addMana(t,e,0,"CCC")
  t.Logf("PRECONDITION life=%d loss=%d mana=%d",e.G.Players[0].Life,
    e.LifeLostThisTurn(0),e.G.Players[0].Pool.Total())
  t.Logf("AT_ENDSTEP turn=%d phase=%v stack=%d pending=%v",e.G.Turn,
    e.G.Step,len(e.G.Stack),e.Pending())
  for i:=0;i<120;i++ {
    d:=e.Pending()
    if d==nil {
      e.Advance()
      d=e.Pending()
      if d==nil && len(e.G.Stack)==0 {break}
      if d==nil {continue}
    }
    if d.Kind==decision.KPriority {
      passPriorityOnce(t,e)
      continue
    }
    t.Logf("DECISION step=%d kind=%v player=%d options=%+v",
      i,d.Kind,d.Player,d.Options)
    pick:=0
    // Intentionally choose affirmative/pay and maximum offered X;
    // log the options to make the choice auditable.
    for _,opt:=range d.Options {
      if opt.Index>pick {pick=opt.Index}
    }
    if err:=e.Submit(decision.Intent{Seq:d.Seq,Player:d.Player,
      Choices:[]int{pick}});err!=nil {t.Fatalf("choice %d: %v",pick,err)}
    if i>100 {t.Fatalf("too many pending decisions")}
  }
  tokens:=0
  for _,o:=range e.G.Objs {
    if !o.IsToken {continue}
    if o.Face()!=nil && o.Face().Name=="Astartes Warrior Token" {tokens++}
    if o.Face()!=nil && len(o.Face().Name)>0 {
      t.Logf("TOKEN name=%q zone=%v owner=%v",o.Face().Name,o.Zone,o.Owner)
    }
  }
  for _,ev:=range e.L.Events {
    if ev.Kind==events.Note && len(ev.Text)>0 {
      fmt.Printf("SOURCE_NOTE %s\n",ev.Text)
    }
  }
  t.Logf("RESULT token_count=%d life=%d loss=%d mana=%d",
    tokens,e.G.Players[0].Life,e.LifeLostThisTurn(0),e.G.Players[0].Pool.Total())
  if tokens==0 {t.Fatal("No Astartes Warrior tokens created despite life lost and mana available")}
}
