> Current-state notice (2026-10-11): read CURRENT_STATE.md and HANDOFF.md first. This supporting document includes earlier design/increment details; it is not complete current implementation or approval evidence.

# Data dictionary v0.1

## Team ledger

Team: id, context (live or exercise run ID), name, manually declared location settlement, members, capabilities, available and private capability token. Runtime location updates on an arrived/completed task are team-reported, not GPS. Assignment: target settlement, instructions, required capability, status/version, source, original event_time, recorded_at, immutable dispatch evidence and idempotency request_id. Team events retain status/message, actor, event_time and recorded_at. States: assigned → accepted → en_route → arrived → completed; accepted/en_route/arrived may become blocked; blocked → en_route is explicit resumption. Cancelled is only possible from assigned/accepted via admin. All non-terminal statuses reserve the team. Live and every exercise use separate inventories; historical-weather exercise assignments remain simulated.

## Recovery assessment fields

`rainfall.rain_mm` keys 1/3/6/24/72 are complete preceding-hour precipitation sums (rain/showers/snow water equivalent), in mm. End is the most recent complete UTC hour; no proportional interpolation. `coverage_hours` reports actual non-null hourly counts; incomplete sums are null. `wet_duration_hours` is consecutive hourly intervals >=0.1 mm; `duration_at_least` marks a truncated/gapped beginning. `latest_interval_mm/minutes` is separate current interval evidence and is never added again to the hourly history.

`terrain.factor/level` is a prototype susceptibility proxy from flatness and river distance. Elevation is surface elevation, not water depth. `severity` is unknown/none/watch/high/critical; none means no elevated screening signal, not verified safety. `confidence` is low/medium/high evidence support, distinct from severity. `evidence_strength` and `score` are rule-based indices, not probabilities. See config/flood_assessment.json and SLICE_2_VALIDATION.md for limitations.

Replay weather SourceRecord payload retains original_available_at (null if unknown), acquisition timestamp and availability_basis. The adapter's available_at is explicitly a retrospective playback release time. It must never be claimed as verified historical publication time or fed into a historical operational performance comparison as though it were known then.

Authoritative field constraints: engine/schemas.py and generated /openapi.json.

## Common records

- id: nonempty entity/event identifier, no whitespace.
- run_id: execution identifier; future persistence must partition by this value.
- provenance.source: live, replay (real historical data), or simulated (generated).
- provider: origin of the datum, distinct from source mode.
- event_time: original observation/event time; for forecasts, issue time.
- available_at: when usable by the decision maker on the event timeline, including known publication/receipt delays. Must not precede event_time. Unknown historical availability must not be invented as verified fact.
- recorded_at: wall timestamp at platform recording; not a model feature.
- event_name, replayed_at: mandatory historical event identity and wall playback timestamp for replay. Original event timestamp remains event_time.
- valid_at: time a weather value describes. Forecast validity may be later than decision time; its issue/availability may not.
- All timestamps: ISO 8601 with timezone. Compare as aware datetimes; clocks emit UTC, UI will display Asia/Kolkata.
- display_label: computed LIVE / SIMULATION / REPLAY label; response formatting must preserve it. Future banners/exports are not implemented.

## Domain contracts

- Location: WGS84 latitude [-90,90], longitude [-180,180].
- Settlement: name, location, optional nonnegative population; unknown is null.
- RoadSegment: directed node IDs, positive length_m/travel_minutes, status unknown/open/at_risk/confirmed_closed. Graph and closure evidence added later.
- Shelter: name/location, nonnegative capacity and occupied; occupied cannot exceed capacity. Reservations added in ledger phase.
- Report: raw_text, internet/esp_now transport, optional sender location, settlement/road IDs and people_count. Transport size is a separate firmware byte constraint.
- Resource: team/vehicle/boat, location, capacity, status.
- Assignment: settlement/team, optional vehicle/shelter, ordered road IDs, positive [starts_at,ends_at) reservation window, status. Foreign-key, closure, overlap and temporal occupancy checks belong to Phase 6.
- WeatherObservation: observed/forecast/reanalysis, precipitation_mm >= 0, interval_minutes > 0, location, valid_at.
- Event: kind weather/report/closure/resource_change/assignment_update; entity_id references its typed payload. Envelope validation does not resolve that reference yet.

## Planned prediction features and labels

Features: rainfall sums over 1/3/6 hours, issued forecast rainfall, antecedent saturation proxy, elevation, slope, distance to river, road type, past closure information, latest report state/age, minutes to segment arrival. Units and derivations must be finalized with actual Phase 1 sources. No future ground truth enters features.
Label: usability (1 usable, 0 unusable) at expected arrival according to held-out event truth. Split whole event sequences; keep calibration and tuning separate from final test events.

