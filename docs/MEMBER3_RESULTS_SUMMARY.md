# JalQ-R — Research Results Summary (Member 3)

**Evidence type:** synthetic simulation using Qiskit Aer. These measurements were collected on the **earlier shared-weather farm model**, before Member 2's field-specific version was merged. They are **not** field validation, hardware runtime, or a quantum-advantage demonstration.

## A. Selective invocation benchmark: 24 held-out episodes

Source: `results/quantum_24/summary.csv` in the official repository.

| Policy | Mean realized stress ↓ | Quantum calls | Total Qiskit shots | Quantum improvements |
|---|---:|---:|---:|---:|
| Classical only | 2627.0578 | 0 | 0 | 0 |
| Always QAOA | 2627.0578 | 50 | 19200 | 0 |
| Selective QAOA | 2627.0578 | 6 | 2304 | 0 |
| Random gate | 2627.0578 | 4 | 1536 | 0 |
| Extra classical | 2627.0578 | 0 | 0 | 0 |

Selective invocation used **88% fewer total quantum shots than always-QAOA** in this experiment, with no change in mean realized moisture stress. Classical-only achieved the same quality using no Qiskit shots. Random invocation happened to use fewer shots than selective here; the observed held-out invocation counts were not exactly matched.

## B. Fixed-parameter vs COBYLA QAOA: 10 seed comparison

Source: `results/member1_compare_10.csv` in the official repository.

| Metric | Fixed-angle QAOA | COBYLA QAOA |
|---|---:|---:|
| Mean final sampled expected stress ↓ | 3864.13 | 2949.16 |
| Total shots across seeds | 3840 | 3840 |
| Total circuit evaluations | 40 | 90 |
| Seeds in which final sampled stress was lower | 0 / 10 | 10 / 10 |
| Improvement over classical incumbent | None reported | None reported |

COBYLA's mean final-sample expected stress was approximately **23.7% lower** than fixed-angle QAOA's in these 10 runs. This is **not** a 23.7% reduction in realized moisture stress, nor a hardware speedup. Fixed and COBYLA methods allocated their total shot budgets differently between tuning and final evaluation; additional independent repetitions and common evaluation shots would strengthen the comparison.

## C. Demonstration roadmap

1. Run `python -m pytest -q` and show tests passing.
2. Start `python -m uvicorn server:app --reload` and show the same single-page web app.
3. In **Farm Model**, enable field-specific weather; demonstrate changing W2 rainfall for East Field, then recalculate.
4. In **Overview**, show that three irrigation events remain allocated and the explanation reflects the selected policy.
5. In **Experiments**, display the two **CSV-backed, clearly historical** result groups.
6. Run `python member2_demo.py --quantum` for a current upgraded-farm COBYLA integration demo.
7. Explain that the exact offline optimum is used **only for post-decision evaluation**, and that the classical planner has been competitive on tested small instances.

## D. Limitations and future evaluation

- No actual irrigation field measurements or sensor calibration.
- Exactly K identical irrigation events; do **not** claim water savings.
- The existing website's timeline advance treats the selected forecast as a synthetic observed weather realization.
- Not yet a statistically powered field-specific-model benchmark. Re-run repeated, held-out field-specific weather episodes after this UI merge and archive the new CSVs separately.
- Compare quantum calls, shots, circuit depth, and classical model evaluation cost; shot count alone is not total energy, wall-clock time or hardware advantage.
- No quantum-produced solution improved the classical incumbent in the currently reported comparisons.

**Suggested research claim:** JalQ-R provides a tested hybrid irrigation scheduling prototype with constraint-preserving simulated QAOA search and a heuristic for reducing optional quantum invocations. Its experiments expose when classical scheduling is already sufficient, without claiming a quantum advantage.
