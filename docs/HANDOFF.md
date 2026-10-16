# Current handoff

Updated 2026-10-16, Asia/Kolkata. Read CURRENT_STATE.md and PROGRESS.md with this file. Archived handoffs are history, not current instructions.

## Authorization and exact next action
User approved publishing the project to their GitHub account as **Lakhimpur Control Center - Public**, with teammate credits **Paritosh and Atulya**. Target: paritosh-py/Lakhimpur-Control-Center. Preparing initial commit/publication; do not claim push completed until remote verification. No new functional phase approved.

Previous increment: Citizen settlement parity fix is built as **1.0.2+3**, including direct-online UI correction. Physical-phone acceptance remains pending. Next functional verification is installing this APK, checking the 16 settlements, sending a report, checking dashboard receipt, and closing from phone/dashboard. Do not silently launch another functional phase.

Citizen APK: apps/citizen_flutter/AeroLink-main/apps/mobile/build/app/outputs/flutter-apk/app-debug.apk. Download endpoint /citizen-app.apk?v=3. Last known LAN origin http://10.10.0.170:8001 (verify IP/server). Team APK at /team-app.apk is different.

## Continuity rules
1. Read AGENTS.md and NewContext.md fully, then this file, CURRENT_STATE.md and PROGRESS.md.
2. Inspect relevant source before editing. Requirements describe intent; source shows implementation; tests prove only their tested scope.
3. Latest user instructions override old plans. Preserve newer routing, reports, Team and Flutter work even where incomplete.
4. Preserve untracked files, raw data, runtime SQLite/cache and active processes. No reset/clean/rewrite.
5. Update current sections in place. Archive superseded facts instead of stacking contradictory next steps.

## Latest completed increment and verification
- Changed presentation only: apps/web/src/command/live.css, new light-theme.css, presentation styles in LiveOverview.tsx, ReportsPage.tsx and Assessments.tsx. No backend/model/database/mobile-app code changed.
- npm.cmd run build passed (TypeScript and production Vite bundle). Existing live-overview Playwright regression passed:1test,7.8seconds. No full backend/browser suite rerun for palette work.
- Inspected desktop1440 and mobile390 layouts, Overview/Teams/Reports and navigation; no page overflow in measured Overview/Reports. Core text/semantic palette contrast ratios4.97?14.41:1; this is not a comprehensive accessibility audit.
- Screenshots under docs/screenshots/light-*.png. Existing live regression also refreshed slice1-live screenshot filenames; those image files now show the new palette, not the historical dark theme.
- Context reconciliation completed: CURRENT_STATE, HANDOFF, PROGRESS, OPEN_QUESTIONS, documentation index and AGENTS updated; supporting docs carry current-state pointers. Superseded full handoffs preserved in history.
- Exact next action: user refreshes dashboard and reviews appearance; pending Citizen1.0.2+3 physical acceptance remains. No new functional phase approved.

## Critical facts
- District is Lakhimpur, Assam. Live is default; historical ERA5 and synthetic exercise stay separate.
- Road model uses saved weather and simulated training labels, ETA30/60/120. It does not respond to live/exercise rainfall.
- Citizen reports persist and receive Gemini/rule triage, but are NOT connected to live settlement assessments.
- Route prototype exists. Missing predictions default to LOW/zero probability and can imply 100% reliability; closure registry is not connected. Do not call it operationally safe or complete.
- Citizen selected settlement ID is now submitted; canonical 16 names match. Build success does not prove latest APK installed on phone.
- GitHub publication is the active task. Check Git history/remote to establish the current commit/push state; earlier untracked-state notes are historical.

Historical conflicting files preserved under history/context-reconciliation-2026-10-11/. Older HANDOFF_HISTORY_2026-10-11.md also remains historical. See CURRENT_STATE.md for detailed architecture, limits and resume information.

## Tooltip contrast correction — 2026-10-11
User reported dark settlement hover background. Fixed Admin-scoped light-theme.css to override legacy style.css Leaflet !important declarations: white background, dark text,14px font, light border/directional arrows. Production build passed; actual browser hover computed white rgb(255,255,255), dark rgb(37,43,42),14px. Screenshot light-tooltip-fix.png. No behavior or data changed. Next: refresh dashboard; prior physical Citizen acceptance remains pending.

## Header simplification — 2026-10-11
User requested removing Pages/side panel and enlarging the heading. Removed drawer, backdrop, Pages trigger and associated state/Escape handler from LiveOverview.tsx. Main navigation tabs remain. Heading now full “Lakhimpur Control Center”, bold responsive26–36px via light-theme.css. Build passed; browser confirmed no sidebar/trigger,36px desktop heading and no390px viewport overflow. Screenshots light-heading-desktop/mobile.png. No backend/data changes; this supersedes earlier notes retaining the drawer.

## GitHub publication preparation - 2026-10-16
README now describes current features/limits and credits Paritosh and Atulya (only Paritosh GitHub username verified). Account paritosh-py verified using existing sign-in. Public repository name approved by user. Ignore rules exclude local agent tools, credentials, runtime databases, APK/build artifacts, logs/signing material and screenshots containing possible report details. Files remain locally. Candidate source scan found no recognized secret patterns or matches to local configured secrets; this is a bounded scan, not a comprehensive security audit. No application code changed or application tests rerun for publication.
