# JalQ-R — final submission presentation and verification

**Team:** Quantum_coderz · **Team ID:** VTU-QFF-HC-0167 · **Track:** Quantum Applications for Climate Change & Sustainability

## Research contribution

**Primary question:** Can a forecast-aware **selective QAOA invocation** policy reduce QAOA calls and circuit shots relative to an **always-run QAOA** policy, while maintaining selected irrigation schedule quality under synthetic weather uncertainty?

**What changes relative to always QAOA:** When a replanning event fails the heuristic trigger, the system does not run quantum circuits. **The per-invocation shot allocation does not dynamically shrink** just because the gate is selective. QAOA is p=1, with COBYLA and a fixed-weight XY mixer, simulated in Qiskit Aer. Classical search makes an incumbent; all measured QAOA candidates are classically validated before they can replace it.

## Actual measured result (CSV-backed)

**Source:** `results/hybrid_field/aggregate_summary.csv` and its per-replicate metadata; three independent blocks with six held-out synthetic episodes each, 384 shots per successful invocation, three QAOA calls maximum per episode in the experiment runner. In total, 18 held-out episodes **per policy**.

| Policy | QAOA calls completed | Circuit shots | Mean realized synthetic moisture stress | Quantum improvement over classical incumbent |
|---|---:|---:|---:|---:|
| Always-run QAOA | 38 | 14,592 | 3,746.88 | 0 |
| **Selective QAOA** | **13** | **4,992** | **3,746.88** | **0** |
| Random invocation | 16 | 6,144 | 3,746.88 | 0 |
| Classical-only | 0 | 0 | 3,746.88 | 0 |

**Quantum shots saved relative to always QAOA:** `(14592 - 4992) / 14592 × 100 = 65.8%` (rounded). **Calls avoided:** 25. The experiment runner enforces up to three calls *per episode*; the interactive site carries a *single-browser session* budget. Those are two different scopes.

**Be clear in your presentation:**

- Final schedule quality matched in these cases **because the risk-scored classical incumbent was retained** whenever quantum sampling did not improve it. Do **not** claim QAOA alone matched the classical solver.
- Classical-only obtained the same mean realized moisture stress with **zero quantum shots**. No quantum advantage has been demonstrated.
- Random invocation was calibrated on development episodes, but observed held-out counts differ (16 versus 13). Do **not** claim the intelligent gate is superior to a matched-rate random policy.
- These are synthetic, ideal-simulator Qiskit Aer measurements, **not** measured farm-water savings, hardware speedups or energy reductions.
- Earlier shared-weather `results/quantum_24/` and `results/historical_test/` studies and `results/member1_compare_10.csv` belong to older experimental conditions. Do not combine their scores or present their percentages as current Hybrid results.
- The historical COBYLA-versus-fixed-angle result (~23.7% lower final *sampled expected stress*) is not a realized irrigation-stress benefit, and final/pilot shot splits differed.

## What the new website shows

1. **Experiments → Primary quantum research result:** Dataset-driven percentage, same-or-different observed mean stress, QAOA calls avoided. The page loads these figures from the archived CSV through `/api/research-results`; if data are missing it does not show a fabricated number.
2. **Overview → Quantum candidate detail:** After a successful actual QAOA call, displays the **best measured QAOA candidate risk**, **classical incumbent risk** and whether the selected final plan is classical or quantum-improved. If the call is skipped, no fictitious candidate is displayed.
3. **Farm Model:** Shared/field-specific weather, risk inputs, invocation policy and advancing with completed windows locked.
4. **Research Notes:** Expected-stress RZ/RZZ phase, feasible XY mixing, QAOA candidate search, and explicit classical CVaR verification.

## Live demonstration — approximately 3 minutes

