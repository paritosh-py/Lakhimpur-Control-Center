# Clarified product and recovery proposal

2026-10-11 priority change: user explicitly authorized manual team assignment and Team App status updates in exercises before citizen/NLP integration. That bounded increment is tracked in TEAM_WORKFLOW_VALIDATION.md. This does not mark all of Slice 4 complete: routes, road model, shelter/resource allocation and automatic replanning remain dependencies, and no fake route recommendations are used.

Latest delivery status: Slice 1 accepted by user; Slice 2 explicitly approved and implemented. See SLICE_2_VALIDATION.md and HANDOFF.md. Slices 3–5 remain gated by separate approvals. Earlier proposal/pending-approval wording below is historical context.

2026-10-10. Proposal only; application changes await approval. Latest user requirements override conflicting older implementation/completion notes. Keep NewContext.md unchanged as the original specification. Detailed defects: COMMAND_DASHBOARD_AUDIT.md.

## Workspace decision

Improve this workspace incrementally. Retain acquired raw data/provenance, district configuration, 800-road graph, 16 settlements, seven reference camps, map layers, shared clocks, strict schema foundations and package setup. Repair source adapters, generator chronology and warning state; replace incorrect aggregation/evidence logic. Split the monolithic React component by actual workflows. No new framework, microservice architecture or parallel replacement project is needed. Use one FastAPI application, one React application with admin/team/citizen routes, and a local SQLite store for operational state. SQLite is a proposal consistent with the earlier stack decision, not an existing implementation.

## Intended flow

Live weather or explicitly selected replay/exercise + incoming reports -> validated, timestamped stored inputs -> per-settlement assessment -> severity/confidence and priorities -> road model + routes -> suitable team/shelter plan -> dispatcher approval/assignment -> team updates -> reassessment/replanning. Every view reads the same versioned backend state.

Live monitoring is the startup view. It refreshes current information automatically, has no playback controls, and shows unavailable/stale data honestly. It must not require reports to assess weather/terrain, invent incidents, or interpret missing rain as zero. Six wet settlements means six independently marked settlements, subject to real provider grid resolution; shared grid cells must not be presented as independent station readings. Rainfall status is distinct from a disaster warning.

Assess severity from each settlement's rainfall amounts, duration, terrain susceptibility and available reports. Susceptibility changes response to rainfall; it does not justify fabricating different rainfall values. Confidence separately reflects freshness, coverage, source quality and agreement. Two demonstrably independent corroborating reporters may increase confidence; repeated messages from one sender do not. No reports means "No ground reports received", not zero risk or automatic distrust. Conflicts and stale reports remain visible. Initial unvalidated hazard rules must be labeled heuristic, not calibrated probabilities.

## Historical scenarios

Real historical weather replay remains separate from the synthetic response exercise, as approved by the user. Preserve source files and original values. Any adjusted rain, generated report, closure or resource event is individually simulated with parent source and transformation recorded. An exercise based on real weather is a mixed-evidence synthetic exercise, not a verified reconstruction. Original time and replay time remain visible. ERA5 reanalysis cannot be represented as a forecast issued at the historical decision time.

Candidate event: Assam/Lakhimpur 2024 monsoon flooding, compatible with cached June 25–July 5 weather. ASDMA's 2024 memorandum documents flood impacts; its seasonal district totals cannot identify hourly conditions in the 16 selected settlements. July 1 daily report is indexed with Lakhimpur/Kadam impacts but its direct download failed during research; obtain and verify the document before importing its details. ASDMA also lists a North Lakhimpur/Ranganadi flood study and flood hazard atlas, useful for susceptibility context. Do not infer a landslide occurred in a selected settlement from statewide reports.

Sources inspected:
- https://asdma.assam.gov.in/sites/default/files/swf_utility_folder/departments/asdma_revenue_uneecopscloud_com_oid_70/menu/document/assam_flood_memorandum_2024_.pdf
- https://asdma.assam.gov.in/portlet-innerpage/studies-projects
- https://www.asdma.gov.in/pdf/flood_report/2024/Daily_Flood_Report_01.07.2024.pdf (indexed contents available; direct fetch failed)
- https://open-meteo.com/en/docs (current model weather; not verified ground observations)

## Model integration owned by teammates

Report extraction interface: REPORT_CONTRACT_PROPOSAL.md. Do not independently retrain/replace the teammate's parser.

Road feature windows are exactly 1, 3, 6, 24 and 72 hours. Proposed names rain_1h_mm, rain_3h_mm, rain_6h_mm, rain_24h_mm, rain_72h_mm; backward accumulation versus forward forecasts must be agreed with teammate before freezing the contract. Use the same units, temporal alignment, rainfall grid mapping, missing-data policy and feature preprocessing as training. Provide decision_time and arrival_time/lead_minutes; if the model only predicts current accessibility, it cannot silently be treated as an arrival-time predictor. Specify accessible/unusable positive class, probability calibration and uncertainty semantics.

Static features: segment_id, length_m, elevation_mid_m, elevation_min_m, elevation_max_m, road_type. Existing data has length, road_type and midpoint elevation only. Sample terrain along the full road geometry to derive min/max, recording DEM resolution, vertical datum, coverage and sampling method. These are sampled terrain estimates, not surveyed road-deck extrema. Agree whether length means full segment or distance traveled on a partial segment. Government road categories require an explicit mapping to the model's vocabulary.

