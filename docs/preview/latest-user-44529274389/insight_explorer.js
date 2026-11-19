/* Reusable simulation insight explorer. All claims come from pinned run events;
 * render() is category-agnostic and uses a model with cards, metrics and evidence.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  else root.DeckInsightExplorer=api;
})(typeof window!=="undefined"?window:globalThis,function(){
  "use strict";
  const create=(tag,cls,value)=>{
    const n=document.createElement(tag);
    if(cls)n.className=cls;
    if(value!==undefined&&value!==null)n.textContent=String(value);
    return n;
  };
  const median=values=>{
    if(!values.length)return null;
    const sorted=[...values].sort((a,b)=>a-b),mid=Math.floor(sorted.length/2);
    return sorted.length%2?sorted[mid]:(sorted[mid-1]+sorted[mid])/2;
  };
  const isCreature=(card)=>!!card&&/\bCreature\b/i.test((card.type_line||"").split("—")[0]);

  // First insight: creatures actually RESOLVED from a modeled hand cast.
  // Do not count mere battlefield presence, ETB triggers or unmodeled cards.
  function creaturePlays(runs,lookup){
    const valid=(runs||[]).filter(r=>Number.isInteger(r.seed)&&
      Array.isArray(r.events)&&r.events.length&&
      Array.isArray(r.state_snapshots));
    if(!valid.length)return null;
    const cards=new Map();
    function slot(name){
      if(!cards.has(name))cards.set(name,{name,played:new Set(),seen:new Set(),examples:[],firstTurns:new Map()});
      return cards.get(name);
    }
    for(const run of valid){
      const seen=new Set();
      for(const name of run.mulligan?.opening_hand||[]){
        if(isCreature(lookup(name)))seen.add(name);
      }
      for(let i=0;i<run.events.length;i++){
        const row=run.events[i];
        for(const event of row.events||[]){
          if(event.type==="draw"&&typeof event.card==="string"&&isCreature(lookup(event.card)))
            seen.add(event.card);
        }
        for(const name of run.state_snapshots[i]?.hand||[]){
          if(isCreature(lookup(name)))seen.add(name);
        }
      }
      for(const row of run.events){
        for(let index=0;index<(row.events||[]).length;index++){
          const event=row.events[index];
          if(event.type!=="creature_resolved"||typeof event.card!=="string"||
             !isCreature(lookup(event.card)))continue;
          const item=slot(event.card);
          item.played.add(run.seed);
          seen.add(event.card); // A successful hand cast establishes access.
          item.firstTurns.set(run.seed,Math.min(row.turn,item.firstTurns.get(run.seed)??Infinity));
          item.examples.push({seed:run.seed,turn:row.turn,eventIndex:index,
            cardName:event.card,kind:event.type,run,
            description:"Creature resolved from a recorded hand cast"});
        }
      }
      for(const name of seen)slot(name).seen.add(run.seed);
    }
    const contenders=[...cards.values()].filter(c=>c.played.size).map(c=>{
      const firstTurns=[...c.firstTurns.values()],turn=median(firstTurns);
      const rate=c.seen.size?Math.round(100*c.played.size/c.seen.size):null;
      const chronological=[...c.examples].sort((a,b)=>a.seed-b.seed||a.turn-b.turn||a.eventIndex-b.eventIndex);
      const nearMedian=[...c.examples].sort((a,b)=>Math.abs(a.turn-turn)-Math.abs(b.turn-turn)||a.seed-b.seed||a.eventIndex-b.eventIndex);
      return {name:c.name,score:c.played.size,scoreLabel:c.played.size+" / "+valid.length+" runs",
        card:lookup(c.name),metrics:[
          {id:"played",label:"Games played",value:c.played.size+" / "+valid.length,
           explanation:"Distinct seeds with a recorded creature resolution. Click again for the next example.",
           examples:chronological},
          {id:"access",label:"Played when seen",value:rate===null?"—":rate+"%",
           explanation:c.played.size+" of "+c.seen.size+" seeds where the card was seen in the kept hand, a draw, a later hand snapshot, or a successful cast. These are observed accesses, not legal casting opportunities.",
           examples:chronological},
          {id:"turn",label:"Median turn played",value:turn===null?"—":String(turn),
           explanation:"Median first resolution turn among seeds where this creature was played.",
           examples:nearMedian}
        ]};
    }).sort((a,b)=>b.score-a.score||a.name.localeCompare(b.name));
    if(!contenders.length)return null;
    return {
      id:"creature-plays",kicker:"Creature development · reviewed actions",
      title:"Most common creature",
      value:contenders[0].score+" / "+valid.length,
      description:"Runs with "+contenders[0].name+" resolved within "+valid[0].events.length+" modeled turns",
      explanation:"Counts named creature resolutions recorded by the bounded simulator. These are not multiplayer outcomes or card-power rankings.",
      chartLabel:"Games with a recorded creature resolution",
      contenders,total:valid.length
    };
  }

  function render(model,options={}){
    if(!model?.contenders?.length)return null;
    let selected=0,activeMetric=null,exampleIndex=-1,viewerOpen=false,viewIndex=0;
    const panel=create("details","board-report insight-report");
    const summary=create("summary","board-summary insight-summary");
    const top=model.contenders[0].card;
    const headline=create("span","board-summary-copy");
    headline.append(create("span","board-kicker","Key insight"),
      create("strong","insight-head-title",model.title));
    const subtitle=create("span","insight-head-subtitle");
    subtitle.appendChild(create("span","insight-head-name",model.contenders[0].name));
    if(top?.mana_cost&&typeof options.renderMana==="function"){
      const mana=create("span","insight-head-mana");
      mana.appendChild(options.renderMana(top.mana_cost));
      subtitle.appendChild(mana);
    }
    headline.append(subtitle,create("span","insight-head-stat",
      model.headlineDetail||(model.value+" · "+model.chartLabel.toLowerCase())),
      create("span","board-open","Explore cards and evidence →"));
    summary.appendChild(headline);
    if(top?.art||top?.image){
      const cover=create("img","board-cover");
      cover.src=top.art||top.image;cover.alt="";cover.loading="lazy";
      summary.appendChild(cover);
    }
    panel.appendChild(summary);
    const body=create("div","board-body insight-body");
    body.appendChild(create("p","micro",model.explanation));
    const compare=create("div","insight-compare");
    const chosen=create("div","insight-selected-card");
    const ranking=create("div","insight-ranking");
    compare.append(chosen,ranking);
    body.appendChild(compare);
    const performance=create("div","insight-performance");
    const evidence=create("div","insight-evidence");
    body.append(performance,evidence);
    panel.appendChild(body);

    function showEvidence(){
      evidence.replaceChildren();
      const card=model.contenders[selected];
      const metric=card.metrics.find(m=>m.id===activeMetric);
      if(!metric||exampleIndex<0||!metric.examples.length){
        const description=metric&&!metric.examples?.length?
          "No corresponding recorded events for this card and metric. The value and interpretation above are still available.":
          "Select a performance metric to inspect recorded examples. Click the same metric again to cycle through them.";
        evidence.appendChild(create("p","micro",description));
        return;
      }
      const examples=metric.examples;
      const example=examples[exampleIndex%examples.length];
      const heading=create("div","insight-evidence-heading");
      heading.append(create("strong",null,metric.label+" · supporting run"),
        create("span","micro",(exampleIndex+1)+" of "+examples.length));
      evidence.appendChild(heading);
      const detail=create("div","insight-example");
      detail.append(create("strong",null,"Seed "+example.seed+" · Turn "+example.turn),
        create("p","small",example.cardName+" · "+example.description));
      const controls=create("div","insight-example-controls");
      const previous=create("button","stone-button","← Previous");
      const next=create("button","stone-button","Next →");
      previous.type=next.type="button";
      previous.onclick=()=>{exampleIndex=(exampleIndex-1+examples.length)%examples.length;showEvidence()};
      next.onclick=()=>{exampleIndex=(exampleIndex+1)%examples.length;showEvidence()};
      const open=create("button","gold-button",viewerOpen?"Hide full turn":"Show full turn here");
      open.type="button";
      open.setAttribute("aria-expanded",String(viewerOpen));
      open.onclick=()=>{viewerOpen=!viewerOpen;showEvidence()};
      controls.append(previous,next,open);
      detail.appendChild(controls);evidence.appendChild(detail);
      const all=create("details","insight-example-all");
      all.appendChild(create("summary",null,"Browse "+examples.length+" matching recorded event"+(examples.length===1?"":"s")));
      const list=create("div","insight-example-list");
      examples.forEach((item,i)=>{
        const button=create("button","insight-example-row",
          "Seed "+item.seed+" · Turn "+item.turn+" · "+item.cardName);
        button.type="button";button.setAttribute("aria-pressed",String(i===exampleIndex));
        button.onclick=()=>{exampleIndex=i;showEvidence()};
        list.appendChild(button);
      });
      all.appendChild(list);evidence.appendChild(all);
      if(viewerOpen){
        const viewer=create("section","insight-inline-replay");
        viewer.setAttribute("aria-label","Turn-by-turn evidence for seed "+example.seed);
        viewer.appendChild(create("p","insight-inline-intro",
          "Seed "+example.seed+" · Turn "+example.turn+
          " · exact recorded actions and end-of-turn zones"));
        const replayRoot=create("div","replay-root");
        viewer.appendChild(replayRoot);
        if(typeof options.onRenderEvidence==="function"){
          try{options.onRenderEvidence(replayRoot,example,card,metric)}
          catch(error){replayRoot.textContent="The recorded game could not be displayed."}
        }else replayRoot.textContent="Full turn viewer is not connected.";
        evidence.appendChild(viewer);
      }
    }

    function showSelected(){
      const card=model.contenders[selected];
      const mode=model.views?.[viewIndex]||null;
      const ranked=model.contenders.map((entry,index)=>({
        entry,index,score:mode?Number(entry.viewScores?.[mode.id]||0):entry.score
      })).filter(item=>item.score>0).sort((a,b)=>
        b.score-a.score||a.entry.name.localeCompare(b.entry.name));
      const max=ranked[0]?.score||1;
      chosen.replaceChildren();ranking.replaceChildren();performance.replaceChildren();
      chosen.appendChild(create("span","board-kicker","Selected card"));
      const physical=card.card;
      if(physical?.image||physical?.art){
        const button=create("button","insight-card-art");
        button.type="button";button.setAttribute("aria-label","View printed card details for "+card.name);
        const img=create("img");
        img.src=physical.image||physical.art;img.alt=card.name;img.loading="lazy";
        button.appendChild(img);
        button.onclick=()=>options.onOpenCard?.(physical.oracle_id);
        chosen.appendChild(button);
      }
      chosen.appendChild(create("strong","insight-card-name",card.name));
      ranking.append(create("h3",null,mode?mode.chartLabel:model.chartLabel));
      if(model.views?.length>1){
        const toggle=create("div","insight-ranking-views");
        model.views.forEach((view,i)=>{
          const button=create("button","insight-ranking-view"+(i===viewIndex?" is-active":""),
            view.label);
          button.type="button";
          button.setAttribute("aria-pressed",String(i===viewIndex));
          button.onclick=()=>{
            if(i===viewIndex)return;
            viewIndex=i;
            // Preserve the selected card when that measurement exists.
            // Otherwise select the strongest eligible entry in the new view.
            if(!Number(model.contenders[selected]?.viewScores?.[view.id])){
              const next=[...model.contenders].map((c,j)=>({
                c,j,score:Number(c.viewScores?.[view.id]||0)
              })).filter(x=>x.score>0).sort((a,b)=>
                b.score-a.score||a.c.name.localeCompare(b.c.name))[0];
              if(next)selected=next.j;
            }
            activeMetric=null;exampleIndex=-1;viewerOpen=false;
            showSelected();
          };
          toggle.appendChild(button);
        });
        ranking.appendChild(toggle);
      }
      ranking.appendChild(create("p","micro",
        (mode?.chartLabel||model.chartLabel)+" · select any bar"));
      // The adjusted-score tab explains its heuristic where the ranking is
      // shown. Other graph modes remain focused on inspectable game evidence.
      if(mode?.formula){
        const method=create("div","insight-ranking-method");
        method.append(create("strong",null,"How this score is calculated"),
          create("code","insight-ranking-formula",mode.formula));
        if(mode.explanation)
          method.appendChild(create("p","micro",mode.explanation));
        ranking.appendChild(method);
      }
      const bars=create("div","insight-bars");
      ranked.slice(0,12).forEach(({entry,index,score})=>{
        const button=create("button","insight-bar"+(index===selected?" is-selected":""));
        button.type="button";button.setAttribute("aria-pressed",String(index===selected));
        const head=create("span","insight-bar-caption");
        head.append(create("span",null,entry.name),
          create("strong",null,(mode?entry.viewLabels?.[mode.id]:null)||
            entry.scoreLabel));
        const track=create("span","insight-bar-track"),fill=create("span","insight-bar-fill");
        fill.style.width=100*score/max+"%";
        track.appendChild(fill);button.append(head,track);
        button.onclick=()=>{selected=index;activeMetric=null;exampleIndex=-1;viewerOpen=false;showSelected()};
        bars.appendChild(button);
      });
      ranking.appendChild(bars);
      performance.appendChild(create("h3",null,"Selected card performance"));
      const stats=create("div","insight-metrics");
      for(const item of card.metrics){
        const button=create("button","insight-metric"+(item.id===activeMetric?" is-selected":""));
        button.type="button";button.setAttribute("aria-pressed",String(item.id===activeMetric));
        button.title=item.explanation;
        button.append(create("strong",null,item.value),create("span",null,item.label));
        button.onclick=()=>{
          const examples=item.examples||[];
          if(!examples.length){
            activeMetric=item.id;exampleIndex=-1;viewerOpen=false;
            showSelected(); // Show its explanation even when the count is zero.
            return;
          }
          if(activeMetric===item.id&&exampleIndex>=0)exampleIndex=(exampleIndex+1)%examples.length;
          else{activeMetric=item.id;exampleIndex=0}
          viewerOpen=true; // A metric opens the cached run inline; no additional request.
          showSelected();
        };
        stats.appendChild(button);
      }
      performance.appendChild(stats);
      const metric=card.metrics.find(m=>m.id===activeMetric);
      performance.appendChild(create("p","micro",metric?.explanation||
        "Select a metric for its denominator and supporting games."));
      showEvidence();
    }
    showSelected();
    return panel;
  }

  return {median,creaturePlays,render};
});
