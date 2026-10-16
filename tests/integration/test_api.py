from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.app.main import create_app
from engine.clock import ScenarioClock

NOW = datetime(2026, 10, 10, tzinfo=timezone.utc)
client = TestClient(create_app(ScenarioClock(NOW)))


def test_health_uses_injected_clock_and_config():
    assert client.get("/api/health").json()["time"] == "2026-10-10T00:00:00+00:00"
    config = client.get("/api/config").json()
    assert (config["district"], config["state"], config["hazard"]) == ("Lakhimpur", "Assam", "flood")


def test_replay_validation_roundtrip_and_missing_label_metadata():
    event = {"id": "e1", "run_id": "replay-1", "kind": "report", "entity_id": "r1",
             "provenance": {"source": "replay", "provider": "fixture", "event_name": "Flood 2024",
                            "event_time": "2024-07-02T00:00:00Z", "available_at": "2024-07-02T00:00:00Z",
                            "recorded_at": NOW.isoformat(), "replayed_at": NOW.isoformat()}}
    response = client.post("/api/events/validate", json=event)
    assert response.status_code == 200
    assert response.json()["label"].startswith("REPLAY:")
    assert response.json()["event"]["provenance"]["event_time"].startswith("2024-07-02")
    del event["provenance"]["replayed_at"]
    assert client.post("/api/events/validate", json=event).status_code == 422


def test_no_unimplemented_ingestion_route():
    assert client.post("/api/nonexistent_intake", json={}).status_code == 404
    assert client.get("/openapi.json").status_code == 200
