# Project handoff - read this before continuing

## Citizen settlement parity correction - 2026-10-11

User requested Citizen App settlement names match the dashboard dropdown screenshot. Replaced the incorrect hardcoded town list with all 16 canonical entries from data/processed/settlements.geojson, preserving exact names (including diacritics), IDs, display order and coordinates. Online submission now forwards the selected settlementId from the SOS form and uses it rather than re-snapping to a different nearest settlement; invalid selected IDs are rejected. Nearest-settlement fallback remains only when no settlement is selected.

Citizen version is now 1.0.2+3. Exact 16-entry parity verified programmatically; Dart analysis found no issues. Flutter debug APK build passed (23.9 seconds), version 1.0.2 build 3 ready. No server, source geography, existing reports or dashboard code changed. Next: install the rebuilt Citizen APK at /citizen-app.apk?v=3 and check dropdown and report settlement. This supersedes v1.0.1/build 2 download instructions; direct-internet UI fix is retained.


## Resume and citizen online-flow correction - 2026-10-11

Latest user clarification: installed Citizen App still showed old AeroLink/node timeline when connected to the internet. This resumes/fixes the current citizen increment; it does not authorize a new routing/planning phase. Newer routing/report/Flutter work already existed on disk and was preserved. Historical lower handoff sections about these features being absent are stale; do not use them to remove newer work.

Root cause confirmed in code: SOSTransmissionStageCard selected the online view only after isDeliveredOnline became true; while checking connectivity/awaiting HTTP receipt it rendered the offline mesh timeline. Fixed with explicit checking/internet/mesh delivery-path state and a direct-dashboard progress screen. Internet errors remain internet errors; BLE is never invoked on that path, and stray mesh acknowledgements cannot change an online request. Online completion requires a server report ID. Active report badge now says Received, not Dispatched. Missing triage score no longer fabricates 75. Narrow-screen report/reference/triage/offline labels now wrap.

Other bounded fixes: 25-second send timeout (previous 8 seconds was shorter than server triage timeout), HTTP error preservation, explicit failed-close error, no fallback from server report ID to offline SOS ID for closing, restored non-forced active-request reset guard, debug-only cleartext HTTP for local Wi-Fi. Build version 1.0.1+2. No backend code, report records, active runs or server processes were changed in this correction.

Checks: all 16 Flutter tests passed (existing offline tests now explicitly inject offline connectivity, plus new online service/widget tests). Static analysis passed with no issues; final APK 1.0.1 build 2 assembled and LAN download verified. See CITIZEN_ONLINE_FIX.md. Prior 131 Python/13 browser checks are historical, not rerun for this Flutter-only change. Laptop read-only checks: 8000/8001 health 200, LAN 10.10.0.170:8001 health 200, current 8001 OpenAPI contains report send/close routes. These do not prove physical-phone reachability.

Exact next action: install the new Citizen APK v1.0.1 build 2 over the old app, send on same Wi-Fi, verify Checking connection -> Sending directly to the dashboard -> Delivered via internet; no AeroLink steps on internet. Verify dashboard receipt and phone/dashboard closure. APK endpoint remains /citizen-app.apk on port 8001. Do not confuse this Flutter Citizen APK with /team-app.apk (Team WebView). Physical acceptance is pending.


Updated: 2026-10-11, Asia/Kolkata. This is the current consolidated checkpoint.

## Latest user instruction and exact stopping point

User instruction:
- Citizen app online decoupling: when connected to internet, does not need to send SOS through LoRa Nodes (ESP32). When offline, connect to ESP node and send data through node.
- After "hold to send SOS screen", remove the old hardware timeline screen when online; send directly to the command dashboard with Gemini AI disaster triage.
- On Command Dashboard, reports must be visible when received, with an option to close the request.
- Enable closing the request from both the citizen mobile app and the command dashboard.

Completed Work:
1. **Online Decoupling & Seamless Transmission**:
   - `sos_service.dart`: When online, sends directly via `sendReportOnline()` over HTTP to `/api/reports?context=live`.
   - ESP32 / LoRa BLE transmission completely bypassed when online (zero BLE scanning or connection delays).
   - If offline (`hasInternet == false`), smoothly falls back to BLE mesh transmission with AeroLink ESP nodes.
