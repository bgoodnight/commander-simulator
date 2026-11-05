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
    "SVar:X:Count$Valid Creature.token+YouCtrl\n" +
    "Oracle:Instant and sorcery spells you cast cost {1} less for each creature token you control.\n"

const reducerCostProbeSrc = "Name:Generic Spell Reducer\nManaCost:1 U\nTypes:Creature Human Wizard\nPT:1/3\n" +
    "S:Mode$ ReduceCost | ValidCard$ Instant,Sorcery | Type$ Spell | Activator$ You | Amount$ 1\n" +
    "Oracle:Instant and sorcery spells you cast cost {1} less.\n"

const reducerCostProbeSrc2 = "Name:Second Generic Spell Reducer\\nManaCost:U R\\nTypes:Creature Wizard\\nPT:2/2\\n" +
    "S:Mode$ ReduceCost | ValidCard$ Instant,Sorcery | Type$ Spell | Activator$ You | Amount$ 1\\n" +
    "Oracle:Instant and sorcery spells you cast cost {1} less.\\n"

const spellCostProbeSrc = "Name:Five Mana Probe\nManaCost:5 U\nTypes:Instant\nOracle:Probe.\n"
const sorceryCostProbeSrc = "Name:Sorcery Probe\nManaCost:2 U U\nTypes:Sorcery\nOracle:Probe.\n"
const creatureCostProbeSrc = "Name:Creature Probe\nManaCost:5 U\nTypes:Creature Wizard\nPT:1/1\nOracle:Probe.\n"
const tokenCostProbeSrc = "Name:Probe Creature Token\nTypes:Creature Warrior\nPT:1/1\nOracle:Token.\n"

func TestMagnusCreatureTokenReductionsStackAndRespectColors(t *testing.T) {
    e, cfg, spell := newFixtureDeck(t, 82818, spellCostProbeSrc, magnusCostProbeSrc, reducerCostProbeSrc, reducerCostProbeSrc2, sorceryCostProbeSrc, creatureCostProbeSrc)
    // ReduceCost composition is valid even when fixture card is in library.
    // SpellEffectiveCost intentionally returns empty for non-hand objects.
    check:=func(label string, id state.ObjID, expected int32){
        t.Helper()
        if got:=reduceOf(t,e,0,id);got!=expected {
            t.Fatalf("%s: reduction %d, want %d",label,got,expected)
        }
    }
    check("baseline",spell,0)
    putCreature(t,e,0,magnusCostProbeSrc)
    check("Magnus zero tokens",spell,0)
    putToken(t,e,0,tokenCostProbeSrc,state.ZBattlefield)
    check("Magnus one token",spell,1)
    putToken(t,e,0,tokenCostProbeSrc,state.ZBattlefield)
    putToken(t,e,0,tokenCostProbeSrc,state.ZBattlefield)
    check("Magnus three tokens",spell,3)
    putCreature(t,e,0,reducerCostProbeSrc)
    check("three tokens plus one generic reducer",spell,4)
    putCreature(t,e,0,reducerCostProbeSrc2)
    check("three tokens plus two generic reducers",spell,5)
    putToken(t,e,0,tokenCostProbeSrc,state.ZBattlefield)
    check("four tokens plus two reducers",spell,6)
    var sorcery, creature state.ObjID
    // newFixtureDeck constructs the first card as spell and usually puts
    // the other named cards in the library or hand. Scan all objects.
    for _,obj:=range e.G.Objs {
        if obj.Face()==nil||obj.IsToken {continue}
        switch obj.Face().Name {
        case "Sorcery Probe": sorcery=obj.ID
        case "Creature Probe": creature=obj.ID
        }
    }
    if sorcery==0||creature==0 {t.Fatal("missing fixture objects")}
    check("sorcery also receives token-scaled reducers",sorcery,6)
    check("non-instant non-sorcery does not get discount",creature,0)
    replayCheck(t,e,cfg)
}
