# Model/session handoff

## 2026-10-11 ? Team Android road-estimates increment

User explicitly approved starting a simple Android WebView app and moved model prediction display to the Team App, not the command dashboard. User will test on a physical Android phone on the same Wi-Fi. This supersedes the prior proposed dashboard overlay.

Implemented: validated read-only `/api/ml/roads?eta=30|60|120` proxy, exact road joins, missing-estimate preservation and explicit errors; React Team App road screen (`?view=roads`) with travel-horizon selector, search/filter/details, input quality and visible saved-weather labels; native Java WebView wrapper in apps/team-android, Gradle wrapper, Android 8+ debug APK, native server-address setup and error recovery. Built web app served by FastAPI at `/team-mobile`; APK at `/team-app.apk`. Existing team token survives in-page navigation; HTTP Wi-Fi request-ID fallback tested. No dashboard risk overlay was added.

Verified: real upstream 30/60/120 responses each join 800/800 roads; phone-facing LAN page and APK download return HTTP 200 from this laptop. 118 Python tests pass using a fresh temp directory (existing .pytest_temp permissions blocked the first run). All 11 browser tests pass in 53.4 s; additional team lifecycle rerun with randomUUID unavailable passes. TS/Vite production build passes. Real-API mobile and desktop screenshots inspected. APK assembled successfully; final Android lint/build status is recorded in TEAM_ANDROID_VALIDATION.md. No physical device was attached, so Android installation, native interaction and phone-to-laptop reachability remain user verification.

Current phone server: 0.0.0.0:8001, PID 7076 at checkpoint (verify before restarting); Wi-Fi IP 10.10.0.170 may change. Existing backend 8000 and Vite 5173 were left running. Port 8000 has old loaded backend code until restarted; the new standalone demo is on 8001. Active replay state is per process; old exercise contexts cannot be resumed by the new process. Persistence/raw data preserved. See apps/team-android/README.md for startup, download and build steps.

Exact next action: user installs the debug APK from http://10.10.0.170:8001/team-app.apk and enters http://10.10.0.170:8001 in the app. Validate on the physical phone before the next increment. Dynamic POST inference, routing, automatic travel-time calculation, route-specific segment selection, replanning and model calibration remain pending. No approval inferred for these larger phases.


Updated: 2026-10-10, Asia/Kolkata. This is the restart checkpoint, not a conversation transcript. Refresh it after substantive work or before switching models.

## Latest instruction — overrides older completion notes below

2026-10-11 TEAM INCREMENT COMPLETE: user-approved team assignment/status workflow is implemented ahead of citizen/NLP work. Read TEAM_WORKFLOW_VALIDATION.md. Teams & assignments supports isolated live/run rosters, capability/availability-filtered manual dispatch and editing; SQLite prevents double booking and retains history. Local Team App link receives tasks and sends accepted/en_route/arrived/completed/blocked/messages. Map and dashboard reflect status; severity changes flag review without silently reassigning commitments. Reset archives old exercise contexts; browser reload can restore the active backend exercise when switching from default Live. Simulation time wording corrected.

Final checks: 97 Python tests passed; all 9 browser tests passed in 55.7 seconds; TypeScript/Vite production build passed. Desktop/team-mobile screenshots inspected. No pending feature edits or failed checks. API PID 21332 on 8000; Vite PID 22576 on 5173 at checkpoint (verify before restarting). Runtime DB data/runtime/operations.sqlite3 contains isolated test exercise records; no live test assignments were created. Do not delete the ledger, raw sources or untracked workspace files.

Routes/ETA, road-model recommendations, shelter/vehicle allocation, citizen/NLP intake and automatic replanning are still incomplete. This increment does not claim all of Recovery Slice 4 is complete or authorize unrequested remaining slices. TeamApp is local with capability links; admin authentication/LAN deployment not provided.

