# JalQ-R Benchmark — how to run

This experimental harness runs **rolling-horizon irrigation decisions** over multiple synthetic weather episodes. It compares all five JalQ-R policies, and writes reproducible CSV tables and a Markdown report. No field or hardware benefit is claimed.

## From the official repo folder (PowerShell)

```powershell
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
```

Classical-only smoke test (do not cite as quantum performance):

```powershell
python experiments.py --mode smoke --dev 4 --test 6 --output results/smoke
```

**Actual Qiskit Aer benchmark** (will take longer):

```powershell
python experiments.py --mode quantum --dev 4 --test 6 --shots 384 --output results/quantum
```

Larger repeated test, if your laptop has capacity:

```powershell
python experiments.py --mode quantum --dev 8 --test 20 --shots 384 --output results/quantum_20
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
5. Maximum quantum calls are enforced per trajectory across all quantum policies (default three). The underlying web UI **does not yet persist this budget**.
6. Reported `classical_evaluations_reported` excludes some model work and is not a fair all-in classical compute-cost measure. This version's extra-classical search is not compute-matched to quantum tuning.
7. Qiskit Aer results are **simulator results**, not quantum hardware performance. Cost summaries use actual reported shots and the project's compiled-gate proxy.
8. Risk-aware candidate selection uses the current project's approximate empirical CVaR calculation, not fractional-tail exact CVaR.
9. The current quantum engine uses p=1 and three fixed parameter trials; better variational optimizers and baselines remain future work.

## Recommendation for your PPT

Only cite `results/quantum*/report.md` produced on a machine that ran and completed the actual Qiskit code. Include the run settings (number of episodes, shot count, seed), explain limitations, and do not assume that selective quantum is better than classical unless the measured results demonstrate it.
