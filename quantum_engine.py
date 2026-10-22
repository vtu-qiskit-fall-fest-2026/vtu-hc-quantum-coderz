"""JalQ-R: shot-budgeted QAOA on Qiskit Aer.

Expected quadratic stress drives the QAOA phase and parameter optimization.
The full CVaR-based risk is evaluated CLASSICALLY for observed bitstrings.
This module never invokes the offline exact-optimum enumerator.

Public compatibility contract:
    build_qaoa_circuit(planner, seed_bits, gamma, beta)
    qaoa_candidate(planner, seed_bits, shots=384)

Research modes:
    qaoa_candidate: COBYLA proposals, fixed total circuit-shot budget.
    fixed_qaoa_candidate: original 3-point parameter search at same shot budget.
"""
from __future__ import annotations

import importlib.util
from collections import Counter

import numpy as np


INITIAL_PARAMS = (0.8, 0.35)
FIXED_PARAMS = ((0.8, 0.35), (1.8, 0.8), (3.4, 1.15))
BASIS_GATES = ["rz", "sx", "x", "cx", "measure"]


def quantum_available():
    """Whether the Qiskit runtime imports appear available (not a run guarantee)."""
    return (
        importlib.util.find_spec("qiskit") is not None
        and importlib.util.find_spec("qiskit_aer") is not None
    )


