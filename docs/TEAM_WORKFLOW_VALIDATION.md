# Team assignment increment — 2026-10-11

The user explicitly prioritized team functionality after Slice 2: teams must be assignable to settlements during an exercise and receive/return updates through the Team App. This increment is implemented ahead of the earlier citizen/NLP slice. It does not mark the entire routing/allocation phase complete.

## Working journey

1. Open http://127.0.0.1:5173. Choose Replay & exercises and load a synthetic exercise (historical weather is also supported).
2. Open Teams & assignments. Add Team A with a current settlement, member count and declared capabilities.
3. Choose a target settlement, required capability, an eligible team and task instructions. Assign team.
4. Use Open Team App in the roster. This opens a separate local view for that team. It receives the task automatically.
5. Accept → En route → Arrived → Completed. Send a free-text status message at any active stage. Report road blocked requires a description; it reserves the team and raises an operator-review notice. Resume travel is an explicit team action, not a model reopening a road.
6. Dashboard polling receives updates within about five seconds. Locate assignment shows the target settlement, assigned team and task status on the map. Markers are assignment destinations, not GPS tracking or travel paths.
7. Return to Live: its roster and assignments are separate. Returning to Replay restores the active backend run, including assignments; a page reload still defaults to Live.

Warnings and selected-settlement details have assignment actions. The assignment form displays the selected settlement's current severity/confidence/priority. A later severity change flags active tasks for operator review; the system does not silently change an assigned destination. Completed tasks remain in history.

## Persistence and constraints

- SQLite at data/runtime/operations.sqlite3, ignored by Git. Lazy initialization, transactional writes, a unique active-assignment index, unique names per context and client request IDs.
- Team inventories are isolated by context: live or the exact exercise run ID. Each reset/new run gets an empty independent roster. Old records remain in SQLite and old team links become read-only. The timeline itself is still in memory; a backend restart ends exercise updates but preserves records. Live assignments remain usable after restart.
- Team capability and availability checked on dispatch. Active assignment blocks a second task and roster edits. Completion releases the reservation and records the team at the target settlement; this is a reported location, not GPS.
- Enforced status transitions and optimistic versions reject stale updates. Repeated identical request IDs are idempotent. Admin cancellation only applies before travel (assigned/accepted). En-route, arrived and blocked commitments cannot be silently cancelled/reassigned through this control.
- Assignment captures assessment evidence at dispatch. Every assignment/update records event time and wall receipt time. Actions performed against historical weather are still **simulated assignments**, never claimed as historical rescue records.
- Team links contain a random bearer capability in the URL fragment, sent to the API as an Authorization header. A link only updates its team's tasks. Keep links private. The command center is a local prototype without administrator authentication; do not expose this server publicly. No production access-control claim is made.
- No messages are sent through external SMS/email/radio services. Team App uses the same laptop backend. Phone/LAN exposure, authenticated multi-user deployment and offline delivery remain separate work.

## Scope limits

This is manual assignment plus task coordination. Candidate teams are filtered by availability and declared capability. There is no invented shortest route, travel time, arrival-time road prediction, shelter suitability, vehicle/bed reservation or automatic replan. An unstructured team blockage note requires review; it does not automatically identify or confirm closure of a specific road segment or alter the flood engine as a verified ground observation.

Remaining integration dependencies: teammate road model payload/window semantics and artifact/API, terrain road extrema, closure verification policy, resource inventories, citizen/NLP dispatcher integration. Those must be built before claiming the complete recommended-team → feasible route → shelter → resource/replanning workflow.

## Validation

- 97 Python tests passed, including seven new integration tests: full lifecycle/messages/location/release, concurrent double-booking attempts, dispatch/update retries, capability/availability/name/location validation, invalid transitions and versions, cross-team access rejection, blocked reservations, uncommitted cancellation, SQLite reopening, live/exercise/reset isolation and commitment preservation while weather advances.
- TypeScript/Vite build passed.
- All 9 browser tests passed in 55.7 seconds. Integration exercised control center and separate Team App, assignment delivery, blockage/resume/completion, map consistency, page reload restoration, reset isolation and mobile width, along with existing live/replay/warning regressions.
- Screenshots: docs/screenshots/teams-desktop.png and docs/screenshots/team-app-mobile.png. Inspected both. Existing live/replay/warning browser tests are retained.
- One existing Starlette TestClient deprecation warning remains; it does not fail tests.

No existing geography, weather source files, team records or previous assignment history were discarded. Test team records are confined to clearly simulated run contexts.
