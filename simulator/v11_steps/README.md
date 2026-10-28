# V11 — ordinary turn steps and a focused card batch

October 28, 2026. This iteration adds explicit ordinary-turn timing and replaces
serial attacker-by-attacker damage with one combat damage batch. It enables
three named cards and upgrades one existing partial effect. V10 remains the
rollback checkpoint; this is not a complete Commander implementation.

## Added cards and rules

| Card | Implemented behavior | Important interactions checked |
|---|---|---|
| Abrade | Announce one mode: 3 damage to a creature, or destroy an artifact | Accumulated damage, indestructible, hexproof, mode-specific targets, no automatic mode switch when a target leaves |
| Capsize | Bounce a permanent; optional buyback 3 | Add buyback before generic cost reductions; preserve UU; return only on successful resolution; counters/fizzles send it to graveyard; tokens cease rather than enter hand |
| Arcane Adaptation | Enchantment with the declared **Wizard** choice; additive creature types across battlefield, spell stack and owned off-battlefield cards | Harmonic Prodigy doubles an adapted Third Path Iconoclast; already queued triggers survive removal; later casts stop benefiting when the enchantment leaves |
| Frantic Search | Draw 2, discard 2, untap up to 3 chosen lands in one resolution | No intermediate priority; lands are not targeted and may be opponents'; actual source IDs become usable again; rocks do not untap |

Printed card definitions are not rewritten when Adaptation is present. The shared
kernel derives additive subtypes from static ability descriptors, and trigger
eligibility queries use those derived types. Only the tested Wizard choice is
exposed here; this is not an unrestricted creature-type/layer engine.

Casting options travel with the announced action. Additional-cost choices are
validated before payment. Capsize's buyback return is a resolution destination;
it does not occur if the spell is countered or all its targets are illegal.
Other buyback spells remain unsupported.

## Turn and combat changes

The driver exposes untap, upkeep, draw, first main, beginning of combat, attacker
declaration, blocker declaration, combat damage, end of combat, second main,
end and cleanup. No attackers means blocker/damage steps are skipped. Untap gives
no priority; ordinary cleanup gives none unless a triggered/SBA window requires
it. Mana pools empty between exposed steps/phases, and a land drop is a main-phase
special action with priority and an empty stack, once across both main phases.

Attackers are chosen and tapped together before responses. Blockers are declared
before another response window. Ordinary creature/player combat damage is
assigned from the resulting board and applied as one batch before the SBA/trigger
checkpoint. A creature remains blocked if its blocker leaves. Summoning sickness
uses the creatures controlled at the start of the player's turn, rather than a
global round number. Haste, vigilance, flying/reach and existing target/keyword
primitives are exercised. One blocker per attacker is the supported assignment
subset; no multi-block ordering, first/double strike or trample is claimed.

Synthetic engine/clock upkeep effects are now declared trigger frames. A synthetic
combo finisher that loses its setup in response resolves without eliminating
players, rather than raising an exception. These remain explicitly synthetic
opponent effects, not printed combo-card implementations.

## Validation and narratives

```bash
python run_all_tests.py
python simulator/v11_steps/validate.py
```

There are **372 tests across eleven suites**, including **50 new v11 tests**.
`validate.py` defaults to 200 twelve-round games (50 seeds in each Magnus seat),
five targeted interaction stories and two unforced seeded games. The targeted
stories preserve card inventories and use actual source-object payments; their
starting boards and selected cards are explicitly forced diagnostics.

Read [INTERACTION_REPORT.md](INTERACTION_REPORT.md) for observed outcomes. Each
story has a Markdown transcript and JSON state/payment/priority diagnostics.
`--narratives-only` refreshes those files without replacing a recorded sweep.

For programmatic use, put this directory on the Python path and import
`StepTable` from `stepped`. Policies receive the same v10 priority interface;
expanded utility spells additionally expose legal mode/buyback/target choices.
The default pilot avoids deliberately destroying/bouncing its own board, while
explicit policies may choose those legal targets.

## Remaining limits

Only one detailed Magnus deck is live. Other card effects and many existing named
bodies/triggers still represent subsets. The expansion does not implement Auras,
Equipment, planeswalker loyalty/attacks, first/double strike, trample, multiple
blockers, damage prevention, comprehensive continuous-effect layers, spell copies,
commander damage or verified loops. Creature tap activations remain gated.

Fabled Passage and several land ETB/utility effects retain their prior adapters;
temporary token expiry remains a cleanup adapter rather than a complete delayed
end-step trigger system. Generic scry/selection for other cards remains partial.
Only U/R/colorless mana and the existing supported cost subset are available.
No card-power or win-rate conclusions should be drawn from these diagnostics.
