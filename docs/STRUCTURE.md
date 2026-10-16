> Current-state notice (2026-10-11): read CURRENT_STATE.md and HANDOFF.md first. This supporting document includes earlier design/increment details; it is not complete current implementation or approval evidence.

# Approved structure

Root remains HackMatrix_AL. Existing NewContext.md is preserved.

Team increment: backend/app/services/teams.py (SQLite team/task ledger), backend/app/api/teams.py (admin and Team App endpoints), apps/web/src/command/Teams.tsx and teams.css (management/assignment UI), apps/web/src/team/TeamApp.tsx (capability-link field view). Runtime database is data/runtime/operations.sqlite3; geography/source files remain separate.

Recovery Slice 2 adds engine/warnings/assessment.py (shared pure screening), backend/app/services/assessments.py (snapshot/rank assembly), apps/web/src/command/Assessments.tsx (warning evidence/page), and config/flood_assessment.json (explicit unvalidated prototype rules). LiveOverview remains the only mounted command surface and contains the shared navigation/map with optional replay controls. Legacy warning/scorer/UI source is preserved but disconnected from production routes.

| Path | Purpose |
|---|---|
| config/ | District, later thresholds, seeded scenario definitions |
| docs/ | Contracts, tracking, architecture and demonstration notes |
| data/raw, processed, replays, generators/ | Source downloads, graph/features, historical records, seeded generation |
| engine/clock.py, schemas.py, config.py | Shared time, validated contracts and district settings |
| engine/ingest, warnings, reports, prediction, routing, allocation, replanning/ | Phase-specific domain modules |
| models/training, saved/ | Training scripts and versioned model outputs |
| evaluation/results/ | Matched baseline evaluation and results |
| backend/app/main.py | API entry point |
| backend/app/api, services, realtime, db/ | Future endpoints, orchestration, updates and persistence |
| apps/web/src/shared, command, team, citizen/ | One frontend with three role views |
| hardware/esp32-phone-node, esp32-gateway, bridge/ | Two firmware projects and serial ingestion |
| exports/replays, resource_ledgers, forecast_features_labels, dispatch_logs, route_checks, baseline_outcomes/ | Generated submission evidence |
| tests/unit, integration, scenarios/ | Contract/unit, API/integration and future full-scenario tests |
| scripts/ | Setup and operational helpers |
| .tools/, .venv/ | Ignored workspace-local tooling and Python environment |
| pyproject.toml, uv.lock | Python dependencies and reproducible resolution |

Later-phase folders contain explanatory README placeholders, not claimed implementations.

Phase 1 additions: scripts/acquire_phase1.py, extract_osm.py, build_geography.py, build_weather.py, validate_phase1.py; engine/ingest/weather.py; backend/app/api/geography.py; apps/web React/Leaflet application and Playwright tests; config/shelter_reference.json, historical_event.json, data_quality_exclusions.json; data/processed GeoJSON/graph/weather/manifest; docs/screenshots/ and PHASE_1_DATA_REPORT.md. Original NewContext.md remains unchanged.


### Team Android increment
- apps/team-android: native Android WebView wrapper, Gradle project/wrapper, build and phone setup README.
- apps/web/src/team/RoadEstimates.tsx and roads.css: Team App road prediction view; requestId.ts supports local HTTP team operations.
- backend/app/api/road_predictions.py: validated saved-snapshot proxy and ID join, no operational state writes.
- scripts/start-team-mobile.ps1: build web assets and serve the phone demo over LAN.
