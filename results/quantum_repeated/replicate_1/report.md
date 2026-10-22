# JalQ-R exploratory benchmark repor

**Mode:** QUANTUM
**Held-out episodes:** 30
**Development episodes:** 10
**Random invocation probability, calibrated on development:** 0.050

**Metrics: lower simulated realized moisture stress is better.**

| Policy | Mean realized stress ± SD | Δ vs classical (paired) | Forecast gap | Planner seconds / episode (mean ± SD) | Q calls (completed/requested) | Shots | 2Q gate-shots |
|---|---:|---:|---:|---:|---:|---:|---:|
| never | 2,657.2 ± 1,200.0 | +0.0 | 0.00 | 0.007058 ± 0.001358 | 0/0 | 0 | 0 |
| always | 2,657.2 ± 1,200.0 | +0.0 | 0.00 | 0.198163 ± 0.360988 | 62/62 | 23808 | 700416 |
| selective | 2,657.2 ± 1,200.0 | +0.0 | 0.00 | 0.016543 ± 0.023859 | 6/6 | 2304 | 50688 |
| random | 2,657.2 ± 1,200.0 | +0.0 | 0.00 | 0.016693 ± 0.023990 | 5/5 | 1920 | 59904 |
| extra_classical | 2,657.2 ± 1,200.0 | +0.0 | 0.00 | 0.007474 ± 0.002165 | 0/0 | 0 | 0 |
| exact_classical | 2,657.2 ± 1,200.0 | +0.0 | 0.00 | 0.012337 ± 0.002542 | 0/0 | 0 | 0 |

Negative paired difference means lower realized moisture stress than classical-only.
Forecast gap is selected-schedule risk minus the exact post-hoc optimum under the same available forecast/scenario model; it is not a future-weather oracle or policy outcome.

## Interpretation and limitations

Qiskit Aer invocations completed. These results are not evidence of quantum advantage without stronger baselines and statistical evaluation.
- Simulated farm model and forecast generator, not agronomically validated
- Quantum cost reported in shot counts and gate-weighted shots, not hardware time
- The original heuristic's random policy has fixed 0.5 probability; this experiment instead calibrates Bernoulli calls on development episodes
- Random and selective invocation rates may differ on held-out episodes; check their observed rates
- Extra-classical baseline is the current 8-round local search, not strictly matched to quantum CPU cos
- Planner score requests, unique loss vectors, scenario evaluations, and offline exact enumeration are reported separately; none is CPU time or a hardware-equivalent cos
- The exact forecast reference for other policies is post-hoc; exact_classical deliberately uses this same current-forecast enumeration as an expensive adaptive classical baseline, without observing future realized weather
- Current quantum engine uses p=1 with three fixed pilot parameter combinations; this is not a full variational parameter optimizer
- The current empirical CVaR averages the worst ceil(tail_fraction*scenario_count) simulated values (approximation)
- Local wall-clock planner runtime is machine- and load-dependent; it is not a quantum hardware timing claim
- Quantum mode must yield completed Qiskit circuit calls; smoke mode cannot establish quantum performance
- Synthetic truth is revealed only after each policy commits current-window irrigation decisions
- Forecast differences between policies arise only from endogenous past irrigation decisions, not different exogenous weather

Repeat the quantum benchmark with multiple seeds before using it in a presentation.
