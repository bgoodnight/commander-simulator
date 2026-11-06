package effects

import (
  "testing"
  "github.com/adams-shaun/gorge/engine/cards"
)

// Explicit AnyNumber is NOT a one-card ChangeNum; it permits a zero-or-more
// public-origin pick subject to the existing WithTotalCMC budget.
func TestExperimentalTechnomancerAnyNumberCompiled(t *testing.T) {
  sa:=&cards.SA{API:"ChangeZone",Params:map[string]string{
    "Origin":"Graveyard","Destination":"Battlefield","Hidden":"True",
    "ChangeType":"Artifact.Creature","WithTotalCMC":"6","AnyNumber":"True",
  }}
  p:=ChangeZoneOf(sa)
  if !p.AnyNumber || p.ChangeNum.Present || p.WithTotalCMC.Text!="6" {
    t.Fatalf("Technomancer cardinality and budget lost: %+v",p)
  }
  for _,key:=range p.Unread {
    if key=="AnyNumber" {t.Fatal("AnyNumber is still an ignored ChangeZone parameter")}
  }
  exact:=&cards.SA{API:"ChangeZone",Params:map[string]string{
    "Origin":"Graveyard","Destination":"Battlefield","Hidden":"True",
    "ChangeNum":"1","AnyNumber":"True",
  }}
  q:=ChangeZoneOf(exact)
  if !q.AnyNumber || q.ChangeNum.Text!="1" {
    t.Fatalf("Explicit ChangeNum must take precedence: %+v",q)
  }
  absent:=&cards.SA{API:"ChangeZone",Params:map[string]string{
    "Origin":"Graveyard","Destination":"Battlefield","Hidden":"True",
  }}
  if ChangeZoneOf(absent).AnyNumber {
    t.Fatal("Cards without AnyNumber must retain their existing one-card default")
  }
}
