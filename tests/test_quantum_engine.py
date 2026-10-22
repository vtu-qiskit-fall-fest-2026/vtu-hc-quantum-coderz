"""Actual Aer execution checks; skipped when optional quantum deps are absent."""
import pytest

pytest.importorskip("qiskit")
pytest.importorskip("qiskit_aer")

from experiments import create_episode, request_for
from planner import Planner
from quantum_engine import build_qaoa_circuit, qaoa_candidate


def test_qaoa_circuit_transpiles_and_aer_returns_feasible_candidate():
    episode = create_episode(20261022)
    request = request_for(
        episode, 0, [29.0, 23.0, 25.0], [[0] * 4 for _ in range(3)], None,
        policy="never", shots=128, scenario_count=5,
    )
    planner = Planner(request)
    seed = planner.candidates()[0]["bits"]
    circuit = build_qaoa_circuit(planner, seed, gamma=0.8, beta=0.35)
    assert circuit.num_qubits == planner.n
    assert circuit.num_clbits == planner.n

    result = qaoa_candidate(planner, seed, shots=128)
    assert result["status"] == "completed"
    assert result["shots"] == 128
    assert result["circuit_evaluations"] == 4
    assert result["candidate_bits"] is not None
    assert planner.feasible(result["candidate_bits"])
    assert result["raw_feasibility_rate"] == 1.0
    assert result["compiled_gate_shots"] >= result["two_qubit_gate_shots"] > 0


def test_aer_shot_allocation_is_exact_at_minimum_and_default():
    from quantum_engine import allocate_shots

    assert sum(allocate_shots(64)) == 64
    assert sum(allocate_shots(384)) == 384
