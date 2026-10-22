"""Member 3 web/API integration tests for the merged member 1+2 model."""
import csv
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import server
from planner import FarmRequest, Planner


client = TestClient(server.app)


def example():
    return {
        "policy": "never",
        "scenario_count": 7,
        "seed": 11,
        "rain_by_field": [[3, 0, 5, 2], [1, 4, 0, 3], [5, 2, 1, 0]],
        "evaporation_by_field": [[4, 5, 4, 5], [3, 4, 5, 4], [5, 6, 5, 6]],
        "target_by_window": [[40, 42, 45, 43], [38, 41, 43, 40], [44, 46, 47, 45]],
    }


def test_new_field_matrices_flow_to_planner():
    payload = server.Payload(**example())
    direct = Planner(FarmRequest(**payload.model_dump()))
    assert direct.rain_scenarios.shape == (7, 3, 4)
    assert direct.target_matrix.shape == (3, 4)
    r = client.post('/api/plan', json=example())
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['synthetic_data'] is True
    assert data['quantum_invoked'] is False
    assert sum(sum(row) for row in data['schedule']) == 3
    assert data['classical_baseline']['risk'] > 0


def test_invalid_matrix_is_http_422():
    payload = example()
    payload['rain_by_field'] = [[1, 2, 3, 4]]
    r = client.post('/api/plan', json=payload)
    assert r.status_code == 422
    assert 'rain_by_field' in r.text


def test_legacy_api_still_works():
    r = client.post('/api/plan', json={'policy': 'never'})
    assert r.status_code == 200
    assert r.json()['remaining_quota'] == 3


def test_dashboard_serves_html_with_member3_assets():
    r = client.get('/')
    assert r.status_code == 200
    assert '/static/member3.js' in r.text
    assert '/static/member3.css' in r.text
    assert client.get('/static/member3.js').status_code == 200
    assert client.get('/static/member3.css').status_code == 200


def test_results_endpoint_gracefully_handles_missing_csvs(monkeypatch, tmp_path):
    monkeypatch.setattr(server, 'BASE', tmp_path)
    r = client.get('/api/research-results')
    assert r.status_code == 200
    data = r.json()
    assert data['farm_model'] == 'legacy_shared_weather'
    assert data['rolling_horizon'] is None
    assert data['optimizer_comparison'] is None


def _save(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_results_endpoint_uses_csv_content_not_embedded_values(monkeypatch, tmp_path):
    _save(tmp_path / 'results/quantum_24/summary.csv', [
        {"policy": "never", "episodes": 2, "mean_realized_stress": 123.25,
         "total_quantum_calls": 0, "total_shots": 0, "total_quantum_improvements": 0},
        {"policy": "always", "episodes": 2, "mean_realized_stress": 123.25,
         "total_quantum_calls": 3, "total_shots": 1152, "total_quantum_improvements": 0},
    ])
    _save(tmp_path / 'results/member1_compare_10.csv', [
        {"seed": "1", "method": "fixed", "final_mean_sampled_stress": 500, "shots": 384, "circuit_evaluations": 4},
        {"seed": "1", "method": "cobyla", "final_mean_sampled_stress": 400, "shots": 384, "circuit_evaluations": 9},
        {"seed": "2", "method": "fixed", "final_mean_sampled_stress": 550, "shots": 384, "circuit_evaluations": 4},
        {"seed": "2", "method": "cobyla", "final_mean_sampled_stress": 430, "shots": 384, "circuit_evaluations": 9},
    ])
    monkeypatch.setattr(server, 'BASE', tmp_path)
    r = client.get('/api/research-results')
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['rolling_horizon']['episodes'] == 2
    assert data['rolling_horizon']['policies'][1]['total_shots'] == 1152
    assert data['optimizer_comparison']['seeds'] == 2
    methods = {x['method']:x for x in data['optimizer_comparison']['methods']}
    assert methods['fixed']['mean_final_sampled_stress'] == pytest.approx(525)
    assert methods['cobyla']['mean_final_sampled_stress'] == pytest.approx(415)
    assert methods['cobyla']['total_shots'] == 768
