# Recovery Slice 1 — live monitoring

Completed 2026-10-10 after explicit user approval. Scope: reliable live weather overview for the 16 existing settlements. This does not mark the audited warning engine, historical simulation or operational workflows complete.

## Delivered

- Root URL opens Live Overview automatically and independently of existing scenario runs.
- GET /api/live/conditions fetches current Open-Meteo Best Match model conditions for all 16 settlement coordinates. Original cached historical/forecast files are never substituted for current data.
- Map, settlement table and selected-place details use the same snapshot. Temperature, rain/showers, weather code, clouds, humidity, wind and daylight come from provider fields. Clear nighttime weather is not labeled sunny; precipitation uses its actual interval (currently 15 minutes), not mm/hour.
- Page checks every minute; serialized upstream fetch at most every ten minutes; failure retry after one minute. Missing values remain unknown. Failed refresh or readings older than one hour are stale. These are engineering freshness settings, not hazard thresholds.
- Last successful snapshot persists in ignored data/runtime/live_weather.json, separate from acquired originals. Validation checks coverage/order, units, values, UTC and validity time; a new download cannot freshen old observations.
- No Step/Reset or fabricated warning/incident in Live view. Starting live through scenario API returns 409; stepping/resetting a legacy live adapter also returns 409.
- Old exercise UI remains at /?view=exercise, explicitly labeled under repair. Its Live button links back to Overview. Known warning defects remain recorded in COMMAND_DASHBOARD_AUDIT.md.
- Source coverage page and camp details disclose modeled weather, grid sharing and unknown operational availability.

## Verification

- 86 Python tests passed, including seven new cases covering settlement mapping, six wet locations, missing/nighttime values, cache/backoff/restart, outage without cache, invalid responses, stale timestamps and live/scenario isolation.
- 8 Chrome browser tests passed: four new Live tests and four retained legacy UI checks. Exact six-marker rainfall rendering, map/list selection, no playback/warning API calls from Live, reload, desktop/mobile and errors verified. Legacy UI checks passing do not resolve legacy warning defects.
- TypeScript and Vite production build passed.
- Actual provider call on October 10 returned 16 current locations, 10 model grid cells and zero rainy locations in that sampled interval. These are timestamped model readings, not permanent claims or ground observations.
- Screenshots: docs/screenshots/slice1-live-desktop.png and slice1-live-mobile.png. Inspected desktop/mobile; fixed marker opacity/layering. No page-wide mobile overflow.
- One upstream Starlette TestClient deprecation warning. Existing Windows pytest temp directory may be locked; validated with a new --basetemp=tmp/slice1-tests-final and -p no:cacheprovider, without deleting protected folders.

## Files and operation

New service: backend/app/services/live_weather.py; router: backend/app/api/live.py; UI: apps/web/src/command/LiveOverview.tsx and live.css. Registered in existing app; playback guarded in scenario.py; tests/unit/test_live_weather.py and apps/web/tests/live.spec.ts added. Legacy browser tests now target exercise URL. HTTPX moved to runtime dependencies and uv.lock updated offline.

Run API and Vite using README.md. Backend needs outbound HTTPS access, with TLS verification enabled. No weather API key used. Check for updates asks the service for current state without bypassing upstream throttling. Automatic refresh occurs while the page polls; there is no claim of an unattended background acquisition daemon.

Provider docs: https://open-meteo.com/en/docs . No IMD/CWC gauge or official disaster status claimed. Original dataset caches are preserved.

Next: approval for Slice 2, covering correct rainfall windows/duration, susceptibility/severity/confidence and chronological replay. Reports, dispatch, model-based routing, ledger, hardware and replanning remain later slices.
