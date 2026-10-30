# V17 Mystical Tutor

`TutorTable` uses the historical v1.6 deck and adds Mystical Tutor: a blue instant that searches its controller's library for an instant or sorcery, optionally fails to find, reveals the selection, shuffles, and puts the selected card on top. The choice occurs on resolution and uses live object identities. A `tutor_policy` may choose a legal object ID or `None`; the default uses the existing selection scoring heuristic. This is a bounded search policy, not an optimized tutor strategy.

Tests cover selection and subsequent draw, shuffle when declining to find, invalid selection, a Young Pyromancer interaction, and Brainstorm resolving in response before the search. The search uses current card type metadata; double-faced and general type-changing effects are outside scope. No additional caching was added.

Run `python simulator/v17_tutor/tests.py`, `python run_all_tests.py`, and `python simulator/v17_tutor/validate.py`. Rules reference: [Eternal Masters release notes](https://magic.wizards.com/en/news/feature/eternal-masters-release-notes-2016-06-02).
