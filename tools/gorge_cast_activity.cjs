"use strict";

// Count native cast events, including the commander and repeated casts.
// The projected Gorge event's absent player field represents seat zero.
function extract(game, hero, cards) {
  const counts = new Map();
  let spells = 0, creatures = 0, completeTypes = true;
  for (const turn of game.turns || []) for (const event of turn.events || []) {
    if (event.kind !== "cast" || (event.player ?? 0) !== hero) continue;
    spells++;
    const name = event.card_name || game.object_identity?.[String(event.obj)] || null;
    const card = name && cards.get(name);
    const type = card?.type_line;
    if (typeof type !== "string" || !type) completeTypes = false;
    const creature = typeof type === "string" && /\bcreature\b/i.test(type.split("—")[0]);
    if (creature) creatures++;
    if (name) {
      const item = counts.get(name) || {name, casts: 0, creature: !!creature};
      item.casts++;
      counts.set(name, item);
    }
  }
  return {seed: game.seed, spells, creatures: completeTypes ? creatures : null,
    named_casts_complete: [...counts.values()].reduce((s, x) => s + x.casts, 0) === spells,
    cards: [...counts.values()]};
}
module.exports = {extract};
