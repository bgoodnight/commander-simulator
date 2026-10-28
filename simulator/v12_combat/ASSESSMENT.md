# V12 assessment

October 28, 2026. The first three agreed roadmap items are implemented: card
coverage audit, multiple blockers/trample, and first/double strike. The engine
remains a declared Commander subset with one real deck and synthetic opponents.

## Observed validation

- 422 tests passed across twelve historical/versioned suites; 50 are new v12
  tests. The v11 driver's new hook preserves its ordinary single-batch behavior.
- Six targeted narratives passed with conserved physical inventories and actual
  source-ID spell payments. Combat tokens and keyword grants are explicitly
  synthetic fixtures, not silently enabled printed cards.
- 200 twelve-round seeded games (50 seeds in each Magnus seat; three synthetic
  opponent groups) passed physical-card, zone-index, spell-frame, battlefield-view
  and mana-pool consistency checks. No safety stops.
- The sweep exposed 100,920 steps, 3,864 damage batches, 295 batches involving
  multiple declared blockers, and 10,900 source payments.
- Exploratory medians over 12 eight-round games per engine: v11 StepTable
  347.279 ms; v12 CombatTable 314.807 ms. Different blocking decisions alter
  trajectories. These samples do not prove a speedup; they reveal no obvious
  regression requiring optimization before the next milestone.

## Interaction evidence

Read INTERACTION_REPORT.md and the six Markdown/JSON pairs for full traces.

1. A four-power attacker can divide damage 1/3 among 2/3 and 3/4 blockers;
   neither blocker dies. There is no obsolete damage assignment order.
2. Capsize removes one of two blockers before damage. An eight-power trampler
   assigns two to the remaining 2/2 and six to the player.
3. A four-power double-striker marks four on a 1/6 in the first step. The normal
   step assigns two more to the blocker and two to the player through trample.
4. Abrade in the first-step priority window kills a previously damaged blocker.
   A double-striker without trample remains blocked and does no player damage.
5. Actual Magnus with a declared synthetic double-strike grant hits twice,
   creating one Spawn in each separate priority window: eight damage, two Spawn.
6. After Magnus's first hit and token trigger, source-paid Capsize returns it to
   hand. Its token discount reduces Capsize to UU. No second hit occurs: four
   damage, one Spawn. Scheduled second-step timing remains intact.

Additional unit checks cover full-declaration atomicity, duplicate/tapped/illegal
flying blocks, damage-batch rejection before mutation, all-to-one/nonlethal
allocations, marked damage, indestructible thresholds, overassignment, blockers
and attackers leaving, simultaneous trades/multiple-player lethal, strike gained
or lost between steps, pools clearing, priority after both steps, reproducibility
and conservation with the real deck in every seat.

## Audit findings and triage

All 100 physical cards (83 distinct names) are accounted for. Distinct statuses:
23 supported subsets, 25 partial, 35 unsupported. Repeated basics make physical
counts 40/25/35. Supported subset means only the listed behavior is implemented.
The audit is not a comprehensive contemporary Oracle-text certification.

The audit confirmed An Offer You Can't Refuse already uses two actual Treasure
objects, superseding the old v6 ramp adapter. Conversely, a playable body does
not certify all text: Harmonic prowess, Storm-Kiln artifact-count power, Baral
loot and Stormsplitter delayed expiry remain omissions. Special-land and generic
selection adapters remain partial even where historical effect counters called
them supported. No named deck card was newly enabled by this milestone.

Recommended next batches: exact selection/land behavior and missing live engine
text; then copies, relevant creature activations/tutors, graveyard casting and
verified combo lines. Broader damage keywords and attachments remain future
rule milestones. CARD_COVERAGE.md contains the per-card triage evidence.

## Architecture and practical limits

ExpandedCombat reuses v11 attacker declaration and the common authoritative
kernel. It adds validated group blocking, immutable allocation contexts, complete
per-source assignment records, trample thresholds and strike snapshots.
CombatDriver overrides a small backward-compatible damage_steps hook. Damage
assignment and application remain one turn-based action; no stack object or
priority window is inserted between them. SBA processing, trigger ordering and
priority still use the v10 stack. Rule code contains no printed card-name policy.

Default group blocking/assignment is a heuristic; custom policies can select
other legal declarations and splits. A blocker may block only one attacker. No
multi-attacker blockers, menace/banding, deathtouch/lifelink, prevention/protection,
planeswalker/battle attacks, commander damage, general control-change combat
removal, attachments, live spell copies or verified loops are implemented here.
Other named-card/land/selection and delayed-trigger gaps remain as audited.

The unforced sweep validates live group blocking and infrastructure, not natural
strike/trample card coverage. Targeted keyword fixtures validate those rules.
Neither is evidence for deck win rates or card-power rankings.

Rollback: 12ea213bc140a84fcb917e26a8ed6c5104cff5f5 (v11). Historical manifests
remain records of the original milestone bytes; the new manifest covers the
current changed files and v12 artifacts.
