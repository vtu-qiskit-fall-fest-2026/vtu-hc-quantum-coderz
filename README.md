# Quantum_coderz

| | |
| --- | --- |
| **Team** | Quantum_coderz |
| **Team ID** | VTU-QFF-HC-0167 |
| **Tier** | Online |
| **Repository** | vtu-hc-quantum-coderz |
| **Event** | VTU-QFF Hackathon (VTU-Qiskit Fall Fest 2026) |

## Team members (GitHub IDs)

- Shylan Kamesh S — `shylankamesh` — Team Lead
- Sai Santhosh T — `tsaisanth29-ece` — Developer
- Derin Godson — `Derin-Godson` — Developer

## Project

**JalQ-R: Risk-Aware, Resource-Budgeted Quantum Replanning for Water-Scarce Agriculture**

JalQ-R is a research prototype for scheduling a fixed number of irrigation events under uncertain rainfall and evaporation. It models three fields and four planning windows, supports field-specific forecasts and crop targets, and freezes completed decisions during replanning. All farm inputs and evaluation episodes are synthetic.

The planner first creates a feasible classical schedule and scores candidates using expected moisture stress and empirical CVaR tail risk. An optional Qiskit Aer p=1 XY-QAOA search, tuned with COBYLA under a shot budget, proposes additional candidates. Each candidate is checked and scored classically; it replaces the classical incumbent only if it improves that score. Otherwise, the classical schedule is retained. Classical computation remains essential throughout this process.

Our research question is whether selective invocation can reduce quantum calls and circuit shots compared with always invoking QAOA, while maintaining the observed quality of the final selected schedules. The project does not claim to replace, bypass, or outperform classical algorithms. It does not demonstrate quantum advantage or quantum speedup.

The dashboard provides planning, field-level weather controls, rolling call/shot accounting, saved-schedule exact evaluation, and saved benchmark results. The budget is browser-carried demo state, not a secure server-wide quota. Qiskit Aer simulates quantum circuits; these results are not quantum-hardware measurements.

In the saved field-specific study, three seed blocks provided **18 held-out synthetic episodes per policy**:

- Always-run QAOA: **38 calls, 14,592 shots**.
- Selective QAOA: **13 calls, 4,992 shots**.
- Selective invocation used **65.8% fewer shots than always-run QAOA**.
- Every tested policy had the same observed mean realized stress, approximately **3,746.88**.
- **No reported quantum candidate improved the classical incumbent. Classical-only achieved the same observed outcome with zero quantum shots.**

These results support a limited observation about quantum resource usage relative to always-run QAOA. They do not establish superiority over classical-only planning, general equivalence of solution quality, or that the invocation rule outperforms a matched-budget alternative. Exactly K equal-volume irrigation events fixes water use; no real-farm water savings or yield benefit is demonstrated.

**Live website:** [Open JalQ-R](https://jalq-r-605775397403.asia-south1.run.app/)

**Demo/video:** Not yet provided. The live website is available above; the required recorded-demo link must be added before final submission.

Supporting documentation: [design](docs/HYBRID_DESIGN.md), [benchmark results](results/hybrid_field/aggregate_report.md), [reproduce experiments](docs/experiments.md), [results provenance](results/README.md), and [verification record](docs/VERIFICATION.md).

Team contributions: [quantum optimizer](docs/contributions/member1-quantum.md), [farm model and planner](docs/contributions/member2-planner.md), and [dashboard](docs/contributions/member3-dashboard.md). Source provenance and AI-assisted integration are recorded in [integration sources](docs/INTEGRATION_SOURCES.md). The project retains its [MIT license](LICENSE). Prior-work references and implementation details are supporting material; no claim of first-of-its-kind novelty is made.

## Tracks / Problem Statement

**Track 06 — Quantum Applications for Climate Change & Sustainability.**

Allocate exactly K equal-volume irrigation events across eligible field-time slots under uncertain synthetic rainfall and evaporation. Replan as forecasts change without rewriting completed decisions, while accounting for any optional quantum-search calls and shots. Compare selective and always-run QAOA with classical-only and other reference policies, reporting both schedule quality and resource use.

## How to run

Clone the assigned repository and open its root folder:

```bash
git clone https://github.com/vtu-qiskit-fall-fest-2026/vtu-hc-quantum-coderz.git
cd vtu-hc-quantum-coderz
```

Use a Python version compatible with the installed Qiskit/Aer wheels. The recorded Windows environment used Python 3.13. Node.js is needed for the JavaScript regression checks.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Keep the server terminal running. On macOS/Linux, create the environment with `python3 -m venv .venv` and use `.venv/bin/python` instead of the Windows executable path.

Run checks from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q tests --basetemp=pytest_temp
node tests/frontend_regression.cjs
node tests/research_summary_regression.cjs
.\.venv\Scripts\python.exe member2_demo.py --quantum
```

The latest reviewed frontend checks passed, and actual QAOA execution and saved-schedule evaluation succeeded in the deployed website check. This does not substitute for a successful full test-suite run on the final checkout. Earlier full-suite attempts in the review environment encountered an Aer native-library error; see the verification record for historical results and limits.

For a demo, choose **Always run QAOA** and recalculate to demonstrate actual circuit execution; selective mode may legitimately skip it. Change a future field forecast, recalculate, advance one window, and inspect locked past decisions. Experiments shows saved measurements, not a newly executed benchmark. Reset starts a new demo budget. A classical-only installation can use `requirements-classical.txt`; quantum requests then report unavailable.

## Submission checklist

- [ ] Repository created and private
- [x] README updated with project details
- [ ] Team members added as collaborators
- [x] Code pushed to `main`
- [ ] Demo/video link added

Repository creation and the code on main were verified. Current repository privacy and collaborator permissions have not been verified in this review; the team should confirm them before checking those items. The recorded-demo link, final presentation/portal steps, and complete local verification remain pending.
