# Flood Response Platform (Hackathon Project)

> Read this file fully before doing anything. It is the single source of truth for what we are building and HOW we work together.

---

## 0. How to Work on This Project (READ FIRST)

This project is large. **Do not try to build everything at once.** Follow this workflow strictly.

### 0.1 Requirements first
1. **Understand before changing anything.** Read this file, then inspect the existing codebase (folder structure, configs, dependencies, any docs). Summarize what exists and what is missing.
2. **Gather technical details** before writing code: hardware specs, APIs, data sources, library versions, dependencies.
3. **Ask me about anything missing.** This includes, but is not limited to:
   - AI/ML datasets (rainfall, terrain, flood history), model requirements and training data
   - Which LLM/API to use for the report-cleaning layers, and API keys/config (never hardcode secrets)
   - Chosen district, data source access, database choice
   - ESP32 board models, pin/wiring details, connection method
   - Team size, skills and remaining time (if it affects scope)
4. **Do not silently assume anything important.** If you must proceed with an assumption, list it explicitly, mark it `ASSUMPTION`, and ask me to confirm. Wait for my answer on anything that affects architecture, data, or hardware.

### 0.2 Plan before implementing
- Break the work into phases (Section 7 is the starting point). For each phase list: goal, tasks, dependencies, files likely touched, how it will be tested, and "done when" criteria.
- **Show me the plan and get my approval before starting a phase.** Do not begin the next phase without approval.

### 0.3 Implement incrementally
- Finish **one phase at a time**.
- Keep changes small and focused. Do not refactor, rename or reformat unrelated code.
- Preserve working functionality. If a change could break something, say so first.
- Prefer simple, readable code. This is a hackathon, but it must run reliably.

### 0.4 Validate continuously
- Test every piece you add (unit tests where useful, plus a manual run). Show me the results.
- Verify integrations between components (API <-> engine <-> apps).
- Handle errors explicitly (bad input, missing data, network loss). No silent failures.
- Fix bugs before moving on. **Never start a new phase while the previous one has failing tests or known bugs**, unless I explicitly agree.

### 0.5 Keep the project consistent
- Keep documentation current: update `docs/PROGRESS.md` (see 0.6) and any affected docs at the end of each phase.
- Before finishing a phase, re-run earlier tests to confirm nothing regressed.
- If you discover a conflict between this file and reality (or a better idea), tell me instead of quietly deviating.

### 0.6 Tracking files (create in Phase 0)
- `docs/PROGRESS.md`: phases, status (not started / in progress / done), what was completed, known issues.
- `docs/DECISIONS.md`: important decisions and assumptions with date and reason.
- `docs/OPEN_QUESTIONS.md`: things I still need to answer.
- `docs/DATA_DICTIONARY.md`: every data format, feature and label.

### 0.7 Communication style
- Explain things in simple, plain language. Avoid unnecessary jargon.
- Report what you did, what you tested, what remains, and what you need from me.
- Say clearly when something is uncertain or untested.

---

## 1. Project Idea (Simple Version)

During floods, communities get warnings but often do not know **which roads are still usable** or **where help is needed first**. We are building a platform that:

1. Connects hazard warnings with affected settlements and road accessibility.
2. Uses rainfall/terrain data plus reports from people on the ground.
3. **Explains** every alert (evidence + confidence).
4. Helps response teams **prioritize** and **assign** teams, transport and shelter capacity.
5. **Predicts whether a road will still be usable when a team arrives**, not just whether it is open now.
6. **Replans** when conditions change.
7. Works even when the mobile network is down (offline reports through a LoRa-style link).

One-line summary: **"Warning in, action out, with proof."**

### 1.1 Scope (fixed, do not expand without asking)
- **One district** (set in a config file so it is swappable)
- **One primary hazard: flood**
- A **bounded road graph**: roughly 300 to 1,000 road segments, 15 to 40 settlements, 5 to 10 shelters
- Public geography data and documented, simulated disruption histories are acceptable

### 1.1a Mandatory Requirements Checklist (from the problem statement)
Every item below is a hard requirement. Track each one in `docs/PROGRESS.md` with status and evidence (test, file or screenshot). Do not call the project complete until all are verified.

