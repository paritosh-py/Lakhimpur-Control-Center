# Product

> Implementation status: read docs/CURRENT_STATE.md. Capability statements below describe the product vision, not verified completion. Admin visual direction updated2026-10-11: white and light beige, restrained saffron/green accents, readable14?16px interface text, existing layout/behavior preserved. This overrides the older dark-dashboard brand note below; other app themes are unchanged.

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

React 19, TypeScript, Vite, Leaflet, Vanilla CSS; FastAPI backend with Python 3.12, Uvicorn, and Pydantic. Single frontend project (`apps/web`) serving three dedicated role views.

## Users

1. **Incident Commanders & Operations Officers (Admin/Dashboard)**: Emergency managers in the district disaster control room coordinating flood response across Lakhimpur, managing resource ledgers, evaluating road network accessibility, and assigning teams.
2. **Field Rescue Team Leads (Team App - Mobile)**: First responders, boat crews, and transport drivers on phones receiving assignments, following risk-aware routes, and reporting field status (Accepted, En Route, Arrived, Road Blocked).
3. **Affected Citizens & Volunteers (Citizen App - Mobile PWA)**: Local villagers in flood-vulnerable settlements receiving localized road forecasts/alerts and sending SOS or road blockage reports over cellular internet or offline ESP32 radio links.

## Product Purpose

A predictive, transparent flood response platform for Lakhimpur district, Assam under the guiding principle: **"Warning in, action out, with proof."** It translates meteorological forecasts, satellite terrain models, and ground reports into predicted arrival-time road passability, constrained resource allocations, and explainable emergency alerts.

## Positioning

Unlike generic flood monitors that display static rain maps or point-in-time hazard alerts, this platform:
- Predicts whether a road segment will still be usable *at expected arrival time* (hours in advance), not just whether it is dry now.
- Provides an **evidence card** for every alert (Why, Confidence with rationale, Data age).
- Solves constrained assignments (teams, boats, shelters) with time-indexed conflict prevention and explicit replanning when roads fail mid-route.
- Functions even during complete cellular blackout via an offline ESP32 radio link.

## Operating Context

- **District Focus**: Lakhimpur district, Assam, India (display timezone: Asia/Kolkata).
- **Physical Road Graph**: 800 road segments, 748 graph nodes forming a single connected study graph along the North Lakhimpur–Kadam corridor.
- **Key Entities**: 16 retained settlements (GeoNames/OSM), 7 official relief camps (DDMA 2025 Disaster Management Plan), 56 mapped waterways (including Subansiri and Ranganadi rivers).
- **Physical Environment**: High-monsoon riverine flood basin; surface elevation modeled via 90m Copernicus DSM.

## Capabilities and Constraints

1. **Mandatory Honest Labeling (Requirement B6)**: Every record, screen, and export carries an explicit provenance source (`live`, `replay`, or `simulated`). Whenever not showing live data, a persistent, unmissable banner displays `SIMULATION: demo-42; seed 42; not live` or `REPLAY: event dated YYYY-MM-DD; not live`.
2. **Confirmed Closures Are Binding**: A confirmed road closure is visually locked and physically impassable. The ML predictive model can *never* reopen a confirmed closure; only verified newer official evidence can lift a closure.
3. **Decision-Time Chronology (No Future Leakage)**: The system strictly segregates observable inputs from hidden ground truth. Predictions and decisions only consume observations with `available_at <= decision_time`.
4. **Three Execution Modes (Phase 2)**:
   - `Live`: Real-time weather and citizen intake.
   - `Replay`: Hourly playback of the historical June 25–July 5, 2024 Assam flood.
   - `Scenario`: Seeded synthetic monsoon flood crisis for demonstrations.
5. **Explainability First (Requirement B4)**: No alert without an Evidence Card.
6. **Dynamic Replanning (Requirement A1.4)**: Road closures trigger automatic rerouting, locking committed actions, and logging "what changed and why".

## Brand & Visual Commitments

- **Tone**: High-stakes disaster operations, tactical, authoritative, calm, high-contrast, zero fluff.
- **Visual Aesthetic**: Tactical mission control & geospatial command console (deep matte obsidian `#0b0c0e`, architectural graphite `#121418` / `#181c22`, safety amber `#f59e0b` primary authority accent, emergency crimson `#dc2626` / `#ef4444`, forest emerald `#10b981`, hydro river blue `#3b82f6` / `#0284c7`, and topographic slate `#64748b`; zero AI neon cyan or purple).
- **Typography**: Editorial sans (`DM Sans`) paired with technical monospace (`JetBrains Mono`) for telemetry, coordinates, and clocks.
- **Disclosed Emulation**: Hardware link disclosed as *"LoRa link emulated using ESP32 (ESP-NOW)"*.

## Evidence on Hand

- Official District Boundary: NWIC/SOI boundary (dtcode 295).
- Real 800-road network and 56 waterways from Geofabrik OpenStreetMap.
- Real 90m Copernicus Digital Surface Model (GLO-90).
- Real 2025 DDMA Relief Camp Inventory (capacities published, real-time availability unknown).
- 40 synthetic flood events pre-generated and deterministically partitioned (24 train, 6 cal, 10 held-out) with zero ground-truth leakage.
