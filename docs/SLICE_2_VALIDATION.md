# Recovery Slice 2 — settlement warnings and replay

Approved after the user accepted Slice 1. Implemented in the existing workspace; original datasets and geography are retained.

## Delivered behavior

- Live remains the default. Current conditions and the previous 72 hours of model precipitation are acquired together for all 16 settlements. Current 15-minute rain remains separate from complete hourly totals.
- One pure assessment function handles live, historical and synthetic inputs. Rain is mapped by settlement ID/grid and never modified based on elevation. Duplicate intervals do not add rainfall; future event/availability times are excluded.
- Exact backward precipitation totals for 1, 3, 6, 24 and 72 hours ending on the most recent complete UTC hour. Missing hours produce null totals and explicit coverage. Wet duration counts consecutive hourly amounts >=0.1 mm; a missing preceding hour makes it a lower bound.
- Terrain susceptibility uses mapped river proximity and flatness. Surface elevation is displayed as evidence, not silently converted into water depth or an arbitrary rain adjustment.
- Severity, evidence confidence and priority are separate. No weather/history is unknown, not clear. Rain-only settlements appear without being called disasters. The map uses fill for rain and outlines for assessed warning severity.
- Warnings page and map selection read the same snapshot. Every assessment includes amounts, duration, terrain, source/grid, coverage, report evidence, confidence explanation and priority change.
- Synthetic report contributions decay with age; repeated messages from one identified sender do not count as independent corroboration. Recent opposite statuses for the same road/place lower confidence. These are engine inputs from the exercise, not a functioning citizen intake or NLP service.
- Historical replay uses all 16 location series from the unchanged cached ERA5 June 25–July 5, 2024 dataset (three grid cells). ASDMA's verified memorandum provides district flood context, not hourly settlement impacts. Original event times and wall playback times remain labeled.
- Synthetic exercise is separately selected and labeled. Its rain/reports are generated, not historical observations. Generator spatial mapping and arrival-time bucketing are corrected; hidden truth flags are not exposed as report evidence.
- Load, step, play/pause and reset are connected to the backend. Reset creates a new run with no evidence/rank carryover. Live polling is independent of replay. Repeated reads preserve ranking deltas.
- Old unattributed warning overrides return 410. Unverified road warnings return 409. Legacy UI/scorer source remains for reference but is not mounted or called by the operational API. Old exercise URLs now open the live dashboard.

## Rule status and limitations

`config/flood_assessment.json` is **prototype-flood-v1**, an uncalibrated screening profile. Reference rain amounts and severity cutoffs are engineering defaults, not official IMD/ASDMA thresholds. The score and evidence-strength index are not probabilities. The absence of an elevated signal is not an all-clear. Historical original publication availability is unknown: playback releases reanalysis at its validity time explicitly as retrospective exploration, never as a real 2024 decision-time forecast.

The road teammate's exact 1/3/6/24/72-hour input semantics remain unresolved; these warning accumulation windows do not freeze that model contract. No river forecast, hydraulic/inundation model, measured soil saturation, impact lead time, confirmed closure, route, team assignment or resource allocation is fabricated. Closure confirmation/reopening and response coordination remain later slices.

Runs are shared within the local backend process and restart empty. Current weather retains its runtime cache; this is not yet a persistent operational incident ledger. Existing generated training files are preserved and must be regenerated/validated before later model evaluation because the generator was corrected.

## Verification

- 90 Python tests pass. New/regression checks cover exact spatial windows, missing values, interval separation, duration, terrain response, future/delayed evidence exclusion, duplicates, independent/conflicting/stale reports, provenance-invariant scoring, stable GETs, reset, full 72-hour synthetic chronology, historical grid mapping, current-feed outage and retired overrides.
- TypeScript/Vite production build passes.
- Final browser rerun: all eight passed in 23.8 seconds. A mobile provenance-label regression was reproduced and corrected by removing inherited scroll-container overflow from the command surface; the test verifies the label remains in the viewport on both screen sizes.
- Actual live acquisition returned 16 current locations with complete 1/3/6/24/72-hour coverage during verification on October 10, 2026. Snapshot values vary normally; these are model estimates, not stations.
- Eight browser tests pass: live regression/outages, map layers/camps, replay step/play/pause/reset/return-to-live, snapshot-to-warning/map agreement and desktop/mobile layout. Earlier browser pass found a test clicking through an overlapping camp/settlement marker; the regression test now uses the existing settlement layer toggle to select the camp. A sticky NOT LIVE strip keeps original event time visible while scrolling through warnings.
- Legacy tests that expected fake always-present warnings and an off-by-one replay clock were replaced with behavioral correctness checks. Remaining legacy scorer unit tests do not validate the new assessment module; its own tests do.

## Review journey

1. Open http://127.0.0.1:5173 and select a settlement. Inspect its flood assessment and evidence.
2. Open Warnings. Calm live conditions may correctly show no affected settlements.
3. Open Replay & exercises → Load historical weather. Advance or play hourly. All timestamps are from 2024, with a separate playback timestamp.
4. Load synthetic exercise and advance several hours. Open Warnings, inspect evidence and use Show on map.
5. Reset replay, then Return to live. No old reports, historical stepping or synthetic warning state enters Live.

Next slice needs approval: dispatcher/citizen report persistence and teammate NLP API integration. Obtain endpoint, authentication requirements, supported languages and a sample request/response before connecting that model.
