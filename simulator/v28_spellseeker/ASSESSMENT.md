# V28 assessment

Spellseeker is a 2U 1/1 Human Wizard. Its optional ETB trigger searches for an instant or sorcery card with mana value at most two, reveals it, puts it in hand and shuffles. Declining the optional search does not shuffle; failing to find after choosing to search does. Tested interactions include Harmonic Prodigy doubling the trigger and a bounce response leaving the trigger intact. A source-paid narrative follows Step Through wizardcycling into Spellseeker into Consider.

All 703 tests passed locally. A 200-game v1.13 sweep passed consistency checks across all seats without safety stops. Median eight-round runtime was 321.561 ms over 12 games; host and game trajectory differences limit comparisons. Four v14 reference fingerprints, one per seat, still match. No additional caching.

The mana-value helper supports known v1.13 costs and fails closed for unknown symbols or card names. General reveal visibility, cycling triggers, color-changing effects, continuous layers and the Step Through sorcery mode remain unsupported. These games do not establish deck strength.
