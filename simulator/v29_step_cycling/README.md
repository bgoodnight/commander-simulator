# V29 Step Through and cycling triggers

`StepCyclingTable` adds Step Through's 3UU sorcery: it requires two distinct legal creature targets, and returns each that remains legal on resolution. If both targets become illegal the spell fizzles. Targets are available through `step_action` and priority choices. The existing wizardcycling mode remains available. Actual spell costs use the existing Magnus and Sapphire reductions.

Wizardcycling now emits a battlefield `cycled` trigger event; registered `controller_cycles` listeners may queue supported trigger operations. This deliberately does not implement ordinary cycling, triggers on the cycled card in a graveyard, arbitrary cycling effects, reveal visibility, or full target restrictions. The cycling-watcher tests use a synthetic ability, not a claim that a named watcher is implemented. No new cache is added.

Official reference: [Modern Horizons 2 release notes](https://magic.wizards.com/en/news/feature/modern-horizons-2-release-notes-2021-06-04). See the coverage audit and source-paid interaction report in this folder.
