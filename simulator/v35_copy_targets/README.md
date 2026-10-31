# V35 copied spell targets

Reiterate can now copy a registered counterspell and change its stack target, copy Step Through while preserving or changing its two distinct creature targets, copy Abrade with its chosen mode, and copy another Reiterate. A copied Step Through rechecks targets separately on resolution; if at least one remains legal it resolves. Changed targets must be legal when chosen; unchanged targets can become illegal.

The choice hook `copy_target_policy(controller, original_action)` returns a stack frame ID for a copied counterspell/Reiterate, a pair of permanent IDs for Step Through, or an object ID for supported single-target effects. No policy means retain the original targets. Copies still aren't casts. This implementation remains a bounded subset: unsupported card effects, general multi-target/X selection, copies of arbitrary spell types, full protection/replacement rules and loop proofs are not implemented.
