"""Member 2: field-specific weather, crop-target and QUBO/CVaR compatibility."""
from dataclasses import replace
import itertools

import numpy as np
import pytest

from planner import FarmRequest, Planner, decide, empirical_cvar
from quantum_engine import coefficients_to_pauli, quantum_available, qaoa_candidate


def advanced_request(**overrides):
    data = dict(
        moisture=[29., 23., 25.],
        target=[42., 40., 44.],
        priority=[1.3, 1.0, 1.5],
        rain=[3., 0., 4., 1.],
        evaporation=[4., 5., 4., 5.],
        available=[[1, 1, 0, 1], [1, 0, 1, 0], [0, 1, 1, 1]],
        executed=[[0] * 4 for _ in range(3)],
        rain_by_field=[[3., 0., 5., 2.], [1., 4., 0., 3.], [5., 2., 1., 0.]],
        evaporation_by_field=[[4., 5., 4., 5.], [3., 4., 5., 4.], [5., 6., 5., 6.]],
        target_by_window=[[40., 42., 45., 43.], [38., 41., 43., 40.], [44., 46., 47., 45.]],
        quota=3,
        uncertainty=2.0,
        scenario_count=7,
        seed=11,
        quantum_shots=128,
    )
    data.update(overrides)
    return FarmRequest(**data)


def test_legacy_weather_scenarios_match_previous_shared_draws():
    r = advanced_request(rain_by_field=None, evaporation_by_field=None,
                         target_by_window=None, scenario_count=15, seed=7)
    p = Planner(r)
    rng = np.random.default_rng(7)
    for s in range(15):
        rain = np.asarray(r.rain, dtype=float).copy()
        evap = np.asarray(r.evaporation, dtype=float).copy()
        rain += rng.normal(0, r.uncertainty, 4)
        evap += rng.normal(0, r.uncertainty * .35, 4)
        for f in range(3):
            np.testing.assert_allclose(p.rain_scenarios[s, f], np.maximum(0, rain))
            np.testing.assert_allclose(p.evap_scenarios[s, f], np.maximum(0, evap))
            np.testing.assert_allclose(p.target_matrix[f], [r.target[f]] * 4)
    bits = p.candidates()[0]['bits']
    losses, _ = p.loss_vector(bits)
    expected_old_tail = np.sort(losses)[-3:].mean()
    assert np.isclose(p.score(bits)['cvar'], expected_old_tail, atol=1e-8)


def test_zero_uncertainty_can_follow_field_weather_and_changing_targets():
    r = advanced_request(
        moisture=[10, 20, 30],
        target=[0, 0, 0],
        priority=[1, 1, 1],
        rain_by_field=[[1, 2, 3, 4], [0, 0, 0, 0], [5, 5, 5, 5]],
        evaporation_by_field=[[0] * 4 for _ in range(3)],
        target_by_window=[[11, 13, 16, 20], [20, 20, 20, 20], [35, 40, 45, 50]],
        uncertainty=0, quota=0, scenario_count=3, available=[[1] * 4 for _ in range(3)],
    )
    p = Planner(r)
    losses, traces = p.loss_vector([0] * p.n)
    np.testing.assert_allclose(losses, [0, 0, 0], atol=1e-10)
    np.testing.assert_allclose(traces[0, :, 0], [11, 20, 35])
    np.testing.assert_allclose(traces[0, :, 3], [20, 20, 50])
    assert p.score([0] * p.n)['risk'] == pytest.approx(0)


def test_changing_targets_affects_losses():
    r = advanced_request(uncertainty=0)
    p1 = Planner(r)
    p2 = Planner(replace(r, target_by_window=None))
    bits = p1.candidates()[0]['bits']
    assert not np.isclose(np.mean(p1.loss_vector(bits)[0]),
                          np.mean(p2.loss_vector(bits)[0]))


