# Lakhimpur Team Android prototype

Native Android WebView wrapper for the existing React Team App. Android 8+ (API 26). No model runs or trains on the phone. The command laptop proxies the model service and joins predictions to road names/IDs.

## Try the built app on a phone

1. Keep the phone, command laptop and model laptop on the same Wi-Fi.
2. Start the model API on the teammate laptop (`10.10.0.169:8002` at this checkpoint).
3. From this workspace, run `powershell -ExecutionPolicy Bypass -File scripts/start-team-mobile.ps1`. This builds the web app and serves on port 8001. Do not start a second copy if that port is already running.
4. Find this laptop's Wi-Fi IPv4 address with `ipconfig`. At the implementation checkpoint it is `10.10.0.170` (may change).
5. On the phone, visit `http://10.10.0.170:8001/team-app.apk`, download and install the debug APK. Android may ask you to allow installation from that browser.
6. Open **Lakhimpur Team**, enter `http://10.10.0.170:8001`, tap **Open**. The app opens `/team-mobile?view=roads`.

Browser fallback: `http://10.10.0.170:8001/team-mobile?view=roads`.

If the page cannot load, check the IP/port and same-Wi-Fi connection first. The model laptop must listen on its LAN address, not just localhost. Router client isolation or a Windows firewall rule can block phone access. No firewall changes are made by the app. The WebView shows a retry message on server failure; model failures show inside the page and remove old estimates.

Use the **command laptop address**, not the model laptop address, in the Android address field. Only the backend uses `ROAD_MODEL_BASE_URL`. Set that environment variable before starting the server if the teammate's IP changes. `.env.example` documents settings; `.env` is not automatically loaded.

## Features and boundaries

- ETA 30/60/120, refresh, road name/ID search, risk-band filter, road details; all 800 study segments are searchable. The first 100 matching rows render at once.
- Model unusability estimates, actual/reference status and input-quality warnings remain separate.
- Weather snapshot retrieval is owner-supplied metadata, not independently verified per-road time. The API fetch time does not imply new weather. Rainfall completion supplied by the owner is explicitly an example.
- Saved-weather, simulation-trained label stays visible. The current API is not driven by exercise steps or current weather.
- No calculated route, GPS, automatic ETA, route-specific road selection, offline inference or automatic dispatch.
- Existing Team App links retain the capability token when navigating between assignments and roads. You can paste a full team link from the same command server into the Android address field. A localhost URL copied from the laptop must be changed to its Wi-Fi address. Tokens are not saved by the native wrapper.
- Exercise state is in memory per backend process. The separate port-8001 demo cannot resume the active port-8000 exercise. To demo assignments and predictions together, create the exercise/teams on one backend process. Historic assignments remain persisted but old process contexts are read-only.
- Debug build permits HTTP for the Wi-Fi demo. Release networking is HTTPS-only. No JavaScript/native bridge, file access, certificate bypass, camera or location permission. Only same-origin WebView navigation is allowed. This is a local prototype, not an authenticated public deployment.

## Rebuild APK

Open this directory in Android Studio, or use PowerShell from the workspace:

```powershell
$env:JAVA_HOME = 'C:/Program Files/Android/Android Studio/jbr'
$env:ANDROID_HOME = "$env:LOCALAPPDATA/Android/Sdk"
./apps/team-android/gradlew.bat -p apps/team-android assembleDebug lintDebug
```

Uses Gradle 9.3.1, AGP 9.1.0, SDK 36/build-tools 36.0.0, Java 17 source compatibility. Wrapper and Gradle files are committed source; machine paths stay in environment/local.properties. Output: `app/build/outputs/apk/debug/app-debug.apk`. It is debug-signed, not a Play Store release.

Implementation references: [Android WebView guide](https://developer.android.com/develop/ui/views/layout/webapps/webview), [AGP compatibility](https://developer.android.com/build/releases/agp-9-1-0-release-notes).
