# JalQ-R — Quantum_coderz

**Selective, resource-budgeted QAOA for weather-driven irrigation replanning**

Documentation release: **23 October 2026**. This README is the starting point for the complete integrated project. Member contributions are already included; no separate patches are needed.

**Submission status:** code and saved experimental evidence are included. Add the actual demo video and presentation, complete the final laptop walkthrough, and obtain a clean full Python/QAOA verification before submission. The latest local full-suite attempt encountered a Qiskit Aer native-library error; earlier passing runs are historical. See the [verification record](docs/VERIFICATION.md).

VTU-QFF-HC-0167 · Online · Quantum Applications for Climate Change & Sustainability

**Primary research question:** Can a forecast-aware selective invocation policy reduce QAOA execution (calls and circuit shots) relative to always-running QAOA, without worsening selected irrigation schedules on held-out synthetic episodes?

**Working research prototype:** JalQ-R implements classical-first, risk-aware irrigation scheduling and optional Qiskit Aer p=1 XY-QAOA with COBYLA, bounded shots per invocation, and a demo-wide rolling call/shot budget. We evaluate **selective QAOA versus always-run QAOA** as the primary quantum resource-efficiency comparison. Classical-only, random invocation, extra-classical search and an explicit exact reference remain available for correctness and honest practical evaluation. No quantum advantage, quantum speedup, real-farm benefit or water savings have been established.

**Demo video:** **TO ADD BEFORE SUBMISSION** — replace this line with your actual YouTube demonstration URL. No video is provided or claimed in this package.

**Updated Hybrid experiments screenshot:** Captured from this updated HTML/CSS in a local headless browser with real FastAPI TestClient responses reading the saved benchmark CSVs. This is **not** a Qiskit execution screenshot; the team should also capture the completed QAOA demo on its Windows laptop.

![Finalized Hybrid experiments dashboard showing CSV-backed selective versus always-run QAOA evidence](docs/screenshots/hybrid_experiments.png)

[View the full experiments page](docs/screenshots/hybrid_experiments_full.png). [Historical pre-Hybrid overview screenshot](docs/screenshots/overview.png) is preserved only as an archive.

- [Primary research conclusion and figure guide](docs/FINAL_SUBMISSION_GUIDE.md)
- [Hybrid results](results/hybrid_field/aggregate_report.md)
- [Verification report](docs/VERIFICATION.md)
- [How to upload this package](UPLOAD_TO_REPOSITORY.md)
- [Algorithm and budget details](docs/HYBRID_DESIGN.md)
- [Historical results and provenance](results/README.md)
- [Reproduce the experiments](docs/experiments.md)

### Team contribution summaries

These summaries describe the integrated contributions. Follow this README for installation; there are no separate member patches to apply.

- [Member 1: quantum optimizer](docs/contributions/member1-quantum.md)
- [Member 2: farm model and planner](docs/contributions/member2-planner.md)
- [Member 3: dashboard](docs/contributions/member3-dashboard.md)

## Team

| Name | GitHub | Role |
|---|---|---|
| Shylan Kamesh S | shylankamesh | Team Lead |
| Sai Santhosh T | tsaisanth29-ece | Developer |
| Derin Godson | Derin-Godson | Developer |

## Problem and approach

Allocate exactly K equal-volume irrigation events across eligible field-time slots under uncertain rainfall and evaporation, and replan as forecasts change without altering already executed decisions. The **scientific contribution under evaluation** is an *invocation policy*: choose when to spend QAOA calls and shots instead of invoking the same quantum search at every planning opportunity. It is **not** a claim that the quantum planner is faster or better than classical-only scheduling.

The planner generates greedy and local-search schedules, scores their mean stress and fractional-tail empirical CVaR, and applies a forecast-change/ranking-instability gate. If requested and budget remains, fixed-weight XY-QAOA samples candidates using an expected-stress quadratic phase Hamiltonian. COBYLA tunes two angles within the shot allocation. Full risk scoring remains classical, and a quantum candidate is accepted only if it improves the incumbent.

The dashboard supports shared or field-specific weather, changing crop targets, saved-schedule exact evaluation, budget persistence, and separate comparison accounting. It shows the **best measured quantum candidate risk** independently from the **classical incumbent risk** when an actual QAOA call succeeds; the final schedule may still be classical. An exact classical policy is an explicit small-instance reference; other online policies never consult enumeration.

## Run on Windows

Use a Python version supported by the installed Qiskit/Aer wheels (the recorded Windows environment used Python 3.13). Node.js is also needed for the JavaScript regression checks. Open a terminal in this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. On macOS/Linux use `python3 -m venv .venv` and `.venv/bin/python` for subsequent commands. Classical-only installation uses `requirements-classical.txt`; requested quantum search then reports unavailable.

