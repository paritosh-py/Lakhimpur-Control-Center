# Current implementation reference

Audited 2026-10-11 from source. Read with HANDOFF and PROGRESS. Requirements, existing code, historical checks and physical acceptance are distinct.

## Vision and decisions
A coherent flood-response system for Lakhimpur district, Assam: Admin, Team App and Citizen App. Improve existing workspace, do not restart. Flood-focused first; collect other incident reports without claiming independent landslide assessment. Local laptop with internet/LAN. Initial20-hour estimate is historical; remaining deadline unknown.

Live opens by default and can truthfully show calm weather. Historical weather and generated exercise must stay separate with source/original/playback timestamps. Teams must work during exercises too. Severity is assessed risk, confidence is evidence support. Reports optional; repeated device messages are not independent corroboration.

Road arrival predictions belong in Team App, not a new Admin overlay. No model retraining requested. Physical Android phone same Wi-Fi confirmed. Two ESP32 DevKitV1 with nonworking LoRa: intended offline ESP-to-ESP/ESP-NOW demonstration must disclose emulation. Imported BLE code is not physical end-to-end proof. Leaflet retained despite earlier conditional Google Maps key; never reproduce secrets.

Latest appearance request (implemented; see HANDOFF validation): Admin white/light beige, restrained saffron/green, readable text, same layout/content/functionality. Team/Citizen redesign not included.

## Source map
| Layer | Files |
|---|---|
| FastAPI/startup/static serving | backend/app/main.py |
| Admin React19/TypeScript/Vite/Leaflet | apps/web/src/command/LiveOverview.tsx, Assessments.tsx, Teams.tsx, ReportsPage.tsx |
| Team UI | apps/web/src/team/TeamApp.tsx, RoadEstimates.tsx, RouteMap.tsx, NavigationMode.tsx |
| Team Android Java WebView | apps/team-android |
| Citizen Flutter | apps/citizen_flutter/AeroLink-main/apps/mobile |
| Weather | backend/app/services/live_weather.py, backend/app/api/live.py |
| Assessment | backend/app/services/assessments.py, engine/warnings/assessment.py, config/flood_assessment.json |
| Replay/exercise | engine/ingest/source.py, engine/ingest/run.py, data/generators/flood_scenario.py, backend/app/api/scenario.py |
| Teams/persistence | backend/app/services/teams.py, backend/app/api/teams.py |
| Reports/triage | backend/app/services/reports.py, backend/app/api/reports.py |
| Road snapshot proxy | backend/app/api/road_predictions.py |
| Route prototype | backend/app/api/routes.py, engine/routing/route_planner.py |

Old unmounted App/scorer code remains. Its presence/tests do not prove current operational behavior. Do not remove it without approved cleanup.

## Data/provenance
Canonical data/processed contains16 settlement points,800 roads,748 graph nodes,7 reference camps. IDs, not transliterated names, are joins. Sources: GeoNames/OSM/Geofabrik, Copernicus GLO-90, NWIC/SOI boundary, DDMA/ASDMA reference material. See data/SOURCES.md and docs/PHASE_1_DATA_REPORT.md for downloads/license/coverage, including boundary/profile area discrepancy. IMD observations and INDIA-WRIS gauges were suggested but not acquired; do not claim they drive live data.

Open-Meteo Best Match current/recent-hourly values are grid/model estimates, not16 local gauges. Service has10-minute cache TTL,1-minute failure backoff,1-hour stale policy; cache data/runtime/live_weather.json. Unknown remains unknown.

Historical ERA5:25June–5July2024. ASDMA establishes wider flood event, not hourly settlement damage/closures. Original operational availability unknown, not an issued2024forecast. Synthetic rain/reports seed42 default are generated, not reconstructed truth. Coarse terrain susceptibility is not measured flood depth; published camp capacity is not current occupancy.

Canonical names/order (GeoJSON remains authority): Kadam; North Lakhimpur; Gāgaldubi; Diju; Siājuli; Jaihing; Ulubāri; Khuiārpom; Bachāgaon; Naobaicha; Pahumarāgāon; Dulāhātgaon; Nij Lāluk; Chinatoli; Bihpuriāgaon; Bihpuria. Flutter1.0.2+3 exactly matches names/IDs/order/coordinates. GeoJSON lon,lat versus Flutter LatLng lat,lon.

