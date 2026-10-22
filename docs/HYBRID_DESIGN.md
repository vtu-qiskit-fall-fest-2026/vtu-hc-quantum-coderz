# Hybrid integration design

Main retained: field-by-window forecasts and targets, fractional-tail empirical CVaR, COBYLA default, fixed-angle baseline, stale-response version check, research-results dashboard.

Test integrated: rolling call/shot ledger, saved-schedule offline evaluator, rain/evaporation trigger, loss/score caching, workload counters, uncertainty bands, explicit exact classical baseline, repeated benchmark framework.

Review fixes included: currentWindow no longer shadows browser window; advanced controls refresh after advance; accepted plan/forecast references are refreshed; execution errors report attempted work; README matches implementation. Saved-schedule evaluation supersedes the patch's temporary rerun-label workaround.

Budget semantics: each accepted planning response returns remaining calls/shots. Attempted invocations, including unavailable dependencies, consume one call; submitted simulator shots consume shots even if the job later fails. The browser records work even when input edits make a response stale. One operation runs at a time. A lost HTTP response can leave the browser unable to reconcile server-side work; this local demo is not a billing ledger. Comparisons allocate one call per policy independently and expose separate cumulative usage. Reset restores both ledgers.

Cache scope is one immutable Planner request. Loss vectors include every scenario evaluation, including greedy search, trigger features and QUBO work. Score requests/cache hits, unique vectors, QUBO builds and exact enumeration counts are separate metrics. No sum is advertised as total equivalent CPU work. Audit work remains separate from online work.

The exact_classical policy intentionally enumerates current forecast schedules; this is not future-weather access. Other policies access enumeration only in the independent post-hoc auditor. The phase Hamiltonian remains expected quadratic stress; CVaR is classically rescored after measurement.

New field-specific benchmark episodes use independently seeded exogenous field weather, time-varying targets and held-out seed blocks. All policies see the same weather realizations and forecast streams. Smoke mode now guarantees no quantum execution even when Qiskit is installed. Aggregate metadata derives settings and seeds from run files and rejects overlapping held-out seeds or incompatible configurations.
