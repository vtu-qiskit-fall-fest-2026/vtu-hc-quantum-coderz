# Repeated held-out Qiskit Aer policy comparison

**Replicates:** 3; **held-out episodes per policy:** 90; **development episodes per replicate:** 10.
**Run:** Qiskit Aer ideal simulator; 384 shots per call; 15 uncertainty scenarios; maximum 3 calls per episode.
**Outcome:** lower synthetic realized moisture stress is better. Negative paired differences favor the named policy over `never`.

| Policy | Mean stress ± SD | Paired Δ vs never (normal 95% CI) | Wins/ties/losses | Q completed/requested | Improvements | Shots | 2Q gate-shots | Forecast gap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| never | 2743.75 ± 1210.17 | +0.00 [+0.00, +0.00] | 0/90/0 | 0/0 | 0 | 0 | 0 | 0.00 |
| always | 2743.75 ± 1210.17 | +0.00 [+0.00, +0.00] | 0/90/0 | 182/182 | 0 | 69888 | 2082816 | 0.00 |
| selective | 2743.75 ± 1210.17 | +0.00 [+0.00, +0.00] | 0/90/0 | 11/11 | 0 | 4224 | 96768 | 0.00 |
| random | 2743.75 ± 1210.17 | +0.00 [+0.00, +0.00] | 0/90/0 | 5/5 | 0 | 1920 | 59904 | 0.00 |
| extra_classical | 2743.75 ± 1210.17 | +0.00 [+0.00, +0.00] | 0/90/0 | 0/0 | 0 | 0 | 0 | 0.00 |
| exact_classical | 2743.75 ± 1210.17 | +0.00 [+0.00, +0.00] | 0/90/0 | 0/0 | 0 | 0 | 0 | 0.00 |

## Interpretation

These are paired comparisons across the same held-out synthetic weather episode IDs. The confidence intervals are descriptive normal approximations and do not correct for multiple policy comparisons. Quantum samples are classically rescored, and the classical incumbent is retained unless a sampled schedule scores better under the planner objective. `exact_classical` exhaustively enumerates each current feasible schedule set using the same forecast scenarios; it is an expensive, exact current-model reference, not a future-weather oracle. A completed Qiskit call therefore does not imply an improvement.

## Limits

- All weather and moisture values are synthetic and are not field validation.
- Aer is an ideal simulator and the result is not quantum hardware evidence.
- No policy showed benefit unless supported by the paired held-out outcomes; inspect wins, ties, losses and confidence intervals.
- Gate-shot totals are compiled two-qubit or all-gate instruction counts multiplied by shots, not runtime, energy, or hardware cost.
- Classical scenario counts are operation proxies; CPU time is reported separately and is machine-dependent.
- The exact_classical policy enumerates the same current forecast/scenario model at each decision and is an expensive classical reference, not a future-weather oracle.

Inputs and per-run outputs are preserved under `replicate_1/` through `replicate_3/`. The JSON metadata records seeds and settings.
