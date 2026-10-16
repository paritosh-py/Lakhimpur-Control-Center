# Aerolink Basecamp Codebase Context Map

> Implementation audit: 2026-09-05. This document describes the code currently in the repository. Source code takes precedence over the README and UI labels.

## Project Summary

Aerolink Basecamp is a Next.js 16 App Router dashboard for receiving emergency signals, using Gemini 2.5 Flash to reconstruct and triage them, storing incident records in local JSON files, and sending dispatcher messages back through a hardware bridge.

The implemented transport is **Bluetooth LE from Android to the Victim ESP32, Wi-Fi UDP between the ESP32 nodes, and USB serial from the Base Station ESP32 to Node.js**. There is no LoRa, SX1278, or mesh-relay implementation. The main application is a local-file-backed prototype rather than a multi-user production service.

## Runtime Architecture

```mermaid
graph TD
    App[Android application] -->|BLE write| Field[Victim ESP32]
    Field -->|Wi-Fi UDP 4330| Base[Base Station ESP32 access point]
    Base -->|USB serial 115200| Bridge[scripts/bridge.js]
    Bridge -->|POST /api/data| Ingest[/api/data]
    Ingest -->|encrypt pending ticket| Tickets[src/data/tickets.json]
    Ingest -->|write NEW_SIGNAL notification| Buffer[src/data/external.json]
    Buffer -->|poll every 1.5s| Dashboard[Authenticated AdminDashboard]
    Dashboard -->|open via PATCH /api/reconstruct| Process[/api/reconstruct]
    Process -->|fetch Gemini 2.5 Flash| AI[Google Generative Language API]
    Process -->|save active analyzed ticket| Tickets
    Dashboard -->|POST /api/prioritize| Triage[/api/prioritize]
    Triage -->|fetch Gemini| AI
    Dashboard -->|PATCH /api/reconstruct| Tickets
    Bridge -->|GET /api/reconstruct with x-bridge-auth| Tickets
    Bridge -->|serial [ticket-id] note| Base
    Base -.->|UDP 4331 broadcast; current victim does not listen| Field
```

### Main signal lifecycle

1. `scripts/bridge.js` frames complete compact or pretty-printed emergency JSON objects from fragmented serial output printed by the base ESP32.
2. It validates and posts the full structured report, a readable incident summary, a stable ticket ID, and coordinate-based `manualLocation` to `/api/data`.
3. `/api/data` immediately creates an encrypted `pending` ticket and writes a `NEW_SIGNAL` notification to `external.json`.
4. The dashboard displays the notification and polls the persisted Dispatcher Intake.
5. Opening a request calls `/api/reconstruct` with the `open` action, changes it to `active`, and runs the existing Gemini reconstruction once.
6. Closing a request changes it to `resolved`; Overview statistics and map pins update from that persisted state.
7. `bridge.js` polls all tickets, detects previously unseen note timestamps, and writes `[ticket-id] note` to the Base Station ESP32. The Base Station broadcasts it on UDP `4331`; the current Victim firmware does not receive that port.

## Repository Inventory

### Root and configuration

- [package.json](package.json): package name `disasted`, scripts `dev`, `build`, `start`, and `lint`; Next.js `16.2.4`, React `19.2.4`, TypeScript, Tailwind 4/PostCSS, Lucide, Framer Motion, Pigeon Maps, Leaflet/React Leaflet, Recharts, SerialPort, and Gemini SDK dependencies.
- [package-lock.json](package-lock.json): npm lockfile.
- [tsconfig.json](tsconfig.json): strict TypeScript, bundler module resolution, JSX transform, `@/*` mapped to `src/*`, no emit.
- [next.config.ts](next.config.ts): disables Next dev indicators.
- [eslint.config.mjs](eslint.config.mjs): Next core-web-vitals and TypeScript ESLint configuration with generated directories ignored.
- [postcss.config.mjs](postcss.config.mjs): Tailwind 4 PostCSS plugin.
- [.env.example](.env.example): server-side `GEMINI_API_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` examples. It does not document `ENCRYPTION_KEY`.
- [.gitignore](.gitignore): ignores dependencies, Next output, environment files except `.env.example`, local JSON databases, scratch tools, and generated TypeScript files.
- [README.md](README.md): setup and product overview; it still describes LoRa/SX1278 even though the firmware is Wi-Fi UDP.
- [AGENTS.md](AGENTS.md): requires reading the installed Next.js 16 documentation before changing Next.js code.
- [codebase_context_map.md](codebase_context_map.md): this implementation-backed map.

