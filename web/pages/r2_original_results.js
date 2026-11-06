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
      $("r2-game-picker")?.remove();
      $("key-insights-grid")?.replaceChildren();
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
  function showCohortInsights(report,total,version=null){
    const grid=$("key-insights-grid");
    if(!grid)return;
    if(!verifiedReport(report,total,version)){
      const placeholder=document.createElement("p");
      placeholder.className="game-outcome-empty";
      placeholder.textContent="Approved game results are available; named-card findings "+
        "have not yet been published for this cohort.";
      grid.replaceChildren(placeholder);
      return;
    }
    $("key-insights-empty").hidden=true;
    window.DeckGameOutcomes.renderCohortInsights(grid,report,total,{
      lookupRecordedCard:window.GorgeDeckLabCardInfo,
      renderMana:value=>window.GorgeDeckLabMana?.(value),
      onOpenRecordedCard:name=>window.GorgeDeckLabOpenCard?.(name)
    });
    // Core section visibility is tied to result readiness, not card ranking count.
  }
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
    if(catalog.total<=200 && !preview)return false;
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
    const histogram=summary.game_turn_histogram||[];
    const maxFrequency=Math.max(1,...histogram.map(item=>item.games));
    for(const group of histogram){
      const row=create("div");
      const label=create("span","Turn "+group.turn+": "+group.games+" games ");
      const bar=create("progress");
      bar.max=maxFrequency;bar.value=group.games;
      bar.setAttribute("aria-label","Games ending on turn "+group.turn);
      row.append(label,bar);
      turnsList.append(row);
    }
    if(!turnsList.children.length)
      turnsList.append(create("p","No game length data available."));
    detailStats.append(matchupTitle,matchupList,turnsTitle,turnsList);
    setResultsState("ready");
    showCohortInsights(verifiedInsights,summary.n,catalog.version);
    const picker=create("div");picker.id="r2-game-picker";
    const gameSelect=create("select");gameSelect.className="game-outcome-scenario-select";
    gameSelect.setAttribute("aria-label","Choose recorded game");
    const placeholder=create("option","Choose a game to review");placeholder.value="";
    gameSelect.appendChild(placeholder);
    const replayHeading=create("p","Loading games…");replayHeading.className="micro";
    picker.append(gameSelect,replayHeading);
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
    const showGame=async(gameId,pageNumber,label)=>{
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
        replayHeading.textContent="Selected game replay · individual game (not cohort statistics)";
        window.DeckGameOutcomes.renderTurnReviewer(reviewer,[batch],{
          deckKey:key,deckHash:selected.sha,
          commanderName:selected.commander,commanderArt:selected.art,
          isGorge:true,reviewerRoot:reviewer,reviewerPanel:panel,
          lookupRecordedCard:window.GorgeDeckLabCardInfo,
          deckCardNames:selected.cardNames,
          renderMana:value=>window.GorgeDeckLabMana?.(value),
          onOpenRecordedCard:name=>window.GorgeDeckLabOpenCard?.(name),
          hideGameSelector:true,displayGameLabel:label,
          fullCardInsights:verifiedInsights,
          fullCohortGames:verifiedInsightCount
        });
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
          const option=create("option",label);option.value=g.game_id;option.dataset.page=String(number);
          gameSelect.appendChild(option);
        }
        if(number===0)replayHeading.textContent="Choose a game to review.";
        }
        if(seen.size!==summary.n)throw Error("Incomplete game index");
      }catch(err){
        if(live())replayHeading.textContent="Some games could not be loaded: "+String(err.message||err);
      }
    };
    gameSelect.addEventListener("change",()=>{
      const option=gameSelect.selectedOptions[0];
      if(option?.value)showGame(option.value,Number(option.dataset.page),option.textContent);
    });
    renderedDeck=key;
    const status=$("game-outcome-status");
    if(status)status.textContent=summary.n+" approved games · complete-cohort summary";
    void loadGames();
    return true;
  }

  async function refresh(key=window.__deckLabActiveKey){
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
      if(verifiedReport(report,population)){
        showCohortInsights(report,population);
      }else{
        // Use only the approved native games already returned by R2, with an
        // explicit observed-game denominator. Do not call them full-cohort.
        window.DeckGameOutcomes.renderRecordedBatchInsights(
          $("key-insights-grid"),batch,{
            deckKey:key,deckHash:selected.sha,commanderName:selected.commander,
            lookupRecordedCard:window.GorgeDeckLabCardInfo,
            deckCardNames:selected.cardNames,
            renderMana:value=>window.GorgeDeckLabMana?.(value),
            onOpenRecordedCard:name=>window.GorgeDeckLabOpenCard?.(name)
          });
      }
      window.DeckGameOutcomes.render(root,[batch],{
        deckKey:key,deckHash:selected.sha,
        commanderName:selected.commander,commanderArt:selected.art,
        isGorge:true,reviewerRoot:reviewer,reviewerPanel:panel,
        lookupRecordedCard:window.GorgeDeckLabCardInfo,
        deckCardNames:selected.cardNames,
        renderMana:value=>window.GorgeDeckLabMana?.(value),
        onOpenRecordedCard:name=>window.GorgeDeckLabOpenCard?.(name),
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
    }
  }
  window.R2OriginalResults={refresh,ownsRenderedDeck};
  // App boot asynchronously chooses its initial deck and calls refresh.
})();
