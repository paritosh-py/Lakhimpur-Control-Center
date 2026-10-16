# Progress

## Citizen settlement parity correction - 2026-10-11

User requested Citizen App settlement names match the dashboard dropdown screenshot. Replaced the incorrect hardcoded town list with all 16 canonical entries from data/processed/settlements.geojson, preserving exact names (including diacritics), IDs, display order and coordinates. Online submission now forwards the selected settlementId from the SOS form and uses it rather than re-snapping to a different nearest settlement; invalid selected IDs are rejected. Nearest-settlement fallback remains only when no settlement is selected.

Citizen version is now 1.0.2+3. Exact 16-entry parity verified programmatically; Dart analysis found no issues. Flutter debug APK build passed (23.9 seconds), version 1.0.2 build 3 ready. No server, source geography, existing reports or dashboard code changed. Next: install the rebuilt Citizen APK at /citizen-app.apk?v=3 and check dropdown and report settlement. This supersedes v1.0.1/build 2 download instructions; direct-internet UI fix is retained.


## Resume and citizen online-flow correction - 2026-10-11

Latest user clarification: installed Citizen App still showed old AeroLink/node timeline when connected to the internet. This resumes/fixes the current citizen increment; it does not authorize a new routing/planning phase. Newer routing/report/Flutter work already existed on disk and was preserved. Historical lower handoff sections about these features being absent are stale; do not use them to remove newer work.

Root cause confirmed in code: SOSTransmissionStageCard selected the online view only after isDeliveredOnline became true; while checking connectivity/awaiting HTTP receipt it rendered the offline mesh timeline. Fixed with explicit checking/internet/mesh delivery-path state and a direct-dashboard progress screen. Internet errors remain internet errors; BLE is never invoked on that path, and stray mesh acknowledgements cannot change an online request. Online completion requires a server report ID. Active report badge now says Received, not Dispatched. Missing triage score no longer fabricates 75. Narrow-screen report/reference/triage/offline labels now wrap.

Other bounded fixes: 25-second send timeout (previous 8 seconds was shorter than server triage timeout), HTTP error preservation, explicit failed-close error, no fallback from server report ID to offline SOS ID for closing, restored non-forced active-request reset guard, debug-only cleartext HTTP for local Wi-Fi. Build version 1.0.1+2. No backend code, report records, active runs or server processes were changed in this correction.

Checks: all 16 Flutter tests passed (existing offline tests now explicitly inject offline connectivity, plus new online service/widget tests). Static analysis passed with no issues; final APK 1.0.1 build 2 assembled and LAN download verified. See CITIZEN_ONLINE_FIX.md. Prior 131 Python/13 browser checks are historical, not rerun for this Flutter-only change. Laptop read-only checks: 8000/8001 health 200, LAN 10.10.0.170:8001 health 200, current 8001 OpenAPI contains report send/close routes. These do not prove physical-phone reachability.

Exact next action: install the new Citizen APK v1.0.1 build 2 over the old app, send on same Wi-Fi, verify Checking connection -> Sending directly to the dashboard -> Delivered via internet; no AeroLink steps on internet. Verify dashboard receipt and phone/dashboard closure. APK endpoint remains /citizen-app.apk on port 8001. Do not confuse this Flutter Citizen APK with /team-app.apk (Team WebView). Physical acceptance is pending.


## Current status: Citizen Reports, Gemini AI Triage & Flutter Integration — 2026-10-11

| Workstream | Current status |
|---|---|
| Geographic data & Basecamp Pinning | Implemented; Borimuri Basecamp (748G+M62, 27.2666° N, 94.1255° E) pinned in district config, geography API, and maps |
| Live monitoring & Settlement Warnings | Implemented; clean live monitoring on load with zero scenario-endpoint contamination |
| Historical replay & synthetic exercises | Implemented; labeled ERA5 reanalysis & synthetic disaster scenarios with clean `✓ Playback complete` indicator and non-spinning disabled cursor |
| Manual team dispatch & persistence | Implemented; SQLite ledger, isolated contexts, multi-team support; stationed teams rendered on map and in settlement details panel; persists across reloads |
| Teammate road-model connection | Implemented; concurrent 30/60/120m arrival horizon queries joining 800 road segments; 45s in-memory TTL caching |
| Route planning & Arrival ETA Evaluation | Implemented; dual-leg pathfinding (Basecamp → Settlement → Shelter) evaluated at arrival ETA |
| Confirmed closures & Rejection explanations | Implemented; binding closures strictly rejected; plain-language rejection reasons for avoided paths |
| Turn-by-Turn Navigation HUD | Implemented; Google Maps-style navigation HUD in Team App with maneuvers, ETA, and mission action buttons |
| Team Mobile Portal Stability | Implemented; decoupled background polling prevents re-render flashing and preserves map state |
| Team Android Native Wrapper & APK | Implemented; apps/team-android built; defaults to team view; APK served at /team-app.apk |
| Citizen Reports & Gemini AI Triage | Implemented; Control Center reports dashboard with Close Request action, Gemini 2.5 Flash live API prioritization, offline heuristic fallback, repeat device tracking |
| Citizen Flutter App Decoupling & Ingestion | Implemented; direct online HTTP messaging (zero LoRa/BLE overhead when online), offline ESP node fallback, new online delivery triage screen with Close Request, host auto-probing for physical phone Wi-Fi |
| Full Test Suite Verification | 131 Python tests pass (100%); 13 Playwright E2E browser tests pass (100%); TS/Vite build passes; Dart analyze 0 issues |