### Hardware and bridge tools

- [hardware/victim_node/victim_node.ino](hardware/victim_node/victim_node.ino): exact demonstration Victim ESP32 firmware. It exposes the Android-facing BLE service, joins `CodeRed_SOS_Network` as a Wi-Fi station, and forwards the BLE payload unchanged to `192.168.4.1:4330`.
- [hardware/transceiver/transceiver.ino](hardware/transceiver/transceiver.ino): exact demonstration Base Station ESP32 firmware. It creates the open `CodeRed_SOS_Network` access point, receives UDP on `4330`, prints packets at serial `115200`, reads newline-delimited serial replies, and broadcasts them to `192.168.4.255:4331`.
- [scripts/bridge.js](scripts/bridge.js): primary duplex serial bridge. Default port `COM13`, baud `115200`, API root `http://127.0.0.1:3000/api`, uplink deduplication window 10 seconds, downlink polling every 2 seconds. Reads `ADMIN_PASSWORD` from `.env.local` for the bridge auth header.
- [scripts/bridge-protocol.js](scripts/bridge-protocol.js): validates the Android emergency JSON contract, buffers fragmented serial lines, derives stable ticket IDs, and maps reports into dashboard payloads. Its Node tests are in `bridge-protocol.test.js`.
- [scripts/wifi_bridge.js](scripts/wifi_bridge.js): alternate TCP bridge on `0.0.0.0:5555`. Parses both parenthesized and ticket-prefixed formats, posts to `/api/data`, and writes newer notes back to the connected TCP client. Its downlink request omits bridge authentication.
- [scratch/wifi_to_serial.js](scratch/wifi_to_serial.js): ignored test utility that pipes TCP port `5555` directly to hardcoded `COM4` at `115200`; it does not use the API.

### Application routes and server actions

- [src/app/layout.tsx](src/app/layout.tsx): root layout; loads Google Inter and JetBrains Mono fonts, global CSS, metadata title `Disast-ED | Rescue Recon Dashboard`.
- [src/app/page.tsx](src/app/page.tsx): protects `/` with `checkAuth()` and renders `AdminDashboard`.
- [src/app/login/page.tsx](src/app/login/page.tsx): redirects authenticated users and renders `LoginForm`.
- [src/app/monitor/page.tsx](src/app/monitor/page.tsx): public polling monitor for the external signal buffer; polls every second and keeps a ten-entry local log.
- [src/app/victim/page.tsx](src/app/victim/page.tsx): public field-node view. Polls the global external buffer, reads ticket IDs from `localStorage.myDistressTickets`, and displays incident history, marker state, decoded messages, and admin notes.
- [src/app/actions/auth.ts](src/app/actions/auth.ts): server actions for credential comparison, HTTP-only `admin_session` cookie creation, and logout.
- [src/app/api/data/route.ts](src/app/api/data/route.ts): unauthenticated single-signal buffer API.
- [src/app/api/reconstruct/route.ts](src/app/api/reconstruct/route.ts): authenticated manual creation, lazy AI processing when a request is opened, ticket reads, and dispatcher updates, with an unauthenticated `ids` query path.
- [src/app/api/prioritize/route.ts](src/app/api/prioritize/route.ts): analyzes unprocessed unresolved tickets, then applies the existing Gemini triage ranking.
- [src/app/api/intelligence/route.ts](src/app/api/intelligence/route.ts): authenticated analysis-only Gemini endpoint; does not create a ticket.

