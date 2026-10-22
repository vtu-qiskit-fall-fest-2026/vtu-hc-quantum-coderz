"""FastAPI local demo server for JalQ-R."""
from pathlib import Path
import csv
import statistics
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from planner import FarmRequest, decide
from quantum_engine import quantum_available

BASE=Path(__file__).resolve().parent
app=FastAPI(title='JalQ-R', version='0.1.0', description='Synthetic research prototype — not an operational farm system')
app.mount('/static', StaticFiles(directory=BASE/'static'), name='static')

class Payload(BaseModel):
    moisture: list[float] = Field(default_factory=lambda:[29.,23.,25.])
    target: list[float] = Field(default_factory=lambda:[42.,40.,44.])
    priority: list[float] = Field(default_factory=lambda:[1.3,1.0,1.5])
    rain: list[float] = Field(default_factory=lambda:[3.,0.,4.,1.])
    evaporation: list[float] = Field(default_factory=lambda:[4.,5.,4.,5.])
    available: list[list[int]] = Field(default_factory=lambda:[[1,1,0,1],[1,0,1,0],[0,1,1,1]])
    executed: list[list[int]] = Field(default_factory=lambda:[[0]*4 for _ in range(3)])
    start_window: int = 0
    quota: int = 3
    irrigation_gain: float = 10.
    uncertainty: float = 2.0
    risk_weight: float = 0.35
    alpha: float = 0.8
    scenario_count: int = 15
    seed: int = 7
    policy: str = 'selective'
    trigger_shift: float = 0.25
    trigger_regret: float = 0.04
    trigger_instability: float = 0.10
    quantum_shots: int = 384
    quantum_max_calls: int = 3
    quantum_calls_used: int = 0
    quantum_shots_budget: int | None = None
    quantum_shots_used: int = 0
    previous_evaporation: list[float] | None = None
    previous_evaporation_by_field: list[list[float]] | None = None
    selected_schedule: list[list[int]] | None = None
    previous_rain: list[float] | None = None
    previous_plan: list[list[int]] | None = None
    rain_by_field: list[list[float]] | None = None
    evaporation_by_field: list[list[float]] | None = None
    target_by_window: list[list[float]] | None = None
    previous_rain_by_field: list[list[float]] | None = None

@app.get('/')
def home():return FileResponse(BASE/'static'/'index.html')

@app.get('/api/health')
def health():return {'ok':True,'quantum_available':quantum_available(), 'disclaimer':'Synthetic educational prototype'}

@app.post('/api/plan')
def plan(payload:Payload):
    try:return decide(FarmRequest(**payload.model_dump(exclude={'selected_schedule'})))
    except ValueError as exc:raise HTTPException(422,detail=str(exc))

@app.post('/api/evaluate')
def evaluate(payload:Payload):
    """Score a submitted plan against the offline optimum; never used online."""
    try:
        from planner import Planner
        planner=Planner(FarmRequest(**payload.model_dump(exclude={'selected_schedule'})))
        matrix=payload.selected_schedule
        if matrix is None or len(matrix)!=3 or any(len(row)!=4 for row in matrix):
            raise ValueError('Run the planner first and submit its 3×4 schedule for evaluation')
        if any(value not in (0,1) for row in matrix for value in row):
            raise ValueError('Selected schedule must be binary')
        bits=tuple(int(matrix[f][t]) for f,t in planner.slots)
        if not planner.feasible(bits) or planner.to_matrix(bits)!=matrix:
            raise ValueError('Selected schedule is infeasible for the current inputs')
        selected=planner.score(bits)
        exact=planner.evaluate_exact_offline()
        return {'schedule':matrix,'objective':selected,'offline_evaluation':{
            'optimal_risk':round(exact['risk'],2),'selected_risk':round(selected['risk'],2),
            'gap':round(selected['risk']-exact['risk'],2),'only_for_posthoc_validation':True}}
    except ValueError as exc:raise HTTPException(422,detail=str(exc))


@app.get('/api/research-results')
def research_results():
    """Read stored CSV evidence; never fabricate benchmarks or run Qiskit.

    Sections are deliberately distinct: hybrid_field contains newer field-specific
    COBYLA results, while rolling_horizon and optimizer_comparison are historical
    shared-weather benchmarks.
    """
    out = {
        'hybrid_field': None,
        'source_kind': 'saved_synthetic_simulator_experiments',
        'farm_model': 'mixed_by_section',
        'rolling_horizon': None,
        'optimizer_comparison': None,
        'notes': [
            'hybrid_field, when present, is newer COBYLA field-specific synthetic evidence.',
            'rolling_horizon and optimizer_comparison are earlier shared-weather studies.',
            'Selective shot savings versus always-QAOA reflect fewer calls, not a quantum speedup.',
            'Classical-only matched the selected final schedule outcomes with zero QAOA shots.',
            'The classical fallback may mask differences in measured quantum candidate quality.',
            'COBYLA sampled mean expected stress is not realized irrigation stress.',
        ],
    }
    path = BASE / 'results' / 'quantum_24' / 'summary.csv'
    if path.is_file():
        with path.open(encoding='utf-8-sig', newline='') as fh:
            rows = list(csv.DictReader(fh))
        if rows:
            out['rolling_horizon'] = {
                'source': 'results/quantum_24/summary.csv',
                'episodes': int(rows[0]['episodes']),
                'policies': [
                    {
                        'policy': row['policy'],
                        'mean_realized_stress': float(row['mean_realized_stress']),
                        'total_quantum_calls': int(row['total_quantum_calls']),
                        'total_shots': int(row['total_shots']),
                        'total_quantum_improvements': int(row['total_quantum_improvements']),
                    }
                    for row in rows
                ],
            }
    path = BASE / 'results' / 'member1_compare_10.csv'
    if path.is_file():
        with path.open(encoding='utf-8-sig', newline='') as fh:
            rows = list(csv.DictReader(fh))
        if rows:
            names = sorted(set(row['method'] for row in rows))
            out['optimizer_comparison'] = {
                'source': 'results/member1_compare_10.csv',
                'seeds': len(set(row['seed'] for row in rows)),
                'methods': [
                    {
                        'method': name,
                        'mean_final_sampled_stress': statistics.mean(
                            float(row['final_mean_sampled_stress'])
                            for row in rows if row['method'] == name
                        ),
                        'total_shots': sum(
                            int(row['shots']) for row in rows if row['method'] == name
                        ),
                        'evaluations': sum(
                            int(row['circuit_evaluations'])
                            for row in rows if row['method'] == name
                        ),
                    }
                    for name in names
                ],
            }
    path = BASE / 'results' / 'hybrid_field' / 'aggregate_summary.csv'
    if path.is_file():
        with path.open(encoding='utf-8-sig', newline='') as fh:
            rows=list(csv.DictReader(fh))
        if rows:
            out['hybrid_field']={
                'source':'results/hybrid_field/aggregate_summary.csv',
                'episodes':int(rows[0]['heldout_episodes']),
                'policies':[{'policy':r['policy'],
                    'mean_realized_stress':float(r['mean_realized_stress']),
                    'total_quantum_calls':int(r['completed_quantum_calls']),
                    'total_shots':int(r['shots']),
                    'total_quantum_improvements':int(r['quantum_improvements_over_classical_incumbent'])} for r in rows],
            }
    return out

