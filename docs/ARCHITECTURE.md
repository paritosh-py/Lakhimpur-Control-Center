> Current-state notice (2026-10-11): read CURRENT_STATE.md and HANDOFF.md first. This supporting document includes earlier design/increment details; it is not complete current implementation or approval evidence.

# System Architecture

Updated: 2026-10-11, Asia/Kolkata.

## 1. High-Level System Overview

```
                               ┌─────────────────────────────────────────────────────────────┐
                               │                    DATA SOURCES & SENSORS                   │
                               │  - Open-Meteo Numerical Weather (Live, 16 study cells)      │
                               │  - ERA5 Historical Reanalysis (June-July 2024 Flood)        │
                               │  - Synthetic Seeded Disaster Generator (72-hour scenarios)   │
                               │  - Teammate LightGBM Road Accessibility Model (30/60/120m)   │
                               │  - Copernicus GLO-90 DSM Elevation/Slope + OSM Road Graph   │
                               └──────────────────────────────┬──────────────────────────────┘
                                                              │
                                                              ▼
                               ┌─────────────────────────────────────────────────────────────┐
                               │                     CORE SHARED ENGINE                      │
                               │                                                             │
                               │  ┌────────────────────────┐    ┌─────────────────────────┐  │
                               │  │   Shared Clocks        │    │    Warning Engine       │  │
                               │  │   LiveClock /          │    │    Multi-factor risk    │  │
                               │  │   ScenarioClock        │    │    Evidence Cards       │  │
                               │  └────────────────────────┘    └─────────────────────────┘  │
                               │                                                             │
                               │  ┌────────────────────────┐    ┌─────────────────────────┐  │
                               │  │  Dual-Leg Route Planner│    │   Report Pipeline       │  │
                               │  │  Basecamp ➔ Settle     │    │   Gemini 2.5 Triage     │  │
                               │  │  Settle ➔ Shelter      │    │   Repeat device alert   │  │
                               │  │  Arrival ETA Risk Eval │    │   Location trust scorer │  │
                               │  └────────────────────────┘    └─────────────────────────┘  │
                               └──────────────────────────────┬──────────────────────────────┘
                                                              │
                                                              ▼
                               ┌─────────────────────────────────────────────────────────────┐
                               │                    FASTAPI BACKEND SERVICE                  │
                               │  - /api/live, /api/scenario, /api/warnings                  │
                               │  - /api/teams (Operations SQLite Ledger)                    │
                               │  - /api/routes (Route Planning & Active Missions)           │
                               │  - /api/reports (Reports SQLite Ledger & Gemini Triage)     │
                               │  - /team-app.apk, /citizen-app.apk, /team-mobile            │
                               └──────────────┬───────────────┬───────────────┬──────────────┘
                                              │               │               │
                                              ▼               ▼               ▼
     ┌────────────────────────────────────────┴───┐   ┌───────┴──────┐   ┌────┴─────────────────────────┐
     │           COMMAND DASHBOARD                │   │   TEAM APP   │   │        CITIZEN APP           │
     │      (React + Leaflet + TypeScript)        │   │ (PWA/Android)│   │       (Flutter Mobile)       │
     │  - Live & Replay Map (16 settlements)      │   │ - Active Leg │   │ - Direct HTTP online send    │
     │  - Explainable Evidence Cards              │   │ - Google-HUD │   │ - BLE mesh offline fallback  │
     │  - Teams & Resource Operations             │   │ - Maneuvers  │   │ - Gemini Triage Screen       │
     │  - Citizen Reports Inbox & Close Request   │   │ - Status sync│   │ - Close Request button       │
     │  - Repeat Device & Escalation History      │   │ - Block rept │   │ - 16 canonical settlements   │
     └────────────────────────────────────────────┘   └──────────────┘   └──────────────────────────────┘
```

---

## 2. Core Modules

### 2.1 Clocks & Time Provenance (`engine/clock.py`, `engine/schemas.py`)
- **LiveClock**: Reads real wall time for live monitoring.
- **ScenarioClock**: Advances explicitly through historical or synthetic simulation time.
- **Provenance Rules**: Every record carries `source` (`live`, `replay`, `simulated`), `event_time`, and `replayed_at` (audit time). No algorithm may branch on the `source` label.

### 2.2 Warning Engine (`engine/warnings/`)
- Multi-factor flood risk scoring: rainfall accumulation windows (1h, 3h, 6h, 24h, 72h), wet duration, DEM surface elevation, slope, and proximity to major waterways.
- Explainable Evidence Cards: plain-language explanation (`why`), confidence rating (`high`/`medium`/`low`), confidence reason, newest data age, estimated lead time, 6-factor metrics grid, and uncertainty disclosures.

### 2.3 Route Planner (`engine/routing/route_planner.py`)
- Undirected NetworkX graph built from `data/processed/graph.json` (800 road segments, 748 nodes).
- **Basecamp Origin**: Permanently pinned at Borimuri Basecamp (`748G+M62`, lat `27.2666° N`, lon `94.1255° E`).
- **Two-Leg Journey**:
  - Leg 1 (Rescue): Basecamp -> Target Settlement.
  - Leg 2 (Evacuation): Target Settlement -> Closest Relief Shelter.
- **Arrival ETA Evaluation**: Evaluates cumulative transit time to map segments into 30m, 60m, or 120m model risk predictions. Confirmed closures are strictly binding; high flood risk ($P \ge 0.70$) triggers alternate routing with plain-language rejection reasons.

### 2.4 Reports & Disaster Triage Service (`backend/app/services/reports.py`)
- Stores reports in SQLite (`data/runtime/reports.sqlite3`).
- **Gemini 2.5 Flash Disaster Triage**: Calls Google Gemini 2.5 Flash API with configured key. Automatically extracts structured disaster fields (urgency: `CRITICAL`/`HIGH`/`MEDIUM`/`LOW`, priority score 0–100, concise summary, action recommendation, trapped counts, casualties, road impassable flags). Graceful fallback to heuristic triage if API is offline.
- **Repeat Device Tracking**: Tracks and alerts on multiple submissions from the same phone/device hash, surfacing escalation in trapped counts or urgency.
- **Location Trust Scoring**: Measures distance between sender coordinates and reported settlement (`on_site`, `nearby`, `not_at_location`).

### 2.5 Operations & Team Ledger (`backend/app/services/teams.py`)
- Stores rosters and dispatches in SQLite (`data/runtime/operations.sqlite3`).
- Strict context isolation between live and exercise runs.
- Double-booking prevention via transactional constraints.

---

## 3. Physical Device & LAN Architecture

- Laptop runs FastAPI backend bound to `0.0.0.0:8001` (LAN access) and `127.0.0.1:8000` (localhost).
- Android phones on the same Wi-Fi network connect to `http://<laptop-ip>:8001`.
- Built APKs:
  - Team App APK: `http://<laptop-ip>:8001/team-app.apk`
  - Citizen App APK: `http://<laptop-ip>:8001/citizen-app.apk`
