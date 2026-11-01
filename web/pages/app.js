/* Commander Deck Lab — standalone static frontend, no framework.
 * Original audio cues generated with Web Audio; no borrowed game sound files.
 * No simulation logic is executed: all observation traces come from Python.
 */
"use strict";
const $ = id => document.getElementById(id);
const NS = "http://www.w3.org/2000/svg";
const BASIC = new Set(["Plains","Island","Swamp","Mountain","Forest","Wastes",
  "Snow-Covered Plains","Snow-Covered Island","Snow-Covered Swamp",
  "Snow-Covered Mountain","Snow-Covered Forest"]);
const LABELS = {
  magnus_premium:"Magnus · Premium",magnus_budget:"Magnus · Budget",
  wretched_ranks:"Wretched Ranks · Gisa",
  mortarion_current:"Mortarion · Current",mortarion_ideal:"Mortarion · Ideal",
  necron_dynasties:"Necron Dynasties"
};
const MODE_NOTE = "Precomputed observation only · no spells, abilities, combat or win rates modeled.";
let data=null, archives=null, allNames=[], selected=null, activeTab="overview";
let cachedByName = new Map(),extraCards={},activeCounts=null,history=[],localVersions=[];
const soundKey="commander-deck-lab-sound-v1";
function readSoundPreference(){
  try{return localStorage.getItem(soundKey)!=="off"}catch(e){return true}
}
let selectedSeed="0",soundEnabled=readSoundPreference(),audioUnlocked=false,audio=null,lastRecord=null,autoTimer=null;
let selectedVersionId=null,preferredByCommander={},lastCommanderId=null;
const pageName=location.pathname.endsWith("/results.html")?"results":
  location.pathname.endsWith("/editor.html")?"editor":"summary";