## Actual connected workflows
1. Provider weather -> AssessmentService.live -> settlement map/table/warnings. Completed backward1/3/6/24/72h totals and coverage, wet duration, terrain proxy, separate severity/evidence confidence. Partial/current interval separate. Rules uncalibrated prototype, not official flood alerts.
2. Replay/exercise -> chronological run records -> shared assessment. Live stepping rejected. Generated reports can influence exercise assessments. Run state in process memory; backend processes do not share runs.
3. Manual Admin dispatch -> SQLite context-scoped assignment -> Team token portal -> accepted/en_route/arrived/completed or blocked/resume -> status/messages. Version/idempotency/reservation checks prevent team double booking; completion releases team. Severity changes flag review, not automatic resource optimization.
4. Citizen online -> POST /api/reports?context=live -> Gemini/rule triage -> ReportStore -> Admin reports -> close status API. **AssessmentService.live constructs weather records only, does not read ReportStore. Citizen reports are not yet integrated into live settlement warning/prioritization.**
5. Team route -> route API -> saved-weather30/60/120 predictions -> graph path to settlement/camp. Assignment can expose this estimate in Team UI; it does not submit current/exercise rainfall to model.

## Road-model resolved contract
Owner GET http://10.10.0.169:8002/ml/roads/simple?eta=60. ETA30/60/120 minutes is intended decision-to-arrival duration. Proxy GET /api/ml/roads?eta=60. Env names ROAD_MODEL_BASE_URL, ROAD_MODEL_WEATHER_RETRIEVED_AT. reports.py now loads root.env; older claim nothing loads.env is stale. Never log secret values.

Response model_version=lightgbm_v2_candidate, mode=snapshot_demo, eta_minutes, road_count, predictions[]. Fields road_id,probability_unusable,risk_level,road_status,data_quality_status. Proxy validates probabilities/risk/type/duplicates and exact IDs; absent estimates null. Network503,invalid upstream502,invalid ETA422.

rainfall_1h_mm/3h/6h/24h/72h are backward rolling accumulated millimetres at common timestamp, not intensity/future forecast. Requested road inputs: length,midpoint/min/max elevation,road class. Custom POST/preprocessing contract unverified.

Owner weather retrieval2026-10-10T10:27:51.083909Z, example completion2026-10-10T10:00:00Z; not verified per-road times. Fetch time differs from weather time. Refresh/ETA/exercise stepping do not update rainfall. No verified custom POST.

Simulated usability labels, not real closures. Owner metrics on simulated validation: AUC.96308,Brier.07286,recall87.50%,precision81.35% at.50; not independently reproduced or real-calibrated. CHECK_REQUIRED means uncertain/missing/distribution-shifted inputs, not closure. LOW<.40,MODERATE[.40,.70),HIGH>=.70; LOW does not establish safe/open.

## Route prototype gaps (do not claim complete/safe)
- Undirected nx.Graph; class speeds primary50,secondary40,tertiary30,residential25,unclassified20,track15 km/h; no validated traffic/vehicle/flood speed or directional restrictions.
- Origin Borimuri Basecamp27.2666,94.1255; actual team origin unused; API team_id argument unused.
- Cumulative ETA buckets <=45->30,<=90->60,larger->120; no explicit beyond120 coverage rejection.
- **Missing prediction defaults probability0,LOW,qualityOK; outage can display100% route reliability. This is a defect, not a safe fallback.** Separate proxy null handling does not fix planner defaults.
- Reliability product of(1-p) is not calibrated real-world route safety; dependencies not modeled.
- Caller closure set rejected, but route endpoint passes confirmed_closures=None; no integrated verified closure/evidence reopening registry. Prediction road_status overwrites graph status before closure check, another precedence risk.
- Up to5 candidate paths. When all nonclosed candidates high-risk, one may occupy recommended slot while retaining rejected-risk status.
- Camp chosen by graph time without current capacity/suitability/reservations.
- Model horizons concurrently fetched,3.5s wrapper timeout,45s cache; partial horizon availability can still say connected.
- /api/routes/active selects first context active task without team token or first settlement preview if none. Not secure multi-team personalization.
- Same-target Team background refresh may skip route fetch. Navigation HUD manually advances steps; not GPS turn-by-turn. Closure-triggered replanning incomplete.
These findings await a bounded functional correction; not silently fixed during documentation/theme work.

