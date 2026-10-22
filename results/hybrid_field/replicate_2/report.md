# JalQ-R exploratory benchmark report

**Mode:** QUANTUM
**Farm model:** field_specific; **engine:** XY-QAOA p=1 COBYLA
**Held-out episodes:** 6
**Development episodes:** 4
**Random invocation probability, calibrated on development:** 0.375

**Metrics: lower simulated realized moisture stress is better.**

| Policy | Mean realized stress ± SD | Δ vs classical (paired) | Forecast gap | Planner seconds / episode (mean ± SD) | Q calls (completed/requested) | Shots | 2Q gate-shots |
|---|---:|---:|---:|---:|---:|---:|---:|
| never | 3,683.7 ± 891.5 | +0.0 | 0.00 | 0.008298 ± 0.004121 | 0/0 | 0 | 0 |
| always | 3,683.7 ± 891.5 | +0.0 | 0.00 | 1.398728 ± 2.391046 | 12/12 | 4608 | 138240 |
| selective | 3,683.7 ± 891.5 | +0.0 | 0.00 | 0.136733 ± 0.094143 | 4/4 | 1536 | 36864 |
| random | 3,683.7 ± 891.5 | +0.0 | 0.00 | 0.117683 ± 0.110556 | 3/3 | 1152 | 32256 |
| extra_classical | 3,683.7 ± 891.5 | +0.0 | 0.00 | 0.018039 ± 0.001625 | 0/0 | 0 | 0 |
| exact_classical | 3,683.7 ± 891.5 | +0.0 | 0.00 | 0.036670 ± 0.010155 | 0/0 | 0 | 0 |

Negative paired difference means lower realized moisture stress than classical-only.
Forecast gap is selected-schedule risk minus the exact post-hoc optimum under the same available forecast/scenario model; it is not a future-weather oracle or policy outcome.

## Interpretation and limitations

Qiskit Aer invocations completed. These results are not evidence of quantum advantage without stronger baselines and statistical evaluation.
- Simulated farm model and forecast generator, not agronomically validated
- Quantum cost reported in shot counts and gate-weighted shots, not hardware time
- The original heuristic's random policy has fixed 0.5 probability; this experiment instead calibrates Bernoulli calls on development episodes
- Random and selective invocation rates may differ on held-out episodes; check their observed rates
- Extra-classical baseline is the current 8-round local search, not strictly matched to quantum CPU cost
- Planner score requests, unique loss vectors, scenario evaluations, and offline exact enumeration are reported separately; none is CPU time or a hardware-equivalent cost
- The exact forecast reference for other policies is post-hoc; exact_classical deliberately uses this same current-forecast enumeration as an expensive adaptive classical baseline, without observing future realized weather
- Current quantum engine uses p=1 XY-QAOA with budgeted COBYLA trials; fixed angles remain a separate comparison baseline
- Final risk uses fractional-tail empirical CVaR; the phase circuit uses expected quadratic stress only
- Local wall-clock planner runtime is machine- and load-dependent; it is not a quantum hardware timing claim
- Quantum mode must yield completed Qiskit circuit calls; smoke mode cannot establish quantum performance
- Synthetic truth is revealed only after each policy commits current-window irrigation decisions
- Forecast differences between policies arise only from endogenous past irrigation decisions, not different exogenous weather

Repeat the quantum benchmark with multiple seeds before using it in a presentation.
