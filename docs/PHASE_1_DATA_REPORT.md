# Phase 1 data and validation report

Completed 2026-10-10 for Lakhimpur district, Assam. This is the data and reference-map foundation, not an operational flood-warning or dispatch system.

## Delivered coverage

| Dataset | Final coverage |
|---|---|
| Official district boundary | NWIC / Survey of India polygon, transformed to WGS84 |
| Bounded road graph | 800 segments, 748 nodes, one connected component |
| Settlements | 16 gazetteer places inside the district polygon |
| Relief camps | 7 published reference sites; current occupancy and availability unknown |
| Waterways | 56 OSM features |
| Terrain | Copernicus GLO-90 surface elevation and local slope; no missing sampled values |
| Current weather snapshot | 16 locations, 8 model grid cells, 3,840 hourly records; no missing values |
| Historical weather | 16 locations, 3 ERA5 grid cells, 4,224 hourly records; no missing values |
| Acquisition integrity | 14 raw source files with verified SHA-256 hashes |

The study area is the North Lakhimpur–Kadam corridor, not every road in the district. Maximum settlement-to-road distance is 739.9 m; maximum camp-to-road distance is 72.7 m. These are nearest-geometry distances, not verified last-mile routes.

## Provenance and limits

- The NWIC GIS polygon measures approximately 2,922.5 square kilometres after projection to UTM 46N, while the district profile states 2,277. The polygon is preserved as published; the mismatch remains unresolved and is visible in dataset limitations.
- Kimin was excluded conservatively: its gazetteer administrative label conflicts with Papum Pare's official directory. Raw data remains intact; the exclusion is recorded in config/data_quality_exclusions.json.
- Camp coordinates and published capacity values come from the 2025–26 district plan. Current capacity and occupancy are null. Malformed coordinates in other rows were not guessed.
- Elevation is a 90 m digital surface model. It cannot resolve road decks, small embankments or actual flood depth. Tiles are mosaicked before slope sampling to avoid seam artifacts.
- Current weather covers October 3–12, 2026 UTC; historical weather covers June 25–July 5, 2024 UTC. Multiple settlements share model grid cells; they are not independent stations.
- ERA5 is retrospective reanalysis. Original forecast issuance/availability is not invented. Historical weather cannot be used as if a 2024 operator had the reanalysis in real time.
- Official historical flood documents supply event context, not per-road closure labels. No population, travel time, closure truth or current shelter availability was invented.
- IMD authentication and WRIS gauge access remain unavailable. Open-Meteo provides modeled weather; OSM waterways do not substitute for observed river levels.

## Delivered software

Acquisition caches raw sources with metadata and checksums. Builders derive the graph, terrain, entities and normalized weather. FastAPI serves read-only geography, source and weather endpoints. React/Leaflet displays the layers, evidence inspector, weather chart and explicit reference-only labels on desktop and mobile. Online basemap tiles are optional; cached vectors render locally.

## Validation

- 29 Python tests passed, including original foundation tests, geographic containment/connectivity, weather chronology and missing data, corrupt-cache detection, DMS validation and terrain seam regression.
- 2 Chrome browser tests passed: layer rendering/toggling, shelter evidence, desktop/mobile layout, and visible API failure/retry behavior.
- TypeScript checks and Vite production build passed.
- Raw source integrity: 14 hashes verified; dataset coverage recorded in data/processed/validation.json.
- Desktop and mobile screenshots are in docs/screenshots/.

One upstream Starlette TestClient deprecation warning remains; no test failures. Full role apps, scenario playback, hazard scores, model training, routing, allocation and hardware are later phases.

Run and reproduction commands are in README.md. Exact source URLs, dates and hashes are in data/processed/source_manifest.json; the human-readable register is data/SOURCES.md. Proposed next work is docs/PHASE_2_PLAN.md and requires phase approval.
