'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const labels=require('../data/gorge_display_labels.json');
const names=require('../web/pages/display_names.js')(labels);
const replay=require('../web/pages/gorge_replay.js');
test('deck, pod, archetype, color and model labels retain their meaning',()=>{
  assert.equal(names.deck('science-pip'),'Science!');
  assert.equal(names.group('pods','science-pip / cavalry-charge'),'Science! · Cavalry Charge');
  assert.equal(names.group('archetypes','face_down'),'Face Down');
  assert.equal(names.group('identities','WUB'),'White · Blue · Black');
  assert.equal(names.feature('opponent:deadly-disguise'),'Opponent: Deadly Disguise');
  assert.equal(names.feature('seat:3'),'Player seat 3');
  assert.equal(names.feature('color:U'),'Opponent color: Blue');
  assert.equal(names.deck('future-unknown-deck'),'Future Unknown Deck');
});
test('headline denominator excludes draws and handles no decisive results',()=>{
  assert.deepEqual(replay.decisiveTotals({wins:25,losses:75,draws:20}),
    {total:100,winRate:.25,lossRate:.75});
  assert.deepEqual(replay.decisiveTotals({wins:0,losses:0,draws:5}),
    {total:0,winRate:null,lossRate:null});
});
