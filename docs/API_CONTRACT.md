> Current-state notice (2026-10-11): read CURRENT_STATE.md and HANDOFF.md first. This supporting document includes earlier design/increment details; it is not complete current implementation or approval evidence.

# API Contract

Updated: 2026-10-11, Asia/Kolkata.

## 1. System & Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status, version, and injected UTC clock time |
| `GET` | `/docs` | Interactive OpenAPI Swagger UI |
| `GET` | `/openapi.json` | OpenAPI 3.1 JSON schema |

---

## 2. Geography (`backend/app/api/geography.py`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/geography/summary` | Bounding box, counts of settlements, roads, shelters, and waterways |
| `GET` | `/api/geography/{layer}` | GeoJSON FeatureCollection for `boundary`, `roads`, `waterways`, `settlements`, or `shelters` |

---

## 3. Live Weather & Monitoring (`backend/app/api/live.py`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/live/conditions` | Real-time Open-Meteo weather snapshot for 16 study settlements, hourly rainfall accumulation (1h, 3h, 6h, 24h, 72h), staleness flags, provider metadata, and flood screening assessments |

---

## 4. Replay & Synthetic Exercises (`backend/app/api/scenario.py`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/scenario/start` | Starts an exercise (`mode: "replay"` for ERA5 2024 flood reanalysis, or `mode: "scenario"` with `seed` and `duration_hours` for synthetic flood exercise). Returns run ID |
| `POST` | `/api/scenario/step` | Advances the active exercise by 1 hour |
| `POST` | `/api/scenario/reset` | Resets the exercise timeline back to step 1 |
| `POST` | `/api/scenario/stop` | Stops the active exercise and clears run state |
| `GET` | `/api/scenario/status` | Returns whether an exercise is active, current step index, run ID, and exhaustion flag |
| `GET` | `/api/scenario/snapshot` | Returns the current weather and flood assessment snapshot for the active exercise step |

---

## 5. Settlement Warnings (`backend/app/api/warnings.py`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/warnings/summary` | Summary of active warnings across settlements, highest-risk entities, and severity counts (`?mode=live` or `?mode=exercise`) |
| `GET` | `/api/warnings/settlements` | List of all settlements ranked by risk score with severity and primary drivers |
| `GET` | `/api/warnings/{id}/card` | Full Explainable Evidence Card for a specific settlement |

---

## 6. Teams & Operations (`backend/app/api/teams.py`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/teams/state?context=live\|{run_id}` | Complete operations ledger: active team roster, assignments, and audit event history |
| `POST` | `/api/teams?context=...` | Adds a team (name, initial settlement location, member count, capabilities) |
| `PUT` | `/api/teams/{id}?context=...` | Updates team details or availability |
| `POST` | `/api/teams/assignments?context=...` | Dispatches a team to a settlement with task instructions. Enforces single active commitment |
| `POST` | `/api/teams/assignments/{id}/cancel?context=...` | Cancels an uncommitted assignment |
| `GET` | `/api/teams/portal` | Team portal state for team leads via Bearer token |
| `POST` | `/api/teams/portal/{assignment_id}/updates` | Updates status (`accepted`, `en_route`, `arrived`, `completed`, `blocked`) and appends status messages |

---

## 7. Road Accessibility Model Proxy (`backend/app/api/road_predictions.py`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/ml/roads?eta=30\|60\|120` | Proxies upstream LightGBM road predictions for 800 segments from `http://10.10.0.169:8002/ml/roads/simple`. Returns probability unusable, risk level, data quality, joined with GeoJSON road properties. In-memory 45s TTL cache |

---

## 8. Routing & Google Maps-Style Navigation (`backend/app/api/routes.py`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/routes/plan?settlement_id={id}&team_id={optional}` | Computes dual-leg route (Leg 1: Basecamp -> Settlement; Leg 2: Settlement -> Shelter) evaluated against arrival ETA road model predictions. Returns recommended route, alternatives, plain-language rejection explanations, polyline, and turn-by-turn maneuvers |
| `GET` | `/api/routes/active?context=live\|{run_id}` | Returns the navigation mission plan for the active assignment, or defaults to first study settlement for instant live navigation |

---

## 9. Citizen & Field Reports (`backend/app/api/reports.py`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/reports?context=live\|{run_id}&status={optional}` | Returns all submitted citizen reports, repeat device alerts, and KPI summary counters |
| `POST` | `/api/reports?context=live\|{run_id}` | Ingests a citizen report from online or offline mesh. Triggers Gemini 2.5 Flash Disaster Triage and location trust scoring |
| `POST` | `/api/reports/{id}/status?context=live\|{run_id}` | Updates report status (`new`, `verified`, `actioned`, `closed`, `dismissed`) |
| `POST` | `/api/reports/{id}/verify?context=live\|{run_id}` | Marks a report as verified or dismissed with operator notes |

---

## 10. Static Apps & Mobile Downloads (`backend/app/main.py`)

| Path | Description |
|---|---|
| `/team-mobile` | Serves the built Team Mobile web portal |
| `/team-app.apk` | Serves the Android native WebView debug APK |
| `/citizen-app.apk` | Serves the Flutter Citizen App debug APK |
