# V18 assessment

The canonical v1.13 list contains 100 physical cards, one commander, 14 Islands and 6 Mountains. The adapter preserves exact names and quantities, and the historical v1.6 tables remain available. Full Oracle identity, color identity and Commander legality checks remain outstanding. Twenty-nine distinct names are absent from the old catalog and are intentionally inert with unknown type. Mystical Tutor is unavailable while unknown card types remain in the library. Phyrexian Altar is a normal game object but its effect is not implemented.

All 610 tests passed. The 200-game 12-round v1.13 sweep checked physical-card conservation and other engine invariants in all four seats with zero safety stops. The median 8-round v1.13 game time over 12 samples was 457.988 ms. Historical benchmarks use a different deck and cannot be used for a controlled speed comparison. No additional caching was introduced.

The audit is an initial inherited coverage report, not an independent certification of older card metadata. Unverified cards and missing rules mean these games cannot establish deck strength or validate combo lines.
