# JalQ-R Benchmark — how to run

This experimental harness runs **rolling-horizon irrigation decisions** over multiple synthetic weather episodes. It compares six policies, including an exact classical current-forecast enumeration baseline, and writes reproducible CSV tables and a Markdown report. No field or hardware benefit is claimed.

## From the official repo folder (PowerShell)

```powershell
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
```

Classical-only smoke test (do not cite as quantum performance):

```powershell
python experiments.py --mode smoke --dev 4 --test 6 --output results/smoke
```

**Actual Qiskit Aer benchmark** (will take longer; install the full requirements):

```powershell
python experiments.py --mode quantum --dev 4 --test 6 --shots 384 --output results/quantum
```

Larger repeated test, if your laptop has capacity:

```powershell
python experiments.py --mode quantum --dev 8 --test 20 --shots 384 --output results/quantum_20
```

Repeated comparison used for the current report (3 independent seed blocks; 90 held-out episodes per policy):

```powershell
python experiments.py --mode quantum --dev 10 --test 30 --shots 384 --scenario-count 15 --max-quantum-calls 3 --seed 20261022 --output results/quantum_repeated/replicate_1
python experiments.py --mode quantum --dev 10 --test 30 --shots 384 --scenario-count 15 --max-quantum-calls 3 --seed 20262022 --output results/quantum_repeated/replicate_2
python experiments.py --mode quantum --dev 10 --test 30 --shots 384 --scenario-count 15 --max-quantum-calls 3 --seed 20263022 --output results/quantum_repeated/replicate_3
python tools/summarize_repeated_benchmarks.py
```

## Outputs

- `steps.csv`: per-weather-window forecasts, gate indicators, calls, scores and realized stress.
- `episodes.csv`: four-window trajectory metrics for each policy and episode.
- `summary.csv`: average test-episode scores, deviations and quantum cost totals.
- `metadata.json`: seeds, randomized-policy calibration, cost accounting and caveats.
- `report.md`: pasteable summary table and limitations.

The `--mode quantum` flag refuses to run without Qiskit and raises an error if a requested quantum circuit does not complete. The `--mode smoke` flag is only for debugging and **must not be included as quantum research evidence**.

## Scientific integrity

1. Every policy faces the same underlying four-window realization in a given episode. Its decisions may cause a different soil-moisture trajectory.
2. The planner sees only the current forecast and realized *past* weather; simulated actual weather for future windows is used only after a schedule decision.
3. A fixed random-invocation probability is calibrated on separate development episodes using classical rollouts. It is not chosen by looking at final test results. The observed invocation frequencies will not necessarily match exactly on small held-out sets.
4. `never`, `always`, `selective`, `random`, and `extra_classical` use the same actual project code. Random is driven by the benchmark rather than the prototype's fixed 50% coin flip.
5. Maximum quantum calls and total shots are enforced across each benchmark trajectory. The web demo carries the same explicit call/shot budget between rolling replans and persists it in browser storage until Reset demo is selected.
6. Classical work is reported as score requests, unique loss vectors, scenario evaluations and exact-enumeration candidate counts. These are model-work proxies, not CPU-equivalent operations. Wall-clock time is reported separately.
7. The `exact_classical` baseline exhaustively minimizes the current forecast/scenario objective at every decision. It is an expensive adaptive classical reference and does not see future realized weather. `extra_classical` remains the extended local-search baseline.
8. Qiskit Aer results are **simulator results**, not quantum hardware performance. Cost summaries include actual shots and compiled two-qubit gate-shots plus all compiled gate-shots; these are accounting proxies, not runtime or energy.
9. Per-episode local planner wall time is measured alongside quantum costs. It depends on machine load and is not a hardware-time comparison.
10. Risk-aware candidate selection uses the current project's approximate empirical CVaR calculation, not fractional-tail exact CVaR.
11. The current quantum engine uses p=1 and three fixed parameter trials plus a validation sample; learned variational optimizers and noise studies remain future work. Each allocation sums exactly to the configured shot cap, including at the supported 64-shot minimum.

## Recommendation for your PPT

Only cite `results/quantum*/report.md` produced on a machine that ran and completed the actual Qiskit code. Include the run settings (number of episodes, shot count, seed), explain limitations, and do not assume that selective quantum is better than classical unless the measured results demonstrate it.
