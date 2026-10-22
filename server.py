"""FastAPI local demo server for JalQ-R."""
from pathlib import Path
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
    previous_rain: list[float] | None = None
    previous_evaporation: list[float] | None = None
    previous_plan: list[list[int]] | None = None
    selected_schedule: list[list[int]] | None = None

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