**Base requirements**
| # | Requirement | Where built | How it is verified |
|---|---|---|---|
| B1 | Covers **one district** and **one primary hazard type** (flood) | Phase 0, 1 | District and hazard set in config; no other district/hazard code paths required |
| B2 | Uses rainfall/terrain data (live, historical, or clearly labeled replayed data) to **map affected settlements and road closures** | Phase 1, 2, 3 | Given rainfall + terrain, the engine outputs a list of affected settlements and closed/at-risk road segments; test with at least one live-feed run and one replay |
| B3 | **Updates response priorities as conditions change** | Phase 3, 7 | Changing rainfall, a closure or a new report re-ranks settlements; test shows rank change and a recorded reason |
| B4 | Shows the **evidence and confidence** behind each warning | Phase 3 | Every alert has an evidence card (why, confidence with reason, data age); no alert without one |
| B5 | Is **tested on false-alert rate and route validity** under simulated disruption | Phase 5, 10 | Evaluation script runs on held-out simulated disruption events and reports both metrics, for our system and the baseline |
| B6 | **Clearly timestamps and labels any replayed historical event**, so it is never confused with live data | Phase 2, 8 | `source=replay` with original and replay timestamps on every record; banner on all three apps; exports carry the label; test that replay data can never appear unlabeled |

**Addition 1: Resource-constrained response planning**
| # | Requirement | Where built | How it is verified |
|---|---|---|---|
| A1.1 | Assign teams, transport and shelter capacity to affected settlements using declared priorities, travel times, resource requirements and confirmed road status | Phase 6 | Solver output respects priorities, travel times and confirmed closures |
| A1.2 | Track assignments over time; prevent conflicting team use and shelter overflow | Phase 6 | Resource ledger tests: no double-booked team, no shelter above capacity |
| A1.3 | Show unmet needs and the reasons they remain unmet | Phase 6, 8 | Unmet-needs panel lists each unserved settlement with a specific reason |
| A1.4 | Replan after a closure, changed hazard report or resource loss; preserve completed/committed actions; label historical replay timestamps | Phase 7 | Replan tests for each trigger; completed/committed actions unchanged; "what changed and why" note; replay labels intact |

**Addition 2: Predicting road accessibility at arrival**
| # | Requirement | Where built | How it is verified |
|---|---|---|---|
| A2.1 | Predict whether a segment will remain usable at expected arrival, using time-stamped environmental conditions, terrain and reports available at decision time | Phase 5 | Feature pipeline uses only data with timestamp <= decision time (leakage test) |
| A2.2 | Use predictive uncertainty to compare feasible routes and plans; confirmed closures stay binding until valid updated evidence changes them | Phase 5, 6 | Routes show reliability; test that the model never reopens a confirmed closure |
| A2.3 | Compare against current-status-only routing on identical held-out event sequences; report prediction quality, invalid routes and response delays | Phase 10 | Matched comparison table: precision/recall/AUC/calibration, invalid routes, response delay |

**Scope and data**
- One district, one hazard, a bounded road graph with settlements and shelters. Public geography and documented simulated disruption histories are acceptable (document how they were generated).

**Required demonstration (all must appear in the demo scenario)**
1. Deteriorating access
2. A confirmed closure
3. Insufficient shelter or transport capacity
4. Conflicting or stale reports
5. Unserved settlements and replanning

**Required evidence to submit**
Road/event replays, resource ledgers, forecast features and labels, dispatch logs, route checks, and matched baseline response outcomes (see Section 6).

### 1.2 Judging criteria (design decisions should serve these)
1. Innovativeness
2. Tech stack (modern, effective)
3. Presentation (clear, organized)
4. UI/UX (simple, usable)
5. AI & ML integration (real depth, not decoration)

---

## 2. Core Principles (Non-Negotiable)

1. **Honest labeling.** Every record carries a timestamp and a `source` field with one of three values: `live`, `replay` (a real historical event played back) or `simulated` (synthetic/generated). Replay and simulated data must always be labeled on screen, in logs and in exports, never confused with live data.
   - Every `replay` record carries **both** the original event timestamp and the replay timestamp, plus the event name/date (e.g., "REPLAY of flood event dated YYYY-MM-DD, not live").
   - A persistent banner is visible on every screen (dashboard, team app, citizen app) whenever the system is not showing live data: "REPLAY: event dated X" or "SIMULATION".
   - Users still see only two modes (Live and Demo Scenario). A Demo Scenario may be built from a real historical event (labeled `replay`) or be fully synthetic (labeled `simulated`), and the label says which.
   - The engine itself ignores `source` when making decisions (see principle 2); it is only for labeling and auditing.
