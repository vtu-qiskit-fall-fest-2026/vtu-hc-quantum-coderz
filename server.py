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
    previous_rain: list[float] | None = None
    previous_plan: list[list[int]] | None = None

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

