import itertools
import numpy as np
import pytest
from fastapi.testclient import TestClient
from server import app
from planner import Planner, FarmRequest, decide
from quantum_engine import allocate_shots, coefficients_to_pauli, decode_qiskit_bitstring

@pytest.fixture
def farm_request():
    return FarmRequest(moisture=[29,23,25],target=[42,40,44],priority=[1.3,1,1.5],rain=[3,0,4,1],evaporation=[4,5,4,5],available=[[1,1,0,1],[1,0,1,0],[0,1,1,1]],executed=[[0]*4 for _ in range(3)])

def test_fixed_quota(farm_request):
    p=Planner(farm_request)
    for candidate in p.candidates():
        assert p.feasible(candidate['bits'])
        assert sum(candidate['bits'])==3

def test_scenario_range_bounds_expected_trajectory(farm_request):
    p=Planner(farm_request)
    bits=p.candidates()[0]['bits']
    bounds=p.trajectory_range(bits)
    assert np.asarray(bounds['lower']).shape==(3,4)
    assert np.all(np.asarray(bounds['lower'])<=np.asarray(bounds['upper']))

def test_quadratic_expectation_exact(farm_request):
    p=Planner(farm_request)
    c,a,b=p.expected_qubo()
    offset,h,j=coefficients_to_pauli(c,a,b)
    for bits in itertools.product((0,1),repeat=p.n):
        x=np.asarray(bits)
        expected=float(p.loss_vector(bits)[0].mean())
        direct=c+float(a@x)+float(x@b@x)
        z=1-2*x
        phase=offset+float(h@z)+float(z@j@z)
        assert abs(expected-direct)<1e-7
        assert abs(phase-expected)<1e-7

def test_exact_isolation(farm_request,monkeypatch):
    def forbidden(_):raise AssertionError('Online planner used evaluation oracle')
    monkeypatch.setattr(Planner,'evaluate_exact_offline',forbidden)
    d=decide(farm_request)
    assert 'offline_evaluation' not in d

def test_rolling_horizon_freezes_past(farm_request):
    initial=decide(farm_request)
    old=initial['schedule']
    farm_request.start_window=1
    farm_request.previous_plan=old
    farm_request.previous_rain=list(farm_request.rain)
    for i in range(3):
        farm_request.executed[i][0]=old[i][0]
        farm_request.moisture[i]+=farm_request.rain[0]-farm_request.evaporation[0]+farm_request.irrigation_gain*old[i][0]
    farm_request.rain[1]=8
    updated=decide(farm_request)
    for i in range(3): assert updated['schedule'][i][0]==old[i][0]
    assert sum(map(sum,updated['schedule']))==farm_request.quota
    assert updated['remaining_quota']==farm_request.quota-sum(row[0] for row in old)

def test_invalid_past_and_impossible_quota(farm_request):
    farm_request.executed[0][0]=1
    with pytest.raises(ValueError):Planner(farm_request)
    farm_request.executed[0][0]=0
    farm_request.start_window=3
    farm_request.quota=7
    with pytest.raises(ValueError):Planner(farm_request)

def test_api():
    client=TestClient(app)
    assert client.get('/').status_code==200
    data=client.post('/api/plan',json={}).json()
    assert 'offline_evaluation' not in data
    assert data['synthetic_data'] is True
    assert sum(sum(row) for row in data['schedule'])==3
    exact=client.post('/api/evaluate',json={'selected_schedule':data['schedule']}).json()['offline_evaluation']
    assert exact['gap']>=-1e-7
    assert client.post('/api/plan',json={'quota':12}).status_code==422

def test_quantum_requested_missing_is_honest(farm_request):
    farm_request.policy='always'
    d=decide(farm_request)
    assert d['quantum_invoked']
    if d['quantum']['status']=='unavailable_install_qiskit_and_qiskit_aer':
        assert d['quantum']['shots']==0
        assert not d['quantum_improved']
        assert d['quantum_budget']['calls_remaining']==farm_request.quantum_max_calls-1

@pytest.mark.parametrize('budget',[64,65,127,128,384,10000])
def test_shot_allocation_respects_total_budget(budget):
    allocation=allocate_shots(budget)
    assert len(allocation)==4
    assert all(isinstance(value,int) and value>0 for value in allocation)
    assert sum(allocation)==budget

@pytest.mark.parametrize('budget',[0,3,True,64.5])
def test_shot_allocation_rejects_impossible_budgets(budget):
    with pytest.raises(ValueError):allocate_shots(budget)

def test_qiskit_measurement_order_is_little_endian_for_planner_bits():
    assert decode_qiskit_bitstring('1 00',3)==(0,0,1)
    assert decode_qiskit_bitstring('011',3)==(1,1,0)
    with pytest.raises(ValueError):decode_qiskit_bitstring('10x',3)

