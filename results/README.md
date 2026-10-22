# Measurement provenance

- `hybrid_field/`: NEW hybrid COBYLA + fractional-CVaR + field-specific rolling-horizon measurements, 3 x 6 held-out episodes. Reproduction commands in docs/experiments.md.
- `quantum/`, `quantum_24/`: unchanged historical main shared-weather fixed-angle studies.
- `member1_compare*.csv`: unchanged historical fixed-angle versus COBYLA sampling comparison; not farm-outcome improvement.
- `historical_test/quantum_repeated/`: unchanged test ZIP's historical 90-episode shared-weather study, fixed-angle and approximate CVaR.

Historical aggregate_metadata.json in the test archive has an incorrect hardcoded second/third seed block. Actual replicate metadata records development starts 20261022, 20262022, 20263022. The historical files are preserved as received; consult their per-run metadata. The hybrid aggregator fixes this for new runs by reading actual run settings.

Historical prose mentioning a “current” algorithm describes that older snapshot, not the hybrid. No archived results were relabelled as new measurements.
