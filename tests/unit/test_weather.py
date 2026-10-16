import pytest
from engine.ingest.weather import normalize_weather


def sample():
    return {"latitude":27.2, "longitude":94.1, "utc_offset_seconds":0,
            "hourly_units":{"precipitation":"mm"},
            "hourly":{"time":["2024-07-02T00:00", "2024-07-02T01:00"], "precipitation":[0, None]}}


def test_historical_provenance_never_claims_as_issued_forecasts():
    result = normalize_weather(sample(), {"retrieved_at":"2026-10-10T10:00:00+00:00"}, historical=True)
    assert result["source"] == "replay"
    assert result["missing_values"] == 1
    for row in result["records"]:
        assert row["replayed_at"].startswith("2026") and row["event_time"].startswith("2024")
        assert row["original_available_at"] is None
        assert row["available_at"].startswith("2026")
    assert result["records"][1]["precipitation_mm"] is None


@pytest.mark.parametrize("mutation", ["negative", "units", "length", "gap"])
def test_invalid_weather_rejected(mutation):
    data = sample()
    if mutation == "negative": data["hourly"]["precipitation"][0] = -1
    if mutation == "units": data["hourly_units"]["precipitation"] = "inch"
    if mutation == "length": data["hourly"]["precipitation"].pop()
    if mutation == "gap": data["hourly"]["time"][1] = "2024-07-02T02:00"
    with pytest.raises(ValueError):
        normalize_weather(data, {"retrieved_at":"2026-10-10T10:00:00+00:00"}, historical=False)


def test_forecast_snapshot_never_fabricates_issue_time():
    result = normalize_weather(sample(), {"retrieved_at":"2024-07-01T10:00:00+00:00"}, historical=False)
    row = result["records"][0]
    assert row["measurement"] == "forecast"
    assert row["original_issued_at"] is None
    assert row["event_time"] == row["available_at"]
    assert row["valid_at"] > row["available_at"]