### Citizen Field Reports, Online Decoupling & Request Closure (2026-10-11)
1. **Online vs Offline Mesh Decoupling**:
   - In `apps/citizen_flutter/.../sos_service.dart`, when internet is present (`hasInternet == true`), reports send directly to the Command Dashboard via HTTP `POST /api/reports?context=live`.
   - LoRa / ESP32 node transmission is completely bypassed when online.
   - Offline fallback: if internet is unavailable, users can connect to an ESP32 AeroLink node via Bluetooth to transmit over the local mesh.
2. **Replaced Old Timeline Screen with Online Delivery & Gemini Triage View**:
   - In `sos_transmission_stage_card.dart`, the old 5-stage timeline (`Emergency data prepared`, `Sending to AeroLink device`, `Confirmed`, etc.) is bypassed when online.
   - Rendered dedicated `_buildOnlineSuccessCard`: green `DELIVERED VIA INTERNET` header, Report Reference, Active/Closed status badge, Gemini Disaster Triage card (urgency, priority score, summary, and action guidance).
   - Citizen **"✓ Close Request (Mark Resolved)"** button calls `closeReportOnline()` (`POST /api/reports/{id}/status` with `status: "closed"`).
   - **"Send Another Report"** button resets state cleanly.
3. **Physical Phone Wi-Fi Auto-Discovery (`lakhimpur_service.dart`)**:
   - Auto-probes candidate hosts on Wi-Fi (`http://10.10.0.170:8000`, `8001`, `10.0.2.2:8000`, `127.0.0.1:8000`), persisting active host in `SharedPreferences`.
   - Added in-app Server Config dialog accessible from the SOS screen header.
4. **Command Dashboard Request Closure & Filters (`apps/web`)**:
   - `ReportsPage.tsx` updated with dedicated **"✓ Close Request"** button on each active report card.
   - Closed reports render a distinct `✓ CLOSED / RESOLVED` badge with a `↺ Reopen Request` option.
   - KPI strip includes `Active Open` and `Closed / Resolved` counters.
   - Filter bar features a Status dropdown: `Active Requests Only` (default), `All Statuses`, `✓ Closed / Resolved Only`, `New`, `Verified`, `Actioned`, `Dismissed`.
   - Optimistic UI updates ensure instant operator responsiveness.
5. **Fresh Debug APK Assembled**:
   - Fresh 153.4 MB APK compiled with `flutter build apk --debug`.
   - Served directly at `http://10.10.0.170:8001/citizen-app.apk` and `http://127.0.0.1:8000/citizen-app.apk`.

## Historical progress entries (retained for audit)

## 2026-10-11 ? Team Android road-estimates increment

User explicitly approved starting a simple Android WebView app and moved model prediction display to the Team App, not the command dashboard. User will test on a physical Android phone on the same Wi-Fi. This supersedes the prior proposed dashboard overlay.

Implemented: validated read-only `/api/ml/roads?eta=30|60|120` proxy, exact road joins, missing-estimate preservation and explicit errors; React Team App road screen (`?view=roads`) with travel-horizon selector, search/filter/details, input quality and visible saved-weather labels; native Java WebView wrapper in apps/team-android, Gradle wrapper, Android 8+ debug APK, native server-address setup and error recovery. Built web app served by FastAPI at `/team-mobile`; APK at `/team-app.apk`. Existing team token survives in-page navigation; HTTP Wi-Fi request-ID fallback tested. No dashboard risk overlay was added.

