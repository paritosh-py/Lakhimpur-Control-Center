# Phase 3 Proposal — Warning Engine with Evidence Cards and Severity Ranking

> Approved and in progress according to docs/PROGRESS.md and the approval section of docs/HANDOFF.md. Completion validation remains pending.

## Goal
Connect the ingested environmental and operational data streams (weather, terrain, road graph, and reports) to compute explainable risk scores, generate evidence cards (Requirement B4), and dynamically rank settlements and road segments by severity as inputs change (Requirement B3).

## Key Tasks
1. **Warning Engine Core (`engine/warnings/risk.py`)**:
   - Compute risk score per settlement and per road segment from:
     - Recent rainfall accumulation (1h, 3h, 6h)
     - Ground saturation (cumulative past days)
     - Terrain features (elevation, slope, distance to nearest river)
     - Incoming field reports (closures, water levels)
   - Calibrated risk scoring scale [0.0, 1.0] with severity tiers: Low, Medium, High, Critical.

2. **Evidence Cards & Explainability (`engine/warnings/evidence.py`)** (Requirement B4):
   - Every warning produces an explicit Evidence Card containing:
     - **Why**: Plain-language breakdown of contributory factors (e.g., "78 mm rain in past 6h; low elevation 92m; 180m from Ranganadi River").
     - **Confidence Level**: High / Medium / Low with explicit machine-readable rationale (data source quality, observation density, age).
     - **Data Age**: Staleness in minutes/hours for each contributing source.
   - Guard: No warning or alert can be issued without an evidence card.

3. **Severity-Based Settlement Ranking (`engine/warnings/ranking.py`)** (Requirement B3):
   - Dynamic prioritization algorithm ordering all 16 settlements by urgency.
   - Track rank changes over time: whenever new rainfall arrives, a road closes, or a field report appears, settlements re-rank with an auditable reason recorded ("Naobaicha rose from #4 to #1 due to confirmed closure on access corridor osm-238668521").

4. **API Endpoints (`backend/app/api/warnings.py`)**:
   - `GET /api/warnings/settlements`: Ranked settlements with current risk score, priority rank, rank change delta, and evidence card.
   - `GET /api/warnings/roads`: At-risk and closed road segments with flood risk score and evidence.
   - `GET /api/warnings/evidence/{entity_id}`: Full evidence card for a specific settlement or road.

5. **Web UI Integration (`apps/web/src/`)**:
   - Severity-ranked settlements panel in Command Dashboard.
   - Interactive evidence card modal/drawer when clicking an alert or settlement.
   - Visual risk indicators (color coding roads/settlements by warning severity).

## Dependencies
- Completed Phase 1 (geography graph, terrain, settlement & shelter GeoJSON).
- Completed Phase 2 (source adapters, scenario player emitting timestamped records).

## Tests & Verification
- Unit tests (`tests/unit/test_warnings.py`):
  - Risk formula sanity (higher rain, lower elevation, closer river = higher risk).
  - Every alert has an evidence card with why, confidence, and age (Requirement B4).
  - Input changes trigger settlement re-ranking with recorded reason (Requirement B3).
  - Stale or missing data lowers confidence score appropriately.
- Integration tests (`tests/integration/test_warnings_api.py`):
  - API endpoints return valid ranked list and evidence cards.
- Playwright E2E test (`apps/web/tests/warnings.spec.ts`):
  - Dashboard shows severity rank list, clicking displays evidence card.

## Done When
- Changing weather or stepping a scenario dynamically re-ranks settlements with recorded reasons.
- Every warning exposes an evidence card with why, confidence, and data age.
- 100% of test suite passes.