## Citizen and report details
Flutter lib/services/sos_service.dart separates checking/internet/mesh from receipt. Online shows direct-dashboard progress, never node timeline; requires server report ID; ignores stray mesh ACK. Failures explicit. Received badge replaces Dispatched. No fabricated75 triage score; Gemini label only actual gemini_ai. Close requires server ID and failed close remains open.

lib/services/lakhimpur_service.dart holds canonical list; selected ID forwarded and invalid selected ID rejected client-side, nearest fallback only without selection. Send timeout25s versus server Gemini10s; close8s. Server Config persists host; discovery includes laptop8000/8001,hotspot,emulator,localhost. Phone localhost is phone, not laptop.

Connectivity detects interface, not backend reachability. Cached host can be stale. POST fallback across hosts has no robust deduplication, so timeout/retry can duplicate. Active request state not durably restored after app restart; dashboard-close-to-phone polling sync not verified. Old1023-byte payload cap applies before transport choice. BLE/node/hardware end-to-end unverified.

Report API remaps camelCase, preserves raw description/triage, device counts/history/status. Nearest snap has no geographic-distance cap; API authentication/ownership/context/coordinate validation incomplete. New IDs generated, no robust duplicate-message uniqueness. Repeated device is not independent corroboration. Status new/verified/actioned/dismissed/closed/resolved; no full evidence trust/audit pipeline.

GeminiTriageService uses Gemini2.5Flash when configured, otherwise rule_heuristic; urgency score not calibrated warning confidence. Teammate separate Python/FastAPI NLP endpoint/schema/languages/auth not integrated. REPORT_CONTRACT_PROPOSAL.md is a proposal, not actual API. Preserve raw text/time/source/location/uncertainty in future integration; do not invent contract.

## Runtime and artifacts
State data/runtime/operations.sqlite3 for teams/reports; weather cache alongside. Never delete/reset database or mutate real reports for casual smoke tests. Verify current ports/PIDs before restarting; historical PIDs stale. Separate API processes share database, not run memory.

Setup README.md, scripts/start-team-mobile.ps1, apps/team-android/README.md. Python .venv/Scripts/python.exe. Web npm.cmd run build in apps/web. Flutter flutter.bat test, dart.bat analyze lib/ test/, flutter.bat build apk --debug in mobile folder; C:/flutter/bin. SDK user AppData/Local/Android/Sdk, Android Studio JBR. Verify existing tools, do not reinstall blindly.

Built-web /team-mobile with ?view=team or ?view=roads and team token hash; root Admin usually Vite5173. API8000/8001. Last-known laptop10.10.0.170; model10.10.0.169:8002; verify these. Same-Wi-Fi HTTP is not public internet deployment. Citizen debug manifest permits cleartext. Team wrapper remembers origin, not token.

Citizen1.0.2+3 artifact160821357bytes,SHA256 70EAF5557FC3EE59F50B3D11F8230524D4C553D8A7FADAEA0538BAA972D4A2C6 at audit. Path/endpoint in HANDOFF. Latest phone install unconfirmed. Laptop200/build success is not phone acceptance. PROGRESS separates historical/fresh checks. No application tests rerun solely for context audit.

## Remaining roadmap and approval
Accept latest Citizen physical build; connect reports to settlement evidence with time/context/dedup/trust; fix route unknown/closure/identity/freshness/coverage semantics; obtain real dynamic POST contract; implement route-aware assignment, vehicles/boats/beds/time-window ledger/unmet needs/committed-action replanning; integrate teammate NLP and offline gateway; held-out calibration/matched baseline/five required scenarios/exports/rehearsal. This list is not blanket approval. Propose/test bounded increments and update current docs in place.
