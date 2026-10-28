# Magnus v1.6 implementation coverage — v12

Code-path audit of the actual 99 plus commander. Supported subset means the listed behavior is live; it is not full Oracle certification. Partial means a usable effect has known omissions. Unsupported cards are excluded from legal casts, not replaced by invented generic effects.

Inventory: 100 physical cards; 83 distinct names. Statuses include commander and repeated basics.

| Status | Distinct names | Physical cards |
|---|---:|---:|
| supported subset | 23 | 40 |
| partial | 25 | 25 |
| unsupported | 35 | 35 |

## Triage

| Priority | Area | Reason |
|---|---|---|
| P1 | Exact selection and land rules | Selection spells and utility lands are already used; correct existing approximations before comparing decks. |
| P1 | Engine omissions and delayed triggers | Harmonic prowess, Storm-Kiln power, Baral loot and Stormsplitter expiry affect live board states. |
| P2 | Spell copying | Shared prerequisite for Twincast/Reiterate/Dualcaster/Sigil Tracer and magecraft/copy interactions. |
| P2 | Creature activations and tutoring | Patron Wizard/Voidmage, Spellseeker, Mystical Tutor and transmute need explicit legal choices and costs. |
| P3 | Graveyard casting, replacement/layer breadth and combos | Breach, alternate costs, type engines and candidate loops need reusable prerequisites and interruption tests. |

The combat expansion does not add named cards to the deck. First/double strike and trample are validated with explicitly synthetic combat fixtures; those results must not be interpreted as newly complete deck-card implementations.

## Per-card evidence and limits

