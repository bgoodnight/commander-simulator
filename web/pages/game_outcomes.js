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
  const GORGE_FORMAT="commander-gorge-outcomes-v1";
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
    const gorge=batch?.format===GORGE_FORMAT&&batch.engine==="gorge"&&
      batch.opponent_fidelity==="gorge_native_full_100_card_decks";
    const legacy=batch?.format===FORMAT&&
      batch.opponent_fidelity==="abstract_opponent_pressure_not_card_exact";
    if(!batch||(!gorge&&!legacy)||batch.schema_version!==1||
       typeof batch.deck_key!=="string"||typeof batch.deck_sha256!=="string"||
       typeof batch.scenario!=="string"||
       batch.outcomes_are_competitive_win_rates!==false||
       !Number.isInteger(batch.requested_rounds)||batch.requested_rounds<1||
       batch.requested_rounds>60||!Array.isArray(batch.runs)||
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
  function limitationsDisclosure(isGorge=false,isOmniscient=false){
    const details=create("details","game-outcome-limits");
    const trigger=create("summary",null,"ⓘ");
    trigger.setAttribute("aria-label","Model limitations and what improves accuracy");
    trigger.title=isGorge?"Gorge replay provenance and limitations":"Early modeled results · limitations";
    const content=create("div","game-outcome-limits-content");
    if(isGorge){
      content.append(
        create("strong",null,"Gorge native four-player games · limited public sample"),
        create("p",null,"All opposing seats are genuine 100-card decks with Gorge AI pilots. Results are recorded native game-over events, not calibrated win-rate estimates."),
        create("p",null,isOmniscient?
          "Synthetic omniscient mode provides named hands and draws for all four simulated players. Snapshots are at the first decision of each turn, NOT at turn end or necessarily after game over.":
          "Public replay omits private hand/draw identities. Visible board and life snapshots are at the first decision of each turn, NOT at turn end or necessarily after game over."),
        create("p",null,"Abilities are counted separately: explicit native activation pushes and pushed triggers. Ordinary mana taps are not all activation events, and the native log does not yet link every resolution and effect back to its originating ability."),
        create("p",null,"Card rankings use source-verified casts, plays, native abilities and published snapshots. They are descriptive samples, not gameplay correctness or calibrated win-rate proof."));
    }else content.append(
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
    copy.appendChild(create("strong","game-outcome-title","Game Outcomes"));
    const numbers=create("div","game-outcome-hero-stats");
    const short=[["win","Wins"],["loss","Losses"],["unresolved","Unresolved"]];
    for(const [state,label] of short){
      const metric=create(state==="win"&&options.onHighlightClick?"button":"div","game-outcome-hero-stat is-"+state);
      if(state==="win"&&options.onHighlightClick){
        metric.type="button";metric.title="Overall win rate · compare life progression in wins and losses";
        metric.setAttribute("aria-label","Overall win rate · open life progression for wins and losses");
        metric.setAttribute("aria-haspopup","dialog");
        metric.addEventListener("click",event=>{
          event.preventDefault();event.stopPropagation();
          options.onHighlightClick("winlife",metric);
        });
      }
      const share=(100*group.counts[state]/group.total);
      metric.append(create("strong",null,Number(share.toFixed(1))+"%"),
        create("span",null,label+" · "+group.counts[state]+"/"+group.total));
      numbers.appendChild(metric);
    }
    copy.appendChild(numbers);
    // Keep the outcome proportions with the percentages they describe.
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
    copy.appendChild(bar);
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
    copy.appendChild(create("span","game-outcome-hero-meta",
      options.outcomeMeta||group.total+" games"));
    summary.appendChild(copy);
    panel.appendChild(summary);
    const body=create("div","game-outcome-body");
    childBuilder(body);
    panel.appendChild(body);
    // The icon is a sibling so it remains operable while the game card is closed.
    wrapper.append(panel,limitationsDisclosure(options.isGorge,options.isOmniscient));
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
        // Missing or rate-limited external artwork must never leave a broken
        // image icon in the matchup panel.
        img.onerror=()=>{
          const missing=create("div","game-outcome-art-missing","✧");
          if(img.parentElement)img.replaceWith(missing);
          const note=caption?.querySelector?.("small");
          if(note)note.textContent="Commander illustration unavailable";
        };
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
    if(run.batch?.engine==="gorge")return "observed "+run.completed_rounds+
      " turns · native game result";
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
      "land","seen","seenCreature","unplayed","activated","triggered",
      "removal","creatureKills","damage","longest","finisher","tutorFound","tutorUsed"];
    const maps=Object.fromEntries(kinds.map(k=>[k,new Map()]));
    const complete=runs.filter(run=>Array.isArray(run.ui_observations)&&
      run.ui_observations.length===run.completed_rounds);
    let confirmedTutors=0;
    const playCounts=new Map();
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
         (!["tutorFound","tutorUsed","activated","triggered"].includes(kind)&&basic(name)))return;
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
          if(action.type==="draw"&&action.card&&!basic(action.card)&&
             (action.seat===undefined||Number(action.seat)===0)){
            seen.add(action.card);
            record("seen",action.card,run,row.turn,0,{eventIndex});
          }
          const name=action.card;
          if(name&&!basic(name)&&
             (action.type==="land_play"||action.type==="reviewed_instant_response"||
              String(action.type||"").endsWith("_cast"))&&
             (action.seat===undefined||Number(action.seat)===0))
            playCounts.set(name,(playCounts.get(name)||0)+1);
          if(CAST_TYPES.has(action.type)&&name&&!basic(name)&&
             // Gorge's source observations also include three real opponents.
             // Only the chosen deck's actions belong in its card performance.
             (run.batch?.engine!=="gorge"||
               action.seat===undefined||Number(action.seat)===0)){
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
          if(action.card||action.source){
            const ownAbility=action.seat===undefined||Number(action.seat)===0;
            if(run.batch?.engine==="gorge"){
              // Gorge ability pushes are distinct, authoritative events.
              // Only the selected controller's abilities count toward its
              // insight rankings; opponent pushes remain in the replay.
              if(ownAbility&&action.type==="ability_activated")
                record("activated",action.card||action.source,run,row.turn,1,
                  {eventIndex,sourceSeq:action.source_seq});
              if(ownAbility&&action.type==="ability_triggered")
                record("triggered",action.card||action.source,run,row.turn,1,
                  {eventIndex,sourceSeq:action.source_seq});
            }else if(/activated|trigger/.test(action.type||"")){
              // Historical Python records used the combined original tile.
              record("activated",action.card||action.source,run,row.turn,1,
                {eventIndex});
            }
          }
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
        const gorgeAbility=["activated","triggered"].includes(kind)&&
          complete.some(run=>run.batch?.engine==="gorge");
        const score=kind==="longest"?mean(item.durations):
          kind==="seen"||kind==="seenCreature"||kind==="unplayed"?seen:
          // Ability cards rank by real frequency per game, including zero
          // activations/triggers in other games. Historical modeled card
          // tiles retain their former per-game presence ordering.
          gorgeAbility?mean(complete.map(run=>item.counts.get(run)||0)):
          ["removal","creatureKills","damage","tutorFound","tutorUsed"].includes(kind)?
            counts.reduce((t,x)=>t+x,0):
            counts.filter(x=>x>0).length;
        const perGame=kind==="longest"?item.durations:
          complete.map(run=>item.counts.get(run)||0);
        return {...item,score,timesPlayed:playCounts.get(item.name)||0,average:mean(perGame),
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
  // Prefer Scryfall-derived color identity from the cached commander card.
  // The accent can vary slightly by seat so mono-black pods remain readable.
  function commanderBoardTheme(name,seat,lookup){
    const identity=lookup?.(name)?.color_identity;
    const colors=Array.isArray(identity)?
      ["W","U","B","R","G"].filter(c=>identity.includes(c)):[];
    const key=colors.join("");
    const mono={
      W:["#dbcda4","#332f29"],U:["#76b8e3","#1c3447"],
      B:["#a998c6","#302939"],R:["#e99b80","#432a2a"],
      G:["#90c59a","#203a30"]
    };
    if(colors.length===0)
      return {accent:"#829d97",wash:"#213234",identity:"Colorless or unavailable"};
    if(key==="B"){
      const variations=[
        ["#b39ac9","#30263a"],["#9a9eb8","#292b3b"],
        ["#bd91ae","#392634"],["#ac99bb","#30293b"]
      ];
      const [accent,wash]=variations[seat%variations.length];
      return {accent,wash,identity:"Black"};
    }
    if(colors.length===1){
      const [accent,wash]=mono[key];
      return {accent,wash,identity:({W:"White",U:"Blue",B:"Black",
        R:"Red",G:"Green"})[key]};
    }
    const scheme=colors.map(c=>mono[c][0]);
    return {
      accent:scheme[0],wash:"#29303e",
      gradient:"linear-gradient(105deg,"+scheme.join(",")+")",
      identity:colors.join("/")
    };
  }
  function setCommanderTheme(element,theme){
    element.style.setProperty("--commander-accent",theme.accent);
    element.style.setProperty("--commander-wash",theme.wash);
    element.style.setProperty("--commander-stripe",
      theme.gradient||"linear-gradient(90deg,"+theme.accent+","+theme.accent+")");
  }
  function seatChangeSummary(current,before){
    const strip=create("div","insight-seat-life-strip");
    for(const seat of SEATS){
      const value=lifeAt(current,seat),old=before?lifeAt(before,seat):value;
      const delta=Number.isFinite(value)&&Number.isFinite(old)?value-old:null;
      const item=create("div","insight-seat-life"+(delta?
        delta>0?" is-gain":" is-loss":""));
      item.append(create("span","insight-seat-life-name",seat===0?"You":"Seat "+(seat+1)),
        create("strong","insight-seat-life-value","♥ "+nfmt(value)),
        create("span","insight-seat-life-delta",
          delta?(delta>0?"+":"")+delta:!aliveAt(current,seat)?"Out":""));
      strip.appendChild(item);
    }
    return strip;
  }
  function enemyActivitySummary(actions){
    const enemy=(actions||[]).filter(a=>Number.isInteger(a.seat)&&a.seat>0);
    if(!enemy.length)return null;
    const kinds=[
      ["creature",a=>a.type==="creature_cast"||a.type==="reviewed_graveyard_creature_cast"],
      ["enchantment",a=>a.type==="enchantment_cast"],
      ["artifact",a=>a.type==="artifact_cast"],
      ["land",a=>a.type==="land_play"],
      ["spell",a=>typeof a.type==="string"&&a.type.endsWith("_cast")]
    ];
    const counts=new Map(),extras=[];
    for(const action of enemy){
      const found=kinds.find(([,test])=>test(action));
      if(found)counts.set(found[0],(counts.get(found[0])||0)+1);
      else if(!["ability_activated","ability_triggered"].includes(action.type)&&
        narratedAction(action))extras.push(action);
    }
    const played=[...counts].map(([kind,count])=>
      count+" "+kind+(count===1?"":"s"));
    const fragments=[];
    if(played.length)fragments.push("Enemies played "+played.join(", "));
    const activations=enemy.filter(a=>a.type==="ability_activated").length;
    const triggers=enemy.filter(a=>a.type==="ability_triggered").length;
    if(activations)fragments.push(activations+" activated "+
      (activations===1?"ability":"abilities"));
    if(triggers)fragments.push(triggers+" triggered "+
      (triggers===1?"ability":"abilities"));
    // Miscellaneous engine events are not meaningful summary categories.
    return fragments.length?fragments.join(" · "):null;
  }
  // Single source-grounded narration vocabulary for collapsed and expanded turns.
  // Successful spell resolutions are not repeated after their casts.
  function narratedAction(a){
    if(!a||typeof a!=="object")return null;
    const type=String(a.type||"");
    const card=typeof a.card==="string"&&a.card.trim()?a.card:
      typeof a.source==="string"&&a.source.trim()?a.source:null;
    const target=typeof a.target_name==="string"&&a.target_name.trim()?a.target_name:null;
    // Abstract stress events describe modeled outcomes, not identifiable
    // opposing spells. Never display raw internal event identifiers.
    if(/abstract_destroy_prevented/.test(type))
      return {verb:"Destruction prevented",card:null};
    if(/abstract_blocked_combat/.test(type))
      return {verb:"Attack blocked",card:null};
    if(/abstract_unblocked_damage/.test(type))
      return {verb:"Unblocked combat damage",card:null,
        detail:Number.isFinite(a.amount)?String(a.amount):null};
    if(/abstract_combo_loss/.test(type))
      return {verb:"Modeled combo pressure",card:null};
    if(/abstract_creature/.test(type))
      return {verb:"Opponent creature development",card:null};
    if(type==="ability_activated")
      return {verb:"Activated ability of",card};
    if(type==="ability_triggered")
      return {verb:"Triggered ability of",card};
    if(type==="draw")return {verb:"Drew",card};
    if(type==="land_play")return {verb:"Played",card};
    if(type==="cleanup_discard")return {verb:"Discarded",card};
    if(type==="opponent_abstract_discard")
      return {verb:"Opponent discarded a card",card:null};
    if(/countered|counter_spell|spell_counter/.test(type))
      return {verb:"Countered",card};
    if(/returned?_to_hand|bounce/.test(type))
      return {verb:"Returned to hand",card};
    if(/_exile|exiled|exile_/.test(type))
      return {verb:type.startsWith("opponent_abstract")?
        "Opponent exiled a permanent":"Exiled",
        card:type.startsWith("opponent_abstract")?null:card};
    if(/blocked_combat|combat_blocked|block_declared/.test(type))
      return {verb:"Blocked",card};
    if(/_destroy|destroyed|_dies|died/.test(type))
      return {verb:type.startsWith("opponent_abstract")?
        "Opponent destroyed a permanent":"Destroyed",
        card:type.startsWith("opponent_abstract")?null:card};
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
    // Unrecognized engine bookkeeping cannot be translated faithfully
    // into player-visible events. Keep it out of the narrative.
    return null;
  }
  function narratedText(n){
    return [n.verb,n.card,n.detail].filter(Boolean).join(" ");
  }
  function turnNarration(actions){
    // The header is a play summary, not the full combat/removal log.
    // Reserve damage and defensive events for the expanded turn.
    const list=(actions||[]).filter(a=>!(/damage|attack|block|prevented|combo_loss/
      .test(String(a?.type||"")))).map(narratedAction).filter(Boolean);
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
  function actionEvidenceDetail(action){
    if(!action||typeof action!=="object")return "";
    const facts=[];
    // Engine-native ability IDs remain in the data, not in the replay UI.
    if(Number.isFinite(action.life_lost)&&action.life_lost>0)
      facts.push(action.life_lost+" life lost"+
        (Number.isInteger(action.target_seat)?" by seat "+(action.target_seat+1):""));
    else if(Number.isFinite(action.amount)&&action.amount>0&&
      /damage/.test(String(action.type||"")))
      facts.push(action.amount+" damage"+
        (Number.isInteger(action.target_seat)?" to seat "+(action.target_seat+1):""));
    if(Number.isFinite(action.destroyed_count)&&action.destroyed_count>0)
      facts.push(action.destroyed_count+" permanents destroyed");
    if(typeof action.destination==="string"&&
      ["hand","graveyard","battlefield","exile"].includes(action.destination))
      facts.push("to "+action.destination);
    if(Number.isFinite(action.mana_added)&&action.mana_added>0)
      facts.push("+"+action.mana_added+" mana");
    return facts.join(" · ");
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

  function turnArtManaValue(card){
    const explicit=card?.mana_value??card?.cmc;
    if(Number.isFinite(Number(explicit))&&explicit!==null&&explicit!==undefined)
      return Number(explicit);
    const cost=card?.mana_cost;
    if(typeof cost!=="string")return null;
    const symbols=[...cost.matchAll(/\{([^}]+)\}/g)].map(m=>m[1].trim().toUpperCase());
    if(!symbols.length)return null;
    return symbols.reduce((sum,symbol)=>{
      if(/^\d+$/.test(symbol))return sum+Number(symbol);
      if(symbol==="X"||symbol==="Y"||symbol==="Z")return sum;
      if(/^\d+\//.test(symbol))return sum+Number(symbol.split("/")[0]);
      return sum+1;
    },0);
  }
  function turnArtCard(observation,openingHand,lookup){
    const hasArt=name=>{
      if(typeof name!=="string"||!name.trim())return false;
      const card=lookup?.(name);
      return typeof (card?.art||card?.image)==="string";
    };
    if(!observation)return (openingHand||[]).find(hasArt)||null;
    const plays=(observation.actions||[]).filter(a=>
      a&&typeof a.card==="string"&&a.card.trim()&&
      (a.seat===undefined||Number(a.seat)===0)&&
      !String(a.type||"").startsWith("opponent_")&&
      (a.type==="land_play"||a.type==="reviewed_instant_response"||
       String(a.type||"").endsWith("_cast"))&&hasArt(a.card));
    const nonlands=plays.filter(a=>{
      const card=lookup?.(a.card);
      const type=String(card?.type_line||"").split("—")[0];
      return a.type!=="land_play"&&!/\bLand\b/i.test(type)&&
        !BASIC_LANDS.has(a.card.trim().toLowerCase());
    });
    // Highest printed mana value is a visual spotlight, not mana spent.
    // Keep the first eligible play when values are equal or unavailable.
    if(nonlands.length){
      let best=nonlands[0],value=turnArtManaValue(lookup?.(best.card));
      for(const candidate of nonlands.slice(1)){
        const next=turnArtManaValue(lookup?.(candidate.card));
        if(next!==null&&(value===null||next>value)){
          best=candidate;value=next;
        }
      }
      return best.card;
    }
    if(plays.length)return plays[0].card;
    // When no cards were played, a named observed event still gives the
    // header a real image without inventing a cast.
    return (observation.actions||[]).map(a=>a?.card||a?.source).find(hasArt)||null;
  }
  function openingHandDescription(run){
    const handLabel=run.gorge_source?.opening_hand_boundary==="first_pending_decision_of_turn"?
      "First recorded hand":"Opening hand";
    if(run.batch?.engine==="gorge"&&Array.isArray(run.opening_hand))
      return handLabel+" · "+run.opening_hand.join(", ");
    if(run.batch?.engine==="gorge")
      return handLabel+" · "+(Number.isInteger(run.opening_hand_count)?
        run.opening_hand_count:"unknown")+" cards (identities private)";
    const hand=Array.isArray(run.opening_hand)?run.opening_hand:[];
    const mulligan=run.mulligan;
    const count=Number.isInteger(mulligan?.count)&&mulligan.count>=0?
      mulligan.count:typeof mulligan?.taken==="boolean"?(mulligan.taken?1:0):null;
    const prefix=count===0?"Kept initial hand":
      count===1?"Mulliganed once":
      count!==null?"Mulliganed "+count+" times":
      "Opening hand";
    return prefix+(hand.length?", drew "+hand.join(", "):"");
  }
  function recordedManaOutput(observation){
    // null is unavailable in historical exports; [] is recorded zero.
    const colors=observation?.mana_produced_by_color;
    if(!colors||typeof colors!=="object")return null;
    return ["W","U","B","R","G","C"].filter(k=>
      Number.isInteger(colors[k])&&colors[k]>0)
      .map(symbol=>({symbol,count:colors[symbol]}));
  }
  function manaPips(target,mana,options){
    if(mana===null){
      target.appendChild(create("span","insight-mana-unavailable","—"));
      return;
    }
    if(!mana.length){target.appendChild(create("span",null,"0"));return}
    for(const {symbol,count} of mana){
      const pip=create("span","insight-color-mana-pip");
      const art=options.renderMana?.("{"+symbol+"}");
      if(art)pip.appendChild(art);
      else pip.appendChild(create("span","insight-fallback-mana",symbol));
      if(count>1)pip.appendChild(create("span","insight-mana-count","×"+count));
      target.appendChild(pip);
    }
  }
  // Gorge records the exact token identity, but does not yet export
  // calculated token power/toughness (including counters and modifiers).
  // Only provide printed/base stats for explicitly known token kinds.
  const KNOWN_TOKENS=Object.freeze({
    "Zombie Token":{type:"Token Creature — Zombie",power:2,toughness:2,glyph:"☠",tone:"zombie"},
    "Spawn Token":{type:"Token Creature",glyph:"✺",tone:"spawn"},
    "Necron Warrior Token":{type:"Token Creature",glyph:"⚙",tone:"necron"},
    "Crab Token":{type:"Token Creature — Crab",glyph:"♋",tone:"crab"},
    "Faerie Token":{type:"Token Creature — Faerie",glyph:"✧",tone:"faerie"},
    "Clue Token":{type:"Token Artifact — Clue",glyph:"⌕",tone:"clue"},
    "Treasure Token":{type:"Token Artifact — Treasure",glyph:"◆",tone:"generic"},
    "Drake Token":{type:"Token Creature — Drake",glyph:"✧",tone:"generic"},
    "Food Token":{type:"Token Artifact — Food",glyph:"◈",tone:"generic"},
    "Blood Token":{type:"Token Artifact — Blood",glyph:"◇",tone:"generic"},
    "Gold Token":{type:"Token Artifact — Gold",glyph:"◆",tone:"generic"},
    "Map Token":{type:"Token Artifact — Map",glyph:"⌕",tone:"generic"},
    "Servo Token":{type:"Token Artifact Creature — Servo",power:1,toughness:1,glyph:"⚙",tone:"generic"},
    "Wizard Token":{type:"Token Creature — Wizard",glyph:"✦",tone:"generic"},
    "Astartes Warrior Token":{type:"Token Creature — Astartes Warrior",glyph:"♜",tone:"generic"}
  });
  function tokenInfo(name,options={}){
    if(typeof name!=="string")return null;
    if(KNOWN_TOKENS[name])return KNOWN_TOKENS[name];
    // Source flags are authoritative, including named tokens that lack a
    // 'Token' suffix. Old flattened R2 replays retain a name-only fallback.
    const sourceToken=Array.isArray(options.tokenNames)&&options.tokenNames.includes(name);
    if(sourceToken||/\btoken$/i.test(name)){
      const nativeType=options.tokenTypes?.[name];
      return {type:typeof nativeType==="string"&&nativeType.trim()?
        nativeType:"Token",glyph:"◇",tone:"generic"};
    }
    return null;
  }
  // Fetch at most once per known token identity. A token's complete official
  // printing is optional enrichment; its Gorge identity remains authoritative.
  const TOKEN_ART_PROMISES=new Map();
  function officialTokenArt(name,token){
    if(!KNOWN_TOKENS[name]||typeof fetch!=="function")return Promise.resolve(null);
    if(TOKEN_ART_PROMISES.has(name))return TOKEN_ART_PROMISES.get(name);
    const base=name.replace(/\s+Token$/i,"");
    const url="https://api.scryfall.com/cards/search?q="+
      encodeURIComponent('t:token "'+base+'"')+
      "&unique=prints&include_extras=true";
    const promise=fetch(url,{headers:{"Accept":"application/json"}})
      .then(r=>r.ok?r.json():null).then(result=>{
        const matches=Array.isArray(result?.data)?result.data.filter(card=>{
          if(card.layout!=="token"||!Array.isArray(card.image_uris?Object.keys(card.image_uris):[]))return false;
          if(!card.image_uris?.normal||!card.scryfall_uri)return false;
          const title=String(card.name||"").trim().toLowerCase();
          if(title!==base.toLowerCase()&&title!==name.toLowerCase())return false;
          if(Number.isInteger(token.power)&&String(card.power)!==String(token.power))return false;
          if(Number.isInteger(token.toughness)&&String(card.toughness)!==String(token.toughness))return false;
          const expected=String(token.type||"").split("—")[1]?.trim().toLowerCase();
          if(expected&&!String(card.type_line||"").toLowerCase().includes(expected))return false;
          return true;
        }):[];
        if(!matches.length)return null;
        const card=matches[0];
        return {name,type_line:card.type_line||token.type,
          image:card.image_uris.normal,art:card.image_uris.art_crop||null,
          scryfall:card.scryfall_uri,oracle_text:card.oracle_text||"",
          power:card.power??null,toughness:card.toughness??null,
          mana_value:card.cmc??0,mana_cost:card.mana_cost||""};
      }).catch(()=>null);
    TOKEN_ART_PROMISES.set(name,promise);
    return promise;
  }
  function groupedBattlefieldTokens(cards,options){
    const groups=new Map(),result=[];
    for(const name of cards){
      const token=tokenInfo(name,options);
      if(!token){result.push({name,count:1});continue}
      const key=String(name);
      if(!groups.has(key)){
        const group={name,count:0};groups.set(key,group);result.push(group);
      }
      groups.get(key).count++;
    }
    return result;
  }
  function recordedCardTypes(name,lookup,options={}){
    const token=tokenInfo(name,options);
    if(token)return token.type.toLowerCase().split("—")[0];
    const card=lookup?.(name);
    return String(card?.type_line||card?.type||"")
      .split("—")[0].toLowerCase();
  }
  // Each permanent belongs in exactly one zone. Artifact creatures and
  // enchantment creatures are creatures first; planeswalkers have a separate
  // area rather than being mixed with untyped permanents.
  function battlefieldZone(name,options){
    const type=recordedCardTypes(name,options.lookupRecordedCard,options);
    if(/\bcreature\b/.test(type))return "Creatures";
    if(/\bland\b/.test(type))return "Lands";
    if(/\bplaneswalker\b/.test(type))return "Planeswalkers";
    if(/\bartifact\b/.test(type))return "Artifacts";
    if(/\benchantment\b/.test(type))return "Enchantments";
    return "Other permanents";
  }
  function endStatePanel(observation,options){
    const panel=create("section","insight-end-state");
    // The recorded snapshot boundary stays in the data; the replay view
    // starts directly with the inspectable zones rather than engine notes.
    if(observation.snapshot_is_turn_end!==false)
      panel.appendChild(create("strong","insight-end-state-title","End-of-turn state"));
    if(Number.isInteger(observation.hand_count)&&!Array.isArray(observation.hand))
      panel.appendChild(create("p","micro","Hand · "+observation.hand_count+
        " cards. Individual identities are private in the public export."));
    const battlefield=Array.isArray(observation.battlefield)?observation.battlefield:[];
    const byType=new Map(["Creatures","Lands","Planeswalkers","Artifacts",
      "Enchantments","Other permanents"].map(name=>[name,[]]));
    for(const name of battlefield)
      byType.get(battlefieldZone(name,options)).push(name);
    const zones=[
      ["Exile",observation.exile],
      ["Command zone",observation.command],
      ...[...byType].map(([name,cards])=>[name,cards]),
      ["Graveyard",observation.graveyard],
      ["Hand",observation.hand]
    ];
    const typed=battlefield.length-byType.get("Other permanents").length;
    if(battlefield.length&&!typed)
      panel.appendChild(create("p","micro",
        "Card types unavailable for recorded battlefield"));
    for(const [label,cards] of zones){
      if(!Array.isArray(cards))continue;
      const group=create("details","insight-end-zone insight-board-"+label.toLowerCase().replace(/[^a-z]+/g,"-"));
      group.open=label!=="Graveyard";
      const icon=({Hand:"▤","Command zone":"♛",Creatures:"♟",Lands:"◇",
        Artifacts:"⚙",Enchantments:"✦",Planeswalkers:"♛","Other permanents":"◈",
        Graveyard:"◆",Exile:"⊘"})[label]||"◈";
      const trigger=create("summary","insight-end-zone-label");
      trigger.append(create("span","insight-end-zone-icon",icon),
        create("span",null,label+" · "+cards.length));
      group.appendChild(trigger);
      if(label==="Graveyard"&&cards.length){
        // Keep a compact, inspectable preview visible while the zone is closed.
        trigger.style.flexWrap="wrap";
        const preview=create("span","insight-graveyard-preview");
        preview.style.flexBasis="100%";
        preview.style.display="flex";preview.style.flexWrap="wrap";
        preview.style.gap="0.25rem";preview.style.marginTop="0.35rem";
        const previewNames=cards.slice(-3).reverse();
        previewNames.forEach((name,index)=>{
          const tile=insightActionCard(name,options,{});
          if(index>0)tile.style.marginLeft="-0.6rem";
          tile.style.position="relative";tile.style.zIndex=String(previewNames.length-index);
          const inspect=tile.onclick;
          tile.onclick=event=>{
            event.preventDefault();event.stopPropagation();
            if(index===0)inspect?.(event);
            else group.open=true;
          };
          if(index>0){
            tile.setAttribute("aria-label","Expand graveyard to see "+name);
            tile.title="Expand graveyard";
          }
          preview.appendChild(tile);
        });
        const syncPreview=()=>{preview.hidden=group.open;
          preview.style.display=group.open?"none":"flex";};
        group.addEventListener("toggle",syncPreview);
        trigger.appendChild(preview);
        syncPreview();
      }
      const list=create("div","insight-action-cards");
      const entries=byType.has(label)?
        groupedBattlefieldTokens(cards,options):cards.map(name=>({name,count:1}));
      for(const item of entries)list.appendChild(
        insightActionCard(item.name,options,{count:item.count}));
      if(!cards.length)list.appendChild(create("span","micro","None"));
      group.appendChild(list);panel.appendChild(group);
    }
    if(Array.isArray(observation.opponent_hands)&&!options.hideOpponentHands){
      const all=create("details","insight-end-zone insight-omniscient-opponents");
      all.appendChild(create("summary","insight-end-zone-label",
        "Opponents' hands"));
      const group=create("div","insight-omniscient-opponent-list");
      for(const player of observation.opponent_hands){
        const item=create("details","insight-end-zone");
        const named=Array.isArray(player.hand)?player.hand:[];
        item.appendChild(create("summary","insight-end-zone-label",
          "Seat "+(player.seat+1)+" · "+player.deck_key+" · Hand "+player.hand_count));
        const cards=create("div","insight-action-cards");
        for(const name of named)cards.appendChild(insightActionCard(name,options));
        if(!named.length)cards.appendChild(create("span","micro",
          player.hand===null?"Not recorded":"Empty"));
        item.appendChild(cards);group.appendChild(item);
      }
      all.appendChild(group);panel.appendChild(all);
    }
    // Mana totals are rendered in their own section before enemy turns.
    return panel;
  }
  function compactInsightTimeline(root,run,options={}){
    // Projection metadata is tied to the recorded game, not the selected deck.
    // Source-backed token identities take precedence over name heuristics.
    options={...options,
      tokenNames:run.gorge_source?.token_names||options.tokenNames,
      tokenTypes:run.gorge_source?.token_types||options.tokenTypes};
    root.replaceChildren();
    const head=create("div","game-outcome-evidence-head");
    head.append(create("strong",null,options.displayGameLabel||
      "Seed "+run.seed+" · "+stateLabel(run.outcome.status)),
      create("span","micro",roundLabel(run)));
    if(!options.hideEvidenceHead||run.batch?.engine==="gorge")root.appendChild(head);
    const timeline=create("div","insight-turn-timeline");
    root.appendChild(timeline);
    const life=run.life_history||[];
    for(let index=0;index<life.length;index++){
      const observation=index?run.ui_observations?.[index-1]:null;
      const previous=index>1?run.ui_observations?.[index-2]:null;
      const current=life[index],before=index?life[index-1]:null;
      const row=create("details","insight-turn-row");
      const firstCard=turnArtCard(observation,run.opening_hand,
        options.lookupRecordedCard);
      const firstArt=firstCard&&options.lookupRecordedCard?.(firstCard);
      const image=firstArt?.art||firstArt?.image;
      let cover=null;
      if(typeof image==="string"&&/^https:\/\//.test(image)){
        cover=create("img","insight-turn-cover");
        cover.src=image;cover.alt="";cover.loading="lazy";
        cover.referrerPolicy="no-referrer";
        // Attach art to the summary itself so it is visible while the
        // native details element is collapsed, not only when expanded.

      }
      if(Number.isInteger(options.focusTurn)&&options.focusTurn===index)row.open=true;
      const summary=create("summary","insight-turn-row-summary");
      if(cover)summary.appendChild(cover);
      summary.appendChild(create("strong","insight-turn-label",
        index?"Turn "+index:"Draw"));
      const pilot=(observation?.actions||[]).filter(a=>
        a.seat===undefined||Number(a.seat)===0);
      // Compact Gorge synopsis: show every card played individually and
      // group only repeated abilities from the SAME source card. The detailed
      // replay below preserves all events in their exact recorded order.
      const gorgeSummary=()=>{
        const ordinary=pilot.filter(a=>
          !["ability_activated","ability_triggered"].includes(a.type));
        const plays=ordinary.filter(a=>narratedAction(a)).map(a=>{
          const said=narratedAction(a);
          const type=String(a.type||"");
          const kind=type==="creature_cast"||type==="reviewed_graveyard_creature_cast"?
            "creature ":type==="artifact_cast"?"artifact ":
            type==="enchantment_cast"?"enchantment ":
            type==="land_play"?"land ":"";
          return said.verb==="Played"?
            "Played "+kind+(said.card||"card"):
            narratedText(said);
        });
        const counts=new Map();
        for(const action of pilot){
          if(!["ability_activated","ability_triggered"].includes(action.type))continue;
          const card=action.card||action.source||"unknown source";
          const key=action.type+"|"+card;
          if(!counts.has(key))counts.set(key,{type:action.type,card,count:0});
          counts.get(key).count++;
        }
        const abilities=[...counts.values()].map(({type,card,count})=>
          (count>1?count+"× ":"")+
          (type==="ability_activated"?"Activated":"Triggered")+
          " ability of "+card);
        return [plays.join(", "),abilities.length?
          (plays.length?"and then ":"")+abilities.join(", "):""]
          .filter(Boolean).join(plays.length&&abilities.length?" ":"");
      };
      const synopsis=run.batch?.engine==="gorge"?
        gorgeSummary():turnNarration(pilot);
      summary.appendChild(create("span","insight-turn-activity",
        index?synopsis||"No named plays recorded":openingHandDescription(run)));
      const badges=create("span","insight-turn-metrics");
      const now=lifeAt(current,0),was=before?lifeAt(before,0):now;
      const delta=now-was;
      const hp=create("span","insight-turn-metric","♥ "+nfmt(now));
      badges.appendChild(hp);
      const hand=index===0?run.opening_hand:observation?.hand;
      const handCount=Array.isArray(hand)?hand.length:
        index===0?run.opening_hand_count:observation?.hand_count;
      if(Number.isInteger(handCount)){
        const handBadge=textButton("▤ "+handCount,
          "insight-turn-metric insight-hand-shortcut",event=>{
            // Prevent the parent <summary> from toggling itself after we open it.
            event?.preventDefault?.();
            event?.stopPropagation?.();
            row.open=true;
            const section=body.querySelector?.(".insight-end-zone");
            if(section)section.open=true;
          });
        handBadge.setAttribute("aria-label",Array.isArray(hand)?
          "Show "+handCount+" named cards in hand":
          "Hand contains "+handCount+" cards; identities not published");
        badges.appendChild(handBadge);
      }
      if(index>0){
        const mana=recordedManaOutput(observation);
        const display=create("span","insight-turn-metric insight-turn-mana");
        display.setAttribute("aria-label","Mana generated"+(mana===null?": not recorded":""));
        if(mana===null&&run.batch?.engine==="gorge")
          display.appendChild(create("span",null,"None"));
        else
          manaPips(display,mana,options);
        badges.appendChild(display);
      }
      summary.appendChild(badges);
      const arrow=create("span","insight-turn-expand","Explore ▾");
      summary.appendChild(arrow);
      row.appendChild(summary);
      const body=create("div","insight-turn-row-body");
      if(index===0){
        if(run.batch?.engine==="gorge"&&!Array.isArray(run.opening_hand))
          body.appendChild(create("p","micro",
            "Gorge recorded "+nfmt(run.opening_hand_count)+
            " cards in the opening hand. The public replay does not include card identities or mulligan decisions."));
        else body.appendChild(endStatePanel({
          hand:run.opening_hand||[],hand_count:run.opening_hand_count,
          opponent_hands:run.opening_hands_by_seat||null,
          battlefield:[],graveyard:[],exile:[],
          snapshot_is_turn_end:run.batch?.engine==="gorge"?false:undefined,
          snapshot_note:"Starting hand at the first pending decision of the game; mulligan history was not captured."
        },{...options,openingDraw:true,isGorge:run.batch?.engine==="gorge"}));
      }else if(!observation){
        body.appendChild(create("p","micro",
          "Action and zone details were not exported for this round."));
      }else{
        const actions=observation.actions||[];
        if(!actions.length)body.appendChild(create("p","micro","No recorded plays"));
        // Missing seat attribution belongs to the pilot, ahead of enemy activity.
        const own=actions.filter(a=>!Number.isInteger(a.seat)||Number(a.seat)===0);
        const enemy=actions.filter(a=>Number.isInteger(a.seat)&&a.seat>0);
        function actionSection(title,events,cssClass,showSeat,container=body){
          events=events.filter(a=>narratedAction(a));
          if(!events.length)return;
          const section=create("section","insight-action-phase "+cssClass);
          section.appendChild(create("h4","insight-action-phase-heading",title));
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
            const evidence=actionEvidenceDetail(a);
            if(evidence)text.appendChild(create("small","insight-action-facts",evidence));
            if(spoken.card){
              const printed=options.lookupRecordedCard?.(spoken.card);
              if(typeof (printed?.art||printed?.image)==="string")
                line.appendChild(insightActionCard(spoken.card,options,{artOnly:true}));
            }
            line.appendChild(text);
            items.appendChild(line);
          }
          section.appendChild(items);container.appendChild(section);
        }
        actionSection("Your turn",own,"is-player",false);
        // Native mana events provide exact color totals, but do not
        // reliably identify individual producing permanents.
        const mana=recordedManaOutput(observation);
        const manaBlock=create("details","insight-mana-detail");
        const manaHeading=create("summary","insight-mana-summary");
        manaHeading.appendChild(create("strong",null,"Mana generated"));
        const manaTotals=create("span","insight-mana-total");
        if(mana===null&&run.batch?.engine==="gorge")
          manaTotals.appendChild(create("span",null,"None"));
        else manaPips(manaTotals,mana,options);
        manaHeading.appendChild(manaTotals);
        manaBlock.appendChild(manaHeading);
        manaBlock.appendChild(create("p","micro",mana?.length?
          "Recorded mana by color. This Gorge export does not identify which cards generated each amount.":
          "No mana production was recorded for this turn."));
        body.appendChild(manaBlock);
        // Keep the rest of the round to a single small evidence block.
        // Opponent cards are counted only from explicit cast/land events.
        const rest=create("section","insight-rest-of-turn");
        rest.appendChild(create("h4","insight-rest-title","Enemy turns"));
        // Reconstruct native opposing turns, not category totals. One section
        // per actual enemy turn, in Gorge's recorded global turn order.
        // Events by a different actor are kept in a separate response group.
        const rosterBySeat=new Map((run.opponent_decks||[]).map(entry=>
          [Number(entry.seat),entry.commander_name||entry.deck_key]));
        const enemyTurns=[];
        for(const event of actions){
          if(!Number.isInteger(event.native_turn)||event.native_turn_seat===0)
            continue;
          if(!Number.isInteger(event.native_turn_seat)||
             event.native_turn_seat<1||event.native_turn_seat>3)continue;
          let turn=enemyTurns.find(item=>item.nativeTurn===event.native_turn&&
            item.seat===event.native_turn_seat);
          if(!turn){
            turn={nativeTurn:event.native_turn,seat:event.native_turn_seat,actions:[]};
            enemyTurns.push(turn);
          }
          turn.actions.push(event);
        }
        enemyTurns.sort((a,b)=>a.nativeTurn-b.nativeTurn);
        // Group repeated activations/triggers by source, while every draw
        // and play remains separately named in recorded order.
        function enemyTurnNarration(events){
          const parts=[],abilities=new Map();
          for(const event of events){
            const said=narratedAction(event);
            if(!said)continue;
            if(["ability_activated","ability_triggered"].includes(event.type)){
              const card=said.card||"unknown source";
              const key=event.type+"|"+card;
              if(!abilities.has(key))abilities.set(key,{type:event.type,card,count:0});
              abilities.get(key).count++;
              continue;
            }
            if(!["draw","land_play"].includes(event.type)&&
               !String(event.type).endsWith("_cast")&&
               event.type!=="reviewed_instant_response")continue;
            const kind=event.type==="creature_cast"||
              event.type==="reviewed_graveyard_creature_cast"?"creature ":
              event.type==="land_play"?"land ":
              event.type==="artifact_cast"?"artifact ":
              event.type==="enchantment_cast"?"enchantment ":"";
            parts.push(said.verb==="Played"?
              "played "+kind+(said.card||"card"):
              "drew "+(said.card||"a card"));
          }
          for(const {type,card,count} of abilities.values()){
            parts.push((count>1?count+"× ":"")+
              (type==="ability_activated"?"activated":"triggered")+
              " ability of "+card);
          }
          return parts.join(", ");
        }
        if(enemyTurns.length){
          for(const enemyTurn of enemyTurns){
            const commander=rosterBySeat.get(enemyTurn.seat)||
              "Seat "+(enemyTurn.seat+1);
            const owned=enemyTurn.actions.filter(a=>a.seat===enemyTurn.seat);
            const responses=enemyTurn.actions.filter(a=>a.seat!==enemyTurn.seat);
            const turnPanel=create("details","insight-end-zone insight-enemy-turn");
            const heading=create("summary","insight-end-zone-label");
            heading.appendChild(create("strong",null,commander));
            heading.appendChild(create("span","insight-enemy-turn-summary",
              enemyTurnNarration(owned)||"No named plays recorded"));
            turnPanel.appendChild(heading);
            // Full source chronology is preserved in expandable detail.
            const detailed=create("div","insight-enemy-turn-detail");
            actionSection(commander+"'s turn",owned,"is-opponent",true,detailed);
            if(responses.length){
              const byActor=new Map();
              for(const action of responses){
                if(!byActor.has(action.seat))byActor.set(action.seat,[]);
                byActor.get(action.seat).push(action);
              }
              for(const [seat,events] of byActor){
                const name=seat===0?"You":
                  rosterBySeat.get(seat)||"Seat "+(seat+1);
                actionSection(name+" responded",events,
                  "is-opponent is-response",true,detailed);
              }
            }
            turnPanel.appendChild(detailed);
            rest.appendChild(turnPanel);
          }
        }else if(enemy.length){
          // Older exports lack native turn ownership; report attributed
          // player actions without inventing any ordering across turns.
          const grouped=new Map();
          for(const action of enemy){
            if(!grouped.has(action.seat))grouped.set(action.seat,[]);
            grouped.get(action.seat).push(action);
          }
          for(const [seat,events] of grouped){
            const name=rosterBySeat.get(seat)||"Seat "+(seat+1);
            const disclosure=create("details","insight-end-zone insight-enemy-turn");
            const heading=create("summary","insight-end-zone-label");
            heading.append(create("strong",null,name),
              create("span","insight-enemy-turn-summary",
                enemyTurnNarration(events)||"No named plays recorded"));
            disclosure.appendChild(heading);
            actionSection(name,events,"is-opponent",true,disclosure);
            rest.appendChild(disclosure);
          }
        }
        const damage=actions.filter(a=>/damage|blocked_combat|combat_blocked|block_declared/
          .test(String(a?.type||""))&&narratedAction(a));
        if(damage.length){
          const combat=create("div","insight-rest-combat");
          for(const event of damage){
            const described=narratedAction(event);
            const label=[described.verb,
              actionEvidenceDetail(event)||described.detail].filter(Boolean).join(" · ");
            combat.appendChild(create("p","insight-rest-event",label));
          }
          rest.appendChild(combat);
        }
        const board=create("section","insight-board-panel");
        board.appendChild(create("h4","insight-board-title","Board state"));
        const boardContent=create("div","insight-board-content");
        board.appendChild(boardContent);
        const states=Array.isArray(observation.board_states)?observation.board_states:null;
        const roster=new Map((run.opponent_decks||[]).map(p=>
          [Number(p.seat),p.commander_name||p.deck_key]));
        const ownCommander=run.opening_board_states?.find(p=>p.seat===0)?.command?.[0]||
          states?.find(p=>p.seat===0)?.command?.[0]||
          run.batch?.commander_name||"Your commander";
        roster.set(0,ownCommander);
        const themes=new Map(SEATS.map(seat=>
          [seat,commanderBoardTheme(roster.get(seat)||"",seat,options.lookupRecordedCard)]));
        let chosenSeat=0;
        const seatTiles=create("div","insight-seat-life-strip insight-board-seats");
        const paintBoard=()=>{
          setCommanderTheme(board,themes.get(chosenSeat));
          const selected=states?.find(p=>p.seat===chosenSeat);
          const state=selected|| (chosenSeat===0?observation:null);
          boardContent.replaceChildren();
          if(state){
            boardContent.appendChild(endStatePanel(state,{...options,
              isGorge:run.batch?.engine==="gorge",hideOpponentHands:true}));
          }else{
            boardContent.appendChild(create("p","micro",
              "No verified board state recorded for this player."));
          }
          for(const button of seatTiles.children){
            button.setAttribute("aria-pressed",
              String(Number(button.dataset.seat)===chosenSeat));
          }
        };
        for(const seat of SEATS){
          const name=roster.get(seat)||"Seat "+(seat+1);
          const tile=textButton("","insight-seat-life insight-board-seat",()=>{
            chosenSeat=seat;paintBoard();
          });
          tile.dataset.seat=String(seat);
          setCommanderTheme(tile,themes.get(seat));
          tile.title=name+" · "+themes.get(seat).identity+
            " · click to inspect this board";
          tile.appendChild(create("span","insight-seat-life-name",
            name+(seat===0?" (You)":"")));
          const value=lifeAt(current,seat);
          const old=before?lifeAt(before,seat):value;
          const change=Number.isFinite(value)&&Number.isFinite(old)?
            value-old:null;
          const totals=create("span","insight-board-life-values");
          totals.appendChild(create("strong","insight-seat-life-value",
            "♥ "+nfmt(value)));
          if(change!==null&&change!==0){
            const delta=create("span","insight-seat-life-delta "+
              (change>0?"is-gain":"is-loss"),
              (change>0?"+":"−")+nfmt(Math.abs(change)));
            delta.title="Net life change since the previous recorded state";
            delta.setAttribute("aria-label",
              (change>0?"Gained ":"Lost ")+nfmt(Math.abs(change))+" life");
            totals.appendChild(delta);
          }
          tile.appendChild(totals);
          seatTiles.appendChild(tile);
        }
        board.appendChild(seatTiles);
        paintBoard();
        const moves=observedZoneChanges(previous,observation);
        for(const move of moves){
          const line=create("p","insight-rest-event");
          line.appendChild(insightActionCard(move.card,options,{textOnly:true}));
          line.appendChild(create("span",null," · "+move.verb));
          rest.appendChild(line);
        }
        body.appendChild(rest);
        body.appendChild(board);
      }
      if(!observation){
        const rest=create("section","insight-rest-of-turn");
        rest.appendChild(create("h4","insight-rest-title","Enemy turns"));
        rest.appendChild(seatChangeSummary(current,before));
        body.appendChild(rest);
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
    const token=tokenInfo(name,options);
    const card=token?null:options.lookupRecordedCard?.(name);
    let resolvedTokenCard=null;
    const button=textButton("","insight-action-card"+
      (display.artOnly?" is-art-only":"")+
      (display.textOnly?" is-text-only":"")+
      (token?" is-token is-token-"+token.tone:""),
      ()=>{if(token)options.onOpenTokenCard?.(resolvedTokenCard||
        {name,type_line:token.type,oracle_text:"",power:token.power??null,
         toughness:token.toughness??null});
        else options.onOpenRecordedCard?.(name)});
    button.setAttribute("aria-label","View "+name+" card details");
    if(token&&!display.textOnly){
      const tokenArt=create("span","insight-token-art",token.glyph);
      tokenArt.setAttribute("aria-hidden","true");
      button.appendChild(tokenArt);
      officialTokenArt(name,token).then(official=>{
        if(!official)return;
        resolvedTokenCard=official;
        if(!button.isConnected)return;
        const img=create("img","insight-token-card-image");
        img.src=official.image;img.alt=name+" official token card";
        img.loading="lazy";img.referrerPolicy="no-referrer";
        img.onerror=()=>{resolvedTokenCard=null;img.replaceWith(tokenArt)};
        tokenArt.replaceWith(img);
      });
    }
    const art=card?.art||card?.image;
    if(!token&&!display.textOnly&&typeof art==="string"&&/^https:\/\//.test(art)){
      const img=create("img","insight-action-art");
      img.src=art;img.alt="";img.loading="lazy";img.referrerPolicy="no-referrer";
      button.appendChild(img);
    }
    if(!display.artOnly||token||!(typeof art==="string"&&/^https:\/\//.test(art))){
      const title=create("span","insight-action-name",name);
      button.appendChild(title);

    }
    if(token)button.title=token.type;
    if(token&&display.count>1){
      const quantity=create("span","insight-token-quantity","×"+display.count);
      quantity.setAttribute("aria-label",display.count+" identical tokens");
      button.appendChild(quantity);
      button.setAttribute("aria-label",display.count+" × "+button.getAttribute("aria-label"));
    }
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
      role:"img","aria-label":"Your median life by round, with middle-half band"});
    const plotW=width-left-right,plotH=height-top-bottom;
    const maxRound=Math.max(1,trend.at(-1)?.round||1);
    const maxLife=Math.max(40,...trend.flatMap(row=>
      [0].map(s=>row.seats[s].p75||0)),1);
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
    for(const seat of [0]){
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
    for(const seat of [0]){
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
  // Vertical finish-round distribution, with sparse ticks and exact counts
  // preserved as accessible bar descriptions instead of dense row labels.
  function renderGameLengthHistogram(root,entries){
    const counts=new Map();
    for(const entry of entries||[]){
      const round=Number(entry.round),games=Number(entry.games);
      if(!Number.isInteger(round)||round<0||!Number.isInteger(games)||games<=0)continue;
      counts.set(round,(counts.get(round)||0)+games);
    }
    if(!counts.size){
      root.appendChild(create("span","micro","No finished games"));return;
    }
    const rounds=[...counts.keys()].sort((a,b)=>a-b);
    const first=rounds[0],last=rounds.at(-1);
    const total=rounds.reduce((n,r)=>n+counts.get(r),0);
    const n=last-first+1;
    const binWidth=Math.max(1,Math.ceil(n/32));
    const bins=[];
    for(let low=first;low<=last;low+=binWidth){
      const high=Math.min(last,low+binWidth-1);
      let value=0;
      for(let round=low;round<=high;round++)value+=counts.get(round)||0;
      bins.push({low,high,value});
    }
    const maxCount=Math.max(1,...bins.map(bin=>bin.value));
    const plot=create("div","game-length-histogram");
    plot.setAttribute("role","img");
    plot.setAttribute("aria-label","Game length distribution across "+total+
      " finished games, from round "+first+" to round "+last);
    const bars=create("div","game-length-histogram-bars");
    // Aggregate only when the finish-round range becomes too wide for
    // legible bars. A bin remains explicit about its inclusive round range.
    for(const {low,high,value} of bins){
      const column=create("div","game-length-histogram-column");
      const bar=create("span","game-length-histogram-bar");
      bar.style.height=(value/maxCount*100)+"%";
      const label=low===high?"Round "+low:"Rounds "+low+"–"+high;
      column.title=label+": "+value+" game"+(value===1?"":"s");
      column.setAttribute("aria-label",column.title);
      column.appendChild(bar);bars.appendChild(column);
    }
    const axis=create("div","game-length-histogram-axis");
    const labelCount=Math.min(5,n);
    const ticks=new Set();
    for(let i=0;i<labelCount;i++)ticks.add(first+
      Math.round(i*(last-first)/Math.max(1,labelCount-1)));
    for(const tick of [...ticks].sort((a,b)=>a-b)){
      const label=create("span",null,"R"+tick);
      label.style.left=(n===1?50:(tick-first)/(last-first)*100)+"%";
      axis.appendChild(label);
    }
    plot.append(bars,axis);root.appendChild(plot);
  }
  function histogram(root,runs,maxRound){
    const counts=new Map();
    for(const run of runs){
      if(!run.outcome.complete)continue;
      counts.set(run.completed_rounds,(counts.get(run.completed_rounds)||0)+1);
    }
    renderGameLengthHistogram(root,[...counts].map(([round,games])=>({round,games})));
  }
  // Search and step through games without presenting an unbounded dropdown.
  function gameNavigator(root,onSelect,options={}){
    const controls=create("div","game-navigator");
    const search=create("input","game-navigator-search");
    search.type="search";search.value="";search.placeholder="Find game or opponent";
    search.setAttribute("aria-label","Find a game or opponent");
    const result=create("select","game-navigator-filter");
    result.setAttribute("aria-label","Filter games by result");
    for(const [value,label] of [["","All results"],["win","Wins"],["loss","Losses"]]){
      const option=create("option",null,label);option.value=value;result.appendChild(option);
    }
    result.value="";
    const nav=create("div","game-navigator-controls");
    const previous=textButton("‹","game-navigator-step",()=>step(-1));
    previous.setAttribute("aria-label","Previous matching game");
    const next=textButton("›","game-navigator-step",()=>step(1));
    next.setAttribute("aria-label","Next matching game");
    const status=create("span","game-navigator-status","Choose a game");
    const list=create("div","game-navigator-results");
    list.setAttribute("aria-label","Matching games");
    nav.append(previous,status,next);
    controls.append(search,result,list);root.appendChild(controls);
    // Keep the pager alongside the reviewer title, while search and result
    // filtering remain beneath the heading. Detached fixtures still work.
    (options.controlsHost||controls).appendChild(nav);
    let games=[],selected=null,filtered=[];
    function refresh(){
      const term=search.value.trim().toLowerCase();
      filtered=games.filter(game=>(!result.value||game.result===result.value)&&
        (!term||(game.search||game.label).toLowerCase().includes(term)));
      const current=filtered.findIndex(game=>game.id===selected);
      previous.disabled=current<=0;next.disabled=!filtered.length||current===filtered.length-1;
      status.textContent=selected&&current>=0?(current+1)+" of "+filtered.length:
        filtered.length?"Choose a game · "+filtered.length+" available":"No matching games";
      list.replaceChildren();
      // A short choice list stays useful on a phone even for enormous cohorts.
      const center=Math.max(0,current);const begin=Math.max(0,Math.min(center-2,filtered.length-5));
      for(const game of (term?filtered.slice(begin,begin+5):[])){
        const button=textButton(game.label,"game-navigator-game",()=>choose(game.id));
        button.setAttribute("aria-pressed",String(game.id===selected));list.appendChild(button);
      }
    }
    function choose(id,turn=null){
      const game=games.find(x=>x.id===id);if(!game)return false;
      selected=id;refresh();onSelect(game,turn);return true;
    }
    function step(direction){
      if(!filtered.length)return;
      const current=filtered.findIndex(game=>game.id===selected);
      const index=current<0?0:Math.max(0,Math.min(filtered.length-1,current+direction));
      choose(filtered[index].id);
    }
    search.addEventListener("input",refresh);result.addEventListener("change",refresh);
    refresh();
    return {setGames(items){games=items.slice();refresh()},choose,
      clearFilters(){search.value="";result.value="";refresh()}};
  }
  function turnReviewer(root,groups,options={}){
    root.replaceChildren();
    const available=groups.filter(g=>g.runs.length);
    if(!available.length){root.textContent="No recorded games.";return}
    const games=available.flatMap(group=>group.runs.map(run=>({group,run})));
    function gameLabel(entry,index){
      const enemies=opponentDecks(entry.run,entry.run.batch).map(deck=>deck.name);
      return "Game "+(index+1)+"/"+games.length+" · "+stateLabel(entry.run.outcome.status)+
        (enemies.length?" · "+enemies.join(" · "):"");
    }
    const choices=create("div","game-outcome-review-controls");root.appendChild(choices);
    const evidence=create("div","game-outcome-evidence game-outcome-review-evidence");
    root.appendChild(evidence);
    const items=games.map((entry,index)=>({id:String(index),entry,
      label:gameLabel(entry,index),result:entry.run.outcome.status,
      search:gameLabel(entry,index)+" seed "+entry.run.seed}));
    const headerNav=!options.hideGameSelector?
      (typeof document!=="undefined"&&typeof document.getElementById==="function"?
        document.getElementById("turn-reviewer-nav"):null):null;
    if(headerNav)headerNav.replaceChildren();
    const nav=gameNavigator(choices,(item,turn)=>{
      const {group,run}=item.entry;
      runDetails(evidence,run,{example:group.exampleBySeed.get(run.seed),
        onShowRecordedActions:options.onShowRecordedActions,onOpenRecordedCard:options.onOpenRecordedCard,
        onOpenTokenCard:options.onOpenTokenCard,
        lookupRecordedCard:options.lookupRecordedCard,renderMana:options.renderMana,
        focusTurn:turn,displayGameLabel:options.displayGameLabel||item.label});
    },{controlsHost:headerNav});
    nav.setGames(items);if(options.hideGameSelector)choices.hidden=true;
    const first=games.findIndex(({group,run})=>group.exampleBySeed.has(run.seed));
    nav.choose(String(first>=0?first:0),options.focusTurn??null);
    return function jump(id,seed,turn=null){
      const index=games.findIndex(({group,run})=>group.id===id&&String(run.seed)===String(seed));
      if(index<0)return;
      nav.clearFilters();nav.choose(String(index),turn);
      options.reviewerPanel?.scrollIntoView?.({behavior:"smooth",block:"start"});
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
      triggered:"Most triggered ability",
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
    const isAbility=["activated","triggered"].includes(kind)&&options.isGorge;
    const tutorCount=options.tutorSearchCount||0;
    const valueFor=item=>isTutor?
      (100*item.eventCount/Math.max(1,tutorCount)).toFixed(1)+"%":
      isHeld?nfmt(item.heldMedian)+" rounds":
      isCount?(100*item.games/coverage).toFixed(1)+"%":
      item.average.toFixed(2)+"/game";
    const displayValue=item=>valueFor(item);
    const cardData=item=>options.lookupRecordedCard?.(item.name)||null;
    let initialSelect=null;
    const panelTitle=isAbility&&kind==="activated"?
      "Most activated ability":insightCategoryLabel(kind);
    const panel=card(panelTitle,"Card insight",
      displayValue(winner),winner.name,body=>{
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
          // Selecting a card resets the example cycle, without expanding
          // the full game reviewer or forcing a scroll away from this card.
          const relevant=[];
          const used=new Set();
          const addExample=(run,turn)=>{
            if(!Array.isArray(run?.life_history)||run.life_history.length<2)return;
            const group=groups.find(g=>g.runs.includes(run));
            if(!group)return;
            const focus=Number.isInteger(turn)&&turn>=1?turn:1;
            const key=group.id+":"+run.seed+":"+focus;
            if(used.has(key))return;
            used.add(key);
            relevant.push({run,turn:focus,group});
          };
          for(const hit of [...item.events].sort((a,b)=>
            a.turn-b.turn||a.seed-b.seed))addExample(hit.run,hit.turn);
          // For metrics based on hand presence rather than named actions,
          // fall back to seen runs. Do not pad a run with a fictitious
          // second "example" at turn 1 when it already has evidence.
          const eventRuns=new Set(item.events.map(hit=>hit.run));
          for(const run of item.seen)
            if(!eventRuns.has(run))addExample(run,1);
          const examples=relevant.slice(0,12);
          if(typeof options.onReviewGame==="function")for(const entry of (item.exampleGames||[])){
            if(examples.length>=12)break;
            if(typeof entry.game_id==="string")examples.push({gameId:entry.game_id,turn:entry.turn??null});
          }
          const reviewExample=entry=>entry.gameId?
            options.onReviewGame?.(entry.gameId,entry.turn):onReviewRun(entry.group.id,entry.run.seed,entry.turn);
          let tracker=null,detailsRoot=null;
          let exampleIndex=-1;
          let draw=()=>{
            if(!tracker||!detailsRoot)return;
            const entry=examples[Math.max(0,exampleIndex)]||examples[0];
            if(!entry)return;
            runDetails(detailsRoot,entry.run,{
              focusTurn:entry.turn,
              hideEvidenceHead:true,
              lookupRecordedCard:options.lookupRecordedCard,
              renderMana:options.renderMana,
              onOpenRecordedCard:options.onOpenRecordedCard,
              onOpenTokenCard:options.onOpenTokenCard,
              example:entry.group.exampleBySeed?.get(entry.run.seed),
              onShowRecordedActions:options.onShowRecordedActions
            });
          };
          const openExample=()=>{
            if(!examples.length)return;
            exampleIndex=(exampleIndex+1)%examples.length;
            tracker.open=true;
            draw();
          };
          const tileSet=create("div","game-outcome-insight-grid insight-featured-metrics");
          for(const [label,value] of isHeld?[
            ["Median turns held",item.heldMedian],
            ["Mean turns held",item.average]
          ]:isAbility?[
            [kind==="activated"?"Recorded activations":"Recorded triggers",item.eventCount],
            ["Median event turn",quantile(item.turns,.5)]
          ]:[
            ["Times played",item.timesPlayed||0],
            ["Median event turn",quantile(item.turns,.5)]
          ]){
            const metric=create("button","game-outcome-insight-metric insight-featured-metric-link");
            metric.type="button";
            metric.setAttribute("aria-label",label+" · view next example game");
            metric.append(create("span",null,label),
              create("strong",null,value===null?"—":nfmt(value)));
            metric.disabled=!examples.length;
            metric.onclick=options.isGorge?()=>{
              if(!examples.length)return;
              exampleIndex=(exampleIndex+1)%examples.length;
              const entry=examples[exampleIndex];
              reviewExample(entry);
            }:openExample;
            tileSet.appendChild(metric);
          }
          stats.appendChild(tileSet);
          if(examples.length){
            if(options.isGorge){
              const open=textButton("View an example game ↗","game-outcome-review-link",()=>{
                const entry=examples[0];
                reviewExample(entry);
              });
              evidence.appendChild(open);
            }else{
            tracker=create("details","insight-inline-tracker insight-inline-tracker-compact");
            const trigger=create("summary",null,"View example games");
            tracker.appendChild(trigger);
            const full=textButton("Open full reviewer ↗",
              "game-outcome-review-link insight-example-full-link",()=>{
                const entry=examples[Math.max(0,exampleIndex)]||examples[0];
                onReviewRun(entry.group.id,entry.run.seed,entry.turn);
              });
            // The archived Python experiments retain their exact original
            // inline evidence presentation. Gorge uses a real-seed picker.
            if(options.isGorge){
              const controls=create("div",
                "insight-inline-tracker-controls gorge-legacy-example-controls");
              const choice=create("select","gorge-legacy-example-select");
              choice.setAttribute("aria-label","Choose a recorded source game and turn");
              examples.forEach((entry,i)=>{
                const option=create("option",null,
                  "Real decks · Seed "+entry.run.seed+" · Turn "+entry.turn+
                  " · "+stateLabel(entry.run.outcome.status));
                option.value=String(i);choice.appendChild(option);
              });
              choice.addEventListener("change",()=>{
                exampleIndex=Number(choice.value);
                draw();
              });
              controls.append(choice,full);
              detailsRoot=create("div","insight-inline-tracker-review");
              tracker.append(controls,detailsRoot);
              const previousDraw=draw;
              draw=()=>{
                choice.value=String(Math.max(0,exampleIndex));
                previousDraw();
              };
            }else{
              tracker.appendChild(full);
              const exampleLabel=create("div","insight-example-game-label");
              detailsRoot=create("div","insight-inline-tracker-review");
              tracker.append(exampleLabel,detailsRoot);
              const setLabel=()=>{
                const entry=examples[Math.max(0,exampleIndex)]||examples[0];
                exampleLabel.textContent=
                  "Scenario "+entry.group.scenario+" · Seed "+entry.run.seed+
                  " · "+stateLabel(entry.run.outcome.status);
              };
              const previousDraw=draw;
              draw=()=>{setLabel();previousDraw()};
            }
            tracker.addEventListener("toggle",()=>{
              trigger.textContent=tracker.open?"Close example games":"View example games";
              if(tracker.open)draw();
            });
            evidence.appendChild(tracker);
            }
          }
        }
        ranking.appendChild(create("strong","insight-featured-chart-title",isHeld?"Top cards · mean rounds held":"Top cards"));
        if(isHeld)ranking.appendChild(create("p","micro","The headline shows the median; bars show the mean of the same recorded holding times. Cards are ranked by mean."));
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
            create("strong",null,isHeld?nfmt(item.average)+" rounds":valueFor(item)));
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
    const title=create("strong","game-outcome-title",panelTitle);
    const subtitle=create("span","insight-head-subtitle");
    const featuredName=create("span","insight-head-name",winner.name);
    const costSlot=create("span","insight-head-mana");
    subtitle.append(featuredName,costSlot);
    const number=create("span","game-outcome-number",displayValue(winner));
    copy.replaceChildren(title,subtitle,number);
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
  // Card-based rankings share one compact, labelled set of controls.
  // Filter only using recorded card metadata, never by guessing from names.
  function filteredInsightPanel(kind,source,coverage,groups,options,onReviewRun,
                               type="all",ascending=false){
    const types=[
      ["all","All",()=>true],
      ["creature","Creature",t=>/\bcreature\b/.test(t)],
      ["artifact","Artifact",t=>/\bartifact\b/.test(t)],
      ["enchantment","Enchantment",t=>/\benchantment\b/.test(t)],
      ["spell","Instant / Sorcery",t=>/\b(instant|sorcery)\b/.test(t)],
      ["land","Land",t=>/\bland\b/.test(t)]
    ];
    const typed=item=>String(options.lookupRecordedCard?.(item.name)?.type_line||options.lookupRecordedCard?.(item.name)?.type||"").toLowerCase();
    const available=types.filter(([id,,match])=>id==="all"||
      source.some(item=>{const t=typed(item);return t&&match(t)}));
    const predicate=(available.find(([id])=>id===type)||available[0])[2];
    const items=source.filter(item=>type==="all"||predicate(typed(item))).slice()
      .sort((a,b)=>(ascending?a.score-b.score:b.score-a.score)||a.name.localeCompare(b.name));
    const panel=cardPerformancePanel(kind,items,coverage,groups,options,onReviewRun);
    if(!panel)return null;
    // Lightweight renderer contract tests provide a non-DOM stand-in for
    // insight panels; preserve the panel when DOM drilldown controls cannot
    // be attached. Actual browser panels always support querySelector.
    if(typeof panel.querySelector!=="function")return panel;
    const body=panel.querySelector(".game-outcome-body");
    if(!body)return panel;
    const controls=create("div","gorge-card-type-controls");
    controls.setAttribute("role","group");
    controls.setAttribute("aria-label","Filter and sort "+insightCategoryLabel(kind));
    const change=(next,order,label)=>{
      const replacement=filteredInsightPanel(kind,source,coverage,groups,options,onReviewRun,next,order);
      if(replacement){replacement.open=true;panel.replaceWith(replacement);
        [...replacement.querySelectorAll("button")].find(button=>button.getAttribute("aria-label")===label)?.focus();}
    };
    for(const [id,label] of available){
      const button=textButton(label,"gorge-icon-button",()=>change(id,ascending,"Filter: "+label));
      button.style.width="auto";button.style.padding="0.4rem 0.65rem";
      button.title="Filter: "+label;button.setAttribute("aria-label","Filter: "+label);
      button.setAttribute("aria-pressed",String(id===type));controls.appendChild(button);
    }
    const nextLabel=ascending?"Show highest first":"Show lowest first";
    const order=textButton(ascending?"Lowest ↑":"Highest ↓","gorge-icon-button gorge-sort-button",
      ()=>change(type,!ascending,ascending?"Show lowest first":"Show highest first"));
    order.style.width="auto";order.style.padding="0.4rem 0.65rem";
    order.title=nextLabel;order.setAttribute("aria-label",nextLabel);controls.appendChild(order);
    if(ascending)panel.querySelector(".game-outcome-title").textContent=
      insightCategoryLabel(kind).replace(/^Most /,"Least ").replace(/^Longest /,"Shortest ");
    const heading=body.querySelector(".insight-featured-chart-title");
    if(heading)heading.textContent=(ascending?"Lowest":"Highest")+" recorded cards"+
      (kind==="longest"?" · mean rounds held":"");
    body.prepend(controls);
    return panel;
  }
  function readablePredictor(feature){
    const name=String(feature||"");
    if(typeof window!=="undefined"&&window.DeckDisplayNames&&
       /^(opponent|archetype|color|seat):/.test(name))
      return window.DeckDisplayNames.feature(name);
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
    const isGorge=runs[0]?.batch?.engine==="gorge";
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
    // Use source-observed events. Never infer mana capacity from land counts or
    // treat a missing turn-five observation as zero mana.
    const commanderName=String(options.commanderName||"").trim().toLowerCase();
    const commanderArrival=run=>{
      if(!commanderName)return null;
      for(const row of run.ui_observations||[]){
        if((row.actions||[]).some(action=>
          Number(action.seat??0)===0&&
          String(action.card||"").trim().toLowerCase()===commanderName&&
          /cast/.test(String(action.type||""))))return row.turn;
      }
      return null;
    };
    const manaAtFive=run=>{
      const row=(run.ui_observations||[]).find(x=>x.turn===5);
      if(!row||!row.mana_produced_by_color)return null;
      const values=Object.values(row.mana_produced_by_color);
      if(!values.length||values.some(x=>!Number.isFinite(Number(x))))return null;
      return values.reduce((sum,x)=>sum+Number(x),0);
    };
    // An uncast commander is a right-censored arrival, not an outlier
    // to discard. Include every game in the median's denominator, and
    // return N/A if the middle observation(s) have no observed cast turn.
    const arrivalMedian=entries=>{
      if(!entries.length)return null;
      const sorted=entries.map(commanderArrival)
        .map(value=>Number.isFinite(value)?value:Infinity)
        .sort((a,b)=>a-b);
      const low=sorted[Math.floor((sorted.length-1)/2)];
      const high=sorted[Math.floor(sorted.length/2)];
      return Number.isFinite(low)&&Number.isFinite(high)?
        (low+high)/2:null;
    };
    const arrivalSamples=runs.map(commanderArrival).filter(Number.isFinite);
    const rampSamples=runs.map(manaAtFive).filter(Number.isFinite);
    const medianArrival=arrivalMedian(runs);
    const averageMana=rampSamples.length?
      rampSamples.reduce((a,b)=>a+b,0)/rampSamples.length:null;
    const heroHighlights=[
      {key:"matchup",label:"Best matchup",value:bestMatchup?
        (100*bestMatchup.counts.win/Math.max(1,bestMatchup.games)).toFixed(1)+"%":"—",
       detail:bestMatchup?.title||"No opponent groups"},
      {key:"length",label:"Game length",value:finishedMedian===null?"—":nfmt(finishedMedian),
       detail:"Median finished rounds"},
      {key:"arrival",label:"Commander arrival",value:medianArrival===null?"N/A":nfmt(medianArrival),
       detail:"Median across all "+total+" games · "+arrivalSamples.length+" casts"},
      {key:"ramp",label:"Mana ramp",value:averageMana===null?"—":averageMana.toFixed(2),
       detail:"Avg. mana generated on turn 5 · "+rampSamples.length+"/"+total+" recorded"}
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
        arrival:"Commander Arrival · Wins vs Losses",
        ramp:"Turn Five Mana · Wins vs Losses",
        winlife:"Life Progression · Wins vs Losses"
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
    const seedList=[...new Set(runs.map(run=>run.seed))]
      .filter(Number.isInteger).sort((a,b)=>a-b);
    const seedLabel=seedList.length?
      "Seeds "+(seedList[0]===seedList.at(-1)?seedList[0]:
        seedList[0]+"–"+seedList.at(-1)):"Seeds unavailable";
    const outcomeMeta=total+" games · "+groups[0].requestedRounds+
      " rounds · "+groups.length+" opponent groups · "+seedLabel+
      (runs.some(r=>r.gorge_source?.visibility==="omniscient")?
        " · Omniscient simulated hands":"");
    cards.appendChild(outcomeCard({
      counts,total,terminal:finished.length,
      terminalRounds:finished.map(run=>run.completed_rounds)
    },{...options,isGorge,isOmniscient:runs.some(r=>r.gorge_source?.visibility==="omniscient"),
       heroHighlights,outcomeMeta,onHighlightClick:openDetail},body=>{
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
    // Paired charts share one scale so red/green bar lengths are comparable.
    const comparisonBarChart=(body,measure,format)=>{
      const subsets=[
        {name:"Wins",color:"#4dab76",runs:wins},
        {name:"Losses",color:"#d66565",runs:runs.filter(r=>r.outcome.status==="loss")}
      ];
      const stats=subsets.map(group=>{
        const values=group.runs.map(measure).filter(Number.isFinite);
        return {...group,values,value:format==="median"?
          arrivalMedian(group.runs):values.length?
          values.reduce((a,b)=>a+b,0)/values.length:null};
      });
      const max=Math.max(1,...stats.map(group=>group.value||0));
      for(const item of stats){
        const line=create("div","game-outcome-seat-bar");
        line.style.margin="14px 0";
        line.appendChild(create("span",null,item.name+" · "+item.values.length+
          "/"+item.runs.length+(format==="median"?" cast":" observed")));
        const track=create("div","game-outcome-finish-track");
        track.style.height="20px";
        const bar=create("span","game-outcome-finish-fill");
        bar.style.display="block";bar.style.height="100%";
        bar.style.background=item.color;
        bar.style.width=item.value===null?"0%":(100*item.value/max)+"%";
        track.appendChild(bar);
        line.append(track,create("strong",null,item.value===null?"N/A":
          format==="mean"?item.value.toFixed(2):nfmt(item.value)));
        body.appendChild(line);
      }
    };
    detailPanels.set("arrival",card("Commander Arrival","Median first cast turn",
      medianArrival===null?"N/A":nfmt(medianArrival),
      "All games included; N/A if the median cast turn was not observed",
      body=>comparisonBarChart(body,commanderArrival,"median")));
    detailPanels.set("ramp",card("Mana Ramp","Turn five mana generated",
      averageMana===null?"—":averageMana.toFixed(2),
      "Native positive mana production on your fifth turn; missing observations excluded",
      body=>comparisonBarChart(body,manaAtFive,"mean")));
    detailPanels.set("winlife",card("Life Progression","Wins vs losses",
      counts.win+" / "+counts.loss,
      "Median life by recorded round · green wins, red losses",
      body=>{
        const categories=[
          {name:"Wins",color:"#4dab76",data:lifeTrend(wins,groups[0].requestedRounds)},
          {name:"Losses",color:"#d66565",data:lifeTrend(
            runs.filter(r=>r.outcome.status==="loss"),groups[0].requestedRounds)}
        ];
        const legend=create("div","game-outcome-legend");
        for(const item of categories){
          const chip=create("span",null,item.name);
          chip.style.borderColor=item.color;legend.appendChild(chip);
        }
        body.appendChild(legend);
        const width=680,height=240,left=42,right=16,top=15,bottom=34;
        const plotW=width-left-right,plotH=height-top-bottom;
        const maxRound=Math.max(1,...categories.flatMap(c=>c.data.map(r=>r.round)));
        const maxLife=Math.max(40,...categories.flatMap(c=>c.data.map(r=>
          r.seats[0]?.p75||0)));
        const ceiling=Math.ceil(maxLife/10)*10;
        const x=round=>left+round/maxRound*plotW;
        const y=life=>top+plotH-Math.max(0,life)/ceiling*plotH;
        const svg=svgNode("svg",{viewBox:"0 0 "+width+" "+height,
          role:"img","aria-label":"Median life progression for wins in green and losses in red"});
        for(const frac of [0,.25,.5,.75,1]){
          const value=Math.round(ceiling*frac);
          svg.appendChild(svgNode("line",{x1:left,y1:y(value),x2:width-right,
            y2:y(value),stroke:"#7a817e","stroke-opacity":.3}));
          const tick=svgNode("text",{x:7,y:y(value)+4,fill:"#c4cbbd","font-size":11});
          tick.textContent=String(value);svg.appendChild(tick);
        }
        for(const item of categories){
          const points=item.data.filter(r=>Number.isFinite(r.seats[0]?.median));
          if(!points.length)continue;
          svg.appendChild(svgNode("polyline",{
            points:points.map(r=>x(r.round)+","+y(r.seats[0].median)).join(" "),
            fill:"none",stroke:item.color,"stroke-width":3,
            "stroke-linecap":"round","stroke-linejoin":"round"}));
        }
        for(const round of [0,Math.round(maxRound/2),maxRound]){
          const tick=svgNode("text",{x:x(round),y:height-8,
            "text-anchor":"middle",fill:"#c4cbbd","font-size":11});
          tick.textContent="R"+round;svg.appendChild(tick);
        }
        body.appendChild(svg);
        body.appendChild(create("p","micro",
          "Each round includes only games with an observed snapshot at that round. "+
          "Survivorship can change the plotted cohort over time."));
      }));
    // Game detail panels are now reached from the four overview tiles.
    // Card-specific discoveries follow the commander dashboard.
    // Missing named sources never become guessed card-level findings.
    // Gorge key insights must use a complete precomputed native-feature
    // cohort. Sampled replay events are evidence only; never the ranking
    // denominator. Historical non-Gorge renderers retain their own logic.
    // R2's dedicated Key Insights section owns the card rankings.
    // Preserve the legacy embedded insights only when explicitly needed.
    if(!options.externalInsights){
    let signals;
    if(isGorge){
      const report=options.fullCardInsights;
      const fullN=options.fullCohortGames;
      const matching=report&&Number.isInteger(fullN)&&fullN>0&&
        report.verified_games===fullN&&report.observed_games===fullN&&
        report.coverage?.missing===0&&report.coverage?.level==="full-cohort"&&
        report.categories&&typeof report.categories==="object";
      if(matching){
        const examples=new Map(runs.map(run=>[run.seed,run]));
        const ranked={};
        const ownNames=Array.isArray(options.deckCardNames)?new Set(options.deckCardNames.map(n=>n.toLowerCase())):null;
        const typeMatches=(kind,item)=>{
          if(ownNames&&!ownNames.has(item.name.toLowerCase()))return false;
          const type=String(options.lookupRecordedCard?.(item.name)?.type_line||"").toLowerCase();
          if(!ownNames)return true;
          if(kind==="creature")return /\bcreature\b/.test(type);
          if(kind==="artifact")return /\bartifact\b/.test(type);
          if(kind==="enchantment")return /\benchantment\b/.test(type);
          if(kind==="instant")return /\binstant\b/.test(type);
          if(kind==="spell")return /\b(instant|sorcery)\b/.test(type);
          if(kind==="land")return /\bland\b/.test(type)&&!/\bbasic\s+land\b/.test(type);
          if(kind==="seenCreature")return /\bcreature\b/.test(type);
          return true;
        };
        for(const [kind,items] of Object.entries(report.categories)){
          if(!Array.isArray(items))continue;
          ranked[kind]=items.filter(item=>typeMatches(kind,item)).map(item=>({
            ...item,
            // Evidence is clickable only for a genuinely retained recording.
            events:(item.exampleEvents||[]).filter(([seed])=>examples.has(seed))
              .map(([seed,turn])=>({seed,turn,run:examples.get(seed)})),
            seen:new Set((item.exampleSeenSeeds||[]).map(seed=>examples.get(seed))
              .filter(Boolean)),
          }));
        }
        signals={coverage:fullN,total:fullN,
          confirmedTutors:report.confirmed_tutors||0,ranked};
      }else{
        signals={coverage:0,total:fullN||0,confirmedTutors:0,ranked:{}};
      }
    }else{
      signals=observationCardStats(runs,options.lookupRecordedCard,
        options.commanderName);
    }
    if(signals.coverage){
      const kinds=isGorge?
        ["played","creature","artifact","enchantment","instant","spell","land",
          ...(runs.some(r=>r.gorge_source?.visibility==="omniscient")?
             ["longest"]:[]),
          "activated","triggered"]:
        ["played","creature","artifact","enchantment",
          "instant","spell","land","longest",
          "activated","removal","creatureKills","damage","finisher",
          ...(signals.confirmedTutors?["tutorFound","tutorUsed"]:[])];
      const playedTypes=["played","creature","artifact","enchantment","instant","spell","land"];
      const seenTypes=["seen","seenCreature"];
      function groupedPlayedPanel(kind,types=playedTypes,ascending=false){
        const source=signals.ranked[kind]||[];
        const sorted=types===playedTypes?source.slice().sort((a,b)=>
          (ascending?a.games-b.games:b.games-a.games)||a.name.localeCompare(b.name)):source;
        const panel=cardPerformancePanel(kind,sorted,
          signals.coverage,groups,{...options,isGorge,tutorSearchCount:signals.confirmedTutors},onReviewRun);
        if(!panel)return null;
        const body=panel.querySelector(".game-outcome-body");
        const controls=create("div","gorge-card-type-controls");
        controls.setAttribute("role","group");controls.setAttribute("aria-label","Card type and ranking");
        const typesMeta={played:["▣","All cards"],creature:["♞","Creatures"],artifact:["⚙","Artifacts"],enchantment:["✦","Enchantments"],instant:["ϟ","Instants"],spell:["✧","Instants and sorceries"],land:["♜","Nonbasic lands"],seen:["▣","All cards"],seenCreature:["♞","Creatures"]};
        const render=(next,order,focusLabel)=>{
          const replacement=groupedPlayedPanel(next,types,order);
          if(replacement){replacement.open=true;panel.replaceWith(replacement);
            replacement.querySelector('[aria-label="'+focusLabel+'"]')?.focus();}
        };
        for(const type of types){
          if(!signals.ranked[type]?.length)continue;
          const [icon,label]=typesMeta[type];
          const button=textButton(icon+" "+label,"gorge-icon-button",()=>render(type,ascending,label));
          button.style.width="auto";button.style.padding="0.4rem 0.65rem";button.title=label;button.setAttribute("aria-label",label);button.setAttribute("aria-pressed",String(type===kind));controls.appendChild(button);
        }
        if(types===playedTypes){
          const label=ascending?"Show most played first":"Show least played first";
          const order=textButton(ascending?"Least ↑":"Most ↓","gorge-icon-button gorge-sort-button",()=>render(kind,!ascending,ascending?"Show least played first":"Show most played first"));
          order.style.width="auto";order.style.padding="0.4rem 0.65rem";order.title=label;order.setAttribute("aria-label",label);order.setAttribute("aria-pressed",String(ascending));controls.appendChild(order);
          if(ascending)panel.querySelector(".game-outcome-title").textContent="Least played "+(kind==="played"?"card":typesMeta[kind][1].toLowerCase());
          const note=create("p","micro","Least-played rankings include recorded candidates in this snapshot; cards without recorded plays may be absent.");
          note.hidden=!ascending;body.prepend(note);
        }
        body.prepend(controls);
        return panel;
      }
      for(const kind of kinds){
        if(isGorge&&playedTypes.includes(kind)&&kind!=="played")continue;
        if(isGorge&&kind==="played"){
          const panel=groupedPlayedPanel(kind);
          if(panel)cards.appendChild(panel);
          continue;
        }
        if(isGorge&&kind==="seenCreature")continue;
        if(isGorge&&kind==="seen"){
          const panel=groupedPlayedPanel(kind,seenTypes);
          if(panel)cards.appendChild(panel);
          continue;
        }
        const panel=filteredInsightPanel(kind,signals.ranked[kind]||[],
          signals.coverage,groups,
          {...options,isGorge,tutorSearchCount:signals.confirmedTutors},onReviewRun);
        if(panel)cards.appendChild(panel);
      }
    }else if(!isGorge){
      // The R2 adapter owns the optional Key Insights panel. Do not inject
      // another placeholder into the Results dashboard when data is absent.
      cards.appendChild(create("p","game-outcome-empty",
        "Card insights require named card and hand observations from the current published batch."));
    }
    }
    // The regression story belongs after every game/card panel, immediately
    // above the independent turn reviewer.
    // Gorge cohort regression comes exclusively from all verified outcomes
    // in the precomputed report; never show a replay-sample regression here.
    // When an external insights panel is authoritative, no secondary
    // analytics card belongs under the Results summary.
    if(!isGorge&&!options.externalInsights)
      cards.appendChild(elasticNetPanel(options.discoveryReport,options));
    if(options.reviewerRoot){
      jumpToReview=turnReviewer(options.reviewerRoot,groups,options);
    }
    if(typeof options.onReviewerReady==="function")options.onReviewerReady(jumpToReview);
    return report;
  }
  // Render the existing outcome card from complete-cohort Worker statistics.
  // Missing metrics stay unavailable; they are never inferred from a replay.
  function renderCohortOverview(root,summary,options={}){
    if(!summary||!Number.isInteger(summary.n)||summary.n<1||
       summary.wins+summary.losses!==summary.n)throw Error("Invalid cohort overview");
    const counts={win:summary.wins,loss:summary.losses,draw:0,unresolved:0,not_evaluated:0};
    const opponents=summary.groups?.opponents||[];
    const best=opponents.filter(x=>Number.isFinite(x.win_rate)).sort((a,b)=>b.win_rate-a.win_rate)[0];
    const highlights=[
      {key:"matchup",label:"Best matchup",value:best?(100*best.win_rate).toFixed(1)+"%":"—",detail:best?.name||"Not available"},
      {key:"length",label:"Game length",value:Number.isFinite(summary.median_game_turns)?nfmt(summary.median_game_turns):"—",detail:"Median recorded turns"},
      {key:"arrival",label:"Commander arrival",value:"—",detail:"Turn data unavailable"},
      {key:"ramp",label:"Mana ramp",value:"—",detail:"Turn-five mana data unavailable"}
    ];
    const grid=create("div","board-grid game-outcome-grid latest-insight-grid");
    const hero=outcomeCard({counts,total:summary.n,terminal:summary.n,terminalRounds:[]},
      {...options,isGorge:true,heroHighlights:highlights,outcomeMeta:summary.n+" games · complete cohort"},
      body=>body.appendChild(create("p","micro","Complete cohort results from the Worker.")));
    // These values are visual summaries, not the former drilldown panels.
    // Make them non-interactive until the complete-cohort drilldowns exist.
    for(const button of hero.querySelectorAll(".game-outcome-hero-highlight")){
      button.removeAttribute("aria-haspopup");button.disabled=true;
    }
    grid.appendChild(hero);root.replaceChildren(grid);
  }
  const playedInsightKinds=["played","creature","artifact","enchantment","instant","spell","land"];
  const insightTypes={played:["▣","All cards"],creature:["♞","Creatures"],artifact:["⚙","Artifacts"],enchantment:["✦","Enchantments"],instant:["ϟ","Instants"],spell:["✧","Instants and sorceries"],land:["♜","Nonbasic lands"]};
  function insightPanels(grid,rankings,coverage,groups,options,onReviewRun){
    function grouped(kind,ascending=false){
      const items=(rankings[kind]||[]).slice().sort((a,b)=>
        (ascending?a.games-b.games:b.games-a.games)||a.name.localeCompare(b.name));
      const panel=cardPerformancePanel(kind,items,coverage,groups,options,onReviewRun);
      if(!panel)return null;
      const body=panel.querySelector(".game-outcome-body");
      const controls=create("div","gorge-card-type-controls");
      controls.setAttribute("role","group");controls.setAttribute("aria-label","Card type and ranking");
      const change=(next,order,label)=>{const replacement=grouped(next,order);if(replacement){
        replacement.open=true;panel.replaceWith(replacement);
        replacement.querySelector('[aria-label="'+label+'"]')?.focus();}};
      for(const type of playedInsightKinds){
        if(!rankings[type]?.length)continue;
        const [icon,label]=insightTypes[type];
        const button=textButton(icon+" "+label,"gorge-icon-button",()=>change(type,ascending,label));
        button.style.width="auto";button.style.padding="0.4rem 0.65rem";button.title=label;button.setAttribute("aria-label",label);
        button.setAttribute("aria-pressed",String(type===kind));controls.appendChild(button);
      }
      const label=ascending?"Show most played first":"Show least played first";
      const order=textButton(ascending?"Least ↑":"Most ↓","gorge-icon-button gorge-sort-button",()=>
        change(kind,!ascending,ascending?"Show least played first":"Show most played first"));
      order.style.width="auto";order.style.padding="0.4rem 0.65rem";order.title=label;order.setAttribute("aria-label",label);controls.appendChild(order);
      if(ascending)panel.querySelector(".game-outcome-title").textContent="Least played "+
        (kind==="played"?"card":insightTypes[kind][1].toLowerCase());
      body.prepend(controls);return panel;
    }
    const played=grouped("played");if(played)grid.appendChild(played);
    for(const kind of ["longest","activated","triggered","removal","creatureKills","damage","finisher","tutorFound","tutorUsed"]){
      if((kind==="tutorFound"||kind==="tutorUsed")&&!options.tutorSearchCount)continue;
      const panel=filteredInsightPanel(kind,rankings[kind]||[],coverage,groups,options,onReviewRun);
      if(panel)grid.appendChild(panel);
    }
  }
  // Reuse the exact information control and popup treatment from the
  // Overall Results hero; only the explanatory copy differs.
  function insightMethodologyDisclosure(message){
    const info=create("details","game-outcome-limits insight-methodology");
    const trigger=create("summary",null,"ⓘ");
    trigger.setAttribute("aria-label","About these insights");
    trigger.title="Card insight methodology and limitations";
    const popup=create("div","game-outcome-limits-content");
    popup.append(create("strong",null,"Key Insights · methodology"),
      create("p",null,message));
    info.append(trigger,popup);
    return info;
  }
  // Methodology is a compact disclosure in the Key Insights title row.
  // Standalone renderers/test fixtures without that panel keep the disclosure
  // immediately above their grid.
  function placeInsightMethodology(root,info,grid){
    const slot=root.id==="key-insights-grid"?
      (typeof document!=="undefined"&&typeof document.getElementById==="function"?
        document.getElementById("key-insights-info"):null):null;
    if(slot){slot.replaceChildren(info);root.replaceChildren(grid);}
    else root.replaceChildren(info,grid);
  }
  function renderCohortInsights(root,report,total,options={}){
    const grid=create("div","board-grid game-outcome-grid latest-insight-grid");
    if(!report||report.verified_games!==total||report.observed_games!==total||
       report.coverage?.level!=="full-cohort"||report.coverage?.missing!==0){
      root.replaceChildren(create("p","game-outcome-empty","Card insights are pending complete cohort evidence."));return;
    }
    const rankings={};
    for(const [kind,items] of Object.entries(report.categories||{}))
      if(Array.isArray(items))rankings[kind]=items.map(item=>({...item,events:[],seen:new Set()}));
    insightPanels(grid,rankings,total,[],{...options,isGorge:true,tutorSearchCount:report.confirmed_tutors||0},()=>{});
    if(!grid.children.length)grid.appendChild(create("p","game-outcome-empty","No recorded card insights."));
    const info=insightMethodologyDisclosure(
      "Card rankings use the complete verified cohort of "+total+
      " games. Example games link to the recorded event when source evidence is available.");
    placeInsightMethodology(root,info,grid);
  }
  function renderRecordedBatchInsights(root,batch,options={}){
    const report=model([batch],options.deckKey,options.deckHash);
    const runs=report.groups.flatMap(group=>group.runs);
    const signals=observationCardStats(runs,options.lookupRecordedCard,options.commanderName);
    const info=insightMethodologyDisclosure(signals.coverage?
      "Card findings from "+signals.coverage+" of "+runs.length+
      " approved games with complete recorded card observations. These are observed-game findings, not verified full-cohort rankings.":
      "No named card observations are available in these approved games yet.");
    const grid=create("div","board-grid game-outcome-grid latest-insight-grid");
    if(signals.coverage){
      const owned=Array.isArray(options.deckCardNames)?new Set(options.deckCardNames.map(name=>name.toLowerCase())):null;
      const rankings={};for(const [kind,items] of Object.entries(signals.ranked))
        rankings[kind]=items.filter(item=>!owned||owned.has(item.name.toLowerCase()));
      insightPanels(grid,rankings,signals.coverage,report.groups,{...options,isGorge:true},
        (id,seed,turn)=>options.onReviewRun?.(id,seed,turn));
    }
    placeInsightMethodology(root,info,grid);return {coverage:signals.coverage,findings:grid.children.length};
  }
  // Allow a paginated data source to populate the exact original turn
  // reviewer without rendering a misleading single-game outcomes dashboard.
  function renderTurnReviewer(root,batches,options={}){
    const report=model(batches,options.deckKey,options.deckHash);
    root.replaceChildren();
    if(!report.groups.length){
      root.appendChild(create("span","micro","No recorded turns."));
      return report;
    }
    turnReviewer(root,report.groups,options);
    return report;
  }
  return {FORMAT,STATES,validate,model,lifeTrend,renderGameLengthHistogram,matchupRows,matchupMetrics,
    knockoutRound,opponentDecks,tokenInfo,battlefieldZone,observationCardStats,turnSpotlight,gameNavigator,render,renderCohortOverview,renderCohortInsights,renderRecordedBatchInsights,renderTurnReviewer};
});
