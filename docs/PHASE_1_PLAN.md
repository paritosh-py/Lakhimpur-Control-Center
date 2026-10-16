# Phase 1 plan — approved and completed

User approved Phase 1. Final scope and validation evidence are in [PHASE_1_DATA_REPORT.md](PHASE_1_DATA_REPORT.md). Final bounded coverage is 800 road segments, 16 settlements and 7 reference camps.

Goal: a verified, bounded Lakhimpur geography dataset with rainfall/terrain inputs and a minimal map.
Budget target: about 3 hours; report access blockers rather than silently inventing source data.

Tasks:
1. Obtain and verify district boundary; select a connected study area within it. Target 300–1,000 road segments, 15–40 settlements and 5–10 shelters (default target 500/20/5).
2. Download/cache OSM roads, waterways and settlements; inspect connectivity and settlement-to-road attachment. Verify shelter evidence or explicitly mark demonstration locations/capacities simulated.
3. Acquire DEM and derive elevation/slope; record voids and missing values without substituting zeros. Confirm download credentials if needed.
4. Fetch a timestamped weather sample and official supporting evidence where accessible. Record units, source resolution, issue/availability/validity timestamps and retrieval time.
5. Select a documented historical flood event for the next phase's replay; keep synthetic disruption truth separate.
6. Initialize the shared frontend and minimal map; add read-only geography endpoints. Full source adapters, generator, warnings and role workflows belong to later phases.
7. Update source register, dictionary, decisions and requirement evidence.

Likely files: config/district.yaml; scripts/load_geography.py; data/raw/ and processed/; data/SOURCES.md; engine/ingest/; backend/app/api/; apps/web/; tests/unit/ and integration/; docs/.

Dependencies: network/download access; authoritative boundary identification; usable DEM route; source attribution/license review; explicit simulation labels for any unsupported shelter capacity or population needs.

Tests: graph size/connectivity; valid coordinates and positive edge lengths; entity references and nearest-road attachment; rainfall units and timestamps; missing-data handling; cached download reproducibility; API geometry response; browser map inspection; rerun Phase 0 tests.

Done when: map shows verified district/study area, bounded roads, settlements and shelter points; terrain/weather samples are usable and documented; simulated values are visible as such; all checks pass. External-source gaps are reported and must not be marked complete without evidence or an agreed scope change.