const PAGE_INFO={results:"Early turns",summary:"Deck overview",editor:"Deck editor"};
let scrollObserver=null;
const storageKey="commander-deck-lab-pages-v1";
const el=(tag,text,className)=>{
  const node=document.createElement(tag);
  if(text!==undefined&&text!==null)node.textContent=String(text);
  if(className)node.className=className;
  return node;
};
function clear(node){if(node)node.replaceChildren();}
function note(msg,error=false){
  const status=$("toast");
  status.textContent=msg;status.hidden=false;
  status.style.borderColor=error?"#d9a196":"#dabb80";
  clearTimeout(note._timeout);
  note._timeout=setTimeout(()=>status.hidden=true,4100);
}
function originalSound(kind="click"){
  if(!soundEnabled||!audioUnlocked)return;
  try{
    const Audio=window.AudioContext||window.webkitAudioContext;
    if(!Audio)return;
    if(!audio)audio=new Audio();
    if(audio.state==="suspended")audio.resume();
    const now=audio.currentTime;
    const notes={
      click:[[370,.06,.045],[555,.08,.025]],
      summon:[[174,.18,.12],[260,.3,.14],[392,.45,.09]],
      success:[[392,.12,.07],[494,.16,.07],[660,.22,.07]],
      error:[[147,.11,.08],[131,.14,.05]],
      page:[[240,.055,.03],[340,.09,.02]]
    };
    for(const [freq,duration,volume] of (notes[kind]||notes.click)){
      const osc=audio.createOscillator(),gain=audio.createGain();
      osc.type=kind==="summon"?"sine":"triangle";
      osc.frequency.setValueAtTime(freq,now);
      osc.frequency.exponentialRampToValueAtTime(Math.max(40,freq*.93),now+duration);
      gain.gain.setValueAtTime(.001,now);
      gain.gain.exponentialRampToValueAtTime(volume,now+.012);
      gain.gain.exponentialRampToValueAtTime(.001,now+duration);
      osc.connect(gain).connect(audio.destination);
      osc.start(now);osc.stop(now+duration+.015);
    }
  }catch(e){soundEnabled=false;syncSoundControl();$("audio-toggle").textContent="♫ Sound unavailable";}
}
function syncSoundControl(){
  const button=$("audio-toggle");
  button.setAttribute("aria-pressed",String(soundEnabled));
  button.textContent=soundEnabled?"♫ Sound on":"♫ Sound off";
  button.title=soundEnabled?"Mute sound effects":"Enable sound effects";
}
function enableSound(){
  soundEnabled=!soundEnabled;
  try{localStorage.setItem(soundKey,soundEnabled?"on":"off")}catch(e){}
  syncSoundControl();
  if(soundEnabled)originalSound("success");
}
function safeText(value){return String(value??"");}
function cardInfo(name){
  return cachedByName.get(name.toLowerCase())||null;
}
function cardForId(id){return extraCards[id]||data.cards[id]||null;}
function addAliases(item){
  if(!item||!item.oracle_id)return;
  cachedByName.set(item.name.toLowerCase(),item);
  for(const face of item.face_names||[])cachedByName.set(face.toLowerCase(),item);
}
function loadLocal(){
  try{
    const stored=JSON.parse(localStorage.getItem(storageKey)||"{}");
    if(stored&&typeof stored==="object"){
      const arr=Array.isArray(stored.versions)?stored.versions:[];
      localVersions=arr.filter(v=>v&&typeof v.id==="string"&&
        typeof v.baseKey==="string"&&v.counts&&typeof v.counts==="object").slice(0,60);
      preferredByCommander=stored.preferredByCommander&&typeof stored.preferredByCommander==="object"?
        stored.preferredByCommander:{};
      lastCommanderId=typeof stored.lastCommanderId==="string"?stored.lastCommanderId:null;
      if(stored.extraCards&&typeof stored.extraCards==="object"){
        for(const item of Object.values(stored.extraCards)){
          if(item&&typeof item.name==="string"&&typeof item.oracle_id==="string"&&
              Array.isArray(item.color_identity)){
            extraCards[item.oracle_id]=item;addAliases(item);
          }
        }
      }
    }
  }catch(e){localVersions=[];extraCards={};}
}
function persist(){
  try{localStorage.setItem(storageKey,JSON.stringify({
    versions:localVersions.slice(0,60),preferredByCommander,lastCommanderId,extraCards
  }));return true}
  catch(e){note("Browser storage unavailable. Export the decklist to keep it.",true);return false}
}
function imageNode(card,art=true,className=""){
  if(!card||!(art?card.art:card.image)){
    const fallback=el("div","✧  "+safeText(card?.name||"Unknown Legend"),"no-image");
    if(className)fallback.classList.add(className);return fallback;
  }
  const img=el("img",null,className);
  img.src=art?card.art:card.image;
  img.alt=card.name+" card illustration";
  img.loading="lazy";img.referrerPolicy="no-referrer";
  img.onerror=()=>{
    const fallback=el("div","✧  "+card.name,"no-image");
    if(img.parentElement)img.replaceWith(fallback);
  };
  return img;
}
function selectedDeck(){return data.decks.find(d=>d.key===selected);}
function commanderCard(deck){return cardForId(deck.commander_id);}
function svg(tag,attrs={}){
  const node=document.createElementNS(NS,tag);
  for(const [k,v] of Object.entries(attrs))node.setAttribute(k,String(v));
  return node;
}
function makeBars(items,{color="#bfa066",maxHeight=130}={}){
  const width=540,height=185,left=20,right=8,top=12,bottom=36;
  const chart=svg("svg",{class:"bar-chart",viewBox:`0 0 ${width} ${height}`,
    role:"img","aria-label":items.map(x=>x[0]+": "+x[1]).join(", ")});
  const max=Math.max(1,...items.map(i=>i[1]));
  for(let k=0;k<=3;k++){
    const y=top+(maxHeight*k/3);
    chart.appendChild(svg("line",{x1:left,y1:y,x2:width-right,y2:y,class:"gridline"}));
  }
  const gap=7,barWidth=(width-left-right-(items.length-1)*gap)/Math.max(1,items.length);
  items.forEach(([label,value],i)=>{
    const x=left+i*(barWidth+gap);
    const barHeight=value/max*maxHeight;
    chart.appendChild(svg("rect",{x,y:top+maxHeight-barHeight,width:barWidth,
      height:Math.max(1,barHeight),rx:3,fill:color,
      class:"bar "+(label==="Land"?"bar-land":"")}));
    const val=svg("text",{x:x+barWidth/2,y:top+maxHeight-barHeight-6,
      "text-anchor":"middle"});val.textContent=value;chart.appendChild(val);
    const text=svg("text",{x:x+barWidth/2,y:height-21,
      "text-anchor":"middle"});text.textContent=label.length>10?label.slice(0,9)+"…":label;
    chart.appendChild(text);
  });
  return chart;
}
function sameCommanderDecks(commanderId){
  return data.decks.filter(deck=>deck.commander_id===commanderId);
}
function deckVersionsForCommander(commanderId){
  const keys=new Set(sameCommanderDecks(commanderId).map(d=>d.key));
  return localVersions.filter(v=>keys.has(v.baseKey))
    .sort((a,b)=>String(b.updated||b.created||"").localeCompare(String(a.updated||a.created||"")));
}
function latestSelectionForCommander(commanderId){
  const preferred=preferredByCommander[commanderId];
  if(preferred?.key&&sameCommanderDecks(commanderId).some(d=>d.key===preferred.key)){
    const version=localVersions.some(v=>v.id===preferred.version&&v.baseKey===preferred.key)?
      preferred.version:null;
    return {key:preferred.key,version};
  }
  const saved=deckVersionsForCommander(commanderId)[0];
  if(saved)return {key:saved.baseKey,version:saved.id};
  return {key:sameCommanderDecks(commanderId)[0]?.key,version:null};
}
function versionById(id){
  return localVersions.find(v=>v.id===id&&v.baseKey===selected)||null;
}
function activeVersion(){return selectedVersionId?versionById(selectedVersionId):null;}
function hasUnsavedChanges(){
  if(!selected||!activeCounts)return false;
  const reference=activeVersion()?.counts||initialCounts();
  return [...new Set([...Object.keys(reference),...Object.keys(activeCounts)])]
    .some(name=>(reference[name]||0)!==(activeCounts[name]||0));
}
function isUnsimulatedVersion(){
  if(activeVersion())return true;
  if(!selected||!activeCounts)return false;
  const original=initialCounts(),names=new Set([
    ...Object.keys(original),...Object.keys(activeCounts)
  ]);
  return [...names].some(name=>(original[name]||0)!==(activeCounts[name]||0));
}
function visibleCounts(){
  if(activeCounts&&typeof activeCounts==="object")return activeCounts;
  return initialCounts();
}
function displayDeckCards(){
  const deck=selectedDeck();
  if(!deck)return [];
  const commander=deck.cards.find(c=>c.zone==="Commander");
  const result=commander?[commander]:[];
  for(const [name,qty] of Object.entries(visibleCounts())){
    if(!qty)continue;
    const card=cardInfo(name);
    result.push({name,qty,zone:"Library",oracle_id:card?.oracle_id||null});
  }
  return result;
}
function activeDeckTitle(){
  return activeVersion()?.title||
    (isUnsimulatedVersion()?"Unsaved deck draft · "+(LABELS[selected]||selected):
      LABELS[selected]||selectedDeck()?.commander||"");
}
function updateSelectionBadge(){
  if(!selected)return;
  const deck=selectedDeck(),card=commanderCard(deck),portrait=$("medallion-portrait");
  clear(portrait);portrait.appendChild(imageNode(card,true,"medallion-art"));
  $("commander-medallion").setAttribute("aria-label","Change commander from "+deck.commander);
  $("active-commander").textContent=deck.commander;
  $("active-deck-name").textContent=activeDeckTitle();
  $("active-deck-state").textContent=isUnsimulatedVersion()?
    "Edited deck · no cached results":"Cached results available";
  const link=$("change-deck-link"),url=new URL("./editor.html",location.href);
  url.searchParams.set("deck",selected);
  if(selectedVersionId)url.searchParams.set("version",selectedVersionId);
  link.href=url.href;
}
function buildDeckRail(){
  const rail=$("commander-rail");clear(rail);
  const seen=new Set();
  for(const deck of data.decks){
    if(seen.has(deck.commander_id))continue;
    seen.add(deck.commander_id);
    const card=commanderCard(deck),button=el("button",null,"commander-choice");
    button.type="button";button.dataset.commander=deck.commander_id;
    button.appendChild(imageNode(card,true,"choice-art"));
    const details=el("span");details.appendChild(el("strong",deck.commander));
    details.appendChild(el("small",sameCommanderDecks(deck.commander_id).length+
      " built-in deck(s) · "+deckVersionsForCommander(deck.commander_id).length+" saved"));
    button.appendChild(details);
    button.addEventListener("click",()=>{
      if(hasUnsavedChanges()&&!window.confirm(
          "Discard unsaved deck changes? You can save this version first."))return;
      const choice=latestSelectionForCommander(deck.commander_id);
      summon(choice.key,{versionId:choice.version});
      closeCommanderPicker();originalSound("summon");
    });
    rail.appendChild(button);
  }
}
function closeCommanderPicker(){
  $("commander-picker").hidden=true;
  $("commander-medallion").setAttribute("aria-expanded","false");
}
function toggleCommanderPicker(){
  const open=$("commander-picker").hidden;
  $("commander-picker").hidden=!open;
  $("commander-medallion").setAttribute("aria-expanded",String(open));
  if(open)buildDeckRail();
  originalSound("click");
}
function syncPageNavigation(){
  const params=new URLSearchParams(location.search);
  params.set("deck",selected);
  if(selectedVersionId)params.set("version",selectedVersionId);
  else params.delete("version");
  try{window.history.replaceState(null,"",location.pathname+"?"+params.toString())}
  catch(e){/* history may be unavailable in local previews */}
  for(const link of document.querySelectorAll(".site-link")){
    const target=new URL(link.href,location.href);
    target.searchParams.set("deck",selected);
    if(selectedVersionId)target.searchParams.set("version",selectedVersionId);
    else target.searchParams.delete("version");
    link.href=target.href;
  }
  updateSelectionBadge();
}
function summon(key,{versionId=null,remember=true}={}){
  const deck=data.decks.find(d=>d.key===key);
  if(!deck)return;
  selected=key;
  selectedVersionId=versionId&&localVersions.some(v=>v.id===versionId&&v.baseKey===key)?
    versionId:null;
  activeCounts=selectedVersionId?{...versionById(selectedVersionId).counts}:null;
  history=[];
  if(remember){
    lastCommanderId=deck.commander_id;
    preferredByCommander[deck.commander_id]={key,version:selectedVersionId};
    persist();
  }
  $("app-content").hidden=false;
  $("app-content").style.animation="none";
  void $("app-content").offsetWidth;$("app-content").style.animation="";
  selectedSeed=String(data.seeds[0]);
  renderOverview();renderLibrary();renderRecords();initializeDraft();
  showPage();syncPageNavigation();
}
function showPage(){
  const enabled={
    results:["records","insights"],
    summary:["overview"],
    editor:["library","workshop"]
  }[pageName];
  for(const pane of document.querySelectorAll(".tab-pane"))
    pane.hidden=!enabled.includes(pane.id.replace("pane-",""));
  for(const link of document.querySelectorAll(".site-link")){
    const active=link.dataset.page===pageName;
    link.classList.toggle("active",active);
    if(active)link.setAttribute("aria-current","page");
    else link.removeAttribute("aria-current");
  }
  renderPageIntro();
  document.title=PAGE_INFO[pageName]+" | Commander Deck Lab";
  if(pageName==="results")renderScrollStory();
}
function deckFacts(){
  const cards=displayDeckCards();
  let total=0,lands=0,manaTotal=0,manaCards=0;
  for(const entry of cards){
    const card=cardForId(entry.oracle_id),qty=entry.qty;
    total+=qty;
    if(card?.category==="Land"){lands+=qty;continue}
    if(card&&card.mana_value!==null&&card.mana_value!==undefined&&Number.isFinite(Number(card.mana_value))){
      manaTotal+=Number(card.mana_value)*qty;manaCards+=qty;
    }
  }
  return {total,lands,averageMana:manaCards?(manaTotal/manaCards).toFixed(1):"—"};
}
function renderPageIntro(){
  const intro=$("page-introduction");clear(intro);
  const facts=deckFacts();
  let detail=facts.total+" cards · "+facts.lands+" lands";
  if(pageName==="results"){
    detail=isUnsimulatedVersion()?"No archived observations for this version":
      (aggregate?aggregate.n+" archived hands · 6 turns":"Archived observations");
  }
  intro.append(el("h1",PAGE_INFO[pageName]),el("p",detail));
}
function renderOverview(){
  const deck=selectedDeck(),c=commanderCard(deck);
  $("overview-name").textContent=deck.commander;
  const art=$("overview-art");clear(art);
  const node=imageNode(c,true,"big-portrait");node.classList.add("big-portrait");art.appendChild(node);
  const metrics=$("overview-metrics");clear(metrics);
  const cards=displayDeckCards();
  const facts=deckFacts();
  for(const [value,label] of [[facts.total,"Cards"],[facts.lands,"Lands"],[facts.averageMana,"Avg. nonland mana value"]]){
    const x=el("div",null,"metric");
    x.appendChild(el("strong",value));x.appendChild(el("span",label));metrics.appendChild(x);
  }
  const tags=$("overview-tags");clear(tags);
  for(const txt of [isUnsimulatedVersion()?"Edited deck · no archived results":"Archived observations available"]){
    tags.appendChild(el("span",txt,"chip"));
  }
  const typeCounts={};
  for(const item of cards){
    const kind=cardForId(item.oracle_id)?.category||"Other";
    typeCounts[kind]=(typeCounts[kind]||0)+item.qty;
  }
  const types=Object.entries(typeCounts).sort((a,b)=>b[1]-a[1]);
  const typeBox=$("type-chart");clear(typeBox);typeBox.appendChild(makeBars(types,{color:"#bda46d"}));
  const curve=Array.from({length:9},(_,i)=>[i===8?"8+":String(i),0]);
  for(const x of cards){
    const item=cardForId(x.oracle_id);
    if(!item||item.category==="Land")continue;
    const mv=Math.max(0,Math.min(8,Math.floor(Number(item.mana_value)||0)));
    curve[mv][1]+=x.qty;
  }
  const curveBox=$("mana-chart");clear(curveBox);
  curveBox.appendChild(makeBars(curve,{color:"#80bdb2"}));
}
function libraryRows(){
  const needle=$("library-search").value.trim().toLowerCase();
  const category=$("library-category").value;
  return displayDeckCards().filter(x=>{
    const card=cardForId(x.oracle_id);
    return (!needle||[x.name,card?.type_line,card?.oracle_text].join(" ").toLowerCase().includes(needle))
      && (category==="all"||card?.category===category);
  }).sort((a,b)=>a.zone==="Commander"?-1:b.zone==="Commander"?1:
    a.name.localeCompare(b.name));
}
function renderLibrary(){
  const root=$("library-rows");clear(root);
  const rows=libraryRows();
  $("library-count").textContent=" · "+rows.reduce((n,x)=>n+x.qty,0)+" cards";
  for(const item of rows){
    const card=cardForId(item.oracle_id),tr=el("tr");
    tr.appendChild(el("td",item.qty));
    const col=el("td"),btn=el("button",item.name,"selectable-card");
    btn.type="button";btn.addEventListener("click",()=>showCard(item.oracle_id));
    col.appendChild(btn);
    tr.append(col,el("td",card?.type_line||"Unknown"));
    tr.appendChild(el("td",card?.mana_cost||"—"));root.appendChild(tr);
  }
  if(!rows.length){
    const tr=el("tr"),td=el("td","No matching cards.");td.colSpan=4;tr.appendChild(td);root.appendChild(tr);
  }
}
function showCard(id){
  const card=cardForId(id);if(!card)return;
  const box=$("modal-art");clear(box);box.appendChild(imageNode(card,false));
  $("card-dialog-title").textContent=card.name;
  $("modal-meta").textContent=card.type_line+" · Mana value "+card.mana_value;
  $("modal-oracle").textContent=card.oracle_text||"No Oracle text in the saved record.";
  $("modal-scryfall").href=card.scryfall||"https://scryfall.com/";
  $("dialog-backdrop").hidden=false;$("modal-close").focus();
  originalSound("click");
}
function closeCard(){$("dialog-backdrop").hidden=true}
/* Summary first, and the detailed observation archive second. No fixed
 * deck-specific interpretation: findings are built from the 11 cached seeds.
 */
