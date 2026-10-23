<div align="center">

# JalQ-R | Quantum_coderz

**VTU-QFF-HC-0167** &nbsp;|&nbsp; Tier: **Online**

</div>

---

<div align="center">

| | |
| :--- | :--- |
| **Team** | Quantum_coderz |
| **Team ID** | VTU-QFF-HC-0167 |
| **Tier** | Online |
| **Repository** | [vtu-hc-quantum-coderz](https://github.com/vtu-qiskit-fall-fest-2026/vtu-hc-quantum-coderz.git) |
| **Organisation** | [vtu-qiskit-fall-fest-2026](https://github.com/vtu-qiskit-fall-fest-2026) |
| **Event** | VTU-QFF Hackathon — VTU-Qiskit Fall Fest 2026 |

</div>

---

> **Research prototype.** Numerical classical planning and an optional Qiskit Aer candidate generator. Classical computation remains essential; no bypass, replacement, or superiority over classical algorithms is claimed. See [TODO.md](TODO.md) for remaining work and [demo notes](docs/demo-notes.md) for current demo guidance.

## 📌 Table of Contents

- [Team Members](#-team-members-github-ids)
- [Problem Statement](#-problem-statement)
- [Proposed Solution](#-proposed-solution)
- [Approach & Architecture](#-approach--architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [How to Run](#-how-to-run)
- [How to Push Code](#-how-to-push-code)
- [Submission Checklist](#-submission-checklist)
- [Resources](#-resources)
- [License](#-license)

---

## 👥 Team Members (GitHub IDs)

> Members are added to this repository as **collaborators** and must accept the
> GitHub invitation before they can push. Add your GitHub username below.

| # | Name | GitHub Username | Role |
| :-- | :--- | :--- | :--- |
| 1 | Shylan Kamesh S | shylankamesh | _Team Lead_ |
| 2 | Sai Santhosh T | tsaisanth29-ece | _Developer_ |
| 3 | Derin Godson | Derin-Godson | _Developer_ |

<!--
Optional: add a plain list instead of the table above.
- @username1
- @username2
-->

---

## ❓ Problem Statement

**Problem:** Allocate a fixed quota of irrigation events across eligible field-time slots under uncertain weather. Investigate whether selective quantum replanning can maintain schedule quality while reducing quantum execution cost.

**Why it matters:** Forecast changes can make an existing plan less suitable; additional optimization must justify its computational cost. The synthetic model optimizes timing at exactly K equal-size events and does not demonstrate water savings.

**Track / Category:** Online · Quantum Applications for Climate Change & Sustainability

---

## 💡 Proposed Solution

**Solution:** JalQ-R generates feasible classical schedules, evaluates expected moisture stress and empirical tail risk, and uses a heuristic forecast-response gate to request optional quantum candidate search. It retains the best verified classical or quantum candidate.

**Key idea:** Selective invocation of fixed-weight XY-QAOA with explicit classical fallback.

**Current status:** The integrated hybrid supports field-specific rainfall, evaporation and crop targets, fractional-tail empirical CVaR scoring, frozen completed decisions, and rolling call/shot budgets. Its optional p=1 XY-QAOA search uses COBYLA tuning with ideal Qiskit Aer simulation. Full risk scoring and feasibility checks remain classical; a quantum candidate is accepted only if it improves the classical incumbent.

The current field-specific study includes **18 held-out synthetic episodes per policy** across three seed blocks. Selective QAOA used **13 calls / 4,992 shots**, compared with **38 calls / 14,592 shots** for always-run QAOA: **65.8% fewer shots relative to always-run QAOA only**. All six policies achieved the same observed mean realized stress, approximately **3,746.88**. No quantum candidate improved the classical incumbent; classical-only achieved the same observed outcome with zero quantum shots. These results do not establish superiority over classical algorithms, quantum advantage, hardware speedup, or real-farm water savings. See the [aggregate report](results/hybrid_field/aggregate_report.md) and [run metadata](results/hybrid_field/aggregate_metadata.json). Earlier shared-weather studies are historical and are documented separately in [results provenance](results/README.md).

**Live website:** [Open JalQ-R](https://jalq-r-605775397403.asia-south1.run.app/)

**Presentation:** [Download JalQ-R PowerPoint](VTU-QFF-HC-0167_JalQ-R_final.pptx)

**Recorded demo:** [Watch the demonstration on YouTube](https://youtu.be/ayLlw7HNc8Q)

![Hybrid experiment results](docs/screenshots/hybrid_experiments.png)

This screenshot shows saved synthetic benchmark results, not a quantum-hardware execution. Noise studies, larger instances and farm validation remain future work.

---

## 🧩 Approach & Architecture

```mermaid
flowchart LR
    A[Farm and forecast inputs] --> B[Feasible classical candidates]
    B --> C[Heuristic invocation gate]
    C --> D[Optional Qiskit Aer search]
    B --> E[Feasibility and risk scoring]
    D --> E
    E --> F[Verified schedule and metrics]
```

1. **Input:** Three fields, four windows, synthetic forecasts, eligibility, moisture and remaining quota.
2. **Classical core:** Greedy and bounded swap-based local search with risk-aware scoring.
3. **Quantum core:** Expected-stress QUBO mapped to RZ/RZZ gates and XXPlusYY mixing, with COBYLA parameter tuning. Full CVaR is not encoded in the phase circuit.
4. **Verification:** Check exact quota and rescore candidates classically. Missing Qiskit is reported as unavailable.
5. **Evaluation:** A saved-schedule evaluator computes an exact current-forecast reference without rerunning QAOA. An explicit exact-classical policy is also available as a reference; other online policies do not use enumeration. Live comparisons are illustrative; saved multi-episode results are reported separately.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| Language | Python 3.11+ |
| API | FastAPI, Uvicorn, Pydantic |
| Numerics | NumPy, SciPy (COBYLA) |
| Quantum | Qiskit, Qiskit Aer (optional for classical demo) |
| Frontend | HTML, CSS, vanilla JavaScript |
| Tests | pytest, FastAPI TestClient, HTTPX, Node.js regression checks |
| Version control | Git + GitHub |

---

## 📁 Project Structure

```text
vtu-hc-quantum-coderz/
├── README.md
├── TODO.md
├── requirements.txt
├── requirements-classical.txt
├── requirements-dev.txt
├── planner.py
├── quantum_engine.py
├── server.py
├── start_windows.bat
├── start_mac_linux.sh
├── static/                 # HTML, CSS, JavaScript
├── tests/test_planner.py
├── experiments.py          # Rolling-horizon benchmark
├── results/                # Fresh and historical measurements
├── tools/                  # Benchmark aggregation
└── docs/                   # Design, verification, contributions and demo guidance
```

---

## 🚀 How to Run

Clone the submitted main branch, then create a virtual environment. Install the full requirements to demonstrate Qiskit Aer:

```powershell
git clone --branch main --single-branch https://github.com/vtu-qiskit-fall-fest-2026/vtu-hc-quantum-coderz.git
cd vtu-hc-quantum-coderz
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn server:app --reload
```

Open http://127.0.0.1:8000. On macOS/Linux use `python3 -m venv .venv` and `source .venv/bin/activate`.

For a classical-only installation, use `requirements-classical.txt` instead. Requested quantum runs report unavailable when Qiskit/Aer are absent. The browser stores demo state and remaining budget locally; choose **Reset demo** to restore the sample scenario and initial budget.

### Tests

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q tests --basetemp=pytest_temp
node tests/frontend_regression.cjs
node tests/research_summary_regression.cjs
python member2_demo.py --quantum
```

Development requirements include the classical web dependencies and test tools; install `requirements.txt` as well to exercise Qiskit. The canonical test suite is under `tests/`.

### Validation of this initial upload

This heading is retained from the supplied format. The following describes the reviewed integrated version, not the old skeleton:

- Both frontend regression scripts passed on the reviewed main-branch code.
- A targeted classical/model check passed 21 tests; this was not the full suite.
- Actual QAOA completed on the deployed site with 384 shots across 9 circuits. The remaining budget decreased correctly.
- Saved-schedule exact evaluation returned a zero gap in the tested scenario without additional quantum shots.
- The deployed benchmark page displayed the saved 65.8% shot reduction and correct classical comparison. Narrow-width horizontal overflow remains a known UI issue.
- A successful full Python test-suite run on the final checkout still needs confirmation. Historical passing runs and a later review-environment Aer native-library failure are recorded in [verification](docs/VERIFICATION.md).

No quantum advantage or superiority over classical-only planning is established.


---

## 🔁 How to Push Code

> Full walkthrough: **[Git & Collaboration Handbook](../vtu-hc-guide-git-and-collaboration)** — collaboration
> workflow, branches, pull requests, reviews and conflict resolution.

### Configure Git (first time only)

```bash
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
```

### Everyday workflow

```bash
# Start from the current submitted branch
git checkout main
git pull --ff-only origin main
git checkout -b docs/jalq-readme-update

# Review and commit the README update
git add README.md
git commit -m "docs: update JalQ-R within the supplied README format"

# Push the review branch
git push -u origin docs/jalq-readme-update
```

Open a pull request into `main` and review it with your team before merging. This describes the current repository workflow; follow any newer organizer instructions.

### Commit message convention

| Prefix | Meaning |
| :--- | :--- |
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `test:` | Adding or fixing tests |
| `refactor:` | Code restructure, no behaviour change |
| `chore:` | Build/config/dependency changes |

### Useful commands

```bash
git status              # what changed
git log --oneline -10   # recent commits
git diff                # review changes before committing
git stash               # shelve changes temporarily
git pull --ff-only origin main  # update main while on main
```

### Collaborating on the same repo

- **Use a review branch** and inspect the diff before merging into `main`.
- **Pull before you push** to avoid rejected commits.
- **Commit often** with clear messages.
- **Resolve conflicts** locally: `git pull --rebase`, fix the files, then `git add` + `git rebase --continue`.
- **Ask for a review** before merging — a second pair of eyes catches bugs fast.

---

## ✅ Submission Checklist

- [ ] Assigned event repository used; visibility follows organizer instructions
- [ ] All team members added as **collaborators** and invitations accepted
- [x] `README.md` updated with project details, problem statement and solution
- [x] Team members listed under [Team Members](#-team-members-github-ids)
- [ ] `requirements.txt` committed and project runs from a clean clone
- [x] Code pushed to `main`; reviewed files and frontend checks verified there
- [ ] Notebooks committed with **cleared outputs** (or use `nbstrip`)
- [x] `README` includes a demo screenshot / video link (screenshot included; recorded video still pending)
- [ ] Short project summary submitted on the hackathon portal

---

## 📚 Resources

| Resource | Link |
| :--- | :--- |
| 🔁 Git & collaboration handbook | [Git & Collaboration Handbook](../vtu-hc-guide-git-and-collaboration) |
| ❓ Problem statements, solutions & terms | [Problem Statements, Solutions & Terms](../vtu-hc-guide-problem-and-solution) |
| 📄 README writing guide | [README Guide & Template](../vtu-hc-guide-readme-template) |
| ⚛️ Qiskit documentation | https://docs.quantum.ibm.com/ |
| ⚛️ Qiskit Runtime & primitives | https://quantum.cloud.ibm.com/docs/ |
| 🧪 Qiskit Aer simulator | https://docs.quantum.ibm.com/guides/simulator |
| 💻 IBM Quantum Platform | https://quantum.cloud.ibm.com/ |
| 🎓 Qiskit textbook | https://qiskit.qotlabs.org/learning/ |
| 📋 GitHub Docs | https://docs.github.com/ |

---

### Research references and attribution

- [Irrigation QAOA formulation](https://arxiv.org/abs/2607.13374)
- [Warm-start QAOA with XY mixers](https://arxiv.org/abs/2504.19934)
- [Iterative warm-start XY mixers](https://arxiv.org/abs/2604.02083)
- [Initial-state/mixer alignment](https://www.nature.com/articles/s41534-023-00787-5)

The current project integrates the team's quantum, farm-model and dashboard contributions. Source provenance is recorded in [integration sources](docs/INTEGRATION_SOURCES.md). Code preparation, integration and documentation used AI assistance; the team must understand, test, and attribute its submission according to event rules. Research components are prior art; originality and efficiency are not certified.

## 📄 License

Released under the [MIT License](LICENSE). See `LICENSE` for details.

---

<div align="center">

**Quantum_coderz** · Team ID `VTU-QFF-HC-0167` · Tier `Online`
· Built with ⚛️ Qiskit for the VTU-QFF Hackathon

[⬆ Back to Top](#jalq-r--quantum_coderz)

</div>

