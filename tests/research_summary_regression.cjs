/** Guard against hardcoded research claims or conflating quantum/crop outcomes. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const src = fs.readFileSync('static/member3.js', 'utf8');
const html = fs.readFileSync('static/index.html', 'utf8');
const app = fs.readFileSync('static/app.js', 'utf8');

// Run the production module without mounting the app, exposing its render/load functions.
const nodes = new Map();
function node(id) {
  if (!nodes.has(id)) nodes.set(id, {
    textContent: '', replaceChildren() {}, appendChild() {},
    querySelector(selector) { return node(selector.slice(1)); }
  });
  return nodes.get(id);
}
let response;
const document = { getElementById: node, createElement: () => ({appendChild() {}}),
  readyState: 'loading', addEventListener() {} };
const context = {document, console, fetch: async () => {
  if (response instanceof Error) throw response;
  return {ok: true, json: async () => response};
}};
vm.runInNewContext(src.replace('  function init() {',
  '  globalThis.testApi = {renderPrimaryFinding, loadResearch};\n  function init() {'), context);
const {renderPrimaryFinding, loadResearch} = context.testApi;
const assertCleared = () => {
  for (const id of ['saving', 'quality', 'calls']) assert.equal(node(`m3-primary-${id}`).textContent, '—');
  for (const id of ['shots', 'stress', 'call-detail']) assert.equal(node(`m3-primary-${id}`).textContent, 'No current benchmark data');
};
const section = {
  episodes:18,
  policies:[
    {policy:'never',total_shots:0,total_quantum_calls:0,total_quantum_improvements:0,mean_realized_stress:3746.8774},
    {policy:'always',total_shots:14592,total_quantum_calls:38,total_quantum_improvements:0,mean_realized_stress:3746.8774},
    {policy:'selective',total_shots:4992,total_quantum_calls:13,total_quantum_improvements:0,mean_realized_stress:3746.8774},
  ],
};
renderPrimaryFinding(section);
assert.equal(node('m3-primary-saving').textContent, '65.8%');
assert.equal(node('m3-primary-quality').textContent, 'Same observed mean');
assert.equal(node('m3-primary-calls').textContent, '25 fewer calls');
assert.match(node('m3-primary-status').textContent, /Classical-only.*zero quantum shots/);

// If the CSV-derived data change, the summary must update and not claim parity.
section.policies[1].total_shots = 1000;
section.policies[2].total_shots = 700;
section.policies[2].mean_realized_stress = 3753.5;
renderPrimaryFinding(section);
assert.equal(node('m3-primary-saving').textContent,'30.0%');
assert.notEqual(node('m3-primary-quality').textContent,'Same observed mean');
const valid = structuredClone(section);
section.policies = [];
renderPrimaryFinding(section);
assert.match(node('m3-primary-status').textContent,/Not enough validated CSV data/);
assertCleared();

assert.ok(src.includes('renderPrimaryFinding(data.hybrid_field)'));
assert.ok(src.includes('No fresh hybrid benchmark CSV was found'));
assert.ok(src.includes('not versus classical-only'));
assert.ok(html.includes('id="quantumCandidateDetail"'));
assert.ok(app.includes('best_candidate_risk'));
assert.ok(!html.includes('Hackathon integrity'));
(async () => {
  // A successful render followed by either missing data or a failed refresh
  // must remove all six old headline values, not just replace the status text.
  for (const next of [{}, new Error('offline')]) {
    renderPrimaryFinding(valid);
    assert.equal(node('m3-primary-saving').textContent, '30.0%');
    response = next;
    await loadResearch();
    assertCleared();
    assert.match(node('m3-primary-status').textContent, /No fresh hybrid|Unable to load/);
  }
  renderPrimaryFinding(valid);
  assert.equal(node('m3-primary-saving').textContent, '30.0%');
  console.log('PASS: dataset metrics, changed outcomes, stale cards cleared after invalid/missing/failed refresh, and recovery');
})().catch(error => { console.error(error); process.exitCode = 1; });
