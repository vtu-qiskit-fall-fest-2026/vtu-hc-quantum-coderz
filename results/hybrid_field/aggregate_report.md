# Repeated held-out Qiskit Aer policy comparison

**Replicates:** 3; **held-out episodes per policy:** 18; **development episodes:** [4, 4, 4].
**Run:** quantum; field_specific; XY-QAOA p=1 COBYLA; 384 shots/call; 15 scenarios; 3 calls/episode.
**Outcome:** lower synthetic realized moisture stress is better. Negative paired differences favor the named policy over `never`.

| Policy | Mean stress ± SD | Paired Δ vs never (normal 95% CI) | Wins/ties/losses | Q completed/requested | Improvements | Shots | 2Q gate-shots | Forecast gap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| never | 3746.88 ± 842.61 | +0.00 [+0.00, +0.00] | 0/18/0 | 0/0 | 0 | 0 | 0 | 0.00 |
| always | 3746.88 ± 842.61 | +0.00 [+0.00, +0.00] | 0/18/0 | 38/38 | 0 | 14592 | 423936 | 0.00 |
| selective | 3746.88 ± 842.61 | +0.00 [+0.00, +0.00] | 0/18/0 | 13/13 | 0 | 4992 | 115200 | 0.00 |
| random | 3746.88 ± 842.61 | +0.00 [+0.00, +0.00] | 0/18/0 | 16/16 | 0 | 6144 | 170496 | 0.00 |
| extra_classical | 3746.88 ± 842.61 | +0.00 [+0.00, +0.00] | 0/18/0 | 0/0 | 0 | 0 | 0 | 0.00 |
| exact_classical | 3746.88 ± 842.61 | +0.00 [+0.00, +0.00] | 0/18/0 | 0/0 | 0 | 0 | 0 | 0.00 |

## Interpretation

These are paired comparisons across the same held-out synthetic weather episode IDs. The confidence intervals are descriptive normal approximations and do not correct for multiple policy comparisons. Quantum samples are classically rescored, and the classical incumbent is retained unless a sampled schedule scores better under the planner objective. `exact_classical` exhaustively enumerates each current feasible schedule set using the same forecast scenarios; it is an expensive, exact current-model reference, not a future-weather oracle. A completed Qiskit call therefore does not imply an improvement.

## Limits

- All weather and moisture values are synthetic and are not field validation.
- Aer is an ideal simulator and the result is not quantum hardware evidence.
- No policy showed benefit unless supported by the paired held-out outcomes; inspect wins, ties, losses and confidence intervals.
- Gate-shot totals are compiled two-qubit or all-gate instruction counts multiplied by shots, not runtime, energy, or hardware cost.
- Classical scenario counts are operation proxies; CPU time is reported separately and is machine-dependent.
- The exact_classical policy enumerates the same current forecast/scenario model at each decision and is an expensive classical reference, not a future-weather oracle.

Inputs and per-run outputs are preserved in the replicate directories. JSON metadata is derived from each actual run.
