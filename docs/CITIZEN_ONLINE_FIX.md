# Citizen internet-delivery screen fix - 2026-10-11

## User-reported problem

The installed Citizen App still showed the old AeroLink/node transmission steps while connected to the internet. The user clarified this was the visible workflow problem, not a confirmed server error.

## Root cause and correction

`SOSTransmissionStageCard` previously chose the internet view only when `isDeliveredOnline` became true after receiving the HTTP response. Until then it defaulted to the offline mesh timeline. The transport could already be using HTTP while the screen incorrectly described a node transmission.

The SOS service now tracks connection selection separately from delivery confirmation:

1. **Checking connection** while connectivity is being determined.
2. **Sending directly to the dashboard** when using the online path.
3. **Delivered via internet** only after a response includes the server report ID, or an explicit failure/retry screen.
4. The old mesh timeline is selected only for the offline transport.

Online failure does not send BLE packets. Stray mesh acknowledgements cannot mark an online report delivered. Online reports do not enable the offline chat channel. Closing requires the actual server report ID and confirmation; an unsuccessful close leaves the report open with an error message.

Other small corrections: send timeout raised from 8 to 25 seconds to allow the existing server triage wait; HTTP failure status retained in the connection error; debug Android manifest allows HTTP for the LAN demo; active report says Received rather than Dispatched; missing triage score no longer defaults to fabricated 75; Gemini label follows `triage_source=gemini_ai`; reference/triage/offline labels wrap at phone widths. An existing test exposed the non-forced reset guard no longer protecting active requests; restored that guard.

## Files

Under `apps/citizen_flutter/AeroLink-main/apps/mobile`:

- `lib/services/sos_service.dart`: delivery-path state, transport test injection, receipt/closure handling.
- `lib/services/lakhimpur_service.dart`: send timeout and error reporting.
- `lib/screens/sos/widgets/sos_transmission_stage_card.dart`: online progress, truthful labels, wrapping.
- `android/app/src/debug/AndroidManifest.xml`: local HTTP in debug builds only, following the [Flutter network-policy guidance](https://docs.flutter.dev/release/breaking-changes/network-policy-ios-android).
- `pubspec.yaml`: version **1.0.1+2**.
- `test/sos_online_test.dart`: new online service/widget tests.
- Existing `sos_service_test.dart` and `widget_test.dart`: explicitly select offline connectivity when testing mesh behavior.

## Validation

- All **16 Flutter tests passed**, including online checking/sending/delivery/close, zero BLE packets while online, failures/retry, missing server ID, connectivity-check failure, and existing offline acknowledgement/chat/closure flows.
- Online widget tested at 390px, offline widget at 360px; layout exceptions fixed.
- `dart analyze lib/ test/`: **No issues found**.
- Final source-label adjustment: all 3 online tests passed again.
- APK builds as **1.0.1 (build 2)**. Final build/download verification is recorded at the end of this document.
- Read-only checks from laptop: health on 8000/8001 and LAN 10.10.0.170:8001 returned 200; current 8001 API advertises report submission and status endpoints.
- No backend code changed, no test reports sent to the live database, no user reports closed, and no running backend/exercise was reset. Prior Python/browser test counts were not rerun or claimed as fresh validation.

## Next action and limitations

Install the new **Citizen** APK over the old installed version (not the Team APK): `http://10.10.0.170:8001/citizen-app.apk?v=2`. Keep phone and laptop on the same Wi-Fi; configure the Citizen App server as `http://10.10.0.170:8001` if needed. Send a report and confirm the new direct-dashboard progress, receipt, dashboard listing and closure. The phone's installed app does not update when local source files change.

Physical-phone behavior and offline radio delivery are not verified by these tests. Transport tests use injected HTTP/BLE responses. Same-Wi-Fi connectivity is needed for this local server; a cellular internet connection alone cannot reach its private LAN IP. Automatic post retries across hosts and full server-side idempotency remain a separate reliability concern; this UI fix does not claim to solve every delivery failure. New development phases remain subject to the recorded approval workflow.


Final APK: 181527039 bytes; SHA256 1dbb63456965e8f70a20ada95a0700afc7c2e1de1b881df507844f2222a20797. Final debug build successful; LAN APK download returned a valid ZIP/APK range response. Version verified by aapt2 as 1.0.1, versionCode 2. Physical-phone acceptance pending.
