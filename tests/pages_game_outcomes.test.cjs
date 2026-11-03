'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const Outcomes=require('../web/pages/game_outcomes.js');
const Replay=require('../web/pages/replay.js');

const totals=values=>Object.fromEntries(values.map((v,i)=>[String(i),v]));
function history(rounds){
  return rounds.map((values,round)=>({
    round,life_totals:totals(values),
    alive_seats:values.map((v,i)=>v>0?i:null).filter(x=>x!==null),
    life_changes:round===0?[]:[{seat:0,kind:'loss',amount:Math.max(0,rounds[round-1][0]-values[0]),
      delta:values[0]-rounds[round-1][0],before:rounds[round-1][0],after:values[0],
      source_object_id:null}],
    new_eliminations:[]
  }));
}
function run(seed,status,rounds,roles={"1":"aggro","2":"value","3":"control"},extras={}){
  return {seed,opponent_roles:roles,completed_rounds:rounds.length-1,
    outcome:{status,requested_rounds:3,completed_rounds:rounds.length-1,
      complete:status!=='unresolved',winner_seat:status==='win'?0:null},
    life_history:history(rounds),...extras};
}
function batch(runs,scenario='mixed',extras={}){
  return {format:Outcomes.FORMAT,schema_version:1,
    deck_key:'necron_dynasties',deck_sha256:'a'.repeat(64),
    scenario,seed_count:runs.length,requested_rounds:3,
    opponent_fidelity:'abstract_opponent_pressure_not_card_exact',
    outcomes_are_competitive_win_rates:false,runs,...extras};
}
const runWon=()=>run(0,'win',[
  [40,40,40,40],[36,26,28,29],[32,0,0,0]
]);
const runUnresolved=()=>run(1,'unresolved',[
  [40,40,40,40],[35,38,39,40],[20,12,23,30],[18,9,20,26]
]);
const runLost=()=>run(2,'loss',[
  [40,40,40,40],[30,36,35,40],[0,29,34,40]
]);
test('strict long-game schema prevents goldfish or mislabelled rates from masquerading as matches',()=>{
  assert.equal(Outcomes.validate(batch([runWon()])),true);
  assert.equal(Outcomes.validate({...batch([runWon()]),outcomes_are_competitive_win_rates:true}),false);
  assert.equal(Outcomes.validate({...batch([runWon()]),opponent_fidelity:'goldfish_no_opponents'}),false);
  assert.equal(Outcomes.validate({...batch([runWon()]),format:'commander-bounded-archive-v1'}),false);
  assert.equal(Outcomes.validate(batch([runWon(),runWon()])),false); // duplicate seed
  const wrong=runWon();wrong.life_history[1].life_totals={"0":36,"1":40};
  assert.equal(Outcomes.validate(batch([wrong])),false);
  assert.equal(Outcomes.model([batch([runWon()])],'necron_dynasties','b'.repeat(64)).totalGames,0);
});
test('life trends retain denominators after early finishes and interquartile bands',()=>{
  const t=Outcomes.lifeTrend([runWon(),runUnresolved()],3);
  assert.deepEqual(t.map(x=>x.observed),[2,2,2,1]);
  assert.equal(t[1].seats[0].median,35.5);
  assert.equal(t[1].seats[0].p25,35.25);
  assert.equal(t[1].seats[0].p75,35.75);
  assert.equal(t[2].seats[1].alive,1);
  assert.equal(t[3].seats[0].median,18);
  assert.equal(t[3].seats[0].alive,1);
});
test('unresolved rounds are never added to modeled losses; duplicates do not inflate counts',()=>{
  const x=batch([runWon(),runUnresolved()]);
  const r=Outcomes.model([x,x],'necron_dynasties','a'.repeat(64));
  assert.equal(r.sourceBatches,2);
  assert.equal(r.duplicates,2);
  assert.equal(r.totalGames,2);
  assert.equal(r.groups[0].counts.win,1);
  assert.equal(r.groups[0].counts.loss,0);
  assert.equal(r.groups[0].counts.unresolved,1);
  assert.equal(r.groups[0].terminal,1);
  assert.equal(r.groups[0].life[3].observed,1);
});
test('abstract opponent roles remain scenarios, and named decks use whole-pod associations',()=>{
  const a=batch([runWon(),runUnresolved()],'mixed');
  const b=batch([runLost()],'aggressive');
  const model=Outcomes.model([a,b],'necron_dynasties','a'.repeat(64));
  assert.equal(model.groups.length,2);
  let rows=Outcomes.matchupRows(model.groups);
  assert.equal(rows.length,2);
  assert.ok(rows.every(x=>x.kind==='abstract'));
  assert.ok(rows.every(x=>/abstract policies/.test(x.label)));
  assert.equal(rows[0].counts.win,1);
  const newRoles=runUnresolved();
  newRoles.opponent_roles={"1":"control","2":"aggro","3":"value"};
  const rolled=Outcomes.model(
    [batch([runWon(),newRoles])],'necron_dynasties','a'.repeat(64));
  assert.equal(rolled.groups.length,1);
  assert.match(rolled.groups[0].label,/mixed opponent roles/);
  const tagged=batch([runWon(),runUnresolved()],'mixed',{
    opponent_decks:[
      {seat:1,deck_key:'death_guard',commander_name:'Mortarion'},
      {seat:2,deck_key:'magnus',commander_name:'Magnus'},
      {seat:3,deck_key:'gisa',commander_name:'Gisa'}
    ]
  });
  const enriched=Outcomes.model([tagged],'necron_dynasties','a'.repeat(64));
  assert.equal(enriched.groups[0].deckRoster.length,3);
  rows=Outcomes.matchupRows(enriched.groups);
  assert.equal(rows.length,3);
  assert.ok(rows.every(row=>row.kind==='named'));
  assert.equal(rows[0].games,2);
  assert.ok(rows.some(row=>row.label.includes('Mortarion')));
});
test('pilot personalities and provisional modes preserve independent seed cohorts',()=>{
  const engineLoss=runLost();
  engineLoss.seed=0;
  const original=batch([runWon()],'mixed',{
    pilot_style:'adaptive',provisional_mode:'safe'
  });
  const otherPilot=batch([engineLoss],'mixed',{
    pilot_style:'engine',provisional_mode:'safe'
  });
  const otherMode=batch([runUnresolved()],'mixed',{
    pilot_style:'adaptive',provisional_mode:'off'
  });
  const legacy=batch([runLost()],'mixed');
  const result=Outcomes.model(
    [original,otherPilot,otherMode,legacy],
    'necron_dynasties','a'.repeat(64));
  assert.equal(result.totalGames,4);
  assert.equal(result.groups.length,4);
  assert.equal(result.duplicates,0);
  assert.ok(result.groups.some(g=>g.pilotStyle==='engine'&&g.counts.loss===1));
  assert.ok(result.groups.some(g=>g.pilotStyle==='adaptive'&&
    g.provisionalMode==='safe'&&g.counts.win===1));
  assert.ok(result.groups.some(g=>g.pilotStyle==='adaptive'&&
    g.provisionalMode==='off'&&g.counts.unresolved===1));
  assert.ok(result.groups.some(g=>g.pilotStyle==='unrecorded'&&
    g.provisionalMode==='unrecorded'));
  const duplicate=Outcomes.model([original,original],
    'necron_dynasties','a'.repeat(64));
  assert.equal(duplicate.duplicates,1);
  assert.equal(duplicate.totalGames,1);
});
test('opponent rankings count wins and medians use observed terminal / elimination rounds',()=>{
  const won=runWon(),lost=runLost(),unfinished=runUnresolved();
  const combined=batch([won,lost,unfinished],'aggressive');
  const result=Outcomes.model([combined],'necron_dynasties','a'.repeat(64));
  const rows=Outcomes.matchupRows(result.groups);
  assert.equal(rows.length,1);
  const metrics=Outcomes.matchupMetrics(rows[0]);
  assert.equal(metrics.games,3);
  assert.equal(metrics.wins,1);
  assert.equal(metrics.losses,1);
  assert.equal(metrics.unresolved,1);
  assert.equal(metrics.medianFinishRound,2);
  assert.equal(metrics.finishedGames,2);
  assert.equal(metrics.medianPilotKnockoutRound,2);
  assert.equal(metrics.pilotKnockouts,1);
  assert.equal(metrics.medianVictoryRound,2);
  assert.equal(metrics.gamesWithOpponentKnockout,1);
  assert.equal(metrics.medianLastPilotLife,18);
  assert.equal(Outcomes.knockoutRound(unfinished,0),null);
  const noFinish=Outcomes.matchupMetrics(Outcomes.matchupRows(
    Outcomes.model([batch([unfinished])],'necron_dynasties','a'.repeat(64)).groups)[0]);
  assert.equal(noFinish.medianFinishRound,null);
  assert.equal(noFinish.medianPilotKnockoutRound,null);
  const lots=batch([won,run(3,'win',[[40,40,40,40],[40,0,0,0]])],'balanced');
  const few=batch([lost,unfinished],'control');
  const ranked=Outcomes.matchupRows(Outcomes.model([lots,few],
    'necron_dynasties','a'.repeat(64)).groups);
  assert.equal(ranked[0].title,'Balanced pod');
  assert.equal(ranked[0].counts.win,2);
});
test('modeled panels expose distinct outcome, life and matchup disclosures with clickable seeds',()=>{
  class Node{
    constructor(tag){
      this.tag=tag;this.className='';this.textContent='';this.children=[];
      this.attributes={};this.style={};this.events={};this.dataset={};
    }
    append(...n){this.children.push(...n)}
    appendChild(n){this.children.push(n);return n}
    replaceChildren(...n){this.children=[...n]}
    setAttribute(k,v){this.attributes[k]=String(v);if(k==='open')this.open=true}
    removeAttribute(k){delete this.attributes[k];if(k==='open')this.open=false}
    showModal(){this.open=true}
    close(){this.open=false}
    focus(){}
    addEventListener(k,fn){this.events[k]=fn}
    get lastChild(){return this.children.at(-1)}
  }
  const before=global.document;
  global.document={createElement:t=>new Node(t),createElementNS:(_,t)=>new Node(t)};
  try{
    const root=new Node('main'),reviewer=new Node('section');
    const report=Outcomes.render(root,[batch([runWon(),runUnresolved()])],{
      deckKey:'necron_dynasties',deckHash:'a'.repeat(64),reviewerRoot:reviewer
    });
    const walk=n=>[n,...n.children.flatMap(walk)];
    let nodes=walk(root);
    assert.equal(report.totalGames,2);
    assert.ok(nodes.some(n=>n.tag==='dialog'));
    assert.ok(nodes.some(n=>n.className==='game-outcome-hero-highlight'));
    const matchupTile=nodes.find(n=>n.className==='game-outcome-hero-highlight');
    matchupTile.events.click({preventDefault(){},stopPropagation(){}});
    nodes=walk(root);
    assert.ok(nodes.some(n=>n.className==='game-outcome-matchup-view'));
    assert.ok(nodes.some(n=>n.textContent==='Wins · 1/2'));
    assert.ok(nodes.some(n=>n.textContent==='50%'));
    assert.ok(nodes.some(n=>n.textContent==='Game Outcomes'));
    assert.ok(nodes.some(n=>String(n.textContent).includes('One opponent type recorded')));
    const rank=nodes.find(n=>n.tag==='button'&&n.className==='game-outcome-rank-row');
    assert.ok(rank);
    assert.equal(rank.attributes['aria-pressed'],'true');
    assert.ok(nodes.some(n=>n.className==='game-outcome-insight-metric'));
    const seed=nodes.find(n=>n.tag==='button'&&n.className==='game-outcome-seed');
    assert.ok(seed);seed.onclick();
    nodes=walk(root);
    assert.ok(nodes.some(n=>n.textContent==='Round 2 · 1 of 4 seats alive'));
    const reviewNodes=walk(reviewer);
    assert.ok(reviewNodes.some(n=>n.tag==='select'));
    assert.ok(reviewNodes.some(n=>n.textContent==='Seed 0 · Win · Round 2'));

    // Scenario comparison must not silently cross pilot personalities.
    Outcomes.render(root,[
      batch([runWon()],'balanced',{pilot_style:'adaptive',provisional_mode:'safe'}),
      batch([runLost()],'aggressive',{pilot_style:'engine',provisional_mode:'safe'})
    ],{deckKey:'necron_dynasties',deckHash:'a'.repeat(64)});
    nodes=walk(root);
    // The headline selects one compatible rules/pilot cohort, not both.
    assert.equal(nodes.filter(n=>n.className==='game-outcome-hero-stat is-win').length,1);
    const newMatchupTile=nodes.find(n=>n.className==='game-outcome-hero-highlight');
    newMatchupTile.events.click({preventDefault(){},stopPropagation(){}});
    nodes=walk(root);
    assert.ok(nodes.some(n=>String(n.textContent).includes('One opponent type recorded')));
    assert.ok(!nodes.some(n=>String(n.textContent).includes(
      'Highest observed modeled win share')));
  }finally{global.document=before}
});
test('selecting an opponent scroll entry changes the one shown art card and per-opponent metrics',()=>{
  class Node{
    constructor(tag){this.tag=tag;this.className='';this.textContent='';
      this.children=[];this.style={};this.attributes={};this.events={};}
    append(...a){this.children.push(...a)}
    appendChild(a){this.children.push(a);return a}
    replaceChildren(...a){this.children=a}
    setAttribute(k,v){this.attributes[k]=String(v)}
    addEventListener(k,fn){this.events[k]=fn}
    get lastChild(){return this.children.at(-1)}
  }
  const before=global.document;
  global.document={createElement:t=>new Node(t),createElementNS:(_,t)=>new Node(t)};
  try{
    const root=new Node('main');
    Outcomes.render(root,[
      batch([runWon()],'aggressive',{pilot_style:'adaptive',provisional_mode:'safe'}),
      batch([runLost()],'control',{pilot_style:'adaptive',provisional_mode:'safe'})
    ],{deckKey:'necron_dynasties',deckHash:'a'.repeat(64),
      commanderArt:'https://example.com/pilot.jpg',
      portraitFor:bucket=>({name:bucket.title,art:'https://example.com/'+bucket.archetype+'.jpg'})
    });
    const walk=n=>[n,...n.children.flatMap(walk)];
    let nodes=walk(root);
    assert.ok(nodes.some(n=>n.className==='game-outcome-hero-art'&&
      n.src==='https://example.com/pilot.jpg'));
    // The headline pools both scenarios under the same pilot/rules/horizon,
    // not only the first active scenario.
    assert.ok(nodes.some(n=>n.textContent==='Wins · 1/2'));
    assert.ok(nodes.some(n=>n.textContent==='Losses · 1/2'));
    assert.ok(nodes.some(n=>n.className==='game-outcome-limits'));
    const matchupTile=nodes.find(n=>n.className==='game-outcome-hero-highlight');
    matchupTile.events.click({preventDefault(){},stopPropagation(){}});
    nodes=walk(root);
    const rank=nodes.filter(n=>n.className==='game-outcome-rank-row');
    assert.equal(rank.length,2);
    assert.equal(rank[0].attributes['aria-pressed'],'true');
    assert.ok(nodes.some(n=>n.className==='game-outcome-opponent-art'&&
      n.src.endsWith('/aggressive.jpg')));
    rank[1].onclick();
    nodes=walk(root);
    assert.equal(rank[1].attributes['aria-pressed'],'true');
    assert.equal(rank[0].attributes['aria-pressed'],'false');
    assert.ok(nodes.some(n=>n.className==='game-outcome-opponent-art'&&
      n.src.endsWith('/control.jpg')));
    const labels=nodes.filter(n=>n.className==='game-outcome-insight-metric')
      .flatMap(walk).map(n=>n.textContent);
    assert.ok(labels.includes('Our knockout round'));
    assert.ok(labels.includes('2'));
    assert.ok(labels.includes('0%'));
    assert.equal(nodes.filter(n=>n.className==='game-outcome-opponent-art').length,1);
  }finally{global.document=before}
});
test('results page and exporter wire a future published manifest and local JSON',()=>{
  const html=fs.readFileSync('web/pages/index.html','utf8');
  const app=fs.readFileSync('web/pages/app.js','utf8');
  const build=fs.readFileSync('tools/build_pages_deck_lab.py','utf8');
  assert.match(html,/id="long-game-panel"/);
  assert.match(html,/id="turn-reviewer-results"/);
  assert.doesNotMatch(html,/id="game-outcome-files"/);
  assert.match(html,/game_outcomes\.js/);
  assert.match(app,/loadLongGameFiles/);
  assert.match(app,/loadPublishedLongGame/);
  assert.match(app,/renderLongGamePanel/);
  assert.match(build,/outcome_assets/);
  assert.match(build,/validate_outcome_library/);
  const publisher=fs.readFileSync('tools/publish_game_outcomes.py','utf8');
  assert.match(publisher,/outcomes_are_competitive_win_rates/);
  assert.equal(typeof Replay.renderBoundedEvidence,'function');
});

