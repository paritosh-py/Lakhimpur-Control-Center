"""Unit tests for Citizen Reports, Gemini AI triage, and repeat-device tracking."""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.services.reports import ReportStore, GeminiTriageService


@pytest.fixture
def test_app(tmp_path):
    db_path = tmp_path / "test_ops.sqlite3"
    app = create_app(operations_path=db_path)
    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


def test_gemini_fallback_triage_critical():
    triage = GeminiTriageService(api_key="")
    data = {
        "incident_type": "rescue_sos",
        "description": "Family trapped on roof as water reaches 1st floor!",
        "conditions": ["trapped", "immediatedanger"],
        "people_affected": 5,
        "water_depth_cm": 150,
        "water_trend": "rising",
    }
    result = triage.fallback_triage(data)
    assert result["urgency"] == "CRITICAL"
    assert result["urgency_score"] >= 85
    assert "rescue" in result["primary_hazard"]
    assert result["triage_source"] == "rule_heuristic"


def test_gemini_fallback_triage_road_closure():
    triage = GeminiTriageService(api_key="")
    data = {
        "incident_type": "road_closure",
        "description": "Bridge washed out, road completely blocked near village turn",
        "road_status": "blocked",
    }
    result = triage.fallback_triage(data)
    assert result["urgency"] in ["HIGH", "CRITICAL"]
    assert result["road_closure_asserted"] is True


def test_report_store_crud(tmp_path):
    store = ReportStore(tmp_path / "reports.sqlite3")
    assert store.count_prior_device_reports("live", "DEV-001") == 0

    rep1 = store.save_report(
        {
            "device_id": "DEV-001",
            "incident_type": "general",
            "description": "Water logging in courtyard",
            "people_affected": 2,
        },
        triage={"urgency": "LOW", "urgency_score": 30, "summary": "Courtyard water logging"},
        context="live",
    )
    assert rep1["id"].startswith("REP-")
    assert rep1["device_total_reports"] == 1
    assert rep1["is_repeat_device"] is False

    # Second report from same device
    assert store.count_prior_device_reports("live", "DEV-001") == 1
    rep2 = store.save_report(
        {
            "device_id": "DEV-001",
            "incident_type": "flood_rising",
            "description": "Water now entering house rapidly!",
            "people_affected": 4,
        },
        triage={"urgency": "HIGH", "urgency_score": 75, "summary": "Rapid water ingress"},
        context="live",
    )
    assert rep2["device_total_reports"] == 2
    assert rep2["is_repeat_device"] is True

    # Check stats
    stats = store.stats(context="live")
    assert stats["total"] == 2
    assert stats["unique_devices"] == 1
    assert stats["repeat_reports"] == 1

    # Check device history
    history = store.get_device_history("DEV-001", context="live")
    assert len(history) == 2

    # Update status
    updated = store.update_status(rep1["id"], "verified", "Confirmed by ward member", context="live")
    assert updated["status"] == "verified"


def test_api_report_intake_and_settlement_snapping(client):
    # Post report with coordinates near Lakhimpur town
    payload = {
        "device_id": "MOBILE-APP-99",
        "sender_name": "Rupesh Saikia",
        "incident_type": "road_closure",
        "latitude": 27.23,
        "longitude": 94.10,
        "people_affected": 3,
        "road_status": "blocked",
        "description": "Main road under 3 feet water, tree fallen across lane",
    }
    resp = client.post("/api/reports?context=live", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["device_id"] == "MOBILE-APP-99"
    assert data["settlement_id"] is not None  # Snapped to nearest settlement
    assert data["settlement_name"] is not None
    assert data["is_repeat_device"] is False

    # Submit second report from same device
    payload2 = {
        "device_id": "MOBILE-APP-99",
        "incident_type": "rescue_sos",
        "description": "Now children and elderly are stranded",
        "latitude": 27.23,
        "longitude": 94.10,
    }
    resp2 = client.post("/api/reports?context=live", json=payload2)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["device_total_reports"] == 2
    assert data2["is_repeat_device"] is True

    # Get list
    resp_list = client.get("/api/reports?context=live")
    assert resp_list.status_code == 200
    list_data = resp_list.json()
    assert list_data["count"] == 2

    # Get stats
    resp_stats = client.get("/api/reports/stats?context=live")
    assert resp_stats.status_code == 200
    assert resp_stats.json()["total"] == 2
    assert resp_stats.json()["repeat_reports"] == 1
    assert resp_stats.json()["active"] == 2
    assert resp_stats.json()["closed"] == 0

    # Close the first report
    rep_id = data["id"]
    resp_close = client.post(f"/api/reports/{rep_id}/status?context=live", json={"status": "closed"})
    assert resp_close.status_code == 200
    assert resp_close.json()["status"] == "closed"

    # Verify updated stats reflect closed request
    resp_stats2 = client.get("/api/reports/stats?context=live")
    assert resp_stats2.status_code == 200
    assert resp_stats2.json()["closed"] == 1
    assert resp_stats2.json()["active"] == 1

    # Verify single report lookup (used by Citizen App polling)
    resp_single = client.get(f"/api/reports/{rep_id}?context=live")
    assert resp_single.status_code == 200
    assert resp_single.json()["id"] == rep_id
    assert resp_single.json()["status"] == "closed"