2. **One pipeline.** Live data and demo data go through the **exact same engine**. Only the data source changes. No special-case logic for demo.
3. **Confirmed closures are binding.** A confirmed road closure stays closed until valid, newer evidence changes its status. The ML model can **never** override it.
4. **Decision-time data only.** Predictions may only use information available at the time of the decision (no leakage from the future).
5. **LLM never invents numbers.** Numbers come from the model, rules and data. The LLM is used only to repair/structure report text and to write explanations from already-computed values.
6. **Show evidence.** Every warning, report label and plan decision must be explainable in plain language.
7. **Emulated hardware is disclosed.** In the demo, the offline link is an ESP32 emulation of LoRa. Label it as such on the slide/docs (see Section 5.4).

---

## 3. The Three Components

```
 Data sources ──► CORE ENGINE ──► 1. COMMAND DASHBOARD (admin)
 (live / demo)    (shared)            │
                                      ├──► 2. TEAM APP (phone)
 Citizen reports ──►                  │
 (internet or ESP32 link)             └──► 3. CITIZEN APP (phone)
```

### 3.1 Command Dashboard (admin/operator web app)
Receives and analyzes everything. Contains:
- **Map**: settlements, roads colored by predicted usability (green/yellow/red), confirmed closures shown locked.
- **Data mode**: Live data view, or **Demo Scenario** (generated flood). Switching mode changes only the data source.
- **Severity-ranked settlement list** that re-prioritizes as conditions change.
- **Evidence and confidence panel** for each warning (why, confidence level, data age).
- **Report inbox**: incoming reports (internet or offline link), showing raw text, AI-cleaned text, structured fields, and trust label.
- **Assignment screen**: admin sees available teams/vehicles and assigns them to affected settlements; the assignment is pushed to the team lead's phone.
- **Rescue/transport map**: where to transport people, which vehicle to use, route options with reliability.
- **Shelter overview**: capacity and current occupancy for each shelter; overflow handling.
- **Resource ledger**: every team, vehicle and bed over time (free, assigned, en route, done).
- **Unmet needs panel**: each unserved settlement with the reason.
- **Replan view**: "what changed and why" after each change.
- **Evaluation page**: our system vs. the baseline (Section 6).

### 3.2 Team App (mobile-friendly web app / PWA)
For team leads in the field:
- Receives assignments (target, vehicle, route, route reliability).
- Buttons to update status: Accepted / En route / Arrived / Completed / Road blocked.
- Updates flow back to the dashboard and the resource ledger.

### 3.3 Citizen App (mobile-friendly web app / PWA)
For people in affected areas:
- Receives emergency alerts and a road-access forecast for their area (simulated SMS/push in the demo; a real SMS provider can plug in later).
- Sends field reports:
  - **Online path:** through the internet.
  - **Offline path:** connects (Wi-Fi/Bluetooth) to a LoRa-style device, which relays the message to the dashboard when there is no cellular/internet.
- Short report form: quick buttons (road blocked, need rescue, shelter full, people count) + a short note + the sender's settlement/location. Messages must stay **small** (LoRa packets are tiny, roughly 50 to 200 bytes).

---

## 4. Core Engine: Functional Requirements

### 4.1 Data layer
- Static: roads, settlements, shelters (OpenStreetMap), terrain (DEM: elevation, slope, low-lying areas), population.
- Dynamic: rainfall (live feed + historical), reports, resource states.
- **Live feed:** real rainfall data (may look calm; that is expected). Labeled `source=live`.
- **Replay of a real historical flood:** played back hour by hour at replay speed. Labeled `source=replay`, with the original event date/time and the replay time on every record.
- **Demo Scenario generator:** one action creates a story over time: rain builds, roads degrade, closures are confirmed, shelters fill, conflicting and stale reports arrive. It is documented and reproducible (seeded).
- **Training/test event generator:** produces many documented simulated flood events, including held-out events for evaluation.

### 4.2 Warning engine (explainable)
- Risk score per settlement and per road segment from: recent rainfall (1h/3h/6h), forecast, ground saturation (past days), terrain, and reports.
- Each alert has an **evidence card**: why, confidence (high/medium/low) with the reason, and data age.
- Severity-based prioritization that updates whenever data changes.

