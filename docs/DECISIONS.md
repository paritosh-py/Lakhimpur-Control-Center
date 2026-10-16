> Current-state notice (2026-10-11): read CURRENT_STATE.md and HANDOFF.md first. This supporting document includes earlier design/increment details; it is not complete current implementation or approval evidence.

# Decisions

## Team coordination prioritized — 2026-10-11

User explicitly authorized Teams before the previously ordered citizen/NLP slice. Implement a local SQLite ledger and manual dispatch/status cycle now; no extra framework or external service. SQLite transaction/unique index prevents double booking; per-run contexts isolate exercise resources and retain history across resets. Team capability links work locally and are not administrator authentication. Historical-weather exercises produce simulated assignments. No routing, arrival prediction or shelter capacity is fabricated; status/condition changes request operator review while preserving commitments. Scope evidence: TEAM_WORKFLOW_VALIDATION.md.

## Recovery Slice 2 — 2026-10-10

User approved the next recovery slice after reviewing Slice 1. Shared pure settlement assessment replaces the legacy API scorer; legacy source stays unmounted for traceability. Use explicit prototype-flood-v1 rules, not claims of calibration. Configurable hourly accumulation windows are 1/3/6/24/72 hours; teammate road-model semantics are still pending and are not inferred from this warning implementation. Live hourly precipitation uses Open-Meteo Best Match past_days=3 and excludes future valid times. Replay uses all mapped ERA5 locations and declares retrospective release assumptions. One process-wide replay run is serialized; a new run ID clears rank history. No operational closure policy, automatic dispatch or model-training approval is implied.

## Recovery Slice 1 — 2026-10-10

User approved live-monitoring correction. Retain data/map/stack; use independent Live Overview/current weather service rather than the audited warning engine. Preserve legacy exercises under a repair label. Open-Meteo Best Match model conditions used for this noncommercial prototype. Ten-minute upstream interval, one-minute failure retry, one-hour stale cutoff; actual precipitation interval and shared grid cells disclosed. HTTPX now a runtime dependency. No hazard threshold or operational policy approval inferred.

2026-10-10 (Asia/Kolkata)

- User confirmed Lakhimpur district, Assam; flood is the sole hazard.
- User reports approximately 20 hours and delegates technology selection.
- User approved Phase 0 and local laptop hosting with internet for data acquisition.
- Python/FastAPI/Pydantic backend; SQLite persistence planned; React/TypeScript/Vite/Leaflet frontend planned.
- One frontend under `apps/web`, with command/team/citizen views sharing components. This replaces three independent builds from the original proposal and was included in the approved plan.
- XGBoost/scikit-learn, NetworkX/OSMnx, OR-Tools selected for later phases. Install only when their phases need them.
- Preserve NewContext.md unchanged. Do not duplicate or rename it as CLAUDE.md.
- Local uv-managed Python 3.12 because Python was not on PATH. Exact dependencies recorded in uv.lock after installation.
- Node v22.12.0, npm 10.9.0, Git 2.47.0.windows.2 found. Use npm.cmd to avoid changing machine execution policy.
- Internet sources: Open-Meteo numerical weather; IMD official evidence; ASDMA historical flood context; OSM geography; SRTM terrain. Access and district coverage remain Phase 1 verification tasks; WRIS availability is unverified.
- Simulated road histories are acceptable under the source specification. Combining real weather with invented closures never turns the closures into historical facts.
- Two ESP32 DevKitV1 boards use ESP-NOW; attached LoRa is nonfunctional and disclosed. Firmware awaits pin details.
- LLM is API-based report processing, not trained flood prediction. Gemini adapter proposed; credentials/model selection remain outstanding.
- Provenance separates event/issue time, decision-time availability, wall recording time, and replay playback time. Forecast validity is separate.
- `run_id` reserves isolation between live/demo executions; storage isolation itself is future work.
- Scaffold was created before implementation, with placeholders for later phases.

## Phase 1 — 2026-10-10

