# Lakhimpur Control Center

A flood-response hackathon prototype for **Lakhimpur district, Assam**, connecting a command dashboard, rescue Team App and Citizen App.

## Team

- **Paritosh**  [@paritosh-py](https://github.com/paritosh-py)
- **Atulya**    [atulyavm](https://github.com/atulyavm)

## What is implemented

- Live-first dashboard with current Open-Meteo weather, maps and prototype settlement flood assessments for 16 settlements.
- Separate historical ERA5 weather replay and clearly labeled synthetic disaster exercises.
- Persistent team rosters, manual settlement assignment, task status updates and team messages in live/exercise contexts.
- Citizen Flutter app, online report intake, Gemini triage with a rule-based fallback, and report closure controls.
- Team web portal and Android WebView wrapper, saved-weather LightGBM road-risk estimates, and a graph-routing prototype.
- White/beige Admin interface with readable typography and a single primary navigation bar.

**Prototype limitations:** road predictions use saved weather and simulation-trained labels. Routing has known unknown-input/closure-integration limitations; citizen reports are not yet connected to live settlement assessments. Automatic resource allocation, full replanning and physical end-to-end acceptance remain incomplete. This is not a certified emergency dispatch or safe-routing system. See [current implementation and known gaps](docs/CURRENT_STATE.md) and [verification history](docs/PROGRESS.md).

## Stack and data

React 19, TypeScript, Vite and Leaflet; Python/FastAPI and SQLite; Flutter Citizen App; Java Android Team WebView. The external road model is LightGBM; report triage uses configurable Gemini access.

The study dataset contains 800 road segments, 748 graph nodes, 16 settlements and seven reference relief camps. Sources include OpenStreetMap/Geofabrik, GeoNames, NWIC/Survey of India, Copernicus GLO-90, Open-Meteo and ASDMA. [Source register and limitations](data/SOURCES.md).

The original specification is [NewContext.md](NewContext.md). For continued development, read [AGENTS.md](AGENTS.md), [HANDOFF.md](docs/HANDOFF.md), [CURRENT_STATE.md](docs/CURRENT_STATE.md) and [PROGRESS.md](docs/PROGRESS.md). Requirements are not completion claims.

## Windows setup and run

Workspace-local uv is at `.tools/uv/uv.exe`; managed Python is in `.tools/python`.
No global Python installation or PowerShell activation script is needed.

```powershell
$env:UV_CACHE_DIR = "$PWD\.tools\cache"
$env:UV_PYTHON_INSTALL_DIR = "$PWD\.tools\python"
$env:UV_PYTHON_BIN_DIR = "$PWD\.tools\bin"
.\.tools\uv\uv.exe sync --locked
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/smoke_api.py
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs for interactive API documentation.
`GET /api/health` and `GET /api/config` are read-only.
`POST /api/events/validate` validates and echoes a record; it does not save it.

For a new checkout, install uv from https://docs.astral.sh/uv/getting-started/installation/ or download its official Windows release into `.tools/uv/`.
Then use the setup commands above (substitute `uv` if installed on PATH).
Internet is needed for initial setup and later data acquisition. The core will run on the laptop.
Use `npm.cmd` rather than `npm` under restrictive PowerShell execution policy.

## Open the map

Keep the API command above running. In a second terminal at the repository root:

```powershell
npm.cmd ci --prefix apps/web --cache .tools/npm-cache
npm.cmd run dev --prefix apps/web -- --port 5173
```

Open http://127.0.0.1:5173. Local vectors work without basemap internet; online OSM tiles are opt-in. The Google Maps key is unused. Camp capacities are the published 2025 inventory, not currently available beds.

## Reproduce Phase 1

Raw downloads (about 220 MB) are ignored by Git. Processed datasets and the manifest are included. Rebuild using:

```powershell
.\.venv\Scripts\python.exe scripts/acquire_phase1.py
.\.venv\Scripts\python.exe scripts/extract_osm.py
.\.venv\Scripts\python.exe scripts/build_geography.py
.\.venv\Scripts\python.exe scripts/acquire_phase1.py weather_study
.\.venv\Scripts\python.exe scripts/build_weather.py
.\.venv\Scripts\python.exe scripts/validate_phase1.py
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd run build --prefix apps/web
```

Cache hits verify SHA-256. Preserve original raw files for exact reproduction; rolling download endpoints yield new snapshots on later dates. The terrain regression test requires the raw DEMs. With API/Vite running, browser tests use installed Google Chrome:

```powershell
Set-Location apps/web
npx.cmd playwright test
```

See [Phase 1 data report](docs/PHASE_1_DATA_REPORT.md) and [sources](data/SOURCES.md).

## Citizen Android app

The current Flutter app is in `apps/citizen_flutter/AeroLink-main/apps/mobile`. With Flutter and the Android SDK installed, run `flutter pub get`, `flutter test`, and `flutter build apk --debug` from that directory. Configure the laptop API origin in the app for physical-phone Wi-Fi testing. Debug APKs are built locally and served by the backend at `/citizen-app.apk`; they are not committed to Git. See [online flow validation](docs/CITIZEN_ONLINE_FIX.md).

## Project documents

- [Model/session handoff — start here when switching models](docs/HANDOFF.md)
- [Progress and requirement evidence](docs/PROGRESS.md)
- [Decisions](docs/DECISIONS.md)
- [Open questions](docs/OPEN_QUESTIONS.md)
- [Structure](docs/STRUCTURE.md)
- [API contract](docs/API_CONTRACT.md)
- [Data dictionary](docs/DATA_DICTIONARY.md)

Credentials belong in local environment variables or an ignored `.env` file. Copy `.env.example` and configure your own Gemini key/model and road-model service address. Never commit credentials. The external model service must be supplied separately; its trained weights are not included.


## Android Team App road estimates
A debug Android WebView app now displays the teammate model's saved-weather arrival-risk estimates. See [phone setup and APK build](apps/team-android/README.md). Start the LAN demo with `powershell -ExecutionPolicy Bypass -File scripts/start-team-mobile.ps1`; phone downloads `/team-app.apk` and opens `/team-mobile?view=roads` on port 8001. Keep the model laptop running. This is a labeled snapshot demo, not live routing.

## Repository contents and attribution

Source, configuration templates, processed reference data, synthetic fixtures, tests and continuity documents are included. Local credentials, citizen-report databases, raw download caches, APK/build outputs, development tools and screenshots that may contain report information are excluded. They remain on the development laptop; cloning this repository does not restore those files.

Preserve source attribution and dataset terms in [data/SOURCES.md](data/SOURCES.md). Imported AeroLink source and its existing attribution/license notice are retained under `apps/citizen_flutter/AeroLink-main`; no replacement license is assigned by this upload. Model-owner evaluation figures are not independent validation of this application.
