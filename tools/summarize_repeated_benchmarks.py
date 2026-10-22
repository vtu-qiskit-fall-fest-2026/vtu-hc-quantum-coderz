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
    episodes=[]
    runs=[json.loads((d/'metadata.json').read_text(encoding='utf-8')) for d in replicate_dirs]
    settings=('mode','farm_model','quantum_engine','cvar','shots_per_quantum_call','scenario_count','max_quantum_calls_per_trajectory')
    if any(any(run.get(k)!=runs[0].get(k) for k in settings) for run in runs):
        raise ValueError('Cannot aggregate runs with different model/algorithm/settings')
    seed_sets=[set(run['test_episode_seeds']) for run in runs]
    if any(seed_sets[i]&seed_sets[j] for i in range(len(runs)) for j in range(i)):
        raise ValueError('Held-out episode seeds overlap between replicates')
    for index,directory in enumerate(replicate_dirs):
        for row in read_csv(directory/'episodes.csv'):
            row['replicate']=index; episodes.append(row)
    policies = list(dict.fromkeys(row["policy"] for row in episodes))
    classical = {(row["replicate"],row["episode"]): float(row["total_realized_stress"])
                 for row in episodes if row["policy"] == "never"}

    summary = []
    for policy in policies:
        rows = [row for row in episodes if row["policy"] == policy]
        stress = [float(row["total_realized_stress"]) for row in rows]
        paired = [value - classical[(row["replicate"],row["episode"])]
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

    run_metadata=runs[0]
    total_test=sum(run['heldout_episodes'] for run in runs)
    metadata = {
        'mode':run_metadata['mode'],
        'farm_model':run_metadata.get('farm_model','historical_unspecified'),
        'quantum_engine':run_metadata.get('quantum_engine','historical_unspecified'),
        'runtime_versions_by_replicate':[run.get('runtime_versions') for run in runs],
        'replicates':len(runs),
        'development_episodes_by_replicate':[run['development_episodes'] for run in runs],
        'heldout_episodes_by_replicate':[run['heldout_episodes'] for run in runs],
        'total_heldout_episodes_per_policy':total_test,
        'shots_per_call':run_metadata['shots_per_quantum_call'],
        'scenario_count':run_metadata['scenario_count'],
        'max_quantum_calls_per_trajectory':run_metadata['max_quantum_calls_per_trajectory'],
        'seed_blocks':[{'replicate':i+1,'development_episode_seeds':run['development_episode_seeds'],'test_episode_seeds':run['test_episode_seeds']} for i,run in enumerate(runs)],
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
        f"**Replicates:** {len(runs)}; **held-out episodes per policy:** {total_test}; **development episodes:** {metadata['development_episodes_by_replicate']}.",
        f"**Run:** {metadata['mode']}; {metadata['farm_model']}; {metadata['quantum_engine']}; {metadata['shots_per_call']} shots/call; {metadata['scenario_count']} scenarios; {metadata['max_quantum_calls_per_trajectory']} calls/episode.",
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
    report += ["", "Inputs and per-run outputs are preserved in the replicate directories. JSON metadata is derived from each actual run.", ""]
    (args.root / "aggregate_report.md").write_text("\n".join(report), encoding="utf-8")
    print(output_csv)
    print(args.root / "aggregate_report.md")


if __name__ == "__main__":
    main()