let aggregate=null;
function showAggregate(){
  const result=$("results-kpis"),intro=$("results-takeaway");
  clear(result);clear(intro);
  aggregate=null;
  if(isUnsimulatedVersion()){
    $("results-sample").textContent="No matched archive";
    $("results-provenance").textContent="The saved deck has no pinned Python observations.";
    intro.appendChild(el("p","This modified deck must be exported and run through Python before its performance can be assessed."));
    return;
  }
  if(!window.DeckInsights){
    intro.appendChild(el("p","The local results analysis could not be loaded."));
    return;
  }
  aggregate=window.DeckInsights.summarize(archives[selected]);
  if(!aggregate){
    intro.appendChild(el("p","No verified cached observations are available."));
    return;
  }
  $("results-sample").textContent=aggregate.n+" cached seeds · 6 turns";
  $("results-provenance").textContent="Derived from "+aggregate.n+
    " fixed-seed, keep-seven observations. Only basic lands and Command Tower are modeled; no casts, combat or win rates.";
  const metrics=[
    {label:"2–5 modeled lands in opening hand",value:aggregate.metrics.earlyLand.count+" / "+aggregate.n,
      detail:aggregate.metrics.earlyLand.pct+"% of archived hands",target:"opening"},
    {label:"≥3 modeled sources by turn 3",value:aggregate.metrics.t3Sources.count+" / "+aggregate.n,
      detail:aggregate.metrics.t3Sources.pct+"% of archived runs",target:"resources"},
    {label:"Any mana-value candidate on turn 4",value:aggregate.metrics.t4Candidate.count+" / "+aggregate.n,
      detail:aggregate.metrics.t4Candidate.pct+"% of archived runs",target:"candidates"}
  ];
  for(const m of metrics){
    const card=el("button",null,"result-stat");
    card.type="button";
    card.append(el("span",m.value,"result-stat-value"),
      el("span",m.label,"result-stat-label"),el("small",m.detail));
    card.setAttribute("aria-label",m.label+": "+m.value+", "+m.detail+". Scroll to examine evidence.");
    card.onclick=()=>{
      const target=document.querySelector('.story-step[data-chart="'+m.target+'"]');
      target?.scrollIntoView({behavior:window.matchMedia?.("(prefers-reduced-motion: reduce)").matches?
        "auto":"smooth",block:"center"});
      originalSound("page");
    };
    result.appendChild(card);
  }
  const parts=window.DeckInsights.findings(aggregate);
  intro.appendChild(el("strong","What to take from these observations"));
  intro.appendChild(el("p",parts.map(p=>p.summary).join(" ")));
  intro.appendChild(el("p","This is a small, selected set of archived draws. These metrics describe opening land and mana-value screens—not actual casting, board development, victory or deck strength.","micro"));
}
function renderRecords(){
  const seedSelect=$("seed-select");clear(seedSelect);
  for(const seed of data.seeds){
    const option=el("option","Seed "+seed);option.value=String(seed);
    seedSelect.appendChild(option);
  }
  seedSelect.value=selectedSeed;
  const warning=$("results-current-warning");
  if(isUnsimulatedVersion()){
    warning.hidden=pageName!=="results";
    clear(warning);
    warning.appendChild(el("strong","No cached simulations for “"+activeDeckTitle()+"”. "));
    warning.appendChild(document.createTextNode(
      "This is a browser-edited deck. Its original's results do not describe this version. "));
    const baseline=el("button","View built-in deck's cached records","stone-button");
    baseline.type="button";baseline.onclick=()=>summon(selected);
    warning.appendChild(baseline);
    $("show-record").disabled=true;$("export-record").disabled=true;
    clear($("record-info"));clear($("turn-timeline"));
    $("turn-timeline").textContent="Export the edited decklist and generate fresh Python observations.";
    lastRecord=null;
    for(const section of document.querySelectorAll(".story-step"))section.hidden=true;
    showAggregate();return;
  }
  warning.hidden=true;
  $("show-record").disabled=false;$("export-record").disabled=false;
  for(const section of document.querySelectorAll(".story-step"))section.hidden=false;
  showAggregate();
  displayRecord();
}
function displayRecord(){
  if(isUnsimulatedVersion()){renderRecords();return}
  const record=archives[selected]?.[$("seed-select").value];
  if(!record){note("No cached observation for that seed.",true);return}
  selectedSeed=String(record.seed);lastRecord=record;
  const count=Math.min(Number($("turn-select").value)||6,record.trace.length);
  const info=$("record-info");clear(info);
  const opener=el("div",null,"archive-summary");
  opener.append(el("strong","Seed "+record.seed),el("span","Opening hand: "+record.opening_hand.join(" · ")));
  info.appendChild(opener);
  const timeline=$("turn-timeline");clear(timeline);
  for(const t of record.trace.slice(0,count)){
    const node=el("div",null,"turn");
    node.appendChild(el("div",t.turn,"number"));
    const body=el("div",null,"turn-body");
    const drawn=el("div");drawn.append(el("strong","Draw "),el("span",t.drawn||"No draw","muted"));
    const land=el("div");land.append(el("strong","Modeled land "),el("span",t.land_played||"None","muted"));
    body.append(drawn,land);
    body.appendChild(el("div",window.DeckInsights?.sources(t)+" modeled sources · "+
      t.hand_count+" cards in hand","small"));
    const candidates=t.candidate_if_supported||[];
    body.appendChild(el("div",candidates.length?
      "Mana-value candidates (not castability): "+candidates.map(x=>x.card).join(", "):
      "No candidate passed the mana-value screen","small"));
    const affordable=t.source_paid_mana_preview||[];
    body.appendChild(el("div",affordable.length?
      "Modeled sources can pay printed symbols for: "+affordable.map(x=>x.card).join(", "):
      "No fixed printed costs payable with modeled sources on this turn",
      "small"));
    body.appendChild(el("div","Payment feasibility only; no legal casts, effects, optional costs, or priority modeled.","micro"));
    node.appendChild(body);timeline.appendChild(node);
  }
}
function detailForBar(kind,group,summary){
  const seeds=group.seeds||[];
  const header=kind==="opening"?
    group.label+" modeled lands in opening seven":
    kind==="resources"?group.label+" modeled sources on turn three":
    "Turn "+group.label.slice(1)+" · any mana-value candidate";
  const exact=kind==="candidates"?
    group.numerator+" of "+summary.n+" runs ("+group.value+"%)":
    group.value+" of "+summary.n+" runs";
  const evidence=seeds.length?"Matching archived seeds: "+seeds.join(", "):
    "No archived seeds matched this bar.";
  let implication=kind==="opening"?
    "These counts only include basic lands and Command Tower.":
    kind==="resources"?
    "Other mana sources, ramp and color payment aren't simulated.":
    "Candidates pass only the total-mana-value screen; legal play is not checked.";
  return {header,exact,evidence,implication};
}
function renderInsightChart(kind,groups,rootId,detailId){
  const root=$(rootId),detail=$(detailId);clear(root);clear(detail);
  if(!aggregate)return;
  const chart=makeBars(groups.map(g=>[g.label,g.value]),{
    color:kind==="opening"?"#d2b47f":kind==="resources"?"#73bdb1":"#aa97cf"
  });
  root.appendChild(chart);
  const bars=chart.querySelectorAll("rect.bar");
  const ink={opening:"#d2b47f",resources:"#73bdb1",candidates:"#aa97cf"}[kind];
  bars.forEach((bar,index)=>{
    bar.style.fill=ink;
    const y=Number(bar.getAttribute("y"));
    const h=Number(bar.getAttribute("height"));
    bar.dataset.targetY=String(y);
    bar.dataset.targetHeight=String(h);
    const group=groups[index];
    if(!group)return;
    bar.setAttribute("role","button");
    bar.setAttribute("tabindex","0");
    bar.setAttribute("aria-label",group.label+": "+
      (kind==="candidates"?group.value+" percent":group.value+" observed runs")+
      ". Select to inspect archived seeds.");
    bar.classList.add("interactive-bar");
    const title=document.createElementNS(NS,"title");
    title.textContent=group.label+" · "+(kind==="candidates"?
      group.numerator+"/"+aggregate.n+" runs":group.value+"/"+aggregate.n+" runs");
    bar.appendChild(title);
    const activate=()=>{
      for(const b of bars)b.classList.toggle("selected-bar",b===bar);
      const result=detailForBar(kind,group,aggregate);
      clear(detail);
      detail.append(el("strong",result.header),el("span",result.exact),
        el("p",result.evidence),el("small",result.implication));
      if(group.seeds?.length){
        const seedButton=el("button","Inspect seed "+group.seeds[0],"glyph-button");
        seedButton.type="button";
        seedButton.onclick=()=>{
          $("seed-select").value=group.seeds[0];displayRecord();
          document.querySelector(".archived-details").scrollIntoView({
            behavior:window.matchMedia?.("(prefers-reduced-motion: reduce)").matches?
              "auto":"smooth",block:"start"
          });
        };
        detail.appendChild(seedButton);
      }
      originalSound("click");
    };
    bar.addEventListener("click",activate);
    bar.addEventListener("keydown",e=>{
      if(e.key==="Enter"||e.key===" "){e.preventDefault();activate()}
    });
  });
}
function animateFinding(section,visible){
  section.classList.toggle("visible",visible);
  const bars=[...section.querySelectorAll("rect.bar[data-target-y]")];
  if(!bars.length)return;
  const reduced=window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  if(reduced||!window.d3){
    for(const bar of bars){
      bar.setAttribute("y",bar.dataset.targetY);
      bar.setAttribute("height",bar.dataset.targetHeight);
    }
    return;
  }
  const chart=window.d3.select(section).selectAll("rect.bar[data-target-y]");
  chart.interrupt();
  if(visible){
    chart.transition().duration(750).ease(window.d3.easeCubicOut)
      .attr("y",function(){return this.dataset.targetY})
      .attr("height",function(){return this.dataset.targetHeight});
  }else{
    chart.attr("y",function(){
      return Number(this.dataset.targetY)+Number(this.dataset.targetHeight);
    }).attr("height",0);
  }
}
function installScrollStory(){
  if(scrollObserver){scrollObserver.disconnect();scrollObserver=null}
  const sections=[...document.querySelectorAll(".story-step")].filter(s=>!s.hidden);
  const reduced=window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  if(reduced||!("IntersectionObserver" in window)){
    sections.forEach(s=>animateFinding(s,true));return;
  }
  sections.forEach(s=>animateFinding(s,false));
  scrollObserver=new IntersectionObserver(entries=>{
    for(const entry of entries)animateFinding(entry.target,entry.isIntersecting);
  },{threshold:.16,rootMargin:"0px 0px -8% 0px"});
  sections.forEach(s=>scrollObserver.observe(s));
}
function renderScrollStory(){
  if(!aggregate||isUnsimulatedVersion()){
    for(const id of ["scroll-sources","scroll-hand","scroll-candidates"])
      clear($(id));
    return;
  }
  const findings=window.DeckInsights.findings(aggregate);
  for(const [index,kind] of ["opening","resources","candidates"].entries()){
    const f=findings[index];
    $("story-title-"+kind).textContent=f.title;
    $("story-summary-"+kind).textContent=f.summary;
    $("story-meaning-"+kind).textContent=f.meaning;
    $("story-caveat-"+kind).textContent=f.caveat;
  }
  renderInsightChart("opening",aggregate.openingGroups,"scroll-sources","detail-opening");
  renderInsightChart("resources",aggregate.turn3Groups,"scroll-hand","detail-resources");
  renderInsightChart("candidates",aggregate.candidateGroups,"scroll-candidates","detail-candidates");
  installScrollStory();
}
function exportFile(filename,content,type="text/plain"){
  const object=new Blob([content],{type});
  const url=URL.createObjectURL(object);
  const anchor=document.createElement("a");anchor.href=url;anchor.download=filename;
  document.body.appendChild(anchor);anchor.click();anchor.remove();
  setTimeout(()=>URL.revokeObjectURL(url),4000);
}
function exportRecord(){
  if(!lastRecord)return;
  exportFile(selected+"-seed-"+selectedSeed+"-cached-observation.json",
    JSON.stringify(lastRecord,null,2),"application/json");
  originalSound("click");
}
function initialCounts(){
  return Object.fromEntries(selectedDeck().cards.filter(x=>x.zone!=="Commander").map(x=>[x.name,x.qty]));
}
function sumCounts(counts){return Object.values(counts).reduce((a,b)=>a+Number(b||0),1)}
function normalizedCounts(counts){
  const normalized={};
  for(const [name,num] of Object.entries(counts))
    if(Number.isInteger(num)&&num>0)normalized[name]=num;
  return normalized;
}
function validateCounts(counts,{allowIncomplete=false}={}){
  const deck=selectedDeck(),cmd=commanderCard(deck);
  if(!allowIncomplete&&sumCounts(counts)!==100)
    throw Error("A Commander deck must have exactly 100 cards, including its commander.");
  const identities=new Set([deck.commander_id]);
  for(const [name,qty] of Object.entries(counts)){
    if(!Number.isInteger(qty)||qty<0)throw Error("Card quantities must be whole positive numbers.");
    const card=cardInfo(name);
    if(!card)throw Error("Missing verified metadata: "+name+". Use Fetch card details first.");
    if(card.commander_legality!=="legal")throw Error(name+" is not marked Commander-legal in cached metadata.");
    if(name===deck.commander||card.oracle_id===deck.commander_id)throw Error("The commander cannot also be in the library.");
    if([...card.color_identity].some(color=>!cmd.color_identity.includes(color)))
      throw Error(name+" has colors outside "+deck.commander+"'s color identity.");
    if(!card.is_basic && qty>1)throw Error("Commander singleton: "+name+" cannot appear "+qty+" times.");
    if(identities.has(card.oracle_id))throw Error("One Oracle card occurs under multiple names: "+name);
    identities.add(card.oracle_id);
  }
  return true;
}
function initializeDraft(){
  activeCounts=isUnsimulatedVersion()?{...activeVersion().counts}:initialCounts();
  history=[];
  $("add-name").value="";
  $("draft-title").value=activeVersion()?.title||"";
  renderDraft();renderVersions();renderDeckVersionSelector();
}
function activeDelta(){
  const initial=initialCounts(),names=new Set([...Object.keys(initial),...Object.keys(activeCounts)]);
  return [...names].filter(name=>(initial[name]||0)!==(activeCounts[name]||0))
    .sort((a,b)=>a.localeCompare(b)).map(name=>({
      name,before:initial[name]||0,after:activeCounts[name]||0,
      delta:(activeCounts[name]||0)-(initial[name]||0)
    }));
}
function renderDraft(){
  if(!selected)return;
  updateSelectionBadge();
  renderLibrary();renderOverview();
  if(pageName==="results")renderRecords();
  renderPageIntro();
  const remove=$("remove-name");clear(remove);
  for(const name of Object.keys(activeCounts).sort((a,b)=>a.localeCompare(b))){
    if(activeCounts[name]<=0)continue;
    const o=el("option",activeCounts[name]+" × "+name);o.value=name;remove.appendChild(o);
  }
  const diff=$("workshop-diff");clear(diff);
  const changes=activeDelta();
  if(!changes.length){diff.appendChild(el("p","No changes yet. Your original deck remains intact.","small"));}
  for(const item of changes){
    const row=el("div",null,"deck-row");
    row.appendChild(el("strong",item.name));
    row.appendChild(el("span",(item.delta>0?"+":"")+item.delta,
      item.delta>0?"diff-up":"diff-down"));diff.appendChild(row);
  }
  $("undo-button").disabled=!history.length;
  $("reset-button").disabled=!changes.length;
  const total=sumCounts(activeCounts);
  $("workshop-message").textContent=changes.length?
    changes.length+" card quantities modified · "+total+" / 100 cards including commander. "+
      (total===100?"Ready for legality validation and Save As.":"Add or remove cards to return to 100 before saving.")+
      " "+MODE_NOTE:
    "Choose cards to add, remove or swap. The saved source deck remains unchanged.";
  $("workshop-message").classList.toggle("error",total!==100);
  $("save-local").disabled=total!==100;
  $("export-deck").disabled=total!==100;
  renderDeckVersionSelector();
}
function changeDraftQuantity(action){
  if(!activeCounts)return;
  const name=(action==="remove"?$("remove-name").value:$("add-name").value.trim());
  if(!name){note("Select a card to "+action+".",true);return}
  const candidate={...activeCounts};
  if(action==="remove"){
    if(!candidate[name]||candidate[name]<1){
      note("That card is not in this draft.",true);return;
    }
    candidate[name]--;
    if(!candidate[name])delete candidate[name];
  }else{
    candidate[name]=(candidate[name]||0)+1;
  }
  try{
    validateCounts(candidate,{allowIncomplete:true});
    history.push({...activeCounts});activeCounts=candidate;
    renderDraft();originalSound("success");
    if(action==="add")$("add-name").value="";
  }catch(err){note(err.message,true);originalSound("error")}
}
function trySwap(){
  const remove=$("remove-name").value,add=$("add-name").value.trim();
  if(!remove||!add){note("Choose one card to remove and one to add.",true);return}
  const candidate={...activeCounts};
  if(!candidate[remove]){note("Selected card is no longer in the draft.",true);return}
  candidate[remove]--;
  if(candidate[remove]===0)delete candidate[remove];
  candidate[add]=(candidate[add]||0)+1;
  try{
    validateCounts(candidate);
    history.push({...activeCounts});activeCounts=candidate;
    renderDraft();originalSound("success");
    $("add-name").value="";
  }catch(err){note(err.message,true);originalSound("error")}
}
function undo(){
  if(history.length){activeCounts=history.pop();renderDraft();originalSound("click")}
}
function revertDraft(){activeCounts=initialCounts();history=[];renderDraft();originalSound("click")}
function saveVersion(){
  const title=$("draft-title").value.trim();
  if(title.length<1||title.length>70){
    note("Give this deck version a title (1–70 characters).",true);return;
  }
  try{validateCounts(activeCounts)}catch(err){note(err.message,true);return}
  const duplicate=deckVersionsForCommander(selectedDeck().commander_id)
    .some(v=>v.title.trim().toLocaleLowerCase()===title.toLocaleLowerCase());
  if(duplicate){
    note("A saved deck with that name already exists for this commander. Choose a new name.",true);
    return;
  }
  const now=new Date().toISOString();
  const id="v-"+Date.now().toString(36)+"-"+Math.random().toString(36).slice(2,9);
  const record={id,title,baseKey:selected,counts:{...activeCounts},
    created:now,updated:now};
  localVersions.unshift(record);
  if(localVersions.length>60)localVersions=localVersions.slice(0,60);
  // Save As always creates a separately named revision. The original remains intact.
  summon(selected,{versionId:id});
  originalSound("success");
  note("Saved “"+title+"” in this browser. Download the decklist to keep a durable copy.");
}
function renderDeckVersionSelector(){
  const control=$("deck-version-select");clear(control);
  const commanderId=selectedDeck().commander_id;
  const presets=el("optgroup");presets.label="Built-in decks · cached results";
  for(const deck of sameCommanderDecks(commanderId)){
    const option=el("option",LABELS[deck.key]||deck.key);
    option.value="preset:"+deck.key;presets.appendChild(option);
  }
  control.appendChild(presets);
  const versions=deckVersionsForCommander(commanderId);
  if(versions.length){
    const saved=el("optgroup");saved.label="Your saved browser decks · not simulated";
    for(const version of versions){
      const option=el("option",version.title+" · saved "+String(version.updated||version.created||"").slice(0,10));
      option.value="saved:"+version.id;saved.appendChild(option);
    }
    control.appendChild(saved);
  }
  if(hasUnsavedChanges()){
    const draft=el("option","● Unsaved changes to "+activeDeckTitle());
    draft.value="unsaved";
    control.appendChild(draft);
    control.value="unsaved";
  }else{
    control.value=selectedVersionId?"saved:"+selectedVersionId:"preset:"+selected;
  }
}
function loadDeckSelection(value){
  if(value==="unsaved")return;
  if(hasUnsavedChanges()&&!window.confirm(
      "Discard unsaved deck changes? Save as a named deck first to keep them.")){
    renderDeckVersionSelector();return;
  }
  if(value.startsWith("preset:")){
    const deck=data.decks.find(d=>d.key===value.slice(7));
    if(deck&&deck.commander_id===selectedDeck().commander_id)
      summon(deck.key);
    return;
  }
  if(value.startsWith("saved:")){
    const version=localVersions.find(v=>v.id===value.slice(6));
    if(!version||!sameCommanderDecks(selectedDeck().commander_id)
      .some(d=>d.key===version.baseKey))return;
    const previous=selected;
    selected=version.baseKey;
    try{validateCounts(version.counts)}
    catch(e){selected=previous;note("Saved deck cannot be loaded: "+e.message,true);renderDeckVersionSelector();return}
    selected=previous;
    summon(version.baseKey,{versionId:version.id});
    note("Loaded “"+version.title+"”. No cached simulation is associated with this edited version.");
  }
}
function renderVersions(){
  const root=$("saved-versions");clear(root);
  const versions=deckVersionsForCommander(selectedDeck().commander_id);
  if(!versions.length){
    root.appendChild(el("p","No named browser decks saved for this commander.","small"));
    return;
  }
  for(const version of versions){
    const row=el("div",null,"saved-row");
    if(version.id===selectedVersionId)row.classList.add("selected-version");
    const label=el("div");
    label.appendChild(el("strong",version.title));
    label.appendChild(el("div",
      (LABELS[version.baseKey]||version.baseKey)+" · "+
      String(version.updated||version.created||"").slice(0,10)+" · browser only",
      "micro"));
    const actions=el("div",null,"control-row");
    const load=el("button","Load","glyph-button");
    load.onclick=()=>loadDeckSelection("saved:"+version.id);
    const del=el("button","Delete","glyph-button");
    del.onclick=()=>{
      localVersions=localVersions.filter(v=>v.id!==version.id);
      if(selectedVersionId===version.id){
        summon(version.baseKey);
      }else{
        persist();renderVersions();renderDeckVersionSelector();
      }
      originalSound("click");
    };
    actions.append(load,del);row.append(label,actions);root.append(row);
  }
}
function newDeckVersion(){
  // Create a distinct unsaved draft, preserving current card quantities.
  // A built-in card list remains read-only; no cached results are attached.
  selectedVersionId=null;
  history=[];
  $("draft-title").value="";
  if(!isUnsimulatedVersion()){
    $("version-help").textContent="New draft from the built-in deck. Make a swap, enter a name, then Save as named deck.";
  }else{
    $("version-help").textContent="New unsaved draft copied from the current deck. Save it under a new name.";
  }
  renderDraft();renderDeckVersionSelector();
  syncPageNavigation();
  note("New draft created. Enter a name and save to keep it.");
}
function exportDeck(){
  if(!selected)return;
  try{validateCounts(activeCounts)}catch(err){note(err.message,true);return}
  const commander=selectedDeck().commander;
  const lines=[
    "# Exported from Commander Deck Lab (static version; no game results)",
    "Commander","1 "+commander,"","Library"
  ];
  for(const name of Object.keys(activeCounts).sort((a,b)=>a.localeCompare(b)))
    lines.push(activeCounts[name]+" "+name);
  const name=(selectedDeck().key+"-"+($("draft-title").value||"custom"))
    .replace(/[^a-z0-9-]+/gi,"-").slice(0,70).toLowerCase();
  exportFile(name+".txt",lines.join("\n")+"\n");
  originalSound("success");
  note("Decklist exported. Import it into the Python simulator to generate new results.");
}
function matchesForName(q){
  const needle=q.toLowerCase().trim();
  if(needle.length<2)return [];
  const candidates=allNames.filter(name=>name.toLowerCase().startsWith(needle)).slice(0,25);
  if(candidates.length<15){
    for(const name of allNames){
      if(name.toLowerCase().includes(needle)&&!candidates.includes(name)){
        candidates.push(name);
        if(candidates.length>=25)break;
      }
    }
  }
  return candidates.slice(0,25);
}
function suggestNames(){
  const term=$("add-name").value.trim()||$("fetch-name").value.trim();
  const matches=matchesForName(term),box=$("name-suggestions");clear(box);
  for(const name of matches){const option=el("option");option.value=name;box.appendChild(option)}
}
function listenToNameInput(){
  clearTimeout(autoTimer);
  autoTimer=setTimeout(suggestNames,100);
}
function normalizeFetched(raw){
  if(!raw||!raw.oracle_id||!raw.name||!raw.type_line||!Array.isArray(raw.color_identity))
    throw Error("Scryfall did not return a complete card identity.");
  const face=Array.isArray(raw.card_faces)?raw.card_faces.find(f=>f?.image_uris)||{}:{};
  const imagery=raw.image_uris||face.image_uris||{};
  const print=raw.legalities?.commander||"unknown";
  return {
    oracle_id:raw.oracle_id,name:raw.name,type_line:raw.type_line,
    category:["Land","Creature","Artifact","Enchantment","Planeswalker","Instant","Sorcery"]
      .find(t=>raw.type_line.includes(t))||"Other",
    mana_value:raw.cmc,mana_cost:raw.mana_cost||"",
    color_identity:raw.color_identity,commander_legality:print,
    oracle_text:raw.oracle_text||raw.card_faces?.map(f=>f.oracle_text||"").join("\n")||"",
    power:raw.power,toughness:raw.toughness,
    image:imagery.normal||null,art:imagery.art_crop||null,
    scryfall:raw.scryfall_uri||null,
    is_basic:raw.type_line.includes("Basic Land"),
    face_names:raw.card_faces?.map(f=>f.name).filter(Boolean)||[]
  };
}
async function fetchCard(){
  const name=$("fetch-name").value.trim();
  if(!name||name.length>200){note("Enter an exact card name before fetching.",true);return}
  const existing=cardInfo(name);
  if(existing){$("fetch-status").textContent=existing.name+" already has cached metadata.";
    originalSound("click");return}
  const status=$("fetch-status");
  status.textContent="Requesting this card from Scryfall…";
  $("fetch-card").disabled=true;
  try{
    // Explicit user action only. Scryfall exposes this public CORS JSON API.
    const response=await fetch("https://api.scryfall.com/cards/named?exact="+encodeURIComponent(name),
      {headers:{"Accept":"application/json"}});
    if(!response.ok)throw Error(response.status===404?"Name not found in Scryfall. Check spelling.":
      "Scryfall request failed (HTTP "+response.status+").");
    const raw=await response.json(),card=normalizeFetched(raw);
    const aliases=[card.name,...card.face_names].map(x=>x.toLowerCase());
    if(!aliases.includes(name.toLowerCase()))throw Error("Returned card name did not match the requested name.");
    extraCards[card.oracle_id]=card;addAliases(card);persist();
    status.textContent=card.name+" cached in this browser. You can now try swapping it into a deck.";
    $("add-name").value=name;
    note(card.name+" is ready for validation.");
    originalSound("success");
  }catch(err){
    status.textContent="Unable to fetch: "+err.message+
      " You can still download the decklist and import it using Python.";
    originalSound("error");
  }finally{$("fetch-card").disabled=false}
}
function registerEvents(){
  syncSoundControl();
  document.addEventListener("pointerdown",()=>{audioUnlocked=true},{once:true});
  document.addEventListener("keydown",()=>{audioUnlocked=true},{once:true});
  $("audio-toggle").onclick=enableSound;
  $("commander-medallion").onclick=toggleCommanderPicker;
  document.addEventListener("click",e=>{
    if(!e.target.closest(".selector-anchor"))closeCommanderPicker();
  });
  document.addEventListener("keydown",e=>{
    if(e.key==="Escape")closeCommanderPicker();
  });
  $("deck-version-select").onchange=e=>loadDeckSelection(e.target.value);
  $("new-version-button").onclick=newDeckVersion;
  // Navigation links lead to independent static pages (no client router).
  $("library-search").oninput=renderLibrary;
  $("library-category").onchange=renderLibrary;
  $("show-record").onclick=()=>{displayRecord();originalSound("page")};
  $("export-record").onclick=exportRecord;
  $("turn-select").onchange=displayRecord;
  $("seed-select").onchange=displayRecord;
  $("swap-button").onclick=trySwap;
  $("remove-one-button").onclick=()=>changeDraftQuantity("remove");
  $("add-one-button").onclick=()=>changeDraftQuantity("add");
  $("undo-button").onclick=undo;
  $("reset-button").onclick=revertDraft;
  $("save-local").onclick=saveVersion;
  $("export-deck").onclick=exportDeck;
  $("fetch-card").onclick=fetchCard;
  $("add-name").oninput=listenToNameInput;
  $("fetch-name").oninput=listenToNameInput;
  $("modal-close").onclick=closeCard;
  $("dialog-backdrop").onclick=e=>{if(e.target.id==="dialog-backdrop")closeCard()};
  document.addEventListener("keydown",e=>{if(e.key==="Escape")closeCard()});
}
async function boot(){
  registerEvents();
  try{
    const response=await Promise.all([
      fetch("./decks.json"),fetch("./observations.json"),fetch("./names.json")
    ]);
    if(response.some(r=>!r.ok))throw Error("Site data could not be loaded. Check the Pages deployment.");
    [data,archives,allNames]=await Promise.all(response.map(r=>r.json()));
    if(data.format!=="commander-deck-lab-static-v1"||!data.decks.length)
      throw Error("Unexpected static dataset format.");
    allNames.sort((a,b)=>a.localeCompare(b));
    for(const card of Object.values(data.cards))addAliases(card);
    loadLocal();buildDeckRail();
    const params=new URLSearchParams(location.search);
    const key=params.get("deck"),requestedVersion=params.get("version");
    let choice;
    if(data.decks.some(d=>d.key===key)){
      const validVersion=localVersions.some(v=>v.id===requestedVersion&&v.baseKey===key)?
        requestedVersion:null;
      choice={key,version:validVersion};
    }else if(lastCommanderId&&sameCommanderDecks(lastCommanderId).length){
      choice=latestSelectionForCommander(lastCommanderId);
    }else{
      const first=data.decks.find(d=>d.key==="magnus_premium")||data.decks[0];
      choice=latestSelectionForCommander(first.commander_id);
    }
    summon(choice.key,{versionId:choice.version});
  }catch(err){
    const rail=$("commander-rail");clear(rail);
    rail.appendChild(el("p","Unable to open the archive: "+err.message));
    note("Deck archive unavailable. Verify the static data build.",true);
  }
}
boot();
