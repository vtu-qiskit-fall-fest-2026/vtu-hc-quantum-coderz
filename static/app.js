const initialState = {
  moisture:[29,23,25], target:[42,40,44], priority:[1.3,1.0,1.5],
  rain:[3,0,4,1], evaporation:[4,5,4,5],
  available:[[1,1,0,1],[1,0,1,0],[0,1,1,1]],
  executed:[[0,0,0,0],[0,0,0,0],[0,0,0,0]],
  start_window:0, quota:3, irrigation_gain:10, uncertainty:2,
  risk_weight:.35, alpha:.8, scenario_count:15, seed:7,
  policy:'selective', quantum_shots:384, trigger_shift:.25,
  trigger_regret:.04,trigger_instability:.10,
  previous_rain:null, previous_evaporation:null, previous_plan:null,
  rain_by_field:null, evaporation_by_field:null, target_by_window:null,
  previous_rain_by_field:null, previous_evaporation_by_field:null,
  quantum_max_calls:3, quantum_calls_used:0, quantum_shots_budget:1152, quantum_shots_used:0,

};
const state=structuredClone(initialState);
const STORAGE_KEY='jalqr-hybrid-v1';
try { const saved=JSON.parse(localStorage.getItem(STORAGE_KEY)||'null');
  if(saved && typeof saved==='object') for(const key of Object.keys(initialState)) if(key in saved) state[key]=saved[key];
} catch {}
let currentPlan = null;
let busy=false;
let comparisonUsage={calls:0,shots:0};
try { comparisonUsage=JSON.parse(localStorage.getItem(STORAGE_KEY+'-comparison')||'null')||comparisonUsage; } catch {}
function persistState(){try{localStorage.setItem(STORAGE_KEY,JSON.stringify(state));localStorage.setItem(STORAGE_KEY+'-comparison',JSON.stringify(comparisonUsage));}catch{}}
function updateBudget(){
  if(el('budgetStatus'))el('budgetStatus').textContent=`Planning budget: ${state.quantum_max_calls-state.quantum_calls_used} calls / ${state.quantum_shots_budget-state.quantum_shots_used} shots remaining. Separate comparison usage: ${comparisonUsage.calls} calls / ${comparisonUsage.shots} shots since reset.`;
}
function rememberAccepted(snapshot,schedule){
  state.previous_plan=structuredClone(schedule);
  state.previous_rain=[...snapshot.rain];state.previous_evaporation=[...snapshot.evaporation];
  state.previous_rain_by_field=snapshot.rain_by_field?structuredClone(snapshot.rain_by_field):null;
  state.previous_evaporation_by_field=snapshot.evaporation_by_field?structuredClone(snapshot.evaporation_by_field):null;
}