Government candidates: NRIDA/PMGSY GeoSadak rural road open data, and NRSC/Bhuvan CartoDEM. Portal coverage/access and exact Lakhimpur fields need verification; do not claim every required model feature is supplied ready-made or that rural-road data covers all highways. Preserve OSM segment IDs and connectivity until a verified crosswalk exists.
- https://pmgsy.nic.in/list-nrida-most-often-used-services
- https://www.pmgsy.nic.in/sites/default/files/Press_Releases/PIB1800373_2.pdf (search-indexed official release identifies OpenData; direct fetch failed)
- https://bhuvan.nrsc.gov.in/wiki/index.php/Frequently_Asked_Questions (indexed CartoDEM description; direct fetch failed)

Routes must honor directionality and confirmed closures, estimate arrival progressively along the route, and query accessibility at each segment's expected arrival. Unknown model output is not safe access. Nearest suitable shelter means reachable via a feasible route with capacity and relevant facilities, not merely shortest straight-line distance. Initial assignments should be recommendations with explicit admin dispatch; scope of later automatic reassignment needs agreement. Preserve completed/committed work and log changes.

## UI structure

Simple professional operations layout with readable type, restrained color and real navigation. Avoid decorative telemetry, official affiliation claims and permanent online indicators. Map is central on overview; detailed diagnostics appear on selection or dedicated pages. Status must use text/icons as well as color.

| Page | Purpose |
|---|---|
| Overview (default Live) | 16-settlement map, current conditions/freshness, prominent named warnings, selected settlement details |
| Warnings | Separate settlement cards/list with rainfall amount/duration, susceptibility, severity, confidence, reports and changes; rain-only observations distinguished from hazard alerts |
| Teams & Assignments | Add/manage teams, location/capabilities/status, recommended and dispatched tasks, route/ETA and updates |
| Dispatcher | Citizen/SOS and team message inbox, raw/extracted text, channel, arrival time, map match, verification/conflict controls |
| Shelters & Resources | Camp map, verified available capacity, vehicles/boats, reservations and unmet needs |
| Replay & Exercises | Verified dataset selection versus synthetic overlay, chronological controls and persistent provenance banner |
| Plans & History | What changed, assignment/replanning decisions, evidence and outcomes |

Citizen app: minimal report/SOS form, location, delivery acknowledgement. Team app: assigned task, route/evidence, accept/en route/arrived/completed/blocked and messages. Same backend and report contract. SMS requires a real provider or modem; ESP-NOW requires working firmware/serial bridge. Simulated transport must be labeled; rich JSON is assembled at the gateway, not transmitted as a large radio packet.

## Delivery slices and visible acceptance

Each slice needs approval before implementation; no broad approval is inferred from this proposal. Repair code and tests within each slice and preserve working geography/data.

| Slice | Main files/areas | Done when |
|---|---|---|
| 1 Live foundation and overview | ingest, storage, weather API, React overview/navigation, source status | Opens live automatically; all 16 show actual current timestamped conditions or explicit unknown; no live stepping; outage/reload tested; no fabricated warning/incident |
| 2 Settlement warnings and replay | feature windows, warning/evidence/ranking, replay adapter, warning page | Spatially and temporally correct rain/duration/terrain assessments; independent severity/confidence; chronological replay; no future availability leakage; map/card/list agree |
| 3 Dispatcher and citizen reporting | report adapter/schema, persistence, trust, citizen view, SMS/bridge interfaces | Raw report reaches inbox, teammate model structures it, uncertain location reviewed, dedup/conflict/staleness work, assessment updates without inventing values |
| 4 Teams, shelters, road model and dispatch | terrain enrichment, model adapter, directed routing, inventory, reservations, team view | Team added; feasible route/arrival prediction and suitable camp selected; dispatch delivered; status returns; no closure crossing/double booking/overflow |
| 5 Replanning, offline link and evaluation | planner, ledger, bridge/firmware, replay/evaluation exports | Changed closure/resource condition updates only feasible uncommitted actions, records unmet needs/reasons, offline report arrives; matched baseline and model validation completed |

No ML-backed route feature is marked complete before the teammate artifact and preprocessing are integrated. No UI button is called functional before its persistent backend transition is tested. Use regression tests around demonstrated defects, not just nonempty responses. Show a short working user journey after every slice.

## Open decisions

User clarification after this proposal: first version remains flood-focused while capturing other incident reports. Teammate report model will be served through a Python/FastAPI HTTP API; endpoint, example request/response, authentication and supported languages remain pending. Road model uses time points 1/3/6/24/72 hours through 72 hours; the answer does not yet establish whether these represent lagged samples, accumulated rainfall or forecast horizons. Preserve these exact points and request a sample model input/output before integration. Correction Slice 1 approval has not yet been granted by these clarification answers.

- Road model: exact window meaning, feature schema, preprocessing, rainfall spatial mapping, model format/API, arrival horizon, output class/probability/uncertainty.
- Report model: example input/output, supported languages and delivery method.
- Hazard scope: original project is flood-only; latest examples mention landslides. Capture other reports, but independent landslide risk needs explicit scope confirmation and suitable evidence.
- Before dependent slices: SMS provider/modem, operational inventories versus explicitly simulated exercise inventory, trust/reopen thresholds, hardware ports and automatic dispatch authority. Remaining time remains deferred by user.
