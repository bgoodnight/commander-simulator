package rules

import (
 "testing"
 "github.com/adams-shaun/gorge/engine/state"
)

// Card-definition equivalence check for the compiled Baral reduction confirmed
// by the registry test. The engine must reduce instant and sorcery generic
// costs only, without reducing colored mana or creature spells.
const baralPaymentProbeSrc = "Name:Baral, Chief of Compliance\nManaCost:1 U\nTypes:Legendary Creature Human Wizard\nPT:1/3\n" +
 "S:Mode$ ReduceCost | ValidCard$ Instant,Sorcery | Type$ Spell | Activator$ You | Amount$ 1\n" +
 "Oracle:Instant and sorcery spells you cast cost {1} less to cast.\n"
const baralInstantProbe = "Name:Baral Instant Probe\nManaCost:2 U\nTypes:Instant\nOracle:Test.\n"
const baralSorceryProbe = "Name:Baral Sorcery Probe\nManaCost:2 U\nTypes:Sorcery\nOracle:Test.\n"
const baralCreatureProbe = "Name:Baral Creature Probe\nManaCost:2 U\nTypes:Creature Human Wizard\nPT:1/1\nOracle:Test.\n"

func TestBaralGenericSpellDiscountInRules(t *testing.T) {
 e,cfg,spell:=newFixtureDeck(t,90127,baralInstantProbe,baralPaymentProbeSrc,baralSorceryProbe,baralCreatureProbe)
 if got:=reduceOf(t,e,0,spell);got!=0 {t.Fatalf("Baral absent: discount=%d",got)}
 putCreature(t,e,0,baralPaymentProbeSrc)
 if got:=reduceOf(t,e,0,spell);got!=1 {t.Fatalf("Baral instant discount=%d, want 1",got)}
 var sorcery,creature state.ObjID
 for _,obj:=range e.G.Objs {
    if obj.IsToken||obj.Face()==nil {continue}
    switch obj.Face().Name {
    case "Baral Sorcery Probe":sorcery=obj.ID
    case "Baral Creature Probe":creature=obj.ID
    }
 }
 if sorcery==0||creature==0 {t.Fatal("missing fixture cards")}
 if got:=reduceOf(t,e,0,sorcery);got!=1 {t.Fatalf("sorcery discount %d, want 1",got)}
 if got:=reduceOf(t,e,0,creature);got!=0 {t.Fatalf("creature discount %d, want 0",got)}
 replayCheck(t,e,cfg)
}
