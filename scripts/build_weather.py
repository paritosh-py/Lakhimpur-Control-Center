import json
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine.ingest.weather import normalize_weather

for raw_name, out_name, historical in (("weather_live.json", "weather_live.json", False),
                                       ("weather_historical_2024.json", "weather_reanalysis_2024.json", True)):
    raw = ROOT / "data/raw" / raw_name
    payload = json.loads(raw.read_text())
    metadata = json.loads(raw.with_name(raw.name + ".metadata.json").read_text())
    normalized = normalize_weather(payload, metadata, historical=historical)
    (ROOT / "data/processed" / out_name).write_text(json.dumps(normalized, indent=2, ensure_ascii=False), encoding="utf-8")
    print(out_name, len(normalized["records"]), "hours; missing", normalized["missing_values"])

places = json.loads((ROOT / "data/processed/settlements.geojson").read_text(encoding="utf-8"))["features"]
by_coordinate = {tuple(f["geometry"]["coordinates"]): f["properties"]["id"] for f in places}
for mode, historical in [("live", False), ("historical", True)]:
    raw = ROOT / "data/raw" / f"weather_settlements_{mode}.json"
    payloads = json.loads(raw.read_text(encoding="utf-8"))
    metadata = json.loads(raw.with_name(raw.name + ".metadata.json").read_text(encoding="utf-8"))
    params = parse_qs(urlparse(metadata["url"]).query)
    requested = list(zip(map(float, params["longitude"][0].split(",")), map(float, params["latitude"][0].split(","))))
    if len(payloads) != len(requested) or not set(by_coordinate).issubset(set(requested)):
        raise ValueError("Cached weather request does not match selected settlements")
    records = []
    for index, payload in enumerate(payloads):
        if payload.get("location_id", index) != index:
            raise ValueError("Weather location order mismatch")
        if requested[index] not in by_coordinate:
            continue  # Previously acquired point was excluded by later source QA.
        normalized = normalize_weather(payload, metadata, historical=historical)
        normalized["settlement_id"] = by_coordinate[requested[index]]
        normalized["requested_longitude"], normalized["requested_latitude"] = requested[index]
        records.append(normalized)
    result = {"source": "replay" if historical else "live", "retrieved_at": metadata["retrieved_at"],
              "settlement_count": len(records), "unique_grid_cells": len({(r["latitude"], r["longitude"]) for r in records}),
              "locations": records}
    (ROOT / "data/processed" / f"weather_settlements_{mode}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(mode, len(records), "settlements;", result["unique_grid_cells"], "unique weather grid cells")