def test_evaporation_forecast_shift_is_a_gate_signal(farm_request):
    farm_request.policy='never'
    farm_request.previous_rain=list(farm_request.rain)
    farm_request.previous_evaporation=list(farm_request.evaporation)
    farm_request.trigger_instability=0
    p=Planner(farm_request)
    unchanged=p.trigger(p.candidates())
    farm_request.evaporation[2]+=8
    changed=Planner(farm_request)
    signal=changed.trigger(changed.candidates())
    assert unchanged['evaporation_shift']==0
    assert not unchanged['condition']
    assert signal['evaporation_shift']>0
    assert signal['shift']==signal['evaporation_shift']
    assert signal['condition']

@pytest.mark.parametrize('value',[float('nan'),float('inf'),-float('inf')])
def test_non_finite_inputs_are_rejected(farm_request,value):
    farm_request.rain[1]=value
    with pytest.raises(ValueError):Planner(farm_request)

def test_extreme_inputs_are_rejected_before_overflow(farm_request):
    farm_request.moisture[0]=1e308
    with pytest.raises(ValueError,match='magnitudes'):
        Planner(farm_request)

def test_rolling_quantum_budget_blocks_calls_and_preserves_classical_fallback(farm_request,monkeypatch):
    monkeypatch.setattr('quantum_engine.quantum_available',lambda:False)
    farm_request.policy='always'
    farm_request.quantum_max_calls=2
    farm_request.quantum_calls_used=2
    farm_request.quantum_shots_budget=128
    d=decide(farm_request)
    assert d['quantum_requested'] is True
    assert d['quantum_invoked'] is False
    assert d['quantum_budget_blocked'] is True
    assert d['quantum']['status']=='budget_exhausted'
    assert sum(map(sum,d['schedule']))==farm_request.quota
    assert d['quantum_budget']['calls_remaining']==0

def test_quantum_execution_error_keeps_verified_classical_schedule(farm_request,monkeypatch):
    monkeypatch.setattr('quantum_engine.quantum_available',lambda:True)
    def fail(*args,**kwargs):
        return {'status':'execution_error','candidate_bits':None,'shots':64,
                'circuit_evaluations':1,'gate_weighted_shots':0,'two_qubit_gates':0,'depth':0}
    monkeypatch.setattr('quantum_engine.qaoa_candidate',fail)
    farm_request.policy='always'
    d=decide(farm_request)
    assert d['quantum']['status']=='execution_error'
    assert sum(map(sum,d['schedule']))==farm_request.quota
    assert d['quantum_improved'] is False

def test_requested_shots_are_clamped_to_remaining_rolling_budget(farm_request,monkeypatch):
    monkeypatch.setattr('quantum_engine.quantum_available',lambda:True)
    requested=[]
    def complete(planner,seed_bits,shots):
        requested.append(shots)
        return {'status':'completed','candidate_bits':list(seed_bits),'shots':shots,
                'circuit_evaluations':4,'gate_weighted_shots':0,'two_qubit_gates':0,'depth':0,'candidates':1}
    monkeypatch.setattr('quantum_engine.qaoa_candidate',complete)
    farm_request.policy='always'
    farm_request.quantum_max_calls=1
    farm_request.quantum_shots_budget=70
    d=decide(farm_request)
    assert requested==[70]
    assert d['quantum_budget']['shots_remaining']==0
    assert d['quantum_budget']['calls_remaining']==0

def test_api_validation_and_budget_schema():
    client=TestClient(app)
    data=client.post('/api/plan',json={'quantum_calls_used':3,'quantum_max_calls':3}).json()
    assert data['quantum_budget']['calls_remaining']==0
    invalid=client.post('/api/plan',content='{"rain":[1,2,NaN,4]}',headers={'Content-Type':'application/json'})
    assert invalid.status_code==422
    assert client.post('/api/evaluate',json={}).status_code==422

def test_qaoa_import_failure_is_reported_and_falls_back(farm_request,monkeypatch):
    import builtins
    original_import=builtins.__import__
    def broken_optional_import(name,*args,**kwargs):
        if name in ('qiskit','qiskit_aer'):raise ImportError('simulator dependency failed to import')
        return original_import(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',broken_optional_import)
    monkeypatch.setattr('quantum_engine.quantum_available',lambda:True)
    farm_request.policy='always'
    d=decide(farm_request)
    assert d['quantum']['status']=='execution_error'
    assert 'failed to import' in d['quantum']['error']
    assert sum(map(sum,d['schedule']))==farm_request.quota

