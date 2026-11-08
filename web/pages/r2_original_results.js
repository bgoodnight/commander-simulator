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
  let generation=0,renderedDeck=null,verifiedInsights=null,verifiedInsightCount=null;
  let recoveryTimer=null;
  const RECOVERY_DELAY_MS=[350,1200];
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
  // One Results readiness policy. Authorization and cohort approval are
  // enforced by R2; the browser never guesses access from a local toggle.
  // Optional panels render only when their own source-backed data exists.
  function setResultsState(state){
    if(!["loading","unavailable","ready"].includes(state))throw Error("Invalid results state");
    const ready=state==="ready";
    document.body.dataset.r2ResultsState=state;
    const reviewer=$("turn-reviewer-panel");
    if(reviewer){
      reviewer.hidden=!ready;
      reviewer.style.setProperty("display",ready?"block":"none","important");
    }
    if(!ready){
      document.dispatchEvent(new Event("gorge:results-reset"));
      $("r2-game-picker")?.remove();
      $("key-insights-grid")?.replaceChildren();
      $("key-insights-info")?.replaceChildren();
      $("turn-reviewer-nav")?.replaceChildren();
      $("turn-reviewer-results")?.replaceChildren();
      document.body.classList.remove("r2-original-results-active");
    }
    // A valid R2 result activates all three sections as one group.
    // Missing named card metrics are described *inside* Key Insights.
    setInsightsVisible(ready);
  }
  function setInsightsVisible(available){
    const panel=$("key-insights-panel");
    if(!panel)return;
    panel.hidden=!available;
    panel.style.setProperty("display",available?"block":"none","important");
  }
  function verifiedReport(report,total,version=null){
    return Number.isInteger(total)&&total>0&&report?.verified_games===total&&
      report?.observed_games===total&&report?.coverage?.missing===0&&
      report?.coverage?.level==="full-cohort"&&
      (!version||report.cohort_version===version)&&
      report.categories&&typeof report.categories==="object";
  }
  function showCohortInsights(report,total,version=null,onReviewGame=null){
    const grid=$("key-insights-grid");
    if(!grid)return;
    if(!verifiedReport(report,total,version)){
      const placeholder=document.createElement("p");
      placeholder.className="game-outcome-empty";
      placeholder.textContent="Approved game results are available; named-card findings "+
        "have not yet been published for this cohort.";
      $("key-insights-info")?.replaceChildren();
      grid.replaceChildren(placeholder);
      return;
    }
    $("key-insights-empty").hidden=true;
    window.DeckGameOutcomes.renderCohortInsights(grid,report,total,{
      lookupRecordedCard:window.GorgeDeckLabCardInfo,
      onReviewGame,
      renderMana:value=>window.GorgeDeckLabMana?.(value),
      onOpenRecordedCard:name=>window.GorgeDeckLabOpenCard?.(name),
      onOpenTokenCard:card=>window.GorgeDeckLabOpenTokenCard?.(card)
    });
    // Core section visibility is tied to result readiness, not card ranking count.
  }
  function ownsRenderedDeck(key){return renderedDeck===key;}
  // Small, approved materialized cohorts can use the *existing* original
  // Results renderer, including its original Key Insights and Turn Reviewer.
  // Reassemble only Worker-verified single-game projections; do not infer
  // hidden hands from public replay or use unapproved source recordings.
  async function originalBatchFromMaterialized(catalog,key,ticket,selected){
    if(!Number.isInteger(catalog.total)||catalog.total<1||catalog.total>200||
       !Number.isInteger(catalog.page_count)||
       catalog.page_count!==Math.ceil(catalog.total/25)||
       !/^[a-f0-9]{64}$/.test(catalog.version||""))
      throw Error("Invalid original-layout materialized cohort");
    const live=()=>ticket===generation&&key===window.__deckLabActiveKey;
    const read=async(path,params)=>{
      const url=new URL(path,api);
      url.searchParams.set("deck",key);
      for(const [name,value] of Object.entries(params))
        url.searchParams.set(name,String(value));
      const response=await fetch(url,{cache:"no-store"});
      if(!response.ok)throw Error("Materialized replay HTTP "+response.status);
      const result=await response.json();
      if(result.schema!=="gorge-r2-materialized-response-v1"||
         result.status!=="ready"||result.deck!==key||
         result.version!==catalog.version)
        throw Error("Materialized replay cohort changed");
      return result;
    };
    const indexed=[];
    const ids=new Set();
    for(let page=0;page<catalog.page_count;page++){
      const result=await read("/v1/ui/page",{page});
      if(!live())return null;
      if(result.page?.page!==page||result.page?.total!==catalog.total||
         !Array.isArray(result.page.games)||result.page.games.length<1||
         result.page.games.length>25)
        throw Error("Incomplete materialized game index");
      for(const game of result.page.games){
        if(typeof game.game_id!=="string"||!game.game_id||
           ids.has(game.game_id)||!["win","loss"].includes(game.result))
          throw Error("Invalid materialized game identity");
        ids.add(game.game_id);
        indexed.push({page,id:game.game_id});
      }
    }
    if(indexed.length!==catalog.total)throw Error("Incomplete approved cohort");
    let original=null;
    const runs=[];
    // Bound concurrency and memory; the large-cohort path remains on demand.
    for(let offset=0;offset<indexed.length;offset+=4){
      const details=await Promise.all(indexed.slice(offset,offset+4).map(
        async item=>read("/v1/ui/game",{page:item.page,game_id:item.id})));
      if(!live())return null;
      for(let i=0;i<details.length;i++){
        const item=indexed[offset+i],detail=details[i];
        if(detail.game?.game_id!==item.id||
           !window.DeckGameOutcomes?.validate(detail.game.batch))
          throw Error("Invalid approved native replay");
        const batch=detail.game.batch;
        if(batch.deck_key!==key||batch.deck_sha256!==selected.sha||
           batch.engine!=="gorge"||batch.runs.length!==1)
          throw Error("Materialized deck revision or run count mismatch");
        if(original&&(batch.format!==original.format||
                      batch.scenario!==original.scenario||
                      batch.pilot_style!==original.pilot_style))
          throw Error("Mixed original Results cohort");
        // This release-check must demonstrate genuinely omniscient hands.
        const run=batch.runs[0];
        if(run.gorge_source?.visibility!=="omniscient"||
           run.gorge_source?.synthetic_simulation_only!==true||
           !Array.isArray(run.opening_hand)||
           run.opening_hand.length!==run.opening_hand_count||
           !Array.isArray(run.opening_hands_by_seat)||
           run.opening_hands_by_seat.length!==3)
          throw Error("Approved game is missing omniscient hand identities");
        original ||= batch;
        runs.push(run);
      }
    }
    const rounds=Math.max(...runs.map(run=>run.completed_rounds));
    const batch={...original,requested_rounds:rounds,
      runs:runs.map(run=>({...run,
        outcome:{...run.outcome,requested_rounds:rounds}}))};
    if(!window.DeckGameOutcomes.validate(batch))
      throw Error("Complete original Results cohort failed validation");
    return batch;
  }
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
    if(catalog.status!=="ready"){
      setResultsState("unavailable");
      statusMessage("R2 results not available for this deck.");
      return true;
    }
    const insightUrl=new URL("/v1/ui/insights",api);
    insightUrl.searchParams.set("deck",key);
    // Card insights are independently hash-verified by the Worker and must
    // cover the same immutable cohort version as the headline statistics.
    const insightResponse=await fetch(insightUrl,{cache:"no-store"});
    if(ticket!==generation||key!==window.__deckLabActiveKey)return true;
    if(insightResponse.ok){
      const item=await insightResponse.json();
      if(item.schema!=="gorge-r2-materialized-response-v1"||
         item.version!==catalog.version||item.deck!==key)throw Error("Insight cohort drift");
      if(item.status==="ready"){
        const report=item.insights;
        if(verifiedReport(report,catalog.total,catalog.version)){
          verifiedInsights=report;
          verifiedInsightCount=catalog.total;
        }
      }
    }else if(insightResponse.status!==404){
      // Existing outcomes remain available, but never use partial card rankings.
      verifiedInsights=null;verifiedInsightCount=null;
    }
    if(catalog.total<=200 && !preview){
      const batch=await originalBatchFromMaterialized(catalog,key,ticket,selected);
      return batch?{batch}:true;
    }
    const summary=catalog.summary;
    if(summary?.schema!=="gorge-r2-live-summary-v1" ||
       summary.cohort_version!==catalog.version ||
       summary.n!==catalog.total)throw Error("Materialized summary mismatch");
    const root=$("game-outcome-results"),reviewer=$("turn-reviewer-results");
    if(!root)return true;
    document.body.classList.add("r2-original-results-active");
    const rawReplay=$("gorge-replay-panel");
    if(rawReplay)rawReplay.style.setProperty("display","none","important");
    for(const id of ["simulation-snapshot",
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
    const overview=create("section");
    const detailStats=create("section");
    detailStats.className="r2-cohort-details";
    const matchupTitle=create("h4","Full-cohort opponent matchups");
    const matchupList=create("div");
    for(const group of (summary.groups?.opponents||[]).slice(0,12)){
      const row=create("p",group.name+" · "+group.wins+" wins / "+
        group.losses+" losses across "+group.n+" games ("+
        (group.win_rate*100).toFixed(1)+"%)");
      matchupList.append(row);
    }
    if(!matchupList.children.length)
      matchupList.append(create("p","No opponent matchup data available."));
    const turnsTitle=create("h4","Game length distribution · all approved games");
    const turnsList=create("div");
    window.DeckGameOutcomes.renderGameLengthHistogram(turnsList,
      (summary.game_turn_histogram||[]).map(item=>({
        round:item.turn,games:item.games
      })));
    detailStats.append(matchupTitle,matchupList,turnsTitle,turnsList);
    setResultsState("ready");
    const picker=create("div");picker.id="r2-game-picker";
    const replayHeading=create("p","");replayHeading.className="micro";
    const gameItems=[];
    const navHost=$("turn-reviewer-nav");
    navHost?.replaceChildren();
    const navigator=window.DeckGameOutcomes.gameNavigator(picker,(item,turn)=>
      showGame(item.id,item.page,item.label,turn),{controlsHost:navHost});
    picker.append(replayHeading);
    $("r2-game-picker")?.remove();
    reviewer.replaceChildren();
    reviewer.before(picker);
    window.DeckGameOutcomes.renderCohortOverview(overview,summary,{
      commanderName:selected.commander,commanderArt:selected.art
    });
    root.replaceChildren(overview,detailStats);
    let selectedRequest=0;
    const readJson=async(url)=>{
      const res=await fetch(url,{cache:"no-store"});
      if(!res.ok)throw Error("R2 Results HTTP "+res.status);
      return res.json();
    };
    const live=()=>ticket===generation&&key===window.__deckLabActiveKey;
    const showGame=async(gameId,pageNumber,label,turn=null)=>{
      const request=++selectedRequest;
      replayHeading.textContent="Loading selected game…";
      try{
        const url=new URL("/v1/ui/game",api);
        url.searchParams.set("deck",key);
        url.searchParams.set("page",String(pageNumber));
        url.searchParams.set("game_id",gameId);
        const detail=await readJson(url);
        if(!live()||request!==selectedRequest)return;
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
        replayHeading.textContent="";
        window.DeckGameOutcomes.renderTurnReviewer(reviewer,[batch],{
          deckKey:key,deckHash:selected.sha,
          commanderName:selected.commander,commanderArt:selected.art,
          isGorge:true,reviewerRoot:reviewer,reviewerPanel:panel,
          lookupRecordedCard:window.GorgeDeckLabCardInfo,
          deckCardNames:selected.cardNames,
          renderMana:value=>window.GorgeDeckLabMana?.(value),
          onOpenRecordedCard:name=>window.GorgeDeckLabOpenCard?.(name),
          onOpenTokenCard:card=>window.GorgeDeckLabOpenTokenCard?.(card),
          hideGameSelector:true,displayGameLabel:label,focusTurn:turn,
          fullCardInsights:verifiedInsights,
          fullCohortGames:verifiedInsightCount
        });
        if(turn!==null)panel?.scrollIntoView?.({behavior:"smooth",block:"start"});
      }catch(err){
        if(live()&&request===selectedRequest)replayHeading.textContent="Replay unavailable: "+String(err.message||err);
      }
    };
    const loadGames=async()=>{
      try{
        const seen=new Set();
        for(let number=0;number<catalog.page_count;number++){
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
        for(const g of result.page.games){
          if(typeof g.game_id!=="string"||seen.has(g.game_id)||!Array.isArray(g.opponent_decks))
            throw Error("Invalid or duplicate game metadata");
          seen.add(g.game_id);
          const label="Game "+seen.size+" · "+(g.result==="win"?"Win":"Loss")+" · "+(g.turns??"?")+
            " turns · "+g.opponent_decks.map(d=>window.DeckDisplayNames?.deck(d)||d).join(", ");
          gameItems.push({id:g.game_id,page:number,label,result:g.result,search:label});
        }
        navigator.setGames(gameItems);
        }
        if(seen.size!==summary.n)throw Error("Incomplete game index");
      }catch(err){
        if(live())replayHeading.textContent="Some games could not be loaded: "+String(err.message||err);
      }
    };
    document.dispatchEvent(new CustomEvent("gorge:cohort-ready",{detail:{
      deck:key,version:catalog.version,total:catalog.total
    }}));
    const loadingGames=loadGames();
    showCohortInsights(verifiedInsights,summary.n,catalog.version,async(gameId,turn)=>{
      await loadingGames;
      if(!live())return;
      navigator.clearFilters();
      if(!navigator.choose(gameId,turn))replayHeading.textContent="Example game is unavailable in this cohort.";
    });
    renderedDeck=key;
    const status=$("game-outcome-status");
    if(status)status.textContent=summary.n+" approved games · complete-cohort summary";
    return true;
  }

  async function refresh(key=window.__deckLabActiveKey,attempt=0){
    if(recoveryTimer!==null){clearTimeout(recoveryTimer);recoveryTimer=null;}
    const ticket=++generation;
    $("r2-game-picker")?.remove();
    renderedDeck=null;
    verifiedInsights=null;verifiedInsightCount=null;
    setResultsState("loading");
    const selected=window.GorgeDeckLabSelectedDeck?.(key);
    if(!key||!selected?.eligible){
      setResultsState("unavailable");
      statusMessage("R2 results not available for this deck.");
      return;
    }
    statusMessage("Checking approved Gorge game results…");
    try{
      const materialized=await loadMaterialized(key,ticket,selected);
      if(materialized===true)return;
      let result;
      if(materialized?.batch){
        result={schema:"gorge-r2-original-ui-batch-response-v1",deck:key,
          population:"approved_current_decisive_only",status:"ready",
          batch:materialized.batch};
      }else{
        const url=new URL("/v1/ui/batch",api);
        url.searchParams.set("deck",key);
        const response=await fetch(url,{cache:"no-store"});
        if(!response.ok)throw Error("Worker returned HTTP "+response.status);
        result=await response.json();
      }
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
        setResultsState("unavailable");
        statusMessage("R2 results not available for this deck. "+description);
        return;
      }
      const batch=result.batch;
      if(!batch||batch.deck_key!==key||
         batch.deck_sha256!==selected.sha){
        setResultsState("unavailable");
        statusMessage("R2 results not available for this deck revision.");
        return;
      }
      if(!window.DeckGameOutcomes?.validate(batch))
        throw Error("Original Results renderer rejected Worker batch");
      const root=$("game-outcome-results"),reviewer=$("turn-reviewer-results");
      if(!root)return;
      document.body.classList.add("r2-original-results-active");
      const rawReplay=$("gorge-replay-panel");
      if(rawReplay)rawReplay.style.setProperty("display","none","important");
      const panel=$("turn-reviewer-panel");
      if(panel)panel.hidden=false;
      for(const id of ["simulation-snapshot",
                        "development-panel","archive-observation-details",
                        "opponent-replay-panel"]){
        const element=$(id);if(element)element.hidden=true;
      }
      const legacyRefresh=$("game-outcome-refresh");
      if(legacyRefresh)legacyRefresh.hidden=true;
      const diagnostic=$("pane-records")?.querySelector(".diagnostic-panel");
      if(diagnostic)diagnostic.hidden=true;
      setResultsState("ready");
      const report=verifiedInsights||window.__gorgeCardInsights?.[key]||null;
      const population=verifiedInsightCount||window.__gorgeFullCohort?.decks?.[key]?.n||batch.runs.length;
      let reviewRecordedRun=null;
      if(verifiedReport(report,population)){
        showCohortInsights(report,population);
      }else{
        // Use only the approved native games already returned by R2, with an
        // explicit observed-game denominator. Do not call them full-cohort.
        window.DeckGameOutcomes.renderRecordedBatchInsights(
          $("key-insights-grid"),batch,{
            deckKey:key,deckHash:selected.sha,commanderName:selected.commander,
            onReviewRun:(id,seed,turn)=>reviewRecordedRun?.(id,seed,turn),
            lookupRecordedCard:window.GorgeDeckLabCardInfo,
            deckCardNames:selected.cardNames,
            renderMana:value=>window.GorgeDeckLabMana?.(value),
            onOpenRecordedCard:name=>window.GorgeDeckLabOpenCard?.(name),
            onOpenTokenCard:card=>window.GorgeDeckLabOpenTokenCard?.(card)
          });
      }
      window.DeckGameOutcomes.render(root,[batch],{
        deckKey:key,deckHash:selected.sha,
        commanderName:selected.commander,commanderArt:selected.art,
        isGorge:true,externalInsights:true,reviewerRoot:reviewer,reviewerPanel:panel,
        onReviewerReady:jump=>{reviewRecordedRun=jump},
        lookupRecordedCard:window.GorgeDeckLabCardInfo,
        portraitFor:bucket=>window.GorgeDeckLabOpponentPortrait?.(bucket),
        deckCardNames:selected.cardNames,
        renderMana:value=>window.GorgeDeckLabMana?.(value),
        onOpenRecordedCard:name=>window.GorgeDeckLabOpenCard?.(name),
          onOpenTokenCard:card=>window.GorgeDeckLabOpenTokenCard?.(card),
        fullCardInsights:verifiedInsights||window.__gorgeCardInsights?.[key]||null,
        fullCohortGames:verifiedInsightCount||window.__gorgeFullCohort?.decks?.[key]?.n||null
      });
      renderedDeck=key;
      const label=batch.runs.length+" approved native Gorge game"+
        (batch.runs.length===1?"":"s")+" · original Results UI";
      const status=$("game-outcome-status");
      if(status)status.textContent=label;
    }catch(err){
      if(ticket!==generation||key!==window.__deckLabActiveKey)return;
      setResultsState("unavailable");
      statusMessage("R2 results not available: "+String(err.message||err));
      if(attempt<RECOVERY_DELAY_MS.length){
        recoveryTimer=setTimeout(()=>{
          recoveryTimer=null;
          if(ticket===generation&&key===window.__deckLabActiveKey)
            refresh(key,attempt+1);
        },RECOVERY_DELAY_MS[attempt]);
      }
    }
  }
  window.R2OriginalResults={refresh,ownsRenderedDeck};
  // App boot asynchronously chooses its initial deck and calls refresh.
})();
