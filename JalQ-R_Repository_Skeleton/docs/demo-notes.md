# JalQ-R | Functional Research Web Demo

**Risk-Aware, Resource-Budgeted Quantum Replanning for Water-Scarce Agriculture**

A FastAPI + responsive vanilla HTML/CSS/JavaScript website that includes:

- A **real numerical classical planner** with a 3-field × 4-window moisture model and exactly-K irrigation decisions.
- Synthetic rainfall/evaporation scenarios and a **risk-aware score** combining expected stress and empirical tail CVaR.
- A **heuristic invocation gate** using forecast shift, candidate regret proxy, and ranking instability.
- **Rolling-horizon replanning** that freezes completed irrigation events and uses updated observed moisture.
- An **optional actual Qiskit Aer** XY-QAOA candidate search (expected-stress quadratic surrogate, Pauli-Z RZ/RZZ costs, XXPlusYY XY mixing).
- A polished visual dashboard, forecasts controls, comparison table, and independently callable exact evaluator.

**Scientific boundaries:** The quantum phase circuit optimizes a quadratic *expected-stress surrogate*, not full CVaR; returned bitstrings are rescored classically with CVaR. Only synthetic data is used. Exact enumeration is isolated in `evaluate_exact_offline` and `/api/evaluate` and is never consulted by `/api/plan`. A heuristic trigger **does not establish** quantum advantage. The model uses **exactly K** equal-volume events, so no water-saving claim is made. A single comparison screen is not a statistically validated benchmark.

## Run locally (Windows PowerShell)

```powershell
cd JalQ_R_Web_Demo
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn server:app --reload
```

Open **http://127.0.0.1:8000** in your browser.

If Qiskit installation is temporarily unavailable, the working classical web demo can be used with:

```powershell
python -m pip install -r requirements-classical.txt
python -m uvicorn server:app --reload
```

In classical-only mode, requested quantum runs are explicitly labeled **unavailable**, with no made-up quantum metrics. Add `qiskit` and `qiskit-aer` before recording a demonstration of quantum execution.

## Test

```powershell
python -m pytest -q
```

Run the API with `uvicorn` then try `/api/health`, `/api/plan` (POST), and `/api/evaluate` (POST). The exact-evaluation endpoint is strictly for post-hoc analysis.

## Files

- `static/index.html`, `static/styles.css`, `static/app.js` — functioning responsive UI.
- `server.py` — FastAPI app and HTTP endpoints.
- `planner.py` — farm simulation, scenario risk, feasibility, classical search, and heuristic trigger.
- `quantum_engine.py` — Qiskit Aer XY-QAOA circuit and shot/gate counting, used only when available.
- `tests/` — deterministic model, constraint, surrogate-QUBO, API and rolling-horizon tests.

## Three-member team integration plan

1. **Farm/model engineer:** own `planner.py`, crop stress assumptions, update rules and validation tests.
2. **Quantum engineer:** own `quantum_engine.py`, test in a real Qiskit environment, add noise/performance and a fair Dicke-state/XY reference implementation.
3. **UI/evaluation engineer:** own `static/`, `server.py`, held-out experiments and presentation.

## Important incomplete research tasks

- Qiskit **cannot be executed** in the assistant's artifact-generation environment if packages are absent. The optional Qiskit circuit is included, but it must be installed and tested on your system before you claim it works.
- The Qiskit branch uses **three parameter trials** and p=1; it is a functional candidate generator, not a fully tuned or proven quantum optimizer.
- The comparison page runs one scenario. For credible results implement repeated **held-out forecast-update trajectories**, calibrate random invocation to JalQ-R's call rate, compare against equally budgeted classical search, and report uncertainty across seeds.
- Quantum cost reports shots, circuit evaluations and gate-weighted shots, which are proxies rather than exact hardware execution times.
- The classical baseline's objective evaluations should be included in an all-in computational budget before claiming savings over classical-only search.
- The simplified crop-moisture model is illustrative, not farm validated; there is no claim of yield benefit.
- The source does not include hosting/deployment credentials or a public server. Deploy only after local tests and team approval.

## Attribution & hackathon rules

The hackathon guidelines supplied to this chat require your team to do its own development during the event window, to credit references and open-source work, and to push only to the official assigned private repository. **Verify with the organizers whether AI-assisted code is permitted**. Have your team understand, independently test, revise and attribute any generated code before submission; this starter may not meet their originality rules without that approval.

References: IBM Quantum Qiskit SDK and Aer documentation; Ortikov & Ilhamov (2026) irrigation QAOA; do Carmo et al. (2025) warm-start QAOA/XY; Bucher et al. (2026) iterative warm-start XY.

