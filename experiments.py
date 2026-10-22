"""JalQ-R rolling-horizon experimental benchmark.

Research boundaries:
- Simulated weather, not agronomic field observations.
- Decisions receive forecasts and past observations, NOT future realizations.
- Six policies share the same exogenous scenario for each episode.
- Classical/quantum outputs are evaluated on actual simulated weather after decisions.
- Random invocation probability is calibrated on disjoint development episodes.
- This is an exploratory benchmark, not a hardware quantum-advantage test.

Quick check (no Qiskit required):
    python experiments.py --mode smoke --dev 4 --test 6
Real Qiskit benchmark:
    python experiments.py --mode quantum --dev 6 --test 12 --shots 384
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
import time
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np

from planner import FarmRequest, Planner, decide
from quantum_engine import quantum_available

POLICIES = ("never", "always", "selective", "random", "extra_classical", "exact_classical")
FIELDS = 3
WINDOWS = 4
BASE_RAIN = (3.0, 0.0, 4.0, 1.0)
BASE_EVAP = (4.0, 5.0, 4.0, 5.0)
DEFAULT_AVAILABLE = ((1, 1, 0, 1), (1, 0, 1, 0), (0, 1, 1, 1))
TARGET = (42.0, 40.0, 44.0)
PRIORITY = (1.3, 1.0, 1.5)
MOISTURE = (29.0, 23.0, 25.0)


def installed_version(package: str) -> str | None:
    try:
        return version(package)
    except PackageNotFoundError:
        return None


@dataclass(frozen=True)
class WeatherEpisode:
    seed: int
    actual_rain: tuple[float, ...]
    actual_evap: tuple[float, ...]
    forecasts_rain: tuple[tuple[float, ...], ...]
    forecasts_evap: tuple[tuple[float, ...], ...]


def create_episode(seed: int) -> WeatherEpisode:
    """Produce exogenous realization and successive forecasts, deterministically.

    This offline generator can sample the truth. The optimizer receives only
    its forecast for the current step; truth is revealed after that step.
    """
    rng = np.random.default_rng(seed)
    actual_rain = np.maximum(0, np.array(BASE_RAIN) + rng.normal(0, 2.7, WINDOWS))
    actual_evap = np.maximum(0, np.array(BASE_EVAP) + rng.normal(0, 0.7, WINDOWS))
    forecast_rain = []
    forecast_evap = []
    for t in range(WINDOWS):
        # Forecast uncertainty gradually contracts as more information arrives.
        sigma_r = (3.4, 2.2, 1.4, 0.7)[t]
        sigma_e = (1.0, 0.75, 0.5, 0.25)[t]
        rf, ef = actual_rain.copy(), actual_evap.copy()
        rf[t:] = np.maximum(0, actual_rain[t:] + rng.normal(0, sigma_r, WINDOWS - t))
        ef[t:] = np.maximum(0, actual_evap[t:] + rng.normal(0, sigma_e, WINDOWS - t))
        forecast_rain.append(tuple(round(float(x), 4) for x in rf))
        forecast_evap.append(tuple(round(float(x), 4) for x in ef))
    return WeatherEpisode(
        seed=seed,
        actual_rain=tuple(float(x) for x in actual_rain),
        actual_evap=tuple(float(x) for x in actual_evap),
        forecasts_rain=tuple(forecast_rain),
        forecasts_evap=tuple(forecast_evap),
    )


def request_for(
    episode: WeatherEpisode,
    window: int,
    moisture: list[float],
    executed: list[list[int]],
    prior_plan: list[list[int]] | None,
    *,
    policy: str,
    shots: int,
    scenario_count: int,
) -> FarmRequest:
    """Build a public information state; never insert realized future weather."""
    return FarmRequest(
        moisture=list(moisture),
        target=list(TARGET),
        priority=list(PRIORITY),
        rain=list(episode.forecasts_rain[window]),
        evaporation=list(episode.forecasts_evap[window]),
        available=[list(row) for row in DEFAULT_AVAILABLE],
        executed=[list(row) for row in executed],
        start_window=window,
        quota=3,
        irrigation_gain=10.0,
        uncertainty=2.0,
        risk_weight=0.35,
        alpha=0.8,
        scenario_count=scenario_count,
        seed=episode.seed + 31,  # Same risk-scenario stream for all policies.
        policy=policy,
        trigger_shift=0.25,
        trigger_regret=0.04,
        trigger_instability=0.10,
        quantum_shots=shots,
        previous_rain=(list(episode.forecasts_rain[window - 1]) if window else None),
        previous_evaporation=(list(episode.forecasts_evap[window - 1]) if window else None),
        previous_plan=([list(row) for row in prior_plan] if prior_plan is not None else None),
    )


def calibrate_random_probability(
    development_episodes: list[WeatherEpisode], *, shots: int, scenario_count: int
) -> tuple[float, int, int]:
    """Use classical rollouts on TRAIN episodes, never held-out outcomes.

    Calibration uses the never-run planner's information states. This avoids
    using held-out trigger frequencies to choose the random policy's rate.
    """
    eligible = triggered = 0
    for episode in development_episodes:
        trace, _ = run_episode(
            episode,
            policy="never",
            shots=shots,
            scenario_count=scenario_count,
            random_probability=0.0,
            max_quantum_calls=0,
            mode="smoke",
        )
        for rec in trace:
            if rec["nontrivial"]:
                eligible += 1
                triggered += int(rec["gate_condition"])
    return (triggered / eligible if eligible else 0.0, triggered, eligible)


def run_episode(
    episode: WeatherEpisode,
    *,
    policy: str,
    shots: int,
    scenario_count: int,
    random_probability: float,
    max_quantum_calls: int,
    mode: str,
) -> tuple[list[dict], dict]:
    """Simulate all four decision windows for one policy and realization."""
    if policy not in POLICIES:
        raise ValueError(f"Unknown policy {policy}")
    observed_moisture = list(MOISTURE)
    executed = [[0] * WINDOWS for _ in range(FIELDS)]
    prior_plan = None
    if max_quantum_calls < 0 or shots < 64:
        raise ValueError("Quantum call budget must be non-negative and shots must be at least 64")
    calls_remaining = max_quantum_calls
    shots_used = 0
    # Random calls are independent across steps and reproducible by episode.
    invocation_rng = np.random.default_rng(episode.seed + 9_100_017)
    records: list[dict] = []

    for t in range(WINDOWS):
        req = request_for(
            episode,
            t,
            observed_moisture,
            executed,
            prior_plan,
            policy="never",
            shots=shots,
            scenario_count=scenario_count,
        )
        planning_space = Planner(req)
        nontrivial = 0 < planning_space.k < planning_space.n and planning_space.n >= 2
        if policy == "always":
            requested = True
        elif policy == "selective":
            requested = True  # decide() evaluates its genuine gate internally.
        elif policy == "random":
            requested = bool(invocation_rng.random() < random_probability)
        else:
            requested = False

        blocked_by_budget = bool(nontrivial and requested and calls_remaining <= 0)
        if policy == "selective":
            # Selective policy is evaluated by the actual decision gate whenever
            # budget is available. Budget exhausted means classical fallback.
            effective_policy = "selective" if calls_remaining > 0 else "never"
        elif policy == "extra_classical":
            effective_policy = "extra_classical"
        elif policy == "exact_classical":
            effective_policy = "exact_classical"
        elif policy in ("always", "random"):
            effective_policy = "always" if requested and calls_remaining > 0 else "never"
        else:
            effective_policy = "never"
        req.policy = effective_policy
        req.quantum_max_calls = calls_remaining
        req.quantum_calls_used = 0
        req.quantum_shots_budget = max_quantum_calls * shots
        req.quantum_shots_used = shots_used
        plan_started = time.perf_counter()
        plan = decide(req)
        planning_runtime_seconds = time.perf_counter() - plan_started
        quantum = plan["quantum"]
        called = bool(plan["quantum_invoked"])
        if called:
            calls_remaining -= 1
        shots_used += int(quantum.get("shots", 0))
        if calls_remaining < 0 or shots_used > max_quantum_calls * shots:
            raise AssertionError("Rolling quantum call or shot budget exceeded")
        if mode == "quantum" and called and quantum["status"] != "completed":
            raise RuntimeError(
                f"Quantum execution failed for episode={episode.seed}, "
                f"policy={policy}, window={t+1}: {quantum}"
            )
        if int(quantum.get("shots", 0)) > shots:
            raise AssertionError("A quantum invocation exceeded its shot allocation")

        schedule = plan["schedule"]
        if sum(sum(row) for row in schedule) != 3:
            raise AssertionError("Output schedule violated the total exact-K constraint")
        if any(schedule[f][past] != executed[f][past] for f in range(FIELDS) for past in range(t)):
            raise AssertionError("Replanning modified an executed irrigation event")

        # Post-hoc exact optimum under this decision's forecast/scenarios. It
        # never sees future realized weather and never affects the chosen plan.
        audit = Planner(req)
        selected_bits = tuple(schedule[f][window] for f, window in audit.slots)
        selected_forecast_risk = audit.score(selected_bits, track=False)["risk"]
        exact_forecast = audit.evaluate_exact_offline()
        exact_forecast_gap = max(0.0, selected_forecast_risk - exact_forecast["risk"])
        classical_forecast_gap = max(0.0, plan["classical_baseline"]["risk"] - exact_forecast["risk"])
        work = plan["planner_work"]

        # Now, and only now, reveal the actual rain/evaporation for window t.
        irrigation_events_this_window = 0
        realized_stress = 0.0
        for f in range(FIELDS):
            irrigation_event = int(schedule[f][t])
            irrigation_events_this_window += irrigation_event
            executed[f][t] = irrigation_event
            observed_moisture[f] += (
                episode.actual_rain[t] - episode.actual_evap[t] + 10.0 * irrigation_event
            )
            realized_stress += PRIORITY[f] * (observed_moisture[f] - TARGET[f]) ** 2

        prior_plan = schedule
        records.append({
            "episode": episode.seed,
            "policy": policy,
            "window": t + 1,
            "nontrivial": int(nontrivial),
            "gate_condition": int(plan["trigger"]["condition"]),
            "forecast_shift": plan["trigger"]["shift"],
            "regret_proxy": plan["trigger"]["regret_proxy"],
            "ranking_instability": plan["trigger"]["ranking_instability"],
            "budget_blocked": int(blocked_by_budget),
            "quantum_invoked": int(called),
            "quantum_status": quantum["status"],
            "quantum_improved": int(plan["quantum_improved"]),
            "shots": int(quantum.get("shots", 0)),
            "gate_weighted_shots": int(quantum.get("gate_weighted_shots", 0)),
            "circuit_evaluations": int(quantum.get("circuit_evaluations", 0)),
            "two_qubit_gates_max": int(quantum.get("two_qubit_gates", 0)),
            "circuit_depth_max": int(quantum.get("depth", 0)),
            "two_qubit_gate_shots": int(quantum.get("two_qubit_gate_shots", quantum.get("gate_weighted_shots", 0))),
            "compiled_gate_shots": int(quantum.get("compiled_gate_shots", 0)),
            "classical_evaluations_reported": int(plan["classical_evaluations"]),
            "planner_score_requests": int(work["score_requests"]),
            "planner_score_cache_hits": int(work["score_cache_hits"]),
            "planner_loss_vector_requests": int(work["loss_vector_requests"]),
            "planner_loss_vector_cache_hits": int(work["loss_vector_cache_hits"]),
            "planner_unique_loss_vectors": int(work["unique_loss_vectors"]),
            "planner_loss_scenario_evaluations": int(work["loss_scenario_evaluations"]),
            "planner_qubo_builds": int(work["qubo_builds"]),
            "planner_exact_enumeration_evaluations": int(work["exact_enumeration_evaluations"]),
            "offline_exact_evaluations": math.comb(len(audit.slots), audit.k),
            "selected_forecast_risk": float(selected_forecast_risk),
            "exact_forecast_risk": float(exact_forecast["risk"]),
            "selected_forecast_gap": float(exact_forecast_gap),
            "classical_forecast_gap": float(classical_forecast_gap),
            "planning_runtime_seconds": float(planning_runtime_seconds),
            "predicted_risk": float(plan["objective"]["risk"]),
            "classical_baseline_risk": float(plan["classical_baseline"]["risk"]),
            "realized_stress": float(realized_stress),
            "irrigation_events": irrigation_events_this_window,
            "selected_schedule": json.dumps(schedule, separators=(",", ":")),
        })

    if sum(sum(row) for row in executed) != 3:
        raise AssertionError("Total executed irrigation events did not equal 3")
    summary = {
        "episode": episode.seed,
        "policy": policy,
        "total_realized_stress": float(sum(r["realized_stress"] for r in records)),
        "mean_predicted_risk": float(statistics.mean(r["predicted_risk"] for r in records)),
        "quantum_calls": sum(r["quantum_invoked"] for r in records),
        "quantum_successful_calls": sum(r["quantum_status"] == "completed" for r in records),
        "quantum_improvements": sum(r["quantum_improved"] for r in records),
        "shots": sum(r["shots"] for r in records),
        "gate_weighted_shots": sum(r["gate_weighted_shots"] for r in records),
        "circuit_evaluations": sum(r["circuit_evaluations"] for r in records),
        "two_qubit_gate_shots": sum(r["two_qubit_gate_shots"] for r in records),
        "compiled_gate_shots": sum(r["compiled_gate_shots"] for r in records),
        "classical_evaluations_reported": sum(r["classical_evaluations_reported"] for r in records),
        "planner_score_requests": sum(r["planner_score_requests"] for r in records),
        "planner_score_cache_hits": sum(r["planner_score_cache_hits"] for r in records),
        "planner_loss_vector_requests": sum(r["planner_loss_vector_requests"] for r in records),
        "planner_loss_vector_cache_hits": sum(r["planner_loss_vector_cache_hits"] for r in records),
        "planner_unique_loss_vectors": sum(r["planner_unique_loss_vectors"] for r in records),
        "planner_loss_scenario_evaluations": sum(r["planner_loss_scenario_evaluations"] for r in records),
        "planner_qubo_builds": sum(r["planner_qubo_builds"] for r in records),
        "planner_exact_enumeration_evaluations": sum(r["planner_exact_enumeration_evaluations"] for r in records),
        "offline_exact_evaluations": sum(r["offline_exact_evaluations"] for r in records),
        "mean_selected_forecast_gap": statistics.mean(r["selected_forecast_gap"] for r in records),
        "mean_classical_forecast_gap": statistics.mean(r["classical_forecast_gap"] for r in records),
        "planning_runtime_seconds": sum(r["planning_runtime_seconds"] for r in records),
        "budget_blocked": sum(r["budget_blocked"] for r in records),
        "eligible_nontrivial_updates": sum(r["nontrivial"] for r in records),
        "irrigation_events": sum(r["irrigation_events"] for r in records),
    }
    return records, summary


def mean_and_std(values: list[float]) -> tuple[float, float]:
    return statistics.mean(values), statistics.stdev(values) if len(values) >= 2 else 0.0


def save_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError("No data")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def benchmark(*, dev: int, test: int, shots: int, scenario_count: int,
              max_quantum_calls: int, seed: int, mode: str, output: Path) -> dict:
    if dev < 2 or test < 2:
        raise ValueError("Use at least two dev and two test episodes")
    if shots < 64:
        raise ValueError("Use at least 64 shots per quantum invocation")
    if mode not in ("smoke", "quantum"):
        raise ValueError("mode must be smoke or quantum")
    if mode == "quantum" and not quantum_available():
        raise RuntimeError("Qiskit Aer is not installed. Install requirements.txt first.")

    dev_episodes = [create_episode(seed + i) for i in range(dev)]
    test_episodes = [create_episode(seed + 100_000 + i) for i in range(test)]
    random_probability, dev_triggers, dev_eligible = calibrate_random_probability(
        dev_episodes, shots=shots, scenario_count=scenario_count
    )
    step_rows, episode_rows = [], []
    for policy in POLICIES:
        for episode in test_episodes:
            steps, result = run_episode(
                episode,
                policy=policy,
                shots=shots,
                scenario_count=scenario_count,
                random_probability=random_probability,
                max_quantum_calls=max_quantum_calls,
                mode=mode,
            )
            step_rows.extend(steps)
            episode_rows.append(result)

    groups = {p: [r for r in episode_rows if r["policy"] == p] for p in POLICIES}
    classical_by_episode = {r["episode"]: r for r in groups["never"]}
    summary_rows = []
    for p in POLICIES:
        rows = groups[p]
        actual = [r["total_realized_stress"] for r in rows]
        saved_v_classical = [r["total_realized_stress"] - classical_by_episode[r["episode"]]["total_realized_stress"] for r in rows]
        avg, std = mean_and_std(actual)
        paired_mean, paired_std = mean_and_std(saved_v_classical)
        runtime_mean, runtime_std = mean_and_std([r["planning_runtime_seconds"] for r in rows])
        total_eligible = sum(r["eligible_nontrivial_updates"] for r in rows)
        summary_rows.append({
            "policy": p,
            "episodes": len(rows),
            "mean_realized_stress": round(avg, 4),
            "std_realized_stress": round(std, 4),
            "mean_paired_difference_from_classical": round(paired_mean, 4),
            "std_paired_difference_from_classical": round(paired_std, 4),
            "mean_predicted_risk": round(statistics.mean(r["mean_predicted_risk"] for r in rows), 4),
            "mean_local_planning_runtime_seconds": round(runtime_mean, 6),
            "std_local_planning_runtime_seconds": round(runtime_std, 6),
            "total_quantum_calls": sum(r["quantum_calls"] for r in rows),
            "total_completed_quantum_calls": sum(r["quantum_successful_calls"] for r in rows),
            "quantum_call_rate_per_nontrivial_update": round(
                sum(r["quantum_calls"] for r in rows) / max(1, total_eligible), 4
            ),
            "total_quantum_improvements": sum(r["quantum_improvements"] for r in rows),
            "total_shots": sum(r["shots"] for r in rows),
            "total_gate_weighted_shots": sum(r["gate_weighted_shots"] for r in rows),
            "total_two_qubit_gate_shots": sum(r["two_qubit_gate_shots"] for r in rows),
            "total_compiled_gate_shots": sum(r["compiled_gate_shots"] for r in rows),
            "total_classical_evaluations_reported": sum(r["classical_evaluations_reported"] for r in rows),
            "total_planner_score_requests": sum(r["planner_score_requests"] for r in rows),
            "total_planner_loss_scenario_evaluations": sum(r["planner_loss_scenario_evaluations"] for r in rows),
            "total_planner_exact_enumeration_evaluations": sum(r["planner_exact_enumeration_evaluations"] for r in rows),
            "total_offline_exact_evaluations": sum(r["offline_exact_evaluations"] for r in rows),
            "mean_selected_forecast_gap": round(statistics.mean(r["mean_selected_forecast_gap"] for r in rows), 4),
            "mean_classical_forecast_gap": round(statistics.mean(r["mean_classical_forecast_gap"] for r in rows), 4),
            "total_budget_blocked": sum(r["budget_blocked"] for r in rows),
        })

    output.mkdir(parents=True, exist_ok=True)
    save_csv(output / "steps.csv", step_rows)
    save_csv(output / "episodes.csv", episode_rows)
    save_csv(output / "summary.csv", summary_rows)
    metadata = {
        "mode": mode,
        "scientific_status": "EXPLORATORY; NOT a quantum advantage claim",
        "runtime_versions": {"python": sys.version.split()[0], "numpy": np.__version__,
                             "qiskit": installed_version("qiskit"),
                             "qiskit_aer": installed_version("qiskit-aer")},
        "development_episodes": dev,
        "heldout_episodes": test,
        "development_episode_seeds": [e.seed for e in dev_episodes],
        "test_episode_seeds": [e.seed for e in test_episodes],
        "calibrated_random_probability": random_probability,
        "development_triggered": dev_triggers,
        "development_nontrivial_updates": dev_eligible,
        "shots_per_quantum_call": shots,
        "max_quantum_calls_per_trajectory": max_quantum_calls,
        "scenario_count": scenario_count,
        "qiskit_available": quantum_available(),
        "limitations": [
            "Simulated farm model and forecast generator, not agronomically validated",
            "Quantum cost reported in shot counts and gate-weighted shots, not hardware time",
            "The original heuristic's random policy has fixed 0.5 probability; this experiment instead calibrates Bernoulli calls on development episodes",
            "Random and selective invocation rates may differ on held-out episodes; check their observed rates",
            "Extra-classical baseline is the current 8-round local search, not strictly matched to quantum CPU cost",
            "Planner score requests, unique loss vectors, scenario evaluations, and offline exact enumeration are reported separately; none is CPU time or a hardware-equivalent cost",
            "The exact forecast reference for other policies is post-hoc; exact_classical deliberately uses this same current-forecast enumeration as an expensive adaptive classical baseline, without observing future realized weather",
            "Current quantum engine uses p=1 with three fixed pilot parameter combinations; this is not a full variational parameter optimizer",
            "The current empirical CVaR averages the worst ceil(tail_fraction*scenario_count) simulated values (approximation)",
            "Local wall-clock planner runtime is machine- and load-dependent; it is not a quantum hardware timing claim",
            "Quantum mode must yield completed Qiskit circuit calls; smoke mode cannot establish quantum performance",
            "Synthetic truth is revealed only after each policy commits current-window irrigation decisions",
            "Forecast differences between policies arise only from endogenous past irrigation decisions, not different exogenous weather",
        ],
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    report = [
        "# JalQ-R exploratory benchmark report", "",
        f"**Mode:** {mode.upper()}",
        f"**Held-out episodes:** {test}",
        f"**Development episodes:** {dev}",
        f"**Random invocation probability, calibrated on development:** {random_probability:.3f}",
        "", "**Metrics: lower simulated realized moisture stress is better.**", "",
        "| Policy | Mean realized stress ± SD | Δ vs classical (paired) | Forecast gap | Planner seconds / episode (mean ± SD) | Q calls (completed/requested) | Shots | 2Q gate-shots |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        report.append(
            f"| {row['policy']} | {row['mean_realized_stress']:,.1f} ± {row['std_realized_stress']:,.1f} "
            f"| {row['mean_paired_difference_from_classical']:+,.1f} | {row['mean_selected_forecast_gap']:,.2f} | {row['mean_local_planning_runtime_seconds']:.6f} ± {row['std_local_planning_runtime_seconds']:.6f} "
            f"| {row['total_completed_quantum_calls']}/{row['total_quantum_calls']} | {row['total_shots']} | {row['total_two_qubit_gate_shots']} |"
        )
    report.extend([
        "", "Negative paired difference means lower realized moisture stress than classical-only.",
        "Forecast gap is selected-schedule risk minus the exact post-hoc optimum under the same available forecast/scenario model; it is not a future-weather oracle or policy outcome.",
        "", "## Interpretation and limitations", "",
    ])
    if mode == "smoke":
        report.append(
            "**CLASSICAL SMOKE TEST ONLY.** Quantum invocations are not guaranteed to run. "
            "These numbers must not be used as evidence of quantum improvement or resource efficiency."
        )
    else:
        report.append(
            "Qiskit Aer invocations completed. These results are not evidence of "
            "quantum advantage without stronger baselines and statistical evaluation."
        )
    report.extend("- " + note for note in metadata["limitations"])
    report.append("\nRepeat the quantum benchmark with multiple seeds before using it in a presentation.\n")
    (output / "report.md").write_text("\n".join(report), encoding="utf-8")
    return {"random_probability": random_probability, "summary": summary_rows, "output": str(output)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["smoke", "quantum"], default="smoke",
                        help="smoke checks workflow; quantum enforces actual Qiskit execution")
    parser.add_argument("--dev", type=int, default=4, help="number of calibration episodes")
    parser.add_argument("--test", type=int, default=6, help="number of held-out episodes")
    parser.add_argument("--shots", type=int, default=384, help="shots per Qiskit invocation; minimum 64")
    parser.add_argument("--scenario-count", type=int, default=15, help="weather scenarios in risk evaluation")
    parser.add_argument("--max-quantum-calls", type=int, default=3, help="per episode for all quantum policies")
    parser.add_argument("--seed", type=int, default=20261021, help="reproducible experiment seed")
    parser.add_argument("--output", type=Path, default=Path("results") / "benchmark")
    args = parser.parse_args()
    result = benchmark(dev=args.dev, test=args.test, shots=args.shots,
                       scenario_count=args.scenario_count,
                       max_quantum_calls=args.max_quantum_calls,
                       seed=args.seed, mode=args.mode, output=args.output)
    print(f"Development-calibrated random invocation probability: {result['random_probability']:.3f}")
    for row in result["summary"]:
        print(f"{row['policy']:>16} | actual stress {row['mean_realized_stress']:>11,.2f} "
              f"| quantum calls {row['total_completed_quantum_calls']}/{row['total_quantum_calls']:>3} "
              f"| shots {row['total_shots']:>6}")
    print(f"Saved benchmark output in: {result['output']}")
    if args.mode == "smoke":
        print("WARNING: SMOKE MODE is not quantum-performance evidence. Use --mode quantum with Qiskit installed.")


if __name__ == "__main__":
    main()
