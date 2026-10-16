"""Current model weather, isolated from replay and the legacy warning engine."""
from __future__ import annotations

import json
import math
import ssl
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock

import httpx
import truststore

from engine.clock import Clock, LiveClock
from engine.config import ROOT

FIELDS = {
    "temperature_2m": "°C", "relative_humidity_2m": "%", "precipitation": "mm",
    "rain": "mm", "showers": "mm", "weather_code": "wmo code",
    "cloud_cover": "%", "wind_speed_10m": "km/h", "is_day": "",
}


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def condition(code, is_day) -> str:
    if code == 0:
        return "Sunny" if is_day == 1 else "Clear sky" if is_day == 0 else "Clear sky (daylight unknown)"
    names = {1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Rime fog",
             51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle", 56: "Freezing drizzle",
             57: "Freezing drizzle", 61: "Light rain", 63: "Rain", 65: "Heavy rain",
             66: "Freezing rain", 67: "Heavy freezing rain", 71: "Light snow", 73: "Snow",
             75: "Heavy snow", 77: "Snow grains", 80: "Rain showers", 81: "Rain showers",
             82: "Heavy rain showers", 85: "Snow showers", 86: "Heavy snow showers",
             95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail"}
    return names.get(code, "Conditions unavailable")


class LiveWeatherService:
    refresh_seconds = 600
    retry_seconds = 60
    stale_seconds = 3600

    def __init__(self, clock: Clock | None = None, fetcher=None, cache_path: Path | None = None):
        self.clock = clock or LiveClock()
        self.fetcher = fetcher or self._fetch
        self.cache_path = cache_path or ROOT / "data/runtime/live_weather.json"
        self.features = json.loads((ROOT / "data/processed/settlements.geojson").read_text(encoding="utf-8"))["features"]
        self.lock = Lock()
        self.snapshot = None
        self.error = None
        self.last_attempt = None
        self.next_attempt = None
        try:
            cached = json.loads(self.cache_path.read_text(encoding="utf-8"))
            if cached.get("schema_version") == 1 and cached.get("settlement_ids") == self.ids:
                if timestamp(cached["retrieved_at"]) > self.clock.now():
                    raise ValueError("Cache timestamp is in the future")
                if [r["settlement_id"] for r in cached["rows"]] != self.ids:
                    raise ValueError("Cache coverage mismatch")
                for row in cached["rows"]:
                    history = row.get('hourly_history', [])
                    if not isinstance(history, list): raise ValueError('Invalid rainfall cache')
                    for h in history:
                        if timestamp(h['valid_at']) > timestamp(cached['retrieved_at']):
                            raise ValueError('Future rainfall in cache')
                        amount = h['precipitation_mm']
                        if amount is not None and (not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount < 0):
                            raise ValueError('Invalid rainfall cache value')
                    if set(row["values"]) != set(FIELDS):
                        raise ValueError("Cache schema mismatch")
                    if row["valid_at"]:
                        timestamp(row["valid_at"])
                    for value in row["values"].values():
                        if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value)):
                            raise ValueError("Invalid cache value")
                self.snapshot = cached
        except (OSError, ValueError, KeyError, TypeError):
            pass  # A missing/corrupt cache is never a current observation.

    @property
    def ids(self):
        return [f["properties"]["id"] for f in self.features]

    def _fetch(self, params):
        with httpx.Client(verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT), timeout=20) as client:
            response = client.get("https://api.open-meteo.com/v1/forecast", params=params)
            response.raise_for_status()
            return response.json()

    def _normalize(self, payload, now):
        if not isinstance(payload, list) or len(payload) != len(self.features):
            raise ValueError("Provider returned incomplete settlement coverage")
        rows = []
        for index, (feature, item) in enumerate(zip(self.features, payload, strict=True)):
            if item.get("location_id", index) != index or item.get("utc_offset_seconds") != 0:
                raise ValueError("Provider location order or timezone mismatch")
            lon, lat = feature["geometry"]["coordinates"]
            if abs(item["latitude"] - lat) > 0.5 or abs(item["longitude"] - lon) > 0.5:
                raise ValueError("Provider grid is outside the requested study area")
            current = item.get("current") or {}
            units = item.get("current_units") or {}
            values = {}
            for field, unit in FIELDS.items():
                value = current.get(field)
                if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value)):
                    raise ValueError("Non-numeric weather value")
                if value is not None and units.get(field) != unit:
                    raise ValueError(f"Unexpected unit for {field}")
                if value is not None and field != "temperature_2m" and value < 0:
                    raise ValueError("Negative weather value")
                if value is not None and field in {"relative_humidity_2m", "cloud_cover"} and value > 100:
                    raise ValueError("Invalid percentage")
                values[field] = value
            valid = timestamp(current["time"]) if current.get("time") else None
            if valid and valid > now + timedelta(minutes=15):
                raise ValueError("Provider returned a future current-condition time")
            interval = current.get("interval")
            if interval is not None and (not isinstance(interval, int) or not 0 < interval <= 3600):
                raise ValueError("Unexpected current-condition interval")
            hourly = item.get('hourly') or {}
            history = []
            if hourly:
                times, amounts = hourly.get('time', []), hourly.get('precipitation', [])
                if len(times) != len(amounts) or item.get('hourly_units', {}).get('precipitation') != 'mm':
                    raise ValueError('Invalid hourly rainfall coverage/units')
                for t, amount in zip(times, amounts, strict=True):
                    when = timestamp(t)
                    if amount is not None and (not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount < 0):
                        raise ValueError('Invalid hourly rainfall')
                    # Future hourly forecasts are not observations for accumulation.
                    if when <= now:
                        history.append({'valid_at': when.isoformat(), 'precipitation_mm': amount})
            rows.append({"settlement_id": feature["properties"]["id"], "name": feature["properties"]["name"],
                         "latitude": lat, "longitude": lon, "grid_latitude": item["latitude"],
                         "grid_longitude": item["longitude"], "valid_at": valid.isoformat() if valid else None,
                         "interval_seconds": interval, "values": values, 'hourly_history': history})
        return {"schema_version": 1, "settlement_ids": self.ids, "retrieved_at": now.isoformat(), "rows": rows}

    def get(self):
        with self.lock:
            now = self.clock.now()
            if self.next_attempt is None or now >= self.next_attempt:
                self.last_attempt = now
                try:
                    params = {"latitude": ",".join(str(f["geometry"]["coordinates"][1]) for f in self.features),
                              "longitude": ",".join(str(f["geometry"]["coordinates"][0]) for f in self.features),
                              "current": ",".join(FIELDS), "timezone": "UTC", "forecast_days": 1,
                              "hourly": "precipitation", "past_days": 3,
                              "wind_speed_unit": "kmh", "temperature_unit": "celsius", "precipitation_unit": "mm"}
                    snapshot = self._normalize(self.fetcher(params), self.clock.now())
                    self.snapshot = snapshot
                    self.error = None
                    self.next_attempt = self.clock.now() + timedelta(seconds=self.refresh_seconds)
                    try:
                        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
                        pending = self.cache_path.with_suffix(".tmp")
                        pending.write_text(json.dumps(snapshot, ensure_ascii=False, allow_nan=False), encoding="utf-8")
                        pending.replace(self.cache_path)
                    except OSError:
                        self.error = "Current data loaded, but local cache could not be saved."
                except (httpx.HTTPError, OSError, ValueError, KeyError, TypeError) as exc:
                    self.error = ("Weather provider is unavailable or returned invalid data. "
                                  "Showing the last successful fetch, if available.")
                    self.next_attempt = self.clock.now() + timedelta(seconds=self.retry_seconds)
            return self._view(self.clock.now())

    def _view(self, now):
        rows = {r["settlement_id"]: r for r in self.snapshot["rows"]} if self.snapshot else {}
        retrieved = timestamp(self.snapshot["retrieved_at"]) if self.snapshot else None
        result = []
        for feature in self.features:
            ident = feature["properties"]["id"]
            row = dict(rows.get(ident) or {"settlement_id": ident, "name": feature["properties"]["name"],
                        "latitude": feature["geometry"]["coordinates"][1], "longitude": feature["geometry"]["coordinates"][0],
                        "grid_latitude": None, "grid_longitude": None, "valid_at": None,
                        "interval_seconds": None, "values": {key: None for key in FIELDS}})
            valid = timestamp(row["valid_at"]) if row["valid_at"] else None
            age = max(0, (now - valid).total_seconds()) if valid else None
            usable = valid is not None and any(v is not None for v in row["values"].values())
            stale = usable and (self.error is not None or age > self.stale_seconds or
                                retrieved is None or (now - retrieved).total_seconds() > self.stale_seconds)
            status = "unavailable" if not usable else "stale" if stale else "current"
            rain, showers = row["values"]["rain"], row["values"]["showers"]
            rain_status = "unknown" if status != "current" or rain is None or showers is None else (
                "raining" if rain + showers > 0 else "no_rain")
            row.update(status=status, age_seconds=age, rain_status=rain_status,
                       condition=condition(row["values"]["weather_code"], row["values"]["is_day"]),
                       missing_fields=[k for k, v in row["values"].items() if v is None])
            result.append(row)
        return {"mode": "live", "district": "Lakhimpur, Assam", "provider": "Open-Meteo · Best Match",
                "measurement": "model_estimate", "source_url": "https://open-meteo.com/en/docs",
                "checked_at": now.isoformat(), "retrieved_at": retrieved.isoformat() if retrieved else None,
                "last_attempt_at": self.last_attempt.isoformat() if self.last_attempt else None,
                "next_refresh_at": self.next_attempt.isoformat() if self.next_attempt else None,
                "refresh_seconds": self.refresh_seconds, "error": self.error, "settlements": result,
                "grid_cells": len({(r["grid_latitude"], r["grid_longitude"]) for r in result if r["grid_latitude"] is not None}),
                "counts": {key: sum(r["status"] == key for r in result) for key in ("current", "stale", "unavailable")},
                "raining_count": sum(r["rain_status"] == "raining" for r in result)}
