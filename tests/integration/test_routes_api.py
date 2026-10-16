"""Integration tests for the routing and navigation API endpoints."""
from fastapi.testclient import TestClient
import pytest

from backend.app.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_basecamp_api_endpoint(client):
    res = client.get("/api/geography/basecamp")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Borimuri Basecamp"
    assert data["plus_code"] == "748G+M62"
    assert "graph_node_id" in data
    assert abs(data["latitude"] - 27.2666) < 0.001


def test_routes_plan_endpoint(client):
    geo_res = client.get("/api/geography/settlements")
    assert geo_res.status_code == 200
    settlement_id = geo_res.json()["features"][0]["properties"]["id"]

    res = client.get(f"/api/routes/plan?settlement_id={settlement_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["basecamp"]["name"] == "Borimuri Basecamp"
    assert data["settlement"]["id"] == settlement_id
    assert "mission_summary" in data
    assert data["mission_summary"]["total_distance_km"] > 0
    assert "recommended" in data["leg1_routes"]
    assert len(data["navigation_steps"]) > 0


def test_routes_plan_invalid_settlement(client):
    res = client.get("/api/routes/plan?settlement_id=nonexistent-settlement-id")
    assert res.status_code == 404


def test_routes_active_endpoint(client):
    res = client.get("/api/routes/active")
    assert res.status_code == 200
    data = res.json()
    assert "has_active_assignment" in data
    assert "basecamp" in data or "settlements" in data
