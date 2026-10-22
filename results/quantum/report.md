# JalQ-R exploratory benchmark report

**Mode:** QUANTUM  
**Held-out episodes:** 6  
**Development episodes:** 4  
**Random invocation probability, calibrated on development:** 0.125  

**Metrics: lower simulated realized moisture stress is better.**

| Policy | Mean realized stress ± SD | Δ vs classical (paired) | Q calls | Shots | Gate-weighted shots |
|---|---:|---:|---:|---:|---:|
| never | 2,709.7 ± 1,700.4 | +0.0 | 0 | 0 | 0 |
| always | 2,709.7 ± 1,700.4 | +0.0 | 13 | 4992 | 142848 |
| selective | 2,709.7 ± 1,700.4 | +0.0 | 1 | 384 | 9216 |
| random | 2,709.7 ± 1,700.4 | +0.0 | 1 | 384 | 9216 |
| extra_classical | 2,709.7 ± 1,700.4 | +0.0 | 0 | 0 | 0 |

Negative paired difference means lower realized moisture stress than classical-only.

## Interpretation and limitations

Qiskit Aer invocations completed. These results are not evidence of quantum advantage without stronger baselines and statistical evaluation.
- Simulated farm model and forecast generator, not agronomically validated
- Quantum cost reported in shot counts and gate-weighted shots, not hardware time
- The original heuristic's random policy has fixed 0.5 probability; this experiment instead calibrates Bernoulli calls on development episodes
- Random and selective invocation rates may differ on held-out episodes; check their observed rates
- Extra-classical baseline is the current 8-round local search, not strictly matched to quantum CPU cost
- Reported classical_evaluations undercounts greedy/QUBO work and should NOT be called total classical cost
- Current quantum engine uses p=1 with three fixed pilot parameter combinations; this is not a full variational parameter optimizer
- The current empirical CVaR averages the worst ceil(tail_fraction*scenario_count) simulated values (approximation)
- Quantum mode must yield completed Qiskit circuit calls; smoke mode cannot establish quantum performance
- Synthetic truth is revealed only after each policy commits current-window irrigation decisions
- Forecast differences between policies arise only from endogenous past irrigation decisions, not different exogenous weather

Repeat the quantum benchmark with multiple seeds before using it in a presentation.