test('published outcome loader fetches only the selected deck and refreshes the manifest',async()=>{
  const vm=require('node:vm');
  const script=fs.readFileSync('web/pages/app.js','utf8');
  const start=script.indexOf('function validatePublishedOutcomeIndex(');
  const end=script.indexOf('/* Optional, versioned replay assets.',start);
  assert.ok(start>=0&&end>start);
  const ids={
    mortarion_current:'d'.repeat(64),
    necron_dynasties:'e'.repeat(64)
  };
  const index={
    format:'commander-modeled-outcomes-library-v1',schema_version:1,
    engine_commit:'a'.repeat(40),
    files:['mortarion-current.json','necron.json'],
    by_deck:{
      mortarion_current:['mortarion-current.json'],
      necron_dynasties:['necron.json']
    },
    sha256:{
      'mortarion-current.json':'b'.repeat(64),
      'necron.json':'c'.repeat(64)
    }
  };
  const calls=[];
  let renders=0;
  const context={
    pageName:'results',selected:'mortarion_current',
    data:{decks:Object.keys(ids).map(key=>({key}))},
    selectedDeck:()=>({deck_sha256:ids[context.selected]}),
    isUnsimulatedVersion:()=>false,
    renderLongGamePanel:()=>{renders++},
    window:{DeckGameOutcomes:{validate:x=>!!x&&!!x.deck_key}},
    fetch:async url=>{
      calls.push(url);
      if(url.includes('manifest.json'))return {ok:true,status:200,json:async()=>index};
      const deck=url.includes('mortarion-current.json')?'mortarion_current':'necron_dynasties';
      return {ok:true,status:200,
        json:async()=>({deck_key:deck,deck_sha256:ids[deck]})};
    }
  };
  vm.createContext(context);
  vm.runInContext(
    'const publishedOutcomeBatches=new Map();'+
    'const publishedOutcomeRequests=new Map();'+
     'const publishedAnalysisByDeck=new Map();'+
    'let outcomeManifestPromise=null;let outcomeManifest=null;let outcomeLoadEpoch=0;'+
    'let longGameSourceNote="";'+script.slice(start,end),
    context);
  await vm.runInContext('loadPublishedLongGame()',context);
  assert.equal(calls.filter(x=>x.includes('manifest.json')).length,1);
  assert.equal(calls.filter(x=>x.includes('mortarion-current.json')).length,1);
  assert.equal(calls.filter(x=>x.includes('/necron.json')).length,0);
  context.selected='necron_dynasties';
  await vm.runInContext('loadPublishedLongGame()',context);
  assert.equal(calls.filter(x=>x.includes('/necron.json')).length,1);
  assert.equal(calls.filter(x=>x.includes('manifest.json')).length,1);
  context.selected='mortarion_current';
  await vm.runInContext('loadPublishedLongGame()',context);
  assert.equal(calls.filter(x=>x.includes('mortarion-current.json')).length,1);
  vm.runInContext('refreshPublishedLongGame()',context);
  await new Promise(resolve=>setTimeout(resolve,20));
  assert.equal(calls.filter(x=>x.includes('manifest.json')).length,2);
  assert.equal(calls.filter(x=>x.includes('mortarion-current.json')).length,2);
  assert.ok(renders>=4);
});

