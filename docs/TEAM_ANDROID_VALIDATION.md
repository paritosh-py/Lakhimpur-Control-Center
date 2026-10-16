# Team Android road-estimates validation — 2026-10-11

Approved scope: user requested model display in the Team App and a simple Android WebView app for a physical phone on the same Wi-Fi. No dashboard model overlay, routing or dynamic inference was authorized in this increment.

## Completed

- Backend proxy validates probabilities, model/mode, ETA, IDs, counts, required fields and display bands; malformed responses return 502 and network failure 503. No stale fallback or operational writes. All local roads remain in the response, with null estimates for missing predictions.
- Team road-estimates screen uses real API data, 30/60/120-minute manual horizons, road search/risk filter, percentage details, input-quality explanation and separate reference/model road statuses. All 800 segments searchable; first 100 matches render. Dedicated source labels separate saved weather from fetch time and exercise time.
- Same-origin FastAPI hosting of built mobile view plus APK download. Thin Android WebView wrapper supports server address, retry, same-origin navigation, native back handling and system/keyboard insets. No native JavaScript bridge. HTTP allowed only in debug manifest.
- Existing assignments/status workflow retained. Secure-random request IDs now work over local HTTP without `crypto.randomUUID`.

## Evidence

| Check | Result |
|---|---|
| Python suite | 118 passed, existing Starlette deprecation warning only |
| New proxy tests | 21 passed, including all supported ETA values, malformed/duplicate/out-of-range/mismatched responses, missing joins and outage |
| Browser suite | All 11 passed in 53.4 seconds, including existing live/replay/map/teams/warnings |
| HTTP request-ID fallback | Team dispatch/status/block/resume/completion test passed with randomUUID explicitly unavailable (28.9 seconds) |
| Web build | TypeScript and Vite production build passed |
| Real model API via new proxy | All ETA values returned snapshot_demo and 800/800 matched roads, zero unmatched predictions |
| Real mobile screen | NT Road osm-1092487157-27-28 displayed 0.0641% for 60 minutes, LOW, unknown statuses, CHECK_REQUIRED |
| Mobile layout | 390px viewport has no horizontal page overflow; real-API mobile and desktop screenshots inspected |
| LAN serving | Laptop's LAN page and APK endpoint return HTTP 200; final rebuilt APK served from same output path |
| Android build | Gradle assembleDebug successful; debug-signed APK produced |
| Android lint | lintDebug successful with 0 errors and 8 warnings: older target/tool versions, React-required JavaScript, backup configuration, unused string resources and two untranslated native messages |
| Physical Android device | Not tested: adb found no connected device; installation/native interaction/phone network reachability require user's phone |

Initial full Python run encountered existing `.pytest_temp` filesystem permissions; rerun with `--basetemp=tmp/pytest-road-app-20261011` passed. Initial browser test needed an explicit risk-filter accessible label; corrected and full suite passed. Offline lint needed dependencies; downloaded from configured official repositories. Back-gesture lint warning on legacy fallback was narrowly suppressed with a code comment because API 33+ already registers the native OnBackInvokedCallback; no global lint suppression or baseline was added.

Screenshots: `docs/screenshots/road-estimates-real-mobile.png`, `road-estimates-real-desktop.png`. The earlier `road-estimates-mobile.png` is from explicitly named test fixtures, not the real model.

## Run and remaining scope

Phone server at checkpoint: PID 7076, port 8001, Wi-Fi 10.10.0.170. Verify before reuse. Original 8000/5173 servers were preserved; original backend needs restart to load new API code. Different server processes do not share in-memory exercises. Use one process for a combined exercise/teams demo. Raw data, ledger and archived exercise records preserved.

Phone instructions and build commands: `apps/team-android/README.md`. Download `http://10.10.0.170:8001/team-app.apk`, install, enter `http://10.10.0.170:8001`, tap Open. IP may change. No firewall changes made.

Not implemented: verified custom POST inputs, live/exercise-dependent predictions, route calculation, per-segment arrival estimates, confirmed-closure evidence workflow, calibrated real-world probabilities, automatic dispatch/replanning or offline inference. Displaying these estimates does not complete original requirements A2.1–A2.3.