## Evaluation definitions (before implementation)

- Invalid route: any dispatched route containing a confirmed closure at dispatch, or an actually unusable segment when reached. Rate denominator: dispatched routes. Also report counts; zero denominator is N/A.
- Response delay: first team arrival minus time need became known. Report mean, median, maximum among served settlements; report unserved count and elapsed waiting separately to avoid hiding failures.
- False-alert rate: warnings whose defined outcome does not materialize within the configured horizon / warnings with a fully observable horizon. Horizon/outcome thresholds await confirmation; incomplete follow-up excluded and counted separately.
- Prediction quality: precision/recall for unusable roads (risk=1-usability), ROC AUC and Brier score, reliability curve; report per event and pooled. Single-class AUC is N/A. Classification threshold chosen on validation events only.
- Population served: unique people served under scenario identifiers; shelter use: actual and reserved occupancy over time; unmet needs: reason code, description, opened/resolved timestamps.
- Baseline: same initial resources, solver, constraints, events, decision times, and binding closures. Only road accessibility inputs differ. Never tune on held-out events.

These are contracts and evaluation definitions, not computed results.

## Phase 1 reference datasets

Static GeoJSON is reference inventory, not an operational engine Record. Its provenance.source=live means acquisition from a current public source; recorded_at is acquisition time. Provider/reference_year/label describe evidence age. It never asserts live road safety or camp availability. Conversion into operational records remains Phase 2 work.

- Boundary: official NWIC/SOI district 295, original EPSG:7755 converted to WGS84. Projected area explicitly differs from the profile statistic.
- Roads: physical segments; from_node/to_node follow original OSM way order. oneway, bridge, surface and maxspeed tags preserved. length_m measured in UTM 46N. status=unknown, travel_minutes=null. No synthetic last-mile edges.
- Settlements: GeoNames IDs, population=null, feature code/modification date; administrative and polygon checks, explicit exclusions. GeoNames admin codes 03/307 differ from NWIC code 295.
- Camps: DDMA page 48 published_capacity, reference_year=2025; current_capacity/occupied=null and operational_status=unverified. Malformed source DMS excluded, not guessed.
- elevation_m: nearest-cell Copernicus surface altitude, not road deck height. slope_degrees: central difference over mosaicked 3x3 DSM neighborhood, spacing adjusted for latitude. Road sampling is at segment midpoint.
- distance_to_river_m: UTM distance to OSM river centerline, not current inundation edge.
- nearest_segment_id/graph_node_id: retained graph references. distance_to_road_m/distance_to_graph_node_m are proximity measures; access_verified=false.
- Weather precipitation_mm: preceding hourly interval ending at valid_at, per provider. Null stays missing. available_at is acquisition; original_issued_at/original_available_at unknown. Future forecast event_time uses capture time explicitly, not fabricated model issue time.
- Historical weather: source=replay, original validity/event time, event_name and replayed_at at historical snapshot acquisition. This is a loaded historical snapshot, not a running player. Do not use ERA5 as as-issued 2024 forecasts.
- Both requested point and actual grid point are retained. Shared grid cells are not independent weather stations.
- config/historical_event.json: wave dates and seasonal totals, kept separate from hourly data. No road truth inferred.
- source_manifest.json: URLs, retrieval times, bytes, SHA-256 and licenses; validation.json: checksum/coverage results.


### LightGBM V2 owner contract (2026-10-11)
Input rainfall_1h_mm, rainfall_3h_mm, rainfall_6h_mm, rainfall_24h_mm, rainfall_72h_mm are backward rolling accumulated totals in millimetres sharing one observation time. Not intensities or forecasts. Current GET endpoint accepts only ETA 30/60/120 minutes from prediction decision to arrival; no verified custom POST endpoint yet. Saved weather retrieved 2026-10-10T10:27:51.083909Z; owner gave rainfall completion 2026-10-10T10:00:00Z as an example, not every road's verified timestamp. Retrieval timestamp displayed as owner-supplied, separate from API fetched_at.
probability_unusable is a simulation-trained 0..1 output, displayed times 100 as percent (0.000641 -> 0.0641%). Display bands LOW <.4, MODERATE >=.4 and <.7, HIGH >=.7; absent prediction UNKNOWN. CHECK_REQUIRED means missing/uncertain/distribution-shifted inputs, not a closure. No real-world independent calibration. Owner-reported 2024 simulated validation: ROC-AUC .96308, Brier .07286, recall 87.50%, precision 81.35% at .50; not independently reproduced and not proof of real-road accuracy.
