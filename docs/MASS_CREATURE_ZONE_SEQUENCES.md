# Mass creature zone sequence — bounded first pass

Source-independent three-phase operation for Living Death-like rules:
1. Record and exile creature cards in participating players' graveyards.
2. Record and sacrifice all creatures those players control.
3. Return only cards exiled by phase 1 onto the physical battlefield.

This is a mechanics-level primitive, **not source-verified full Living Death
support**. It requires a separately authorized spell and normal mana payment.
Replacement effects, commander zone choices, APNAP triggered-ability ordering,
priority and true simultaneous movement still require additional host work.
The helper refuses to act when a battlefield commander would need an
unreviewed replacement choice and does not register Living Death as castable.

No new tournament or simulation results are published by this change.
