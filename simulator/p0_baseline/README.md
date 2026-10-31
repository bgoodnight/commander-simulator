# P0 current-engine baseline

`python simulator/p0_baseline/baseline.py` checks four eight-round premium games, one in each seat, against committed SHA-256 fingerprints. Cases use fixed seeds and default pilot choices. The snapshot derives from the v14 semantic serializer and includes current Adventure/copy counts and event histories, final RNG states, zones, stack, choices recorded by the engine, payments and outputs. It is an end-of-game comparison, not a resumable mid-game snapshot or a complete action/choice transcript. A different deck file fails closed on its content hash; establish a deliberately reviewed baseline when behavior or deck changes intentionally.

The baseline was created against commit `d13047b22e9d915b670c9a98397ee35952d504d7`, after the Frostboil fix. The historical defect is documented in `docs/ARCHITECTURE_AUDIT.md`; it is not silently preserved as desired behavior.

`python simulator/p0_baseline/benchmark.py --samples 4 --output /tmp/commander-benchmark.json` records unprofiled initialization and eight/twelve-round timings, materialized target pairs, a payment-planning stress fixture and a spell-copy stack fixture. `BENCHMARK.json` is one exploratory host measurement, not a controlled comparison with past runs. Record each safety stop; do not change budgets or interpret results as deck strength.

Provider integration tests cover Frostboil and Altar in the assembled budget engine, Lindblum and Island in the current premium engine, and replay fingerprints across all four seats. These checks are a starting point, not proof that every card/provider is composed correctly.

`SCENARIOS.json` adds three explicit decision fixtures: Merchant Scroll finding Cyclonic Rift, Reiterate copying Consider with buyback, and Mage Siege with Harmonic Prodigy. Their mana pools are declared fixtures; they are not source-paid turn replays. The recorded choices and final semantic hashes are checked separately from the seeded game cases.
