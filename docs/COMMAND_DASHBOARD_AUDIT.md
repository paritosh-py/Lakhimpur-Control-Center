# Command dashboard functional audit

2026-10-10. Investigation only; no application code changed. User will explain dashboard expectations before the correction plan is finalized. Time budget deferred. User explicitly approved separating real historical weather replay from a synthetic response exercise.

## What exists

- Reusable acquired geography: official boundary, 800 roads, 16 settlements, 7 reference camps, waterways and terrain. Map layers and selection work.
- Cached current/historical weather, acquisition/build scripts, common adapter interface, scenario lifecycle API, seeded synthetic events and separate truth files.
- Warning scorer, evidence/ranking service, API endpoints and dashboard components exist, but the defects below prevent accepting them as correct operational monitoring.
- Reports/trust, prediction, routing, allocation, replanning, evaluation, operational database, team messages and ESP32 firmware/bridge remain placeholders or schema-only foundations. Published camp inventory is not current shelter availability.
- Sidebar is decorative rather than navigation for the original command workflows.

## Defects and root causes

1. **Live mode:** engine/ingest/source.py LiveWeatherAdapter reads successive hours from a static file. scenario.py permits live start/step/reset. main.tsx defaults to scenario (:147), starts rainfall at zero (:151), labels zero Clear / Dry (:404), and exposes Step +1h for every active mode (:542). No upstream refresh exists. Live emits cached weather, not generated incident reports; misleading feed naming/state must not be confused with actual synthetic incident generation.
2. **Disconnected weather:** main.tsx:703 always charts the first 24 cached live hours, even in replay. GFS provider text remains during other sources. A default zero cannot establish sunny conditions. The model weather fetched for all settlements is not connected to the single-location live/replay adapters.
3. **Wrong rainfall features:** service.py:95–96 sums all records with 0.4/0.2 multipliers instead of location-specific rolling 3h/6h windows. It collapses locations, adds unsupported elevation-based rain modulation (:139), fixes forecast rain at zero (:83), approximates saturation, and initializes unknown data age to zero (:84). No decision-time availability guard is applied.
4. **Broken scenario warning API:** service passes run mode scenario into a schema accepting live/replay/simulated. This raises HTTP 500. Frontend warning errors are console-only and leave stale results visible.
5. **False closure confirmation:** frontend and service treat any reported_status=closed as confirmed, without source, proximity, conflict or staleness verification. Evidence then claims official verification and high confidence.
6. **Unsupported evidence:** evidence.py uses fixed access-loss estimates (0.5/1.5/2.5/4 hours), gives replay high confidence by source label, and treats report counts as corroboration. Scorer thresholds are described as calibrated without calibration evidence. Ranker fallback prose invents upstream storm-surge explanations.
7. **State inconsistency:** warning GETs recompute and mutate rank history; global caches are not reset by run lifecycle or isolated by run ID. A closure injected through reevaluate disappears from the next summary while its cached card remains closed. Browser reload restores status but not accumulated closure/feed/weather state.
8. **Future availability leakage:** ScenarioAdapter groups by event_time rather than available_at, delivering delayed reports early. Separate truth files do not prevent this. Replay also assigns ERA5 availability equal to validity despite retrospective reanalysis semantics.
9. **Coverage and documentation:** warning baseline evaluates 75 selected roads, not all 800. Roads/settlements share ranks and only 15 rows render. B6 is marked complete despite absent role apps/exports. OPEN_QUESTIONS still mentions Phase 2 approval. PRODUCT describes intended capabilities as existing; official-authority header and constant online label imply unsupported status.
10. **Insufficient acceptance tests:** tests largely check schemas, nonempty text, score monotonicity and visible widgets. The browser warning test permits stale initial results after scenario failure. validate_phase3.py advertises batch event validation without actually running it. Passing these tests does not establish correct live monitoring or calibrated hazard prediction.

## Reproduced checks

Isolated Python TestClient processes were used; the user's running server was not changed.

- Default pytest: 77 passed, 2 setup errors from existing .pytest_temp permission locks.
- With fresh directory: `python -m pytest -q --basetemp=tmp/audit-20261010-review -p no:cacheprovider`: **79 passed**, one Starlette deprecation warning.
- Idle warning summary: source live, 91 entries, first card rain 0 and age 0 without a live acquisition.
- Live start then step: HTTP 200, record dated 2026-10-03T00:00Z while clock was 2026-10-10T14:07Z.
- Scenario start/step then warnings/summary: HTTP 500; EvidenceCard rejects source_mode=scenario.
- Inject closure osm-1092487157-27-28 then read summary: road absent from summary but cached evidence still says confirmed closed.
- Seed 42, 72-hour exercise: **8 records delivered before available_at**. Example event 2024-06-26 04:00Z, available 09:00Z, emitted at scenario clock 05:00Z.
- No new browser validation, operational calibration or live provider fetch was performed during this audit. Source inspection covered UI, API, adapters, generator, warnings and tests.

## Provisional correction sequence — NOT approved

Preserve datasets, usable schemas, map and generator infrastructure. Do not rewrite the whole project.

1. Restore trustworthy live monitoring: default live, server refresh/cache/backoff, current condition fields and per-location time series, explicit source/time/staleness, unknown distinct from zero. Remove live playback controls and reject stepping live at API level. Separate environmental telemetry from real incidents.
2. Repair common state and warning pipeline: shared clocks, availability guards, true time windows, versioned assessments, run isolation, read-only GETs, persistent closure evidence, honest missing data and separate settlement/road priorities. All widgets consume the same snapshot. Remove unsupported lead times/calibration/verification claims.
3. Separate chronological real-weather replay and synthetic response exercise. Preserve original dates and per-record provenance. Real replay cannot claim historical road/dispatch truth that is absent; synthetic operational records remain labeled simulated. Feed the same downstream engine without future truth/availability leakage.
4. Restore navigation around connected workflows: Live Overview; Replay & Exercises; Map & Access; Incidents & Reports; Teams & Tasks; Messages; Shelters & Resources; Plans & Audit. Final structure pending user's expectations. No fake functional actions in unimplemented sections.
5. Implement missing original workflows in separately approved slices: persistent report intake/trust; inventories and team status; accessibility model/routing; assignment solver and reservation ledger; replanning/unmet needs; ESP-NOW communication; matched evaluation. A replay cannot update a real allocator until the allocator exists.

For each slice: defect regression tests, bounded implementation, API/UI workflow verification, earlier test regression checks, evidence-based progress update. Acceptance includes outages, mode transitions/reload, delayed reports, conflicts, closure persistence, and eventually no double-booking/overflow or lost commitments.

Candidate weather source: Open-Meteo current conditions and hourly data (weather code, temperature, rain, cloud cover, wind/humidity as available), explicitly labeled model-derived rather than local station observations. Official docs inspected: https://open-meteo.com/en/docs . Official warnings/river gauges need separate verified acquisition; unavailable readings must stay unavailable.

## Pending input and next action

User will describe command dashboard expectations next: wait before finalizing the plan. Remaining time deferred. Real-weather replay versus synthetic exercise separation accepted. Provider credentials, actual resource inventory, closure/reopening policies and hardware ports remain unresolved before dependent work; never request keys in chat.

This audit supersedes blanket Phase 2/3 completion claims. No correction implementation or Phase 4 has been approved under the latest instruction.
