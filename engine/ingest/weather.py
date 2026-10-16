"""Normalize cached weather without inventing original forecast issuance times."""
from datetime import datetime, timezone


def normalize_weather(payload: dict, metadata: dict, *, historical: bool) -> dict:
    hourly = payload["hourly"]
    if payload["hourly_units"]["precipitation"] != "mm" or payload.get("utc_offset_seconds") != 0:
        raise ValueError("Expected millimetres and UTC weather data")
    times, rain = hourly["time"], hourly["precipitation"]
    if len(times) != len(rain) or not times:
        raise ValueError("Missing or mismatched weather series")
    fetched = datetime.fromisoformat(metadata["retrieved_at"])
    rows = []
    previous = None
    for text, value in zip(times, rain):
        valid = datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
        if previous is not None and (valid - previous).total_seconds() != 3600:
            raise ValueError("Weather timestamps must be consecutive hourly intervals")
        if value is not None and (not isinstance(value, (int, float)) or not 0 <= value < float("inf")):
            raise ValueError("Invalid precipitation")
        rows.append({"valid_at": valid.isoformat(), "precipitation_mm": value,
            "interval_minutes": 60, "available_at": fetched.isoformat(),
            "original_issued_at": None, "original_available_at": None,
            "measurement": "reanalysis" if historical else "forecast" if valid > fetched else "model_estimate",
            "source": "replay" if historical else "live",
            "event_time": fetched.isoformat() if valid > fetched else valid.isoformat(),
            "event_time_basis": "retrieval of forecast snapshot; original issue time unknown" if valid > fetched else "value validity time",
            "recorded_at": fetched.isoformat(),
            **({"event_name": "Assam flood context, June–July 2024", "replayed_at": fetched.isoformat()} if historical else {})})
        previous = valid
    return {"provider": "Open-Meteo / ERA5" if historical else "Open-Meteo / GFS seamless",
            "latitude": payload["latitude"], "longitude": payload["longitude"],
            "retrieved_at": fetched.isoformat(), "source": "replay" if historical else "live",
            "label": "HISTORICAL REANALYSIS — June–July 2024; not live, not an issued forecast" if historical else "LIVE-SOURCE SNAPSHOT — model-derived weather",
            "original_availability_known": False,
            "decision_time_use": "Do not use as 2024 decision-time forecasts" if historical else "Available only from retrieval timestamp",
            "missing_values": sum(row["precipitation_mm"] is None for row in rows), "records": rows}