For tests:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q tests --basetemp=pytest_temp
node tests/frontend_regression.cjs
node tests/research_summary_regression.cjs
.\.venv\Scripts\python.exe member2_demo.py --quantum
```

The tested package versions are recorded in [requirements-tested.txt](requirements-tested.txt). This records the tested environment; the ordinary requirements retain compatible ranges.

## Fresh hybrid measurements — 22 October 2026

Three independent seed blocks, four development and six held-out episodes each: **18 held-out episodes per policy**, field-specific weather and changing targets, ideal Aer, 384 shots/call, at most three calls/episode.

| Policy | Mean realized stress ↓ | Completed quantum calls | Shots | Quantum improvements |
|---|---:|---:|---:|---:|
| Classical-only | 3746.88 | 0 | 0 | 0 |
| Always QAOA | 3746.88 | 38 | 14592 | 0 |
| Selective QAOA | 3746.88 | 13 | 4992 | 0 |
| Random invocation | 3746.88 | 16 | 6144 | 0 |
| Extra classical | 3746.88 | 0 | 0 | 0 |
| Exact classical | 3746.88 | 0 | 0 | 0 |

**Primary finding:** Selective QAOA used **65.8% fewer quantum circuit shots** (4,992 versus 14,592) and **25 fewer completed QAOA calls** (13 versus 38) than always-run QAOA over the same 18 held-out synthetic episodes. Both policies had the same **observed mean realized moisture stress** (3,746.88). The selected schedule retains the risk-scored classical incumbent unless a measured quantum candidate improves it, so *equal final quality does not prove that QAOA alone produced the same quality*. No tested quantum sample improved the classical incumbent.

**Essential comparison boundary:** Classical-only achieved the same final stress with **zero** quantum shots. The 65.8% refers **only** to *selective versus always-run QAOA*, not to savings versus classical-only, nor to CPU time, energy, water use or quantum speedup. Random invocation was calibrated on development episodes, but its observed held-out call rate (16 calls) does not exactly match selective's (13); this does not prove the heuristic is better than a matched-rate random trigger.

Historical 24-episode and 90-episode studies used earlier shared-weather/fixed-angle implementations. The historical optimizer comparison measures final sampled expected stress, not crop outcomes. They are preserved separately and must not be presented as hybrid measurements.

## Demo sequence

1. Start with Reset demo and inspect the feasible classical schedule.
2. Open Farm Model, enable field-level inputs and change a future rainfall or evaporation value.
3. Recalculate. Choose Always QAOA to demonstrate actual Aer execution, show best measured quantum candidate risk versus the classical incumbent, and inspect budget consumption; selective invocation may legitimately skip it.
4. Advance one window, observe completed cells lock, then recalculate.
5. In Experiments, read the **CSV-backed primary selective-versus-always QAOA result** first; inspect fresh and historical results separately. Evaluate the saved schedule without rerunning quantum search.
6. Explain that comparisons use separate one-call allocations per policy; their cumulative usage is visible above the dashboard.

## Scope and limitations

- Three fields and four windows; synthetic linear moisture dynamics with squared target deviation. This penalizes both over- and under-target moisture; it is not a validated agronomic loss function.
- Exactly K equal-size events means water use is fixed; this prototype does not demonstrate water savings.
- p=1, ideal simulator, shot-noise-affected sampling/parameter search; no hardware-noise study, Dicke-state comparison, or published-method superiority claim.
- Planning budget is state carried by this single-browser demo and validated by the API. It is not a secure multi-user/server-global quota. Reloading restores usage; Reset starts a new demo. Use a single tab.
- The dashboard advances using forecasts as synthetic observations. The experiment runner independently reveals simulated realized weather after each decision.
- Shot reduction occurs because the selective policy *skips QAOA invocations*, not because it adaptively reduces the shots within each successful call. Work counters are model-operation proxies; timings are local machine measurements, not hardware runtime or energy.
- The selected final schedule's equality across policies is protected by the classical fallback and does not establish standalone QAOA solution-quality parity. A computation-matched random-policy and stronger classical/quantum baselines remain future work.

## Files

`planner.py`: farm model, CVaR, candidates, trigger, budgets, exact reference.
`quantum_engine.py`: COBYLA and fixed-angle XY-QAOA, shot and gate accounting.
`server.py`: API, saved-plan evaluator, CSV-backed evidence.
`static/`: dashboard. `tests/`: numerical/API/quantum/frontend regressions.
`experiments.py`: six-policy rolling-horizon benchmark; `tools/`: run aggregation.
`results/`: explicitly separated fresh and historical measurements.
`docs/FINAL_SUBMISSION_GUIDE.md`: demo narrative, numbers, and submission checklist; no invented video or portal confirmation.

## References and attribution

- [Irrigation QAOA formulation](https://arxiv.org/abs/2607.13374)
- [Warm-start XY mixers](https://arxiv.org/abs/2504.19934)
- [Iterative warm-start XY mixers](https://arxiv.org/abs/2604.02083)
- [Initial-state/mixer alignment](https://www.nature.com/articles/s41534-023-00787-5)

Quantum components build on prior work. Novelty is not certified. Team sources and AI-assisted integration are recorded in [integration sources](docs/INTEGRATION_SOURCES.md). The team should understand and explain all submitted code. MIT license retained in [LICENSE](LICENSE).
