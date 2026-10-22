# JalQ-R — Member 1 patch (quantum optimizer)

## What is changed

- `quantum_engine.py` maintains the original `qaoa_candidate(planner, seed_bits, shots=384)` signature.
- The default `qaoa_candidate` now tries COBYLA proposals under a **strict circuit-shot budget** (at most 8×32 optimization shots, with unused pilot shots added to the final sampling budget; total = 384).
- `fixed_qaoa_candidate` preserves the three-angle pilot search for an equal-shot comparison.
- Additional diagnostics: measured validity, distinct schedules, mean sampled expected stress, best sampled CVaR-based risk, angle settings, per-evaluation shots/gates/depth.
- `requirements.txt` adds SciPy; `tests/test_quantum.py` adds checks; `compare_quantum.py` writes fair-shot comparison CSV.

## Replace only these paths in your clone

```
quantum_engine.py
requirements.txt
tests/test_quantum.py
compare_quantum.py
```

DO NOT replace `planner.py`, `server.py`, `experiments.py`, or `static/*`.

## Windows PowerShell

```
git switch main
git pull origin main
git switch -c feature/quantum-optimizer
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -c "from server import Payload,plan; x=plan(Payload(policy='always')); print(x['quantum'])"
python compare_quantum.py --shots 384 --seeds 7 11 23 --output results/member1_compare.csv
```

For slower but broader evidence, repeat with more seeds. Do not change the random seed for one method but not the other.

## Important interpretation

- The actual farm choice uses the best classical incumbent unless a sampled quantum solution has *lower* risk.
- Parameter tuning optimizes expected quadratic stress, NOT CVaR.
- The fixed vs COBYLA comparison measures shot counts and sampled schedule quality; it is **not** a claim of a quantum advantage over classical optimization or hardware speedup.
- All shots, including COBYLA's pilot experiments and the final measurement, count toward the budget.
- `optimizer_success=False` can simply mean COBYLA stopped at its limited evaluation budget; if fewer than 4 pilots fit, COBYLA is intentionally skipped. Check `status='completed'`, shot counts and scores separately.
- Do NOT equate 'best candidate risk' from all pilot+final samples with final circuit distribution quality. Use `final_mean_sampled_expected_stress` for that separate question.
- After Member 2 changes `planner.py`, rerun the exact QUBO/phase tests and joint integration tests.

## GitHub submission

```
git status
git add quantum_engine.py requirements.txt tests/test_quantum.py compare_quantum.py
git commit -m "feat: budgeted COBYLA QAOA with diagnostics and fixed-shot baseline"
git push -u origin feature/quantum-optimizer
```

Open a Pull Request against `main`. Ensure tests pass before merging.