1. Open the website; show the **exact-K** schedule and risk-aware farm setting (30 seconds).
2. Open **Experiments** first. State the primary question; point to 65.8% fewer quantum shots and the equal selected results across 18 held-out synthetic episodes (45 seconds).
3. In **Farm Model**, enable field-specific mode. Change future weather and recalculate. Advance one window; check the completed cells are disabled (40 seconds).
4. Choose **Always run QAOA** and recalculate. Verify `Quantum Search: Executed`, COBYLA, circuit/shot totals and **best measured quantum candidate versus classical incumbent** (45 seconds).
5. Show budget usage and reset; explain that selective invocation sometimes legitimately skips a quantum call and classical fallback stays usable (30 seconds).
6. End with limitations: no real farm validation, water savings, quantum advantage, speedup, hardware results, or superiority over a matched random trigger (30 seconds).

### Judges' toughest question

**“If classical-only is just as good, why use quantum?”**

> In these small synthetic instances, classical-only is the better practical choice. Our objective is narrower: study when an optional QAOA subroutine should be *invoked*, and measure its quantum execution cost against an always-run QAOA baseline. We built and ran the actual quantum circuit, but our experiments did not establish a quantum advantage over the classical baseline or added crop benefit. The framework makes this boundary measurable instead of hiding it.

## Verification commands — from project root in Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q tests --basetemp=.\pytest_temp
node tests/frontend_regression.cjs
node tests/research_summary_regression.cjs
.\.venv\Scripts\python.exe member2_demo.py --quantum
.\.venv\Scripts\python.exe -m uvicorn server:app --reload
```

**Do not report the package as tested on a clean Windows installation until your team has run these commands.** The previous Hybrid package's Windows verification report is dated 22 October 2026 and records 72 passing tests. New dashboard summary tests are included in this submission update; actual Windows results after the changes must be recorded by the team. One nonblocking Starlette/httpx warning was previously observed.

### Manual browser acceptance check

- [ ] Experiments loads saved results: 65.8%, 4,992 versus 14,592 shots; 13 versus 38 QAOA calls; 3,746.88 mean stress for both.
- [ ] Classical-only remains visible with zero quantum shots.
- [ ] Always QAOA completes and the best measured candidate-risk line appears.
- [ ] Changing field-level inputs invalidates the old schedule; advancing locks past windows.
- [ ] Reset demo restores starting state/budget; saved-plan evaluator does **not** re-run quantum.
- [ ] No browser console error or dead button.
- [x] Updated **Experiments** screenshot captured from this version's HTML/CSS with genuine CSV API responses through a headless FastAPI TestClient bridge (`docs/screenshots/hybrid_experiments.png`). This does **not** depict a completed Qiskit run.
- [ ] Team captures a real **QAOA completed** demo screenshot/video on its Windows machine.
- [ ] Real YouTube demonstration URL added; PPT/portal submitted according to organizer rules.

## Suggested 7-slide PPT content

1. Problem: water-quota constrained irrigation decisions under uncertain synthetic weather.
2. Research question: selective versus always-run quantum invocation; no quantum advantage claim.
3. Farm optimization: three fields × four windows, exactly K events, CVaR rescoring, frozen past.
4. Qiskit algorithm: expected quadratic phase Hamiltonian (RZ/RZZ), feasible XY mixer, COBYLA pilots/final shots.
5. Hybrid policy: classical incumbent → forecast-aware gate → optional QAOA → independent feasibility/risk check → fallback.
6. **Results:** 14,592 vs 4,992 shots; 38 vs 13 QAOA calls; equal 3,746.88 final stress; classical zero quantum shots.
7. Limitations, honest conclusion, future compute-matched random and stronger classical baselines, actual demo links.

## Package delivery — team action required

- Update README's **Demo video** placeholder with the genuine YouTube URL.
- An updated Experiments screenshot is included. Also capture a completed **Qiskit Aer** execution screenshot on the demo laptop; the supplied screenshot uses the synthetic dataset and classical-only test environment.
- Review the submitted sources/AI assistance acknowledgment and compliance with the organizer's final rules.
- Copy this project's **contents** into the root of the official repository checkout; preserve its `.git` directory. Use a feature branch and PR as in `UPLOAD_TO_REPOSITORY.md`.
- Run the commands above in a fresh installation, check the `main`/required submission branch actually contains the merged changes, and submit the PPT and project details. This ZIP does **not** itself publish anything.
