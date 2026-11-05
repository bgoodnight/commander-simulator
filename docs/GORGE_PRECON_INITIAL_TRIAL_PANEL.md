# Initial Gorge precon opponent rotation — preparation only

This is a **non-production** 12-deck experimental rotation selected from 60
stock Commander precons, using the genuine source-backed Gorge
Mortarion/Magnus run artifacts from
[workflow 42053608363](https://github.com/bgoodnight/commander-simulator/actions/runs/42053608363).
The preparation workflow performs **no simulations** and does not touch R2.

## Evidence assessed

- 60 candidate stock precons imported; all encountered in both 60-game runs.
- 40 had complete Oracle card-name resolution and no engine errors, draws or
  turn-limit stalls in their three exposures per player deck (six total).
- 12 were chosen for varied color identities, release eras and strategic
  hypotheses. All 12 have 3/3 completed, verified trials against each of
  Mortarion and Magnus, an exact pinned source decklist SHA-256 and the
  same Oracle bulk provenance.
- This is **stability screening**, not a test of signature-mechanic
  fidelity, play quality, or deck power. No decks have passed manual
  rules/pilot certification yet.

The prepared initial rotation is:

1. Guided By Nature (G)
2. Peer Through Time (U)
3. Sneak Attack (UB)
4. Party Time (WB)
5. Draconic Rage (RG)
6. Swell the Host (UG)
7. Virtue and Valor (WG)
8. Quick Draw (UR)
9. Arm for Battle (WR)
10. World Shaper (BRG)
11. Science! (URW)
12. Eldrazi Incursion (WUBRG)

The canonical keys and immutable source hashes live at
`data/gorge_initial_trial_opponents_v1.json`.

## Workflow and safeguards

- `.github/workflows/gorge-precon-evidence.yml` rebuilds a per-deck
  qualification report from prior two-hero recordings. It produces
  `precon-qualification.json`, `experimental-opponents.json` and
  `opponents.txt`. The first 40 may enter *bounded tests*; the 12 are
  the explicitly pinned initial test rotation.
- `tools/gorge_trial_panel_validate.py` refuses changed source cards,
  stale Oracle hashes, active-role confusion, or an unauthorized player deck.
- `.github/workflows/gorge-precon-60-qualification.yml` is **manual only**.
  Later, after UI readiness, dispatch it with `panel_mode=initial12`
  or `panel_mode=all60`, and `games=12` or `games=60`.
- The test population always remains `experimental_rotation_only` and
  `eligible_for_analytics=false`. No current cohort gets approved from
  this trial. Games are stored as diagnostic artifacts, not benchmark data.

## Remaining work before production activation

Review representative card mechanics and pilot decisions from genuine native
traces, including underrepresented strategies and repeatable effects; verify
decklist legality under the selected card corpus; assess the six turn-limit
stalls; validate consistency under the approved rules patch; then prepare
and review production admission for a first cohort. Full benchmark runs,
including any fresh Mortarion/Magnus large sample, stay deferred until
UI deployment is ready.

GitHub Actions evidence artifacts have retention limits. Preserve the
compact audit report and relevant native-replay evidence separately before
they expire. No historical R2 data should be deleted or retroactively
marked production approved.
