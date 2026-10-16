"""Phase 2 integration tests: scenario API endpoints."""
from fastapi.testclient import TestClient

from backend.app.main import create_app

client = TestClient(create_app())


class TestScenarioAPI:
    def test_status_before_start(self):
        client.post("/api/scenario/stop")
        r = client.get("/api/scenario/status")
        assert r.status_code == 200
        data = r.json()
        assert data["is_active"] is False
        assert data["mode"] is None

    def test_step_before_start_fails(self):
        r = client.post("/api/scenario/step")
        assert r.status_code == 400

    def test_scenario_lifecycle(self):
        """Start → step → step → status → reset → step → stop."""
        # Start
        r = client.post("/api/scenario/start", json={
            "mode": "scenario", "seed": 42, "duration_hours": 12
        })
        assert r.status_code == 200
        data = r.json()
        assert data["mode"] == "scenario"
        assert "SIMULATION" in data["display_label"]
        run_id_1 = data["run_id"]

        # Step 1
        r = client.post("/api/scenario/step")
        assert r.status_code == 200
        step_data = r.json()
        assert step_data["step_index"] == 1
        assert step_data["run_id"] == run_id_1
        assert "SIMULATION" in step_data["display_label"]

        # Step 2
        r = client.post("/api/scenario/step")
        assert r.status_code == 200
        assert r.json()["step_index"] == 2

        # Status
        r = client.get("/api/scenario/status")
        assert r.status_code == 200
        assert r.json()["step_index"] == 2
        assert r.json()["is_active"]

        # Reset
        r = client.post("/api/scenario/reset")
        assert r.status_code == 200
        reset_data = r.json()
        run_id_2 = reset_data["run_id"]
        assert run_id_2 != run_id_1
        assert reset_data["status"]["step_index"] == 0

        # Step after reset
        r = client.post("/api/scenario/step")
        assert r.status_code == 200
        assert r.json()["step_index"] == 1
        assert r.json()["run_id"] == run_id_2

        # Stop
        r = client.post("/api/scenario/stop")
        assert r.status_code == 200
        assert r.json()["status"]["is_active"] is False

    def test_replay_mode(self):
        r = client.post("/api/scenario/start", json={"mode": "replay"})
        assert r.status_code == 200
        data = r.json()
        assert "REPLAY" in data["display_label"]
        assert "not live" in data["display_label"]

        r = client.post("/api/scenario/step")
        assert r.status_code == 200
        step = r.json()
        # All records should be labeled replay
        for rec in step["records"]:
            assert rec["source"] == "replay"
            assert rec["event_name"] is not None
            assert rec["replayed_at"] is not None

        client.post("/api/scenario/stop")

    def test_live_mode(self):
        r = client.post("/api/scenario/start", json={"mode": "live"})
        assert r.status_code == 409
        assert "cannot be started" in r.json()["detail"]

    def test_scenario_records_never_have_truth(self):
        """Observable records from scenario API must never contain ground truth."""
        r = client.post("/api/scenario/start", json={
            "mode": "scenario", "seed": 99, "duration_hours": 24,
            "peak_rain_mm_h": 35.0
        })
        assert r.status_code == 200

        all_records = []
        for _ in range(24):  # step through all hours
            r = client.post("/api/scenario/step")
            if r.status_code != 200:
                break
            all_records.extend(r.json()["records"])

        for rec in all_records:
            assert rec["source"] == "simulated"
            assert "ground_truth" not in str(rec.get("payload", {}))

        client.post("/api/scenario/stop")

    def test_same_seed_same_results(self):
        """Same seed + same params → identical first step records."""
        results = []
        for _ in range(2):
            client.post("/api/scenario/start", json={
                "mode": "scenario", "seed": 123, "duration_hours": 6
            })
            r = client.post("/api/scenario/step")
            results.append(r.json())
            client.post("/api/scenario/stop")

        r1, r2 = results
        assert r1["num_records"] == r2["num_records"]
        assert r1["record_kinds"] == r2["record_kinds"]

    def test_existing_endpoints_still_work(self):
        """Regression: Phase 1 endpoints unaffected."""
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/config").status_code == 200
        assert client.get("/api/geography/summary").status_code == 200

    def test_synthetic_exercise_pune_report_decreases_confidence_and_priority(self, tmp_path):
        """During a synthetic exercise, sending a report from Pune updates the warning engine,
        detects the location mismatch (~2,200 km from Assam), drops confidence to low,
        and decreases the settlement's priority score.
        """
        app = create_app(operations_path=tmp_path / "test_ops.sqlite3")
        c = TestClient(app)
        # 1. Start a synthetic scenario
        c.post("/api/scenario/start", json={
            "mode": "scenario", "seed": 42, "duration_hours": 12, "peak_rain_mm_h": 30.0
        })

        # 2. Advance 4 hours so rain builds up and warnings exist
        for _ in range(4):
            c.post("/api/scenario/step")

        # 3. Get scenario snapshot before report
        snap_before = c.get("/api/scenario/snapshot")
        assert snap_before.status_code == 200
        cards_before = {card["settlement_id"]: card for card in snap_before.json()["assessments"]}
        
        # Pick an affected settlement
        affected = [card for card in snap_before.json()["assessments"] if (card.get("score") or 0) > 20]
        target_settlement = affected[0] if affected else snap_before.json()["assessments"][0]
        target_id = target_settlement["settlement_id"]
        score_before = target_settlement["score"]
        rank_before = target_settlement["rank"]
        count_before = target_settlement["reports"]["count"]

        # 4. User sends a report from Pune (lat: 18.65, lon: 73.76) for this settlement
        rep_payload = {
            "device_id": "PUNE-DEVICE-USER-01",
            "sender_name": "Paritosh (from Pune)",
            "incident_type": "rescue_sos",
            "settlement_id": target_id,
            "latitude": 18.6513,
            "longitude": 73.7621,
            "people_affected": 2,
            "description": "Urgent assistance needed, water entering homes",
        }
        rep_res = c.post("/api/reports?context=live", json=rep_payload)
        assert rep_res.status_code == 200

        # 5. Fetch scenario snapshot again
        snap_after = c.get("/api/scenario/snapshot")
        assert snap_after.status_code == 200
        cards_after = {card["settlement_id"]: card for card in snap_after.json()["assessments"]}
        target_after = cards_after[target_id]

        # 6. Verify:
        # - The report was ingested by the warning priority engine
        assert target_after["reports"]["count"] == count_before + 1
        assert target_after["reports"]["location_mismatch"] is True
        assert target_after["reports"]["mismatch_distance_km"] > 1000.0
        assert "location mismatch" in target_after["reports"]["message"].lower()

        # - Confidence score dropped to 'low'
        assert target_after["confidence"] == "low"
        assert "location mismatch" in target_after["confidence_reason"].lower()

        # - Priority score decreased slightly due to the location mismatch
        if score_before:
            assert target_after["score"] < score_before
            assert round(score_before - target_after["score"], 1) == 6.0

        # Clean up
        c.post("/api/scenario/stop")
