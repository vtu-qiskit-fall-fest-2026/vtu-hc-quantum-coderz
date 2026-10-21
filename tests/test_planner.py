import itertools
import numpy as np
import pytest
from fastapi.testclient import TestClient
from server import app
from planner import Planner, FarmRequest, decide
from quantum_engine import coefficients_to_pauli

@pytest.fixture
def farm_request():
    return FarmRequest(moisture=[29,23,25],target=[42,40,44],priority=[1.3,1,1.5],rain=[3,0,4,1],evaporation=[4,5,4,5],available=[[1,1,0,1],[1,0,1,0],[0,1,1,1]],executed=[[0]*4 for _ in range(3)])

def test_fixed_quota(farm_request):
    p=Planner(farm_request)
    for candidate in p.candidates():
        assert p.feasible(candidate['bits'])
        assert sum(candidate['bits'])==3

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
    exact=client.post('/api/evaluate',json={}).json()['offline_evaluation']
    assert exact['gap']>=-1e-7
    assert client.post('/api/plan',json={'quota':12}).status_code==422

def test_quantum_requested_missing_is_honest(farm_request):
    farm_request.policy='always'
    d=decide(farm_request)
    assert d['quantum_invoked']
    if d['quantum']['status']=='unavailable_install_qiskit_and_qiskit_aer':
        assert d['quantum']['shots']==0
        assert not d['quantum_improved']

