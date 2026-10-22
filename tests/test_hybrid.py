import json
from pathlib import Path
import subprocess
import sys
import pytest
from fastapi.testclient import TestClient
import server
from planner import FarmRequest, Planner, decide
from experiments import create_episode, request_for, run_episode

def request(**changes):
    data=server.Payload(policy='never').model_dump(exclude={'selected_schedule'})
    data.update(changes)
    return FarmRequest(**data)

def test_field_evaporation_trigger_and_cached_qubo():
    r=request(evaporation_by_field=[[4.]*4 for _ in range(3)],previous_evaporation_by_field=[[1.]*4 for _ in range(3)])
    p=Planner(r);assert p.trigger(p.candidates())['evaporation_shift']==3
    a=p.expected_qubo();before=p.loss_scenario_evaluations
    assert p.expected_qubo() is a
    assert p.loss_scenario_evaluations==before and p.qubo_builds==1

def test_offline_endpoint_does_not_run_quantum(monkeypatch):
    client=TestClient(server.app)
    plan=client.post('/api/plan',json={'policy':'never'}).json()
    monkeypatch.setattr(server,'decide',lambda *a,**k:pytest.fail('Offline endpoint reran planner'))
    result=client.post('/api/evaluate',json={'policy':'always','selected_schedule':plan['schedule']})
    assert result.status_code==200
    assert result.json()['schedule']==plan['schedule']

def test_persistent_budget_with_field_model(monkeypatch):
    monkeypatch.setattr('quantum_engine.quantum_available',lambda:True)
    def candidate(p,seed_bits,shots):
        return dict(status='completed',candidate_bits=seed_bits,shots=shots,circuit_evaluations=1)
    monkeypatch.setattr('quantum_engine.qaoa_candidate',candidate)
    r=request(policy='always',quantum_max_calls=1,quantum_shots_budget=70,rain_by_field=[[3.,0.,2.,1.]]*3)
    first=decide(r);assert first['quantum']['shots']==70
    r.quantum_calls_used=1;r.quantum_shots_used=70
    second=decide(r)
    assert second['quantum']['status']=='budget_exhausted'
    assert sum(map(sum,second['schedule']))==3

def test_field_specific_benchmark_reveals_truth_after_decisions():
    e=create_episode(772,field_specific=True)
    r=request_for(e,1,[30,30,30],[[0]*4 for _ in range(3)],None,policy='never',shots=64,scenario_count=3)
    assert r.rain_by_field==[list(f.forecasts_rain[1]) for f in e.field_episodes]
    assert r.previous_evaporation_by_field==[list(f.forecasts_evap[0]) for f in e.field_episodes]
    rows,summary=run_episode(e,policy='never',shots=64,scenario_count=3,random_probability=0,max_quantum_calls=0,mode='smoke')
    assert summary['irrigation_events']==3 and summary['shots']==0
    assert len(rows)==4

def test_smoke_mode_never_executes_quantum(monkeypatch):
    monkeypatch.setattr('quantum_engine.qaoa_candidate',lambda *a,**k:pytest.fail('Smoke ran quantum'))
    _,summary=run_episode(create_episode(22),policy='always',shots=64,scenario_count=3,random_probability=1,max_quantum_calls=3,mode='smoke')
    assert summary['shots']==0

def test_fractional_values_are_not_feasible():
    p=Planner(request())
    assert not p.feasible([0.5,0.5,1,1,0,0,0,0])

def test_fresh_hybrid_results_are_separate_from_historical():
    data=server.research_results()
    assert data['hybrid_field']['episodes']==18
    assert data['hybrid_field']['source']=='results/hybrid_field/aggregate_summary.csv'
    assert data['rolling_horizon']['source']=='results/quantum_24/summary.csv'
    policies={r['policy']:r for r in data['hybrid_field']['policies']}
    assert policies['always']['total_shots']==14592
    assert policies['selective']['total_shots']==4992
