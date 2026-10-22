# JalQ-R development status

Status: synthetic research prototype. No field validation or quantum advantage is claimed.

## Before a recorded quantum demo

- [x] Install classical development dependencies and run the complete test suite.
- [x] Execute and verify the Qiskit Aer branch, bit ordering, feasibility, exact shot use and compiled gate counts.
- [x] Fix minimum shot allocation so pilots and validation use no more than the configured budget, including at 64 shots.
- [x] Invalidate stale plans after control changes or horizon advancement; require replanning before executing the next window.
- [x] Distinguish quantum execution errors, unavailable Qiskit, budget exhaustion, and skipped requests.

## Research implementation

- [x] Enforce rolling quantum call and shot budgets in benchmark episodes and the browser demo.
- [ ] Implement budget-limited parameter optimization and a Dicke + XY baseline.
- [x] Add repeated held-out trajectories with independent synthetic weather realizations and development-only random-call calibration.
- [x] Add an exact current-forecast classical baseline and retain the extended local-search baseline.
- [ ] Add noisy simulations and broader problem-size evaluation.
- [x] Label the empirical CVaR ceil-tail approximation explicitly.
- [x] Report planner score requests, cache hits, unique loss vectors, scenario-loss evaluations, QUBO builds and exact-enumeration candidate counts.
- [x] Document ranking instability as candidate-pair scenario-order reversals.
- [x] Keep the offline exact evaluator independent from online planning.
- [x] Compare policy quality, planner wall time and explicit quantum/classical workload proxies without treating simulator timing as hardware timing.

## Submission

- [ ] Fill in actual team member names and GitHub handles in README.
- [ ] Add demo video and include measured results with limitations; the current report is available in `results/quantum_repeated/aggregate_report.md`.
- [ ] Confirm package versions from the team's tested environment.
- [ ] Have the team review any proposed integration separately; this assignment's changes stay on `test`.

