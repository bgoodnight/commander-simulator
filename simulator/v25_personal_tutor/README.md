# V25 Personal Tutor

`PersonalTutorTable` adds Personal Tutor as a U sorcery. On resolution, its controller may find a sorcery in their library, reveal it, shuffle, and place it on top. A `tutor_policy` chooses a legal object ID or `None` to fail to find; the default ranks legal cards using the existing simple selection heuristic. The policy sees a `personal_tutor` request, distinct from Mystical Tutor. Card types use v20's verified kernel data, while unsupported effects remain inert.

Focused checks cover sorcery-only candidates, fail-to-find and shuffle, legal timing through the priority choices, colored mana, Young Pyromancer, and tutoring and casting Ral's Reinforcements. A source-paid narrative follows that tutor chain. The engine retains partial simultaneous token-entry and card-color limitations from earlier versions, and no new caching is introduced.

Reference: [Scryfall Personal Tutor](https://scryfall.com/card/ptk/53/personal-tutor).