2. **Replaced Old Hardware Timeline with Online Delivery & Gemini Triage View**:
   - `sos_transmission_stage_card.dart`: When delivered via internet, the old 5-stage timeline (`Emergency data prepared`, `Sending to AeroLink device`, `Confirmed`, `Acknowledged`, `Request completed`) is replaced with an Online Delivery Screen.
   - Displays green `DELIVERED VIA INTERNET` banner, Report Reference, Active/Closed status badge, and Gemini Disaster Triage card (Urgency, Priority Score, Summary, and Recommended Action).
   - Citizen **"✓ Close Request (Mark Resolved)"** button calls `closeOnlineReport()` which posts status `"closed"`.
   - **"Send Another Report"** button allows citizens to clear the screen and submit fresh reports.
3. **Physical Phone Wi-Fi Support & Host Discovery**:
   - `lakhimpur_service.dart`: Candidate host auto-probing (`http://10.10.0.170:8000`, `http://10.10.0.170:8001`, `http://10.0.2.2:8000`, `http://127.0.0.1:8000`). Caches reachable host in `SharedPreferences`.
   - Added in-app Server Config dialog on the SOS screen header for viewing or manually updating the API host IP.
4. **Command Dashboard Request Closure & Filters (`apps/web`)**:
   - `ReportsPage.tsx`: Added dedicated **"✓ Close Request"** button to every active report card, updating status to `"closed"`.
   - Closed reports show a distinct `✓ CLOSED / RESOLVED` badge with a `↺ Reopen Request` button.
   - Filter dropdown with `Active Requests Only` (default), `All Statuses`, `✓ Closed / Resolved Only`, `New`, `Verified`, `Actioned`, `Dismissed`.
   - Summary KPI cards updated with `Active Open` and `Closed / Resolved` counters.
   - React state updated optimistically for instant operator feedback.
5. **Fresh Debug APK Assembled**:
   - Compiled with `flutter build apk --debug`: 153.4 MB APK.
   - Served via FastAPI at `http://10.10.0.170:8001/citizen-app.apk` and `http://127.0.0.1:8000/citizen-app.apk`.

**Validation Checkpoint:**
- 131 Python tests pass in 36.5s (`.venv\Scripts\python.exe -m pytest tests/ -v`).
- 13 Playwright E2E browser tests pass in 51.8s (`npx.cmd playwright test`).
- TypeScript / Vite production bundle built with 0 errors.
- Dart analyze passes with 0 issues (`dart analyze lib/`).
- FastAPI server running on port 8000 (localhost) and port 8001 (Wi-Fi 0.0.0.0 LAN access).
- Vite dev server running on port 5173.
- No secrets stored in git-tracked files.

**Exact next action:**
Citizen app APK is downloadable directly from `http://10.10.0.170:8001/citizen-app.apk`.
User installs the APK on their phone, sends a report via Wi-Fi, and tests closing the request from the phone or dashboard.
## Read order and instruction precedence

1. AGENTS.md.
2. NewContext.md fully: original project specification; never rename or duplicate it.
3. This file, then the current section of docs/PROGRESS.md.
4. docs/TEAM_ANDROID_VALIDATION.md and apps/team-android/README.md for the newest increment.
5. docs/TEAM_WORKFLOW_VALIDATION.md and docs/SLICE_2_VALIDATION.md for retained functionality.
6. For the next task, inspect relevant actual code, docs/API_CONTRACT.md, docs/DATA_DICTIONARY.md, docs/DECISIONS.md and docs/OPEN_QUESTIONS.md.

Latest explicit user requirements override older NewContext design details and historical phase notes. A proposal is not approval. Inspect existing code before editing, preserve completed work, test each approved increment, update this handoff afterward. No clean-slate rewrite is wanted.

## What the user is trying to build

A coherent disaster-response system for Lakhimpur district, Assam, flood-focused first. Admin command dashboard, rescue Team App and Citizen App must eventually work together. Other incident reports may be captured without pretending to assess independent landslide hazards.

