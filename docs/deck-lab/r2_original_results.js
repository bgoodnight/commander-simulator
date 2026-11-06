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
  let generation=0,renderedDeck=null,retryTimer=null;
  const RETRY_DELAYS=[350,1200]; // Bounded recovery for a transient initial Worker failure.
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
  async function refresh(key=window.__deckLabActiveKey,attempt=0){
    if(retryTimer!==null){clearTimeout(retryTimer);retryTimer=null;}
    const ticket=++generation;
    renderedDeck=null;
    const selected=window.GorgeDeckLabSelectedDeck?.(key);
    if(!key||!selected?.eligible)return;
    statusMessage("Checking approved Gorge game results…");
    try{
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
      // A first-load network or renderer failure must not require changing
      // commander to kick the adapter. Keep retries scoped to this selection.
      if(attempt<RETRY_DELAYS.length){
        retryTimer=setTimeout(()=>{
          retryTimer=null;
          if(ticket===generation&&key===window.__deckLabActiveKey)
            refresh(key,attempt+1);
        },RETRY_DELAYS[attempt]);
      }
    }
  }
  window.R2OriginalResults={refresh,ownsRenderedDeck};
  // App boot asynchronously chooses its initial deck and calls refresh.
})();
