/* Human-readable presentation only: stable source IDs remain unchanged. */
(function(root,factory){
  const api=factory(root.DeckDisplayLabelData||{});
  if(typeof module==='object'&&module.exports)module.exports=factory;
  else root.DeckDisplayNames=api;
})(typeof window!=='undefined'?window:globalThis,function(registry){
  'use strict';
  const pretty=value=>String(value??'').replace(/[_-]+/g,' ').replace(/\b\w/g,c=>c.toUpperCase());
  const lookup=(section,key)=>registry[section]?.[key]||pretty(key);
  function deck(key){return lookup('decks',key)}
  function group(kind,key){
    if(kind==='opponents')return deck(key);
    if(kind==='pods')return String(key).split(' / ').map(deck).join(' · ');
    if(kind==='archetypes')return lookup('archetypes',key);
    if(kind==='colors')return lookup('colors',key);
    if(kind==='identities')return key==='Colorless'?key:[...key].map(c=>lookup('colors',c)).join(' · ');
    if(kind==='seats')return 'Seat '+key;
    return pretty(key);
  }
  function feature(raw){
    if(String(raw).includes(' × '))return String(raw).split(' × ').map(feature).join(' × ');
    const match=String(raw).match(/^([^:]+):(.+)$/);
    if(!match)return pretty(raw);
    const [,family,key]=match;
    const kind={opponent:'opponents',archetype:'archetypes',color:'colors',seat:'seats'}[family];
    const value=family==='seat'?key:kind?group(kind,key):pretty(key);
    return (registry.predictor_families?.[family]||pretty(family)+': {value}').replace('{value}',value);
  }
  return {deck,group,feature};
});