Verified: real upstream 30/60/120 responses each join 800/800 roads; phone-facing LAN page and APK download return HTTP 200 from this laptop. 118 Python tests pass using a fresh temp directory (existing .pytest_temp permissions blocked the first run). All 11 browser tests pass in 53.4 s; additional team lifecycle rerun with randomUUID unavailable passes. TS/Vite production build passes. Real-API mobile and desktop screenshots inspected. APK assembled successfully; final Android lint/build status is recorded in TEAM_ANDROID_VALIDATION.md. No physical device was attached, so Android installation, native interaction and phone-to-laptop reachability remain user verification.

Current phone server: 0.0.0.0:8001, PID 7076 at checkpoint (verify before restarting); Wi-Fi IP 10.10.0.170 may change. Existing backend 8000 and Vite 5173 were left running. Port 8000 has old loaded backend code until restarted; the new standalone demo is on 8001. Active replay state is per process; old exercise contexts cannot be resumed by the new process. Persistence/raw data preserved. See apps/team-android/README.md for startup, download and build steps.

Exact next action: user installs the debug APK from http://10.10.0.170:8001/team-app.apk and enters http://10.10.0.170:8001 in the app. Validate on the physical phone before the next increment. Dynamic POST inference, routing, automatic travel-time calculation, route-specific segment selection, replanning and model calibration remain pending. No approval inferred for these larger phases.


## Recovery status (latest)

2026-10-11: approved TEAM INCREMENT COMPLETE. Persistent isolated rosters, manual settlement dispatch, Team App task/status/messages, map links, conflict/version checks, reset archives and preserved commitments. 97 Python tests, 9 browser tests and production build pass; TEAM_WORKFLOW_VALIDATION.md. Full Recovery Slice 4 remains partial: no road-model/route/ETA, shelter/vehicle reservations or automatic planner. Dispatcher/citizen NLP remains not started. This supersedes the in-progress entry below.

2026-10-11: Teams workflow explicitly approved out of sequence, in progress. SQLite persistence, exercise isolation, manual assignments, Team App/status updates and linked map are this increment. NLP/citizen intake, route model, shelters/transport allocation and automatic replanning remain unfinished.

Slice 2 completed: shared settlement assessment, Warnings page/map evidence, correct complete rainfall windows and duration, prototype terrain response, separate confidence and report support, retrospective ERA5 replay for all 16 settlements, and synthetic chronology/mapping repairs. 90 Python tests, 8 browser tests, production build pass. See SLICE_2_VALIDATION.md for precise scope and uncalibrated-rule limitations. Original B2/B3/B4 claims below are superseded: settlement screening works; road warning/closure verification and operational prediction do not. Slice 3 is awaiting approval; no full-project completion is claimed.

Slice 2 approved and in progress: rainfall windows/duration, terrain susceptibility, independent severity/confidence, Warnings page and corrected replay. Validation pending. This supersedes pending-approval notes below.

Slice 1 explicitly approved and completed: live-default Overview, actual current per-settlement weather, consistent map/table/details, source freshness/errors, rejection of live playback. 86 Python tests, 8 browser tests and production build pass; see SLICE_1_VALIDATION.md. Slice 2 awaits approval. Original-phase Done labels below are historical and remain subject to COMMAND_DASHBOARD_AUDIT.md.

Updated 2026-10-10, Asia/Kolkata. Phases 0–1 foundation retained. Phases 2–3 reopened for correctness review following COMMAND_DASHBOARD_AUDIT.md. Correction implementation and Phase 4 await an approved plan; user is clarifying dashboard expectations. Historical completion evidence below is not acceptance of the audited behavior.

| Phase | Status | Evidence / remaining work |
|---|---|---|
| 0 Foundation | Done | Scaffold, contracts, configuration, clocks, API, tracking; 16 tests and actual HTTP smoke pass (docs/PHASE_0_VALIDATION.md) |
| 1 Geography and data | Done | 800 roads, 16 settlements, 7 reference camps, terrain, current/historical weather and map; 29 Python tests, 2 browser tests, production build pass; PHASE_1_DATA_REPORT.md |
| 2 Source adapters, generators & UI overhaul | Done | Common SourceAdapter, RunState, LiveWeatherAdapter, ReplayWeatherAdapter, ScenarioAdapter, 40 synthetic events batch (24 train / 6 cal / 10 held-out), strict observable vs truth separation, scenario start/step/reset/stop API, map UI controls and persistent B6 banner; Impeccable craft floor audit completed (zero AI slop, strict 8pt grid, 3-pane tactical console, DM Sans + JetBrains Mono); 66 Python tests, 3 Playwright tests pass; validate_phase2.py passes |
| 3 Warning engine | Done | Multi-factor risk scorer (rain 1h/3h/6h + forecast + DEM elevation/slope + river proximity + saturation API + reports), confirmed closures score 100 critical, dynamic re-ranking with plain-language reasons (B3), explainable Evidence Cards with confidence rating, lead time, data age, and uncertainty disclosure (B4); 79 Python tests, 4 Playwright browser tests pass; validate_phase3.py passes 100% |
| 4 Reports and trust | Not started | LLM, proximity, conflict and staleness |
| 5 Prediction and routing | Not started | Event split, calibration, arrival routes |
| 6 Allocation and ledger | Not started | Resources, reservations and unmet needs |
| 7 Replanning | Not started | Triggers, commitments and audit |
| 8 Three apps | Not started | One React project, three views |
| 9 Hardware | Not started | Board/pin confirmation and ESP-NOW test |
| 10 Evaluation | Not started | Matched baseline and automatic exports |
| 11 Rehearsal | Not started | Two clean runs and backup video |

