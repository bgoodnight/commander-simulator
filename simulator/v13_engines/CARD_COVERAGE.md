# Magnus coverage — v13

Implementation audit of all 100 physical cards, across 83 names. Supported subset means the behavior below is live, not complete Oracle certification. General legend rules, replacement/draw triggers, spell-copy production and other documented engine limits still apply.

| Status | Distinct names | Physical cards |
|---|---:|---:|
| supported subset | 32 | 49 |
| partial | 16 | 16 |
| unsupported | 35 | 35 |

Nine distinct names moved from partial to supported subset. Frantic Search also gained an explicit discard policy. No previously unsupported named card was enabled. Historical v12 audit is preserved.

| Card | Qty | Status | Behavior / gap |
|---|---:|---|---|
| Magnus the Red | 1 | partial | Flying, token discount and combat-hit token trigger live; commander damage and full Commander rules remain absent. |
| Tzaangor Shaman | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Exalted Flamer of Tzeentch | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Pink Horror | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Heralds of Tzeentch | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Lord of Change | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Mutalith Vortex Beast | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Harmonic Prodigy | 1 | supported subset | Prowess until cleanup; doubling of other Wizards or Shamans, with correct self-Wizard exclusion. |
| Young Pyromancer | 1 | supported subset | Body and instant/sorcery cast token trigger. |
| Storm-Kiln Artist | 1 | supported subset | Live artifact-count power and cast/copy magecraft descriptors; spell-copy production remains absent. |
| Docent of Perfection | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Archmage Emeritus | 1 | supported subset | Body plus cast/copy magecraft draw descriptors, including Harmonic doubling; live spell-copy production remains absent. |
| Patron Wizard | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Voidmage Prodigy | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Spellseeker | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Veyran, Voice of Duality | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Baral, Chief of Compliance | 1 | supported subset | Generic discount and optional draw/discard trigger after a controlled spell/ability actually counters a spell. |
| Third Path Iconoclast | 1 | supported subset | Body and noncreature cast artifact-Soldier trigger. |
| Dualcaster Mage | 1 | unsupported | No live registered printed effect; drawn/reported but excluded from legal casts. |
| Stormsplitter | 1 | supported subset | Otter/Wizard, haste, copiable-base token triggers and next-end-step delayed exile; no general copy-effect layers. |
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
| Brainstorm | 1 | supported subset | Draw three, then choose/order two cards from the entire hand onto the library; one resolution. |
| Ponder | 1 | supported subset | Look at up to three, order, optionally shuffle, then draw; explicit resolution choices. |
| Preordain | 1 | supported subset | Scry two with ordered top/bottom partition, then draw. |
| Telling Time | 1 | supported subset | Look at three; one to hand, one to top, one to bottom; short-library instruction order. |
| Impulse | 1 | supported subset | Look at four; one to hand and the rest to bottom in chosen order; not a draw. |
| Frantic Search | 1 | supported subset | Draw two, choose/discard two, untap up to three distinct lands; one resolution. |
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

## Next triage

- P1: Special-land entry/utility abilities — Remaining live land adapters still affect mana development.
- P2: Spell copies and relevant creature activations/tutors — Unlock unsupported spellslinger cards using the shared stack and costs.
- P3: Graveyard casting, layer/replacement breadth and verified combos — Requires broader reusable rules and interruption tests.