| Card | Qty | Status | Live behavior / gap |
|---|---:|---|---|
| Magnus the Red | 1 | partial | Flying, token discount and combat-hit token trigger live; commander damage and full Commander rules remain absent. |
| Tzaangor Shaman | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Exalted Flamer of Tzeentch | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Pink Horror | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Heralds of Tzeentch | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Lord of Change | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Mutalith Vortex Beast | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Harmonic Prodigy | 1 | partial | Wizard/Shaman trigger doubling live; prowess is absent. |
| Young Pyromancer | 1 | supported subset | Body and instant/sorcery cast token trigger. |
| Storm-Kiln Artist | 1 | partial | Cast/copy trigger descriptor creates Treasure; artifact-count power bonus and live spell-copy production absent. |
| Docent of Perfection | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Archmage Emeritus | 1 | supported subset | Body and magecraft trigger descriptors; live casts tested, spell copies not yet produced. |
| Patron Wizard | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Voidmage Prodigy | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Spellseeker | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Veyran, Voice of Duality | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Baral, Chief of Compliance | 1 | partial | Generic discount live; counter-triggered loot absent. |
| Third Path Iconoclast | 1 | supported subset | Body and noncreature cast artifact-Soldier trigger. |
| Dualcaster Mage | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Stormsplitter | 1 | partial | Cast-trigger token copies use a declared subset; expiry is cleanup rather than a delayed end-step trigger. |
| Jace, Vryn's Prodigy | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Goblin Electromancer | 1 | supported subset | Body and generic instant/sorcery discount with colored-cost floor. |
| Sigil Tracer | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Sol Ring | 1 | supported subset | Declared U/R/colorless mana ability; source-ID payment, tap and applicable costs. |
| Arcane Signet | 1 | supported subset | Declared U/R/colorless mana ability; source-ID payment, tap and applicable costs. |
| Izzet Signet | 1 | supported subset | Declared U/R/colorless mana ability; source-ID payment, tap and applicable costs. |
| Talisman of Creativity | 1 | supported subset | Declared U/R/colorless mana ability; source-ID payment, tap and applicable costs. |
| Resonating Lute | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Maskwood Nexus | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Arcane Adaptation | 1 | partial | Additive Wizard types live in declared zones; unrestricted creature-type choice/layers absent. |
| The Lost and the Damned | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Underworld Breach | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Sorcerer Class | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Phyrexian Altar | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Fellwar Stone | 1 | supported subset | Declared U/R/colorless mana ability; source-ID payment, tap and applicable costs. |
| Mind Stone | 1 | supported subset | Colorless source plus paid tap/sacrifice draw activation with source reservation. |
| Brainstorm | 1 | partial | Selection adapter; exact draw/put-back ordering and choices absent. |
| Ponder | 1 | partial | Selection adapter; exact look/reorder/shuffle choices absent. |
| Preordain | 1 | partial | Selection adapter; full scry choices absent. |
| Telling Time | 1 | partial | Selection adapter; exact hand/top/bottom choice sequence absent. |
| Impulse | 1 | partial | Selection adapter; exact look/choose/bottom choices absent. |
| Frantic Search | 1 | supported subset | Atomic draw two/discard two/untap up to three lands; discard uses deterministic pilot selection. |
| Mystical Tutor | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Muddle the Mixture | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Step Through | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Twincast | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Reiterate | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Counterspell | 1 | supported subset | Target spell frame and counter destination. |
| Arcane Denial | 1 | partial | Counter live; printed delayed draw timing/choices incomplete. |
| Swan Song | 1 | supported subset | Restricted spell target and flying Bird compensation. |
| An Offer You Can't Refuse | 1 | supported subset | Noncreature spell counter and two actual source-ID Treasure tokens for its controller. |
| Flusterstorm | 1 | partial | Counter subset; storm copies and pay-one choice absent. |
| Pongify | 1 | supported subset | Creature destruction, indestructible handling and Ape compensation. |
| Abrade | 1 | supported subset | Announced modes, three creature damage or artifact destruction; target recheck. |
| Chaos Warp | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Chaos Mutation | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Cyclonic Rift | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| March of Swirling Mist | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Jeska's Will | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Mana Geyser | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Mathemagics | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Comet Storm | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Capsize | 1 | supported subset | Permanent bounce, optional buyback three, additional-cost reduction, counter/fizzle destinations. |
| Searing Touch | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Mystic Speculation | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Command Tower | 1 | supported subset | Declared land mana source; ordinary land-play timing. |
| Steam Vents | 1 | partial | Mana/ETB adapter; printed land subtypes and full entry choice not audited. |
| Training Center | 1 | partial | Mana/ETB adapter; opponent-count entry condition not fully modeled. |
| Stormcarved Coast | 1 | partial | Mana/ETB adapter; printed land-count entry condition not fully modeled. |
| Sulfur Falls | 1 | partial | Mana/ETB adapter; Island/Mountain subtype entry condition not fully modeled. |
| Shivan Reef | 1 | supported subset | Declared land mana source; ordinary land-play timing. |
| Spirebluff Canal | 1 | partial | Mana/ETB adapter; printed land-count entry condition not fully modeled. |
| Riverglide Pathway | 1 | partial | Chosen U/R mana face adapter; full modal double-faced characteristics absent. |
| Fiery Islet | 1 | partial | U/R mana and life cost live; sacrifice-to-draw activation absent. |
| Cascade Bluffs | 1 | supported subset | Declared land mana source; ordinary land-play timing. |
| Exotic Orchard | 1 | supported subset | Declared land mana source; ordinary land-play timing. |
| Fabled Passage | 1 | partial | Prior fetch/ETB adapter; not a priority-aware printed activated ability. |
| Otawara, Soaring City | 1 | partial | Land mana live; channel absent. |
| Sokenzan, Crucible of Defiance | 1 | partial | Land mana live; channel absent. |
| Riptide Laboratory | 1 | partial | Land mana live; Wizard-bounce activation absent. |
| Mystic Sanctuary | 1 | partial | Mana/ETB adapter; complete Island-subtype condition and graveyard-to-top choice absent. |
| Island | 12 | supported subset | Declared land mana source; ordinary land-play timing. |
| Mountain | 7 | supported subset | Declared land mana source; ordinary land-play timing. |

Evidence: v6 named-spec adapter, v7 descriptors, v9b live registration, v9c mana provider, v10 response/activation providers, v11 card expansion and v12 combat. Historical supported/approx counters measure chosen effects and should not be treated as whole-card completion percentages.
