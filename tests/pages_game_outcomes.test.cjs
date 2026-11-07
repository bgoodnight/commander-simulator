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
test('Gorge tokens use source identity and permanent types for exclusive zones',()=>{
  const lookup=name=>({
    'Saheeli, Sublime Artificer':{type_line:'Legendary Planeswalker — Saheeli'},
    'Baleful Strix':{type_line:'Artifact Creature — Bird'},
    'Mox Amber':{type_line:'Legendary Artifact'},
    'Dryad Arbor':{type_line:'Land Creature — Dryad'}
  })[name]||null;
  const opts={lookupRecordedCard:lookup,
    tokenNames:['Experimental Construct'],
    tokenTypes:{'Experimental Construct':'Token Artifact Creature — Construct'}};
  assert.equal(Outcomes.tokenInfo('Servo Token').type,'Token Artifact Creature — Servo');
  assert.equal(Outcomes.battlefieldZone('Servo Token',opts),'Creatures');
  assert.equal(Outcomes.battlefieldZone('Drake Token',opts),'Creatures');
  assert.equal(Outcomes.battlefieldZone('Faerie Token',opts),'Creatures');
  assert.equal(Outcomes.battlefieldZone('Spawn Token',opts),'Creatures');
  assert.equal(Outcomes.battlefieldZone('Treasure Token',opts),'Artifacts');
  assert.equal(Outcomes.battlefieldZone('Clue Token',opts),'Artifacts');
  assert.equal(Outcomes.battlefieldZone('Experimental Construct',opts),'Creatures');
  assert.equal(Outcomes.battlefieldZone('Saheeli, Sublime Artificer',opts),'Planeswalkers');
  assert.equal(Outcomes.battlefieldZone('Baleful Strix',opts),'Creatures');
  assert.equal(Outcomes.battlefieldZone('Dryad Arbor',opts),'Creatures');
  assert.equal(Outcomes.battlefieldZone('Mox Amber',opts),'Artifacts');
  assert.equal(Outcomes.battlefieldZone('Unknown Token',opts),'Other permanents');
  assert.equal(Outcomes.tokenInfo('Experimental Construct',opts).tone,'generic');
  assert.equal(Outcomes.tokenInfo('Ordinary card',opts),null);
});
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
      this.attributes={};this.style={setProperty(name,value){this[name]=value}};this.events={};this.dataset={};
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
    assert.ok(walk(reviewer).some(n=>n.className==='insight-turn-row'));
    const reviewNodes=walk(reviewer);
    assert.ok(reviewNodes.some(n=>n.tag==='select'));
    assert.ok(reviewNodes.some(n=>n.textContent==='Game 1/2 · Win'));

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
      this.children=[];this.style={setProperty(name,value){this[name]=value}};this.attributes={};this.events={};}
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
  assert.match(source,/onReviewRun\(entry\.group\.id,entry\.run\.seed,entry\.turn\)/);
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
      this.children=[];this.attributes={};this.dataset={};this.style={setProperty(name,value){this[name]=value}};this.events={};this.hidden=false}
    append(...n){this.children.push(...n)}
    appendChild(n){this.children.push(n);return n}
    replaceChildren(...n){this.children=[...n]}
    setAttribute(k,v){this.attributes[k]=String(v)}
    removeAttribute(k){delete this.attributes[k]}
    addEventListener(k,fn){this.events[k]=fn}
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
    assert.ok(walk(card).some(n=>n.tag==='summary'&&
      n.textContent==='View example games'));
    // Grave Titan has two distinct recorded seeds, so cycle through both.
    buttons[0].onclick();
    const metrics=walk(card).filter(n=>n.className.includes('insight-featured-metric-link'));
    assert.equal(metrics.length,2);
    assert.ok(metrics.some(n=>n.children[0].textContent==='Times played'));
    assert.ok(metrics.some(n=>n.children[0].textContent==='Median event turn'));
    const tracker=walk(card).find(n=>n.className.includes('insight-inline-tracker'));
    assert.ok(tracker);
    metrics[0].onclick();
    assert.equal(tracker.open,true);
    assert.ok(!walk(tracker).some(n=>n.tag==='select'));
    assert.ok(walk(tracker).some(n=>n.className==='insight-turn-row'));
    const label=walk(tracker).find(n=>n.className==='insight-example-game-label');
    assert.ok(label);
    assert.match(label.textContent,/Seed 1 · Unresolved/);
    metrics[1].onclick();
    assert.match(label.textContent,/Seed 2 · Unresolved/);
    metrics[0].onclick();
    assert.match(label.textContent,/Seed 1 · Unresolved/);
    const action=walk(tracker).find(n=>n.className.includes('insight-example-full-link'));
    assert.ok(action);
    assert.equal(action.textContent,'Open full reviewer ↗');
    tracker.open=false;tracker.events.toggle();
    assert.ok(walk(tracker).some(n=>n.tag==='summary'&&
      n.textContent==='View example games'));
    tracker.open=true;tracker.events.toggle();
    assert.ok(walk(tracker).some(n=>n.tag==='summary'&&
      n.textContent==='Close example games'));
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
      this.children=[];this.attributes={};this.dataset={};this.style={setProperty(name,value){this[name]=value}};
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
      externalInsights:true,reviewerRoot:reviewer
    });
    const walk=n=>[n,...n.children.flatMap(walk)];
    const grid=root.children.find(n=>n.className.includes('latest-insight-grid'));
    const dialog=root.children.find(n=>n.tag==='dialog');
    assert.ok(dialog);
    // The dedicated R2 Key Insights panel owns card rankings, not this hero.
    assert.equal(walk(grid).filter(n=>n.className.includes('game-outcome-hero')&&
      n.tag==='details').length,1);
    assert.equal(walk(grid).filter(n=>n.tag==='details'&&
      n.className.includes('game-outcome-card')).length,1);
    assert.ok(!walk(grid).some(n=>n.className==='game-outcome-title'&&
      ['Opponent Types','Game Length','Commander Arrival','Mana Ramp'].includes(n.textContent)));
    const tiles=walk(grid).filter(n=>n.className==='game-outcome-hero-highlight');
    assert.deepEqual(tiles.map(n=>n.children[0].textContent),
      ['Best matchup','Game length','Commander arrival','Mana ramp']);
    const headings=['Opponent Types','Game Length','Commander Arrival','Mana Ramp'];
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
    // Game-length distribution is vertical with a sparse tick axis.
    tiles[1].events.click({preventDefault(){},stopPropagation(){}});
    assert.ok(walk(dialog).some(n=>n.className==='game-length-histogram-bars'));
    const axis=walk(dialog).find(n=>n.className==='game-length-histogram-axis');
    assert.ok(axis&&axis.children.length<=5);
    // Overall win percentage opens the two-outcome life progression.
    const winMetric=walk(grid).find(n=>n.className==='game-outcome-hero-stat is-win');
    assert.ok(winMetric);
    assert.equal(winMetric.tag,'button');
    assert.equal(winMetric.attributes['aria-haspopup'],'dialog');
    winMetric.events.click({preventDefault(){},stopPropagation(){}});
    const life=walk(dialog).find(n=>n.tag==='svg'&&
      n.attributes['aria-label']?.includes('Median life progression for wins'));
    assert.ok(life);
    assert.ok(walk(life).filter(n=>n.tag==='polyline').length>=1);
    assert.ok(!walk(dialog).some(n=>n.textContent==='Seat 2'));
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
      this.children=[];this.attributes={};this.style={setProperty(name,value){this[name]=value}};this.dataset={};this.events={};
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
    const root=new Node('main'),reviewer=new Node('section'),openedTokens=[];
    const withTurns={...runUnresolved(),opening_hand:['Grave Titan'],
      ui_observations:[
        {turn:1,hand:['Grave Titan'],battlefield:[],graveyard:[],
          actions:[{type:'creature_cast',card:'Grave Titan',seat:0}]},
        {turn:2,hand:[],battlefield:['Grave Titan','Servo Token'],graveyard:[],
          actions:[{type:'draw',card:'Plains',seat:0}]},
        {turn:3,hand:[],battlefield:['Grave Titan'],graveyard:[],
          actions:[{type:'land_play',card:'Swamp',seat:0}]}]};
    Outcomes.render(root,[batch([withTurns])],{
      deckKey:'necron_dynasties',deckHash:'a'.repeat(64),
      reviewerRoot:reviewer,onOpenTokenCard:card=>openedTokens.push(card),lookupRecordedCard:name=>({
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
    assert.equal(walk(opened).filter(n=>n.className.split(' ').includes('insight-board-seat')).length,4);
    assert.ok(walk(opened).some(n=>n.className.includes('insight-seat-life-delta is-loss')));
    assert.ok(walk(turns[3]).some(n=>n.textContent==='Swamp'));
    const token=walk(turns[2]).find(n=>n.tag==='button'&&n.attributes['aria-label']==='View Servo Token card details');
    assert.ok(token,'turn reviewer renders Servo token');
    token.onclick();
    assert.equal(openedTokens[0]?.name,'Servo Token');
    const insight=walk(root).find(n=>n.className.includes('insight-featured-panel')&&
      walk(n).some(x=>x.textContent==='Most played card'));
    assert.ok(insight);
    const tracker=walk(insight).find(n=>n.className.includes('insight-inline-tracker'));
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
      this.children=[];this.attributes={};this.style={setProperty(name,value){this[name]=value}};this.dataset={};this.events={};}
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
    assert.ok(walk(targetPanel).some(n=>n.tag==='summary'&&
      n.textContent==='View example games'));
  }finally{global.document=before}
});

