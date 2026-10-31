# Package extraction, first seam

`ServiceRegistry` validates unique names, dependencies, and cycles before constructing any service. Each `build()` calls factories anew and returns a read-only service mapping; factories remain responsible for producing independent mutable state. Dependencies are passed as read-only mappings. The registry is deliberately independent of particular cards, decks, and legacy imports.

`commander_sim.legacy.run(deck='premium', seed=0, rounds=8)` invokes the existing CLI in a separate interpreter and returns its JSON result. Subprocess isolation prevents the historical modules' unqualified names and `sys.path` manipulation from contaminating the caller. This is a compatibility adapter, not an in-process migration or an implementation of multiple detailed decks. It does not yet expose game objects, policy injection, or an event stream.

Run package contracts with `python -m unittest discover -s tests -q`; the repository's `run_all_tests.py` also runs them. The next extraction should move a real service behind a narrow interface and compare it against the saved replay baselines before changing the live engine.
