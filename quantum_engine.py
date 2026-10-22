"""Optional, genuine Qiskit Aer candidate-generation branch.

No quantum outputs are fabricated when Qiskit/Aer are unavailable.
Optimization uses EXPECTED quadratic stress. CVaR is ranked classically by planner.
"""
import importlib.util
import numpy as np

def quantum_available():
    return importlib.util.find_spec('qiskit') is not None and importlib.util.find_spec('qiskit_aer') is not None

def coefficients_to_pauli(c,a,b):
    """x=(I-Z)/2; E=c+sum(a_i x_i)+sum(b_ij x_i x_j)."""
    h=-np.asarray(a,dtype=float)/2
    z2=np.zeros_like(b,dtype=float)
    offset=float(c+sum(a)/2)
    for i in range(len(a)):
        for j in range(i+1,len(a)):
            v=float(b[i,j]); offset+=v/4
            h[i]-=v/4;h[j]-=v/4;z2[i,j]=v/4
    return offset,h,z2

def allocate_shots(shots, pilot_count=3):
    """Split one positive integer shot budget across pilots and validation.

    Small configured budgets are valid too: pilots shrink to one shot instead
    of silently exceeding the caller's budget.
    """
    if isinstance(pilot_count,bool) or not isinstance(pilot_count,(int,np.integer)) or pilot_count < 1:
        raise ValueError('Pilot count must be a positive integer')
    if isinstance(shots, bool) or not isinstance(shots, (int, np.integer)) or shots < pilot_count + 1:
        raise ValueError('Shot budget must allow at least one shot per pilot and one validation shot')
    shots=int(shots);pilot_count=int(pilot_count)
    pilot = max(1, shots // 8)
    while pilot_count * pilot >= shots:
        pilot -= 1
    return [pilot] * pilot_count + [shots - pilot_count * pilot]

def decode_qiskit_bitstring(bitstring, width):
    """Convert Qiskit's displayed most-significant-first count key to x[i]."""
    compact=bitstring.replace(' ','')
    if len(compact)>width or any(bit not in '01' for bit in compact):
        raise ValueError('Measurement key does not match the circuit width')
    return tuple(int(bit) for bit in compact.zfill(width)[::-1])

def build_qaoa_circuit(planner, seed_bits, gamma, beta):
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import XXPlusYYGate
    n=planner.n
    if not planner.feasible(seed_bits):raise ValueError('Quantum seed must be feasible')
    c,a,b=planner.expected_qubo()
    _, h, j = coefficients_to_pauli(c,a,b)
    scale=max(1.,max(abs(float(v)) for v in [*a,*b.flat]))
    qc=QuantumCircuit(n)
    for i, bit in enumerate(seed_bits):
        if bit:qc.x(i)
    # One shallow fixed-weight preparation layer; n>1 assured by caller.
    for i in range(0,n-1,2):qc.append(XXPlusYYGate(0.75), [i,i+1])
    for i in range(n):
        if abs(h[i])>1e-9:qc.rz(2*gamma*h[i]/scale,i)
    for i in range(n):
        for k in range(i+1,n):
            if abs(j[i,k])>1e-9:qc.rzz(2*gamma*j[i,k]/scale,i,k)
    # Connected XY mixer: staggered edges can reach all weight-K strings.
    for parity in (0,1):
        for i in range(parity,n-1,2):qc.append(XXPlusYYGate(2*beta),[i,i+1])
    qc.measure_all()
    return qc

def qaoa_candidate(planner,seed_bits,shots=384):
    # Three pilot parameter sets with a held-out validation sample.
    shot_allocation=allocate_shots(shots)
    final_shots=shot_allocation[-1]
    best_score=float('inf');best_params=None;best_bits=None
    two_qubit_gate_shots=0;compiled_gate_shots=0;largest_depth=0;max_2q=0;evals=0;valid_counts=0;shots_used=0
    phases=[(0.8,0.35),(1.8,0.8),(3.4,1.15)]
    try:
        from qiskit import transpile
        from qiskit_aer import AerSimulator
        simulator=AerSimulator()
        rng=np.random.default_rng(planner.r.seed+919)

        def execute(gamma,beta,number):
            nonlocal two_qubit_gate_shots,compiled_gate_shots,largest_depth,max_2q,evals,valid_counts,best_bits,best_score,shots_used
            circuit=build_qaoa_circuit(planner,seed_bits,gamma,beta)
            compiled=transpile(circuit,basis_gates=['rz','sx','x','cx','measure'],optimization_level=1,seed_transpiler=7)
            twoq=int(compiled.count_ops().get('cx',0))
            all_gates=sum(int(count) for gate,count in compiled.count_ops().items() if gate!='measure' and gate!='barrier')
            largest_depth=max(largest_depth,compiled.depth())
            max_2q=max(max_2q,twoq)
            two_qubit_gate_shots+=twoq*number
            compiled_gate_shots+=all_gates*number
            # Charge a submitted backend request even if execution subsequently fails.
            shots_used+=number;evals+=1
            result=simulator.run(compiled,shots=number,seed_simulator=int(rng.integers(1,2**31))).result()
            counts=result.get_counts()
            total_weight=0.;valid=0;sample_winner=None;sample_winner_risk=float('inf')
            for key, nshots in counts.items():
                bits=decode_qiskit_bitstring(key,planner.n)
                if not planner.feasible(bits):continue
                valid+=nshots
                # Quantum tuning uses expected stress surrogate, not CVaR.
                surrogate=float(planner.loss_vector(bits)[0].mean())
                total_weight+=nshots*surrogate
                risk=planner.score(bits)['risk']
                if risk<sample_winner_risk:sample_winner_risk=risk;sample_winner=bits
            valid_counts+=valid
            if sample_winner is not None:
                if best_bits is None or sample_winner_risk < planner.score(best_bits)['risk']:
                    best_bits=sample_winner
            return total_weight/max(1,valid) if valid else float('inf')
        for params, number in zip(phases, shot_allocation[:-1]):
            score=execute(*params,number)
            if score<best_score:best_score=score;best_params=params
        if best_params is None:best_params=phases[0]
        execute(*best_params,final_shots)
        return {'status':'completed','candidate_bits':best_bits,'shots':shots_used,
            'circuit_evaluations':evals,'gate_weighted_shots':two_qubit_gate_shots,
            'two_qubit_gate_shots':two_qubit_gate_shots,'compiled_gate_shots':compiled_gate_shots,
            'two_qubit_gates':max_2q,'depth':largest_depth,
            'raw_feasibility_rate':round(valid_counts/max(1,shots_used),3),
            'candidates':1 if best_bits is not None else 0,
            'method':'Qiskit Aer, seed-based XY QAOA p=1; expected-stress surrogate'}
    except Exception as exc:
        return {'status':'execution_error','candidate_bits':None,'error':str(exc)[:220],
            'shots':shots_used,'circuit_evaluations':evals,
            'gate_weighted_shots':two_qubit_gate_shots,
            'two_qubit_gate_shots':two_qubit_gate_shots,'compiled_gate_shots':compiled_gate_shots,
            'two_qubit_gates':max_2q,
            'depth':largest_depth,'candidates':0}