### 4.3 Report pipeline and trust engine
1. **Intake** from the citizen app (internet) or the offline link.
2. **AI layer 1:** repair broken/garbled text.
3. **AI layer 2:** convert to a structured record (location, road, status, people count, time). Fill only what is stated; leave blanks instead of guessing.
4. Always store the **raw message** next to the cleaned version, with a confidence label. Low confidence -> "needs human check".
5. **Trust score** from:
   - **Location consistency:** compare the sender's location with the reported place. A sender in settlement D reporting a problem in settlement A is **not at the location**: lower trust. Use distance (tunable threshold), and for roads, distance to the nearest point on the segment.
   - Agreement with other reports nearby
   - Agreement with rainfall/terrain evidence
   - Report age (staleness decay)
   - Source type (official, volunteer, anonymous) and sender history if available
6. **Labels:** On-site / Nearby / Not at location (with plain-language reason).
7. **Rules:** "Not at location" reports are never deleted; they stay visible with lower weight and can **never confirm a closure on their own**. Conflicts (open vs. closed) are shown openly and lower confidence.
8. Note: during the demo the presenter is not physically in the district, so the apps must support a **"set my location"** option (pick settlement or drop a pin) and the demo scenario's fake reports carry simulated sender locations.

### 4.4 Road accessibility prediction (Addition 2)
- Predict whether a segment is **still usable at expected arrival time**, using only decision-time data.
- Features: rainfall so far, forecast, ground saturation, elevation, slope, distance to river, road type, past closures, latest report status and its age, minutes until arrival.
- Labels: whether the segment was usable at arrival time in replayed/simulated events.
- Model: start with gradient boosting (LightGBM or XGBoost). **Calibrate probabilities** and output uncertainty.
- Split data **by event**, never randomly (held-out event sequences).
- **Risk-aware routing:** route reliability = product of segment usability probabilities; cost = travel time + risk penalty; show alternatives (fastest vs. safest). Confirmed closures are removed entirely.
- **Confirmed closures stay binding until valid updated evidence changes their status.** Define "valid updated evidence" explicitly and keep it in config. Starting proposal (confirm with me): reopening requires a report/observation that is **newer than the closure timestamp** AND from an official source, or from multiple trusted on-site reports that agree; reports labeled "Not at location", stale reports, and the ML model alone can never reopen a road. Every reopen/close decision is logged with its evidence.
- **Time-stamped inputs only:** every environmental observation, forecast and report used as a feature must carry its own timestamp, and the feature builder rejects anything newer than the decision time. Add an automated leakage test.
- Predictions are made for **expected arrival time** (decision time + estimated travel time to that segment), not for "now".

### 4.5 Resource allocation (Addition 1)
- Inputs: settlement needs and **declared priority**, **resource requirements per settlement** (e.g., number and type of rescue teams, vehicles/boats, people to shelter, medical needs), team/vehicle/shelter resources with locations and availability, **travel times**, and **confirmed road status**.
- Solver (e.g., OR-Tools) assigns teams, transport and shelter beds.
- Constraints: no team in two places at once, no shelter over capacity, only valid routes, vehicle type must suit the task and the route, priority first and travel time as tiebreaker.
- **Use route reliability (Addition 2) in planning, not only in routing.** Plans are compared using predicted reliability: a settlement reachable only by a low-reliability route is flagged, and the planner may prefer a slightly slower but more reliable plan. Confirmed closures are hard constraints, never trade-offs.
- **Resource ledger is time-indexed.** Every team, vehicle and bed has reserved time windows (assigned, en route, on task, done, free), with timestamps. Before any assignment is accepted, the ledger checks for overlaps (team double-use) and shelter occupancy over time (including people already en route). Every ledger entry carries the `source` label (live/replay/simulated) and the replay timestamp where relevant.
- **Unmet needs** keep a specific machine-readable reason code plus a plain-language reason, and are shown over time (when they appeared, when/if they were resolved).
- **Unmet needs** are logged with reasons (e.g., "only road closed (confirmed 14:10)", "Shelter A full, B unreachable", "no transport left").