test('rich current-run observations restore most played creature and instant cards',()=>{
  const lookup=name=>({
    'Grave Titan':{type_line:'Creature — Giant'},
    'Sol Ring':{type_line:'Artifact'},
    'Go for the Throat':{type_line:'Instant'}
  })[name]||null;
  const rich={seed:12,completed_rounds:2,opening_hand:['Grave Titan'],
    ui_observations:[
      {turn:1,hand:['Grave Titan'],actions:[
        {type:'artifact_cast',card:'Sol Ring'},
        {type:'reviewed_instant_response',card:'Go for the Throat'}]},
      {turn:2,hand:[],actions:[
        {type:'creature_cast',card:'Grave Titan'},
        {type:'reviewed_removal_resolved',card:'Go for the Throat',destroyed_count:1}]}
    ]};
  const signals=Outcomes.observationCardStats([rich],lookup);
  assert.equal(signals.coverage,1);
  assert.equal(signals.creature.name,'Grave Titan');
  assert.equal(signals.instant.name,'Go for the Throat');
  assert.equal(signals.artifact.name,'Sol Ring');
  assert.equal(signals.removal.name,'Go for the Throat');
  const missing=Outcomes.observationCardStats([{seed:13,completed_rounds:2}],lookup);
  assert.equal(missing.coverage,0);
  assert.equal(missing.creature,null);
});

