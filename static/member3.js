/* Member 3: additive controls and read-only experimental dashboard.
   Uses the shared state and API from static/app.js; no mock benchmark values. */
(() => {
  'use strict';

  const FIELDS = ['North Field', 'East Field', 'South Field'];
  const WINDOWS = 4;
  const examples = {
    rain_by_field: [[3,0,5,2], [1,4,0,3], [5,2,1,0]],
    evaporation_by_field: [[4,5,4,5], [3,4,5,4], [5,6,5,6]],
    target_by_window: [[40,42,45,43], [38,41,43,40], [44,46,47,45]],
  };
  const fmt = n => Number(n).toLocaleString(undefined, {maximumFractionDigits: 2});
  const add = (parent, tag, className, text) => {
    const item = document.createElement(tag);
    if (className) item.className = className;
    if (text != null) item.textContent = String(text);
    parent.appendChild(item);
    return item;
  };

  function rememberPriorForecast() {
    // Capture the pre-edit model only when comparing against a real prior plan.
    if (currentPlan && state.previous_plan === null) {
      state.previous_plan = structuredClone(currentPlan.schedule);
      state.previous_rain = [...state.rain];
      if (state.rain_by_field && state.previous_rain_by_field === null) {
        state.previous_rain_by_field = structuredClone(state.rain_by_field);
      }
    }
  }

  function setAdvanced(on) {
    if(busy)return;
    rememberPriorForecast();
    if (on) {
      for (const key of Object.keys(examples)) {
        if (!state[key]) state[key] = structuredClone(examples[key]);
      }
    } else {
      for (const key of Object.keys(examples)) state[key] = null;
      state.previous_rain_by_field = null;
      state.previous_evaporation_by_field = null;
    }
    markPlanDirty();
    renderAdvancedControls();
  }

  function renderAdvancedControls() {
    const root = document.getElementById('m3-farm-controls');
    if (!root) return;
    const active = !!state.rain_by_field;
    root.replaceChildren();
    const heading = add(root, 'div', 'm3-flex');
    const title = add(heading, 'div', '');
    add(title, 'h2', '', 'Field-level weather & crop targets');
    add(title, 'p', 'm3-muted', 'Advanced synthetic model · optional 3 × 4 matrices');
    const toggle = add(heading, 'button', 'btn btn-outline', active ? 'Use shared weather' : 'Enable field-level model');
    toggle.type = 'button';
    toggle.addEventListener('click', () => setAdvanced(!active));
    if (!active) {
      add(root, 'p', 'm3-note', 'Currently using the original shared-weather inputs. Enable this model to edit rainfall, evaporation and targets for each field and irrigation window.');
      return;
    }
    add(root, 'p', 'm3-note', 'Synthetic demonstration values only. Past windows are locked. Edit a cell, then click “Recalculate plan”. The shared rainfall sliders above do not control this advanced mode.');
    for (const [key, caption, unit] of [
      ['rain_by_field', 'Rainfall forecast', 'rain'],
      ['evaporation_by_field', 'Evaporation forecast', 'evap'],
      ['target_by_window', 'Moisture target', 'target'],
    ]) {
      const fieldset = add(root, 'div', 'm3-matrix-wrap');
      add(fieldset, 'h3', '', caption);
      const table = add(fieldset, 'table', 'm3-input-table');
      const head = add(table, 'thead', '');
      const hr = add(head, 'tr', '');
      add(hr, 'th', '', 'Field');
      for (let t=0; t<WINDOWS; t++) add(hr, 'th', '', `W${t+1}`);
      const tbody = add(table, 'tbody', '');
      FIELDS.forEach((field, f) => {
        const row = add(tbody, 'tr', '');
        add(row, 'th', '', field);
        for (let t=0; t<WINDOWS; t++) {
          const cell = add(row, 'td', '');
          const input = add(cell, 'input', 'm3-number');
          input.type = 'number'; input.step = '0.5'; input.min = '0'; input.max = '100';
          input.value = String(state[key][f][t]);
          input.disabled = t < state.start_window;
          input.setAttribute('aria-label', `${field} window ${t+1} ${unit}`);
          input.addEventListener('change', () => {
            const val = Number(input.value);
            if (!Number.isFinite(val) || val < 0 || val > 100) {
              input.value = state[key][f][t];
              toast('Enter a finite, nonnegative value no greater than 100.');
              return;
            }
            rememberPriorForecast();
            state[key][f][t] = val;
            markPlanDirty();
            toast('Farm inputs changed. Recalculate before advancing.');
          });
        }
      });
    }
    const action = add(root, 'div', 'm3-flex m3-bottom');
    const runButton = add(action, 'button', 'btn btn-primary', 'Recalculate enhanced farm plan ↗');
    runButton.id='m3-run';runButton.type = 'button';
    runButton.addEventListener('click', () => run());
    add(action, 'span', 'm3-muted', 'The existing CVaR and QUBO remain active.');
  }

  function clearPrimaryFinding(message) {
    for (const id of ['saving', 'quality', 'calls']) {
      document.getElementById(`m3-primary-${id}`).textContent = '—';
    }
    for (const id of ['shots', 'stress', 'call-detail']) {
      document.getElementById(`m3-primary-${id}`).textContent = 'No current benchmark data';
    }
    document.getElementById('m3-primary-status').textContent = message;
  }

  function renderPrimaryFinding(section) {
    // Every primary number comes from /api/research-results' saved CSV, not
    // a hardcoded marketing claim. Missing/incompatible data does not imply a win.
    const rows = Object.fromEntries((Array.isArray(section?.policies) ? section.policies : []).filter(r => r && typeof r === 'object').map(r => [r.policy, r]));
    const always = rows.always;
    const selective = rows.selective;
    const classical = rows.never;
    const summary = document.getElementById('m3-primary-status');
    if (!always || !selective || !classical ||
        !Number.isFinite(Number(always.total_shots)) || Number(always.total_shots) <= 0 ||
        !Number.isFinite(Number(selective.total_shots)) ||
        !Number.isFinite(Number(always.mean_realized_stress)) ||
        !Number.isFinite(Number(selective.mean_realized_stress)) ||
        !Number.isFinite(Number(classical.mean_realized_stress))) {
      clearPrimaryFinding('Not enough validated CSV data to calculate the primary comparison.');
      return;
    }
    const shotsA = Number(always.total_shots);
    const shotsS = Number(selective.total_shots);
    const callsA = Number(always.total_quantum_calls);
    const callsS = Number(selective.total_quantum_calls);
    const stressA = Number(always.mean_realized_stress);
    const stressS = Number(selective.mean_realized_stress);
    const stressC = Number(classical.mean_realized_stress);
    const percentSaved = (shotsA - shotsS) * 100 / shotsA;
    const equalObserved = Math.abs(stressS - stressA) < 1e-6;
    const sameAsClassical = Math.abs(stressS - stressC) < 1e-6;
    document.getElementById('m3-primary-saving').textContent = `${percentSaved.toFixed(1)}%`;
    document.getElementById('m3-primary-shots').textContent = `${fmt(shotsS)} selective vs ${fmt(shotsA)} always-run shots`;
    document.getElementById('m3-primary-quality').textContent = equalObserved ? 'Same observed mean' : `${fmt(stressS - stressA)} Δ stress`;
    document.getElementById('m3-primary-stress').textContent = `${fmt(stressS)} selective vs ${fmt(stressA)} always-run stress`;
    document.getElementById('m3-primary-calls').textContent = `${fmt(callsA - callsS)} fewer calls`;
    document.getElementById('m3-primary-call-detail').textContent = `${fmt(callsS)} selective vs ${fmt(callsA)} always-run calls`;
    summary.textContent = `${section.episodes} held-out synthetic episodes per policy. ` +
      `Classical-only: ${fmt(stressC)} mean realized stress, zero quantum shots. ` +
      `Quantum improvements over the classical incumbent: ${fmt(selective.total_quantum_improvements)} (selective), ${fmt(always.total_quantum_improvements)} (always-run). ` +
      (sameAsClassical ? 'Classical-only achieved the same observed mean stress. ' : 'Classical-only results differed; inspect the table below. ') +
      `Shot savings arise primarily from fewer QAOA invocations, not fewer shots within each call.`;
  }

  function renderShotComparison(section, targetId='m3-rolling', label='Historical rolling-horizon study') {
    const rows = section.policies;
    const parent = document.getElementById(targetId);
    add(parent, 'p', 'm3-muted', `${label} · ${section.episodes} held-out synthetic episodes · source: ${section.source}`);
    const max = Math.max(1, ...rows.map(r => r.total_shots));
    const labels = { never: 'Classical-only', always: 'Always QAOA', selective: 'Selective QAOA', random: 'Random invocation', extra_classical: 'Extra classical', exact_classical: 'Exact classical' };
    rows.forEach(r => {
      const line = add(parent, 'div', 'm3-bar-row');
      const info = add(line, 'div', 'm3-bar-label');
      add(info, 'strong', '', labels[r.policy] || r.policy);
      add(info, 'span', 'm3-muted', `${fmt(r.total_shots)} shots · ${r.total_quantum_calls} calls`);
      const track = add(line, 'div', 'm3-track');
      const fill = add(track, 'div', 'm3-fill');
      fill.style.width = `${(r.total_shots / max) * 100}%`;
      fill.setAttribute('aria-label', `${r.policy}: ${r.total_shots} shots`);
    });
    const table = add(parent, 'table', 'm3-results-table');
    const header = add(table, 'thead', '');
    const tr = add(header, 'tr', '');
    ['Policy', 'Mean realized stress ↓', 'Quantum improvements'].forEach(t => add(tr, 'th', '', t));
    const body = add(table, 'tbody', '');
    rows.forEach(r => {
      const row = add(body, 'tr', '');
      add(row, 'td', '', labels[r.policy] || r.policy);
      add(row, 'td', '', fmt(r.mean_realized_stress));
      add(row, 'td', '', String(r.total_quantum_improvements));
    });
  }

  function renderOptimizerComparison(section) {
    const parent = document.getElementById('m3-optimizer');
    add(parent, 'p', 'm3-muted', `${section.seeds} tested seeds · historical shared-weather model · source: ${section.source}`);
    const max = Math.max(1, ...section.methods.map(r => r.mean_final_sampled_stress));
    section.methods.forEach(r => {
      const card = add(parent, 'div', 'm3-optimizer-card');
      const labels = add(card, 'div', 'm3-flex');
      add(labels, 'strong', '', r.method === 'cobyla' ? 'COBYLA-optimized QAOA' : 'Fixed-parameter QAOA');
      add(labels, 'strong', '', fmt(r.mean_final_sampled_stress));
      const track = add(card, 'div', 'm3-track');
      const fill = add(track, 'div', 'm3-fill');
      fill.style.width = `${(r.mean_final_sampled_stress / max) * 100}%`;
      add(card, 'span', 'm3-muted', `${fmt(r.total_shots)} total shots · ${r.evaluations} circuit evaluations`);
    });
  }

  async function loadResearch() {
    const root = document.getElementById('m3-research');
    clearPrimaryFinding('Reading benchmark CSV files…');
    root.querySelector('#m3-loading').textContent = 'Reading benchmark CSV files…';
    ['m3-hybrid', 'm3-rolling', 'm3-optimizer'].forEach(id => document.getElementById(id).replaceChildren());
    try {
      const res = await fetch('/api/research-results', { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      root.querySelector('#m3-loading').textContent = '';
      if (data.hybrid_field) {
        renderPrimaryFinding(data.hybrid_field);
        renderShotComparison(data.hybrid_field, 'm3-hybrid', 'Hybrid field-specific model · COBYLA');
      } else {
        clearPrimaryFinding('No fresh hybrid benchmark CSV was found. No measured reduction is claimed.');
        add(document.getElementById('m3-hybrid'), 'p', 'm3-muted', 'No hybrid benchmark results available.');
      }
      if (data.rolling_horizon) renderShotComparison(data.rolling_horizon);
      else add(document.getElementById('m3-rolling'), 'p', 'm3-muted', 'No historical rolling-horizon CSV found. Run experiments.py to create results/quantum_24/summary.csv.');
      if (data.optimizer_comparison) renderOptimizerComparison(data.optimizer_comparison);
      else add(document.getElementById('m3-optimizer'), 'p', 'm3-muted', 'No fixed-versus-COBYLA comparison CSV found. Run compare_quantum.py to generate results/member1_compare_10.csv.');
    } catch (error) {
      root.querySelector('#m3-loading').textContent = `Benchmark data unavailable: ${error.message}`;
      clearPrimaryFinding('Unable to load measured results; no metric is being asserted.');
    }
  }

  function init() {
    // Optional fields are understood by the merged Member 2 Planner.
    state.rain_by_field ??= null;
    state.evaporation_by_field ??= null;
    state.target_by_window ??= null;
    state.previous_rain_by_field ??= null;

    const farm = document.getElementById('view-farm');
    const panel = add(farm, 'section', 'panel fullpanel m3-panel');
    panel.id = 'm3-farm-controls';
    renderAdvancedControls();
    window.refreshAdvancedControls = renderAdvancedControls;

    const experiment = document.getElementById('view-experiment');
    const research = document.createElement('section');
    research.id = 'm3-research'; research.className = 'panel fullpanel m3-panel';
    research.innerHTML = `
      <div class="m3-flex"><div><div class="eyebrow dark">PRIMARY QUANTUM RESEARCH RESULT</div><h2>Selective versus always-run QAOA</h2></div><button class="btn btn-outline" id="m3-refresh">Refresh saved results</button></div>
      <p class="m3-lead">Research question: can a forecast-aware invocation policy reduce QAOA calls and shots without worsening selected irrigation schedules on held-out synthetic weather episodes?</p>
      <div class="m3-primary-evidence" aria-label="CSV-backed QAOA efficiency comparison">
        <div class="m3-primary-grid">
          <div class="m3-primary-stat"><span>Quantum-shot change</span><strong id="m3-primary-saving">—</strong><small id="m3-primary-shots">Reading saved benchmark…</small></div>
          <div class="m3-primary-stat"><span>Selected schedule quality</span><strong id="m3-primary-quality">—</strong><small id="m3-primary-stress">Reading saved benchmark…</small></div>
          <div class="m3-primary-stat"><span>Quantum invocations</span><strong id="m3-primary-calls">—</strong><small id="m3-primary-call-detail">Reading saved benchmark…</small></div>
        </div>
        <p id="m3-primary-status" class="m3-primary-status" aria-live="polite">Loading measured benchmark data…</p>
      </div>
      <p class="m3-warning">The primary shot comparison is <strong>selective QAOA versus always-run QAOA</strong>, not versus classical-only. The selected schedule uses a verified classical fallback; equal final results do not establish equal standalone quantum candidate quality. These ideal-simulator results demonstrate neither quantum advantage nor hardware speedup nor real-farm water savings.</p>
      <p id="m3-loading" class="m3-muted"></p>
      <h3>Hybrid field-specific benchmark · all policies</h3><div id="m3-hybrid"></div>
      <h3>Historical shared-weather resource usage</h3><div id="m3-rolling"></div>
      <h3>Historical final-sample expected stress: QAOA settings</h3><div id="m3-optimizer"></div>
      <p class="m3-note">Lower final sampled expected stress is preferable. This is not measured crop outcome. The fixed and COBYLA methods use equal total shot budgets but different tuning/final allocations.</p>`;
    const first = experiment.querySelector('.panel');
    experiment.insertBefore(research, first || null);
    research.querySelector('#m3-refresh').addEventListener('click', loadResearch);
    loadResearch();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();

