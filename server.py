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
    try:return decide(FarmRequest(**payload.model_dump()))
    except ValueError as exc:raise HTTPException(422,detail=str(exc))

@app.post('/api/evaluate')
def evaluate(payload:Payload):
    """EXPLICIT offline endpoint; never used for planning decisions."""
    try:return decide(FarmRequest(**payload.model_dump()),offline_evaluation=True)
    except ValueError as exc:raise HTTPException(422,detail=str(exc))


@app.get('/api/research-results')
def research_results():
    """Read already measured CSVs. Never invent quantum benchmark data.

    These are historical LEGACY farm model experiments, not results on the
    Member 2 field-specific model, and this endpoint does not run Qiskit.
    """
    out = {
        'source_kind': 'historical_simulated_experiments',
        'farm_model': 'legacy_shared_weather',
        'rolling_horizon': None,
        'optimizer_comparison': None,
        'notes': [
            'Benchmarks were generated before the field-specific farm model upgrade.',
            'Shot reduction versus always-QAOA is not total compute speedup.',
            'COBYLA sampled mean expected stress is not realized irrigation stress.',
            'Classical-only matched schedule outcomes in the reported tests; no quantum advantage is claimed.',
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
    return out
