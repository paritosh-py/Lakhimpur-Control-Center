from copy import deepcopy

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.api import road_predictions as model


def payload(eta=60):
    return {"model_version": "lightgbm_v2_candidate", "mode": "snapshot_demo", "eta_minutes": eta,
            "road_count": 1, "predictions": [{"road_id": "osm-1092487157-27-28", "probability_unusable": .000641,
            "risk_level": "LOW", "road_status": "unknown", "data_quality_status": "CHECK_REQUIRED"}]}


def setup(monkeypatch, value=None, failure=None):
    seen = []
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def get(self, url, params):
            seen.append((url, params))
            if failure: raise failure
            return httpx.Response(200, json=value, request=httpx.Request("GET", url))
    monkeypatch.setattr(model.httpx, "AsyncClient", Client)
    return TestClient(create_app()), seen


@pytest.mark.parametrize("eta", [30, 60, 120])
def test_join_provenance_and_no_status_mutation(monkeypatch, eta):
    client, seen = setup(monkeypatch, payload(eta))
    response = client.get(f"/api/ml/roads?eta={eta}")
    assert response.status_code == 200
    body = response.json()
    assert body["eta_minutes"] == eta and seen[0][1] == {"eta": eta}
    assert body["mode"] == "snapshot_demo" and body["source"] == "simulated"
    assert body["matched_count"] == 1 and body["road_count"] == 800
    assert response.headers["cache-control"] == "no-store"
    road = next(r for r in body["roads"] if r["prediction"])
    assert road["prediction"]["probability_unusable"] == .000641
    assert road["recorded_road_status"] == "unknown"
    assert len([r for r in body["roads"] if r["prediction"] is None]) == 799


@pytest.mark.parametrize("eta", [0, 31, 121, "junk"])
def test_invalid_eta_never_calls_model(monkeypatch, eta):
    client, seen = setup(monkeypatch, payload())
    assert client.get(f"/api/ml/roads?eta={eta}").status_code == 422
    assert not seen


@pytest.mark.parametrize("fault", ["nan", "negative", "missing", "duplicate", "count", "eta", "mode", "band"])
def test_bad_model_response_is_explicit(monkeypatch, fault):
    value = deepcopy(payload())
    p = value["predictions"][0]
    if fault == "nan": p["probability_unusable"] = "NaN"
    if fault == "negative": p["probability_unusable"] = -.1
    if fault == "missing": del p["data_quality_status"]
    if fault == "duplicate": value["predictions"].append(deepcopy(p)); value["road_count"] = 2
    if fault == "count": value["road_count"] = 800
    if fault == "eta": value["eta_minutes"] = 30
    if fault == "mode": value["mode"] = "live"
    if fault == "band": p["risk_level"] = "HIGH"
    client, _ = setup(monkeypatch, value)
    response = client.get("/api/ml/roads")
    assert response.status_code == 502
    assert "substituted" in response.json()["detail"]


def test_unavailable_then_recovery_and_unknown_id(monkeypatch):
    client, _ = setup(monkeypatch, failure=httpx.ConnectError("offline"))
    assert client.get("/api/ml/roads").status_code == 503
    value = payload(); value["predictions"][0]["road_id"] = "outside-study"
    client, _ = setup(monkeypatch, value)
    body = client.get("/api/ml/roads").json()
    assert body["matched_count"] == 0 and body["unmatched_prediction_count"] == 1
    assert all(r["prediction"] is None for r in body["roads"])


@pytest.mark.parametrize("probability,band",[(.3999,"LOW"),(.4,"MODERATE"),(.6999,"MODERATE"),(.7,"HIGH"),(1.,"HIGH")])
def test_band_boundaries(monkeypatch, probability, band):
    value = payload(); value["predictions"][0].update(probability_unusable=probability,risk_level=band)
    client, _ = setup(monkeypatch, value)
    assert client.get("/api/ml/roads").status_code == 200