- Dashboard opens in Live, using actual current provider weather for 16 study settlements. Calm/no-disaster conditions are valid. Never replace missing weather with fabricated incidents or historical data.
- Historical ERA5 weather replay and synthetic response exercises stay separate and visibly labeled. Historical data retain original timestamps; modified/generated weather and reports are simulated.
- Map and Warnings page assess settlements independently using terrain susceptibility, rainfall amount/duration and available ground reports. Severity and evidence confidence are separate. Reports are optional evidence; absent reports are not invented. Independent corroboration, age and contradictions affect confidence.
- Teams page supports teams such as A/B/C, settlement assignment, task/status/message return, including in exercises. Eventually consider capabilities, availability, route/travel time, shelter suitability and changing needs without losing committed work.
- Dispatcher/Citizen App will receive free text via online/SMS/offline links. Teammate Python/FastAPI NLP service will structure reports. Contract proposal exists but integration does not.
- **Latest correction:** road-accessibility-at-arrival predictions belong in the Team App, not a new dashboard overlay. Start with a simple Android WebView app displaying the teammate model results.
- Future road routing must evaluate arrival-time accessibility; confirmed closures remain binding regardless of low model risk. Resource constraints, unmet needs and replanning are still required later.
- Keep the UI simple, professional and connected to real functionality. No fake buttons, canned incidents or hardcoded results masquerading as live data.

## User decisions already settled

- District: Lakhimpur, Assam. 16 study settlements, 800 road segments.
- Local laptop hosts the app and uses internet/LAN to acquire data. React/TypeScript/Vite/Leaflet + FastAPI/Python + SQLite retained.
- Initial budget was about 20 hours; remaining time not reconfirmed. Do not assume a fresh deadline.
- Physical Android phone, same Wi-Fi as the laptops. Not an emulator.
- Two ESP32 DevKitV1 boards; attached LoRa nonfunctional. Future offline demonstration uses ESP-to-ESP/ESP-NOW, explicitly labeled emulation. Hardware integration not implemented.
- User gave a Google Maps key earlier; Leaflet retained. Never reproduce that key in docs/code.
- No retraining of teammate road model requested. No need to ask the rainfall-window meaning again; it is resolved below.

## Current implementation and relevant files

| Area | Working now | Main files |
|---|---|---|
| Geography | 16 settlements, 800 roads, 748 nodes, 7 published reference camps, waterways and terrain | data/processed; backend/app/api/geography.py |
| Live monitoring | Open-Meteo current conditions and recent hourly rainfall; explicit outages/staleness; live-first UI | backend/app/services/live_weather.py; backend/app/api/live.py; apps/web/src/command/LiveOverview.tsx |
| Settlement assessment | Shared prototype flood screening; 1/3/6/24/72h rainfall totals/coverage, wet duration, terrain proxy, evidence confidence | engine/warnings/assessment.py; config/flood_assessment.json; backend/app/services/assessments.py; apps/web/src/command/Assessments.tsx |
| Replay/exercise | Chronological ERA5 replay across all 16; separate seeded synthetic weather/reports; live cannot step | engine/ingest/source.py; engine/ingest/run.py; data/generators/flood_scenario.py; backend/app/api/scenario.py |
| Teams | Persistent scoped rosters, manual capability/availability-filtered dispatch, status/messages, double-booking/version checks, history and reset isolation | backend/app/services/teams.py; backend/app/api/teams.py; apps/web/src/command/Teams.tsx; apps/web/src/team/TeamApp.tsx |
| Road-model adapter | Read-only validated HTTP proxy, exact ID join, missing predictions null, unavailable/invalid errors | backend/app/api/road_predictions.py |
| Team road display | 30/60/120 ETA selection, road search/filter/details, input quality, snapshot labels; first 100 matches rendered, all 800 searchable | apps/web/src/team/RoadEstimates.tsx; roads.css; main.tsx view=roads |
| Android | Thin native Java WebView, server address, retries, same-origin navigation, Android back/insets; debug APK | apps/team-android; apps/team-android/README.md |
| Phone serving | Built web at /team-mobile; APK at /team-app.apk; same-origin API | backend/app/main.py; scripts/start-team-mobile.ps1 |