def test_new_expected_qubo_and_ising_agree_with_loss_for_any_bits():
    p = Planner(advanced_request())
    c, a, b = p.expected_qubo()
    offset, h, j = coefficients_to_pauli(c, a, b)
    assert np.allclose(np.tril(b), 0)
    rng = np.random.default_rng(155)
    for _ in range(100):
        x = rng.integers(0, 2, size=p.n)
        direct = float(p.loss_vector(x)[0].mean())
        surrogate = c + float(a @ x) + float(x @ b @ x)
        z = 1 - 2 * x
        phase = offset + float(h @ z) + float(z @ j @ z)
        assert np.isclose(direct, surrogate, atol=1e-6, rtol=1e-10)
        assert np.isclose(direct, phase, atol=1e-6, rtol=1e-10)


def test_empirical_fractional_cvar():
    losses = [10, 20, 30, 40, 50]
    assert empirical_cvar(losses, 0.7) == pytest.approx((50 + .5 * 40) / 1.5)
    assert empirical_cvar(losses, 0.8) == pytest.approx(50.0)
    assert empirical_cvar([1, 2, 3], 0.9) == pytest.approx(3.0)
    with pytest.raises(ValueError):
        empirical_cvar([1, float('nan')], .8)


@pytest.mark.parametrize('field,value', [
    ('rain_by_field', [[1] * 4]),
    ('evaporation_by_field', [[1] * 4] * 2),
    ('target_by_window', [[float('inf')] * 4] * 3),
    ('rain_by_field', [[float('nan')] * 4] * 3),
    ('rain_by_field', [[-1] * 4] * 3),
    ('previous_rain_by_field', [[1] * 4] * 2),
])
def test_invalid_field_specific_inputs_fail_fast(field, value):
    with pytest.raises(ValueError):
        Planner(advanced_request(**{field: value}))


def test_changed_field_forecast_affects_heuristic_shift():
    r = advanced_request(uncertainty=0)
    old = [row[:] for row in r.rain_by_field]
    newer = [row[:] for row in old]
    newer[1][2] += 12
    r = replace(r, rain_by_field=newer, previous_rain_by_field=old,
                previous_rain=list(r.rain))
    p = Planner(r)
    shift = p.trigger(p.candidates())['shift']
    assert shift > 0.0
    assert Planner(replace(r, previous_rain_by_field=newer)).trigger(
        Planner(replace(r, previous_rain_by_field=newer)).candidates()
    )['shift'] == 0.0


def test_rolling_horizon_locks_executed_events_and_quota():
    r = advanced_request(uncertainty=0, policy='never')
    first = decide(r)
    schedule = first['schedule']
    observed_moisture = [
        r.moisture[f] + r.rain_by_field[f][0] - r.evaporation_by_field[f][0]
        + r.irrigation_gain * schedule[f][0]
        for f in range(3)
    ]
    executed = [[0] * 4 for _ in range(3)]
    for f in range(3):
        executed[f][0] = schedule[f][0]
    changed = [row[:] for row in r.rain_by_field]
    changed[2][2] += 10
    nxt = replace(r, start_window=1, moisture=observed_moisture, executed=executed,
                  previous_plan=schedule, rain_by_field=changed,
                  previous_rain_by_field=r.rain_by_field)
    replanned = decide(nxt)
    assert all(replanned['schedule'][f][0] == schedule[f][0] for f in range(3))
    assert sum(map(sum, replanned['schedule'])) == r.quota
    assert replanned['trigger']['shift'] > 0


def test_offline_enumeration_is_not_used_online(monkeypatch):
    def forbidden(self):
        raise AssertionError('Offline exact solver leaked into online policy')
    monkeypatch.setattr(Planner, 'evaluate_exact_offline', forbidden)
    result = decide(advanced_request(policy='never'))
    assert 'offline_evaluation' not in result


def test_exact_offline_gap_nonnegative():
    p = Planner(advanced_request())
    classical = p.candidates()[0]['risk']
    exact = p.evaluate_exact_offline()['risk']
    assert classical - exact >= -1e-7


@pytest.mark.skipif(not quantum_available(), reason='Qiskit Aer unavailable')
def test_merged_member1_optimizer_runs_on_field_specific_model():
    p = Planner(advanced_request())
    result = qaoa_candidate(p, p.candidates()[0]['bits'], shots=128)
    assert result['status'] == 'completed', result.get('error')
    assert result['shots'] == 128
    assert result['raw_feasibility_rate'] == 1.0
    assert p.feasible(result['candidate_bits'])
    assert sum(x['shots'] for x in result['parameter_history']) == 128

