"""Tests for future-information isolation and benchmark reproducibility."""

from experiments import create_episode, request_for, run_episode, calibrate_random_probability


def test_episode_reproducible():
    a = create_episode(42)
    assert create_episode(42) == a
    assert a != create_episode(43)
    assert len(a.forecasts_rain) == 4


def test_request_contains_current_forecast_not_truth():
    episode = create_episode(79)
    req = request_for(
        episode, 1, [29, 23, 25], [[0] * 4 for _ in range(3)], None,
        policy="never", shots=384, scenario_count=5
    )
    assert req.rain == list(episode.forecasts_rain[1])
    assert req.rain[1:] != list(episode.actual_rain[1:])


def test_rolling_horizon_smoke_uses_exact_three_events():
    episode = create_episode(99)
    steps, result = run_episode(episode, policy="never", shots=384,
                                scenario_count=5, random_probability=0.0,
                                max_quantum_calls=0, mode="smoke")
    assert len(steps) == 4
    assert result["irrigation_events"] == 3
    assert result["shots"] == 0
    assert all(r["quantum_invoked"] == 0 for r in steps)
    assert all(r["selected_forecast_gap"] >= 0 for r in steps)
    assert all(r["offline_exact_evaluations"] >= 1 for r in steps)
    assert all(r["planner_loss_scenario_evaluations"] > 0 for r in steps)
    assert result["planner_loss_scenario_evaluations"] == sum(
        r["planner_loss_scenario_evaluations"] for r in steps
    )


def test_exact_classical_policy_matches_current_forecast_optimum():
    from planner import decide

    episode = create_episode(340)
    request = request_for(
        episode, 0, [29.0, 23.0, 25.0], [[0] * 4 for _ in range(3)], None,
        policy="exact_classical", shots=384, scenario_count=5,
    )
    plan = decide(request, offline_evaluation=True)
    assert plan["policy"] == "exact_classical"
    assert plan["objective"]["risk"] == plan["offline_evaluation"]["optimal_risk"]
    assert plan["planner_work"]["exact_enumeration_evaluations"] > 0
    assert plan["quantum"]["status"] == "not_requested"


def test_calibration_uses_only_dev_episode_data():
    episodes = [create_episode(200), create_episode(201)]
    p, on, valid = calibrate_random_probability(episodes, shots=384, scenario_count=5)
    assert 0 <= p <= 1
    assert on <= valid


def test_same_episode_same_policy_reproducible_without_quantum():
    episode = create_episode(102)
    kwargs = dict(policy="never", shots=384, scenario_count=5,
                  random_probability=0, max_quantum_calls=0, mode="smoke")
    a, x = run_episode(episode, **kwargs)
    b, y = run_episode(episode, **kwargs)
    for row in a + b:
        assert row["planning_runtime_seconds"] >= 0
        row.pop("planning_runtime_seconds")
    x.pop("planning_runtime_seconds")
    y.pop("planning_runtime_seconds")
    assert a == b
    assert x == y