Team status lifecycle: assigned -> accepted -> en_route -> arrived -> completed, with blocked/resume and bounded admin cancellation. Busy teams stay reserved; completed task releases team and updates declared location. Reported blockage is NOT automatically a verified road closure. Map markers show assigned destinations/status, not GPS tracks or calculated routes. Changed settlement severity flags review, not automatic reassignment.

Root web view remains live. `?view=team#token=...` is the team portal; `?view=roads#token=...` is road estimates. In-page navigation preserves a team token. Native wrapper remembers the server origin, not the token. requestId.ts provides secure-random IDs on HTTP LAN where crypto.randomUUID is unavailable.

Old App/scorer code remains in the repo but is not evidence of current operational capabilities. Prototype settlement heuristics are not calibrated official warnings. Published camps do not establish current capacity/occupancy. Terrain is a coarse surface model, not measured flood depth.

## Road model: resolved contract and limits

Owner service: GET http://10.10.0.169:8002/ml/roads/simple?eta=60. Supported ETA: 30, 60, 120 minutes, representing intended travel duration from prediction decision to arrival. All three tested responses: 800 unique road IDs, 800 exact matches to GeoJSON properties.id.

Response: model_version=lightgbm_v2_candidate, mode=snapshot_demo, eta_minutes, road_count, predictions[]. Each prediction: road_id, probability_unusable (0..1), risk_level, road_status, data_quality_status. App proxy: GET /api/ml/roads?eta=60. Config ROAD_MODEL_BASE_URL and ROAD_MODEL_WEATHER_RETRIEVED_AT; .env is not automatically loaded.

Rainfall features are backward rolling accumulated totals in mm with a common observation timestamp: rainfall_1h_mm, rainfall_3h_mm, rainfall_6h_mm, rainfall_24h_mm, rainfall_72h_mm. Not intensity or future forecast. Saved weather retrieval supplied by owner: 2026-10-10T10:27:51.083909Z. Rainfall completion 2026-10-10T10:00:00Z was an example; per-road times are not verified. API fetch time is separate from weather time.

Model labels are simulated usability, not verified closures. CHECK_REQUIRED means missing/uncertain/distribution-shifted inputs. Owner reports simulated 2024 ROC-AUC .96308, Brier .07286, recall 87.50%, precision 81.35% at .50; not independently reproduced or calibrated for real deployment.

Display bands: LOW <.40, MODERATE [.40,.70), HIGH >=.70; missing estimate UNKNOWN. Multiply probability by 100 for percent: .000641 -> .0641%. LOW never confirms safe/open. Predictions do not mutate closure records or assignments.

**Critical:** GET uses saved inputs. Refresh/ETA changes do not acquire new weather, and exercise advancement does not alter model rainfall. No verified custom POST endpoint exists yet. Do not call this dynamic live/exercise inference, calculated travel time, route reliability or completed arrival-time routing.

## What is unfinished

Immediate: physical-phone APK installation, native navigation/keyboard/back and phone-to-laptop connectivity testing. No Android device was attached during implementation.

Subsequent work, requiring a bounded approved plan:
- Dynamic model POST feature contract/endpoint, common decision-time timestamps and no-future-data checks. Road min/max elevation and full input preprocessing/provenance remain to validate.
- Route graph travel-time policy, per-segment arrival estimates, route selection, verified-closure workflow and route-specific team display. Current road view lists the whole study network.
- Team recommendations/replanning based on routes, resource/vehicle inventory and shelter occupancy. Preserve committed actions.
- Dispatcher/Citizen App, teammate NLP endpoint/schema/languages/authentication, reliability pipeline and report intake.
- SMS/ESP-NOW transport, hardware wiring and end-to-end testing.
- Matched baseline, real calibration/held-out evaluations, required disruption/resource scenarios and final demo rehearsal.

