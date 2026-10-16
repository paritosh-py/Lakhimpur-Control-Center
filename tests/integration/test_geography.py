import json
from pathlib import Path

from fastapi.testclient import TestClient
import networkx as nx
import pytest
from shapely.geometry import shape

from backend.app.main import create_app
from backend.app.api.geography import load_dataset
from fastapi import HTTPException

DATA = Path(__file__).resolve().parents[2] / "data/processed"


def read(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def test_acquired_graph_is_bounded_connected_and_inside_district():
    boundary = shape(read("boundary.geojson")["features"][0]["geometry"])
    roads = read("roads.geojson")["features"]
    graph = nx.MultiGraph()
    assert 300 <= len(roads) <= 1000
    assert len({f["properties"]["id"] for f in roads}) == len(roads)
    for road in roads:
        p = road["properties"]
        assert boundary.covers(shape(road["geometry"]))
        assert p["length_m"] > 0 and p["elevation_m"] is not None
        assert 0 <= p["slope_degrees"] < 90
        assert p["distance_to_river_m"] >= 0
        assert p["status"] == "unknown" and p["travel_minutes"] is None
        graph.add_edge(p["from_node"], p["to_node"])
    assert nx.is_connected(graph)
    assert set(graph.nodes) == {node["id"] for node in read("graph.json")["nodes"]}


def test_settlements_and_shelters_have_valid_links_and_honest_capacity():
    boundary = shape(read("boundary.geojson")["features"][0]["geometry"])
    segments = {r["properties"]["id"] for r in read("roads.geojson")["features"]}
    for filename, lower, upper in [("settlements.geojson",15,40), ("shelters.geojson",5,10)]:
        features = read(filename)["features"]
        assert lower <= len(features) <= upper
        for feature in features:
            p = feature["properties"]
            assert boundary.covers(shape(feature["geometry"]))
            assert p["nearest_segment_id"] in segments
            assert p["distance_to_road_m"] <= 1500
            assert p["access_verified"] is False
            assert p["provenance"]["recorded_at"]
            if filename == "shelters.geojson":
                assert p["current_capacity"] is None and p["occupied"] is None
                assert p["reference_year"] == 2025 and p["source_page"] == 48
                assert p["published_capacity"] > 0


def test_readonly_api_and_explicit_missing_data(tmp_path):
    client = TestClient(create_app())
    for path in ["/api/geography/summary", "/api/geography/roads", "/api/geography/shelters", "/api/sources", "/api/weather/live", "/api/weather/historical"]:
        assert client.get(path).status_code == 200
    assert client.get("/api/geography/secrets").status_code == 422
    with pytest.raises(HTTPException) as info:
        load_dataset("missing.json", tmp_path)
    assert info.value.status_code == 503
    assert client.post("/api/geography/roads", json={}).status_code == 405


def test_all_settlements_have_labeled_weather_without_missing_values():
    ids = {f["properties"]["id"] for f in read("settlements.geojson")["features"]}
    for mode, source, hours in [("live", "live", 240), ("historical", "replay", 264)]:
        data = read(f"weather_settlements_{mode}.json")
        assert {r["settlement_id"] for r in data["locations"]} == ids
        assert data["settlement_count"] == len(ids)
        for location in data["locations"]:
            assert location["source"] == source and location["missing_values"] == 0
            assert len(location["records"]) == hours
            for row in location["records"]:
                assert row["precipitation_mm"] >= 0
                assert row["source"] == source and row["original_available_at"] is None
                if source == "replay":
                    assert row["event_name"] and row["replayed_at"] and row["event_time"].startswith("2024")
