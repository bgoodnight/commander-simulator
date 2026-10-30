# V22 assessment

Consider is implemented as a blue instant with surveil one and draw. Tests cover keeping or moving the card, source cost, empty-library loss, Young Pyromancer, Mystical Tutor and Sanctuary. The source-paid narrative follows tutor into Consider with Pyromancer, producing two tokens. Surveil-triggered abilities and general layers remain unimplemented.

All 637 tests passed locally. The 200-game 12-round v1.13 sweep passed consistency checks across four seats without safety stops. Median eight-round runtime was 675.022 ms over 12 samples; v21's separate earlier run recorded 324.504 ms. Host conditions and changed trajectories differ, so this is not a controlled measurement of Consider's overhead. Existing caches remain unchanged.

Numerous v1.13 card effects remain unsupported, including Sapphire Medallion, Phyrexian Altar, Underworld Breach, key tutors and copy producers. Results do not establish deck strength.