test('selected card insight embeds relevant game turns and real life/zone change glows',()=>{
  class Node{
    constructor(tag){this.tag=tag;this.className='';this.textContent='';
      this.children=[];this.attributes={};this.style={setProperty(name,value){this[name]=value}};this.dataset={};this.events={};
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
    const tracker=walk(insight).find(n=>n.className.includes('insight-inline-tracker'));
    assert.ok(tracker,'relevant recorded seed should have an expandable timeline');
    assert.equal(walk(tracker).some(n=>n.className==='game-outcome-turn-tile'),false,
      'tracker must render lazily when expanded');
    tracker.open=true;tracker.events.toggle();
    const turns=walk(tracker).filter(n=>n.className==='insight-turn-row');
    assert.equal(turns.length,4);
    assert.ok(walk(turns[1]).some(n=>n.className.includes('insight-seat-life-delta is-loss')));
    assert.ok(walk(turns[2]).some(n=>n.className.includes('insight-hand-shortcut')&&
      n.textContent.includes('▤ 0')));
    assert.ok(walk(turns[2]).some(n=>n.className==='insight-end-state'));
    assert.ok(walk(turns[2]).some(n=>n.className.includes('insight-board-graveyard')&&
      walk(n).some(c=>c.textContent.includes('Graveyard'))));
    assert.ok(walk(turns[2]).some(n=>n.className==='insight-action-art'&&
      n.src.includes('Grave Titan')));
    assert.ok(walk(turns[2]).some(n=>n.className==='insight-action-phase-heading'&&
      n.textContent==='Your turn'));
    assert.equal(walk(tracker).some(n=>n.className==='game-outcome-turn-tile'),false);
  }finally{global.document=before}
});

test('turn background uses first named card and enemy activity has one condensed block',()=>{
  class Node{
    constructor(tag){this.tag=tag;this.className='';this.textContent='';
      this.children=[];this.attributes={};this.style={setProperty(name,value){this[name]=value}};this.dataset={};this.events={};
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
    const header=turns[1].children.find(n=>n.tag==='summary');
    assert.ok(header,'turn header must render while the row is closed');
    const cover=header.children.find(n=>n.className==='insight-turn-cover');
    assert.ok(cover,'art belongs inside the collapsed summary');
    assert.equal(cover.src,'https://example.com/Swamp.jpg');
    assert.equal(turns[1].open,false);
    const firstBody=walk(turns[1]);
    const rest=firstBody.filter(n=>n.className==='insight-rest-of-turn');
    assert.equal(rest.length,1);
    assert.ok(!walk(rest[0]).some(n=>n.textContent.includes('abstract')));
    assert.equal(firstBody.filter(n=>n.className==='insight-action-phase is-opponent').length,0);
    assert.ok(!firstBody.some(n=>n.textContent==='Seat not recorded'));
    const player=firstBody.find(n=>n.className==='insight-action-phase is-player');
    assert.ok(player);
    assert.ok(walk(player).some(n=>n.textContent==='Unknown Card'));
    assert.equal(walk(rest[0]).filter(n=>n.className.split(' ').includes('insight-board-seat')).length,0);
    const second=walk(turns[2]);
    assert.equal(second.filter(n=>n.className.split(' ').includes('insight-board-seat')).length,4);
  }finally{global.document=before}
});

test('narrated turn summary and expanded actions reuse factual card-linked wording',()=>{
  class Node{
    constructor(tag){this.tag=tag;this.className='';this.textContent='';
      this.children=[];this.attributes={};this.style={setProperty(name,value){this[name]=value}};this.dataset={};this.events={};
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
  const opened=[];
  try{
    const r={...runUnresolved(),ui_observations:[
      {turn:1,hand:['Swamp','Grave Titan'],battlefield:[],graveyard:[],exile:[],
       actions:[
         {type:'draw',card:'Swamp',seat:0},
         {type:'land_play',card:'Swamp',seat:0},
         {type:'creature_cast',card:'Grave Titan',seat:0},
         {type:'reviewed_enter_resolved',card:'Grave Titan',seat:0},
         {type:'opponent_abstract_blocked_combat',seat:1},
         {type:'cleanup_discard',card:'Swamp',seat:0}
       ]},
      {turn:2,hand:['Swamp'],battlefield:['Grave Titan'],graveyard:['Swamp'],exile:[],
       actions:[{type:'draw',card:'Sol Ring',seat:0}]},
      {turn:3,hand:[],battlefield:[],graveyard:['Swamp','Grave Titan'],exile:[],
       actions:[]}
    ]};
    const root=new Node('main'),reviewer=new Node('section');
    Outcomes.render(root,[batch([r])],{
      deckKey:'necron_dynasties',deckHash:'a'.repeat(64),reviewerRoot:reviewer,
      lookupRecordedCard:name=>({name,art:'https://example.com/'+name.replaceAll(' ','-')+'.jpg'}),
      onOpenRecordedCard:name=>opened.push(name)
    });
    const turns=walk(reviewer).filter(n=>n.className==='insight-turn-row');
    const turn1=turns[1];
    const heading=walk(turn1).find(n=>n.className==='insight-turn-activity');
    assert.equal(heading.textContent,
      'Drew Swamp, Played Swamp, Grave Titan, Discarded Swamp');
    const player=walk(turn1).find(n=>n.className==='insight-action-phase is-player');
    const labels=walk(player).filter(n=>n.className==='insight-action-verb');
    assert.deepEqual(labels.map(n=>n.textContent),
      ['Drew ','Played ','Played ','Discarded ']);
    const names=walk(player).filter(n=>n.className.includes('is-text-only'));
    const arts=walk(player).filter(n=>n.className.includes('is-art-only'));
    assert.equal(names.length,4);
    assert.equal(arts.length,4);
    names[2].onclick();arts[2].onclick();
    assert.deepEqual(opened,['Grave Titan','Grave Titan']);
    const rest=walk(turn1).find(n=>n.className==='insight-rest-of-turn');
    assert.ok(rest);
    assert.ok(!walk(rest).some(n=>n.textContent==='1 other recorded event'));
    assert.equal(walk(rest).filter(n=>n.className.split(' ').includes('insight-board-seat')).length,0);
    assert.ok(!walk(turn1).some(n=>n.textContent==='reviewed enter resolved'));
    const third=walk(turns[3]);
    assert.ok(third.some(n=>n.textContent.includes('Moved from battlefield to graveyard')));
    assert.ok(third.some(n=>n.className.includes('is-text-only')&&
      walk(n).some(child=>child.textContent==='Grave Titan')));
  }finally{global.document=before}
});

test('rest of turn summarizes named enemy casts and keeps unknown-seat pilot actions first',()=>{
  const source=fs.readFileSync('web/pages/game_outcomes.js','utf8');
  assert.match(source,/actionSection\("Your turn",own/);
  assert.match(source,/!Number\.isInteger\(a\.seat\)\|\|Number\(a\.seat\)===0/);
  assert.match(source,/Enemies played /);
  assert.doesNotMatch(source,/actionSection\("Seat not recorded"/);
  assert.doesNotMatch(source,/actionSection\("Enemy activity/);
  assert.match(source,/insight-seat-life-strip/);
});

test('card insight removes redundant labels, caps visible bars, and links metrics to examples',()=>{
  const source=fs.readFileSync('web/pages/game_outcomes.js','utf8');
  const css=fs.readFileSync('web/pages/style.css','utf8');
  const start=source.indexOf('function cardPerformancePanel(');
  const end=source.indexOf('function readablePredictor(',start);
  const panel=source.slice(start,end);
  assert.ok(start>=0&&end>start);
  for(const phrase of ['Compare cards and evidence','View card details ↗',
    'Select a bar','Bars compare','Jump to recorded turn','Games recorded',
    'Median per game']){
    assert.ok(!panel.includes(phrase),phrase+' should be absent');
  }
  assert.match(panel,/Times played/);
  assert.match(panel,/Median event turn/);
  assert.match(panel,/View example games/);
  assert.match(panel,/exampleIndex=\(exampleIndex\+1\)%examples.length/);
  assert.match(panel,/ranked.slice\(0,10\)/);
  assert.match(css,/\.insight-featured-bars\{grid-auto-rows:64px;max-height:204px/);
  assert.match(css,/\.insight-featured-bars::-webkit-scrollbar/);
});

test('results hero is compact with proportions below percentages and cohort footer',()=>{
  const source=fs.readFileSync('web/pages/game_outcomes.js','utf8');
  const app=fs.readFileSync('web/pages/app.js','utf8');
  const css=fs.readFileSync('web/pages/style.css','utf8');
  const start=source.indexOf('function outcomeCard(');
  const end=source.indexOf('function metricTile(',start);
  const hero=source.slice(start,end);
  assert.ok(start>=0&&end>start);
  assert.ok(!hero.includes('Long-game outcomes'));
  assert.ok(!hero.includes('Explore opponent results'));
  assert.ok(!hero.includes('modeled games'));
  assert.ok(hero.indexOf('copy.appendChild(numbers)')<
    hero.indexOf('copy.appendChild(bar)'));
  assert.ok(hero.indexOf('copy.appendChild(bar)')<
    hero.indexOf('if(options.heroHighlights?.length)'));
  assert.match(hero,/game-outcome-hero-meta/);
  assert.match(source,/outcomeMeta=total\+" games · "/);
  assert.match(source,/opponent groups · "\+seedLabel/);
  assert.match(source,/Seeds "/);
  assert.ok(!app.includes('intro.appendChild(el("h1","Simulation Results"))'));
  assert.match(css,/insight-turn-row \.insight-turn-cover/);
  assert.match(css,/opacity:\.95/);
});

test('compact insight density retains three scrollable ranks and no duplicated expanded mana',()=>{
  const js=fs.readFileSync('web/pages/game_outcomes.js','utf8');
  const css=fs.readFileSync('web/pages/style.css','utf8');
  const start=js.indexOf('function cardPerformancePanel(');
  const end=js.indexOf('function readablePredictor(',start);
  const panel=js.slice(start,end);
  assert.ok(start>=0&&end>start);
  assert.doesNotMatch(panel,/featured\.appendChild\(cost\)/);
  assert.match(panel,/const cost=manaCost\(item\)/); // The header still shows mana.
  assert.match(panel,/ranked\.slice\(0,10\)/);
  assert.match(css,/\.insight-featured-bars\{grid-auto-rows:43px;max-height:137px/);
  assert.match(css,/\.insight-featured-panel \.game-outcome-summary\{min-height:86px/);
  assert.match(css,/\.insight-featured-card-art\{width:min\(100%,138px\)/);
});

test('collapsed turn art and compact insight height have foreground-safe styles',()=>{
  const js=fs.readFileSync('web/pages/game_outcomes.js','utf8');
  const css=fs.readFileSync('web/pages/style.css','utf8');
  assert.match(js,/if\(cover\)summary\.appendChild\(cover\)/);
  assert.match(css,/\.insight-turn-row \.insight-turn-row-summary::before/);
  assert.match(css,/\.insight-turn-row \.insight-turn-cover\{/);
  assert.match(css,/\.insight-featured-panel \.game-outcome-summary\{min-height:64px\}/);
});

test('compact insight summary beats legacy 152px min-height specificity',()=>{
  const css=fs.readFileSync('web/pages/style.css','utf8');
  const oldRule='.latest-insight-grid .game-outcome-card:not(.game-outcome-hero) > .game-outcome-summary';
  const newRule='.latest-insight-grid .game-outcome-card.insight-featured-panel:not(.game-outcome-hero) > .game-outcome-summary';
  const oldIndex=css.indexOf(oldRule),newIndex=css.indexOf(newRule);
  assert.ok(oldIndex>=0&&newIndex>oldIndex);
  assert.match(css.slice(newIndex,newIndex+170),/min-height:68px/);
  assert.match(css.slice(newIndex,newIndex+170),/height:auto/);
});

test('turn header art prefers highest-value nonland play, ties first, and falls back to land',()=>{
  class Node{
    constructor(tag){this.tag=tag;this.className='';this.textContent='';
      this.children=[];this.attributes={};this.style={setProperty(name,value){this[name]=value}};this.dataset={};this.events={};
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
      {turn:1,hand:[],battlefield:[],graveyard:[],
       actions:[{type:'land_play',card:'Swamp',seat:0},
         {type:'artifact_cast',card:'Sol Ring',seat:0},
         {type:'creature_cast',card:'Grave Titan',seat:0},
         {type:'creature_cast',card:'Other Six',seat:0},
         {type:'creature_cast',card:'Tiny Creature',seat:1}]},
      {turn:2,hand:[],battlefield:[],graveyard:[],
       actions:[{type:'land_play',card:'Swamp',seat:0},
         {type:'draw',card:'Grave Titan',seat:0}]},
      {turn:3,hand:[],battlefield:[],graveyard:[],
       actions:[{type:'draw',card:'Sol Ring',seat:0}]}]};
    const cards={
      'Swamp':{type_line:'Basic Land — Swamp',mana_cost:''},
      'Sol Ring':{type_line:'Artifact',mana_cost:'{1}'},
      'Grave Titan':{type_line:'Creature — Giant',mana_cost:'{4}{B}{B}'},
      'Other Six':{type_line:'Creature — Horror',cmc:6},
      'Tiny Creature':{type_line:'Creature',mana_cost:'{9}'}
    };
    const root=new Node('main'),reviewer=new Node('section');
    Outcomes.render(root,[batch([r])],{
      deckKey:'necron_dynasties',deckHash:'a'.repeat(64),reviewerRoot:reviewer,
      lookupRecordedCard:name=>({...cards[name],
        art:'https://example.com/'+name.replaceAll(' ','-')+'.jpg'})
    });
    const rows=walk(reviewer).filter(n=>n.className==='insight-turn-row');
    const image=index=>rows[index].children.find(n=>n.tag==='summary')
      .children.find(n=>n.className==='insight-turn-cover')?.src;
    assert.equal(image(1),'https://example.com/Grave-Titan.jpg');
    assert.equal(image(2),'https://example.com/Swamp.jpg');
    assert.equal(image(3),'https://example.com/Sol-Ring.jpg');
  }finally{global.document=before}
});

test('compact turn display does not leak internal abstract event identifiers',()=>{
  const js=fs.readFileSync('web/pages/game_outcomes.js','utf8');
  const css=fs.readFileSync('web/pages/style.css','utf8');
  const a=js.indexOf('function narratedAction(');
  const b=js.indexOf('function narratedText(',a);
  const narrator=js.slice(a,b);
  assert.ok(a>=0&&b>a);
  assert.doesNotMatch(narrator,/return \{verb:type\.replaceAll/);
  assert.match(narrator,/Destruction prevented/);
  assert.match(narrator,/Attack blocked/);
  assert.match(narrator,/Unblocked combat damage/);
  assert.match(narrator,/return null/);
  assert.match(css,/\.insight-turn-row \.insight-turn-row-summary\{\s*min-height:48px/);
  assert.match(css,/\.insight-turn-activity\{font-size:\.72rem;min-width:0/);
});

test('turn rows expand naturally for multiline summaries while metrics do not squeeze the text',()=>{
  const css=fs.readFileSync('web/pages/style.css','utf8');
  const rule=css.slice(css.lastIndexOf('/* Turn height follows the action narrative'));
  assert.match(rule,/grid-template-areas:"turn narrative expand" "\. metrics metrics"/);
  assert.match(rule,/white-space:normal/);
  assert.match(rule,/-webkit-line-clamp:3/);
  assert.match(rule,/grid-area:metrics;width:100%;max-width:none/);
  assert.match(rule,/min-height:64px;height:auto/);
});

test('opening draw row shows actual cards with only sourced mulligan wording',()=>{
  const js=fs.readFileSync('web/pages/game_outcomes.js','utf8');
  const exporter=fs.readFileSync('tools/build_game_outcomes.py','utf8');
  assert.match(js,/index\?"Turn "\+index:"Draw"/);
  assert.match(js,/index\?synopsis\|\|"No named plays recorded":openingHandDescription\(run\)/);
  assert.match(js,/count===0\?"Kept initial hand"/);
  assert.match(js,/count===1\?"Mulliganed once"/);
  assert.match(js,/count!==null\?"Mulliganed "\+count\+" times"/);
  assert.match(js,/run\.opening_hand/);
  assert.match(exporter,/"mulligan":\{/);
  assert.match(exporter,/"taken":run\.get\("mulligan",\{\}\)\.get\("taken"\)/);
});
test('compact example controls omit selector and repeated run heading',()=>{
  const js=fs.readFileSync('web/pages/game_outcomes.js','utf8');
  const css=fs.readFileSync('web/pages/style.css','utf8');
  const page=fs.readFileSync('docs/deck-lab/results.html','utf8');
  assert.ok(!js.includes('Choose a relevant recorded example'));
  assert.match(js,/Close example games/);
  assert.match(js,/hideEvidenceHead:true/);
  assert.match(js,/insight-example-game-label/);
  assert.match(css,/insight-example-full-link/);
  assert.match(css,/compact-selection\{margin-bottom:3px\}/);
  assert.ok(page.includes('id="game-outcome-refresh"')); // Existing page-wide refresh is separate from compact evidence controls.
});

test('long turns use natural height and combat remains in expanded evidence',()=>{
  const css=fs.readFileSync('web/pages/style.css','utf8');
  const js=fs.readFileSync('web/pages/game_outcomes.js','utf8');
  const newer=css.slice(css.lastIndexOf('/* Adaptive turn lengths'));
  assert.match(newer,/-webkit-line-clamp:unset/);
  assert.match(newer,/overflow:visible;white-space:normal/);
  assert.match(newer,/insight-turn-row \.insight-turn-row-summary\{min-height:58px;height:auto/);
  const narration=js.slice(js.indexOf('function turnNarration('),
    js.indexOf('function observedZoneChanges('));
  assert.match(narration,/damage\|attack\|block\|prevented\|combo_loss/);
  assert.match(js,/function actionEvidenceDetail\(action\)/);
  assert.match(js,/insight-rest-combat/);
  assert.match(js,/actionEvidenceDetail\(a\)/);
});

test('turn summary only shows supported mana colors and hand, not battlefield/graveyard badges',()=>{
  const js=fs.readFileSync('web/pages/game_outcomes.js','utf8');
  const css=fs.readFileSync('web/pages/style.css','utf8');
  assert.match(js,/function recordedManaOutput\(observation\)/);
  assert.match(js,/mana_produced_by_color/);
  assert.match(js,/insight-hand-shortcut/);
  assert.match(js,/function endStatePanel\(observation,options\)/);
  assert.match(js,/\["Creatures","Lands","Planeswalkers","Artifacts",/);
  assert.match(js,/"Enchantments","Other permanents"/);
  assert.match(js,/\["Hand",observation.hand\]/);
  assert.match(css,/\.insight-end-zone/);
  assert.ok(!js.includes('[["▤","hand"],["♟","battlefield"],["◆","graveyard"]]'));
});

test('turn summaries and end state use actual mana pips and clickable typed cards',()=>{
  class Node{
    constructor(tag){this.tag=tag;this.className='';this.textContent='';
      this.children=[];this.attributes={};this.style={setProperty(name,value){this[name]=value}};this.dataset={};this.events={};this.open=false}
    append(...items){this.children.push(...items)}
    appendChild(item){this.children.push(item);return item}
    replaceChildren(...items){this.children=[...items]}
    setAttribute(k,v){this.attributes[k]=String(v)}
    addEventListener(k,handler){this.events[k]=handler}
    get lastChild(){return this.children.at(-1)}
    querySelector(selector){
      if(selector==='.insight-end-zone')return this.children.flatMap(
        function walk(n){return [n,...n.children.flatMap(walk)]}
      ).find(n=>n.className==='insight-end-zone')||null;
      return null;
    }
  }
  const old=global.document;global.document={
    createElement:tag=>new Node(tag),createElementNS:(_,tag)=>new Node(tag)};
  const walk=n=>[n,...n.children.flatMap(walk)];
  try{
    const run0={...runUnresolved(),opening_hand:['Swamp','Sol Ring'],
      ui_observations:[
        {turn:1,hand:['Swamp','Dark Ritual'],battlefield:[
          'Swamp','Sol Ring','Baleful Strix','Phyrexian Arena'],
         graveyard:['Dead Card'],exile:[],actions:[],
         mana_produced_by_color:{B:2,C:2}},
        {turn:2,hand:[],battlefield:[],graveyard:[],exile:[],actions:[]},
        {turn:3,hand:[],battlefield:[],graveyard:[],exile:[],actions:[]}
      ]};
    const types={'Swamp':'Basic Land — Swamp','Sol Ring':'Artifact',
      'Baleful Strix':'Artifact Creature — Bird',
      'Phyrexian Arena':'Enchantment','Dark Ritual':'Instant','Dead Card':'Sorcery'};
    const root=new Node('main'),reviewer=new Node('section');
    Outcomes.render(root,[batch([run0])],{
      deckKey:'necron_dynasties',deckHash:'a'.repeat(64),reviewerRoot:reviewer,
      lookupRecordedCard:name=>({type_line:types[name]||'',name,
        art:'https://example.com/card.jpg'}),
      renderMana:cost=>{const n=new Node('span');n.className='test-mana';
        n.textContent=cost;return n}
    });
    const turn=walk(reviewer).find(n=>n.className==='insight-turn-row'&&
      walk(n).some(x=>x.textContent==='Turn 1'));
    assert.ok(turn);
    const summary=turn.children.find(n=>n.tag==='summary');
    assert.ok(walk(summary).some(n=>n.textContent==='▤ 2'));
    assert.ok(walk(summary).some(n=>n.textContent==='{B}'));
    assert.ok(walk(summary).some(n=>n.textContent==='{C}'));
    assert.ok(!walk(summary).some(n=>String(n.textContent).includes('◆ 1')));
    const zones=walk(turn).filter(n=>n.className.startsWith('insight-end-zone '));
    const labels=zones.map(z=>walk(z.children[0]).map(n=>n.textContent).join(''));
    for(const text of ['Hand · 2','Creatures · 1','Lands · 1',
      'Artifacts · 1','Enchantments · 1','Graveyard · 1'])
      assert.ok(labels.some(x=>x.includes(text)),text);
    const hand=walk(summary).find(n=>n.className.includes('insight-hand-shortcut'));
    hand.onclick();
    assert.equal(turn.open,true);
    const handZone=zones.find(z=>z.className.includes('insight-board-hand'));
    assert.ok(handZone);
    assert.equal(handZone.open,true);
    assert.ok(walk(handZone).some(n=>n.tag==='button'&&
      String(n.attributes['aria-label']).includes('Dark Ritual')));
  }finally{global.document=old}
});

test('R2 insight panels forward token-detail handlers into nested recorded examples',()=>{
  const adapter=fs.readFileSync('web/pages/r2_original_results.js','utf8');
  const render=fs.readFileSync('web/pages/game_outcomes.js','utf8');
  // Full-cohort rankings, observed-batch fallback, and per-game replay all
  // share the token detail bridge. Leaving any out makes token tiles inert.
  const callbacks=adapter.match(/onOpenTokenCard:card=>window\.GorgeDeckLabOpenTokenCard\?\.\(card\)/g)||[];
  assert.ok(callbacks.length>=4,'every R2 insight and replay entrypoint needs token clicks');
  assert.match(render,/onOpenTokenCard:options\.onOpenTokenCard,\s*example:entry\.group/);
  assert.match(render,/if\(token\)options\.onOpenTokenCard\?\.\(/);
});
