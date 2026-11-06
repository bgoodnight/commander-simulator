"use strict";
/* Stable Worker-to-original-DeckGameOutcomes presentation adapter.
 * No native Gorge interpretation in the browser, no experimental fallback.
 */
(function(){
  const base=window.GORGE_R2_API_BASE||
    "https://gorge-r2-direct-api-preview.darbosama.workers.dev";
  let api;
  try{
    api=new URL(base);
    if(api.protocol!=="https:"||
       !/^[a-z0-9-]+\.[a-z0-9-]+\.workers\.dev$/i.test(api.hostname))return;
  }catch{return;}
  let generation=0,renderedDeck=null;
  const $=id=>document.getElementById(id);
  const statusMessage=(message)=>{
    const root=$("game-outcome-results"),status=$("game-outcome-status");
    if(root){
      const line=document.createElement("p");
      line.className="game-outcome-empty";
      line.textContent=message;
      root.replaceChildren(line);
    }
    if(status)status.textContent=message;
  };
  function ownsRenderedDeck(key){return renderedDeck===key;}
  // Materialized views keep statistics cohort-wide while replay is loaded per click.
  async function loadMaterialized(key,ticket,selected){
    const endpoint=new URL("/v1/ui/catalog",api);
    endpoint.searchParams.set("deck",key);
    const response=await fetch(endpoint,{cache:"no-store"});
    if(response.status===404)return false; // rollout compatibility with old Worker
    if(!response.ok)throw Error("Materialized catalog HTTP "+response.status);
    const catalog=await response.json();
    if(catalog.schema!=="gorge-r2-materialized-response-v1" ||
       catalog.deck!==key)throw Error("Invalid materialized catalog");
    if(ticket!==generation||key!==window.__deckLabActiveKey)return true;
    // Preserve the polished original renderer for cohorts it can safely handle.
    // Opt into the new layout for staging via ?materializedResults=1.
    const preview=new URLSearchParams(window.location.search).get("materializedResults")==="1";
    if(catalog.status==="ready" && catalog.total<=200 && !preview)return false;
    if(catalog.status!=="ready"){
      statusMessage("No approved current results are published for this deck.");
      return true;
    }
    const summary=catalog.summary;
    if(summary?.schema!=="gorge-r2-live-summary-v1" ||
       summary.cohort_version!==catalog.version ||
       summary.n!==catalog.total)throw Error("Materialized summary mismatch");
    const root=$("game-outcome-results"),reviewer=$("turn-reviewer-results");
    if(!root)return true;
    for(const id of ["simulation-snapshot","key-insights-panel",
                      "development-panel","archive-observation-details",
                      "opponent-replay-panel"]){
      const element=$(id);if(element)element.hidden=true;
    }
    const legacyRefresh=$("game-outcome-refresh");
    if(legacyRefresh)legacyRefresh.hidden=true;
    const diagnostic=$("pane-records")?.querySelector(".diagnostic-panel");
    if(diagnostic)diagnostic.hidden=true;
    const panel=$("turn-reviewer-panel");
    if(panel)panel.hidden=false;
    const create=(tag,text)=>{
      const el=document.createElement(tag);
      if(text!==undefined)el.textContent=text;
      return el;
    };
    const heading=create("h3","Approved simulation results");
    const totals=create("p",summary.n+" games · "+summary.wins+" wins · "+
      summary.losses+" losses · "+(summary.win_rate*100).toFixed(1)+
      "% win rate (25% four-player reference)");
    const info=create("p","Summary covers the complete approved cohort. Game pages and replays load separately.");
    const navigation=create("div");
    const list=create("div");
    const replayHeading=create("h4","Select a game to review its recorded turns");
    const replayRoot=create("div");
    root.replaceChildren(heading,totals,info,navigation,list,replayHeading,replayRoot);
    let page=0;
    const readJson=async(url)=>{
      const res=await fetch(url,{cache:"no-store"});
      if(!res.ok)throw Error("R2 Results HTTP "+res.status);
      return res.json();
    };
    const live=()=>ticket===generation&&key===window.__deckLabActiveKey;
    const showGame=async(gameId,pageNumber)=>{
      replayHeading.textContent="Loading selected game…";
      try{
        const url=new URL("/v1/ui/game",api);
        url.searchParams.set("deck",key);
        url.searchParams.set("page",String(pageNumber));
        url.searchParams.set("game_id",gameId);
        const detail=await readJson(url);
        if(!live())return;
        if(detail.schema!=="gorge-r2-materialized-response-v1" ||
           detail.version!==catalog.version || detail.deck!==key ||
           detail.game?.game_id!==gameId)throw Error("Replay version mismatch");
        const batch=detail.game.batch;
        if(batch?.deck_sha256!==selected.sha){
          replayHeading.textContent="Selected game belongs to a different deck revision.";
          return;
        }
        if(!window.DeckGameOutcomes?.validate(batch))
          throw Error("Original replay format rejected");
        replayHeading.textContent="Selected game replay · individual game (not cohort statistics)";
        window.DeckGameOutcomes.render(replayRoot,[batch],{
          deckKey:key,deckHash:selected.sha,
          commanderName:selected.commander,commanderArt:selected.art,
          isGorge:true,reviewerRoot:reviewer,reviewerPanel:panel,
          lookupRecordedCard:window.GorgeDeckLabCardInfo,
          deckCardNames:selected.cardNames,
          renderMana:value=>window.GorgeDeckLabMana?.(value),
          onOpenRecordedCard:name=>window.GorgeDeckLabOpenCard?.(name)
        });
      }catch(err){
        if(live())replayHeading.textContent="Replay unavailable: "+String(err.message||err);
      }
    };
    const showPage=async(number)=>{
      navigation.textContent="Loading games…";
      try{
        const url=new URL("/v1/ui/page",api);
        url.searchParams.set("deck",key);
        url.searchParams.set("page",String(number));
        const result=await readJson(url);
        if(!live())return;
        if(result.schema!=="gorge-r2-materialized-response-v1" ||
           result.version!==catalog.version ||result.deck!==key ||
           result.page?.page!==number ||result.page?.total!==summary.n ||
           !Array.isArray(result.page.games) ||
           result.page.games.length>25)throw Error("Game page version mismatch");
        page=number;
        const prev=create("button","Previous 25");
        prev.type="button";prev.disabled=page===0;
        prev.addEventListener("click",()=>showPage(page-1));
        const next=create("button","Next 25");
        next.type="button";next.disabled=!result.page.has_more;
        next.addEventListener("click",()=>showPage(page+1));
        const counter=create("span"," Page "+(page+1)+" of "+catalog.page_count+" ");
        navigation.replaceChildren(prev,counter,next);
        const rows=result.page.games.map(g=>{
          const button=create("button",g.result.toUpperCase()+" · "+
            (g.turns??"?")+" turns · "+g.opponent_decks.join(", "));
          button.type="button";button.className="game-outcome-game-select";
          button.addEventListener("click",()=>showGame(g.game_id,page));
          return button;
        });
        list.replaceChildren(...rows);
        replayRoot.replaceChildren();
        replayHeading.textContent="Select a game to review its recorded turns";
      }catch(err){
        if(live())navigation.textContent="Game page unavailable: "+String(err.message||err);
      }
    };
    renderedDeck=key;
    const status=$("game-outcome-status");
    if(status)status.textContent=summary.n+" approved games · complete-cohort summary · lazy replays";
    await showPage(0);
    return true;
  }

  async function refresh(key=window.__deckLabActiveKey){
    const ticket=++generation;
    renderedDeck=null;
    const selected=window.GorgeDeckLabSelectedDeck?.(key);
    if(!key||!selected?.eligible)return;
    statusMessage("Checking approved Gorge game results…");
    try{
      if(await loadMaterialized(key,ticket,selected))return;
      const url=new URL("/v1/ui/batch",api);
      url.searchParams.set("deck",key);
      const response=await fetch(url,{cache:"no-store"});
      if(!response.ok)throw Error("Worker returned HTTP "+response.status);
      const result=await response.json();
      if(ticket!==generation||key!==window.__deckLabActiveKey)return;
      if(result.schema!=="gorge-r2-original-ui-batch-response-v1"||
         result.deck!==key||result.population!=="approved_current_decisive_only")
        throw Error("Unexpected original Results API response");
      if(result.status!=="ready"){
        const description={
          awaiting_cohort_approval:"Gorge recordings are in R2, awaiting approved-cohort review.",
          no_warehouse_shards:"No approved Gorge simulations are available for this deck.",
          projection_pending:"The approved games are awaiting original-UI replay projections."
        }[result.status];
        if(!description||result.batch!==null)throw Error("Invalid Worker batch status");
        statusMessage(description);
        return;
      }
      const batch=result.batch;
      if(!batch||batch.deck_key!==key||
         batch.deck_sha256!==selected.sha){
        statusMessage("No approved simulations match this exact Deck Lab deck revision.");
        return;
      }
      if(!window.DeckGameOutcomes?.validate(batch))
        throw Error("Original Results renderer rejected Worker batch");
      const root=$("game-outcome-results"),reviewer=$("turn-reviewer-results");
      if(!root)return;
      const panel=$("turn-reviewer-panel");
      if(panel)panel.hidden=false;
      for(const id of ["simulation-snapshot","key-insights-panel",
                        "development-panel","archive-observation-details",
                        "opponent-replay-panel"]){
        const element=$(id);if(element)element.hidden=true;
      }
      const legacyRefresh=$("game-outcome-refresh");
      if(legacyRefresh)legacyRefresh.hidden=true;
      const diagnostic=$("pane-records")?.querySelector(".diagnostic-panel");
      if(diagnostic)diagnostic.hidden=true;
      window.DeckGameOutcomes.render(root,[batch],{
        deckKey:key,deckHash:selected.sha,
        commanderName:selected.commander,commanderArt:selected.art,
        isGorge:true,reviewerRoot:reviewer,reviewerPanel:panel,
        lookupRecordedCard:window.GorgeDeckLabCardInfo,
        deckCardNames:selected.cardNames,
        renderMana:value=>window.GorgeDeckLabMana?.(value),
        onOpenRecordedCard:name=>window.GorgeDeckLabOpenCard?.(name),
        fullCardInsights:window.__gorgeCardInsights?.[key]||null,
        fullCohortGames:window.__gorgeFullCohort?.decks?.[key]?.n||null
      });
      renderedDeck=key;
      const label=batch.runs.length+" approved native Gorge game"+
        (batch.runs.length===1?"":"s")+" · original Results UI";
      const status=$("game-outcome-status");
      if(status)status.textContent=label;
    }catch(err){
      if(ticket!==generation||key!==window.__deckLabActiveKey)return;
      statusMessage("Original Results API unavailable: "+String(err.message||err));
    }
  }
  window.R2OriginalResults={refresh,ownsRenderedDeck};
  // App boot asynchronously chooses its initial deck and calls refresh.
})();
