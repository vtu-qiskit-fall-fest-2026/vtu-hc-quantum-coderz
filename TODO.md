# JalQ-R development status

Status: synthetic research prototype. No field validation or quantum advantage is claimed.

## Before a recorded quantum demo

- [x] Install classical development dependencies and run the complete test suite.
- [ ] Execute and verify the Qiskit branch, bit ordering, feasibility and gate counts.
- [x] Fix minimum shot allocation so pilots and validation use no more than the configured budget, including at 64 shots.
- [x] Invalidate stale plans after control changes or horizon advancement; require replanning before executing the next window.
- [x] Distinguish quantum execution errors, unavailable Qiskit, budget exhaustion, and skipped requests.

## Research implementation

- [x] Enforce rolling quantum call and shot budgets in benchmark episodes and the browser demo.
- [ ] Implement budget-limited parameter optimization and a Dicke + XY baseline.
- [ ] Add repeated held-out trajectories, independent realized weather, and noisy simulations.
- [ ] Calibrate random invocation to a comparable call rate and strengthen the extra-classical baseline.
- [x] Label the empirical CVaR ceil-tail approximation explicitly.
- [ ] Count all classical model evaluations, including greedy search and trigger features.
- [x] Document ranking instability as candidate-pair scenario-order reversals.
- [x] Keep the offline exact evaluator independent from online planning.
- [ ] Compare quality and total cost without claiming simulator timing is hardware timing.

## Submission

- [ ] Fill in actual team member names and GitHub handles in README.
- [ ] Add demo video and measured results with limitations.
- [ ] Confirm package versions from the team's tested environment.
- [ ] Have the team review any proposed integration separately; this assignment's changes stay on `test`.

