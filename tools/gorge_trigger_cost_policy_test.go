package botpolicy

import (
    "testing"
    "github.com/adams-shaun/gorge/engine/decision"
)

func TestTriggerCostXAndPayPilot(t *testing.T) {
    // Engine offers X=0..3 in ascending order. Selecting X=0 turns the
    // token-producing trigger into a no-op.
    d:=decision.Decision{Seq:1,Player:0,Kind:decision.KChoose,Min:1,Max:1,
       Options:[]decision.Option{
         {Index:0,Kind:"trigger_cost_x",Amount:0},
         {Index:1,Kind:"trigger_cost_x",Amount:1},
         {Index:2,Kind:"trigger_cost_x",Amount:2},
         {Index:3,Kind:"trigger_cost_x",Amount:3},
       }}
    answer:=Decide(Board{},&d,rng(19))
    if err:=d.Validate(answer);err!=nil {t.Fatal(err)}
    if len(answer.Choices)!=1||answer.Choices[0]!=3 {
       t.Fatalf("X policy chose %v, want X=3",answer.Choices)
    }
    pay:=decision.Decision{Seq:2,Player:0,Kind:decision.KChoose,Min:1,Max:1,
      Options:[]decision.Option{
        {Index:0,Kind:"trigger_cost_decline"},
        {Index:1,Kind:"trigger_cost_pay"},
      }}
    accepted:=Decide(Board{},&pay,rng(19))
    if err:=pay.Validate(accepted);err!=nil {t.Fatal(err)}
    if len(accepted.Choices)!=1||accepted.Choices[0]!=1 {
        t.Fatalf("trigger cost choice %v, want Pay",accepted.Choices)
    }
}
