# V16 assessment

Fourteen focused v16 tests and 585 historical tests pass. Two forced narratives use source-paid mana; one uses an explicitly synthetic target-removal response. The seeded 200-game, 12-round sweep passed the existing consistency and card-conservation checks across all four seats, with zero safety stops and six channel activations. A Brainstorm response is exercised in the test suite.

The median eight-round runtime over 12 samples was 572.472 ms for v15 and 559.035 ms for v16 in the same invocation. Different decisions and host conditions mean these measurements do not isolate the cost of channel. Existing caches are unchanged; no new caching was introduced. V14 reference cases remain preserved.

Sokenzan remains partial because the kernel does not represent token color. Legendary-creature cost reductions rely on card metadata and modeled continuous effects; Baral's missing legendary supertype is supplied for v16. Unmodeled replacement effects, color-sensitive interactions and broader type/layer mechanics are outside this milestone. The sweep has one detailed deck and synthetic opponents; it does not establish deck win rates.
