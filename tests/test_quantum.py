"""Quantum implementation checks. Simulation checks skip if Qiskit is absent."""
import itertools

import numpy as np
import pytest

from planner import FarmRequest, Planner, decide
from quantum_engine import (
    coefficients_to_pauli, counts_key_to_bits, fixed_qaoa_candidate,
    qaoa_candidate, quantum_available, shot_plan,
)


def example_planner(seed=7, shots=128):
    req = FarmRequest(
        moisture=[29, 23, 25], target=[42, 40, 44],
        priority=[1.3, 1.0, 1.5], rain=[3, 0, 4, 1],
        evaporation=[4, 5, 4, 5],
        available=[[1, 1, 0, 1], [1, 0, 1, 0], [0, 1, 1, 1]],
        executed=[[0] * 4 for _ in range(3)],
        quota=3, scenario_count=7, seed=seed, quantum_shots=shots,
    )
    return Planner(req)


def test_counts_order():
    assert counts_key_to_bits("1010", 4) == (0, 1, 0, 1)
    assert counts_key_to_bits("0x5", 4) == (1, 0, 1, 0)
    with pytest.raises(ValueError):
        counts_key_to_bits("10000", 4)


def test_shot_plans_reserve_final_sample():
    assert shot_plan(384, "cobyla") == [32] * 8
    assert shot_plan(384, "fixed") == [48] * 3
    for shots in (64, 128, 192, 384, 1000):
        for mode in ("fixed", "cobyla"):
            plan = shot_plan(shots, mode)
            assert all(v > 0 for v in plan)
            assert shots - sum(plan) >= 32
    with pytest.raises(ValueError):
        shot_plan(31, "cobyla")


def test_phase_matches_expected_qubo():
    planner = example_planner()
    c, a, b = planner.expected_qubo()
    offset, h, j = coefficients_to_pauli(c, a, b)
    for bits in itertools.product((0, 1), repeat=planner.n):
        x = np.asarray(bits)
        z = 1 - 2 * x
        expected = float(planner.loss_vector(bits)[0].mean())
        phase = offset + float(h @ z) + float(z @ j @ z)
        assert np.isclose(expected, phase, rtol=1e-9, atol=1e-6)


@pytest.mark.skipif(not quantum_available(), reason="Qiskit Aer unavailable")
def test_cobyla_budget_feasibility_and_diagnostics():
    planner = example_planner(seed=7, shots=384)
    classical_seed = planner.candidates()[0]["bits"]
    result = qaoa_candidate(planner, classical_seed, shots=384)
    assert result["status"] == "completed", result.get("error")
    assert result["shots"] == 384
    assert result["circuit_evaluations"] == result["optimizer_evaluations"] + 1
    assert 4 <= result["optimizer_evaluations"] <= 8
    assert result["final_shots"] >= 32
    assert sum(h["shots"] for h in result["parameter_history"]) == 384
    assert result["gate_weighted_shots"] > 0
    assert result["raw_feasibility_rate"] == 1.0
    assert result["unique_feasible_schedules"] >= 1
    assert result["optimizer"] == "COBYLA"
    assert np.isfinite(result["optimized_gamma"])
    assert np.isfinite(result["optimized_beta"])
    assert result["candidate_bits"] is not None
    assert planner.feasible(result["candidate_bits"])
    assert result["best_candidate_risk"] >= 0


@pytest.mark.skipif(not quantum_available(), reason="Qiskit Aer unavailable")
def test_fixed_baseline_same_shots():
    planner = example_planner(shots=128)
    seed = planner.candidates()[0]["bits"]
    result = fixed_qaoa_candidate(planner, seed, shots=128)
    assert result["status"] == "completed", result.get("error")
    assert result["shots"] == 128
    assert result["circuit_evaluations"] == 4
    assert result["optimizer"] == "fixed_grid"
    assert result["raw_feasibility_rate"] == 1.0
    assert planner.feasible(result["candidate_bits"])


@pytest.mark.skipif(not quantum_available(), reason="Qiskit Aer unavailable")
def test_existing_decide_contract():
    planner = example_planner(shots=128)
    planner.r.policy = "always"
    result = decide(planner.r)
    assert result["quantum_invoked"] is True
    assert result["quantum"]["status"] == "completed", result["quantum"].get("error")
    assert result["quantum"]["shots"] == 128
    assert sum(sum(row) for row in result["schedule"]) == 3
    assert "candidate_bits" not in result["quantum"]
