# Phase 2 proposal — awaiting approval

Goal: make live snapshots, historical weather replay and reproducible synthetic scenarios emit the same timestamped inputs for the shared engine.

Tasks:
1. Add a common source-adapter interface and explicit run state, using the existing clocks and provenance schemas.
2. Refresh live weather with cache, timeout and stale-data handling; preserve retrieval and validity times.
3. Replay the acquired June 25–July 5, 2024 weather with persistent original-date labels. ERA5 is retrospective reanalysis, not a forecast available in 2024; never invent historical issuance times.
4. Generate seeded synthetic event sequences on the acquired graph: rain builds, access deteriorates, closure reports arrive, resources become insufficient, and conflicting/stale reports appear. Generated impacts, population needs, travel assumptions and operational capacities are explicitly simulated.
5. Separate observable inputs from hidden event truth and split generated events into training, calibration and held-out sets by event ID. Later models must never read future truth.
6. Add start/step/reset scenario API controls and a map scenario button/banner. The same input interface feeds the later warning engine; no scenario-specific decision logic.

Dependencies: completed Phase 1 datasets and schemas. No LLM training or API key is needed for this phase. Real historical road closure labels are unavailable; synthetic closure truth must remain labeled simulated even when weather is historical.

Likely files: engine/ingest/, data/generators/, config/scenarios/, backend/app/api/, apps/web/src/, tests/unit/, tests/integration/, docs/.

Tests: same seed produces identical events; different seeds vary events; reset isolates runs; chronology and availability guards reject future inputs; historical labels survive API/export; truth is excluded from observable records; cached live fallback is visibly stale; all existing checks pass.

Done when: the scenario button advances timestamped inputs through the common source layer, live and demo have the same contract, provenance is visible, and reproducible event files are available for later training/evaluation. Warning scores, training, routing and allocation remain later phases.

Approval is required before implementation under NewContext.md section 0.2.
