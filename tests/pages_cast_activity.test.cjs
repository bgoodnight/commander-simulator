"use strict";
const {test}=require("node:test"),assert=require("node:assert/strict");
const outcomes=require("../web/pages/game_outcomes.js");
test("full-cohort cast panels show median and clickable ranked cards",()=>{
  class Node{
    constructor(tag){this.tag=tag;this.children=[];this.className="";this.textContent="";this.style={};this.attributes={};}
    append(...x){this.children.push(...x)}
    appendChild(x){this.children.push(x);return x}
    replaceChildren(...x){this.children=x}
    setAttribute(k,v){this.attributes[k]=v}
    addEventListener(){}
  }
  const prior=global.document;global.document={createElement:tag=>new Node(tag)};
  try{
    const root=new Node("main"),opened=[];
    outcomes.renderCohortInsights(root,{verified_games:4,observed_games:4,
      coverage:{level:"full-cohort",missing:0},categories:{},
      cast_activity:{games:4,median_spells:9.5,median_creatures:6,
        spells:[{name:"Sol Ring",games:2,casts:3}],
        creatures:[{name:"Mortarion",games:3,casts:4}]}},4,
      {onOpenRecordedCard:name=>opened.push(name)});
    const walk=n=>[n,...n.children.flatMap(walk)],nodes=walk(root);
    assert.ok(nodes.some(n=>n.textContent==="Spells cast"));
    assert.ok(nodes.some(n=>n.textContent==="9.5"));
    assert.ok(nodes.some(n=>n.textContent==="75.0% · 4 casts"));
    const button=nodes.find(n=>n.attributes["aria-label"]==="View Mortarion card details");
    assert.ok(button);button.onclick();assert.deepEqual(opened,["Mortarion"]);
  }finally{global.document=prior;}
});