### Components

- [src/components/AdminDashboard.tsx](src/components/AdminDashboard.tsx): authenticated shell, sidebar tab state, geolocation, ticket polling every 4 seconds, informational signal notifications, search, local logs, and modals.
- [src/components/AdminSidebar.tsx](src/components/AdminSidebar.tsx): Overview, Dispatcher, Intelligence navigation and logout.
- [src/components/StatsDashboard.tsx](src/components/StatsDashboard.tsx): counts unopened pending, opened active, and closed resolved tickets.
- [src/components/RequestsPage.tsx](src/components/RequestsPage.tsx): dispatcher intake, in-place AI prioritization, open-triggered AI processing, ticket detail, map, notes, marker updates, closure, and resolved archive.
- [src/components/IntelligenceModule.tsx](src/components/IntelligenceModule.tsx): analysis-only decoder with sample inputs and local intelligence feed.
- [src/components/EmergencyReportDetails.tsx](src/components/EmergencyReportDetails.tsx): shared structured report display for pending signals, the public monitor, and approved dispatcher tickets.
- [src/components/SituationalMap.tsx](src/components/SituationalMap.tsx): Pigeon Maps map, base geolocation, coordinate parsing, Haversine distance, victim overlays, panning, zoom, and fullscreen.
- [src/components/LoginForm.tsx](src/components/LoginForm.tsx): client credential form using the login server action and Framer Motion transitions.
- [src/components/DisasterHeatMap.tsx](src/components/DisasterHeatMap.tsx): unused Leaflet demo with hardcoded Delhi incident circles.

### Data and assets

- [src/lib/ticket-status.ts](src/lib/ticket-status.ts): shared pending/active/resolved lifecycle and legacy-status compatibility helpers.
- [src/lib/ticket-analysis.ts](src/lib/ticket-analysis.ts): deduplicates in-flight Gemini analysis, persists analysis state, and activates opened requests.
- [src/data/external.json](src/data/external.json): ignored runtime buffer; current shape is `{ message, state, timestamp }`, normally `READY`/`IDLE`.
- [src/data/tickets.json](src/data/tickets.json): ignored encrypted local ticket database. It contains historical local records and is not a checked-in data contract.
- [src/app/globals.css](src/app/globals.css): Tailwind import, light canvas palette, semantic colors, layout/card/button/input classes, sidebar sizing, and scrollbars.
- [public/logo.png](public/logo.png): present but not referenced by the application.
- [src/app/favicon.ico](src/app/favicon.ico): favicon asset.

Generated or local-only items include `.next/`, `node_modules/`, `next-env.d.ts`, `.env.local` when present, and the ignored JSON/scratch files.

## Data Contracts

### Runtime ticket

Defined in `src/lib/db.ts`:

```typescript
interface Ticket {
  id: string;
  original: string;
  reconstructed: string;
  urgency: number;
  category: string;
  location: { lat: number; lng: number };
  manualLocation?: string;
  victimName?: string;
  timestamp: string;
  status: string;
  markerColor: "green" | "yellow" | "red" | "none";
  adminNotes: {
    text: string;
    timestamp: string;
    sender: "admin" | "system";
  }[];
  source?: string;
  report?: EmergencyReport;
  analysisStatus?: "pending" | "processing" | "complete" | "failed";
}
```

New requests use `pending` when unopened, `active` when opened and unresolved, and `resolved` when closed. Shared status helpers treat legacy `received` records as active and legacy `completed` records as resolved. `analysisStatus` records `pending`, `processing`, `complete`, or `failed` so completed Gemini analysis is not repeated.

### Emergency report and external buffer

`src/lib/emergency-report.ts` validates `{ type, timestamp, latitude, longitude, peopleAffected, conditions, additionalDetails }`. `/api/data` accepts that exact object directly or as `report` in a bridge payload. Structured reports are encrypted with the automatically created ticket. Numeric coordinates populate both `location` and comma-separated `manualLocation`; the map reads structured report coordinates first. Legacy message payloads remain supported.

