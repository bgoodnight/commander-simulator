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
  existing:=0
  for _,st:=range baral.Faces[0].Statics {
    if st.ModeKind()==cards.StaticReduceCost {existing++}
  }
  if existing>1 {t.Fatalf("unexpected %d existing reducers",existing)}
  name:=baral.Faces[0].Name
  oracle:=baral.Faces[0].Oracle
  if err:=repairBaralCorpus(reg);err!=nil {t.Fatal(err)}
  if baral.Faces[0].Name!=name||baral.Faces[0].Oracle!=oracle {
    t.Fatal("overlay changed original card identity or Oracle")
  }
  want:=before
  if existing==0 {want++}
  if len(baral.Faces[0].Statics)!=want {t.Fatal("unexpected number of statics")}
  var st cards.Static
  for _,candidate:=range baral.Faces[0].Statics {
    if candidate.ModeKind()==cards.StaticReduceCost {st=candidate}
  }
  if st.ModeKind()!=cards.StaticReduceCost ||
     st.ParamStr(cards.PKValidCard)!="Instant,Sorcery" ||
     st.ParamStr(cards.PKAmount)!="1" ||
     st.ParamStr(cards.PKActivator)!="You" ||
     st.ParamStr(cards.PKType)!="Spell" {
       t.Fatalf("Baral reducer mismatch: %+v",st)
  }
  if err:=repairBaralCorpus(reg);err!=nil {t.Fatalf("idempotent patch failed: %v",err)}
  if len(baral.Faces[0].Statics)!=want {t.Fatal("idempotent overlay duplicated discount")}
  t.Logf("Baral verified: preexisting_reducer=%t statics=%d",existing==1,want)
}
