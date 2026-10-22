"""JalQ-R: transparent, synthetic rolling-horizon irrigation planning.

Production claims are deliberately limited: no farm validation, water saving, or
quantum advantage is implied. Enumeration is exclusively an offline evaluator.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
from typing import Optional
import numpy as np

FIELDS = ('North Field', 'East Field', 'South Field')
WINDOWS = 4
DEFAULT_AVAILABILITY = ((1,1,0,1), (1,0,1,0), (0,1,1,1))


def _field_matrix(matrix, legacy, *, name, legacy_is_field_vector=False):
    """Return a field-by-window float array, retaining the legacy vector API."""
    if matrix is None:
        original = np.asarray(legacy, dtype=float)
        result = (np.tile(original[:, None], (1, WINDOWS)) if legacy_is_field_vector
                  else np.tile(original, (3, 1)))
    else:
        result = np.asarray(matrix, dtype=float)
    if result.shape != (3, WINDOWS) or not np.all(np.isfinite(result)):
        raise ValueError(f'{name} must be a finite 3x4 matrix')
    return result


def empirical_cvar(losses, alpha):
    """Exact equally weighted empirical upper-tail CVaR, fractional boundary included."""
    arr = np.asarray(losses, dtype=float).reshape(-1)
    if not len(arr) or not np.all(np.isfinite(arr)) or not (0 < alpha < 1):
        raise ValueError('CVaR requires finite losses and 0 < alpha < 1')
    desc = np.sort(arr)[::-1]
    tail_mass = (1.0 - alpha) * len(desc)
    full = min(len(desc), int(np.floor(tail_mass + 1e-12)))
    fractional = max(0.0, tail_mass - full)
    weighted = float(desc[:full].sum())
    if fractional > 0 and full < len(desc):
        weighted += fractional * float(desc[full])
    return weighted / tail_mass

@dataclass
class FarmRequest:
    moisture: list[float]
    target: list[float]
    priority: list[float]
    rain: list[float]
    evaporation: list[float]
    available: list[list[int]]
    executed: list[list[int]]
    start_window: int = 0
    quota: int = 3
    irrigation_gain: float = 10.0
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
    previous_rain: Optional[list[float]] = None
    previous_plan: Optional[list[list[int]]] = None
    # Optional Member-2 inputs. If absent, the legacy weather/target model is used.
    rain_by_field: Optional[list[list[float]]] = None
    evaporation_by_field: Optional[list[list[float]]] = None
    target_by_window: Optional[list[list[float]]] = None
    previous_rain_by_field: Optional[list[list[float]]] = None

    def validate(self):
        if len(self.moisture) != 3 or len(self.target) != 3 or len(self.priority) != 3: raise ValueError('Three fields are required')
        if len(self.rain) != WINDOWS or len(self.evaporation) != WINDOWS: raise ValueError('Four forecast windows are required')
        if len(self.available) != 3 or len(self.executed) != 3 or any(len(r)!=WINDOWS for r in [*self.available, *self.executed]): raise ValueError('Availability and completed events must be 3×4')
        if not all(v in (0,1) for row in [*self.available,*self.executed] for v in row): raise ValueError('Event matrices must be binary')
        if self.start_window not in range(4): raise ValueError('start_window must be 0..3')
        if self.quota < 0 or self.quota > 12: raise ValueError('Quota must be between 0 and 12')
        if self.irrigation_gain <= 0 or min(self.priority) <= 0: raise ValueError('Gain and priorities must be positive')
        if not 0 <= self.risk_weight <= 1 or not 0 < self.alpha < 1: raise ValueError('Invalid risk parameters')
        if not 3 <= self.scenario_count <= 100: raise ValueError('Scenario count must be 3..100')
        if self.uncertainty < 0: raise ValueError('Uncertainty cannot be negative')
        if self.policy not in ('never','always','selective','random','extra_classical'): raise ValueError('Unknown policy')
        if not 64 <= self.quantum_shots <= 10000: raise ValueError('Quantum shots must be 64..10000')
        for f in range(3):
            for t in range(WINDOWS):
                if self.executed[f][t] and (t >= self.start_window or not self.available[f][t]):
                    raise ValueError('Completed events must be eligible and strictly before current window')
        if self.previous_rain is not None and len(self.previous_rain)!=WINDOWS: raise ValueError('previous_rain must have four values')
        if self.previous_plan is not None and (len(self.previous_plan)!=3 or any(len(a)!=4 for a in self.previous_plan)):
            raise ValueError('previous_plan must be 3×4')
        # Guard against NaN/Inf, which silently invalidates circuit coefficients.
        for name in ('moisture', 'target', 'priority', 'rain', 'evaporation'):
            arr = np.asarray(getattr(self, name), dtype=float)
            if not np.all(np.isfinite(arr)):
                raise ValueError(f'{name} must contain only finite numbers')
        for name in ('irrigation_gain', 'uncertainty', 'risk_weight', 'alpha',
                     'trigger_shift', 'trigger_regret', 'trigger_instability'):
            if not np.isfinite(getattr(self, name)):
                raise ValueError(f'{name} must be finite')
        if self.previous_rain is not None and not np.all(np.isfinite(self.previous_rain)):
            raise ValueError('previous_rain must be finite')
        for name in ('rain_by_field', 'evaporation_by_field',
                     'target_by_window', 'previous_rain_by_field'):
            matrix = getattr(self, name)
            if matrix is not None:
                data = np.asarray(matrix, dtype=float)
                if data.shape != (3, WINDOWS) or not np.all(np.isfinite(data)):
                    raise ValueError(f'{name} must be a finite 3x4 matrix')
        for name in ('rain_by_field', 'evaporation_by_field'):
            matrix = getattr(self, name)
            if matrix is not None and np.any(np.asarray(matrix, dtype=float) < 0):
                raise ValueError(f'{name} cannot contain negative weather forecasts')

    @property
    def remaining(self):
        return self.quota - sum(sum(row) for row in self.executed)

    @property
    def slots(self):
        return [(f,t) for f in range(3) for t in range(self.start_window,WINDOWS) if self.available[f][t]]

class Planner:
    def __init__(self, request: FarmRequest):
        request.validate()
        self.r=request
        self.slots=request.slots
        self.n=len(self.slots)
        self.k=request.remaining
        if self.k < 0 or self.k > self.n: raise ValueError(f'Remaining quota {self.k} cannot fit {self.n} future eligible slots')
        rng = np.random.default_rng(request.seed)
        self.weather_seed = request.seed
        self.target_matrix = _field_matrix(request.target_by_window, request.target,
                                           name='target_by_window', legacy_is_field_vector=True)
        rain_base = _field_matrix(request.rain_by_field, request.rain, name='rain_by_field')
        evap_base = _field_matrix(request.evaporation_by_field, request.evaporation,
                                  name='evaporation_by_field')
        self.rain_scenarios = []
        self.evap_scenarios = []
        remaining = WINDOWS - request.start_window
        for _ in range(request.scenario_count):
            rr, ee = rain_base.copy(), evap_base.copy()
            # Shared perturbations for old vector inputs reproduce the ORIGINAL
            # RNG draws and cross-field correlation; explicit matrices can vary
            # independently between fields. Mixed inputs work independently.
            if request.rain_by_field is None:
                perturb = rng.normal(0, request.uncertainty, remaining)
                rr[:, request.start_window:] += perturb[None, :]
            else:
                rr[:, request.start_window:] += rng.normal(
                    0, request.uncertainty, (3, remaining))
            if request.evaporation_by_field is None:
                perturb = rng.normal(0, request.uncertainty * .35, remaining)
                ee[:, request.start_window:] += perturb[None, :]
            else:
                ee[:, request.start_window:] += rng.normal(
                    0, request.uncertainty * .35, (3, remaining))
            self.rain_scenarios.append(np.maximum(0, rr))
            self.evap_scenarios.append(np.maximum(0, ee))
        self.rain_scenarios = np.asarray(self.rain_scenarios)  # (S, 3, 4)
        self.evap_scenarios = np.asarray(self.evap_scenarios)  # (S, 3, 4)
        self.eval_count = 0

    def feasible(self,bits):
        return len(bits)==self.n and all(int(v) in (0,1) for v in bits) and sum(bits)==self.k

    def to_matrix(self,bits):
        matrix=[[0]*4 for _ in range(3)]
        for (f,t),b in zip(self.slots,bits): matrix[f][t]=int(b)
        for f in range(3):
            for t in range(self.r.start_window): matrix[f][t]=int(self.r.executed[f][t])
        return matrix

    def loss_vector(self,bits):
        """Allows partial bit vectors solely for Hamiltonian coefficient generation."""
        slots=np.zeros((3,4))
        for (f,t),bit in zip(self.slots,bits): slots[f,t]=float(bit)
        moisture=np.tile(np.asarray(self.r.moisture,dtype=float),(self.r.scenario_count,1))
        loss=np.zeros(self.r.scenario_count)
        traces=np.zeros((self.r.scenario_count,3,WINDOWS))
        for t in range(WINDOWS):
            if t >= self.r.start_window:
                moisture += (self.rain_scenarios[:, :, t] - self.evap_scenarios[:, :, t]
                             + self.r.irrigation_gain * slots[:, t])
                loss += np.sum(np.asarray(self.r.priority) *
                               (moisture - self.target_matrix[:, t]) ** 2, axis=1)
            traces[:,:,t]=moisture
        return loss,traces

    def score(self,bits,track=True):
        if not self.feasible(bits): raise ValueError('Candidate does not satisfy exact remaining quota')
        if track:self.eval_count+=1
        losses,_=self.loss_vector(bits)
        # Empirical upper-tail CVaR, including fractional scenario at boundary.
        tail = empirical_cvar(losses, self.r.alpha)
        avg=float(np.mean(losses))
        risk=(1-self.r.risk_weight)*avg+self.r.risk_weight*tail
        return {'risk':float(risk),'mean':avg,'cvar':tail}

    def trajectory(self,bits):
        _,traces=self.loss_vector(bits)
        return np.round(traces.mean(axis=0),2).tolist()

    def expected_qubo(self):
        # This derives a genuinely quadratic surrogate from the linear moisture model.
        zero=[0]*self.n
        c=float(self.loss_vector(zero)[0].mean())
        a=np.empty(self.n); b=np.zeros((self.n,self.n))
        for i in range(self.n):
            x=[0]*self.n;x[i]=1
            a[i]=float(self.loss_vector(x)[0].mean())-c
        for i in range(self.n):
            for j in range(i+1,self.n):
                x=[0]*self.n;x[i]=x[j]=1
                b[i,j]=float(self.loss_vector(x)[0].mean())-c-a[i]-a[j]
        return c,a,b

    def greedy(self):
        selected=[]
        for _ in range(self.k):
            opts=[]
            for i in range(self.n):
                if i in selected:continue
                trial=[int(j in (*selected,i)) for j in range(self.n)]
                opts.append((float(np.mean(self.loss_vector(trial)[0])),i))
            selected.append(min(opts)[1])
        return tuple(int(i in selected) for i in range(self.n))

    def local_search(self,initial,max_rounds=3):
        curr=tuple(initial)
        for _ in range(max_rounds):
            score=self.score(curr)['risk']
            improved=None
            for i in range(self.n):
                if not curr[i]:continue
                for j in range(self.n):
                    if curr[j]:continue
                    tmp=list(curr);tmp[i]=0;tmp[j]=1
                    z=self.score(tmp)['risk']
                    if z < score - 1e-8:
                        score=z; improved=tuple(tmp)
            if improved is None:break
            curr=improved
        return curr

    def candidates(self):
        greedy=self.greedy()
        candidates=[('Greedy',greedy),('Greedy + local search',self.local_search(greedy))]
        if self.r.previous_plan is not None:
            old=tuple(int(self.r.previous_plan[f][t]) for f,t in self.slots)
            # Reconcile the previous plan with the remaining quota deterministically, and verify.
            if sum(old)==self.k:candidates.append(('Carried-forward plan',old))
        # Add only one-swap local variations, never enumerate the exact feasible set in live search.
        seed=candidates[-1][1]
        for i in range(self.n):
            if seed[i]:
                for j in range(self.n):
                    if not seed[j]:
                        arr=list(seed);arr[i]=0;arr[j]=1
                        candidates.append(('Feasible alternative',tuple(arr)))
                        if len(candidates)>=9:break
            if len(candidates)>=9:break
        unique={}
        for label,bits in candidates:
            if bits not in unique:unique[bits]=label
        scored=[{'label':label,'bits':bits,**self.score(bits)} for bits,label in unique.items()]
        scored.sort(key=lambda d:d['risk'])
        return scored

    def trigger(self,candidates):
        r=self.r
        now = _field_matrix(r.rain_by_field, r.rain, name='rain_by_field')
        if r.previous_rain_by_field is not None:
            prev = _field_matrix(r.previous_rain_by_field, r.rain,
                                 name='previous_rain_by_field')
        elif r.previous_rain is not None:
            prev = _field_matrix(None, r.previous_rain, name='previous_rain')
        else:
            prev = now
        future = slice(r.start_window, WINDOWS)
        shift = float(np.mean(np.abs(now[:, future] - prev[:, future])) /
                      max(1., np.mean(np.abs(prev[:, future]))))
        incumbent=None
        if r.previous_plan is not None:
            bits=tuple(int(r.previous_plan[f][t]) for f,t in self.slots)
            if self.feasible(bits):incumbent=self.score(bits)['risk']
        regret=max(0.,((incumbent-candidates[0]['risk'])/max(1.,abs(incumbent)))) if incumbent is not None else 0.
        # Fraction of scenario pairs in which candidate order changes, using current legal candidates.
        top=candidates[:min(4,len(candidates))]
        instability=0.; pairs=0
        for i in range(len(top)):
            for j in range(i+1,len(top)):
                aa=self.loss_vector(top[i]['bits'])[0];bb=self.loss_vector(top[j]['bits'])[0]
                diff=aa-bb; pos=int((diff>1e-9).sum());neg=int((diff<-1e-9).sum())
                instability+=int(pos>0 and neg>0)
                pairs+=1
        instability=instability/max(1,pairs)
        condition=shift>=r.trigger_shift and (regret>=r.trigger_regret or instability>=r.trigger_instability)
        return {'shift':round(shift,4),'regret_proxy':round(regret,4),'ranking_instability':round(instability,4),'condition':bool(condition)}

    def evaluate_exact_offline(self):
        """Never called by decide(): for independent post-hoc evaluation only."""
        best=None
        for select in combinations(range(self.n),self.k):
            bits=tuple(int(i in select) for i in range(self.n))
            risk=self.score(bits,track=False)['risk']
            if best is None or risk<best['risk']:best={'bits':bits,'risk':risk}
        return best


def decide(request: FarmRequest, *, offline_evaluation=False):
    from quantum_engine import qaoa_candidate, quantum_available
    planner=Planner(request)
    candidates=planner.candidates()
    incumbent=candidates[0]
    feature=planner.trigger(candidates)
    rng=np.random.default_rng(request.seed+17)
    if request.policy=='never': invoked=False
    elif request.policy=='always':invoked=True
    elif request.policy=='selective':invoked=feature['condition']
    elif request.policy=='random':invoked=bool(rng.random()<0.5)
    else:invoked=False
    # Trivial fixed-weight space has no meaningful quantum optimization.
    if planner.k==0 or planner.k==planner.n or planner.n<2: invoked=False
    quantum={'status':'not_requested','shots':0,'circuit_evaluations':0,'gate_weighted_shots':0,'two_qubit_gates':0,'depth':0,'candidates':0}
    winner=incumbent; quantum_improved=False
    if request.policy=='extra_classical' and feature['condition']:
        extra=planner.local_search(incumbent['bits'],max_rounds=8)
        obj=planner.score(extra)
        if obj['risk']<winner['risk']-1e-9:winner={'label':'Extended classical search','bits':extra,**obj}
    if invoked:
        if quantum_available():
            quantum=qaoa_candidate(planner,seed_bits=incumbent['bits'],shots=request.quantum_shots)
            if quantum['candidate_bits'] is not None:
                qscore=planner.score(quantum['candidate_bits'])
                if qscore['risk']<winner['risk']-1e-9:
                    quantum_improved=True
                    winner={'label':'Qiskit sample', 'bits':tuple(quantum['candidate_bits']), **qscore}
            quantum.pop('candidate_bits',None)
        else:
            quantum['status']='unavailable_install_qiskit_and_qiskit_aer'
    if request.policy=='selective' and not invoked:
        reason='Conditions did not meet the pre-set heuristic thresholds, or the feasible space is trivial.'
    elif invoked and quantum['status']=='unavailable_install_qiskit_and_qiskit_aer':
        reason='Quantum call requested, but Qiskit is not installed. Classical plan retained.'
    elif invoked:
        reason='Quantum exploration was attempted; best verified risk score was retained.'
    else:reason='Policy returned classical candidates without running Qiskit.'
    result={'name':'JalQ-R','synthetic_data':True,'fields':list(FIELDS),'start_window':request.start_window,
        'remaining_quota':planner.k,'total_quota':request.quota,'slots':[list(s) for s in planner.slots],
        'schedule':planner.to_matrix(winner['bits']),'objective':{'risk':round(winner['risk'],2),'mean':round(winner['mean'],2),'cvar':round(winner['cvar'],2)},
        'classical_baseline':{'risk':round(incumbent['risk'],2),'mean':round(incumbent['mean'],2),'cvar':round(incumbent['cvar'],2)},
        'trajectories':planner.trajectory(winner['bits']),
        'policy':request.policy,'quantum_invoked':invoked,'quantum_improved':quantum_improved,
        'trigger':feature,'reason':reason,'quantum':quantum,
        'classical_candidate_count':len(candidates),'classical_evaluations':planner.eval_count,
        'candidate_overview':[{'source':d['label'],'risk':round(d['risk'],2)} for d in candidates[:5]],
        'caveat':'Idealized synthetic moisture model. Exactly K events; no water savings or quantum speedup claimed.'}
    if offline_evaluation:
        exact=planner.evaluate_exact_offline()
        result['offline_evaluation']={'optimal_risk':round(exact['risk'],2),'gap':round(winner['risk']-exact['risk'],2),
             'only_for_posthoc_validation':True}
    return result