Do not ask the user to re-explain the vision or already supplied model definitions. Ask only for the contract/configuration needed by the selected next increment.

## Validation checkpoint

- 118 Python tests passed; 21 new road-proxy tests. Existing Starlette deprecation warning only.
- 11 Playwright tests passed in 53.4 seconds. Additional team lifecycle test with crypto.randomUUID unavailable passed in 28.9 seconds.
- TypeScript/Vite production build passed.
- Actual model requests for all ETA values: 800/800 matched roads; new LAN page/APK endpoints HTTP 200 from laptop.
- Android assembleDebug and lintDebug passed. Lint: 0 errors, 8 warnings (documented). Native-device behavior untested.
- Screenshots: docs/screenshots/road-estimates-real-mobile.png and road-estimates-real-desktop.png. The earlier road-estimates-mobile.png contains named test fixtures.
- APK: apps/team-android/app/build/outputs/apk/debug/app-debug.apk; 854674 bytes; SHA256 544B9A7F9386554CE2FD6A72E3E8E76559794D85DBA5413321698E75FCBFD6C6 at last build.
- No tests rerun during this documentation-only save. These are prior verified results, not assertions of current process/network availability.

## Runtime and preservation cautions

Workspace: C:/Users/parit/Desktop/HackMatrix_AL, PowerShell, Python .venv, npm.cmd. Git status at save still lists project files as untracked. Work is saved to disk but not a Git commit or off-device backup. Never git clean/reset away these files.

Last observed servers (recheck before action): phone backend PID 7076 on 0.0.0.0:8001; old backend PID 21332 on 127.0.0.1:8000; Vite PID 22576 on 5173. Laptop Wi-Fi IP 10.10.0.170; model laptop 10.10.0.169. Addresses and PIDs can change.

**Two-process trap:** 8000 retained older loaded backend code. Newly added API is on 8001 until 8000 is restarted. In-memory exercise timelines are NOT shared across processes; 8001 cannot resume 8000's active exercise. For combined assignments/predictions, use one updated backend process and deliberately start a new exercise there after preserving old history. Do not restart/reset a current user exercise merely to tidy servers.

Persistent ledger: data/runtime/operations.sqlite3. Weather cache: data/runtime/live_weather.json. Preserve both, all raw/processed sources, generated scenarios and untracked work. Browser tests created isolated exercise records; no live test assignments were created. SQLite retains assignment history, but backend restart ends its in-memory run. Debug HTTP app is a LAN prototype, not an authenticated public release.

## Resume/run instructions

For the current phone test, if server still available:
1. On phone download http://10.10.0.170:8001/team-app.apk and install.
2. Open Lakhimpur Team, enter http://10.10.0.170:8001, tap Open.
3. Browser alternative: http://10.10.0.170:8001/team-mobile?view=roads.
4. Test ETA choices, search/detail, refresh, failure/retry and Android back. Record actual phone result; do not assume laptop HTTP 200 proves phone reachability.

If stopped, from workspace: `powershell -ExecutionPolicy Bypass -File scripts/start-team-mobile.ps1`. Do not start a duplicate port. Keep model service running. Check Wi-Fi IP/client isolation/firewall if needed; no firewall changes have been made.

Build Android using apps/team-android/README.md (installed Android Studio JBR/SDK, Gradle wrapper 9.3.1, AGP 9.1.0, SDK36). Original commands for regression: `.venv/Scripts/python.exe -m pytest -q --basetemp=tmp/<new-test-directory>`; `npm.cmd run build --prefix apps/web`; in apps/web `npx.cmd playwright test` with appropriate servers. Existing .pytest_temp can have permission conflicts; use a fresh path instead of destructive cleanup.

## Approval state

Completed approved increments: foundations/acquisition, recovery live monitoring, shared settlement warnings/replay, manual teams/status workflow, simple Team Android saved-weather prediction display. The most recent request is SAVE/HANDOFF ONLY. No approval to rewrite, add a dashboard prediction layer, retrain, implement full routing/replanning or proceed through every remaining phase. Verify the phone increment, then seek approval for the user's chosen next step.
