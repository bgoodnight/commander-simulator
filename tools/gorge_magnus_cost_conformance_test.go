package rules

import (
    "testing"

    "github.com/adams-shaun/gorge/engine/state"
)

// Conformance fixture for the Magnus strategy: ReduceCost Amount$ uses the
// controller's current CREATURE TOKENS (not all creatures) and stacks with
// independently-gated instant/sorcery reducers. This is not a claim that the
// archived Magnus card's exact Forge script has passed a corpus-level check.
const magnusCostProbeSrc = "Name:Magnus Cost Probe\nManaCost:3 U R\nTypes:Legendary Creature Demon Primarch\nPT:4/5\n" +
    "S:Mode$ ReduceCost | ValidCard$ Instant,Sorcery | Type$ Spell | Activator$ You | Amount$ X\n" +
    "SVar:X:Count$Valid Creature.YouCtrl+Token\n" +
    "Oracle:Instant and sorcery spells you cast cost {1} less for each creature token you control.\n"

const reducerCostProbeSrc = "Name:Generic Spell Reducer\nManaCost:1 U\nTypes:Creature Human Wizard\nPT:1/3\n" +
    "S:Mode$ ReduceCost | ValidCard$ Instant,Sorcery | Type$ Spell | Activator$ You | Amount$ 1\n" +
    "Oracle:Instant and sorcery spells you cast cost {1} less.\n"

const spellCostProbeSrc = "Name:Five Mana Probe\nManaCost:5 U\nTypes:Instant\nOracle:Probe.\n"
const sorceryCostProbeSrc = "Name:Sorcery Probe\nManaCost:2 U U\nTypes:Sorcery\nOracle:Probe.\n"
const creatureCostProbeSrc = "Name:Creature Probe\nManaCost:5 U\nTypes:Creature Wizard\nPT:1/1\nOracle:Probe.\n"
const tokenCostProbeSrc = "Name:Probe Creature Token\nTypes:Creature Warrior\nPT:1/1\nOracle:Token.\n"

func TestMagnusCreatureTokenReductionsStackAndRespectColors(t *testing.T) {
    e, cfg, spell := newFixtureDeck(t, 82818, spellCostProbeSrc, magnusCostProbeSrc, reducerCostProbeSrc, sorceryCostProbeSrc, creatureCostProbeSrc)
    // No active reducers.
    if got:=e.SpellEffectiveCost(0, spell); got!="5 U" {
        t.Fatalf("baseline spell cost %q, want 5 U",got)
    }
    putCreature(t,e,0,magnusCostProbeSrc)
    if got:=e.SpellEffectiveCost(0,spell); got!="5 U" {
        t.Fatalf("Magnus with zero tokens cost %q, want 5 U",got)
    }
    putToken(t,e,0,tokenCostProbeSrc,state.ZBattlefield)
    if got:=e.SpellEffectiveCost(0,spell); got!="4 U" {
        t.Fatalf("Magnus with one token cost %q, want 4 U",got)
    }
    putToken(t,e,0,tokenCostProbeSrc,state.ZBattlefield)
    putToken(t,e,0,tokenCostProbeSrc,state.ZBattlefield)
    if got:=e.SpellEffectiveCost(0,spell); got!="2 U" {
        t.Fatalf("Magnus with three tokens cost %q, want 2 U",got)
    }
    putCreature(t,e,0,reducerCostProbeSrc)
    if got:=e.SpellEffectiveCost(0,spell); got!="1 U" {
        t.Fatalf("stacked three-token + reducer cost %q, want 1 U",got)
    }
    putCreature(t,e,0,reducerCostProbeSrc)
    if got:=e.SpellEffectiveCost(0,spell); got!="U" {
        t.Fatalf("stacked generic reductions cost %q, want U",got)
    }
    // Extra token cannot remove colored pips.
    putToken(t,e,0,tokenCostProbeSrc,state.ZBattlefield)
    if got:=e.SpellEffectiveCost(0,spell); got!="U" {
        t.Fatalf("generic reduction removed blue pip: %q",got)
    }
    var sorcery, creature state.ObjID
    for _,id:=range e.G.Zone(state.ZHand,0) {
        o:=e.G.Obj(id)
        if o==nil||o.Face()==nil {continue}
        switch o.Face().Name {
        case "Sorcery Probe":sorcery=id
        case "Creature Probe":creature=id
        }
    }
    if sorcery==0||creature==0 {t.Fatal("missing priced hand cards")}
    if got:=e.SpellEffectiveCost(0,sorcery); got!="U U" {
        t.Fatalf("sorcery colored pips incorrectly discounted: %q",got)
    }
    if got:=e.SpellEffectiveCost(0,creature); got!="5 U" {
        t.Fatalf("creature incorrectly discounted: %q",got)
    }
    replayCheck(t,e,cfg)
}