def coefficients_to_pauli(c, a, b):
    """Map upper-triangular QUBO into H=offset+sum(h_i Z_i)+sum(j_ij Z_i Z_j).

    The original project convention stores b_ij ONLY for i<j, and evaluates
    c + a @ x + x @ b @ x. Keep that convention for Member 2 integration.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    h = -a / 2.0
    j = np.zeros_like(b, dtype=float)
    offset = float(c + a.sum() / 2.0)
    for i in range(len(a)):
        for k in range(i + 1, len(a)):
            v = float(b[i, k])
            offset += v / 4.0
            h[i] -= v / 4.0
            h[k] -= v / 4.0
            j[i, k] = v / 4.0
    return offset, h, j


def counts_key_to_bits(key, n):
    """Qiskit counts show most-significant measured bit on the LEFT.

    Returns (q0, q1, ..., q[n-1]) in the planner's bit ordering.
    """
    key = str(key).replace(" ", "")
    value = int(key, 16) if key.lower().startswith("0x") else int(key, 2)
    if value < 0 or value >= 2**n:
        raise ValueError("Measurement key is outside the circuit's qubit range")
    return tuple((value >> i) & 1 for i in range(n))


def build_qaoa_circuit(planner, seed_bits, gamma, beta):
    """Feasible seed + shallow XY exploration + expected-stress QAOA p=1."""
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import XXPlusYYGate

    if not planner.feasible(seed_bits):
        raise ValueError("Quantum seed must have exactly the remaining quota")
    n = planner.n
    c, a, b = planner.expected_qubo()
    _, h, j = coefficients_to_pauli(c, a, b)
    scale = max(1.0, float(np.max(np.abs(a))), float(np.max(np.abs(b))))

    qc = QuantumCircuit(n)
    for i, bit in enumerate(seed_bits):
        if bit:
            qc.x(i)

    # Pre-phase exploration; XXPlusYY preserves Hamming weight in the ideal model.
    for i in range(0, n - 1, 2):
        qc.append(XXPlusYYGate(0.75), [i, i + 1])

    for i in range(n):
        if abs(h[i]) > 1e-9:
            qc.rz(2.0 * float(gamma) * float(h[i]) / scale, i)
    for i in range(n):
        for k in range(i + 1, n):
            if abs(j[i, k]) > 1e-9:
                qc.rzz(2.0 * float(gamma) * float(j[i, k]) / scale, i, k)

    for parity in (0, 1):
        for i in range(parity, n - 1, 2):
            qc.append(XXPlusYYGate(2.0 * float(beta)), [i, i + 1])
    qc.measure_all()
    return qc


def shot_plan(shots, method):
    """Return pilot sizes; the remaining shots are reserved for final sampling.

    At 384 shots, COBYLA gets UP TO 8x32-shot evaluations and AT LEAST 128 final shots.
    At 384 shots, FIXED gets 3x48-shot evaluations + 240 final shots.
    """
    shots = int(shots)
    if shots < 64:
        raise ValueError("At least 64 shots are required")
    if method == "cobyla":
        # A 32-shot final execution is guaranteed even at the minimum budget.
        return [32] * min(8, (shots - 32) // 32)
    if method == "fixed":
        pilot = max(8, shots // 8)
        if shots - 3 * pilot < 32:
            pilot = (shots - 32) // 3
        return [pilot] * 3
    raise ValueError("Unknown QAOA method")


def _run_candidate(planner, seed_bits, shots, method):
    if not planner.feasible(seed_bits):
        raise ValueError("Quantum seed must be feasible")
    if planner.n < 2 or planner.k == 0 or planner.k == planner.n:
        return {
            "status": "skipped_trivial", "candidate_bits": None,
            "shots": 0, "circuit_evaluations": 0,
            "gate_weighted_shots": 0, "two_qubit_gates": 0,
            "depth": 0, "candidates": 0, "method": method,
        }
    from qiskit import transpile
    from qiskit_aer import AerSimulator

    # Import scipy in the optimizer mode so the fixed baseline stays independent.
    if method == "cobyla":
        from scipy.optimize import minimize

    shots = int(shots)
    pilots = shot_plan(shots, method)
    rng = np.random.default_rng(planner.r.seed + 919)
    simulator = AerSimulator()

    attempted = 0
    valid_shots = 0
    circuit_evaluations = 0
    gate_weighted_shots = 0
    depth_max = 0
    two_qubit_max = 0
    best_bits = None
    best_risk = float("inf")
    all_counts = Counter()
    surrogate_cache = {}
    risk_cache = {}
    parameter_history = []
    optimizer_evaluations = 0
    best_pilot_score = float("inf")
    best_parameters = tuple(INITIAL_PARAMS)

    def get_cost(bits):
        if bits not in surrogate_cache:
            surrogate_cache[bits] = float(planner.loss_vector(bits)[0].mean())
        return surrogate_cache[bits]

    def get_risk(bits):
        if bits not in risk_cache:
            # These are post-measurement evaluations, not a QAOA phase term.
            risk_cache[bits] = float(planner.score(bits, track=False)["risk"])
        return risk_cache[bits]

    def execute(params, number, stage):
        nonlocal attempted, valid_shots, circuit_evaluations
        nonlocal gate_weighted_shots, depth_max, two_qubit_max
        nonlocal best_bits, best_risk

        number = int(number)
        if number <= 0 or attempted + number > shots:
            raise AssertionError("Quantum shot budget would be exceeded")

        gamma, beta = (float(params[0]), float(params[1]))
        circuit = build_qaoa_circuit(planner, seed_bits, gamma, beta)
        compiled = transpile(
            circuit,
            basis_gates=BASIS_GATES,
            optimization_level=1,
            seed_transpiler=7,
        )
        twoq = int(compiled.count_ops().get("cx", 0))
        depth = int(compiled.depth())
        # Count every submitted circuit shot, including failed jobs.
        job = simulator.run(
            compiled,
            shots=number,
            seed_simulator=int(rng.integers(1, 2**31)),
        )
        attempted += number
        circuit_evaluations += 1
        gate_weighted_shots += twoq * number
        depth_max = max(depth_max, depth)
        two_qubit_max = max(two_qubit_max, twoq)
        counts = job.result().get_counts()
        if sum(int(n) for n in counts.values()) != number:
            raise RuntimeError("Aer returned a measurement count inconsistent with the shot budget")

        valid = 0
        weighted_surrogate = 0.0
        distinct = set()
        for bitstring, count in counts.items():
            bits = counts_key_to_bits(bitstring, planner.n)
            if not planner.feasible(bits):
                continue
            count = int(count)
            valid += count
            valid_shots += count
            distinct.add(bits)
            all_counts[bits] += count
            weighted_surrogate += count * get_cost(bits)
            risk = get_risk(bits)
            if risk < best_risk - 1e-10:
                best_bits = bits
                best_risk = risk

        mean_valid = weighted_surrogate / valid if valid else None
        # Retain feasible-only sample mean for interpretation. Penalize invalid
        # measurements for optimization rather than silently discarding them.
        objective = (
            mean_valid + (number - valid) / number * max(1.0, abs(mean_valid))
            if valid else 1e12
        )
        record = {
            "stage": stage, "gamma": gamma, "beta": beta,
            "shots": number, "valid_shots": valid,
            "unique_feasible_schedules": len(distinct),
            "mean_sampled_expected_stress": mean_valid,
            "objective_value": float(objective),
            "two_qubit_gates": twoq, "depth": depth,
        }
        parameter_history.append(record)
        return float(objective)

    optimization_message = ""
    optimizer_success = False
    try:
        if method == "fixed":
            for params, count in zip(FIXED_PARAMS, pilots):
                observed = execute(params, count, "fixed_pilot")
                optimizer_evaluations += 1
                if observed < best_pilot_score:
                    best_pilot_score = observed
                    best_parameters = tuple(params)
            optimization_message = "Three original fixed parameter trials"
            optimizer_success = True
        else:
            if len(pilots) < 4:
                # Very low budget: do not pretend that COBYLA was able to tune.
                execute(INITIAL_PARAMS, pilots[0], "pilot_low_budget")
                optimizer_evaluations = 1
                best_parameters = tuple(INITIAL_PARAMS)
                optimization_message = "Too few pilot evaluations for SciPy COBYLA; used initial angles"
            else:
                def objective(params):
                    nonlocal optimizer_evaluations, best_pilot_score, best_parameters
                    if optimizer_evaluations >= len(pilots):
                        raise RuntimeError("COBYLA attempted to exceed the allocated pilot budget")
                    score = execute(params, pilots[optimizer_evaluations], "cobyla_pilot")
                    optimizer_evaluations += 1
                    if score < best_pilot_score:
                        best_pilot_score = score
                        best_parameters = (float(params[0]), float(params[1]))
                    return score

                result = minimize(
                    objective,
                    x0=np.asarray(INITIAL_PARAMS, dtype=float),
                    method="COBYLA",
                    options={"maxiter": len(pilots), "rhobeg": 0.35, "tol": 0.001},
                )
                optimizer_success = bool(result.success)
                optimization_message = str(result.message)

        final_shots = shots - attempted
        if final_shots < 32:
            raise AssertionError("Final sampling was not allocated at least 32 shots")
        execute(best_parameters, final_shots, "final")
        if attempted != shots:
            raise AssertionError("Not all allocated circuit shots were accounted for")

        first_mean = parameter_history[0]["mean_sampled_expected_stress"]
        last = parameter_history[-1]
        final_mean = last["mean_sampled_expected_stress"]
        pooled_mean = (
            sum(get_cost(bits) * n for bits, n in all_counts.items()) / valid_shots
            if valid_shots else None
        )
        return {
            "status": "completed",
            "candidate_bits": best_bits,
            "shots": attempted,
            "circuit_evaluations": circuit_evaluations,
            "gate_weighted_shots": gate_weighted_shots,
            "two_qubit_gates": two_qubit_max,
            "depth": depth_max,
            "raw_feasibility_rate": round(valid_shots / attempted, 6),
            "candidates": 1 if best_bits is not None else 0,
            "unique_feasible_schedules": len(all_counts),
            "best_candidate_risk": float(best_risk) if best_bits is not None else None,
            "mean_sampled_expected_stress": pooled_mean,
            "initial_mean_sampled_expected_stress": first_mean,
            "final_mean_sampled_expected_stress": final_mean,
            "final_unique_feasible_schedules": last["unique_feasible_schedules"],
            "optimized_gamma": best_parameters[0],
            "optimized_beta": best_parameters[1],
            "optimizer": "COBYLA" if method == "cobyla" else "fixed_grid",
            "optimizer_success": optimizer_success,
            "optimizer_message": optimization_message,
            "optimizer_evaluations": optimizer_evaluations,
            "final_shots": last["shots"],
            "parameter_history": parameter_history,
            "top_sampled_schedules": [
                {"bits": "".join(map(str, bits)), "count": count, "risk": get_risk(bits)}
                for bits, count in all_counts.most_common(5)
            ],
            "method": (
                "Qiskit Aer, XY-QAOA p=1, COBYLA pilots, expected-stress surrogate"
                if method == "cobyla" else
                "Qiskit Aer, XY-QAOA p=1, three fixed pilot angles, expected-stress surrogate"
            ),
        }
    except Exception as exc:
        return {
            "status": "execution_error",
            "candidate_bits": None,
            "error": str(exc)[:350],
            "shots": attempted,
            "circuit_evaluations": circuit_evaluations,
            "gate_weighted_shots": gate_weighted_shots,
            "two_qubit_gates": two_qubit_max,
            "depth": depth_max,
            "raw_feasibility_rate": round(valid_shots / max(1, attempted), 6),
            "candidates": 0,
            "optimizer": "COBYLA" if method == "cobyla" else "fixed_grid",
            "optimizer_evaluations": optimizer_evaluations,
            "parameter_history": parameter_history,
            "method": method,
        }


def qaoa_candidate(planner, seed_bits, shots=384):
    """New Member 1 algorithm. Signature remains compatible with planner.py."""
    return _run_candidate(planner, seed_bits, shots, "cobyla")


def fixed_qaoa_candidate(planner, seed_bits, shots=384):
    """Old-method comparison using exactly the same *total* measurement budget."""
    return _run_candidate(planner, seed_bits, shots, "fixed")
