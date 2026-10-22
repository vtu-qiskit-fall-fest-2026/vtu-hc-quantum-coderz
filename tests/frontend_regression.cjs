const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('static/app.js','utf8').replace(/boot\(\);\s*$/,'');
const elements=new Map(),storage=new Map();let refreshes=0;
function element(id){if(!elements.has(id))elements.set(id,{textContent:'',innerHTML:'',disabled:false,classList:{add(){},remove(){},toggle(){}},addEventListener(){}});return elements.get(id);}
const context=vm.createContext({structuredClone,console,localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)},document:{getElementById:element},window:{refreshAdvancedControls(){refreshes++}},setTimeout(){return 0},clearTimeout(){}});
vm.runInContext(source,context);
const run=s=>vm.runInContext(s,context);
run(`controls=()=>{};toast=()=>{};render=()=>{};
const sample=()=>({schedule:[[1,0,0,0],[1,0,0,0],[0,1,0,0]],quantum_budget:{calls_limit:3,calls_remaining:2,shots_limit:1152,shots_remaining:768},quantum:{shots:384,status:'completed'},objective:{risk:10}});
state.rain_by_field=[[3,0,5,2],[1,4,0,3],[5,2,1,0]];
state.evaporation_by_field=[[4,5,4,5],[3,4,5,4],[5,6,5,6]];
currentPlan=sample();advance();`);
assert.equal(run('state.start_window'),1);
assert.equal(run('state.executed[0][0]'),1);
assert.equal(run('state.moisture[0]'),38);
assert.equal(run('currentPlan'),null);
assert.equal(refreshes,1);
assert.equal(element('advanceButton').disabled,true);
(async()=>{
  run('api=async()=>sample();state.rain[0]=7;');await run('run()');
  assert.equal(run('state.previous_rain[0]'),7);
  assert.equal(run('state.previous_evaporation_by_field[0][0]'),4);
  assert.equal(run('state.quantum_shots_used'),384);
  assert.ok(storage.has('jalqr-hybrid-v1'));
  // Late quantum results still consume budget, but cannot become the active plan.
  run('api=async()=>{state.rain[1]=9;markPlanDirty();const d=sample();d.quantum_budget.calls_remaining=1;d.quantum_budget.shots_remaining=384;return d;}');
  await run('run()');assert.equal(run('currentPlan'),null);assert.equal(run('state.quantum_shots_used'),768);
  // Comparisons receive independent allocations and expose their own costs.
  run(`const requests=[];api=async(path,payload)=>{requests.push({path,payload});return {schedule:sample().schedule,objective:{risk:10},quantum:{shots:128,status:'completed'},quantum_budget:{calls_limit:1,calls_remaining:0}};};`);
  await run('compare()');assert.equal(run('requests.length'),6);assert.equal(run('comparisonUsage.shots'),768);
  assert.equal(run('requests.every(r=>r.payload.quantum_calls_used===0 && r.payload.quantum_max_calls===1)'),true);
  assert.equal(run('state.quantum_shots_used'),768);
  // Offline evaluation sends the actual saved schedule and never calls /api/plan.
  run(`currentPlan=sample();api=async(path,payload)=>{requests.push({path,payload});return {offline_evaluation:{selected_risk:10,optimal_risk:9,gap:1}};};`);
  await run('exact()');assert.equal(run('requests.at(-1).path'),'/api/evaluate');assert.equal(run('requests.at(-1).payload.selected_schedule[0][0]'),1);
  console.log('PASS: timeline, advanced refresh, stale-result rejection, charged stale work, persistence, comparison accounting, saved-plan evaluation');
})().catch(e=>{console.error(e);process.exitCode=1;});