- User approved Phase 1 acquisition. Conditional Google Maps preference depended on free use: billing is required and free eligibility was not established, so keep Leaflet. Key remains unused and absent from files.
- Use official NWIC/SOI district geometry (EPSG:7755 converted to WGS84), preserving the discrepancy with district-profile area figures.
- Overpass failed; use the dated 2026-10-09 Geofabrik PBF. OSM populated-place coverage was sparse; use GeoNames for settlements.
- Final dataset: 800 physical segments, 748 graph nodes, 16 settlements and seven camps. Exclude ambiguous border locality Kimin; original raw data remains intact. Scope limits are satisfied.
- Public Copernicus GLO-90 DSM replaces tentative SRTM: no account/key needed, explicit 90m limitation. Mosaic adjacent tiles before sampling.
- DDMA 2025 published camp coordinates/capacities replace simulated locations. Current availability and occupancy remain unknown.
- Current and historical weather acquired for every retained settlement; retain actual model-grid coordinates and do not invent original forecast issuance times.
- Map defaults to local vectors; no tile prefetching or automatic live refresh. Roads have unknown status.
- Built-in browser failed to initialize. Isolated headless Chrome via Playwright verifies desktop/mobile rendering and interactions.

## Phase 2 — 2026-10-10

- User explicitly approved Phase 2 ("Go with the phase 2").
- Single common `SourceAdapter` abstract base class used across Live, Historical Replay, and Synthetic Scenarios. The core engine never branches on data source type; all records emit as standard `SourceRecord` envelopes.
- Replay weather uses acquired June 25–July 5, 2024 ERA5 reanalysis with mandatory dual timestamps (`event_time` and `replayed_at`) and `event_name` label. ERA5 reanalysis is explicitly treated as reanalysis, never fabricated as an issued forecast.
- Synthetic flood scenario generation uses a physically intuitive risk formula (rainfall 6h accumulation + low elevation + river proximity + slope) combined with logistic probability scaling on the real Lakhimpur road graph.
- Strict isolation of observable records vs ground truth: observable records contain only information available at event time; hidden ground truth is stored in separate `_truth.json` files and is never accessible to the engine or future ML feature pipelines.
- Generated batch of 40 events split deterministically by event ID (seed-ordered): 24 train (60%), 6 calibration (15%), 10 held-out (25%). No random splitting.
- Scenario run state (`RunState`) is managed in-memory with start, step, reset, stop, status lifecycle controls.
- Persistent mode banner added to web client to satisfy Requirement B6: prominently displays "SIMULATION: demo-42; seed 42; not live" or "REPLAY: Assam flood context; event dated 2024-06-25; not live" whenever not showing live data.
- Configured `--basetemp=.pytest_temp` in pyproject.toml to resolve Windows-specific access denied permissions with default temp directory.


### 2026-10-11 ? Team-only model display and Android wrapper
User requested the saved-weather road model in the rescue Team App and a simple physical-phone Android WebView prototype. Reuse React/FastAPI; add native Java WebView host rather than duplicate domain logic or retrain the model. Manual ETA is a model horizon, not calculated route travel time. Simulation-trained probabilities remain separate from unknown actual road status; no automatic routing/dispatch. Debug HTTP is for same-Wi-Fi use; release stays HTTPS-only.

## Basecamp origin, Two-Leg Routing, and Navigation Mode — 2026-10-11
User clarified the real operational workflow for the Team App:
- Origin: All routes start at Borimuri Basecamp (748G+M62 Plus Code, Borimuri, North Lakhimpur, Assam 787032; coords 27.2666° N, 94.1255° E, connected to graph node 1698435895). Basecamp is permanently pinned on maps.
- Two-Leg Journey: Leg 1 is Basecamp -> Assigned Settlement (Rescue operation). Leg 2 is Settlement -> Closest available DDMA relief shelter (Evacuation operation).
- Model-evaluated arrival routing: Routes are evaluated using the road model predictions for segment arrival ETAs. Confirmed closures strictly invalidate routes; high flood risk (P >= 0.70) triggers warning and alternative routing.
- Rejected road disclosure: Unviable routes are clearly explained with plain-language rejection reasons (flood probability or confirmed closure), rather than dumping raw 800-road tables into the mobile view.
- Turn-by-Turn Navigation HUD: Google Maps-style full-screen navigation HUD providing step-by-step maneuvers, remaining distance, ETA, next turn direction, and mission lifecycle action buttons (Start En Route, Arrived at Destination, Proceed to Shelter, Complete Mission, Report Road Blocked).

## 2026-10-11 continuity and appearance
User approved comprehensive context reconciliation and an Admin appearance-only update. CURRENT_STATE.md records actual implementation and explicit integration gaps; archived claims are not current completion/approval evidence. White/light beige with restrained saffron/green replaces Admin dark palette, retaining layout/functionality; Team and Citizen appearance unchanged. No approval inferred for additional functional phases.
