const state = {
  moisture:[29,23,25], target:[42,40,44], priority:[1.3,1.0,1.5],
  rain:[3,0,4,1], evaporation:[4,5,4,5],
  available:[[1,1,0,1],[1,0,1,0],[0,1,1,1]],
  executed:[[0,0,0,0],[0,0,0,0],[0,0,0,0]],
  start_window:0, quota:3, irrigation_gain:10, uncertainty:2,
  risk_weight:.35, alpha:.8, scenario_count:15, seed:7,
  policy:'selective', quantum_shots:384, trigger_shift:.25,
  trigger_regret:.04,trigger_instability:.10,
  previous_rain:null, previous_plan:null,
};
let currentPlan = null;
const el=id=>document.getElementById(id);
const copyState=()=>structuredClone(state);
const money=v=>Number(v).toLocaleString(undefined,{maximumFractionDigits:1});
const fieldNames=['North Field','East Field','South Field'];
function toast(message){const box=el('toast');box.textContent=message;box.classList.add('show');clearTimeout(window._toastTimer);window._toastTimer=setTimeout(()=>box.classList.remove('show'),3800)}
function setLoading(active){for(const id of ['runMain','runConfigured','compareButton','exactButton']){const b=el(id);if(!b)continue;b.disabled=active}if(active)toast('Computing schedule…')}
function navigate(name){document.querySelectorAll('.view').forEach(v=>v.classList.toggle('is-visible',v.id==='view-'+name));document.querySelectorAll('.nav-link').forEach(a=>a.classList.toggle('active',a.dataset.view===name));el('breadcrumbSection').textContent={overview:'Overview',farm:'Farm Model',experiment:'Experiments',research:'Research Notes'}[name];window.scrollTo({top:0,behavior:'smooth'})}
function wireNav(){document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>navigate(b.dataset.view)));document.querySelectorAll('[data-goto]').forEach(b=>b.addEventListener('click',()=>navigate(b.dataset.goto)))}
function controls(){el('rainControls').innerHTML=state.rain.map((v,i)=>`<div class="control-row"><label for="rain-${i}">Window ${i+1}${i<state.start_window?' · completed':''}</label><output id="rainValue-${i}">${Number(v).toFixed(1)}</output></div><input id="rain-${i}" type="range" min="0" max="16" step="0.5" value="${v}" ${i<state.start_window?'disabled':''}>`).join('');
state.rain.forEach((_,i)=>el('rain-'+i).addEventListener('input',e=>{if(state.previous_rain===null){state.previous_rain=[...state.rain];state.previous_plan=currentPlan?.schedule?structuredClone(currentPlan.schedule):null}state.rain[i]=+e.target.value;el('rainValue-'+i).textContent=state.rain[i].toFixed(1)}));
for(const [id,key,out,format] of [['quotaInput','quota','quotaOut',v=>v],['uncertaintyInput','uncertainty','uncertaintyOut',v=>v.toFixed(1)],['riskInput','risk_weight','riskOut',v=>v.toFixed(2)]]){
  el(id).value=state[key];el(out).textContent=format(state[key]);el(id).addEventListener('input',e=>{state[key]=+e.target.value;el(out).textContent=format(state[key])});
}
el('policyInput').value=state.policy;el('policyInput').addEventListener('change',e=>state.policy=e.target.value);
el('timelineLabel').textContent=`Currently planning from Window ${state.start_window+1}. Previous events remain locked.`;
el('cropProfiles').innerHTML=fieldNames.map((name,i)=>`<div class="crop-card"><h3>${name}</h3><div class="crop-stat"><span>Observed moisture</span><strong id="moistLabel${i}">${state.moisture[i]}</strong></div><input id="moisture${i}" type="range" min="10" max="60" step="1" value="${state.moisture[i]}"><div class="crop-stat"><span>Target</span><strong>${state.target[i]}</strong></div><div class="crop-stat"><span>Crop priority</span><strong>${state.priority[i].toFixed(1)}×</strong></div></div>`).join('');
state.moisture.forEach((_,i)=>el('moisture'+i).addEventListener('input',e=>{state.moisture[i]=+e.target.value;el('moistLabel'+i).textContent=state.moisture[i]}));
}
async function api(path,data){const res=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});let json=await res.json();if(!res.ok)throw new Error(typeof json.detail==='string'?json.detail:'Request failed');return json}
async function run(){setLoading(true);try{const result=await api('/api/plan',copyState());currentPlan=result;render(result);toast('Schedule computed. All displayed scores are real model outputs.')}catch(err){toast('Cannot run planner: '+err.message)}finally{setLoading(false)}}
function render(d){el('quotaMetric').innerHTML=d.remaining_quota+' <small>events</small>';el('riskValue').textContent=money(d.objective.risk);el('meanValue').textContent=money(d.objective.mean);el('cvarValue').textContent=money(d.objective.cvar);el('baselineValue').textContent=money(d.classical_baseline.risk);
const qStatus=d.quantum.status;el('quantumMetric').textContent=qStatus==='completed'?'Executed':qStatus==='unavailable_install_qiskit_and_qiskit_aer'?'Unavailable':d.quantum_invoked?'Attempted':'Skipped';el('quantumDetail').textContent=qStatus==='completed'?`${d.quantum.shots} shots · ${d.quantum.circuit_evaluations} circuits`:qStatus==='unavailable_install_qiskit_and_qiskit_aer'?'Install Qiskit and Aer':'Policy / trigger decision';
el('calendarStatus').textContent=`${d.remaining_quota} remaining events`;const {start_window, schedule}=d;
el('calendarBody').innerHTML=schedule.map((row,f)=>`<tr><td>${fieldNames[f]}</td>${row.map((v,t)=>{const frozen=t<start_window;const allowed=!!state.available[f][t];const cls=frozen&&v?'frozen':v?'yes':!allowed?'blocked':'';const text=v?(frozen?'✓':'●'):(!allowed?'×':'–');return `<td><div class="tile ${cls}" title="${frozen?'Completed event':v?'Irrigation selected':!allowed?'Not eligible':'No irrigation'}">${text}</div></td>`}).join('')}</tr>`).join('');
el('gateLabel').textContent=d.quantum_invoked?'TRIGGERED':d.policy==='never'?'CLASSICAL ONLY':d.quantum.status==='not_requested'?'NOT TRIGGERED':'SKIPPED';el('gateLabel').classList.toggle('active',d.quantum_invoked);el('gateReason').textContent=d.reason;
el('featureShift').textContent=(d.trigger.shift*100).toFixed(1)+'%';el('featureRegret').textContent=(d.trigger.regret_proxy*100).toFixed(1)+'%';el('featureInstability').textContent=(d.trigger.ranking_instability*100).toFixed(1)+'%';el('gateFooter').textContent=`${d.classical_candidate_count} unique classical candidates · ${d.classical_evaluations} evaluations`;
el('engineNotice').textContent=qStatus==='completed'?`Qiskit Aer: ${d.quantum.shots} shots, ${d.quantum.two_qubit_gates} compiled 2-qubit gates (max), depth ${d.quantum.depth}. Quantum improved: ${d.quantum_improved?'yes':'no'}.`:qStatus==='unavailable_install_qiskit_and_qiskit_aer'?'Quantum invocation requested, but Qiskit is not installed. Showing verified classical output only.':`No quantum computation was executed. Showing actual classical outputs. ${d.caveat}`;
renderChart(d.trajectories);el('timelineLabel').textContent=`Currently planning from Window ${state.start_window+1}. Remaining quota: ${d.remaining_quota}.`;
}
function renderChart(trajectories){const svg=el('moistureChart'), w=660,h=235,left=45,right=632,top=17,bottom=192;
const all=trajectories.flat(), low=Math.floor((Math.min(...all)-5)/10)*10, high=Math.ceil((Math.max(...all)+5)/10)*10;
const x=t=>left+t*(right-left)/3, y=v=>bottom-(v-low)/Math.max(1,high-low)*(bottom-top);
let html='';for(let i=0;i<=4;i++){const val=low+(high-low)*i/4;const yy=y(val);html+=`<line x1="${left}" y1="${yy}" x2="${right}" y2="${yy}" stroke="#e9efec" stroke-dasharray="3 5"/><text x="${left-8}" y="${yy+4}" fill="#9baea4" font-size="10" text-anchor="end">${val.toFixed(0)}</text>`}
for(let i=0;i<4;i++)html+=`<text x="${x(i)}" y="212" fill="#9baea4" font-size="11" text-anchor="middle">W${i+1}</text>`;
const colors=['#17826d','#79a8d1','#d7b477'];trajectories.forEach((row,i)=>{const points=row.map((v,t)=>`${x(t)},${y(v)}`).join(' ');html+=`<polyline points="${points}" fill="none" stroke="${colors[i]}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`;row.forEach((v,t)=>{html+=`<circle cx="${x(t)}" cy="${y(v)}" r="4" fill="${colors[i]}" stroke="white" stroke-width="2"/>`})});svg.innerHTML=html;
}
async function compare(){setLoading(true);el('comparisonResult').textContent='Running methods…';try{const snapshot=copyState();const policies=['never','always','selective','extra_classical','random'];const out=[];for(const policy of policies){const d=await api('/api/plan',{...snapshot,policy});out.push({name:policy,d})}
el('comparisonResult').innerHTML=`<div class="calendar-wrap"><table class="comparison-table"><thead><tr><th>POLICY</th><th>RISK SCORE ↓</th><th>QISKIT STATUS</th><th>QUANTUM SHOTS</th></tr></thead><tbody>${out.map(({name,d})=>`<tr><td>${({'never':'Classical only','always':'Always-run QAOA','selective':'JalQ-R selective','extra_classical':'Extra classical','random':'Random invocation'})[name]}</td><td>${money(d.objective.risk)}</td><td class="dim">${d.quantum.status.replaceAll('_',' ')}</td><td>${d.quantum.shots}</td></tr>`).join('')}</tbody></table></div><p class="input-note">One synthetic update only. Random call rate is illustrative (50%), not calibrated to selective call frequency. Results are not evidence of quantum advantage.</p>`;
toast('Comparison generated from live API results.')}catch(e){el('comparisonResult').textContent='Error: '+e.message}finally{setLoading(false)}}
async function exact(){setLoading(true);try{const d=await api('/api/evaluate',copyState());const x=d.offline_evaluation;el('exactResult').innerHTML=`<strong>Exact risk optimum: ${money(x.optimal_risk)}</strong> &nbsp; · &nbsp; <strong>Selected policy gap: ${money(x.gap)}</strong><p class="input-note">Computed independently after the live plan. This answer was never supplied to the decision gate.</p>`;toast('Offline evaluation completed.')}catch(e){el('exactResult').textContent='Error: '+e.message}finally{setLoading(false)}}
function advance(){if(!currentPlan){toast('Run the planner before advancing the horizon.');return}if(state.start_window>=3){toast('Already at the final window. Reset the page to start over.');return}
const window=state.start_window;
state.previous_rain=[...state.rain];state.previous_plan=structuredClone(currentPlan.schedule);
for(let f=0;f<3;f++){state.executed[f][window]=currentPlan.schedule[f][window];state.moisture[f]=Math.round((state.moisture[f]+state.rain[window]-state.evaporation[window]+state.irrigation_gain*state.executed[f][window])*10)/10}
state.start_window++;controls();toast(`Window ${window+1} completed: decisions frozen, observations updated.`)}
async function boot(){wireNav();controls();el('runMain').addEventListener('click',run);el('runConfigured').addEventListener('click',run);el('compareButton').addEventListener('click',compare);el('exactButton').addEventListener('click',exact);el('advanceButton').addEventListener('click',advance);try{const status=await(await fetch('/api/health')).json();el('engineDot').classList.toggle('ready',status.quantum_available);el('engineStatus').textContent=status.quantum_available?'Qiskit engine ready':'Classical engine ready'}catch{el('engineStatus').textContent='API unavailable'}await run()}
boot();