### Gemini reconstruction result

`src/lib/intelligence.ts` calls the REST Generative Language API model `gemini-2.5-flash` and requests JSON with:

```json
{ "reconstructed": "...", "urgency": 1, "category": "..." }
```

The helper skips Gemini thought parts, parses direct JSON or the first JSON object found in text, and throws on missing credentials, API errors, empty output, or invalid JSON.

The reconstruction prompt includes victim name and reported location. The prioritization prompt classifies Fire/Drowning/Trauma as Tier 1 and Food/Water/Shelter as Tier 2, asks Gemini for `sortedIds` and `rationale`, then appends any omitted active tickets after the AI-ranked results.

## API Behavior

### `/api/data`

- `GET`: returns the contents of `external.json`; no authentication.
- `POST`: validates the message/report, suppresses a repeated stable ID or matching recent message, creates an encrypted pending ticket immediately, and writes one `NEW_SIGNAL` notification record; no authentication.
- `PATCH`: acknowledges the current notification and writes `SCANNING...`/`IDLE`; it retains a newer notification if the supplied ticket ID is stale; no authentication.
- Uses an in-process mutex, but synchronous file writes are not atomic across processes.

### `/api/reconstruct`

- `POST`: authenticated; accepts `text`, optional `location`, and optional `source`, invokes Gemini, and appends an active manual ticket.
- `GET`: full list and single-ticket reads require auth. Supplying `ids=a,b` bypasses the auth check and returns decrypted matching tickets.
- `PATCH`: authenticated; `action: "open"` marks an unresolved ticket active and performs pending AI analysis. Ordinary updates accept `id`, a lifecycle status, `markerColor`, `note`, and `sender`.

### `/api/prioritize`

- `POST`: authenticated; analyzes every unprocessed unresolved ticket without changing pending tickets to active, applies the existing Tier 1-over-Tier 2 Gemini triage, and returns the sorted tickets with optional `tacticalReasoning`. Omitted IDs fall back to urgency descending and then oldest first.

### `/api/intelligence`

- `POST`: authenticated; requires non-empty `text`, returns the three reconstruction fields, and does not persist a ticket.

## Storage and Security

- [src/lib/db.ts](src/lib/db.ts) reads and writes `src/data/tickets.json`, caches by file mtime, and serializes writes with an in-process promise chain.
- [src/lib/encryption.ts](src/lib/encryption.ts) uses AES-256-CBC with a random 16-byte IV and stores `iv_hex:ciphertext_hex`. The key comes from `ENCRYPTION_KEY` or the hardcoded fallback `emergency-dispatch-secure-key-32`, copied into a 32-byte buffer.
- Encrypted fields are `original`, `reconstructed`, JSON-stringified `location`, optional `manualLocation`, optional `victimName`, the optional structured emergency report, and each admin note’s `text`. IDs, urgency, category, timestamps, status, marker color, note timestamps/senders, and source remain plaintext.
- Decryption failures log an error and return the original value, supporting legacy/plaintext records but potentially exposing malformed plaintext.
- AES-CBC has no authentication tag or MAC, so ciphertext integrity is not verified.
- Login defaults are `admin` and `Aerolink2026!`; `checkAuth()` also accepts `x-bridge-auth` matching `ADMIN_PASSWORD` or its default. Successful login sets an HTTP-only, Strict SameSite cookie for one day.
- `/api/data` is unauthenticated, `/api/reconstruct?ids=...` exposes decrypted records without auth, and there is no schema validation, rate limiting, role model, or CSRF defense.
- The browser receives decrypted ticket data after an authorized API call; “AES-256 Enabled” describes local file storage, not end-to-end encryption.

## Hardware and Wire Protocols

### ESP32 firmware