2026-10-11: user explicitly moved team functionality ahead of citizen/NLP integration: "Yes, lets start with this now" after confirming exercise team assignment and status updates. Approved scope: persistent separate live/exercise team rosters, manual team-to-settlement dispatch, local Team App and status/message return, map assignment display, availability/capability checks, preserved commitments. Route/ETA and road-model recommendations remain unavailable pending teammate contract. This supersedes the old slice ordering, not approval to fabricate routing or complete the entire response planner. Work in progress; tests pending.

Recovery Slice 2 implemented and validated: read docs/SLICE_2_VALIDATION.md. Shared per-settlement engine, 1/3/6/24/72-hour rainfall coverage/duration, terrain proxy, independent confidence, Warnings page, consistent map evidence, full-location historical replay and separate synthetic exercise. Root remains live. Legacy UI is no longer mounted; source retained. Final Python: 90 pass; browser: 8 pass; production build passes. Prototype heuristics are explicitly uncalibrated. Real provider acquisition verified all 16 with complete 72-hour history. A final frontend check covers the sticky NOT LIVE timeline label. Slice 3 is NOT approved yet.

Current server: API uvicorn on 127.0.0.1:8000 (PID 12544 at checkpoint); existing Vite on 5173. Verify processes before any restart. No uncommitted work may be discarded: workspace files are still untracked. No model credentials used or stored. No in-progress feature edits remain after the final browser check.

Recovery Slice 2 is approved and in progress following acceptance of Slice 1 and "Now correctly implement the next parts", reaffirmed by "Continue from where u left". Scope: shared settlement assessments, Warnings page, chronological historical replay and separate synthetic exercises. Slice 3 onward still needs approval. Preserve live-first behavior; teammate models are not integrated in this slice.

Recovery Slice 1 was explicitly approved ("Yes start") and is completed; read docs/SLICE_1_VALIDATION.md. Root URL now displays real current model weather for all 16 settlements through /api/live/conditions, independently of scenarios. Old UI remains at /?view=exercise, under repair. Latest checks: 86 Python tests, 8 browser tests, TypeScript/Vite build pass. Actual provider fetch: 16 current locations, 10 grids. Runtime cache is separate from original datasets. Slice 2 is NOT approved. Older no-implementation notes below predate the Slice 1 approval; older Phase 3 completion claims do not resolve audited defects.

Latest clarification: flood-focused first, capture other incident types without adding independent hazard models. Teammate NLP service uses Python/FastAPI over HTTP. Road model uses 1/3/6/24/72-hour time points, but sample-versus-accumulation-versus-forecast meaning remains unresolved; obtain an example payload before integration. These answers are configuration clarifications, not approval to start recovery Slice 1. Wait for explicit implementation approval.

Further clarification received: read docs/RECOVERY_PLAN.md and docs/REPORT_CONTRACT_PROPOSAL.md. User now explicitly wants live-first per-settlement monitoring, separate Warnings/Teams/Dispatcher pages, integrated citizen/team apps, teammate-owned NLP and arrival-time road models. Exact road rainfall windows: 1/3/6/24/72 hours. These documents are proposals, not implementation approval. Recommend improving existing workspace. Model contracts and flood-versus-landslide scope questions are pending. Do not wait for expectations again: they have been supplied; next is agreement on correction plan.

User requested an audit and approval of a correction plan BEFORE application changes. Read docs/COMMAND_DASHBOARD_AUDIT.md. Earlier Phase 2/3 completion claims are now challenged by reproduced live-mode, scenario API, stale-state and future-availability defects. Existing 79 tests pass with a fresh temp directory but miss these defects. No application code changed during audit.

User will explain dashboard expectations next; wait before finalizing the plan or implementing. User approved separating real historical weather replay from a synthetic response exercise and deferred the time-budget answer. Earlier phase approvals do not authorize proceeding past this newer audit/approval instruction.

## Read first

1. NewContext.md in full: authoritative scope, requirements and phase workflow.
2. This file and docs/PROGRESS.md: current state and evidence.
3. Relevant supporting documents: docs/DECISIONS.md, docs/OPEN_QUESTIONS.md, docs/PHASE_1_DATA_REPORT.md, data/SOURCES.md, docs/API_CONTRACT.md and docs/DATA_DICTIONARY.md.
4. Inspect actual code and Git status; later user instructions override this checkpoint.

