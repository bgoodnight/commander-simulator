package main

import (
  "os"
  "testing"

  "github.com/adams-shaun/gorge/engine/cards"
  "github.com/adams-shaun/gorge/testkit/testutil"
)

func TestPinnedBaralCorpusOverlay(t *testing.T) {
  corpus:=os.Getenv("GORGE_TEST_CORPUS")
  if corpus=="" {t.Fatal("GORGE_TEST_CORPUS must identify pinned simulation corpus")}
  reg,err:=testutil.OpenCorpusRegistry(corpus)
  if err!=nil {t.Fatal(err)}
  baral,ok:=reg.Lookup("Baral, Chief of Compliance")
  if !ok {t.Fatal("Baral missing")}
  if len(baral.Faces)!=1 {t.Fatalf("unexpected faces: %d",len(baral.Faces))}
  before:=len(baral.Faces[0].Statics)
  if before!=0 {t.Fatalf("pinned Baral now has %d statics: update overlay instead",before)}
  name:=baral.Faces[0].Name
  oracle:=baral.Faces[0].Oracle
  if err:=repairBaralCorpus(reg);err!=nil {t.Fatal(err)}
  if baral.Faces[0].Name!=name||baral.Faces[0].Oracle!=oracle {
    t.Fatal("overlay changed original card identity or Oracle")
  }
  if len(baral.Faces[0].Statics)!=before+1 {t.Fatal("unexpected number of statics")}
  st:=baral.Faces[0].Statics[before]
  if st.ModeKind()!=cards.StaticReduceCost ||
     st.ParamStr(cards.PKValidCard)!="Instant,Sorcery" ||
     st.ParamStr(cards.PKAmount)!="1" ||
     st.ParamStr(cards.PKActivator)!="You" ||
     st.ParamStr(cards.PKType)!="Spell" {
       t.Fatalf("Baral reducer mismatch: %+v",st)
  }
  if err:=repairBaralCorpus(reg);err==nil {
    t.Fatal("double-install should fail, never stack duplicate discounts")
  }
}
