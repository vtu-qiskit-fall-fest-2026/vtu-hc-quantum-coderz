# JalQ-R skeleton TODOs

Status: initial demo skeleton, not final research results.

## Before a recorded quantum demo

- [ ] Install full dependencies and run the complete supplied test suite.
- [ ] Execute and verify the Qiskit branch, bit ordering, feasibility and gate counts.
- [ ] Fix minimum shot allocation: 64 is accepted but three 32-shot pilots plus a final sample require at least 128.
- [ ] Invalidate stale plans after control changes or horizon advancement; require replanning before executing the next window.
- [ ] Display quantum execution errors distinctly from skipped calls.

## Research implementation

- [ ] Enforce a persistent quantum budget across forecast updates and account for every call.
- [ ] Implement budget-limited parameter optimization and a Dicke + XY baseline.
- [ ] Add repeated held-out trajectories, independent realized weather, and noisy simulations.
- [ ] Calibrate random invocation to a comparable call rate and strengthen the extra-classical baseline.
- [ ] Correct empirical CVaR fractional-tail weighting or label its approximation explicitly.
- [ ] Count all classical model evaluations, including greedy search and trigger features.
- [ ] Reconcile ranking-instability documentation with the implemented candidate-pair reversal metric.
- [ ] Ensure the offline evaluation UI evaluates the intended saved plan rather than silently rerunning it.
- [ ] Compare quality and total cost without claiming simulator timing is hardware timing.

## Submission

- [ ] Fill in actual team member names and GitHub handles in README.
- [ ] Add demo video and measured results with limitations.
- [ ] Confirm package versions from the team's tested environment.
- [ ] Review and merge the skeleton PR into main under the repository workflow.