## Mandatory requirement evidence

| ID | Status | Evidence / acceptance still needed |
|---|---|---|
| B1 | Done | config/district.yaml, official boundary, bounded graph; tests/integration/test_geography.py checks coverage |
| B2 | Done | Multi-factor flood risk scorer calibrated for Brahmaputra basin (16 settlements + 75 primary roads); confirmed road closures strictly score 100.0 critical; tests/unit/test_warning_scorer.py and tests/integration/test_warnings_api.py |
| B3 | Done | Dynamic re-ranking with plain-language explanation (`rerank_reason` + `rank_delta`) upon weather shifts or road closures; tests/integration/test_reranking.py and apps/web/tests/warning.spec.ts |
| B4 | Done | Explainable Evidence Card for every warning: plain-language `why`, `confidence` (`high`/`medium`/`low`) + `confidence_reason`, `data_age_seconds`, `lead_time_hours`, 6-factor metrics grid, and honest `uncertainty_disclosure`; tests/unit/test_evidence_card.py and warning.spec.ts |
| B5 | Not started | Held-out false alerts and invalid routes for both systems |
| B6 | Done | `source=replay` requires original event_name and replayed_at timestamp; persistent banner on app shows "REPLAY: event dated X" or "SIMULATION: demo-42; seed 42; not live"; Playwright tests verify banner and mode controls; validate_phase2.py confirms zero unlabeled records |
| A1.1 | Not started | Constrained solver assignments with valid routes |
| A1.2 | Not started | Transactional time-indexed ledger, no double-use/overflow; schema bounds alone do not meet this |
| A1.3 | Not started | Unserved settlements and machine-readable reasons |
| A1.4 | Not started | Triggered replan, preserved completed/committed actions, labels |
| A2.1 | Partial | require_available guard, future forecast/late report tests, and strict observable/truth isolation in 40 generated events; full feature builder and trained model in Phase 5 |
| A2.2 | Not started | Uncertainty-based route/plan comparison and binding closures |
| A2.3 | Not started | Matched held-out predictions, invalid routes, response delays |

Required demo situations (all not started): deteriorating access; confirmed closure; insufficient shelter/transport; conflicting/stale reports; unserved settlements and replanning.

Required submission artifacts (all not started): labeled road/event replays; resource ledgers; forecast features/labels; dispatch logs; route checks; matched baseline outcomes.

## Known limitations

- Acquired datasets and reference map are complete. Operational persistence, LLM calls, trained model, solver and hardware code remain later phases.
- Report validation endpoint does not ingest/save reports; event validation is explicitly non-persistent.
- Starlette emits a deprecation warning for its httpx TestClient integration; tests pass. No warning suppression is configured.
- IMD observations and WRIS gauges unavailable; weather is modeled. Current road passability and shelter availability unknown. Boundary area discrepancy and all data limits are in PHASE_1_DATA_REPORT.md.


## 2026-10-11 ? Teammate LightGBM V2 integration review (no implementation approval)

Reviewed the supplied integration prompt and current map road identifiers. Read-only requests to the teammate LAN API `/ml/roads/simple?eta=30`, `60`, and `120` succeeded: each returned model_version `lightgbm_v2_candidate`, mode `snapshot_demo`, 800 predictions, 800 exact matches to roads.geojson properties.id, and no duplicate road IDs. This verifies transport and joins, not model accuracy. No application code changed or regression tests run in this review.

Proposed next increment: configurable backend proxy, validated response, separate labeled saved-weather AI road-risk overlay, ETA selector and road details, graceful outage handling and focused tests. Await user approval before implementation. Saved-snapshot predictions must not be presented as responding to live/replay rainfall, confirmed road status, or implemented arrival-time routing. Dynamic inference still needs a feature/time contract, weather snapshot provenance and model quality semantics. Existing manual team workflow remains intact.
