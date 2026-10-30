# V23 assessment

Sapphire Medallion is a two-mana artifact that reduces the generic cost of its controller's printed blue v1.13 spells by one, including multicolored spells, without reducing colored pips. Printed spell colors come from the v20 Oracle snapshot; continuous color-changing effects and color metadata for synthetic opponent spells remain unsupported.

The 13 focused tests cover source identity, colored floor, red and multicolored spells, priority choices, removal, cost revalidation, Capsize buyback and combined Magnus/token reductions. A real-source narrative shows Medallion and Capsize buyback. All 650 tests passed locally, including all historical suites and the optional action-cost hook compatibility.

A 200-game v1.13 sweep passed consistency checks across all seats without safety stops. Median eight-round runtime was 574.176 ms over 12 samples; host load and changed game trajectories mean this is not a controlled comparison with earlier milestones. Existing caches remain unchanged. Many other cards, card-color changes, graveyard casting and full combo support remain incomplete. Games do not establish deck strength.