## User decisions and approval state

- Lakhimpur district, Assam; flood only. Original time budget approximately 20 hours; remaining time has not been reconfirmed.
- Laptop hosts locally and uses internet for acquisition. Stack choice delegated.
- Two ESP32 DevKitV1 boards; attached LoRa not functional. Intended demonstration uses ESP-to-ESP / ESP-NOW; firmware, pins and ports remain later work.
- Phases 0–1 foundation retained. Phases 2–3 reopened for correctness review following COMMAND_DASHBOARD_AUDIT.md.
- Defect 4 from audit resolved: `source_mode="scenario"` Pydantic validation error fixed in `schemas.py` and `service.py`.
- Correction plan implementation and Phase 4 await user clarification of dashboard expectations.
- Google Maps preference was conditional on free capability. Leaflet retained; supplied Google key was never used or stored. Do not copy credentials from conversation into files.

## Completed work

- **Phase 0:** Project scaffold, Python/FastAPI/Pydantic contracts, provenance and availability guards, shared live/scenario clocks, config, validation API and tracking documents.
- **Phase 1:** Repeatable acquisition/cache scripts, raw-file metadata and hashes, processed geometry and weather, read-only API and responsive React/TypeScript/Leaflet reference map. 800 roads, 748 nodes, 16 settlements, 7 relief camps, 56 waterways, 90m Copernicus DSM.
- **Phase 2 (Source Adapters, Historical Replay & Synthetic Generators):**
  - Common `SourceAdapter` base class and `SourceRecord` uniform envelope (`engine/ingest/source.py`).
  - `LiveWeatherAdapter`: Wraps cached GFS snapshot with staleness detection.
  - `ReplayWeatherAdapter`: Hourly historical playback of ERA5 June 25–July 5, 2024 weather with persistent dual timestamps (`event_time` + `replayed_at`) and original event name label.
  - `ScenarioAdapter` & seeded generator (`data/generators/flood_scenario.py`): Realistic physical flood simulation based on rain buildup, terrain elevation, slope, and river proximity.
  - Generates 40 reproducible synthetic events partitioned deterministically by event ID: 24 train (60%), 6 calibration (15%), 10 held-out (25%).
  - Strict separation of observable inputs (`_observable.json`) vs hidden ground truth (`_truth.json`). Zero truth leakage.
  - In-memory `RunState` manager (`engine/ingest/run.py`) providing `/start`, `/step`, `/reset`, `/stop`, `/status`.
  - Scenario API router (`backend/app/api/scenario.py`) registered in FastAPI backend.
  - Web UI scenario controls (`apps/web/src/main.tsx`): Mode switcher (Scenario, 2024 Replay, Live), Start/Step (+1h)/Reset/Stop controls, live event feed, dynamic road closure highlighting on map.
  - Persistent Requirement B6 Banner: Displays prominent "SIMULATION: demo-42; seed 42; not live" or "REPLAY: Assam flood context; event dated 2024-06-25; not live" whenever not showing live data.
  - Automated validation script (`scripts/validate_phase2.py`) passes with 40 events verified and 0 truth leakage.