test('current-batch card rankings exclude basics, retain distinct scenario runs and use medians',()=>{
  const lookup=name=>({type_line:{
    'Grave Titan':'Creature — Giant','Sol Ring':'Artifact',
    'Go for the Throat':'Instant','Swamp':'Basic Land — Swamp',
    'Damnation':'Sorcery','Island':'Basic Land — Island'
  }[name]||'Artifact'});
  const example=(seed,cast)=>({seed,completed_rounds:2,
    opening_hand:['Swamp','Grave Titan','Go for the Throat'],
    ui_observations:[
      {turn:1,hand:['Grave Titan','Swamp'],actions:[
        {type:'land_play',card:'Swamp'},
        {type:'artifact_cast',card:'Sol Ring'}]},
      {turn:2,hand:[],actions:cast?
        [{type:'creature_cast',card:'Grave Titan'},
         {type:'reviewed_instant_response',card:'Go for the Throat'}]:
        [{type:'reviewed_instant_response',card:'Go for the Throat'}]}]});
  // Same seed in two different table scenarios represents two games.
  const stats=Outcomes.observationCardStats([example(2,true),example(2,false)],lookup);
  assert.equal(stats.coverage,2);
  assert.equal(stats.creature.name,'Grave Titan');
  assert.equal(stats.creature.games,1);
  assert.equal(stats.creature.median,0.5);
  assert.equal(stats.instant.name,'Go for the Throat');
  assert.equal(stats.instant.games,2);
  assert.equal(stats.longest.name,'Grave Titan');
  assert.equal(stats.longest.heldMedian,1);
  assert.ok(stats.ranked.played.every(x=>x.name!=='Swamp'));
  assert.ok(stats.ranked.seen.every(x=>x.name!=='Swamp'));
  assert.ok(stats.ranked.longest.every(x=>x.name!=='Swamp'));
});
test('elastic net card interpretation and sign chart sit immediately above reviewer',()=>{
  const source=fs.readFileSync('web/pages/game_outcomes.js','utf8');
  const css=fs.readFileSync('web/pages/style.css','utf8');
  assert.match(source,/function readablePredictor\(/);
  assert.match(source,/function elasticNetPanel\(/);
  assert.match(source,/elastic-net-coefficient-chart/);
  assert.match(source,/onReviewRun\(parent\.id,hit\.seed,hit\.turn\)/);
  assert.ok(source.lastIndexOf('cards.appendChild(elasticNetPanel(')>
    source.lastIndexOf('cards.appendChild(card("Life Progression"'));
  assert.ok(source.lastIndexOf('cards.appendChild(elasticNetPanel(')<
    source.lastIndexOf('jumpToReview=turnReviewer('));
  assert.match(css,/\.elastic-net-effect\.is-positive/);
  assert.match(css,/\.elastic-net-effect\.is-negative/);
});


test('featured card insight switches artwork, mana, metrics, and evidence with selected bar',()=>{
  class Node{
    constructor(tag){this.tag=tag;this.className='';this.textContent='';
      this.children=[];this.attributes={};this.dataset={};this.style={};this.hidden=false}
    append(...n){this.children.push(...n)}
    appendChild(n){this.children.push(n);return n}
    replaceChildren(...n){this.children=[...n]}
    setAttribute(k,v){this.attributes[k]=String(v)}
    removeAttribute(k){delete this.attributes[k]}
    addEventListener(){}
    get lastChild(){return this.children.at(-1)}
  }
  const before=global.document;
  global.document={createElement:t=>new Node(t),createElementNS:(_,t)=>new Node(t)};
  try{
    const make=(seed,card)=>run(seed,'unresolved',[
      [40,40,40,40],[40,40,40,40],[40,40,40,40],[40,40,40,40]
    ],undefined,{
      opening_hand:[card],
      ui_observations:[
        {turn:1,hand:[card],actions:[]},
        {turn:2,hand:[],actions:[{type:'creature_cast',card}]},
        {turn:3,hand:[],actions:[]}
      ]
    });
    const lookup=name=>({
      'Grave Titan':{name,art:'https://example.com/grave-art.jpg',
        image:'https://example.com/grave-full.jpg',mana_cost:'{4}{B}{B}',
        type_line:'Creature — Giant'},
      'Plague Spitter':{name,art:'https://example.com/plague-art.jpg',
        image:'https://example.com/plague-full.jpg',mana_cost:'{2}{B}',
        type_line:'Creature — Horror'}
    })[name]||null;
    const root=new Node('main'),reviewer=new Node('section');
    Outcomes.render(root,[batch([
      make(1,'Grave Titan'),make(2,'Grave Titan'),
      make(3,'Plague Spitter')
    ])],{
      deckKey:'necron_dynasties',deckHash:'a'.repeat(64),
      lookupRecordedCard:lookup,reviewerRoot:reviewer,
      renderMana:cost=>{const n=new Node('span');n.textContent='mana:'+cost;return n}
    });
    const walk=n=>[n,...n.children.flatMap(walk)];
    const card=walk(root).find(n=>n.className.includes('insight-featured-panel')&&
      walk(n).some(x=>x.textContent==='Most played creature'));
    assert.ok(card);
    const buttons=walk(card).filter(n=>n.className==='insight-featured-bar');
    assert.equal(buttons.length,2);
    const cover=walk(card).find(n=>n.className==='insight-featured-cover');
    assert.equal(cover.src,'https://example.com/grave-art.jpg');
    assert.ok(walk(card).some(n=>n.textContent==='mana:{4}{B}{B}'));
    buttons[1].onclick();
    assert.equal(buttons[1].attributes['aria-pressed'],'true');
    assert.equal(buttons[0].attributes['aria-pressed'],'false');
    assert.equal(cover.src,'https://example.com/plague-art.jpg');
    assert.ok(walk(card).some(n=>n.textContent==='mana:{2}{B}'));
    assert.ok(walk(card).some(n=>n.tag==='img'&&n.src==='https://example.com/plague-full.jpg'));
    assert.ok(walk(card).some(n=>n.className==='insight-featured-card-name'&&
      n.textContent==='Plague Spitter'));
    assert.ok(walk(card).some(n=>n.className==='game-outcome-review-link'&&
      n.textContent==='Seed 3 · Turn 2'));
  }finally{global.document=before}
});

test('commander and basic lands are excluded while seen-creature and use metrics are normalized',()=>{
  const lookup=name=>({type_line:{
    'Ghoulcaller Gisa':'Legendary Creature — Human Wizard',
    'Grave Titan':'Creature — Giant',
    'Sol Ring':'Artifact',
    'Swamp':'Basic Land — Swamp'
  }[name]||'Artifact'});
  function sample(seed,withTitan){
    return {seed,completed_rounds:2,
      opening_hand:['Swamp','Grave Titan'],
      ui_observations:[
        {turn:1,hand:['Grave Titan'],actions:[
          {type:'land_play',card:'Swamp'},
          {type:'reviewed_commander_cast',card:'Ghoulcaller Gisa'},
          {type:'artifact_cast',card:'Sol Ring'},
          {type:'reviewed_activated_ability',card:'Sol Ring'}]},
        {turn:2,hand:[],actions:[
          ...(withTitan?[{type:'creature_cast',card:'Grave Titan'}]:[]),
          {type:'reviewed_activated_ability',card:'Sol Ring'}]}
      ]};
  }
  const result=Outcomes.observationCardStats(
    [sample(1,true),sample(2,false)],lookup,'Ghoulcaller Gisa');
  assert.equal(result.coverage,2);
  assert.equal(result.played.name,'Sol Ring');
  assert.equal(result.creature.name,'Grave Titan');
  assert.equal(result.creature.games,1);
  assert.equal(result.creature.average,0.5);
  assert.equal(result.seenCreature.name,'Grave Titan');
  assert.equal(result.seenCreature.games,2);
  assert.equal(result.activated.name,'Sol Ring');
  assert.equal(result.activated.average,2);
  for(const category of ['played','seen','seenCreature','creature','longest','activated']){
    assert.ok(!result.ranked[category].some(item=>item.name==='Ghoulcaller Gisa'));
    assert.ok(!result.ranked[category].some(item=>item.name==='Swamp'));
  }
});
test('hero performance metrics open original details as modal panels, not grid duplicates',()=>{
  class Node{
    constructor(tag){this.tag=tag;this.className='';this.textContent='';
      this.children=[];this.attributes={};this.dataset={};this.style={};
      this.events={};this.open=false;this.focused=false;}
    append(...items){this.children.push(...items)}
    appendChild(item){this.children.push(item);return item}
    replaceChildren(...items){this.children=[...items]}
    setAttribute(k,v){this.attributes[k]=String(v);if(k==='open')this.open=true}
    removeAttribute(k){delete this.attributes[k];if(k==='open')this.open=false}
    addEventListener(k,handler){this.events[k]=handler}
    showModal(){this.open=true}
    close(){this.open=false;this.events.close?.()}
    focus(){this.focused=true}
    get lastChild(){return this.children.at(-1)}
  }
  const before=global.document;
  global.document={createElement:tag=>new Node(tag),
    createElementNS:(_,tag)=>new Node(tag)};
  try{
    const root=new Node('main'),reviewer=new Node('section');
    Outcomes.render(root,[batch([runWon(),runUnresolved(),runLost()])],{
      deckKey:'necron_dynasties',deckHash:'a'.repeat(64),
      reviewerRoot:reviewer
    });
    const walk=n=>[n,...n.children.flatMap(walk)];
    const grid=root.children.find(n=>n.className.includes('latest-insight-grid'));
    const dialog=root.children.find(n=>n.tag==='dialog');
    assert.ok(dialog);
    assert.ok(!walk(grid).some(n=>n.className==='game-outcome-title'&&
      ['Opponent Types','Game Length','Eliminations','Life Progression'].includes(n.textContent)));
    const tiles=walk(grid).filter(n=>n.className==='game-outcome-hero-highlight');
    assert.deepEqual(tiles.map(n=>n.children[0].textContent),
      ['Best matchup','Game length','Survival','Final life']);
    const headings=['Opponent Types','Game Length','Eliminations','Life Progression'];
    for(const [i,tile] of tiles.entries()){
      assert.equal(tile.tag,'button');
      assert.equal(tile.attributes['aria-haspopup'],'dialog');
      let stopped=false,prevented=false;
      tile.events.click({preventDefault(){prevented=true},stopPropagation(){stopped=true}});
      assert.ok(stopped&&prevented);
      assert.equal(dialog.open,true);
      const inDialog=walk(dialog);
      assert.ok(inDialog.some(n=>n.className==='game-outcome-title'&&n.textContent===headings[i]));
      assert.ok(inDialog.some(n=>n.className==='game-outcome-body'));
      const close=walk(dialog).find(n=>n.className==='game-outcome-detail-close');
      close.onclick();
      assert.equal(dialog.open,false);
      assert.equal(tile.focused,true);
    }
    assert.ok(walk(dialog).some(n=>n.className==='game-outcome-round-slider'));
  }finally{global.document=before}
});
test('dashboard modal CSS respects motion preferences and mobile size',()=>{
  const css=fs.readFileSync('web/pages/style.css','utf8');
  assert.match(css,/game-outcome-detail-dialog::backdrop/);
  assert.match(css,/prefers-reduced-motion:reduce/);
  assert.match(css,/game-outcome-detail-content/);
});
test('turn spotlight prioritizes real own plays and never invents drawn/opposing art',()=>{
  const art=name=>({name,art:'https://example.com/'+encodeURIComponent(name)+'.jpg'});
  const row={turn:2,actions:[
    {type:'draw',card:'Drawn Only',seat:0},
    {type:'creature_cast',card:'Grave Titan',seat:0},
    {type:'land_play',card:'Swamp',seat:0},
    {type:'reviewed_commander_cast',card:'Ghoulcaller Gisa',seat:0},
    {type:'creature_cast',card:'Opponent Card',seat:1}
  ]};
  const selected=Outcomes.turnSpotlight(row,art);
  assert.equal(selected.name,'Ghoulcaller Gisa');
  assert.equal(selected.action,'reviewed_commander_cast');
  assert.equal(Outcomes.turnSpotlight({actions:[
    {type:'draw',card:'Drawn Only',seat:0},
    {type:'creature_cast',card:'Opponent Card',seat:1}
  ]},art),null);
  assert.equal(Outcomes.turnSpotlight({actions:[
    {type:'creature_cast',card:'Grave Titan',seat:0}
  ]},()=>({name:'Grave Titan'})),null);
});
test('full-game reviewer uses same compact turn rows as insight evidence',()=>{
  class Node{
    constructor(tag){this.tag=tag;this.className='';this.textContent='';
      this.children=[];this.attributes={};this.style={};this.dataset={};this.events={};
      this.open=false;}
    append(...items){this.children.push(...items)}
    appendChild(item){this.children.push(item);return item}
    replaceChildren(...items){this.children=[...items]}
    setAttribute(k,v){this.attributes[k]=String(v)}
    addEventListener(k,handler){this.events[k]=handler}
    get lastChild(){return this.children.at(-1)}
  }
  const before=global.document;
  global.document={createElement:tag=>new Node(tag),
    createElementNS:(_,tag)=>new Node(tag)};
  try{
    const root=new Node('main'),reviewer=new Node('section');
    const withTurns={...runUnresolved(),opening_hand:['Grave Titan'],
      ui_observations:[
        {turn:1,hand:['Grave Titan'],battlefield:[],graveyard:[],
          actions:[{type:'creature_cast',card:'Grave Titan',seat:0}]},
        {turn:2,hand:[],battlefield:['Grave Titan'],graveyard:[],
          actions:[{type:'draw',card:'Plains',seat:0}]},
        {turn:3,hand:[],battlefield:['Grave Titan'],graveyard:[],
          actions:[{type:'land_play',card:'Swamp',seat:0}]}]};
    Outcomes.render(root,[batch([withTurns])],{
      deckKey:'necron_dynasties',deckHash:'a'.repeat(64),
      reviewerRoot:reviewer,lookupRecordedCard:name=>({
        name,art:'https://example.com/'+name.replaceAll(' ','-')+'.jpg'
      })
    });
    const walk=n=>[n,...n.children.flatMap(walk)];
    const turns=walk(reviewer).filter(n=>n.className==='insight-turn-row');
    assert.equal(turns.length,4);
    assert.equal(walk(reviewer).some(n=>n.className==='game-outcome-turn-tile'),false);
    const opened=turns[1];
    opened.open=true;
    assert.ok(walk(opened).some(n=>n.className==='insight-action-art'&&
      n.src==='https://example.com/Grave-Titan.jpg'));
    assert.ok(walk(opened).some(n=>n.className==='insight-seat-summary'));
    assert.ok(walk(opened).some(n=>n.className.includes('insight-seat-chip is-loss')));
    assert.ok(walk(turns[3]).some(n=>n.textContent==='Swamp'));
    const insight=walk(root).find(n=>n.className.includes('insight-featured-panel')&&
      walk(n).some(x=>x.textContent==='Most played card'));
    assert.ok(insight);
    const tracker=walk(insight).find(n=>n.className==='insight-inline-tracker');
    assert.ok(tracker);
    tracker.open=true;tracker.events.toggle();
    const inline=walk(tracker).filter(n=>n.className==='insight-turn-row');
    assert.equal(inline.length,turns.length);
    assert.deepEqual(inline.map(n=>n.children.find(x=>x.tag==='summary').children[0].textContent),
      turns.map(n=>n.children.find(x=>x.tag==='summary').children[0].textContent));
  }finally{global.document=before}
});

test('resolved tutor insights count found targets and tutor sources, not merely casts',()=>{
  const observed=(seed,actions)=>({seed,completed_rounds:1,
    opening_hand:[],ui_observations:[{turn:1,hand:[],actions}]});
  const r1=observed(1,[
    {type:'tutor_cast',card:'Fabricate'},
    {type:'tutor_resolved',card:'Fabricate',target_name:'Sol Ring',destination:'hand'},
    {type:'tutor_resolved',card:'Mystical Tutor',target_name:'Damnation',destination:'library_top'}]);
  const r2=observed(2,[
    {type:'tutor_cast',card:'Fabricate'},
    {type:'tutor_resolved',card:'Fabricate',target_name:'Sol Ring',destination:'hand'},
    {type:'tutor_resolved',card:'Fabricate'}, // Older, target-less projection
    {type:'tutor_resolved',card:'Opponent Tutor',target_name:'Swamp',seat:1}]);
  const r3=observed(3,[
    {type:'tutor_cast',card:'Fabricate'}, // Cast is not a successful find
    {type:'tutor_resolved',card:'Unresolved Search',destination:'hand'}]);
  const stats=Outcomes.observationCardStats([r1,r2,r3],()=>null);
  assert.equal(stats.confirmedTutors,3);
  assert.equal(stats.tutorFound.name,'Sol Ring');
  assert.equal(stats.tutorFound.eventCount,2);
  assert.equal(stats.tutorFound.games,2);
  assert.equal(stats.tutorUsed.name,'Fabricate');
  assert.equal(stats.tutorUsed.eventCount,2);
  assert.equal(stats.tutorUsed.games,2);
  assert.equal(stats.ranked.tutorFound[1].name,'Damnation');
  assert.equal(stats.ranked.tutorUsed[1].name,'Mystical Tutor');
  assert.equal(stats.tutorFound.events[0].tutor,'Fabricate');
  assert.equal(stats.tutorFound.events[0].target,'Sol Ring');
  assert.equal(stats.tutorFound.events[0].destination,'hand');
  assert.equal(stats.ranked.tutorFound.some(x=>x.name==='Swamp'),false);
  const absent=Outcomes.observationCardStats([r3],()=>null);
  assert.equal(absent.confirmedTutors,0);
  assert.equal(absent.tutorFound,null);
  assert.equal(absent.tutorUsed,null);
});
test('tutor card insight panels only appear for confirmed named search resolutions',()=>{
  class Node{
    constructor(tag){this.tag=tag;this.className='';this.textContent='';
      this.children=[];this.attributes={};this.style={};this.dataset={};this.events={};}
    append(...items){this.children.push(...items)}
    appendChild(item){this.children.push(item);return item}
    replaceChildren(...items){this.children=[...items]}
    setAttribute(k,v){this.attributes[k]=String(v)}
    addEventListener(k,cb){this.events[k]=cb}
    get lastChild(){return this.children.at(-1)}
  }
  const before=global.document;
  global.document={createElement:tag=>new Node(tag),
    createElementNS:(_,tag)=>new Node(tag)};
  const make=actions=>({...runUnresolved(),ui_observations:[
    {turn:1,hand:[],actions},{turn:2,hand:[],actions:[]},
    {turn:3,hand:[],actions:[]}]});
  const walk=n=>[n,...n.children.flatMap(walk)];
  const seen=root=>walk(root).filter(n=>n.className==='game-outcome-title').map(n=>n.textContent);
  try{
    const root=new Node('main'),reviewer=new Node('section');
    const options={deckKey:'necron_dynasties',deckHash:'a'.repeat(64),
      reviewerRoot:reviewer,lookupRecordedCard:name=>({
        name,art:'https://example.com/'+name+'.jpg',type_line:'Artifact'})};
    Outcomes.render(root,[batch([make([{type:'tutor_cast',card:'Fabricate'}])])],options);
    assert.ok(!seen(root).includes('Most tutored card'));
    assert.ok(!seen(root).includes('Most used tutor'));
    Outcomes.render(root,[batch([make([
      {type:'tutor_resolved',card:'Fabricate',target_name:'Sol Ring',destination:'hand'}
    ])])],options);
    assert.ok(seen(root).includes('Most tutored card'));
    assert.ok(seen(root).includes('Most used tutor'));
    const targetPanel=walk(root).find(n=>n.className.includes('insight-featured-panel')&&
      walk(n).some(x=>x.textContent==='Most tutored card'));
    assert.ok(targetPanel);
    assert.ok(walk(targetPanel).some(n=>n.className==='game-outcome-number'&&n.textContent==='100.0%'));
    assert.ok(walk(targetPanel).some(n=>n.className==='game-outcome-review-link'&&
      n.textContent.includes('Fabricate → Sol Ring')));
  }finally{global.document=before}
});

test('selected card insight embeds relevant game turns and real life/zone change glows',()=>{
  class Node{
    constructor(tag){this.tag=tag;this.className='';this.textContent='';
      this.children=[];this.attributes={};this.style={};this.dataset={};this.events={};
      this.open=false;}
    append(...items){this.children.push(...items)}
    appendChild(item){this.children.push(item);return item}
    replaceChildren(...items){this.children=[...items]}
    setAttribute(k,v){this.attributes[k]=String(v)}
    addEventListener(k,cb){this.events[k]=cb}
    get lastChild(){return this.children.at(-1)}
  }
  const before=global.document;
  global.document={createElement:tag=>new Node(tag),
    createElementNS:(_,tag)=>new Node(tag)};
  const walk=n=>[n,...n.children.flatMap(walk)];
  try{
    const r={...runUnresolved(),ui_observations:[
      {turn:1,hand:['Grave Titan'],battlefield:[],graveyard:[],
        actions:[{type:'draw',card:'Grave Titan',seat:0}]},
      {turn:2,hand:[],battlefield:['Grave Titan'],graveyard:[],
        actions:[{type:'creature_cast',card:'Grave Titan',seat:0}]},
      {turn:3,hand:[],battlefield:[],graveyard:['Grave Titan'],actions:[]}
    ]};
    const root=new Node('main'),reviewer=new Node('section');
    Outcomes.render(root,[batch([r])],{
      deckKey:'necron_dynasties',deckHash:'a'.repeat(64),reviewerRoot:reviewer,
      lookupRecordedCard:name=>({name,art:'https://example.com/'+name+'.jpg'})
    });
    const insight=walk(root).find(n=>n.className.includes('insight-featured-panel')&&
      walk(n).some(x=>x.textContent==='Most played card'));
    assert.ok(insight);
    const tracker=walk(insight).find(n=>n.className==='insight-inline-tracker');
    assert.ok(tracker,'relevant recorded seed should have an expandable timeline');
    assert.equal(walk(tracker).some(n=>n.className==='game-outcome-turn-tile'),false,
      'tracker must render lazily when expanded');
    tracker.open=true;tracker.events.toggle();
    const turns=walk(tracker).filter(n=>n.className==='insight-turn-row');
    assert.equal(turns.length,4);
    assert.ok(walk(turns[1]).some(n=>n.className.includes('is-loss')&&
      n.textContent.includes('♥')));
    assert.ok(walk(turns[2]).some(n=>n.className.includes('is-gain')&&
      n.textContent.includes('♟ 1')));
    assert.ok(walk(turns[2]).some(n=>n.className.includes('is-loss')&&
      n.textContent.includes('▤ 0')));
    assert.ok(walk(turns[2]).some(n=>n.className==='insight-action-art'&&
      n.src.includes('Grave Titan')));
    assert.ok(walk(turns[2]).some(n=>n.className==='insight-action-phase-heading'&&
      n.textContent.includes('Your recorded actions')));
    assert.equal(walk(tracker).some(n=>n.className==='game-outcome-turn-tile'),false);
  }finally{global.document=before}
});

test('turn background uses first named card and enemy activity has one condensed block',()=>{
  class Node{
    constructor(tag){this.tag=tag;this.className='';this.textContent='';
      this.children=[];this.attributes={};this.style={};this.dataset={};this.events={};
      this.open=false;}
    append(...items){this.children.push(...items)}
    appendChild(item){this.children.push(item);return item}
    replaceChildren(...items){this.children=[...items]}
    setAttribute(k,v){this.attributes[k]=String(v)}
    addEventListener(k,handler){this.events[k]=handler}
    get lastChild(){return this.children.at(-1)}
  }
  const before=global.document;
  global.document={createElement:tag=>new Node(tag),
    createElementNS:(_,tag)=>new Node(tag)};
  const walk=n=>[n,...n.children.flatMap(walk)];
  try{
    const r={...runUnresolved(),ui_observations:[
      {turn:1,hand:['Sol Ring'],battlefield:['Sol Ring'],graveyard:[],
       land_count:1,seat_states:{'1':{lands:2,battlefield:['Token'],hand_size:6}},
       actions:[
         {type:'land_play',card:'Swamp',seat:0},
         {type:'opponent_abstract_damage',seat:1,amount:3},
         {type:'opponent_abstract_pressure',seat:2,amount:1},
         {type:'opponent_abstract_attack',seat:1,amount:2},
         {type:'draw',card:'Unknown Card'}
       ]},
      {turn:2,hand:[],battlefield:['Sol Ring'],graveyard:[],
       land_count:2,seat_states:{'1':{lands:3,battlefield:['Token','Token'],hand_size:5}},
       actions:[{type:'tutor_resolved',card:'Fabricate',seat:0,target_name:'Sol Ring'}]},
      {turn:3,hand:[],battlefield:[],graveyard:[],actions:[]}]};
    const root=new Node('main'),reviewer=new Node('section');
    Outcomes.render(root,[batch([r])],{
      deckKey:'necron_dynasties',deckHash:'a'.repeat(64),
      reviewerRoot:reviewer,
      lookupRecordedCard:name=>({name,art:'https://example.com/'+name.replaceAll(' ','-')+'.jpg'})
    });
    const turns=walk(reviewer).filter(n=>n.className==='insight-turn-row');
    const cover=turns[1].children.find(n=>n.className==='insight-turn-cover');
    assert.ok(cover);
    assert.equal(cover.src,'https://example.com/Swamp.jpg');
    const firstBody=walk(turns[1]);
    const enemy=firstBody.filter(n=>n.className==='insight-action-phase is-opponent');
    assert.equal(enemy.length,1);
    assert.equal(walk(enemy[0]).filter(n=>n.className==='insight-action-entry').length,3);
    assert.ok(firstBody.some(n=>n.textContent.includes('Seat not recorded')));
    const second=walk(turns[2]);
    const seat1=second.find(n=>n.className==='insight-seat-line'&&
      n.children[0].textContent==='Seat 2');
    assert.ok(seat1);
    assert.ok(walk(seat1).some(n=>n.textContent.includes('◆ L 3 +1')));
    assert.ok(walk(seat1).some(n=>n.textContent.includes('♟ P 2 +1')));
    assert.ok(walk(seat1).some(n=>n.textContent.includes('▤ H 5 -1')));
    const seat2=second.find(n=>n.className==='insight-seat-line'&&
      n.children[0].textContent==='Seat 3');
    assert.ok(walk(seat2).some(n=>n.textContent.includes('◆ L —')));
    assert.ok(!walk(seat2).some(n=>n.textContent.includes('◆ L 0')));
  }finally{global.document=before}
});
