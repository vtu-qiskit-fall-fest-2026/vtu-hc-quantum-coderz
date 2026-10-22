"""Offline comparison of fixed-parameter and COBYLA QAOA with equal shot counts.

Usage:
    python compare_quantum.py --shots 384 --seeds 7 11 23 --output results/member1_compare.csv

Not evidence of quantum speedup or advantage over classical optimization.
"""
import argparse
import csv
from pathlib import Path

from planner import FarmRequest, Planner
from quantum_engine import fixed_qaoa_candidate, qaoa_candidate


def make_request(seed, shots):
    return FarmRequest(
        moisture=[29, 23, 25], target=[42, 40, 44],
        priority=[1.3, 1.0, 1.5], rain=[3, 0, 4, 1],
        evaporation=[4, 5, 4, 5],
        available=[[1, 1, 0, 1], [1, 0, 1, 0], [0, 1, 1, 1]],
        executed=[[0] * 4 for _ in range(3)],
        quota=3, uncertainty=2.0, risk_weight=0.35, alpha=0.8,
        scenario_count=15, seed=seed, quantum_shots=shots,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", type=int, default=384)
    parser.add_argument("--seeds", nargs="+", type=int, default=[7, 11, 23])
    parser.add_argument("--output", default="results/member1_compare.csv")
    args = parser.parse_args()
    rows = []
    for seed in args.seeds:
        planner = Planner(make_request(seed, args.shots))
        classical_seed = planner.candidates()[0]["bits"]
        classical_risk = planner.score(classical_seed, track=False)["risk"]
        for name, fn in (("fixed", fixed_qaoa_candidate), ("cobyla", qaoa_candidate)):
            result = fn(planner, classical_seed, shots=args.shots)
            if result["status"] != "completed":
                raise RuntimeError(f"{name} failed on seed {seed}: {result}")
            assert result["shots"] == args.shots
            rows.append({
                "seed": seed, "method": name,
                "classical_risk": round(classical_risk, 6),
                "quantum_best_sampled_risk": result["best_candidate_risk"],
                "quantum_improved_classical": (
                    result["best_candidate_risk"] is not None
                    and result["best_candidate_risk"] < classical_risk - 1e-9
                ),
                "initial_mean_sampled_stress": result["initial_mean_sampled_expected_stress"],
                "final_mean_sampled_stress": result["final_mean_sampled_expected_stress"],
                "unique_feasible_schedules": result["unique_feasible_schedules"],
                "feasibility_rate": result["raw_feasibility_rate"],
                "shots": result["shots"],
                "circuit_evaluations": result["circuit_evaluations"],
                "gate_weighted_shots": result["gate_weighted_shots"],
                "two_qubit_gates_max": result["two_qubit_gates"],
                "depth_max": result["depth"],
            })
            print(
                f"seed={seed:<6} {name:<6} shots={result['shots']} "
                f"best_risk={result['best_candidate_risk']:.2f} "
                f"final_mean={result['final_mean_sampled_expected_stress']:.2f} "
                f"distinct={result['unique_feasible_schedules']}"
            )
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows: {path}")
    print("NOTE: Only exploratory simulated comparisons. No claimed quantum advantage.")


if __name__ == "__main__":
    main()