The Victim ESP32 advertises as `AeroLink-Test`. Android writes the emergency JSON to BLE characteristic `beb5483e-36e1-4688-b7f5-ea07361b26a8`; the Victim joins `CodeRed_SOS_Network` and sends that JSON unchanged to `192.168.4.1:4330`. It notifies Android through characteristic `a1b2c3d4-e5f6-7890-abcd-ef1234567890` after `udp.endPacket()` succeeds.

The Base Station ESP32 creates the open `CodeRed_SOS_Network` access point, receives UDP on `4330`, prints the JSON and transport diagnostics over USB serial at `115200`, and sends a `BASE_STATION_RECEIVED` ACK on UDP `4331`. It also broadcasts newline-delimited serial input to `192.168.4.255:4331`. The current Victim firmware neither binds nor reads UDP `4331`, so both Base Station UDP messages are currently one-way transmissions. Neither sketch contains LoRa or relay code.

### Primary serial bridge

`bridge.js` accepts compact or pretty-printed JSON from the current base-station firmware. It ignores diagnostic text, safely frames USB fragments, validates the seven Android report fields, derives a stable numeric ticket ID from the report, deduplicates for 10 seconds, and posts the structured report to `/api/data`. For downlink it polls all tickets with `x-bridge-auth` and writes:

```text
[<ticket-id>] <admin note>\n
```

The documented `COMMAND TO <VICTIM>` format is not implemented.

### Alternate TCP bridge

`wifi_bridge.js` listens on TCP `5555` and accepts either:

```text
(Name|Location|Message)
[TKT-123] Name: Name | Loc: Location | Msg: Message
```

It forwards parsed messages to `/api/data` and emits `[COMMAND] New Feedback for <victim>: <note>` to the active TCP socket. Its `/api/reconstruct` polling lacks the required bridge header, so it normally receives `401` from the authenticated endpoint.

## UI Behavior

- `/` is the protected command center. It uses browser geolocation for the command marker, global text filtering, live notifications, local mock logs, profile/logout controls, and three informational modals.
- The Overview tab shows pending, active, and resolved counts. Its map receives every pending and active ticket and excludes resolved and legacy-completed tickets.
- Dispatcher supports Intake and Prioritize modes, selection, lazy AI signal processing, map/location display, messages, marker colors (`green`, `yellow`, `red`), closure, and a resolved archive.
- Priority analysis is explicit through the Dispatcher `Prioritize` control and remains within the Dispatcher workflow.
- Intelligence decoding is explicit and local to the feed; it expects optional `entities` and `confidence` fields even though the API returns only reconstructed text, urgency, and category, so the UI falls back to 90% confidence and normally shows no entities.
- `SituationalMap` creates victim overlays from structured report latitude/longitude first, followed by comma-separated `manualLocation` and stored numeric `location` fallbacks.
- `/monitor` and `/victim` poll the unauthenticated `/api/data` buffer, which is global rather than scoped to a device or ticket.

## Known Gaps and Stale Claims

- The README and existing product language claim LoRa/SX1278 mesh networking; the checked-in firmware implements Wi-Fi UDP only.
- No mesh relay, LoRa driver, or 433 MHz radio implementation exists.
- The old map entry for `scripts/bump.js` was removed because the file does not exist.
- `DisasterHeatMap.tsx` is unused and contains hardcoded Delhi demo data.
- `public/logo.png` is unused.
- The external notification buffer stores only the latest signal notification, while every accepted signal is persisted independently in Dispatcher Intake.
- The primary bridge deduplicates for 10 seconds while `/api/data` suppresses stable ticket IDs and compares matching persisted tickets for 15 seconds.
- `.env.example` omits `ENCRYPTION_KEY`, and local fallback credentials/key values exist in source. Any real credentials found in local environment files should be rotated if exposed.
- README states MIT licensing, but no `LICENSE` file is present.

## Local Commands

```bash
npm install
npm run dev
npm run lint
npm run build
node scripts/bridge.js --list
node scripts/bridge.js COM13
```

Open `http://localhost:3000`. The protected dashboard uses the configured environment credentials, or the source defaults when variables are absent. Gemini-backed actions require `GEMINI_API_KEY`.
