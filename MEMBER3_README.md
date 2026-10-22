# JalQ-R — Member 3: dashboard, controls and research evidence

This branch upgrades the existing single-page FastAPI demo **without replacing** Member 1's QAOA or Member 2's planning logic.

## Files to copy from the ZIP

| Path | Action |
|---|---|
| `server.py` | Replace: optional field-specific API inputs and `/api/research-results` |
| `static/index.html` | Replace: loads the Member 3 assets |
| `static/app.js` | Replace: invalidates stale schedules and observes per-field weather on timeline advance |
| `static/member3.js` | Add: 3×4 field inputs and live CSV-backed evidence sections |
| `static/member3.css` | Add: additional dashboard styling |
| `tests/test_dashboard.py` | Add alongside existing tests |
| `MEMBER3_README.md` | Add these instructions alongside the main README |
| `docs/MEMBER3_RESULTS_SUMMARY.md` | Add research interpretation and demo script |

Do **not** replace `planner.py`, `quantum_engine.py`, the existing tests, or the main `README.md`.

## Windows VS Code setup

```powershell
cd C:\Users\physi
git clone https://github.com/vtu-qiskit-fall-fest-2026/vtu-hc-quantum-coderz.git JalQ-R-member3
cd JalQ-R-member3
git switch -c dashboard-v2
code .
```

Copy the files to the paths above. Install dependencies if necessary:

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m uvicorn server:app --reload
```

Open `http://127.0.0.1:8000`. On the **Farm Model** view, enable the field-level model and change one field's rainfall, evaporation or window-specific moisture target. Recalculate. Return to **Overview** to see the actual plan and quantum execution state. On **Experiments**, see read-only bars generated from saved CSVs. This endpoint does **not** run a new benchmark.

## Required smoke tests

```powershell
python -m pytest -q
python member2_demo.py --quantum
python -c "from server import Payload,plan; p=Payload(policy='always'); x=plan(p); print(x['quantum']['status'], x['quantum'].get('optimizer'))"
```

Check that `tests/test_dashboard.py` passes; verify browser input changes are reflected in API responses. The last two commands require Qiskit to report `completed`.

## Important scientific distinction

- `/api/research-results` reads `results/quantum_24/summary.csv` (24-episode policy comparison) and `results/member1_compare_10.csv` (10-seed fixed vs COBYLA QAOA). Those files were generated **before** Member 2's field-specific model was merged.
- The data are not live experimental results for the upgraded farm. The website labels them as historical, exploratory, synthetic data.
- `final_mean_sampled_stress` is a distribution/sample metric, **not the final irrigation outcome**. Reported shot savings are relative to always-QAOA and **not overall speedup** or evidence quantum is better than classical-only.
- Experiments are only recalculated by explicitly running their Python scripts. No fake metrics or new results are fabricated by the UI.
- The existing `Advance one window` control uses the chosen forecast as a **synthetic realized observation** (no sensor stream) and now refuses to advance using an invalidated/stale plan. Past choices remain locked.
- The field-specific controls are added to the same single-page demo. The original shared-weather mode remains available.

## GitHub submission

After validating in the browser and tests:

```powershell
git add server.py static/index.html static/app.js static/member3.js static/member3.css tests/test_dashboard.py MEMBER3_README.md docs/MEMBER3_RESULTS_SUMMARY.md
git commit -m "feat: add field-aware dashboard and measured research results"
git push -u origin dashboard-v2
```

Open a Pull Request with base `main` and compare `dashboard-v2`; ask the team to review before merging. Do not add `__pycache__` files.

## Suggested demo (under 90 seconds)

1. Show **Overview**: exact-K schedule and honest classical/quantum status.
2. Show **Farm Model**: switch to field-level inputs, change one rainfall or target cell, recalculate.
3. Show **Experiments**: historical five-policy shot chart, then fixed-vs-COBYLA sampled stress chart, emphasizing they predate Member 2.
4. Show a fresh `member2_demo.py --quantum` run and passing tests.
5. Close with the limitation: classical alone matched final schedule quality in the historical benchmark; quantum search is an exploratory, resource-counted augmentation.

## Final submission reminders

Update the project-level `README.md` after merged tests, capturing the new code interface, current functionality, limitations, measured results and source CSV paths. Include an actual demo screenshot/video where required, and follow the event's attribution and AI-assistance policies.
