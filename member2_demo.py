"""JalQ-R Member 2: run the extended synthetic farm model directly.

python member2_demo.py
python member2_demo.py --quantum

Does not modify server.py or experiments.py; calls the existing FarmRequest API.
"""
import argparse
from planner import FarmRequest, Planner, decide


def make_farm(policy):
    return FarmRequest(
        moisture=[29., 23., 25.],
        target=[42., 40., 44.],
        priority=[1.3, 1., 1.5],
        rain=[3., 0., 4., 1.],
        evaporation=[4., 5., 4., 5.],
        available=[[1, 1, 0, 1], [1, 0, 1, 0], [0, 1, 1, 1]],
        executed=[[0] * 4 for _ in range(3)],
        rain_by_field=[[3., 0., 5., 2.], [1., 4., 0., 3.], [5., 2., 1., 0.]],
        evaporation_by_field=[[4., 5., 4., 5.], [3., 4., 5., 4.], [5., 6., 5., 6.]],
        target_by_window=[[40., 42., 45., 43.],
                          [38., 41., 43., 40.],
                          [44., 46., 47., 45.]],
        quota=3, uncertainty=2., risk_weight=.35, alpha=.8,
        scenario_count=7, seed=11, policy=policy, quantum_shots=128,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--quantum', action='store_true', help='Run COBYLA with Qiskit Aer')
    args = parser.parse_args()
    r = make_farm('always' if args.quantum else 'never')
    planner = Planner(r)
    result = decide(r)
    exact = planner.evaluate_exact_offline()  # Diagnostic ONLY, never used by decide().
    c, a, b = planner.expected_qubo()
    print('Mode:', r.policy)
    print('Weather scenario shape:', planner.rain_scenarios.shape)
    print('Target matrix shape:', planner.target_matrix.shape)
    print('Eligible decision qubits:', planner.n)
    print('Selected irrigation events:', sum(map(sum, result['schedule'])))
    print('Classical baseline risk:', result['classical_baseline']['risk'])
    print('Final risk:', result['objective']['risk'])
    print('Offline exact optimum:', round(exact['risk'], 4))
    print('Expected-stress QUBO terms:', len(a), int((b != 0).sum()))
    print('Schedule:', result['schedule'])
    if args.quantum:
        print('Quantum status:', result['quantum']['status'])
        print('Quantum optimizer:', result['quantum'].get('optimizer'))
        print('Quantum shots:', result['quantum'].get('shots'))
        print('Quantum error:', result['quantum'].get('error'))
        if result['quantum']['status'] != 'completed':
            raise RuntimeError('Requested quantum simulation did not complete')


if __name__ == '__main__':
    main()