### 4.6 Dynamic replanning
- **Triggers:** road closure, new/changed field report, **changed hazard warning/severity**, shelter full, **resource loss** (team unavailable, vehicle breakdown, shelter lost).
- Completed actions stay as history. Committed actions (e.g., a team already past the point of return) stay locked unless they became impossible. Only uncommitted parts are replanned.
- If a committed action becomes impossible (e.g., its road closed mid-route), it is explicitly flagged and re-handled, with the reason recorded; never silently dropped.
- Every change gets a "what changed and why" note, stored in the dispatch log with timestamp.
- **Replay labeling in replans:** during a replay, every replan, dispatch log entry and ledger change shows both the original event timestamp and the replay timestamp, and the replay label. Historical timestamps are never presented as live.

---

## 5. Hardware: Offline Report Link

### 5.1 Real design (concept)
Citizen phone connects (Wi-Fi/Bluetooth) to a LoRa device, which sends the small message over LoRa to a gateway connected to the command dashboard. Works with no cellular network or internet.

### 5.2 Demo implementation
- Two ESP32 boards.
- ESP32 #1: provides a Wi-Fi access point and a tiny report page; the phone connects to it.
- ESP32 #1 -> ESP32 #2 via **ESP-NOW** (direct, no router/internet, small packets similar to LoRa). Preferred over chaining Wi-Fi hotspots. Confirm with me before choosing.
- ESP32 #2 is connected to the dashboard computer (USB serial); the backend reads messages and feeds the report pipeline.
- If real LoRa boards (e.g., Heltec/TTGO LoRa32) become available, the transport can be swapped without changing the pipeline.

### 5.3 Requirements
- Keep messages within a small fixed size (compact format, e.g., short codes + settlement ID + count + short note).
- Handle lost/duplicate/garbled packets gracefully (this is why AI layer 1 exists).
- Hardware code lives in its own folder with wiring notes and setup instructions.
- **Ask me** for board models, pins and available parts before writing firmware.

### 5.4 Disclosure
Docs and the demo slide must say: *"LoRa link emulated using ESP32 (ESP-NOW). Same flow and packet constraints; production uses LoRa radios."*

---

## 6. Evaluation and Evidence (Must Be Built In)

Run our system and a **current-status-only baseline** (shortest path on currently open roads) on the **same held-out event sequences**.

**Matched comparison rules**
- Identical event sequences, identical starting resources, identical decision times, identical allocation solver and constraints. The **only** difference is the road-accessibility input: baseline uses current status only; ours uses predicted usability at arrival with uncertainty. This isolates the benefit of Addition 2.
- Both systems must treat confirmed closures as binding.
- Held-out events are never used in training or threshold tuning.

