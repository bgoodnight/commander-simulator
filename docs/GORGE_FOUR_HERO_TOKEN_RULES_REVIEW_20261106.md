# Four-commander Gorge rules and token qualification — November 6, 2026

## Decision: conditional NO-GO for large official cohort

[Four-hero native source run 42292766033](https://github.com/bgoodnight/commander-simulator/actions/runs/42292766033) generated **4 full traced games each** for Mortarion Current, Magnus Premium, Necron Dynasties, and Wretched Ranks. All **16/16** games completed with replay verification. The initial workflow's post-run audit failed because Python was launched outside the checkout (missing `PYTHONPATH`), **not** because Gorge failed. All native artifacts were retained and independently analyzed by successful [source audit 42293063199](https://github.com/bgoodnight/commander-simulator/actions/runs/42293063199), [token semantic drilldown 42293271925](https://github.com/bgoodnight/commander-simulator/actions/runs/42293271925), [token recipe review 42293487498](https://github.com/bgoodnight/commander-simulator/actions/runs/42293487498), and [warning-context review 42293653832](https://github.com/bgoodnight/commander-simulator/actions/runs/42293653832). No R2 write, production publish, approval, or 100/500-game batch was performed.

## Native token evidence

| Hero | Games | Token recipe events, all four seats | All-seat token objects | Hero-owned token objects and types |
|---|---:|---:|---:|---|
| Mortarion Current | 4 | 58 | 61 | 3: Astartes Warrior 1, Human Soldier 1, Treasure 1 |
| Magnus Premium | 4 | 70 | 71 | 21: Spawn 8, Treasure 4, Servo 3, Elemental 2, Drake 2, Crab 1, Clue 1 |
| Necron Dynasties | 4 | 89 | 89 | 27: Necron Warrior 24, Clue 1, Food 1, Junk 1 |
| Wretched Ranks | 4 | 81 | 81 | 69: Zombie 69 |
| **Combined** | **16** | **298** | **302** | **120 hero-owned token objects** |

Each sampled game has no unknown token-event object references, no token-kind event referencing an explicitly nontoken object, and every referenced snapshot object exists in the final crosswalk.

**Critical semantics:** the native kind-31 token recipe event generally has `obj:null` and the created object appears in a subsequent event (e.g. `kind:6`, entering battlefield). Token event count and final crosswalk token object count are not inherently identical: do **not** use `event.obj` to directly map all creation events to objects. The early semantic drilldown that treated kind-31 `obj` as mandatory falsely labeled all objects unmatched; it is a **diagnostic limitation, not an observed error**. Count differences alone do not establish missing creation. Exact attribution requires a source-based ordered recipe/zone-entry reconciliation.

**Observed commander activation:** Wretched's 69 hero-owned Zombie objects agree with its 69 zombie recipe events; Necrons' 24 Warrior objects agree with 24 Warrior recipe events; Magnus displays a diverse appropriate token family including Servos and Spawns. Mortarion produced some own Astartes/Treasure/Soldier tokens but only three hero-owned token objects in four games. This is **insufficient exposure** to certify all Mortarion trigger/sacrifice token engines; create targeted scenarios for them. Counts do NOT prove that any specific card activated at the correct frequency or produced correct combat characteristics (power/toughness, tapped/attacking, duration or replacement effects). A hand-reviewed oracle/source-to-token replay is still needed.

## Source-backed warnings / suspected fidelity gaps

1. **Magnus, seed 219201: 96 aborted cast attempts** around **Artistic Refusal**: 80 `cast aborted: cost no longer payable` and 16 `cast aborted: no legal target`. The recordings remain replay-verified; this suggests a pilot/targeting/cost retry loop and could bias game simulations. Diagnose legal option generation, convoke cost and reset behavior; create one deterministic regression.
2. **Adeline, Resplendent Cathar** generates attacking Human tokens, but native source explicitly warns `TokenAttacking$ RememberedPlayer & Valid Planeswalker.ControlledBy Remembered: the planeswalker arm is not implemented; the token attacks the named player`. Observed **11** occurrences in Magnus games (219201, 219202) and **2** in Necrons game 219301. Need verify target selection and whether any planeswalker-targeting alternative was relevant to each state; failure to implement branch is a known rule-coverage gap, not proof these exact states yielded invalid outcomes.
3. **Technomancer**, Magnus game 219200 as an opponent card, emitted `ChangeZone ignores unread parameter(s) AnyNumber$` during a graveyard/mill effect. Check whether desired number of objects and source zone changes are correct.
4. Other events such as `looks at the top of the library`, `clears remembered/imprinted objects`, and `cast aborted` are not automatically evidence of rules violations. Some are informational; case review required.
5. **Pilot and card-role attribution:** hero-owned tokens are distinguished from the 3 opponents' tokens. Seat-zero omitted `player` means seat 0 (never infer the active player); `owner` is not always historical controller. This audit did not independently reconstruct controller changes over time.

## Before running a larger corrected official batch

- Add deterministic Gorge regression for repeated **Artistic Refusal** attempts, inspecting availability of legal targets, convoke cost payment and event/intent retry loop. Ensure capped retries and meaningful failure classification.
- Review **Adeline** attacking-token target choice against Oracle rules and actual opponent planeswalker presence, then fix or document/qualify the unsupported branch.
- Reproduce **Technomancer** graveyard-zone selection with exact `AnyNumber$` parameter interpretation.
- Add per-card recipes / source-event-then-zone-entry token linkage (rather than assuming kind-31 `obj` identifies a token). Verify owner/controller, characteristics, token quantity, entry tapped/attacking and disappearance, at least for Astartes, Servo, Spawn, Zombie and Necron Warrior.
- Run targeted Mortarion token-engine cases to ensure enough activation coverage. Repeat four-hero small qualification after fixes using new unused seeds and full native retention.
- Compare exact engine, patch, card corpus, deck SHA, opponent panel and pilot versions against the approved corrected baseline. Keep any divergent batches experimental; do not mix with the 24 approved games until eligibility checks pass.
- Only then schedule a larger staged 100-game-per-hero batch with complete R2 preservation, reviewed source inventory, and approval-gated atomic production publication.

**Scope:** These 16 simulations are smoke and fidelity diagnostics, not official performance data or statistically independent proof of engine correctness.

## Experimental repair branch — November 6 follow-up

This section supersedes earlier wording that all three findings remain untouched. Every change below remains isolated to this branch and intentionally changes the rules/pilot fingerprint versus the approved baseline. Neither main nor R2 current pointers have been modified.

- **Technomancer**: `tools/patch_gorge_changezone_anynumber.py` teaches the pinned `api:ChangeZone` compiler the explicit `AnyNumber$ True` parameter and extends the hidden public-graveyard picker to allow a zero-to-eligible-card range, preserving `WithTotalCMC$` sum budget and prioritizing explicit `ChangeNum$`. [Focused compilation/parameter tests passed](https://github.com/bgoodnight/commander-simulator/actions/runs/42295134940); [original seed 219200 reconstructed with patch and finished/replay-verified; missing-parameter warning count zero](https://github.com/bgoodnight/commander-simulator/actions/runs/42295533537). Still require a **positive multiple-artifact-creatures chosen under budget** semantic regression before calling full card behavior certified.
- **Adeline**: `tools/patch_gorge_adeline_token_defender.py` uses Gorge's established `enteringDefenders`/AskTape player-or-planeswalker selection; restricts eligible walker to the remembered opponent, never others/battles, and falls back to the opponent when no answer is served. [Focused original rules/replay tests passed](https://github.com/bgoodnight/commander-simulator/actions/runs/42296203973). A new test `tools/gorge_adeline_planeswalker_test.go` checks the actual PW option; see [positive CI](https://github.com/bgoodnight/commander-simulator/actions/workflows/gorge-adeline-rule-fix.yml) for status. A live PW *selected* on the decision tape would be the next strongest check.
- **Artistic Refusal**: [exact original seed 219201 and modes captured](https://github.com/bgoodnight/commander-simulator/actions/runs/42296117836). The card (owner seat 1) had 97 proposals and 96 reversals in the original trace, from `KChoose` Convoke announcements / subsequent cost or target reversals. The experimental generic `tools/patch_gorge_convoke_pilot_fallback.py` retains available non-mana-producer Convoke helpers even if the **current floating pool** alone cannot finish the cost; the Gorge 601.2g/h payment-stranded guard still enforces real payment. [Same failing seed passed](https://github.com/bgoodnight/commander-simulator/actions/runs/42296990411), with cost aborts **80 → 28**, target aborts **16 → 6**, total **96 → 34**, finished/replay-verified. The **34 remaining** are unresolved and the heuristic may need stronger independent pilot fairness testing. Do not infer valid strategic play merely from fewer aborts.

[Combined four-hero fresh-seed CI](https://github.com/bgoodnight/commander-simulator/actions/workflows/gorge-four-hero-rules-regression.yml) integrates all three overlays, four games per hero, immutable local private artifacts only; gate promotion on its result plus targeted still-missing cases. Do not approve a new source cohort until the engine/pilot fingerprints and full rules audit have passed and reviewed source inventory has been updated.
