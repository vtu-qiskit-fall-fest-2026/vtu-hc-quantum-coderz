"""Aggregate independent held-out policy benchmark runs using only stdlib."""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("results/quantum_repeated"))
    parser.add_argument("--replicates", type=int, default=3)
    args = parser.parse_args()
    replicate_dirs = [args.root / f"replicate_{i}" for i in range(1, args.replicates + 1)]
    episodes = [row for directory in replicate_dirs for row in read_csv(directory / "episodes.csv")]
    policies = list(dict.fromkeys(row["policy"] for row in episodes))
    classical = {row["episode"]: float(row["total_realized_stress"])
                 for row in episodes if row["policy"] == "never"}

    summary = []
    for policy in policies:
        rows = [row for row in episodes if row["policy"] == policy]
        stress = [float(row["total_realized_stress"]) for row in rows]
        paired = [value - classical[row["episode"]]
                  for row, value in zip(rows, stress)]
        mean_delta = statistics.mean(paired)
        sd_delta = statistics.stdev(paired) if len(paired) > 1 else 0.0
        ci_half = 1.96 * sd_delta / math.sqrt(len(paired))
        summary.append({
            "policy": policy,
            "heldout_episodes": len(rows),
            "mean_realized_stress": statistics.mean(stress),
            "std_realized_stress": statistics.stdev(stress) if len(stress) > 1 else 0.0,
            "paired_difference_vs_never": mean_delta,
            "paired_difference_ci95_normal_low": mean_delta - ci_half,
            "paired_difference_ci95_normal_high": mean_delta + ci_half,
            "paired_wins": sum(value < -1e-9 for value in paired),
            "paired_ties": sum(abs(value) <= 1e-9 for value in paired),
            "paired_losses": sum(value > 1e-9 for value in paired),
            "completed_quantum_calls": sum(int(row["quantum_successful_calls"]) for row in rows),
            "requested_quantum_calls": sum(int(row["quantum_calls"]) for row in rows),
            "quantum_improvements_over_classical_incumbent": sum(int(row["quantum_improvements"]) for row in rows),
            "shots": sum(int(row["shots"]) for row in rows),
            "two_qubit_gate_shots": sum(int(row["two_qubit_gate_shots"]) for row in rows),
            "compiled_gate_shots": sum(int(row["compiled_gate_shots"]) for row in rows),
            "planner_score_requests": sum(int(row["planner_score_requests"]) for row in rows),
            "planner_loss_scenario_evaluations": sum(int(row["planner_loss_scenario_evaluations"]) for row in rows),
            "planner_exact_enumeration_evaluations": sum(int(row["planner_exact_enumeration_evaluations"]) for row in rows),
            "offline_exact_evaluations": sum(int(row["offline_exact_evaluations"]) for row in rows),
            "mean_selected_forecast_gap": statistics.mean(float(row["mean_selected_forecast_gap"]) for row in rows),
            "mean_classical_forecast_gap": statistics.mean(float(row["mean_classical_forecast_gap"]) for row in rows),
            "mean_planner_seconds_per_episode": statistics.mean(float(row["planning_runtime_seconds"]) for row in rows),
        })

    output_csv = args.root / "aggregate_summary.csv"
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    run_metadata = json.loads((replicate_dirs[0] / "metadata.json").read_text(encoding="utf-8"))
    metadata = {
        "mode": "quantum",
        "runtime_versions": run_metadata.get("runtime_versions"),
        "replicates": args.replicates,
        "development_episodes_per_replicate": 10,
        "heldout_episodes_per_replicate": 30,
        "total_heldout_episodes_per_policy": 30 * args.replicates,
        "shots_per_call": 384,
        "scenario_count": 15,
        "max_quantum_calls_per_trajectory": 3,
        "seed_blocks": [
            {"replicate": index, "seed": 20261022 + (index - 1) * 10000}
            for index in range(1, args.replicates + 1)
        ],
        "confidence_interval": "Paired normal-approximation 95% interval on episode-level differences; descriptive, not adjusted for multiple comparisons",
        "limitations": [
            "All weather and moisture values are synthetic and are not field validation.",
            "Aer is an ideal simulator and the result is not quantum hardware evidence.",
            "No policy showed benefit unless supported by the paired held-out outcomes; inspect wins, ties, losses and confidence intervals.",
            "Gate-shot totals are compiled two-qubit or all-gate instruction counts multiplied by shots, not runtime, energy, or hardware cost.",
            "Classical scenario counts are operation proxies; CPU time is reported separately and is machine-dependent.",
            "The exact_classical policy enumerates the same current forecast/scenario model at each decision and is an expensive classical reference, not a future-weather oracle.",
        ],
    }
    (args.root / "aggregate_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    report = [
        "# Repeated held-out Qiskit Aer policy comparison", "",
        f"**Replicates:** {args.replicates}; **held-out episodes per policy:** {30 * args.replicates}; **development episodes per replicate:** 10.",
        "**Run:** Qiskit Aer ideal simulator; 384 shots per call; 15 uncertainty scenarios; maximum 3 calls per episode.",
        "**Outcome:** lower synthetic realized moisture stress is better. Negative paired differences favor the named policy over `never`.",
        "", "| Policy | Mean stress ± SD | Paired Δ vs never (normal 95% CI) | Wins/ties/losses | Q completed/requested | Improvements | Shots | 2Q gate-shots | Forecast gap |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        report.append(
            f"| {row['policy']} | {row['mean_realized_stress']:.2f} ± {row['std_realized_stress']:.2f} "
            f"| {row['paired_difference_vs_never']:+.2f} [{row['paired_difference_ci95_normal_low']:+.2f}, {row['paired_difference_ci95_normal_high']:+.2f}] "
            f"| {row['paired_wins']}/{row['paired_ties']}/{row['paired_losses']} "
            f"| {row['completed_quantum_calls']}/{row['requested_quantum_calls']} | {row['quantum_improvements_over_classical_incumbent']} "
            f"| {row['shots']} | {row['two_qubit_gate_shots']} | {row['mean_selected_forecast_gap']:.2f} |"
        )
    report += ["", "## Interpretation", "",
               "These are paired comparisons across the same held-out synthetic weather episode IDs. The confidence intervals are descriptive normal approximations and do not correct for multiple policy comparisons. Quantum samples are classically rescored, and the classical incumbent is retained unless a sampled schedule scores better under the planner objective. `exact_classical` exhaustively enumerates each current feasible schedule set using the same forecast scenarios; it is an expensive, exact current-model reference, not a future-weather oracle. A completed Qiskit call therefore does not imply an improvement.",
               "", "## Limits", ""]
    report.extend(f"- {item}" for item in metadata["limitations"])
    report += ["", "Inputs and per-run outputs are preserved under `replicate_1/` through `replicate_3/`. The JSON metadata records seeds and settings.", ""]
    (args.root / "aggregate_report.md").write_text("\n".join(report), encoding="utf-8")
    print(output_csv)
    print(args.root / "aggregate_report.md")


if __name__ == "__main__":
    main()