**Metric definitions (write these in `docs/DATA_DICTIONARY.md` before computing anything)**
- **Invalid route:** a dispatched route that includes any segment that is confirmed closed, or that is actually unusable at the time the team reaches it (according to the event's ground truth).
- **Response delay:** time from the settlement's need becoming known (or priority declared) to the first team arriving, counting reroutes and failed attempts. Report average, median and worst case.
- **Accessibility prediction quality:** precision, recall, AUC, calibration (reliability curve and Brier score), per held-out event and overall.
- **False-alert rate:** share of warnings that did not materialize within the defined window.

Report:
- False-alert rate
- Accessibility prediction quality: precision, recall, AUC, calibration
- Invalid routes (routes that hit a road unusable at arrival)
- Response delay (average and worst-case)
- Population served, shelter use, unmet needs

Required demonstrations (script the demo scenario to show all):
1. Deteriorating access
2. A confirmed closure
3. Insufficient shelter or transport capacity
4. Conflicting or stale reports
5. Unserved settlements and replanning

Submission pack (generate automatically from the engine, not by hand):
- Road/event replays (labeled, timestamped)
- Resource ledgers
- Forecast features and labels
- Dispatch logs
- Route validity checks
- Matched baseline outcomes

---

## 7. Phases (Starting Plan: Refine and Get Approval)

| Phase | Name | Done when |
|---|---|---|
| 0 | Foundations: approved file structure (Section 9.1), repo, shared data formats, API contract, shared clock, tracking docs | Folder structure created and documented in `docs/STRUCTURE.md`; everyone can call a test API; docs created |
| 1 | Map and data base: roads graph, settlements, shelters, terrain, rainfall loading | Map shows district with all entities |
| 2 | Data source layer: live feed, demo scenario generator, event generator | Pressing the scenario button feeds the engine like live data |
| 3 | Warning engine with evidence cards and severity ranking | Each alert opens to a clear explanation |
| 4 | Report pipeline and trust engine (AI layers, location check, conflicts, staleness) | "Not at location", stale and conflicting reports behave correctly |
| 5 | Road accessibility prediction and risk-aware routing | Route options with reliability, calibrated model, event-based split |
| 6 | Resource allocation, ledger, unmet needs | No conflicts or overflow; unmet needs have reasons |
| 7 | Dynamic replanning | Closure triggers a reroute with a "what changed" note |
| 8 | Three apps: command dashboard, team app, citizen app | Full flow works end-to-end |
| 9 | ESP32 offline link | Message from phone reaches dashboard without internet |
| 10 | Evaluation vs. baseline and submission pack | Metrics table and exports generated |
| 11 | Demo rehearsal, polish, backup recording | Scripted demo runs cleanly, twice in a row |

Notes:
- Phase 9 (hardware) can be developed in parallel and plugged in at Phase 4.
- If time runs short, cut in this order: real SMS (simulate it), live hardware demo (use a recorded video), citizen-app polish, Bluetooth (keep Wi-Fi). **Never cut:** prediction model, baseline comparison, replanning, unmet-needs panel.

---

## 8. Suggested Tech Stack (Confirm With Me Before Locking)

- **Data/ML:** Python, pandas, GeoPandas, LightGBM or XGBoost, scikit-learn (calibration)
- **Routing:** NetworkX or OSMnx
- **Optimization:** OR-Tools
- **Backend:** FastAPI; PostgreSQL + PostGIS (SQLite acceptable to start)
- **Frontend:** React, Leaflet or MapLibre, Tailwind; apps as PWAs
- **LLM:** only for report repair/structuring and explanation text, via a configurable API (keys in environment variables)
- **Hardware:** ESP32 (Arduino or ESP-IDF), ESP-NOW

If you recommend something different, explain why and ask before switching.

---

## 9. Code and Repo Conventions

### 9.1 Project File Structure (generate this in Phase 0)

**Claude Code must create this folder structure as part of Phase 0, after I approve it.** Rules for generating it:
- First inspect the current repo. If files already exist, **adapt to them**: do not move, rename or delete existing files without asking me.
- Propose the final tree to me (adjusted to the chosen stack and anything that already exists) and **wait for approval** before creating anything.
- Create only the folders and placeholder files (empty stubs and a short `README.md` per major folder saying what belongs there). **No real logic in the scaffold.**
- Save the approved tree and one-line purposes to `docs/STRUCTURE.md`. If the structure changes later, update that file and log the reason in `docs/DECISIONS.md`.
- Keep each module small and focused on one job, so each phase touches few files.

Proposed structure (starting point; names can change after stack decisions):

```
flood-response-platform/
├── CLAUDE.md                     this file
├── README.md                     how to install, run, demo
├── .env.example                  required environment variables (no secrets)
├── .gitignore
│
├── config/
│   ├── district.yaml             chosen district, boundary, hazard = flood
│   ├── thresholds.yaml           trust distance, staleness decay, reopen rules, risk penalties
│   └── scenarios/                demo scenario definitions (seeded)
│
├── docs/
│   ├── PROGRESS.md               phase status + requirements checklist (Section 1.1a)
│   ├── DECISIONS.md              decisions and assumptions with reasons
│   ├── OPEN_QUESTIONS.md         things I still need to answer
│   ├── DATA_DICTIONARY.md        data formats, features, labels, metric definitions
│   ├── STRUCTURE.md              approved file tree and purposes
│   ├── ARCHITECTURE.md           how the pieces connect
│   ├── API_CONTRACT.md           backend endpoints and message formats
│   ├── HARDWARE.md               ESP32 wiring, setup, disclosure line
│   └── DEMO_SCRIPT.md            step-by-step demo with timings
│
├── data/
│   ├── raw/                      downloaded source data (OSM, DEM, rainfall, population)
│   ├── processed/                cleaned graph, settlements, shelters, terrain features
│   ├── replays/                  real historical events (labeled, with original dates)
│   ├── generators/               scenario generator, training/test event generator (seeded)
│   └── SOURCES.md                where every dataset came from, license, date downloaded
│
├── engine/                       core logic, shared by live, replay and simulated data
│   ├── clock.py                  shared clock (live time or replay time)
│   ├── schemas.py                shared data models (settlement, segment, report, resource, assignment, event)
│   ├── ingest/                   live feed, replay player, scenario player (all emit the same format)
│   ├── warnings/                 risk scores, evidence cards, severity ranking
│   ├── reports/                  AI repair layer, AI structuring layer, trust engine, conflicts, staleness
│   ├── prediction/               feature builder, training, calibration, arrival-time prediction
│   ├── routing/                  road graph, risk-aware routing, route reliability
│   ├── allocation/               solver, time-indexed resource ledger, unmet needs
│   ├── replanning/               triggers, committed/completed action handling, "what changed" notes
│   └── pipeline.py               ties the steps together in order
│
├── models/
│   ├── training/                 training scripts and experiment notes
│   └── saved/                    trained model files + version info
│
├── evaluation/
│   ├── baseline.py               current-status-only routing, same solver and resources
│   ├── metrics.py                false-alert rate, precision/recall/AUC/calibration, invalid routes, delays
│   ├── run_eval.py               runs both systems on identical held-out events
│   └── results/                  tables and charts
│
├── backend/
│   ├── app/
│   │   ├── main.py               API entry point
│   │   ├── api/                  endpoints: reports, alerts, assignments, resources, scenarios, evaluation
│   │   ├── services/             glue between API and engine
│   │   ├── realtime/             live updates to the apps (websocket/SSE)
│   │   └── db/                   database models and migrations
│   └── requirements.txt (or pyproject.toml)
│
├── apps/
│   ├── shared/                   shared UI pieces, API client, replay/simulation banner
│   ├── command-dashboard/        map, priority list, evidence panel, report inbox, assignments,
│   │                             shelter overview, ledger, unmet needs, replan view, evaluation page
│   ├── team-app/                 assignments, route + reliability, status buttons
│   └── citizen-app/              alerts, access forecast, report form (online + offline path), "set my location"
│
├── hardware/
│   ├── esp32-phone-node/         firmware: Wi-Fi access point + report page + ESP-NOW send
│   ├── esp32-gateway/            firmware: ESP-NOW receive + USB serial to the dashboard computer
│   ├── bridge/                   backend-side reader that turns serial messages into reports
│   └── WIRING.md
│
├── exports/                      auto-generated submission pack
│   ├── replays/
│   ├── resource_ledgers/
│   ├── forecast_features_labels/
│   ├── dispatch_logs/
│   ├── route_checks/
│   └── baseline_outcomes/
│
├── tests/
│   ├── unit/                     per-module tests (trust, features, routing, ledger, ...)
│   ├── integration/              engine <-> backend <-> apps
│   └── scenarios/                end-to-end: the five required demo situations
│
└── scripts/                      helper commands (setup, load data, run demo, export pack)
```

Where the main requirements live in this structure: replay labels and `source` field in `engine/ingest` + `engine/schemas.py`; leakage test in `tests/unit` for `engine/prediction`; matched baseline in `evaluation/`; submission evidence in `exports/`.
- Configuration in config files/env vars (district, thresholds, API keys). No hardcoded secrets.
- Every function that touches time must use the shared clock, not the system clock directly.
- Seed all random generators so scenarios and results are reproducible.
- Write clear commit messages, one logical change per commit.
- Add short comments where logic is non-obvious, especially trust, prediction and replanning rules.

---

## 10. Risks to Watch

- **Scope creep:** the core (prediction, routing, allocation, replanning, baseline comparison) matters more than extras.
- **Data leakage** in the prediction model (using future info, or random splits across events).
- **AI cleaning errors:** always keep raw text and show confidence.
- **Hardware demo fragility:** Wi-Fi interference in busy halls; test early and keep a backup recording.
- **Mixing demo and live data** without labels.

---

## 11. First Steps for Claude Code

1. Read this file and inspect the current repo. Report what exists.
2. List everything you still need from me (data, hardware, API/config, team and time constraints) in `docs/OPEN_QUESTIONS.md` and ask me directly.
3. Propose the project file structure (Section 9.1), adjusted to what already exists in the repo, and show me the tree for approval.
4. Propose a refined Phase 0 and Phase 1 plan with tasks, dependencies and tests.
5. **Wait for my approval before creating any folders, files or code.**
