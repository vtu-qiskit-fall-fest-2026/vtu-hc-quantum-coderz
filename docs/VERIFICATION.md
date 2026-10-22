# Verification record

## Final documentation package — 23 October 2026

This is the current package record. Older runs below are historical.

- Main README updated with release date, integrated-project instructions and explicit submission status.
- Member patch instructions replaced with contribution summaries. Old demo skeleton notes replaced by links to current guidance. Submission checklist no longer implies the latest full suite passed.
- Both JavaScript syntax checks and both frontend regression scripts passed.
- `python -m pytest -q tests/test_experiments.py tests/test_farm_v2.py -k "not merged_member1_optimizer"`: **21 passed, 1 deselected**. The excluded test exercises Qiskit; this is a deliberately limited classical/model check, not the complete suite.
- All Python sources parsed successfully. All 32 local Markdown links resolve. External reference URLs and organizer portal requirements were not revalidated in this documentation pass.
- Saved aggregate CSV confirms 14,592 vs 4,992 shots (65.8% reduction), identical reported mean stress across policies and zero quantum improvements. These are existing saved results, not newly generated quantum experiments.
- Application source and saved CSV files are byte-identical to the preceding corrected package. No algorithm changes were needed for this documentation cleanup.
- Full Python/API/Qiskit execution and a final end-to-end browser walkthrough are **not certified** by this pass. The preceding full-suite attempt encountered the local Aer native-library failure described below.

Before submission: add the real video, finish the presentation/portal steps, and run the full tests and live QAOA on the demo laptop.

## Current corrected package — 23 October 2026

Changes: benchmark headline cards now clear on refresh, invalid data, missing hybrid results, and request failure. The regression test executes production rendering/loading functions and checks stale values are removed and valid rendering recovers. The submission guide now correctly says quantum advantage over the classical baseline. README includes both JavaScript regression commands. Scientific results and optimizer code are unchanged.

| Check | Current result |
|---|---|
| `node --check static/member3.js` | Passed |
| `node tests/research_summary_regression.cjs` | Passed, including invalid/missing/failed refresh and recovery |
| `node tests/frontend_regression.cjs` | Passed |
| Full Python suite on installed Windows Python 3.13 | Attempted; not completed successfully. Qiskit Aer native-library loading raised Windows exception `0xc0000008`; run was stopped. This is not a passing verification. |

The reviewed input package collected 72 Python tests. No Python source or tests were changed by this correction. A clean full-suite run and live QAOA demonstration on the submission laptop remain required. No fresh isolated installation or final browser walkthrough was completed for this correction.

The older 72-pass and 66-pass/5-skip records below describe earlier environments/packages; their totals differ and neither certifies this corrected ZIP. They are retained as historical records, not a current all-tests-pass claim.

Still pending: real demo video URL, final presentation/portal submission, and final laptop walkthrough.

## Historical hybrid verification — 22 October 2026

Earlier code verification on Windows, Python 3.13.0:

| Check | Result |
|---|---|
| `python -m pytest tests -q --basetemp=pytest_temp` | **72 passed**, 1 nonblocking Starlette/httpx deprecation warning; 9.96 seconds |
| `node --check static/app.js` and `node --check static/member3.js` | Passed |
| `node tests/frontend_regression.cjs` | Passed: advanced timeline refresh, plan invalidation, accepted references, stale-result rejection with resource charging, persistence, comparison accounting, saved-plan API payload |
| `python member2_demo.py --quantum` | Completed: COBYLA, 128 shots, three irrigation events, no quantum error |
| Fresh field-specific benchmark | Three independent blocks; 18 held-out episodes per policy; actual Qiskit Aer executions completed |
| FastAPI tests | Planning, invalid inputs, static assets, historical CSVs, fresh CSVs and saved-plan evaluation passed |

Quantum tests exercise fixed and COBYLA paths, bit ordering, phase mapping, feasible measurements and shot budgets. Hybrid tests cover field evaporation shifts, cache behavior, cumulative budgets, offline isolation, field-specific forecasts, and strictly classical smoke mode.

Browser check: dashboard loaded and produced a schedule; shared evaporation controls appeared; field-specific model enabled; advanced inputs appeared and advancement disabled until recalculation. An actual quantum request was started through the browser. The browser session then became unavailable and its policy gate blocked reconnection. Final quantum completion, advance/lock behavior and visual layout were therefore verified through API/runtime tests, not a completed final browser walkthrough. Do the remaining visual walkthrough on the demo laptop. The supplied `docs/screenshots/overview.png` is a historical user-provided screenshot, not a capture of this hybrid.

Early attempts under restricted local-network permissions stalled in Windows socketpair setup; granting loopback/network access allowed the complete suite to pass. These environment failures were not counted as passing tests. No remote GitHub files were modified.

Fresh outcome: selective used 4,992 shots versus 14,592 for always-QAOA (65.8% fewer). All six policies had identical mean realized stress, 3746.8774. Quantum samples improved no classical incumbent. Classical-only used zero quantum shots. This is a small synthetic ideal-simulator study, not proof of quantum advantage, water savings or hardware speedup.

Reproduce with commands in docs/experiments.md. Direct package versions are in requirements-tested.txt. A fresh isolated installation was not performed; tests used the installed environment. Remaining submission tasks: video URL, PPT/portal submission, team review and final laptop walkthrough.

## Historical narrative/UI update — additional local verification

Changes: README emphasizes the selective-versus-always QAOA research comparison; the Experiments page computes its top-line metrics from `/api/research-results` (saved CSV evidence); Overview distinguishes measured QAOA candidate risk from the classical incumbent; API metadata identifies fresh and historical studies separately. No quantum optimizer, farm equations, experimental CSV values, or historical reports were modified.

- `python -m pytest -q tests --basetemp=/mnt/data/JalQ_R_Submission_Work/pytest_temp`: **66 passed, 5 skipped** in the available environment; the five skipped tests require absent Qiskit components. These numbers **do not replace** the earlier Windows 72-pass Qiskit verification above.
- `node --check static/app.js` and `node --check static/member3.js`: passed.
- `node tests/frontend_regression.cjs`: passed.
- `node tests/research_summary_regression.cjs`: passed. Also checked that modified input data change the summary and do not falsely claim equal stress.
- Automated headless Chromium rendered the current HTML/CSS and used real FastAPI TestClient responses to supply the saved benchmark API. **Observed 65.8%, 4,992 vs 14,592 shots, 25 fewer calls, identical observed mean stress.** Tested advanced field edit → required recalculation → advancement → past-window lock. **No browser JavaScript errors.** Static screenshot: `docs/screenshots/hybrid_experiments.png` (preview) and `hybrid_experiments_full.png`. Browser HTTP network navigation is restricted in this sandbox, so this check used the original frontend sources with a TestClient response bridge; it is **not** a full network-level production browser test.
- Live quantum simulation was **not rerun** here because `qiskit` and `qiskit_aer` are unavailable in this environment. The team's prior Windows screenshot documented 72 passing tests and a successful COBYLA Qiskit Aer demo, but the **team should rerun the complete suite** after copying these UI/documentation changes.

**Pending:** final Windows run of updated package, actual QAOA screenshot/video URL, team review and required organizer PPT/portal submission. Neither GitHub nor the portal has been updated automatically.
