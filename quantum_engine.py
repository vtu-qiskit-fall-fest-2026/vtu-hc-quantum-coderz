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
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    simulator=AerSimulator()
    rng=np.random.default_rng(planner.r.seed+919)
    # Three pilot parameter sets with a held-out validation sample.
    pilot_shots=max(32,shots//8)
    final_shots=shots-3*pilot_shots
    if final_shots<32:raise ValueError('Insufficient quantum shots')
    best_score=float('inf');best_params=None;best_bits=None
    total_gates=0;largest_depth=0;max_2q=0;evals=0;valid_counts=0
    phases=[(0.8,0.35),(1.8,0.8),(3.4,1.15)]
    def execute(gamma,beta,number):
        nonlocal total_gates,largest_depth,max_2q,evals,valid_counts,best_bits,best_score
        circuit=build_qaoa_circuit(planner,seed_bits,gamma,beta)
        compiled=transpile(circuit,basis_gates=['rz','sx','x','cx','measure'],optimization_level=1,seed_transpiler=7)
        twoq=int(compiled.count_ops().get('cx',0))
        largest_depth=max(largest_depth,compiled.depth())
        max_2q=max(max_2q,twoq)
        total_gates+=twoq*number
        result=simulator.run(compiled,shots=number,seed_simulator=int(rng.integers(1,2**31))).result()
        counts=result.get_counts();evals+=1
        total_weight=0.;valid=0;sample_winner=None;sample_winner_risk=float('inf')
        for key, nshots in counts.items():
            bits=[int(v) for v in key.replace(' ','').zfill(planner.n)[::-1]]
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
    try:
        for params in phases:
            score=execute(*params,pilot_shots)
            if score<best_score:best_score=score;best_params=params
        if best_params is None:best_params=phases[0]
        execute(*best_params,final_shots)
        return {'status':'completed','candidate_bits':best_bits,'shots':shots,
            'circuit_evaluations':evals,'gate_weighted_shots':total_gates,
            'two_qubit_gates':max_2q,'depth':largest_depth,
            'raw_feasibility_rate':round(valid_counts/max(1,shots),3),
            'candidates':1 if best_bits is not None else 0,
            'method':'Qiskit Aer, seed-based XY QAOA p=1; expected-stress surrogate'}
    except Exception as exc:
        return {'status':'execution_error','candidate_bits':None,'error':str(exc)[:220],
            'shots':sum([pilot_shots]*evals),'circuit_evaluations':evals,
            'gate_weighted_shots':total_gates,'two_qubit_gates':max_2q,
            'depth':largest_depth,'candidates':0}

