# JalQ-R — Member 2 farm model upgrade

This patch is based on the **main** branch after Member 1's COBYLA PR #1 (`9c5c0ef`).

## What's new

- Separate 3×4 rainfall and evaporation forecasts for each field.
- Separate 3×4 crop-moisture target trajectories for each field.
- Optional separate 3×4 previous rainfall forecast for the selective invocation gate.
- Simulated scenario arrays of shape `(scenario_count, 3, 4)`.
- Accurate fractional-tail empirical CVaR for the risk-aware candidate score.
- Tests for legacy compatibility, rolling-horizon executed decisions, CVaR, QUBO/Ising identity and the merged Member 1 Qiskit engine.
- No changes to `quantum_engine.py`, `server.py`, `experiments.py`, or the frontend.

## Installation using VS Code (Windows PowerShell)

**Work in a fresh clone of the main repository, NOT Member 1's old `quantum-optimization` folder.**

If the `JalQ-R-main` clone already exists:

```powershell
cd C:\Users\physi\JalQ-R-main
git switch main
git pull origin main
git switch -c farm-model-v2
```

If the folder does **not** exist, create it first:

```powershell
cd C:\Users\physi
git clone https://github.com/vtu-qiskit-fall-fest-2026/vtu-hc-quantum-coderz.git JalQ-R-main
cd JalQ-R-main
git switch -c farm-model-v2
```

Copy the contents of this patch into the repository, preserving folders:

| ZIP file | Action |
|---|---|
| `planner.py` | **REPLACE** current `planner.py` |
| `tests/test_farm_v2.py` | **ADD** under existing `tests/` |
| `member2_demo.py` | **ADD** to project root |
| `MEMBER2_README.md` | **ADD** to project root |

Do **not** replace the `tests/` folder or delete existing tests.

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m pytest -q
python member2_demo.py
python member2_demo.py --quantum
```

The quantum demo requires Qiskit Aer; it is expected to print `Quantum status: completed` with 128 shots on the user's working Qiskit setup. Do not merge if tests or this quantum run fail.

## Data contract: optional `FarmRequest` properties

```python
rain_by_field: list[list[float]] | None          # 3 rows: fields; 4 columns: windows
evaporation_by_field: list[list[float]] | None   # (3,4)
target_by_window: list[list[float]] | None       # (3,4)
previous_rain_by_field: list[list[float]] | None # (3,4); for trigger gate
```

The old `rain`, `evaporation`, `target` lists are still required and serve as fallbacks.
When optional weather matrices are absent, **the original shared-weather scenario draws are preserved**; legacy losses and quadratics match the previous implementation for the same seed. For fractional CVaR tails (e.g. 7 scenarios, alpha=0.8), **risk values deliberately change** because the CVaR approximation is corrected. Save new results with new filenames: previous CSVs describe the original model.

An explicit weather matrix receives field-specific random perturbations. An omitted matrix retains the shared original noise model. These are simulated forecasts, not field measurements.

**Important:** `server.py` has not been modified to accept the new optional matrices, and `experiments.py` still generates legacy uniform weather. The demonstration and tests call `FarmRequest` directly; Member 3 must add server/API inputs and upgrade the experiment simulator if a new-model end-to-end benchmark is desired. Until then, the existing website and benchmarks keep using legacy mode.

## The quantum contract is preserved

- `Planner.expected_qubo()` still returns `(constant, linear_coeffs, upper_triangular_pair_coeffs)`.
- `Planner.loss_vector(bits)` still returns `(scenario_losses, moisture_traces)`.
- `Planner.score(bits)['risk']` still implements expected loss / CVaR mixture.
- `Planner.feasible()` and `Planner.slots` keep the same meaning and binary bit order.
- For any binary vector x, `expected_loss(x) ≈ c + a @ x + x @ b @ x`.
- The quantum Hamiltonian still uses **expected quadratic loss only**; CVaR is evaluated classically on sampled candidates.
- Offline enumeration (`evaluate_exact_offline`) stays outside `decide()`.
- The number of fields (3) and windows (4) remains unchanged.

## GitHub submission

After successful testing:

```powershell
git branch --show-current
git add planner.py tests/test_farm_v2.py member2_demo.py MEMBER2_README.md
git commit -m "feat: implement field-specific irrigation model and CVaR"
git push -u origin farm-model-v2
```

Open a Pull Request: base `main` ← compare `farm-model-v2`.
Before merging, run `python -m pytest -q` and `python member2_demo.py --quantum` in the same branch (Qiskit required). 

## Research boundaries

This is an idealized 3-field, 4-window moisture-stress model, NOT a validated agronomic model. Events have identical irrigation gain and the fixed-K constraint cannot substantiate claims of lower water consumption. Distinct field-level weather is illustrative. Classical advantage or quantum advantage has not been established. More diverse scenarios can be scientifically helpful, but a nonzero optimality gap is not guaranteed.