let stateVersion = 0;
function markPlanDirty(){
  currentPlan=null;stateVersion+=1;persistState();
  el('advanceButton').disabled=true;el('calendarStatus').textContent='Plan needs refresh';
  el('exactResult').textContent='Recalculate before evaluating the saved schedule.';
}
const el=id=>document.getElementById(id);
const copyState=()=>structuredClone(state);
const money=v=>Number(v).toLocaleString(undefined,{maximumFractionDigits:1});
const fieldNames=['North Field','East Field','South Field'];
function toast(message){const box=el('toast');box.textContent=message;box.classList.add('show');clearTimeout(window._toastTimer);window._toastTimer=setTimeout(()=>box.classList.remove('show'),3800)}
function setLoading(active){
  busy=active;
  for(const id of ['runMain','runConfigured','compareButton','exactButton','resetButton','m3-run'])if(el(id))el(id).disabled=active;
  el('advanceButton').disabled=active||!currentPlan||state.start_window>=3;
  if(active)toast('Computing schedule…');
}
function navigate(name){document.querySelectorAll('.view').forEach(v=>v.classList.toggle('is-visible',v.id==='view-'+name));document.querySelectorAll('.nav-link').forEach(a=>a.classList.toggle('active',a.dataset.view===name));el('breadcrumbSection').textContent={overview:'Overview',farm:'Farm Model',experiment:'Experiments',research:'Research Notes'}[name];window.scrollTo({top:0,behavior:'smooth'})}
function wireNav(){document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>navigate(b.dataset.view)));document.querySelectorAll('[data-goto]').forEach(b=>b.addEventListener('click',()=>navigate(b.dataset.goto)))}
function controls(){el('rainControls').innerHTML=state.rain.map((v,i)=>`<div class="control-row"><label for="rain-${i}">Window ${i+1}${i<state.start_window?' · completed':''}</label><output id="rainValue-${i}">${Number(v).toFixed(1)}</output></div><input id="rain-${i}" type="range" min="0" max="16" step="0.5" value="${v}" ${i<state.start_window?'disabled':''}>`).join('');
state.rain.forEach((_,i)=>el('rain-'+i).addEventListener('input',e=>{if(state.previous_rain===null){state.previous_rain=[...state.rain];state.previous_plan=currentPlan?.schedule?structuredClone(currentPlan.schedule):null}state.rain[i]=+e.target.value;el('rainValue-'+i).textContent=state.rain[i].toFixed(1);markPlanDirty()}));
el('evaporationControls').innerHTML=state.evaporation.map((v,i)=>`<div class="control-row"><label for="evap-${i}">Window ${i+1}${i<state.start_window?' · completed':''}</label><output id="evapValue-${i}">${Number(v).toFixed(1)}</output></div><input id="evap-${i}" type="range" min="0" max="16" step="0.5" value="${v}" ${i<state.start_window?'disabled':''}>`).join('');
state.evaporation.forEach((_,i)=>el('evap-'+i).addEventListener('input',e=>{if(state.previous_evaporation===null){state.previous_rain=[...state.rain];state.previous_evaporation=[...state.evaporation];state.previous_plan=currentPlan?.schedule?structuredClone(currentPlan.schedule):null}state.evaporation[i]=+e.target.value;el('evapValue-'+i).textContent=state.evaporation[i].toFixed(1);markPlanDirty()}));
for(const [id,key,out,format] of [['quotaInput','quota','quotaOut',v=>v],['uncertaintyInput','uncertainty','uncertaintyOut',v=>v.toFixed(1)],['riskInput','risk_weight','riskOut',v=>v.toFixed(2)]]){
  el(id).value=state[key];el(out).textContent=format(state[key]);el(id).oninput=e=>{state[key]=+e.target.value;el(out).textContent=format(state[key]);markPlanDirty()};
}
el('policyInput').value=state.policy;el('policyInput').onchange=e=>{state.policy=e.target.value;markPlanDirty()};
el('timelineLabel').textContent=`Currently planning from Window ${state.start_window+1}. Previous events remain locked.`;
el('cropProfiles').innerHTML=fieldNames.map((name,i)=>`<div class="crop-card"><h3>${name}</h3><div class="crop-stat"><span>Observed moisture</span><strong id="moistLabel${i}">${state.moisture[i]}</strong></div><input id="moisture${i}" type="range" min="10" max="60" step="1" value="${state.moisture[i]}"><div class="crop-stat"><span>Target</span><strong>${state.target[i]}</strong></div><div class="crop-stat"><span>Crop priority</span><strong>${state.priority[i].toFixed(1)}×</strong></div></div>`).join('');
state.moisture.forEach((_,i)=>el('moisture'+i).addEventListener('input',e=>{state.moisture[i]=+e.target.value;el('moistLabel'+i).textContent=state.moisture[i];markPlanDirty()}));
}
async function api(path,data){const res=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});let json=await res.json();if(!res.ok)throw new Error(typeof json.detail==='string'?json.detail:'Request failed');return json}
async function run(){
  if(busy)return;setLoading(true);const version=stateVersion;const snapshot=copyState();
  try{
    const result=await api('/api/plan',snapshot);
    // Account for actual work even if the response is stale and cannot be used.
    state.quantum_calls_used=result.quantum_budget.calls_limit-result.quantum_budget.calls_remaining;
    state.quantum_shots_used=result.quantum_budget.shots_limit-result.quantum_budget.shots_remaining;
    persistState();updateBudget();
    if(version!==stateVersion){toast('Inputs changed during computation. Recalculate; executed work remains charged.');return;}
    currentPlan=result;rememberAccepted(snapshot,result.schedule);persistState();render(result);
    toast('Verified schedule computed.');
  }catch(err){markPlanDirty();el('engineNotice').textContent='Planning failed: '+err.message;toast('Cannot run planner: '+err.message);}
  finally{setLoading(false);}
}
function render(d){
el('exactResult').textContent='Current schedule is ready. Click “Evaluate saved schedule” for exact evaluation without additional quantum shots.';
el('advanceButton').disabled=state.start_window>=3; if(state.start_window<3)el('advanceButton').disabled=false;el('quotaMetric').innerHTML=d.remaining_quota+' <small>events</small>';el('riskValue').textContent=money(d.objective.risk);el('meanValue').textContent=money(d.objective.mean);el('cvarValue').textContent=money(d.objective.cvar);el('baselineValue').textContent=money(d.classical_baseline.risk);
const qStatus=d.quantum.status;el('quantumMetric').textContent=qStatus==='completed'?'Executed':qStatus==='unavailable_install_qiskit_and_qiskit_aer'?'Unavailable':qStatus==='execution_error'?'Execution error':qStatus==='budget_exhausted'?'Budget exhausted':d.quantum_invoked?'Attempted':'Skipped';el('quantumDetail').textContent=qStatus==='completed'?`${d.quantum.shots} shots · ${d.quantum.circuit_evaluations} circuits · ${d.quantum_budget.calls_remaining} calls left`:qStatus==='unavailable_install_qiskit_and_qiskit_aer'?'Install Qiskit and Aer':qStatus==='execution_error'?(d.quantum.error||'Classical fallback retained'):qStatus==='budget_exhausted'?'Rolling call or shot limit reached':`${d.quantum_budget.calls_remaining} calls · ${d.quantum_budget.shots_remaining} shots left`;
el('calendarStatus').textContent=`${d.remaining_quota} remaining events`;const {start_window, schedule}=d;
el('calendarBody').innerHTML=schedule.map((row,f)=>`<tr><td>${fieldNames[f]}</td>${row.map((v,t)=>{const frozen=t<start_window;const allowed=!!state.available[f][t];const cls=frozen&&v?'frozen':v?'yes':!allowed?'blocked':'';const text=v?(frozen?'✓':'●'):(!allowed?'×':'–');return `<td><div class="tile ${cls}" title="${frozen?'Completed event':v?'Irrigation selected':!allowed?'Not eligible':'No irrigation'}">${text}</div></td>`}).join('')}</tr>`).join('');
el('gateLabel').textContent=d.quantum_budget_blocked?'BUDGET LIMIT':d.quantum.status==='execution_error'?'EXECUTION ERROR':d.quantum_invoked?'TRIGGERED':d.policy==='never'?'CLASSICAL ONLY':d.quantum.status==='not_requested'?'NOT TRIGGERED':'SKIPPED';el('gateLabel').classList.toggle('active',d.quantum_invoked);el('gateReason').textContent=d.reason;
el('featureShift').textContent=(d.trigger.shift*100).toFixed(1)+'% (rain '+(d.trigger.rain_shift*100).toFixed(1)+'% · evap '+(d.trigger.evaporation_shift*100).toFixed(1)+'%)';el('featureRegret').textContent=(d.trigger.regret_proxy*100).toFixed(1)+'%';el('featureInstability').textContent=(d.trigger.ranking_instability*100).toFixed(1)+'%';el('gateFooter').textContent=`${d.classical_candidate_count} unique classical candidates · ${d.classical_evaluations} evaluations · budget ${d.quantum_budget.calls_remaining} calls / ${d.quantum_budget.shots_remaining} shots remaining`;
el('quantumCandidateDetail').textContent=qStatus==='completed' && Number.isFinite(d.quantum.best_candidate_risk)?`Best measured QAOA candidate risk: ${money(d.quantum.best_candidate_risk)} · classical incumbent risk: ${money(d.classical_baseline.risk)}. Final selected schedule: ${d.quantum_improved?'quantum-improved':'classical fallback retained'}. This is candidate quality, not proof of quantum advantage.`:qStatus==='completed'?'QAOA finished but no scored feasible candidate was returned. Final verified schedule remains available.':'Quantum candidate quality appears only after a completed QAOA call; skipped/unavailable calls produce no quantum candidate.';
el('engineNotice').textContent=qStatus==='completed'?`Qiskit Aer: ${d.quantum.shots} shots, ${d.quantum.two_qubit_gates} compiled 2-qubit gates (max), depth ${d.quantum.depth}. Quantum improved: ${d.quantum_improved?'yes':'no'}.`:qStatus==='execution_error'?`Quantum execution failed (${d.quantum.error||'unknown error'}). Attempted shots: ${d.quantum.shots||0}. Showing the verified classical fallback.`:qStatus==='unavailable_install_qiskit_and_qiskit_aer'?'Quantum invocation requested, but Qiskit is not installed. Showing verified classical output only.':qStatus==='budget_exhausted'?'Quantum search was requested but the rolling budget is exhausted. Showing verified classical output.':`No quantum computation was executed. Showing actual classical outputs. ${d.caveat}`;
renderChart(d.trajectories,d.scenario_range);el('timelineLabel').textContent=`Currently planning from Window ${state.start_window+1}. Remaining quota: ${d.remaining_quota}.`;
}
function renderChart(trajectories,range){const svg=el('moistureChart'), left=45,right=632,top=17,bottom=192;
const all=[...trajectories.flat(),...range.lower.flat(),...range.upper.flat()], low=Math.floor((Math.min(...all)-5)/10)*10, high=Math.ceil((Math.max(...all)+5)/10)*10;
const x=t=>left+t*(right-left)/3, y=v=>bottom-(v-low)/Math.max(1,high-low)*(bottom-top);
let html='';for(let i=0;i<=4;i++){const val=low+(high-low)*i/4;const yy=y(val);html+=`<line x1="${left}" y1="${yy}" x2="${right}" y2="${yy}" stroke="#e9efec" stroke-dasharray="3 5"/><text x="${left-8}" y="${yy+4}" fill="#9baea4" font-size="10" text-anchor="end">${val.toFixed(0)}</text>`}
for(let i=0;i<4;i++)html+=`<text x="${x(i)}" y="212" fill="#9baea4" font-size="11" text-anchor="middle">W${i+1}</text>`;
const colors=['#17826d','#79a8d1','#d7b477'];trajectories.forEach((row,i)=>{const upper=range.upper[i].map((v,t)=>`${x(t)},${y(v)}`),lower=range.lower[i].map((v,t)=>`${x(t)},${y(v)}`).reverse();html+=`<polygon points="${[...upper,...lower].join(' ')}" fill="${colors[i]}" opacity=".13" aria-hidden="true"/>`;const points=row.map((v,t)=>`${x(t)},${y(v)}`).join(' ');html+=`<polyline points="${points}" fill="none" stroke="${colors[i]}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`;row.forEach((v,t)=>{html+=`<circle cx="${x(t)}" cy="${y(v)}" r="4" fill="${colors[i]}" stroke="white" stroke-width="2"><title>${fieldNames[i]}, window ${t+1}: ${v.toFixed(2)}</title></circle>`})});svg.innerHTML=html;
}
async function compare(){
  if(busy)return;setLoading(true);const version=stateVersion;const snapshot=copyState();
  el('comparisonResult').textContent='Running independent one-call comparison allocations…';
  const out=[];
  try{
    for(const policy of ['never','always','selective','extra_classical','exact_classical','random']){
      if(version!==stateVersion)break;
      const d=await api('/api/plan',{...snapshot,policy,quantum_max_calls:1,quantum_calls_used:0,quantum_shots_budget:snapshot.quantum_shots,quantum_shots_used:0});
      comparisonUsage.calls+=d.quantum_budget.calls_limit-d.quantum_budget.calls_remaining;
      comparisonUsage.shots+=d.quantum.shots||0;persistState();updateBudget();out.push({policy,d});
    }
    if(version!==stateVersion){el('comparisonResult').textContent='Inputs changed; comparison stopped. Completed work is recorded in comparison usage.';return;}
    el('comparisonResult').innerHTML=`<div class="calendar-wrap"><table class="comparison-table"><thead><tr><th>POLICY</th><th>RISK ↓</th><th>STATUS</th><th>SHOTS</th></tr></thead><tbody>${out.map(({policy,d})=>`<tr><td>${policy}</td><td>${money(d.objective.risk)}</td><td>${d.quantum.status}</td><td>${d.quantum.shots}</td></tr>`).join('')}</tbody></table></div><p class="input-note">Separate experiment budget: each policy gets at most one call of ${snapshot.quantum_shots} shots. Usage is recorded separately from planning. One update only; random uses 50% invocation. No quantum advantage established.</p>`;
  }catch(e){el('comparisonResult').textContent='Comparison error: '+e.message;}
  finally{setLoading(false);}
}
async function exact(){
  if(busy)return;
  if(!currentPlan){el('exactResult').textContent='Recalculate before evaluating the saved schedule.';return;}
  setLoading(true);const version=stateVersion;
  try{
    const d=await api('/api/evaluate',{...copyState(),selected_schedule:structuredClone(currentPlan.schedule)});
    if(version!==stateVersion){el('exactResult').textContent='Inputs changed; please recalculate and evaluate again.';return;}
    const x=d.offline_evaluation;
    el('exactResult').textContent=`Saved schedule risk: ${money(x.selected_risk)} · Exact optimum: ${money(x.optimal_risk)} · Gap: ${money(x.gap)}. No quantum rerun; post-hoc evaluation only.`;
  }catch(e){el('exactResult').textContent='Error: '+e.message;}
  finally{setLoading(false);}
}
function advance(){if(busy)return;if(!currentPlan){toast('Run the planner before advancing the horizon.');return}if(state.start_window>=3){toast('Already at the final window. Reset the page to start over.');return}
const currentWindow=state.start_window;
rememberAccepted(copyState(),currentPlan.schedule);
if(state.rain_by_field){state.previous_rain_by_field=structuredClone(state.rain_by_field);}
for(let f=0;f<3;f++){state.executed[f][currentWindow]=currentPlan.schedule[f][currentWindow];state.moisture[f]=Math.round((state.moisture[f]+(state.rain_by_field?state.rain_by_field[f][currentWindow]:state.rain[currentWindow])-(state.evaporation_by_field?state.evaporation_by_field[f][currentWindow]:state.evaporation[currentWindow])+state.irrigation_gain*state.executed[f][currentWindow])*10)/10}
state.start_window++;markPlanDirty();controls();if(window.refreshAdvancedControls)window.refreshAdvancedControls();toast(`Window ${currentWindow+1} completed using synthetic forecast as observed weather; decisions frozen.`)}
function resetDemo(){
  if(busy)return;
  Object.assign(state,structuredClone(initialState));comparisonUsage={calls:0,shots:0};
  markPlanDirty();controls();if(window.refreshAdvancedControls)window.refreshAdvancedControls();updateBudget();
  el('comparisonResult').textContent='Comparison usage reset.';run();
}
async function boot(){wireNav();controls();updateBudget();el('resetButton').addEventListener('click',resetDemo);el('runMain').addEventListener('click',run);el('runConfigured').addEventListener('click',run);el('compareButton').addEventListener('click',compare);el('exactButton').addEventListener('click',exact);el('advanceButton').addEventListener('click',advance);try{const status=await(await fetch('/api/health')).json();el('engineDot').classList.toggle('ready',status.quantum_available);el('engineStatus').textContent=status.quantum_available?'Qiskit engine ready':'Classical engine ready'}catch{el('engineStatus').textContent='API unavailable'}await run()}
boot();

