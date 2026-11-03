/* Long-game outcome report: presentation of pinned, source-traced records.
 * Opponent policies are abstract. Nothing in this module runs Magic rules,
 * turns an unresolved game into a loss, or estimates competitive win rates.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  else root.DeckGameOutcomes=api;
})(typeof window!=="undefined"?window:globalThis,function(){
  "use strict";
  const FORMAT="commander-modeled-outcomes-v1";
  const STATES=["win","loss","draw","unresolved","not_evaluated"];
  const SEATS=[0,1,2,3];
  const SEAT_COLORS=["#dfc18b","#81bbb2","#b8a3d3","#d69f99"];
  const nfmt=n=>Number.isFinite(n)?String(n):"—";
  const create=(tag,cls,text)=>{
    const node=document.createElement(tag);
    if(cls)node.className=cls;
    if(text!==undefined&&text!==null)node.textContent=String(text);
    return node;
  };
  function quantile(numbers,p){
    if(!numbers.length)return null;
    const a=[...numbers].sort((x,y)=>x-y);
    const k=(a.length-1)*p,i=Math.floor(k),j=Math.min(a.length-1,i+1);
    return a[i]+(a[j]-a[i])*(k-i);
  }
  function lifeAt(row,seat){return row?.life_totals?.[String(seat)]??row?.life_totals?.[seat]}
  function aliveAt(row,seat){
    return (row?.alive_seats||[]).some(s=>Number(s)===seat);
  }
  function exactDeck(batch,key,sha){
    return batch.deck_key===key&&batch.deck_sha256===sha;
  }
  function validate(batch){
    if(!batch||batch.format!==FORMAT||batch.schema_version!==1||
       typeof batch.deck_key!=="string"||typeof batch.deck_sha256!=="string"||
       typeof batch.scenario!=="string"||
       batch.opponent_fidelity!=="abstract_opponent_pressure_not_card_exact"||
       batch.outcomes_are_competitive_win_rates!==false||
       !Number.isInteger(batch.requested_rounds)||batch.requested_rounds<1||
       batch.requested_rounds>30||!Array.isArray(batch.runs)||
       !batch.runs.length||batch.runs.length>200)return false;
    const seeds=new Set();
    for(const run of batch.runs){
      if(!Number.isInteger(run.seed)||seeds.has(run.seed)||
         !Number.isInteger(run.completed_rounds)||run.completed_rounds<1||
         run.completed_rounds>batch.requested_rounds||
         !Array.isArray(run.life_history)||
         run.life_history.length!==run.completed_rounds+1||
         !run.outcome||!STATES.includes(run.outcome.status)||
         run.outcome.completed_rounds!==run.completed_rounds||
         run.outcome.requested_rounds!==batch.requested_rounds)return false;
      seeds.add(run.seed);
      for(let i=0;i<run.life_history.length;i++){
        const row=run.life_history[i];
        if(row.round!==i||!SEATS.every(s=>Number.isFinite(lifeAt(row,s)))||
           !Array.isArray(row.life_changes)||!Array.isArray(row.new_eliminations)||
           !Array.isArray(row.alive_seats))return false;
      }
    }
    return true;
  }
  function roleNames(roles){
    const pairs=[1,2,3].map(s=>String(roles?.[String(s)]||roles?.[s]||"abstract"));
    return pairs.join(" · ");
  }
  function opponentDecks(run,batch){
    const raw=run.opponent_decks||batch.opponent_decks||null;
    if(!Array.isArray(raw))return [];
    const bySeat=new Map();
    for(const entry of raw){
      const seat=Number(entry?.seat);
      const id=entry?.deck_key||entry?.deck_id;
      if(![1,2,3].includes(seat)||typeof id!=="string"||
         !id.trim()||bySeat.has(seat))continue;
      bySeat.set(seat,{
        seat,id,
        name:String(entry.commander_name||entry.deck_name||entry.name||id),
        version:typeof entry.deck_sha256==="string"?entry.deck_sha256:""
      });
    }
    return [...bySeat.values()].sort((a,b)=>a.seat-b.seat);
  }
  function rosterIdentity(decks){
    return decks.map(x=>x.seat+":"+x.id+":"+x.version).join("|");
  }
  function cohortValue(value){
    return typeof value==="string"&&/^[a-z0-9_-]{1,32}$/.test(value)?
      value:"unrecorded";
  }
  function labelFor(group){
    const context=" · pilot: "+group.pilotStyle+
      " · provisional: "+group.provisionalMode;
    if(group.deckRoster.length){
      return group.deckRoster.map(x=>x.name).join(" / ")+" · opposing pod"+context;
    }
    return group.scenario+" · "+(group.roleLabels.size===1?
      [...group.roleLabels][0]:"mixed opponent roles")+" (abstract policies)"+context;
  }
  function model(batches,key,sha){
    const matching=(batches||[]).filter(b=>validate(b)&&exactDeck(b,key,sha));
    const groups=new Map();
    let revisions=0,duplicates=0;
    for(const batch of matching){
      const pilotStyle=cohortValue(batch.pilot_style);
      const provisionalMode=cohortValue(batch.provisional_mode);
      for(const run of batch.runs){
        const deckRoster=opponentDecks(run,batch);
        const roleLabel=roleNames(run.opponent_roles);
        // Identical seeds under different pilot or rules modes are
        // distinct experiments, rather than duplicate imports.
        const id=[batch.scenario,batch.requested_rounds,
          deckRoster.length?"pod:"+rosterIdentity(deckRoster):"abstract_roles",
          pilotStyle,provisionalMode].join("|");
        if(!groups.has(id))groups.set(id,{
          id,scenario:batch.scenario,requestedRounds:batch.requested_rounds,
          pilotStyle,provisionalMode,
          roleLabels:new Set(),deckRoster,runs:[],exampleBySeed:new Map(),seeds:new Map()
        });
        const group=groups.get(id);
        group.roleLabels.add(roleLabel);
        const old=group.seeds.get(run.seed);
        if(old!==undefined){
          // Re-importing the same seed is an update, never an extra game.
          duplicates++;
          group.runs[old]={...run,batch};
        }else{
          group.seeds.set(run.seed,group.runs.length);
          group.runs.push({...run,batch});
        }
        const example=(batch.example_replays||[]).find(e=>e.seed===run.seed);
        if(example)group.exampleBySeed.set(run.seed,example);
      }
      revisions++;
    }
    const out=[...groups.values()];
    for(const group of out){
      group.runs.sort((a,b)=>a.seed-b.seed);
      group.label=labelFor(group);
      group.counts=Object.fromEntries(STATES.map(s=>[s,0]));
      for(const run of group.runs)group.counts[run.outcome.status]++;
      group.total=group.runs.length;
      group.terminal=group.total-group.counts.unresolved-group.counts.not_evaluated;
      group.life=lifeTrend(group.runs,group.requestedRounds);
      group.terminalRounds=group.runs.filter(r=>r.outcome.complete)
        .map(r=>r.completed_rounds);
    }
    out.sort((a,b)=>b.total-a.total||a.label.localeCompare(b.label));
    return {groups:out,sourceBatches:matching.length,duplicates,
      totalGames:out.reduce((n,g)=>n+g.total,0)};
  }
  function lifeTrend(runs,requestedRounds){
    const result=[];
    for(let round=0;round<=requestedRounds;round++){
      const observed=runs.map(r=>r.life_history[round]).filter(Boolean);
      if(!observed.length)break;
      const seats=Object.fromEntries(SEATS.map(s=>{
        const a=observed.map(r=>lifeAt(r,s));
        return [s,{
          mean:a.reduce((x,y)=>x+y,0)/a.length,
          median:quantile(a,.5),p25:quantile(a,.25),p75:quantile(a,.75),
          alive:observed.filter(r=>aliveAt(r,s)).length
        }];
      }));
      result.push({round,observed:observed.length,seats});
    }
    return result;
  }
  function displayRole(role){
    return String(role).split(/[-_ ]+/)
      .map(part=>part?part[0].toUpperCase()+part.slice(1):"").join(" ");
  }
  function matchupRows(groups,mode="scenarios"){
    // The result is always a four-player TABLE outcome, never a head-to-head.
    // A type appearing in two opposing seats counts once per game in 'types'.
    // A 'composition' is a sorted multiset: seat order has no significance.
    if(!["types","compositions","scenarios"].includes(mode))
      throw new RangeError("Unknown opponent comparison mode");
    const buckets=new Map();
    for(const group of groups){
      for(const run of group.runs){
        const opponents=opponentDecks(run,run.batch);
        let names;
        if(opponents.length){
          if(mode==="compositions"&&opponents.length===3){
            names=[{id:"named-pod:"+rosterIdentity(opponents.map(d=>({...d,seat:0}))
              .sort((a,b)=>a.id.localeCompare(b.id)||a.version.localeCompare(b.version))),
              label:opponents.map(d=>d.name).join(" / ")+" · recorded pod",
              title:opponents.map(d=>d.name).join(" / ")+" pod",
              kind:"named_pod"}];
          }else{
            names=opponents.map(d=>({id:"deck:"+d.id+":"+d.version,
              label:d.name+" · present in pod",title:d.name,
              kind:"named",portraitName:d.name}));
          }
        }else if(mode==="scenarios"){
          names=[{id:"scenario:"+group.id,label:group.label,kind:"abstract",
            title:displayRole(group.scenario)+" pod",archetype:group.scenario}];
        }else{
          const roles=[1,2,3].map(seat=>run.opponent_roles?.[seat]||
            run.opponent_roles?.[String(seat)]).filter(role=>
              typeof role==="string"&&role.trim());
          if(roles.length!==3){
            // Historical exports without seat provenance cannot be attributed
            // to a type. Keep their scenario label rather than inventing one.
            names=[{id:"legacy:"+group.id,label:group.label,
              title:displayRole(group.scenario)+" pod",
              kind:"abstract",archetype:group.scenario}];
          }else if(mode==="types"){
            names=[...new Set(roles)].map(role=>({
              id:"type:"+role,label:displayRole(role)+" · present in pod",
              title:displayRole(role),kind:"type",archetype:role
            }));
          }else{
            const sorted=[...roles].sort();
            const counts=new Map();
            for(const role of sorted)counts.set(role,(counts.get(role)||0)+1);
            const title=[...counts].map(([role,count])=>
              displayRole(role)+(count>1?" × "+count:"")).join(" / ");
            names=[{id:"composition:"+sorted.join("|"),
              label:title+" · table composition",title:title+" pod",
              kind:"composition",archetype:null}];
          }
        }
        // A pod with two copies of the same named deck/type is ONE game.
        for(const named of new Map(names.map(row=>[row.id,row])).values()){
          if(!buckets.has(named.id))buckets.set(named.id,{
            id:named.id,label:named.label,title:named.title,kind:named.kind,
            portraitName:named.portraitName||null,archetype:named.archetype||null,
            counts:Object.fromEntries(STATES.map(x=>[x,0])),games:0,runs:[]
          });
          const row=buckets.get(named.id);
          row.games++;row.counts[run.outcome.status]++;
          row.runs.push({run,group});
        }
      }
    }
    return [...buckets.values()].sort((a,b)=>
      b.counts.win-a.counts.win||
      b.counts.win/b.games-a.counts.win/a.games||
      b.games-a.games||a.label.localeCompare(b.label));
  }
  function knockoutRound(run,seat){
    for(let i=1;i<run.life_history.length;i++){
      const row=run.life_history[i],before=run.life_history[i-1];
      if(row.new_eliminations.some(e=>Number(e.seat)===seat)||
         (lifeAt(before,seat)>0&&lifeAt(row,seat)<=0))
        return row.round;
    }
    return null;
  }
  function matchupMetrics(bucket){
    const terminal=bucket.runs.map(x=>x.run).filter(r=>
      r.outcome.complete&&["win","loss","draw"].includes(r.outcome.status));
    const won=terminal.filter(r=>r.outcome.status==="win");
    const losses=bucket.runs.map(x=>x.run).filter(r=>r.outcome.status==="loss");
    const pilotKnockouts=losses.map(r=>knockoutRound(r,0))
      .filter(Number.isFinite);
    const opposingKnockouts=bucket.runs.map(({run})=>
      [1,2,3].map(seat=>knockoutRound(run,seat))
        .filter(Number.isFinite).sort((a,b)=>a-b)[0])
      .filter(Number.isFinite);
    const lastLife=bucket.runs.map(({run})=>
      lifeAt(run.life_history.at(-1),0)).filter(Number.isFinite);
    const median=values=>quantile(values,.5);
    return {
      games:bucket.games,
      wins:bucket.counts.win,losses:bucket.counts.loss,
      draws:bucket.counts.draw,unresolved:bucket.counts.unresolved,
      notEvaluated:bucket.counts.not_evaluated,
      winShare:bucket.games?bucket.counts.win/bucket.games:0,
      medianFinishRound:median(terminal.map(r=>r.completed_rounds)),
      finishedGames:terminal.length,
      medianPilotKnockoutRound:median(pilotKnockouts),
      pilotKnockouts:pilotKnockouts.length,
      medianVictoryRound:median(won.map(r=>r.completed_rounds)),
      victoryGames:won.length,
      medianFirstOpponentKnockoutRound:median(opposingKnockouts),
      gamesWithOpponentKnockout:opposingKnockouts.length,
      medianLastPilotLife:median(lastLife)
    };
  }
  function textButton(label,cls,onclick){
    const b=create("button",cls,label);
    b.type="button";b.onclick=onclick;return b;
  }
  function card(title,kicker,number,detail,childBuilder){
    const panel=create("details","board-report game-outcome-card");
    const summary=create("summary","game-outcome-summary");
    const copy=create("div","game-outcome-summary-copy");
    copy.append(create("span","board-kicker",kicker),
      create("strong","game-outcome-title",title),
      create("span","game-outcome-number",number),
      create("span","game-outcome-caption",detail),
      create("span","board-open","Explore →"));
    summary.appendChild(copy);panel.appendChild(summary);
    const body=create("div","game-outcome-body");
    childBuilder(body);
    panel.appendChild(body);
    return panel;
  }
  function limitationsDisclosure(){
    const details=create("details","game-outcome-limits");
    const trigger=create("summary",null,"ⓘ");
    trigger.setAttribute("aria-label","Model limitations and what improves accuracy");
    trigger.title="Early modeled results · limitations";
    const content=create("div","game-outcome-limits-content");
    content.append(
      create("strong",null,"Early model · interpret with care"),
      create("p",null,"Small samples, unfinished games, incomplete rules and automated pilot choices can change these results."),
      create("p",null,"The current opposing seats are abstract policies, not complete Commander decks. Archetype portraits are illustrative unless a real opposing commander was recorded."),
      create("p",null,"Next improvements: more matched seeds, fuller card rules, improved piloting, and validated opposing deck simulations."));
    details.append(trigger,content);
    return details;
  }
  function outcomeCard(group,options,childBuilder){
    const wrapper=create("div","game-outcome-hero-frame");
    const panel=create("details","board-report game-outcome-card game-outcome-hero");
    const summary=create("summary","game-outcome-summary game-outcome-hero-summary");
    if(typeof options.commanderArt==="string"&&options.commanderArt){
      const art=create("img","game-outcome-hero-art");
      art.src=options.commanderArt;
      art.alt="";
      art.loading="lazy";
      art.referrerPolicy="no-referrer";
      summary.appendChild(art);
    }
    const copy=create("div","game-outcome-hero-copy");
    copy.append(create("span","board-kicker","Long-game outcomes"),
      create("strong","game-outcome-title","Game Outcomes"));
    const numbers=create("div","game-outcome-hero-stats");
    const short=[["win","Wins"],["loss","Losses"],["unresolved","Unresolved"]];
    for(const [state,label] of short){
      const metric=create("div","game-outcome-hero-stat is-"+state);
      const share=(100*group.counts[state]/group.total);
      metric.append(create("strong",null,Number(share.toFixed(1))+"%"),
        create("span",null,label+" · "+group.counts[state]+"/"+group.total));
      numbers.appendChild(metric);
    }
    copy.appendChild(numbers);
    if(options.heroHighlights?.length){
      const highlights=create("div","game-outcome-hero-highlights");
      for(const item of options.heroHighlights){
        const stat=create("button","game-outcome-hero-highlight");
        stat.type="button";
        stat.setAttribute("aria-haspopup","dialog");
        stat.setAttribute("aria-label",item.label+": "+item.value+". Open detailed analysis");
        stat.append(create("span",null,item.label),
          create("strong",null,item.value),
          create("small",null,item.detail),
          create("span","game-outcome-hero-highlight-cue","Explore ↗"));
        // The tiles live inside a <summary>; clicking them must not toggle
        // the surrounding outcome disclosure.
        stat.addEventListener("click",event=>{
          event.preventDefault();event.stopPropagation();
          options.onHighlightClick?.(item.key,stat);
        });
        highlights.appendChild(stat);
      }
      copy.appendChild(highlights);
    }
    const bar=create("div","game-outcome-stacked-bar");
    bar.setAttribute("role","img");
    bar.setAttribute("aria-label",STATES.map(state=>
      stateLabel(state)+" "+group.counts[state]+" of "+group.total).join(", "));
    for(const state of STATES){
      if(!group.counts[state])continue;
      const segment=create("span","is-"+state);
      segment.style.width=(100*group.counts[state]/group.total)+"%";
      bar.appendChild(segment);
    }
    copy.append(bar,create("span","board-open",
      group.total+" modeled games · Explore opponent results →"));
    summary.appendChild(copy);
    panel.appendChild(summary);
    const body=create("div","game-outcome-body");
    childBuilder(body);
    panel.appendChild(body);
    // The icon is a sibling so it remains operable while the game card is closed.
    wrapper.append(panel,limitationsDisclosure());
    return wrapper;
  }
  function metricTile(label,value,detail){
    const item=create("div","game-outcome-insight-metric");
    item.append(create("span",null,label),
      create("strong",null,value===null||value===undefined?"—":
        typeof value==="string"?value:nfmt(value)),
      create("small",null,detail));
    return item;
  }
  function matchupExplorer(parent,groups,options={}){
    const title=create("div","game-outcome-explorer-intro");
    title.append(create("strong",null,"Most wins → Fewest wins"));
    parent.appendChild(title);
    if(!groups.length){
      parent.appendChild(create("p","micro","No recorded opposing groups yet."));
      return;
    }
    if(groups.length===1)parent.appendChild(create("p","micro",
      "One opponent type recorded"));
    const layout=create("div","game-outcome-explorer");
    const portrait=create("div","game-outcome-opponent-portrait");
    const rankSide=create("div","game-outcome-ranking-side");
    const nav=create("div","game-outcome-rank-nav");
    const previous=textButton("← Previous","game-outcome-rank-prev",()=>pick(selected-1,true));
    const next=textButton("Next →","game-outcome-rank-next",()=>pick(selected+1,true));
    const position=create("span","micro");
    nav.append(previous,position,next);
    const ranking=create("div","game-outcome-ranking");
    ranking.setAttribute("role","group");
    ranking.setAttribute("aria-label","Opponent groups sorted by observed modeled wins");
    const rows=groups.map((bucket,i)=>{
      const button=textButton("","game-outcome-rank-row",()=>pick(i,true));
      const header=create("div","game-outcome-rank-label");
      header.append(create("strong",null,bucket.title||bucket.label),
        create("span",null,bucket.counts.win+" win"+(bucket.counts.win===1?"":"s")+
          " · "+bucket.games+" games · "+Math.round(100*bucket.counts.win/bucket.games)+"%"));
      const track=create("div","game-outcome-rank-track");
      const fill=create("span","game-outcome-rank-fill");
      fill.style.width=(100*bucket.counts.win/bucket.games)+"%";
      track.appendChild(fill);
      button.append(header,track);
      button.setAttribute("aria-label",
        (bucket.title||bucket.label)+": "+bucket.counts.win+
        " wins in "+bucket.games+" modeled games");
      ranking.appendChild(button);
      return button;
    });
    rankSide.append(nav,ranking);
    layout.append(portrait,rankSide);
    parent.appendChild(layout);
    const metrics=create("div","game-outcome-insight-grid");
    const seeds=create("div","game-outcome-seeds");
    const evidence=create("div","game-outcome-evidence");
    parent.append(metrics,
      create("strong",null,"Example games"),seeds,evidence);
    let selected=0;
    function pick(index,scroll=false){
      if(index<0||index>=groups.length)return;
      selected=index;
      const bucket=groups[index],values=matchupMetrics(bucket);
      position.textContent=(index+1)+" / "+groups.length;
      previous.disabled=index===0;
      next.disabled=index===groups.length-1;
      rows.forEach((row,i)=>row.setAttribute("aria-pressed",String(i===index)));
      if(scroll&&rows[index].scrollIntoView)
        rows[index].scrollIntoView({block:"nearest"});
      portrait.replaceChildren();
      const art=typeof options.portraitFor==="function"?options.portraitFor(bucket):null;
      if(art?.art){
        const img=create("img","game-outcome-opponent-art");
        img.src=art.art;img.alt=art.name+" card illustration";
        img.loading="lazy";img.referrerPolicy="no-referrer";
        portrait.appendChild(img);
      }else{
        portrait.appendChild(create("div","game-outcome-art-missing","✧"));
      }
      const caption=create("div","game-outcome-portrait-label");
      caption.append(create("strong",null,bucket.title||bucket.label),
        create("small",null,art?.name?
          art.name+(bucket.kind==="named"?" · recorded opposing commander":
            " · illustrative archetype portrait"):
          "No cached commander art"));
      portrait.appendChild(caption);
      caption.appendChild(create("span","game-outcome-portrait-kind",
        bucket.kind==="named"?"Observed in pod":"Illustrative portrait"));
      metrics.replaceChildren(
        metricTile("Games",values.games,"Observed"),
        metricTile("Win share",Math.round(values.winShare*100)+"%",
          values.wins+" win · "+values.losses+" loss · "+values.unresolved+" unresolved"+
          (values.draws?" · "+values.draws+" draw":"")),
        metricTile("Median finish",values.medianFinishRound,
          values.finishedGames+" completed"),
        metricTile("Our knockout round",values.medianPilotKnockoutRound,
          values.pilotKnockouts+" knockouts"),
        metricTile("Victory round",values.medianVictoryRound,
          values.victoryGames+" wins"),
        metricTile("First opponent out",values.medianFirstOpponentKnockoutRound,
          values.gamesWithOpponentKnockout+" games"),
        metricTile("Final life",values.medianLastPilotLife,
          "Median recorded")
      );
      seeds.replaceChildren();evidence.replaceChildren();
      const samples=[
        ...bucket.runs.filter(({run,group})=>group.exampleBySeed.has(run.seed)),
        ...bucket.runs.filter(({run,group})=>!group.exampleBySeed.has(run.seed))
      ].slice(0,6);
      for(const {run,group} of samples){
        const button=textButton("Seed "+run.seed+" · "+stateLabel(run.outcome.status),
          "game-outcome-seed",()=>runDetails(evidence,run,{
            example:group.exampleBySeed.get(run.seed),
            onShowRecordedActions:options.onShowRecordedActions
          }));
        seeds.appendChild(button);
      }
      if(bucket.runs.length>samples.length)
        seeds.appendChild(create("span","micro",bucket.runs.length+
          " games · All seeds in Turn reviewer"));
      if(typeof options.onReviewRun==="function"){
        const {run,group}=bucket.runs[0];
        seeds.appendChild(textButton("Open turn reviewer ↓",
          "game-outcome-review-link",()=>options.onReviewRun(group.id,run.seed)));
      }
    }
    pick(0);
  }
  function stateLabel(status){
    return ({win:"Win",loss:"Loss",draw:"Draw",unresolved:"Unresolved",
      not_evaluated:"Not evaluated"})[status]||status;
  }
  function roundLabel(run){
    return run.outcome.complete?"finished in round "+run.completed_rounds:
      "through round "+run.completed_rounds;
  }
  function countsChart(parent,group,filter){
    const bars=create("div","game-outcome-buckets");
    for(const status of STATES){
      const count=group.counts[status];
      if(!count)continue;
      const row=textButton(stateLabel(status)+" · "+count+" / "+group.total,
        "game-outcome-bucket is-"+status,()=>filter(status));
      row.appendChild(create("span","game-outcome-bucket-bar"));
      row.lastChild.style.width=(100*count/group.total)+"%";
      bars.appendChild(row);
    }
    parent.appendChild(bars);
  }
  // Every card statistic is computed from the active manifest's complete,
  // named turn observations. A cast counts once per recorded action, with
  // separate per-game counts and evidence for median summaries/drilldowns.
  const BASIC_LANDS=new Set(["plains","island","swamp","mountain","forest",
    "wastes","snow-covered plains","snow-covered island","snow-covered swamp",
    "snow-covered mountain","snow-covered forest"]);
  const CAST_TYPES=new Set(["creature_cast","artifact_cast","enchantment_cast",
    "tutor_cast","token_spell_cast","reviewed_draw_spell_cast",
    "reviewed_ritual_cast","reviewed_buyback_cast","reviewed_flashback_cast",
    "reviewed_escape_cast","reviewed_graveyard_spell_cast",
    "reviewed_copy_spell_cast","reviewed_instant_response",
    "reviewed_commander_cast","reviewed_generic_spell_cast",
    "provisional_spell_cast","reviewed_common_spell_resolved",
    "reviewed_zone_spell_resolved","land_play"]);
  function observationCardStats(runs,lookupCard=()=>null,commanderName=null){
    const kinds=["played","creature","instant","spell","artifact","enchantment",
      "land","seen","seenCreature","unplayed","activated","removal","creatureKills","damage","longest","finisher","tutorFound","tutorUsed"];
    const maps=Object.fromEntries(kinds.map(k=>[k,new Map()]));
    const complete=runs.filter(run=>Array.isArray(run.ui_observations)&&
      run.ui_observations.length===run.completed_rounds);
    let confirmedTutors=0;
    // Only actual resolved searches with an explicitly named found card
    // count. A cast alone, ambiguous search, or old stripped projection
    // cannot establish a successfully resolved tutor search.
    function basic(name){
      const printed=lookupCard(name);
      const normalized=String(name||"").trim().toLowerCase();
      // Commanders live in the command zone and have guaranteed access:
      // they are not ordinary draw/play-frequency observations.
      return (!!commanderName&&normalized===String(commanderName).trim().toLowerCase())||
        BASIC_LANDS.has(normalized)||
        /\bBasic\b/i.test(String(printed?.type_line||"").split("—")[0]);
    }
    function record(kind,name,run,turn,quantity=1,extra={}){
      if(typeof name!=="string"||!name.trim()||
         (!["tutorFound","tutorUsed"].includes(kind)&&basic(name)))return;
      const map=maps[kind];
      if(!map.has(name))map.set(name,{name,counts:new Map(),seen:new Set(),
        events:[],durations:[],turns:[]});
      const item=map.get(name);
      if(Number.isFinite(quantity)&&quantity>0)
        item.counts.set(run,(item.counts.get(run)||0)+quantity);
      item.seen.add(run);
      if(Number.isFinite(turn)){
        item.turns.push(turn);
        item.events.push({seed:run.seed,turn,run,...extra});
      }
    }
    for(const run of complete){
      const seen=new Set((run.opening_hand||[]).filter(n=>!basic(n)));
      const casts=new Set();
      const held=new Map();
      // These turn-end snapshots cannot distinguish multiple copies of the
      // same card name. One card name contributes at most once per round.
      for(const row of run.ui_observations){
        for(const name of new Set(row.hand||[])){
          if(basic(name))continue;
          seen.add(name);
          held.set(name,(held.get(name)||0)+1);
        }
        for(const [eventIndex,action] of (row.actions||[]).entries()){
          if(action.type==="tutor_resolved"&&
             (action.seat===undefined||Number(action.seat)===0)&&
             typeof action.card==="string"&&action.card.trim()&&
             typeof action.target_name==="string"&&action.target_name.trim()){
            confirmedTutors++;
            const provenance={eventIndex,tutor:action.card,
              target:action.target_name,destination:action.destination||null};
            // The target may be a basic land, which is entirely legitimate
            // for an unrestricted tutor. Do not apply ordinary-card exclusions.
            record("tutorFound",action.target_name,run,row.turn,1,provenance);
            record("tutorUsed",action.card,run,row.turn,1,provenance);
          }
          if(action.type==="draw"&&action.card&&!basic(action.card)){
            seen.add(action.card);
            record("seen",action.card,run,row.turn,0,{eventIndex});
          }
          const name=action.card;
          if(CAST_TYPES.has(action.type)&&name&&!basic(name)){
            casts.add(name);seen.add(name);
            const card=lookupCard(name);
            const types=String(card?.type_line||card?.category||"").split("—")[0];
            record("played",name,run,row.turn,1,{eventIndex});
            for(const [kind,pattern] of [
              ["creature",/\bCreature\b/i],["instant",/\bInstant\b/i],
              ["spell",/\b(Instant|Sorcery)\b/i],["artifact",/\bArtifact\b/i],
              ["enchantment",/\bEnchantment\b/i],["land",/\bLand\b/i]])
              if(pattern.test(types))
                record(kind,name,run,row.turn,1,{eventIndex});
          }
          if((/activated|trigger/.test(action.type||""))&&
              (action.card||action.source))
            record("activated",action.card||action.source,run,row.turn,1,{eventIndex});
          if(Number.isFinite(action.destroyed_count)&&action.destroyed_count>0&&
              (action.card||action.source))
            record("removal",action.card||action.source,run,row.turn,
              action.destroyed_count,{eventIndex});
          if(Number.isFinite(action.creatures_killed)&&action.creatures_killed>0&&
              (action.card||action.source))
            record("creatureKills",action.card||action.source,run,row.turn,
              action.creatures_killed,{eventIndex});
          // Do not infer player damage/finishing blows from unattributed
          // life deltas. Both require a named source and explicit provenance.
          if(action.target_seat>0&&
              (action.seat===undefined||Number(action.seat)===0)&&
              Number.isFinite(action.life_lost)&&
              action.life_lost>0&&(action.card||action.source))
            record("damage",action.card||action.source,run,row.turn,
              action.life_lost,{eventIndex});
          if(action.type==="reviewed_finishing_blow"&&
              (action.seat===undefined||Number(action.seat)===0)&&
              (action.card||action.source))
            record("finisher",action.card||action.source,run,row.turn,1,{eventIndex});
        }
      }
      for(const name of seen){
        record("seen",name,run,null,1);
        const types=String(lookupCard(name)?.type_line||"").split("—")[0];
        if(/\bCreature\b/i.test(types))record("seenCreature",name,run,null,1);
        if(!casts.has(name))record("unplayed",name,run,null,1);
        // A card cast on the draw turn contributes zero held rounds.
        // Across seen games, include zeros so medians are not inflated.
        const rounds=held.get(name)||0;
        record("longest",name,run,null,rounds);
        maps.longest.get(name).durations.push(rounds);
      }
    }
    const mean=a=>a.length?a.reduce((t,x)=>t+x,0)/a.length:0;
    function sort(kind){
      return [...maps[kind].values()].map(item=>{
        const counts=[...item.counts.values()];
        const seen=item.seen.size;
        const score=kind==="longest"?mean(item.durations):
          kind==="seen"||kind==="seenCreature"||kind==="unplayed"?seen:
          ["removal","creatureKills","damage","tutorFound","tutorUsed"].includes(kind)?
            counts.reduce((t,x)=>t+x,0):
            counts.filter(x=>x>0).length;
        const perGame=kind==="longest"?item.durations:
          complete.map(run=>item.counts.get(run)||0);
        return {...item,score,average:mean(perGame),
          median:quantile(perGame,.5),
          games:counts.filter(x=>x>0).length,
          eventCount:counts.reduce((t,x)=>t+x,0),
          heldMedian:quantile(item.durations,.5)};
      }).filter(item=>item.score>0).sort((a,b)=>
        b.score-a.score||b.average-a.average||
        b.games-a.games||a.name.localeCompare(b.name));
    }
    const ranked=Object.fromEntries(kinds.map(k=>[k,sort(k)]));
    return {coverage:complete.length,total:runs.length,
      confirmedTutors,ranked,
      ...Object.fromEntries(kinds.map(k=>[k,ranked[k][0]||null]))};
  }
  function renderObservationZones(root,observation,options={}){
    if(!observation)return;
    const box=create("div","game-outcome-observed-zones");
    box.appendChild(create("strong",null,"Recorded hand, board and actions"));
    const zones=[["Hand",observation.hand],["Battlefield",observation.battlefield],
      ["Graveyard",observation.graveyard]];
    for(const [label,names] of zones){
      const details=create("details","game-outcome-observed-zone");
      details.appendChild(create("summary",null,label+" · "+(names?.length||0)));
      const list=create("div","game-outcome-observed-cards");
      if(!names?.length)list.appendChild(create("span","micro","None recorded"));
      for(const name of names||[]){
        const button=create("button","game-outcome-recorded-card",name);
        button.type="button";button.onclick=()=>options.onOpenRecordedCard?.(name);
        list.appendChild(button);
      }
      details.appendChild(list);box.appendChild(details);
    }
    const actions=create("details","game-outcome-observed-zone");
    actions.appendChild(create("summary",null,
      "Ordered actions · "+(observation.actions?.length||0)));
    for(const a of observation.actions||[]){
      if(a.type==="untap")continue;
      const label=[a.type?.replaceAll("_"," "),a.card||a.source||a.operation,
        a.seat===undefined?"":"seat "+(Number(a.seat)+1)]
        .filter(Boolean).join(" · ");
      actions.appendChild(create("p","micro",label));
    }
    box.appendChild(actions);
    root.appendChild(box);
  }
  function turnSpotlight(observation,lookupCard=()=>null){
    // The backdrop represents an actual named pilot action in THIS round.
    // Opposing or unattributed events must not become implied pilot plays.
    if(!observation||!Array.isArray(observation.actions))return null;
    const actions=observation.actions.filter(action=>
      action&&typeof action.card==="string"&&action.card.trim()&&
      (action.seat===undefined||Number(action.seat)===0)&&
      !String(action.type||"").startsWith("opponent_")&&
      (CAST_TYPES.has(action.type)||String(action.type||"").endsWith("_cast")||
       /activated|trigger|resolved|removal|damage/.test(String(action.type||""))));
    const weight=action=>{
      const type=String(action.type||"");
      if(type==="reviewed_commander_cast")return 5;
      if(type==="land_play")return 1;
      if(CAST_TYPES.has(type)||type.endsWith("_cast"))return 4;
      if(/removal|damage|activated|trigger|resolved/.test(type))return 3;
      return 2;
    };
    const ordered=[...actions].sort((a,b)=>weight(b)-weight(a));
    for(const action of ordered){
      const card=lookupCard(action.card);
      const art=card?.art||card?.image;
      if(typeof art==="string"&&/^https:\/\//.test(art)){
        return {name:action.card,art,action:action.type};
      }
    }
    return null;
  }
  function turnActionHighlight(observation,spotlight){
    if(!observation)return "Starting life and opening hand";
    const actions=(observation.actions||[]).filter(a=>
      (a.seat===undefined||Number(a.seat)===0)&&
      !String(a.type||"").startsWith("opponent_"));
    const drew=actions.filter(a=>a.type==="draw").length;
    const played=actions.filter(a=>a.card&&
      (CAST_TYPES.has(a.type)||String(a.type||"").endsWith("_cast")));
    const parts=[];
    if(drew)parts.push("Drew "+drew);
    if(spotlight)parts.push(
      (spotlight.action==="land_play"?"Played ":"Cast or activated ")+spotlight.name);
    else if(played.length)parts.push("Played "+played.length+" named card"+
      (played.length===1?"":"s"));
    if(played.length>1)parts.push(played.length+" plays");
    if(!parts.length)parts.push(actions.length?
      actions.length+" recorded actions":"No named plays recorded");
    return parts.join(" · ");
  }

  // Inline insight evidence uses the original compact, expandable turn rows.
  // A round is NOT a reconstructed priority/phase transcript: only explicit
  // action metadata permits naming a phase or an opposing seat.
  function seatChangeSummary(current,before,observation){
    const table=create("section","insight-seat-summary");
    table.appendChild(create("strong","insight-seat-summary-title",
      "End-of-round life & recorded combat"));
    const strip=create("div","insight-seat-summary-strip");
    const actions=observation?.actions||[];
    const changes=current?.life_changes||[];
    for(const seat of SEATS){
      const value=lifeAt(current,seat),old=before?lifeAt(before,seat):value;
      const diff=Number.isFinite(value)&&Number.isFinite(old)?value-old:null;
      const entry=create("div","insight-seat-line");
      entry.appendChild(create("strong","insight-seat-name",
        seat===0?"You":"Seat "+(seat+1)));
      const metrics=create("span","insight-seat-metrics");
      const hp=create("span","insight-seat-chip"+(diff?
        diff>0?" is-gain":" is-loss":""),"♥ "+nfmt(value)+
        (diff?" ("+(diff>0?"+":"")+diff+")":""));
      hp.title="Recorded life total at round end";
      metrics.appendChild(hp);
      // This is confirmed damage RECEIVED, not inferred damage dealt by
      // this player; the source actor is not always available.
      const taken=changes.filter(change=>Number(change.seat)===seat&&
        change.kind==="damage"&&Number.isFinite(change.amount))
        .reduce((sum,change)=>sum+change.amount,0);
      if(taken){
        const badge=create("span","insight-seat-chip is-loss","⚔ −"+taken);
        badge.title="Recorded unprevented damage received this round";
        metrics.appendChild(badge);
      }
      // Blocked combat is shown only when its actor is identified; a
      // block record is not a numerical measure of toughness or prevention.
      const blocks=actions.filter(a=>Number(a.seat)===seat&&
        /blocked_combat|combat_blocked|block_declared/.test(String(a.type||""))).length;
      if(blocks){
        const badge=create("span","insight-seat-chip is-defense","◈ "+blocks+" blocked");
        badge.title="Recorded blocked-combat events, not damage prevented";
        metrics.appendChild(badge);
      }
      if(!aliveAt(current,seat))
        metrics.appendChild(create("span","insight-seat-chip is-eliminated","Eliminated"));
      entry.appendChild(metrics);strip.appendChild(entry);
    }
    table.appendChild(strip);
    table.appendChild(create("span","micro",
      "♥ life and round change · ⚔ confirmed damage received · ◈ blocked combat events. Damage dealt by a particular seat and defensive strength are not inferred from life changes."));
    return table;
  }
  // Single source-grounded narration vocabulary for collapsed and expanded turns.
  // Successful spell resolutions are not repeated after their casts.
  function narratedAction(a){
    if(!a||typeof a!=="object")return null;
    const type=String(a.type||"");
    const card=typeof a.card==="string"&&a.card.trim()?a.card:
      typeof a.source==="string"&&a.source.trim()?a.source:null;
    const target=typeof a.target_name==="string"&&a.target_name.trim()?a.target_name:null;
    if(type==="draw")return {verb:"Drew",card};
    if(type==="land_play")return {verb:"Played",card};
    if(type==="cleanup_discard"||type==="opponent_abstract_discard")
      return {verb:"Discarded",card};
    if(/countered|counter_spell|spell_counter/.test(type))
      return {verb:"Countered",card};
    if(/returned?_to_hand|bounce/.test(type))
      return {verb:"Returned to hand",card};
    if(/_exile|exiled|exile_/.test(type))
      return {verb:"Exiled",card};
    if(/blocked_combat|combat_blocked|block_declared/.test(type))
      return {verb:"Blocked",card};
    if(/_destroy|destroyed|_dies|died/.test(type))
      return {verb:"Destroyed",card};
    if(type==="tutor_resolved")
      return target?{verb:"Found",card:target,detail:card?"with "+card:null}:null;
    if(type==="reviewed_unearth_resolved"||type==="reviewed_attachment_reanimated")
      return {verb:"Returned to battlefield",card};
    if(type==="reviewed_removal_resolved")
      return {verb:"Used removal",card};
    if(type==="reviewed_instant_response")
      return {verb:"Played",card};
    if(type.endsWith("_cast")||type==="reviewed_graveyard_creature_cast")
      return {verb:"Played",card};
    if(type.endsWith("_resolved")||type==="untap"||type==="draw_step"||
       type==="provisional_enter_resolved")return null;
    // Retain an unfamiliar recorded action without calling it a play.
    return {verb:type.replaceAll("_"," "),card};
  }
  function narratedText(n){
    return [n.verb,n.card,n.detail].filter(Boolean).join(" ");
  }
  function turnNarration(actions){
    const list=(actions||[]).map(narratedAction).filter(Boolean);
    const parts=[];
    for(const a of list){
      if(a.verb==="Played"&&parts.length&&parts[parts.length-1].verb==="Played"&&
         a.card&&!a.detail){
        parts[parts.length-1].names.push(a.card);
      }else parts.push({verb:a.verb,names:a.card?[a.card]:[],detail:a.detail});
    }
    return parts.map(p=>p.verb+(p.names.length?" "+p.names.join(", "):"")+
      (p.detail?" "+p.detail:"")).join(", ");
  }
  function observedZoneChanges(previous,current){
    if(!previous||!current)return [];
    // Exact names seen departing one zone and arriving in another.
    // No claim about cause, controller, timing, or a particular spell.
    const changes=[];
    const counts=arr=>{
      const tally=new Map();
      for(const name of arr)if(typeof name==="string")
        tally.set(name,(tally.get(name)||0)+1);
      return tally;
    };
    for(const [from,to] of [
      ["battlefield","graveyard"],["battlefield","exile"],
      ["battlefield","hand"],["hand","graveyard"]]){
      if(![previous[from],previous[to],current[from],current[to]].every(Array.isArray))
        continue;
      const bFrom=counts(previous[from]),bTo=counts(previous[to]);
      const aFrom=counts(current[from]),aTo=counts(current[to]);
      for(const [name,number] of bFrom){
        if(number-(aFrom.get(name)||0)>0 &&
           (aTo.get(name)||0)-(bTo.get(name)||0)>0)
          changes.push({verb:"Moved from "+from+" to "+to,card:name});
      }
    }
    return changes;
  }
  function compactInsightTimeline(root,run,options={}){
    root.replaceChildren();
    const head=create("div","game-outcome-evidence-head");
    head.append(create("strong",null,"Seed "+run.seed+" · "+stateLabel(run.outcome.status)),
      create("span","micro",roundLabel(run)));
    root.appendChild(head);
    root.appendChild(create("p","micro",
      "Player and enemy activity grouped from recorded events. Opponent pressure is abstract; round-end changes do not identify individual enemy turns."));
    const timeline=create("div","insight-turn-timeline");
    root.appendChild(timeline);
    const life=run.life_history||[];
    for(let index=0;index<life.length;index++){
      const observation=index?run.ui_observations?.[index-1]:null;
      const previous=index>1?run.ui_observations?.[index-2]:null;
      const current=life[index],before=index?life[index-1]:null;
      const row=create("details","insight-turn-row");
      const firstCard=index===0?(run.opening_hand||[])[0]:
        (observation?.actions||[]).find(a=>
          typeof (a.card||a.source)==="string"&&
          (a.card||a.source).trim())?.card||
        (observation?.actions||[]).find(a=>
          typeof a.source==="string"&&a.source.trim())?.source;
      const firstArt=firstCard&&options.lookupRecordedCard?.(firstCard);
      const image=firstArt?.art||firstArt?.image;
      if(typeof image==="string"&&/^https:\/\//.test(image)){
        const cover=create("img","insight-turn-cover");
        cover.src=image;cover.alt="";cover.loading="lazy";
        cover.referrerPolicy="no-referrer";row.appendChild(cover);
      }
      if(Number.isInteger(options.focusTurn)&&options.focusTurn===index)row.open=true;
      const summary=create("summary","insight-turn-row-summary");
      summary.appendChild(create("strong","insight-turn-label",
        index?"Turn "+index:"Opening"));
      const pilot=(observation?.actions||[]).filter(a=>
        a.seat===undefined||Number(a.seat)===0);
      const synopsis=turnNarration(pilot);
      summary.appendChild(create("span","insight-turn-activity",
        index?synopsis||"No named plays recorded":"Kept opening hand"));
      const badges=create("span","insight-turn-metrics");
      const now=lifeAt(current,0),was=before?lifeAt(before,0):now;
      const delta=now-was;
      const hp=create("span","insight-turn-metric"+(before&&delta?
        delta>0?" is-gain":" is-loss":""),"♥ "+nfmt(now)+
        (before&&delta?" ("+(delta>0?"+":"")+nfmt(delta)+")":""));
      badges.appendChild(hp);
      for(const [label,key] of [["▤","hand"],["♟","battlefield"],["◆","graveyard"]]){
        const present=observation?.[key];
        if(!Array.isArray(present))continue;
        const earlier=previous?.[key];
        const diff=Array.isArray(earlier)?present.length-earlier.length:null;
        badges.appendChild(create("span","insight-turn-metric"+(diff?
          diff>0?" is-gain":" is-loss":""),label+" "+present.length+
          (diff?" ("+(diff>0?"+":"")+diff+")":"")));
      }
      summary.appendChild(badges);
      const arrow=create("span","insight-turn-expand","Explore ▾");
      summary.appendChild(arrow);
      row.appendChild(summary);
      const body=create("div","insight-turn-row-body");
      if(index===0){
        const initial=run.opening_hand||[];
        body.appendChild(create("p","micro",
          initial.length+" cards in recorded opening hand"));
        const cards=create("div","insight-action-cards");
        for(const name of initial)cards.appendChild(insightActionCard(name,options));
        body.appendChild(cards);
      }else if(!observation){
        body.appendChild(create("p","micro",
          "Action and zone details were not exported for this round."));
      }else{
        const actions=observation.actions||[];
        if(!actions.length)body.appendChild(create("p","micro",
          "No individual actions recorded for this round."));
        // Two stable sections: recorded player activity and a single
        // condensed enemy block. Never infer intra-round phase ordering.
        const own=actions.filter(a=>Number(a.seat)===0);
        const enemy=actions.filter(a=>Number.isInteger(a.seat)&&a.seat>0);
        const unknown=actions.filter(a=>!Number.isInteger(a.seat));
        function actionSection(title,events,cssClass,showSeat){
          events=events.filter(a=>narratedAction(a));
          if(!events.length)return;
          const section=create("section","insight-action-phase "+cssClass);
          section.appendChild(create("h4","insight-action-phase-heading",
            title+" · "+events.length+" recorded actions"));
          const items=create("div","insight-action-sequence");
          for(const a of events){
            const spoken=narratedAction(a);
            if(!spoken)continue;
            const line=create("div","insight-action-entry");
            if(showSeat)line.appendChild(create("strong","insight-action-seat-label",
              "Seat "+(Number(a.seat)+1)));
            const text=create("span","insight-action-description");
            text.appendChild(create("span","insight-action-verb",spoken.verb+" "));
            if(spoken.card)text.appendChild(insightActionCard(spoken.card,options,{textOnly:true}));
            if(spoken.detail)text.appendChild(create("span",null," "+spoken.detail));
            if(spoken.card){
              const printed=options.lookupRecordedCard?.(spoken.card);
              if(typeof (printed?.art||printed?.image)==="string")
                line.appendChild(insightActionCard(spoken.card,options,{artOnly:true}));
            }
            line.appendChild(text);
            items.appendChild(line);
          }
          section.appendChild(items);body.appendChild(section);
        }
        actionSection("Your recorded actions",own,"is-player",false);
        actionSection("Enemy activity (consolidated)",enemy,"is-opponent",true);
        actionSection("Seat not recorded",unknown,"is-unattributed",false);
        const moves=observedZoneChanges(previous,observation);
        if(moves.length){
          const section=create("section","insight-action-phase is-zone-changes");
          section.appendChild(create("h4","insight-action-phase-heading",
            "Observed zone movement · "+moves.length));
          const items=create("div","insight-action-sequence");
          for(const move of moves){
            const line=create("div","insight-action-entry");
            line.appendChild(insightActionCard(move.card,options,{artOnly:true}));
            const description=create("span","insight-action-description");
            description.appendChild(create("span",null,move.verb+" "));
            description.appendChild(insightActionCard(move.card,options,{textOnly:true}));
            line.appendChild(description);items.appendChild(line);
          }
          section.appendChild(items);body.appendChild(section);
        }
        const zones=create("details","insight-turn-zones");
        zones.appendChild(create("summary",null,"End-of-round hand, battlefield and graveyard"));
        renderObservationZones(zones,observation,options);
        body.appendChild(zones);
      }
      body.appendChild(seatChangeSummary(current,before,observation));
      const recordedChanges=current.life_changes||[];
      if(index&&recordedChanges.length){
        const lifeSection=create("section","insight-action-phase is-life");
        lifeSection.appendChild(create("h4","insight-action-phase-heading",
          "Recorded life changes · "+recordedChanges.length));
        for(const entry of recordedChanges){
          const seat=Number(entry.seat);
          lifeSection.appendChild(create("p","micro",
            (seat===0?"You":"Seat "+(seat+1))+" · "+
            String(entry.kind||"life event").replaceAll("_"," ")+" · "+
            (entry.delta>0?"+":"")+nfmt(entry.delta)+" life"));
        }
        body.appendChild(lifeSection);
      }
      for(const eliminated of current.new_eliminations||[])
        body.appendChild(create("p","game-outcome-elimination",
          "Seat "+(Number(eliminated.seat)+1)+" eliminated · "+eliminated.cause));
      row.appendChild(body);
      timeline.appendChild(row);
    }
    if(options.example?.events?.length&&
       typeof options.onShowRecordedActions==="function"){
      const full=create("details","story-drilldown game-outcome-actions");
      full.appendChild(create("summary",null,
        "Source-level play-by-play (available example)"));
      const container=create("div","replay-root");
      full.appendChild(container);
      full.addEventListener("toggle",()=>{
        if(!full.open||full.dataset.rendered)return;
        full.dataset.rendered="1";
        options.onShowRecordedActions(container,options.example,run);
      });
      root.appendChild(full);
    }
  }
  function insightActionCard(name,options,display={}){
    const card=options.lookupRecordedCard?.(name);
    const button=textButton("","insight-action-card"+
      (display.artOnly?" is-art-only":"")+
      (display.textOnly?" is-text-only":""),
      ()=>options.onOpenRecordedCard?.(name));
    button.setAttribute("aria-label","View "+name+" card details");
    const art=card?.art||card?.image;
    if(!display.textOnly&&typeof art==="string"&&/^https:\/\//.test(art)){
      const img=create("img","insight-action-art");
      img.src=art;img.alt="";img.loading="lazy";img.referrerPolicy="no-referrer";
      button.appendChild(img);
    }
    if(!display.artOnly||!(typeof art==="string"&&/^https:\/\//.test(art)))
      button.appendChild(create("span","insight-action-name",name));
    return button;
  }
  // Canonical turn viewer used by card insights and the full-game reviewer.
  // Keep all rendering in one place to prevent divergent evidence semantics.
  function runDetails(root,run,options={}){
    return compactInsightTimeline(root,run,options);
  }
  function svgNode(name,attrs={}){
    const node=document.createElementNS("http://www.w3.org/2000/svg",name);
    for(const [k,v] of Object.entries(attrs))node.setAttribute(k,String(v));
    return node;
  }
  function lifePlot(trend){
    const width=680,height=230,left=36,right=12,top=18,bottom=32;
    const svg=svgNode("svg",{viewBox:"0 0 "+width+" "+height,
      role:"img","aria-label":"Median life by round for all four seats, with middle-half bands"});
    const plotW=width-left-right,plotH=height-top-bottom;
    const maxRound=Math.max(1,trend.at(-1)?.round||1);
    const maxLife=Math.max(40,...trend.flatMap(row=>
      SEATS.map(s=>row.seats[s].p75||0)),1);
    const yCeiling=Math.ceil(maxLife/10)*10;
    const x=r=>left+r/maxRound*plotW;
    // Life can fall below zero on lethal damage. Keep the line on the
    // chart's zero baseline, while retaining the exact negative total in
    // selected-round statistics and life-change evidence.
    const y=n=>top+plotH-(Math.max(0,n)/yCeiling)*plotH;
    for(const tick of [0,.25,.5,.75,1]){
      const value=Math.round(tick*yCeiling);
      svg.appendChild(svgNode("line",{x1:left,y1:y(value),x2:width-right,
        y2:y(value),stroke:"#5f6d68","stroke-opacity":.35}));
      const label=svgNode("text",{x:5,y:y(value)+4,fill:"#c4cbbd","font-size":11});
      label.textContent=String(value);svg.appendChild(label);
    }
    for(const seat of SEATS){
      const good=trend.filter(row=>Number.isFinite(row.seats[seat]?.median));
      if(!good.length)continue;
      const band=[...good.map(row=>[x(row.round),y(row.seats[seat].p75)]),
        ...[...good].reverse().map(row=>[x(row.round),y(row.seats[seat].p25)])];
      if(band.length>2){
        const polygon=svgNode("polygon",{points:band.map(p=>p.join(",")).join(" "),
          fill:SEAT_COLORS[seat],"fill-opacity":.13});
        svg.appendChild(polygon);
      }
      const path=svgNode("polyline",{
        points:good.map(row=>x(row.round)+","+y(row.seats[seat].median)).join(" "),
        fill:"none",stroke:SEAT_COLORS[seat],"stroke-width":2.4,
        "stroke-linejoin":"round","stroke-linecap":"round"});
      svg.appendChild(path);
    }
    for(const tick of [0,Math.round(maxRound/2),maxRound]){
      const label=svgNode("text",{x:x(tick),y:height-8,
        "text-anchor":"middle",fill:"#c4cbbd","font-size":11});
      label.textContent="R"+tick;svg.appendChild(label);
    }
    return svg;
  }
  function roundTrendDetail(root,round){
    root.replaceChildren();
    root.appendChild(create("strong",null,
      "Round "+round.round+" · "+round.observed+" of "+round.total+
      " games still observed"));
    const stats=create("div","game-outcome-life-stats");
    for(const seat of SEATS){
      const row=round.seats[seat],stat=create("div","game-outcome-life-stat");
      stat.append(create("span",null,seat===0?"You":"Seat "+(seat+1)),
        create("strong",null,row.median.toFixed(1).replace(/\.0$/,"")+
          " median"),
        create("small",null,"IQR "+row.p25.toFixed(1)+"–"+row.p75.toFixed(1)+
          " · alive "+row.alive+"/"+round.observed));
      stats.appendChild(stat);
    }
    root.appendChild(stats);
  }
  function histogram(root,runs,maxRound){
    const counts=new Map();
    for(const run of runs){
      if(!run.outcome.complete)continue;
      counts.set(run.completed_rounds,(counts.get(run.completed_rounds)||0)+1);
    }
    if(!counts.size){
      root.appendChild(create("span","micro","No finished games"));return;
    }
    const highest=Math.max(...counts.values());
    const plot=create("div","game-outcome-finish-bars");
    const all=[...counts].sort((a,b)=>a[0]-b[0]);
    for(const [round,count] of all){
      const bar=create("div","game-outcome-finish-row");
      bar.appendChild(create("span",null,"R"+round));
      const track=create("div","game-outcome-finish-track");
      const fill=create("span","game-outcome-finish-fill");
      fill.style.width=(count/highest*100)+"%";
      track.appendChild(fill);
      bar.append(track,create("strong",null,count));
      plot.appendChild(bar);
    }
    root.appendChild(plot);
  }
  function turnReviewer(root,groups,options={}){
    root.replaceChildren();
    const choices=create("div","game-outcome-review-controls");
    const scenarioSelect=create("select","game-outcome-scenario-select");
    scenarioSelect.setAttribute("aria-label","Choose opponent scenario");
    const seedSelect=create("select","game-outcome-scenario-select");
    seedSelect.setAttribute("aria-label","Choose recorded game seed");
    const available=groups.filter(g=>g.runs.length);
    if(!available.length){root.textContent="No recorded games.";return}
    for(const group of available){
      const option=create("option",null,group.scenario+" · "+
        group.runs.length+" games");
      option.value=group.id;
      scenarioSelect.appendChild(option);
    }
    choices.append(scenarioSelect,seedSelect);
    const evidence=create("div","game-outcome-evidence game-outcome-review-evidence");
    root.append(choices,evidence);
    let active=available[0];
    let focusTurn=null;
    function showSeed(){
      const run=active.runs.find(r=>String(r.seed)===String(seedSelect.value));
      if(!run)return;
      runDetails(evidence,run,{example:active.exampleBySeed.get(run.seed),
        onShowRecordedActions:options.onShowRecordedActions,
        onOpenRecordedCard:options.onOpenRecordedCard,
        lookupRecordedCard:options.lookupRecordedCard,
        focusTurn:focusTurn});
    }
    function showGroup(seed,turn=null){
      focusTurn=turn;
      active=available.find(g=>g.id===scenarioSelect.value)||available[0];
      seedSelect.replaceChildren();
      for(const run of active.runs){
        const option=create("option",null,"Seed "+run.seed+" · "+
          stateLabel(run.outcome.status)+" · Round "+run.completed_rounds);
        option.value=String(run.seed);
        seedSelect.appendChild(option);
      }
      const firstExample=active.runs.find(run=>active.exampleBySeed.has(run.seed));
      seedSelect.value=String(seed??(firstExample||active.runs[0]).seed);
      showSeed();
    }
    scenarioSelect.addEventListener("change",()=>showGroup());
    seedSelect.addEventListener("change",showSeed);
    showGroup();
    return function jump(id,seed,turn=null){
      const group=available.find(g=>g.id===id);
      if(!group)return;
      scenarioSelect.value=id;
      showGroup(seed,turn);
      if(options.reviewerPanel?.scrollIntoView)
        options.reviewerPanel.scrollIntoView({behavior:"smooth",block:"start"});
    };
  }

  function insightCategoryLabel(kind){
    return ({
      played:"Most played card",creature:"Most played creature",
      instant:"Most cast instant",spell:"Most cast instant or sorcery",
      artifact:"Most played artifact",enchantment:"Most played enchantment",
      land:"Most played nonbasic land",seen:"Most frequently seen card",
      seenCreature:"Most frequently seen creature",
      unplayed:"Most often left unplayed",activated:"Most used ability",
      removal:"Most permanents destroyed",
      creatureKills:"Most creature kills",damage:"Most damage to opponents",
      longest:"Longest held in hand",finisher:"Finishing blow",
      tutorFound:"Most tutored card",tutorUsed:"Most used tutor"
    })[kind]||kind;
  }
  function cardPerformancePanel(kind,ranked,coverage,groups,options,onReviewRun){
    const winner=ranked[0];
    if(!winner)return null;
    const isHeld=kind==="longest",isCount=["seen","seenCreature","unplayed","played",
      "creature","instant","spell","artifact","enchantment","land"].includes(kind);
    // Headlines should remain comparable across different batch sizes.
    // Binary access/cast metrics use distinct-game share; repeatable event
    // metrics use per-game averages (two decimals), never raw totals.
    const isTutor=kind==="tutorFound"||kind==="tutorUsed";
    const tutorCount=options.tutorSearchCount||0;
    const valueFor=item=>isTutor?
      (100*item.eventCount/Math.max(1,tutorCount)).toFixed(1)+"%":
      isHeld?nfmt(item.heldMedian)+" rounds":
      isCount?(100*item.games/coverage).toFixed(1)+"%":
      item.average.toFixed(2)+"/game";
    const displayValue=item=>valueFor(item);
    const cardData=item=>options.lookupRecordedCard?.(item.name)||null;
    let initialSelect=null;
    const panel=card(insightCategoryLabel(kind),"Card insight",
      displayValue(winner),winner.name,body=>{
        const sub=create("p","micro",isTutor?
          "Percentage of confirmed, named tutor resolutions. Select a card to inspect the search and its recorded turn.":
          isHeld?"Ranked by mean rounds held when seen; the displayed duration is the median.":
          "Select a bar to explore that card's stats and recorded turns.");
        body.appendChild(sub);
        const compare=create("div","insight-featured-compare");
        const featured=create("div","insight-featured-selected");
        const ranking=create("div","insight-featured-ranking");
        compare.append(featured,ranking);body.appendChild(compare);
        const stats=create("div","insight-featured-stats");
        const evidence=create("div","insight-featured-evidence");
        body.append(stats,evidence);
        const bars=[];
        const maxScore=Math.max(1,...ranked.slice(0,10).map(item=>item.score));
        function select(item){
          // The summary and the full-card preview always reflect the exact
          // selected contender, never a fixed image of the original winner.
          updateSummary(item);
          for(const button of bars)
            button.setAttribute("aria-pressed",
              String(button.dataset.card===item.name));
          featured.replaceChildren();stats.replaceChildren();
          evidence.replaceChildren();
          const printed=cardData(item);
          const art=printed?.image||printed?.art;
          if(art){
            const imageButton=textButton("","insight-featured-card-art",
              ()=>options.onOpenRecordedCard?.(item.name));
            imageButton.setAttribute("aria-label","View "+item.name+" card details");
            const image=create("img",null);
            image.src=art;image.alt=item.name+" card artwork";
            image.loading="lazy";image.referrerPolicy="no-referrer";
            imageButton.appendChild(image);
            featured.appendChild(imageButton);
          }
          featured.appendChild(create("strong","insight-featured-card-name",item.name));
          const cost=manaCost(item);
          if(cost)featured.appendChild(cost);
          featured.appendChild(textButton("View card details ↗",
            "game-outcome-recorded-card",
            ()=>options.onOpenRecordedCard?.(item.name)));
          const tileSet=create("div","game-outcome-insight-grid");
          tileSet.append(
            metricTile(isTutor?"Share of tutor searches":
              isHeld?"Median rounds held":"Median per game",
              isTutor?valueFor(item):
                isHeld?nfmt(item.heldMedian):nfmt(item.median),
              isTutor?tutorCount+" confirmed searches":
                isHeld?item.seen.size+" games seen":coverage+" games"),
            metricTile("Games recorded",item.games,coverage+" games"),
            metricTile(isTutor?"Confirmed searches":"Total recorded",item.eventCount,
              isTutor?tutorCount+" total searches":"Relevant actions"),
            metricTile("Median event turn",quantile(item.turns,.5),
              "When individually recorded"));
          stats.appendChild(tileSet);
          const samples=[...item.events].sort((a,b)=>
            a.turn-b.turn||a.seed-b.seed).slice(0,12);
          const examples=create("div","insight-card-examples");
          if(samples.length){
            evidence.appendChild(create("strong","insight-evidence-heading",
              "Jump to recorded turn"));
            for(const hit of samples){
              const parent=groups.find(g=>g.runs.includes(hit.run));
              if(!parent)continue;
              examples.appendChild(textButton(
                "Seed "+hit.seed+" · Turn "+hit.turn+
                  (isTutor?" · "+(kind==="tutorFound"?hit.tutor+" → "+item.name:
                    item.name+" → "+hit.target):""),
                "game-outcome-review-link",
                ()=>onReviewRun(parent.id,hit.seed,hit.turn)));
            }
          }else if(["unplayed","longest","seen"].includes(kind)){
            evidence.appendChild(create("strong","insight-evidence-heading",
              "Inspect a recorded hand"));
            for(const matchingRun of [...item.seen].slice(0,8)){
              const parent=groups.find(g=>g.runs.includes(matchingRun));
              if(!parent)continue;
              examples.appendChild(textButton(
                "Seed "+matchingRun.seed+" · Inspect hand",
                "game-outcome-review-link",
                ()=>onReviewRun(parent.id,matchingRun.seed,1)));
            }
          }
          if(examples.children.length)evidence.appendChild(examples);
          // The inline tracker uses the exact same runDetails projection as
          // the full reviewer; neither hand nor life changes are inferred.
          const relevant=[...new Map([
            ...item.events.map(hit=>[hit.run,hit.turn]),
            ...[...item.seen].map(run=>[run,1])
          ]).entries()].filter(([run])=>
            Array.isArray(run?.life_history)&&run.life_history.length>1)
            .slice(0,12).map(([run,turn])=>({
              run,turn,group:groups.find(g=>g.runs.includes(run))
            })).filter(entry=>entry.group);
          if(relevant.length){
            const tracker=create("details","insight-inline-tracker");
            const summary=create("summary",null,
              "Relevant games & turn tracker · "+relevant.length+
              (relevant.length===1?" game":" games"));
            tracker.appendChild(summary);
            const controls=create("div","insight-inline-tracker-controls");
            const selectRun=create("select","game-outcome-scenario-select");
            selectRun.setAttribute("aria-label","Choose a relevant recorded game");
            relevant.forEach((entry,index)=>{
              const option=create("option",null,entry.group.scenario+
                " · Seed "+entry.run.seed+" · "+stateLabel(entry.run.outcome.status));
              option.value=String(index);selectRun.appendChild(option);
            });
            const detailsRoot=create("div","insight-inline-tracker-review");
            controls.append(selectRun);
            const full=textButton("Open in full reviewer ↗",
              "game-outcome-review-link",()=>{
                const entry=relevant[Number(selectRun.value)]||relevant[0];
                onReviewRun(entry.group.id,entry.run.seed,entry.turn);
              });
            controls.appendChild(full);
            tracker.append(controls,detailsRoot);
            const draw=()=>{
              const entry=relevant[Number(selectRun.value)]||relevant[0];
              runDetails(detailsRoot,entry.run,{
                focusTurn:entry.turn,
                lookupRecordedCard:options.lookupRecordedCard,
                onOpenRecordedCard:options.onOpenRecordedCard,
                example:entry.group.exampleBySeed?.get(entry.run.seed),
                onShowRecordedActions:options.onShowRecordedActions
              });
            };
            selectRun.addEventListener("change",draw);
            tracker.addEventListener("toggle",()=>{
              if(tracker.open)draw();
            });
            evidence.appendChild(tracker);
          }
        }
        ranking.append(
          create("strong","insight-featured-chart-title","Top cards"),
          create("p","micro",
            isTutor?"Bars compare the share of confirmed searches for each card.":
            isHeld?"Mean rounds held sets bar length; median shown beside each card.":
            isCount?"Bars compare the share of complete games featuring the card.":
              "Bars compare recorded actions per complete game."));
        const barList=create("div","insight-featured-bars");
        ranking.appendChild(barList);
        for(const item of ranked.slice(0,10)){
          const button=textButton("","insight-featured-bar",
            ()=>select(item));
          button.dataset.card=item.name;
          button.setAttribute("aria-label","Show "+item.name+" performance");
          button.setAttribute("aria-pressed","false");
          const caption=create("span","insight-featured-bar-caption");
          caption.append(create("span",null,item.name),
            create("strong",null,valueFor(item)));
          const track=create("span","insight-featured-bar-track");
          const fill=create("span","insight-featured-bar-fill");
          fill.style.width=Math.max(1,100*item.score/maxScore)+"%";
          track.appendChild(fill);
          button.append(caption,track);barList.appendChild(button);
          bars.push(button);
        }
        initialSelect=()=>select(winner);
      });
    panel.className+=" insight-card-with-evidence insight-featured-panel";
    const summary=panel.children[0];
    const copy=summary.children[0];
    const title=create("strong","game-outcome-title",insightCategoryLabel(kind));
    const subtitle=create("span","insight-head-subtitle");
    const featuredName=create("span","insight-head-name",winner.name);
    const costSlot=create("span","insight-head-mana");
    subtitle.append(featuredName,costSlot);
    const number=create("span","game-outcome-number",displayValue(winner));
    copy.replaceChildren(create("span","board-kicker","Card insight"),
      title,subtitle,number,create("span","board-open","Compare cards and evidence →"));
    const cover=create("img","insight-featured-cover");
    cover.alt="";cover.loading="lazy";cover.referrerPolicy="no-referrer";
    summary.appendChild(cover);
    function manaCost(item){
      const value=cardData(item)?.mana_cost;
      if(!value)return null;
      const holder=create("span","insight-head-mana");
      const rendered=options.renderMana?.(value);
      if(rendered)holder.appendChild(rendered);
      else holder.textContent=value;
      return holder;
    }
    function updateSummary(item){
      featuredName.textContent=item.name;
      number.textContent=displayValue(item);
      costSlot.replaceChildren();
      const cost=manaCost(item);
      if(cost)for(const child of cost.children.length?cost.children:[cost])
        costSlot.appendChild(child);
      const art=cardData(item)?.art||cardData(item)?.image;
      if(art){cover.src=art;cover.hidden=false}
      else{cover.removeAttribute("src");cover.hidden=true}
    }
    if(initialSelect)initialSelect();
    return panel;
  }
  function readablePredictor(feature){
    const name=String(feature||"");
    if(name.includes(" × ")){
      return name.split(" × ").map(readablePredictor).join(" when facing ");
    }
    if(name.startsWith("opening:"))
      return name.slice(8)+" in the opening hand";
    if(name.startsWith("hand_at_landmark:"))
      return name.slice(17)+" in hand at the landmark round";
    if(name.startsWith("opponent_count:"))
      return name.slice(15)+" opponents at the table";
    if(name.startsWith("opponent_present:"))
      return "Facing a "+name.slice(17)+" opponent";
    return name.replaceAll("_"," ").replaceAll(":"," · ");
  }
  function elasticNetPanel(analysis,options={}){
    if(analysis?.status!=="ready"||!Array.isArray(analysis.findings)||
       !analysis.findings.length)
      return card("Performance patterns","Exploratory elastic net","Unavailable",
        "Not enough supported outcome variation for this model",
        body=>body.appendChild(create("p","micro",
          "This analysis is available when the current batch supports a validated regression.")));
    // Duplicate presence/count encodings of the same singleton opponent
    // represent one story, not two distinct substantive discoveries.
    const seen=new Set();
    const findings=analysis.findings.filter(f=>{
      const key=String(f.feature||"").replace(/^opponent_count:/,"opponent:")
        .replace(/^opponent_present:/,"opponent:");
      if(seen.has(key))return false;
      seen.add(key);return Number.isFinite(f.coefficient);
    }).slice(0,12);
    const positive=findings.filter(f=>f.coefficient>0);
    const negative=findings.filter(f=>f.coefficient<0);
    const firstCard=findings.find(f=>/^(opening:|hand_at_landmark:)/.test(f.feature));
    const headline=firstCard?
      readablePredictor(firstCard.feature)+" was associated with "+
      (firstCard.coefficient>0?"better":"worse")+" modeled outcomes.":
      "Opponent composition was associated with modeled outcomes.";
    const panel=card("What predicted performance?","Exploratory elastic net",
      findings.length+" signals",
      "Associations across "+analysis.games+" simulated games",body=>{
        body.appendChild(create("p","elastic-net-headline",headline));
        body.appendChild(create("p","micro",
          "Positive coefficients indicate higher modeled win likelihood; negative coefficients indicate lower likelihood. These are exploratory associations, not causal card effects."));
        const chart=create("div","elastic-net-coefficient-chart");
        const max=Math.max(.01,...findings.map(f=>Math.abs(f.coefficient)));
        for(const finding of findings){
          const row=create("div","elastic-net-coefficient-row");
          const title=create("span","elastic-net-predictor",readablePredictor(finding.feature));
          const axis=create("div","elastic-net-axis");
          const line=create("span","elastic-net-axis-center");
          axis.appendChild(line);
          const bar=create("span","elastic-net-effect "+(
            finding.coefficient>=0?"is-positive":"is-negative"));
          bar.style.width=Math.max(2,48*Math.abs(finding.coefficient)/max)+"%";
          bar.style.left=finding.coefficient>=0?"50%":(
            50-48*Math.abs(finding.coefficient)/max)+"%";
          axis.appendChild(bar);
          const sign=create("strong","elastic-net-effect-label",
            finding.coefficient>=0?"Higher":"Lower");
          const reliability=create("span","micro",
            Math.round(100*(finding.selection_frequency||0))+
            "% of model refits");
          row.append(title,axis,sign,reliability);
          chart.appendChild(row);
        }
        body.appendChild(chart);
        const summary=create("div","elastic-net-summary");
        summary.append(
          metricTile("Higher likelihood",positive.length,"Positive associations"),
          metricTile("Lower likelihood",negative.length,"Negative associations"),
          metricTile("Model gain",
            Number.isFinite(analysis.holdout_brier)&&
            Number.isFinite(analysis.opponent_baseline_brier)?
              nfmt(analysis.opponent_baseline_brier-analysis.holdout_brier):"—",
            "Brier reduction vs opponent-only baseline")
        );
        body.appendChild(summary);
        const details=create("details","game-outcome-observed-zone");
        details.appendChild(create("summary",null,"How to interpret these findings"));
        details.appendChild(create("p","micro",
          "Bars show relative signed penalized regression coefficients, not absolute changes in win probability. Results are correlated with game outcomes after adjustment for included predictors; selected cards were not randomized. Selection percentages describe consistency across refits, not statistical confidence or causation."));
        details.appendChild(create("p","micro",
          analysis.limitations||"Exploratory model on simulated games."));
        body.appendChild(details);
      });
    panel.className+=" elastic-net-panel";
    return panel;
  }
  function render(root,batches,options={}){
    root.replaceChildren();
    if(options.reviewerRoot)options.reviewerRoot.replaceChildren();
    const report=model(batches,options.deckKey,options.deckHash);
    if(!report.groups.length){
      root.appendChild(create("p","game-outcome-empty",
        "No current published simulations for this exact deck."));
      if(options.reviewerRoot)
        options.reviewerRoot.appendChild(create("span","micro","No recorded turns."));
      return report;
    }
    // Never silently mix rules, pilot profiles or simulation horizons.
    // The newest manifest represents one source engine revision; among its
    // compatible groups, prefer the cohort with the most recorded games.
    const cohorts=new Map();
    for(const group of report.groups){
      const key=[group.pilotStyle,group.provisionalMode,group.requestedRounds].join("|");
      if(!cohorts.has(key))cohorts.set(key,{key,groups:[],games:0});
      const entry=cohorts.get(key);
      entry.groups.push(group);entry.games+=group.total;
    }
    const cohort=[...cohorts.values()].sort((a,b)=>
      b.games-a.games||a.key.localeCompare(b.key))[0];
    const groups=cohort.groups;
    const all=groups.flatMap(group=>group.runs.map(run=>({run,group})));
    const runs=all.map(x=>x.run);
    const total=runs.length;
    const counts=Object.fromEntries(STATES.map(state=>
      [state,runs.filter(run=>run.outcome.status===state).length]));
    const finished=runs.filter(run=>run.outcome.complete);
    const wins=runs.filter(run=>run.outcome.status==="win");
    const knocked=runs.map(run=>knockoutRound(run,0)).filter(Number.isFinite);
    const enemyOut=runs.flatMap(run=>[1,2,3]
      .map(seat=>knockoutRound(run,seat)).filter(Number.isFinite));
    const lastLife=runs.map(run=>lifeAt(run.life_history.at(-1),0))
      .filter(Number.isFinite);
    const life=lifeTrend(runs,groups[0].requestedRounds);
    const matchup=matchupRows(groups,"types");
    const cards=create("div","board-grid game-outcome-grid latest-insight-grid");
    root.appendChild(cards);
    let jumpToReview=null;
    const onReviewRun=(id,seed,turn)=>{
      if(detailDialog.open)closeDialog();
      if(jumpToReview)jumpToReview(id,seed,turn);
    };
    const bestMatchup=matchup[0];
    const finishedMedian=quantile(finished.map(run=>run.completed_rounds),.5);
    const finalLifeMedian=quantile(lastLife,.5);
    const heroHighlights=[
      {key:"matchup",label:"Best matchup",value:bestMatchup?
        (100*bestMatchup.counts.win/Math.max(1,bestMatchup.games)).toFixed(1)+"%":"—",
       detail:bestMatchup?.title||"No opponent groups"},
      {key:"length",label:"Game length",value:finishedMedian===null?"—":nfmt(finishedMedian),
       detail:"Median finished rounds"},
      {key:"survival",label:"Survival",value:(100*runs.filter(run=>
          aliveAt(run.life_history.at(-1),0)).length/total).toFixed(1)+"%",
       detail:"Alive at last recorded round"},
      {key:"life",label:"Final life",value:finalLifeMedian===null?"—":nfmt(finalLifeMedian),
       detail:"Median final recorded life"}
    ];
    // The overview tiles are buttons, not duplicate expanding cards.
    // Each opens its original detailed analysis in a focus-managed dialog.
    const detailPanels=new Map();
    const detailDialog=create("dialog","game-outcome-detail-dialog");
    detailDialog.setAttribute("aria-label","Game performance details");
    const detailSurface=create("div","game-outcome-detail-surface");
    const detailHeader=create("div","game-outcome-detail-header");
    const detailHeading=create("h2","game-outcome-detail-heading");
    const closeDetail=textButton("✕","game-outcome-detail-close",()=>closeDialog());
    closeDetail.setAttribute("aria-label","Close game performance details");
    detailHeader.append(detailHeading,closeDetail);
    const detailContent=create("div","game-outcome-detail-content");
    detailSurface.append(detailHeader,detailContent);
    detailDialog.appendChild(detailSurface);
    root.appendChild(detailDialog);
    let activeTrigger=null;
    function closeDialog(){
      if(typeof detailDialog.close==="function"&&detailDialog.open)
        detailDialog.close();
      else detailDialog.removeAttribute("open");
      activeTrigger?.focus?.();
    }
    function openDetail(key,trigger){
      const panel=detailPanels.get(key);
      if(!panel)return;
      activeTrigger=trigger;
      detailHeading.textContent=({
        matchup:"Opponent Matchups",
        length:"Game Length",
        survival:"Eliminations & Survival",
        life:"Life Progression"
      })[key];
      detailContent.replaceChildren(panel);
      panel.open=true;
      if(typeof detailDialog.showModal==="function")detailDialog.showModal();
      else detailDialog.setAttribute("open","");
      closeDetail.focus?.();
    }
    detailDialog.addEventListener("close",()=>activeTrigger?.focus?.());
    detailDialog.addEventListener("click",event=>{
      if(event.target===detailDialog)closeDialog();
    });
    cards.appendChild(outcomeCard({
      counts,total,terminal:finished.length,
      terminalRounds:finished.map(run=>run.completed_rounds)
    },{...options,heroHighlights,onHighlightClick:openDetail},body=>{
      const buckets=create("div","game-outcome-buckets");
      for(const state of STATES){
        if(!counts[state])continue;
        const row=create("div","game-outcome-bucket is-"+state);
        row.append(create("strong",null,stateLabel(state)),
          create("span",null,counts[state]+" / "+total));
        const bar=create("span","game-outcome-bucket-bar");
        bar.style.width=(counts[state]/total*100)+"%";
        row.appendChild(bar);buckets.appendChild(row);
      }
      body.appendChild(buckets);
      body.appendChild(create("div","micro",groups.length+" opponent groups · "+
        groups[0].requestedRounds+"-round horizon"));
    }));
    const best=matchup[0];
    detailPanels.set("matchup",card("Opponent Types","Types & table compositions",
      best?(100*best.counts.win/Math.max(1,best.games)).toFixed(1)+"%":"—",
      best?"Win share · "+best.title+" · "+matchup.length+" opponent types":
        "No recorded groups",
      body=>{
        const selector=create("select","game-outcome-matchup-mode");
        selector.setAttribute("aria-label","Group opponent outcomes by");
        for(const [value,label] of [
          ["types","Opponent types present in pod"],
          ["compositions","Whole-table compositions"]
        ]){
          const item=create("option",null,label);
          item.value=value;selector.appendChild(item);
        }
        body.appendChild(create("p","micro",
          "A type is counted once per game when present; wins belong to the whole table."));
        body.appendChild(selector);
        const view=create("div","game-outcome-matchup-view");
        body.appendChild(view);
        const redraw=()=>{
          view.replaceChildren();
          matchupExplorer(view,matchupRows(groups,selector.value),{
            ...options,onReviewRun
          });
        };
        selector.addEventListener("change",redraw);
        redraw();
      }));
    detailPanels.set("length",card("Game Length","Finished rounds",
      quantile(finished.map(run=>run.completed_rounds),.5)===null?"—":
        nfmt(quantile(finished.map(run=>run.completed_rounds),.5)),
      "Median · "+finished.length+" finished games",
      body=>{
        const stats=create("div","game-outcome-insight-grid");
        stats.append(
          metricTile("Finished",finished.length,total+" games"),
          metricTile("Victory round",quantile(wins.map(r=>r.completed_rounds),.5),
            wins.length+" wins"),
          metricTile("Unresolved",counts.unresolved,total+" games"));
        body.appendChild(stats);
        histogram(body,finished,groups[0].requestedRounds);
      }));
    detailPanels.set("survival",card("Eliminations","Survival",
      (100*knocked.length/total).toFixed(1)+"%",
      "Our seat eliminated · "+knocked.length+" of "+total+" games",
      body=>{
        const stats=create("div","game-outcome-insight-grid");
        stats.append(
          metricTile("Our knockout",quantile(knocked,.5),
            knocked.length+" recorded"),
          metricTile("Opponent knockouts",enemyOut.length,
            "Across all three seats"),
          metricTile("Opponent knockout round",quantile(enemyOut,.5),
            enemyOut.length+" eliminations"),
          metricTile("Still alive",runs.filter(run=>
            aliveAt(run.life_history.at(-1),0)).length,total+" runs"));
        body.appendChild(stats);
        const bySeat=create("div","game-outcome-seat-bars");
        for(const seat of SEATS){
          const n=runs.filter(run=>knockoutRound(run,seat)!==null).length;
          const bar=create("div","game-outcome-seat-bar");
          bar.append(create("span",null,seat===0?"You":"Seat "+(seat+1)));
          const track=create("div","game-outcome-finish-track");
          const fill=create("span","game-outcome-finish-fill");
          fill.style.width=(n/total*100)+"%";
          track.appendChild(fill);
          bar.append(track,create("strong",null,n+"/"+total));
          bySeat.appendChild(bar);
        }
        body.appendChild(bySeat);
      }));
    detailPanels.set("life",card("Life Progression","Four seats",
      quantile(lastLife,.5)===null?"—":nfmt(quantile(lastLife,.5)),
      "Your median final recorded life",
      body=>{
        const legend=create("div","game-outcome-legend");
        for(const seat of SEATS){
          const chip=create("span",null,seat===0?"You":"Seat "+(seat+1));
          chip.style.borderColor=SEAT_COLORS[seat];legend.appendChild(chip);
        }
        body.append(legend,lifePlot(life));
        const slider=create("input","game-outcome-round-slider");
        slider.type="range";slider.min="0";
        slider.max=String(life.length-1);
        slider.value=String(Math.min(6,life.length-1));
        const detail=create("div","game-outcome-round-detail");
        const displayRound=()=>roundTrendDetail(detail,{
          ...life[Number(slider.value)],total
        });
        slider.addEventListener("input",displayRound);
        body.append(slider,detail);displayRound();
      }));
    // Game detail panels are now reached from the four overview tiles.
    // Card-specific discoveries follow the commander dashboard.
    // Missing named sources never become guessed card-level findings.
    const signals=observationCardStats(runs,options.lookupRecordedCard,
      options.commanderName);
    if(signals.coverage){
      for(const kind of ["played","creature","artifact","enchantment",
        "instant","spell","land","seen","seenCreature","unplayed","longest",
        "activated","removal","creatureKills","damage","finisher",
        ...(signals.confirmedTutors?["tutorFound","tutorUsed"]:[])]){
        const panel=cardPerformancePanel(kind,signals.ranked[kind],
          signals.coverage,groups,
          {...options,tutorSearchCount:signals.confirmedTutors},onReviewRun);
        if(panel)cards.appendChild(panel);
      }
    }else{
      cards.appendChild(create("p","game-outcome-empty",
        "Card insights require named card and hand observations from the current published batch."));
    }
    // The regression story belongs after every game/card panel, immediately
    // above the independent turn reviewer.
    cards.appendChild(elasticNetPanel(options.discoveryReport,options));
    if(options.reviewerRoot){
      jumpToReview=turnReviewer(options.reviewerRoot,groups,options);
    }
    return report;
  }
  return {FORMAT,STATES,validate,model,lifeTrend,matchupRows,matchupMetrics,
    knockoutRound,opponentDecks,observationCardStats,turnSpotlight,render};
});