- **UI Overhaul & Impeccable Craft-Floor Audit:**
  - Audited dashboard with Impeccable skill (`.agent/skills/impeccable/scripts/impeccable.cmd detect`): eliminated generic "AI slop" anti-patterns (banned `.eyebrow` kickers, glowing halos, raw emoji icons, and artificial 3px side borders).
  - Authored [`PRODUCT.md`](file:///c:/Users/parit/Desktop/HackMatrix_AL/PRODUCT.md) documenting platform, design constraints, and visual commitments.
  - Implemented strict 8pt grid token system in [`apps/web/src/style.css`](file:///c:/Users/parit/Desktop/HackMatrix_AL/apps/web/src/style.css) with curated palette and dual typography: `DM Sans` for UI/body and `JetBrains Mono` for telemetry/metrics.
  - Eliminated blue-purple "AI slop" palette: replaced cold navy backgrounds with warm obsidian charcoal (`#0b0c0e`), removed all neon cyan and purple accents, and established an authoritative civil defense scheme (tactical safety amber `#f59e0b` primary authority accent, emergency crimson `#dc2626` step action, archival amber for replay, and clean forest emerald `#10b981` for active units).
  - Redesigned layout into a high-density, balanced 3-pane operations console.
- **Phase 3 (Warning Engine with Evidence Cards and Severity Ranking):**
  - **Calibrated Physics Scorer (`engine/warnings/scorer.py`):** Multi-factor risk engine covering rain (1h, 3h, 6h, forecast), DEM terrain (elevation, slope), river proximity, antecedent precipitation index (ground saturation API), and corroborating incident reports. Confirmed closures strictly output 100.0 risk score and `critical` severity.
  - **Explainable Evidence Cards (`engine/warnings/evidence.py`):** Requirement B4 implementation containing plain-language primary driver explanation (`why`), confidence rating (`high`/`medium`/`low`) and confidence justification, telemetry data age (`data_age_seconds`), estimated access loss onset (`lead_time_hours`), multi-factor 6-cell metric grid, and honest `uncertainty_disclosure`.
  - **Dynamic Re-ranking Engine (`engine/warnings/ranker.py`):** Requirement B3 implementation tracking prior rank order, computing rank shifts (`rank_delta`), and generating plain-language re-ranking explanations (`rerank_reason`, e.g. `"Climbed 87 rank(s) (from #89 to #2) directly due to confirmed impassable closure report."`).
  - **Domain Service & REST API (`engine/warnings/service.py`, `backend/app/api/warnings.py`):** Evaluates all 16 settlements and 75 primary road segments against `RunState`. Endpoints for `/summary`, `/settlements`, `/roads`, `/{entity_id}/card`, and `/reevaluate`.
  - **Frontend Integration (`apps/web/src/main.tsx`, `apps/web/src/style.css`):**
    - Right Pane Ranked Flood Warnings drawer with severity pills (`CRIT`, `HIGH`, `MOD`, `ADV`), active alert list, rank badges, and rank delta indicators.
    - Interactive Explainable Evidence Card expanded inside the Entity Inspector when selecting settlements, roads, or warning items.
    - Live re-ranking synchronization on scenario timeline steps (`+1h`).
  - **Validation & Automated Verification:**
    - `scripts/validate_phase3.py` passes 100% across all 16 settlements and 75 roads.
    - 79 Python backend tests pass (13 unit/integration warning tests).
    - 4 Playwright browser tests pass (`map.spec.ts`, `scenario.spec.ts`, `warning.spec.ts`).
    - Verified visual screenshot saved to `docs/screenshots/phase3-warning-evidence.png`.

## Important data constraints

- Sources: NWIC/SOI boundary, Geofabrik/OSM roads and waterways, GeoNames settlements, Copernicus terrain, Open-Meteo weather, ASDMA historical and camp reference documents.
- Kimin excluded because administrative context conflicts across sources; keep config/data_quality_exclusions.json.
- NWIC polygon area differs from district profile area; preserve and disclose discrepancy. Do not reshape it to force a match.
- Road status, population, travel time, current shelter availability and occupancy are unknown. Published camp capacity is not available bed count.
- Historical reanalysis is not an issued historical forecast. District flood totals are not road closure labels. Future synthetic closures/needs/capacities must be explicitly simulated, even with real weather.
- Current road topology is not verified 2024 topology. Terrain is a surface model, not measured water depth or road-deck elevation.
- Zero future truth leakage: feature pipelines must never consume `_truth.json` files.

## Last validation checkpoint

2026-10-10, after Phase 3 completion:
- **Python (pytest):** 79 tests passed (0 failures, 0 errors, 2 benign warnings: Starlette TestClient and Pytest cache nodeids).
- **Chrome / Playwright:** 4 tests passed (`map.spec.ts`, `scenario.spec.ts`, `warning.spec.ts`), covering layers, camp evidence, mobile layout, API error handling, scenario lifecycle controls, step advancement, persistent B6 banner, ranked alert drawer, and expanded Evidence Cards.
- **TypeScript / Vite build:** Production build passed cleanly in 3.35s (`tsc --noEmit && vite build`).
- **scripts/validate_phase3.py:** 16 settlements and 75 roads evaluated, 100% of alerts carry verified Evidence Cards, dynamic re-ranking delta +87 verified for Kadam, confirmed closure invariance verified.
- **Screenshots in `docs/screenshots/`:**
  - `phase1-desktop.png` (Overhauled 3-pane workbench desktop)
  - `phase1-mobile.png` (Clean, responsive mobile operations console)
  - `phase2-scenario.png` (Synthetic simulation with persistent purple B6 banner and telemetry)
  - `phase2-replay.png` (Historical replay with persistent amber B6 banner)
  - `phase3-warning-evidence.png` (Phase 3 ranked flood warnings and expanded explainable Evidence Card)

## Environment and run instructions

Workspace: `C:/Users/parit/Desktop/HackMatrix_AL`, Windows PowerShell. Local Python 3.12 environment under `.venv`; Node 22.12. Use `npm.cmd` in PowerShell.

Commands from workspace root:

```powershell
# Run backend API (port 8000)
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# Run frontend dev server (port 5173)
npm.cmd run dev --prefix apps/web -- --port 5173
```

Validation & test commands:

```powershell
# Run Python test suite
.\.venv\Scripts\python.exe -m pytest -q

# Acquired-geography validation; old Phase 2/3 scripts do not prove recovery correctness
.\.venv\Scripts\python.exe scripts/validate_phase1.py
# Use the full pytest suite above and browser tests below for the recovery release.

# Build frontend production bundle
npm.cmd run build --prefix apps/web

# Run Playwright end-to-end tests (with backend and Vite running)
Set-Location apps/web; npx.cmd playwright test
```

## Exact next action

Latest next action (supersedes the Slice 2 review sequence below): let user review Teams → assign settlement → Open Team App → status/message → map. Continue with their next explicitly chosen increment. For route-aware recommendations, first obtain the road-model example input/output, exact 1/3/6/24/72 temporal semantics and arrival-time meaning, plus operational inventory/closure policy; do not invent these. Citizen/NLP work still needs the teammate endpoint/schema/languages/authentication. No missing configuration blocks the completed local manual-team workflow.

Final checkpoint: 90 Python tests; all 8 browser tests passed in 23.8 s after fixing inherited mobile overflow so the NOT LIVE strip stays in view; TypeScript/Vite build passed. No unfinished edits or failed checks remain in Slice 2. Old validate_phase3.py and legacy scorer tests are historical artifacts, not evidence for the current engine.

1. Let the user review Slice 2 using the journey in SLICE_2_VALIDATION.md. Do not re-ask their dashboard requirements.
2. Obtain Slice 3 approval before dispatcher/citizen reporting work. Collect teammate FastAPI URL, sample request/response, languages and authentication before its integration.
3. Keep road model semantics/payload, verified closures, team/resource persistence and ESP-NOW work in their recorded later slices. Existing generated event files need regeneration/validation before training or evaluation.


## 2026-10-11 ? Teammate LightGBM V2 integration review (no implementation approval)

Reviewed the supplied integration prompt and current map road identifiers. Read-only requests to the teammate LAN API `/ml/roads/simple?eta=30`, `60`, and `120` succeeded: each returned model_version `lightgbm_v2_candidate`, mode `snapshot_demo`, 800 predictions, 800 exact matches to roads.geojson properties.id, and no duplicate road IDs. This verifies transport and joins, not model accuracy. No application code changed or regression tests run in this review.

Proposed next increment: configurable backend proxy, validated response, separate labeled saved-weather AI road-risk overlay, ETA selector and road details, graceful outage handling and focused tests. Await user approval before implementation. Saved-snapshot predictions must not be presented as responding to live/replay rainfall, confirmed road status, or implemented arrival-time routing. Dynamic inference still needs a feature/time contract, weather snapshot provenance and model quality semantics. Existing manual team workflow remains intact.
