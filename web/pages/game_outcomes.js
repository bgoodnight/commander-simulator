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
  function matchupRows(groups){
    // In a four-player pod, a pilot outcome belongs to the WHOLE table.
    // Even with named opponents, these are conditional associations, not
    // head-to-head win probabilities or individual-opponent attribution.
    const buckets=new Map();
    for(const group of groups){
      for(const run of group.runs){
        const opponents=opponentDecks(run,run.batch);
        const names=opponents.length?
          opponents.map(d=>({id:"deck:"+d.id+":"+d.version,label:d.name+" · present in pod",
            title:d.name,kind:"named",portraitName:d.name})):
          [{id:"scenario:"+group.id,label:group.label,kind:"abstract",
            title:group.scenario[0].toUpperCase()+group.scenario.slice(1)+" pod",
            archetype:group.scenario}];
        for(const named of names){
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
      create("span","board-open","Explore rounds and seeds →"));
    summary.appendChild(copy);panel.appendChild(summary);
    const body=create("div","game-outcome-body");
    childBuilder(body);
    panel.appendChild(body);
    return panel;
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
  function runDetails(root,run,options={}){
    root.replaceChildren();
    const heading=create("div","game-outcome-evidence-head");
    heading.append(create("strong",null,"Seed "+run.seed+" · "+stateLabel(run.outcome.status)),
      create("span","micro",roundLabel(run)));
    root.appendChild(heading);
    const select=create("div","game-outcome-round-options");
    const info=create("div","game-outcome-round-detail");
    function showRound(index){
      info.replaceChildren();
      const row=run.life_history[index],previous=run.life_history[index-1];
      info.appendChild(create("strong",null,"Round "+row.round+
        " · "+row.alive_seats.length+" of 4 seats alive"));
      const totals=create("div","game-outcome-life-stats");
      for(const seat of SEATS){
        const stat=create("div","game-outcome-life-stat");
        const current=lifeAt(row,seat),before=previous?lifeAt(previous,seat):current;
        stat.append(create("span",null,seat===0?"Your life":"Seat "+(seat+1)),
          create("strong",null,nfmt(current)),
          create("small",null,(current-before<0?"":current-before>0?"+":"")+
            (current-before||"±0")+" this round"));
        totals.appendChild(stat);
      }
      info.appendChild(totals);
      const changes=row.life_changes||[];
      if(!changes.length){
        info.appendChild(create("p","micro","No life changes recorded this round."));
      }else{
        const actions=create("div","game-outcome-life-events");
        for(const change of changes){
          const seat=Number(change.seat),dir=change.delta>0?"+":"";
          actions.appendChild(create("p","micro",
            (seat===0?"Your seat":"Seat "+(seat+1))+
            " · "+change.kind+" "+nfmt(change.amount)+
            " ("+dir+nfmt(change.delta)+" life)"+
            (Number.isInteger(change.source_object_id)?
              " · recorded source #"+change.source_object_id:" · unattributed")));
        }
        info.appendChild(actions);
      }
      for(const eliminated of row.new_eliminations||[])
        info.appendChild(create("p","game-outcome-elimination",
          "Seat "+(Number(eliminated.seat)+1)+" eliminated · "+eliminated.cause));
    }
    const slider=create("input","game-outcome-round-slider");
    slider.type="range";slider.min="0";
    slider.max=String(run.life_history.length-1);
    slider.value=String(run.life_history.length-1);
    const readout=create("span","micro","Round "+slider.value);
    slider.addEventListener("input",()=>{
      readout.textContent="Round "+slider.value;showRound(Number(slider.value));
    });
    select.append(slider,readout);root.append(select,info);
    showRound(Number(slider.value));
    const example=options.example;
    if(example?.events?.length&&
       typeof options.onShowRecordedActions==="function"){
      const details=create("details","story-drilldown game-outcome-actions");
      details.appendChild(create("summary",null,"Inspect recorded actions (available example)"));
      const target=create("div","replay-root");
      details.appendChild(target);
      details.addEventListener("toggle",()=>{
        if(!details.open||details.dataset.rendered)return;
        details.dataset.rendered="1";
        options.onShowRecordedActions(target,example,run);
      });
      root.appendChild(details);
    }
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
  function render(root,batches,options={}){
    root.replaceChildren();
    const report=model(batches,options.deckKey,options.deckHash);
    if(!report.groups.length){
      root.appendChild(create("p","game-outcome-empty",
        "No matching long-game outcome batches are loaded for this exact deck revision. "+
        "Import JSON from the 20-round workflow to preview these charts; "+
        "a published long-game batch will appear here automatically when available."));
      return report;
    }
    let active=0;
    const toolbar=create("div","game-outcome-toolbar");
    const choice=create("select","game-outcome-scenario-select");
    choice.setAttribute("aria-label","Select modeled game scenario");
    for(let i=0;i<report.groups.length;i++){
      const g=report.groups[i],option=create("option",null,
        g.label+" · "+g.total+" games · "+g.requestedRounds+" rounds max");
      option.value=String(i);choice.appendChild(option);
    }
    if(report.groups.length>1)toolbar.appendChild(choice);
    const info=create("p","micro");
    toolbar.appendChild(info);root.appendChild(toolbar);
    const cards=create("div","board-grid game-outcome-grid");
    root.appendChild(cards);
    function showGroup(){
      cards.replaceChildren();
      const group=report.groups[active];
      // Opposing tables can be compared across scenarios, but only with
      // the same pilot personality, rule approximations and round horizon.
      const peers=report.groups.filter(g=>
        g.pilotStyle===group.pilotStyle&&
        g.provisionalMode===group.provisionalMode&&
        g.requestedRounds===group.requestedRounds);
      const matchup=matchupRows(peers);
      info.textContent=group.total+" modeled games · "+group.requestedRounds+
        "-round horizon · "+group.scenario+
        " · pilot "+group.pilotStyle+" · provisional "+group.provisionalMode+
        " · abstract opponent policies, not competitive multiplayer win rates";
      // Outcome tile: no denominator changes due to right-censoring.
      cards.appendChild(card("Modeled results","Long-game outcome",
        group.counts.win+" / "+group.total+" wins",
        group.counts.unresolved+" unresolved · "+group.terminal+" finished",
        body=>{
          body.appendChild(create("p","micro",
            "These are life-zero modeled finishes, not verified Commander win rates. "+
            "Unresolved games have reached their time limit; they are not losses."));
          const evidence=create("div","game-outcome-evidence");
          const examples=create("div","game-outcome-seeds");
          let picked=null;
          function showSeeds(status){
            examples.replaceChildren();evidence.replaceChildren();
            const found=group.runs.filter(r=>!status||r.outcome.status===status);
            for(const run of found){
              const button=textButton("Seed "+run.seed+" · "+stateLabel(run.outcome.status)+
                " · "+roundLabel(run),"game-outcome-seed",()=>{
                picked=run.seed;showSeeds(status);
                runDetails(evidence,run,{example:group.exampleBySeed.get(run.seed),
                  onShowRecordedActions:options.onShowRecordedActions});
              });
              button.setAttribute("aria-pressed",String(run.seed===picked));
              examples.appendChild(button);
            }
            if(!found.length)examples.appendChild(create("p","micro",
              "No recorded games for this result."));
          }
          countsChart(body,group,showSeeds);
          const median=quantile(group.terminalRounds,.5);
          body.appendChild(create("p","micro",
            "Median completed round (finished games only): "+
            (median===null?"not yet observed":nfmt(median))+
            ". Finished "+group.terminal+" / "+group.total+
            "; unresolved "+group.counts.unresolved+" / "+group.total+"."));
          body.append(examples,evidence);showSeeds(null);
        }));
      cards.appendChild(card("Life progression","Four-seat life history",
        group.life.at(-1)?.seats[0]?.median?.toFixed(1).replace(/\.0$/,"")||"—",
        "Your median life at last observed round · "+group.life.length+" observed rounds",
        body=>{
          body.appendChild(create("p","micro",
            "Median life per seat; translucent bands show the middle 50%. "+
            "Games that finish stop contributing in later rounds—check the sample size."));
          const legend=create("div","game-outcome-legend");
          for(const seat of SEATS){
            const chip=create("span",null,seat===0?"You":"Seat "+(seat+1));
            chip.style.borderColor=SEAT_COLORS[seat];legend.appendChild(chip);
          }
          body.append(legend,lifePlot(group.life));
          const slider=create("input","game-outcome-round-slider");
          slider.type="range";slider.min="0";
          slider.max=String(group.life.length-1);
          slider.value=String(Math.min(6,group.life.length-1));
          const detail=create("div","game-outcome-round-detail");
          const displayRound=()=>{
            roundTrendDetail(detail,{...group.life[Number(slider.value)],total:group.total});
          };
          slider.addEventListener("input",displayRound);
          body.append(slider,detail);displayRound();
        }));
      cards.appendChild(card("Opposing tables","Matchup comparisons",
        matchup.length+" groups",
        matchup.some(x=>x.kind==="named")?
          "Named opposing deck appearances":"Scenarios and opponent roles only",
        body=>{
          body.appendChild(create("p","micro",
            matchup.some(x=>x.kind==="named")?
              "Results grouped by named opposing deck presence in a four-player pod. "+
              "These are associations, not 1v1 matchups or proof of which deck caused an outcome.":
              "The current simulator exports opponent policies and scenarios, "+
              "not named enemy Commander decks. Specific deck comparisons will appear "+
              "here when opponent_decks identities are exported."));
          const groups=matchup.filter(x=>x.kind===
            (matchup.some(x=>x.kind==="named")?"named":"abstract"));
          if(groups.length>=2){
            const best=groups[0],worst=groups.at(-1);
            const share=b=>Math.round(100*b.counts.win/b.games)+"%";
            const tied=best.counts.win*worst.games===worst.counts.win*best.games;
            body.appendChild(create("p","micro",
              tied?
                "Recorded opponent groups have the same observed modeled win share ("+
                  share(best)+"); there is no meaningful best/worst ranking yet.":
                "Highest observed modeled win share: "+best.label+
                  " ("+best.counts.win+"/"+best.games+"; "+share(best)+
                  "). Lowest: "+worst.label+" ("+worst.counts.win+"/"+
                  worst.games+"; "+share(worst)+"). "+
                  "These small, censored samples do not predict future performance."));
          }else{
            body.appendChild(create("p","micro",
              "Only one opponent group is recorded for this pilot, rules mode and horizon; "+
              "best/worst comparisons require at least two opposing groups."));
          }
          const list=create("div","game-outcome-matchups");
          for(const bucket of groups){
            const row=create("details","game-outcome-matchup");
            row.appendChild(create("summary",null,
              bucket.label+" · "+bucket.counts.win+"/"+bucket.games+
              " modeled wins · "+bucket.counts.loss+" losses · "+
              bucket.counts.unresolved+" unresolved"));
            const seedList=create("div","game-outcome-seeds");
            const detail=create("div","game-outcome-evidence");
            for(const {run,group:source} of bucket.runs){
              seedList.appendChild(textButton(
                source.scenario+" · seed "+run.seed+" · "+stateLabel(run.outcome.status),
                "game-outcome-seed",()=>runDetails(detail,run,{
                  example:source.exampleBySeed.get(run.seed),
                  onShowRecordedActions:options.onShowRecordedActions
                })));
            }
            row.append(seedList,detail);list.appendChild(row);
          }
          body.appendChild(list);
        }));
    }
    choice.onchange=()=>{active=Number(choice.value);showGroup()};
    showGroup();
    return report;
  }
  return {FORMAT,STATES,validate,model,lifeTrend,matchupRows,opponentDecks,render};
});
