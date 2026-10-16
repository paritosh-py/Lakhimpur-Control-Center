# Source acquisition register

Recovery Slice 2 (2026-10-10): live runtime acquisition now requests Open-Meteo Best Match `hourly=precipitation,past_days=3` alongside current conditions for the 16 coordinates. Future hourly valid times are excluded from assessment. [Provider interval definitions](https://open-meteo.com/en/docs) define hourly precipitation as the preceding hour's sum. These are model values, not local rain-gauge observations. Runtime data stays in data/runtime; original acquired files are preserved. Historical playback now uses every location in weather_settlements_historical.json (three shared ERA5 grids), not the single-point sample. No new road-closure ground truth was acquired.

Acquired on 2026-10-10. Exact URLs, retrieval timestamps, licensing notes, sizes and SHA-256 hashes are in [the machine-readable manifest](processed/source_manifest.json) and raw sidecar metadata. Raw files are cached locally and excluded from Git. Processed files retain source references.

| Provider | Acquired data / use | Attribution and limits |
|---|---|---|
| [NWIC National Water Data Portal](https://nwdp.nwic.gov.in/) | Official district GIS ZIP; Lakhimpur/Assam selected and transformed from EPSG:7755 to WGS84 | NWIC / source agency Survey of India; see downloaded metadata for reuse terms; published geometry retained |
| [Geofabrik](https://download.geofabrik.de/asia/india/north-eastern-zone.html) / [OpenStreetMap](https://www.openstreetmap.org/copyright) | 2026-10-09 northeastern India PBF; roads and waterways extracted with osmium | OSM contributors, ODbL; graph connectivity does not verify passability |
| [GeoNames](https://download.geonames.org/export/dump/) | India gazetteer, filtered by district attributes and official polygon | CC BY 4.0; 16 selected populated places; Kimin excluded for conflicting administrative context |
| [Copernicus DEM](https://registry.opendata.aws/copernicus-dem/) | GLO-90 2021 tiles N27/E93 and N27/E94, mosaicked before elevation/slope sampling | Copernicus DEM attribution/license in metadata; 90 m surface model, not road-deck or flood-depth measurements |
| [Open-Meteo](https://open-meteo.com/en/docs) | GFS seamless current weather snapshot, October 3–12, 2026; all 16 settlements | CC BY 4.0, noncommercial API; model estimates, not IMD rain-gauge observations; 8 unique grid cells |
| [Open-Meteo historical weather](https://open-meteo.com/en/docs/historical-weather-api) | ERA5 June 25–July 5, 2024; all 16 settlements | CC BY 4.0; retrospective reanalysis; 3 unique grid cells; not historical issued forecasts |
| [ASDMA](https://asdma.assam.gov.in/) | Lakhimpur DDMP 2025–26 PDF; seven camp coordinates and published capacities transcribed from PDF page 48 | Official reference document, not current occupancy/availability; no contact details extracted |
| [ASDMA](https://asdma.assam.gov.in/) | Assam flood memorandum 2024 PDF | Official event context only; district totals cannot label individual road closures |
| [Lakhimpur district](https://lakhimpur.nic.in/) | District profile and map for cross-checking | Profile area differs from GIS polygon area; discrepancy retained in report |

## Access outcomes and substitutions

- Overpass returned server errors/timeouts; the dated Geofabrik PBF supplies OSM features instead.
- The IMD rainfall API returned HTTP 401; a legacy endpoint failed certificate validation. Certificate checks were not disabled. No IMD observations are claimed.
- No usable live INDIA-WRIS river-gauge series was acquired. The related NWIC portal did supply the official boundary. River geometry is from OSM, not measured river levels.
- An older daily flood-report endpoint reset connections; the ASDMA memorandum supplies historical event context instead.
- Google Maps was not used: billing is required for Maps JavaScript API and a free entitlement was not established. The supplied key was neither stored nor used. Leaflet renders local vectors; optional OSM tiles need internet and attribution.

## Processing and coverage

The connected study graph has 800 road segments and 748 nodes, with 16 settlements, 7 camps and 56 waterways. All retained entities are inside the selected boundary. Population, road status, current shelter capacity and occupancy remain unknown. Raw multi-location weather includes an additional subsequently excluded point; normalization maps requested coordinates to retained settlement IDs without shifting indices.

Source snapshots and current geography are not evidence of 2024 road topology. Preserve raw caches for exact reproduction; rolling endpoints may return different data later. See [validation](processed/validation.json) and [Phase 1 report](../docs/PHASE_1_DATA_REPORT.md).

Historical reanalysis is not a historical issued forecast. Generated closures, shelter capacities or population needs must be individually disclosed as simulated even when based on real geographic features.
