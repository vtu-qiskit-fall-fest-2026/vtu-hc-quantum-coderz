# Reproduce the hybrid benchmark

Install full requirements for real Qiskit Aer. Run from the repository root:

```powershell
python experiments.py --mode quantum --field-specific --dev 4 --test 6 --shots 384 --seed 20261022 --output results/hybrid_field/replicate_1
python experiments.py --mode quantum --field-specific --dev 4 --test 6 --shots 384 --seed 20262022 --output results/hybrid_field/replicate_2
python experiments.py --mode quantum --field-specific --dev 4 --test 6 --shots 384 --seed 20263022 --output results/hybrid_field/replicate_3
python tools/summarize_repeated_benchmarks.py --root results/hybrid_field --replicates 3
```

Use a NEW output folder for modified experiments. Remove `--field-specific` only for the shared-weather model. `--mode smoke` guarantees classical execution and is not quantum-performance evidence.

Each run saves steps, episodes, policy summary, versions, seed lists and a report. Three replicates contain 18 held-out episodes per policy; all policies share exogenous weather within an episode. Development-only classical rollouts calibrate random invocation probability. Actual quantum calls can differ between random and selective on held-out episodes.

Planner elapsed seconds exclude the separate post-hoc exhaustive auditor. Cold imports and machine load affect timings. Gate-shot and scenario-operation counters are proxies, not energy or hardware cost. The full CVaR score is classical; phase/tuning use expected stress. Exact classical is an explicit current-forecast enumeration reference. Extra classical is not compute-matched to quantum optimization.

Noisy hardware experiments, larger instances and a powered comparative study remain future work. The small fresh study found no quantum improvement over the classical incumbent.
