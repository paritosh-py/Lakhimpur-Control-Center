"""Verify acquired-file hashes and report coverage without any network access."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine.clock import LiveClock

raw, out = ROOT / "data/raw", ROOT / "data/processed"
sources = []
for path in sorted(raw.glob("*.metadata.json")):
    meta = json.loads(path.read_text(encoding="utf-8"))
    data = raw / meta["file"]
    actual = hashlib.sha256(data.read_bytes()).hexdigest()
    if actual != meta["sha256"]:
        raise ValueError(f"Source checksum mismatch: {data.name}")
    sources.append(meta)
derived = []
for path in sorted(out.iterdir()):
    if path.suffix in {".json", ".geojson"} and path.name not in {"source_manifest.json", "validation.json"}:
        derived.append({"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
manifest = {"generated_at": LiveClock().now().isoformat(), "sources": sources, "derived_files": derived}
(out / "source_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
summary = json.loads((out / "geography_summary.json").read_text(encoding="utf-8"))
result = {"validated_at": LiveClock().now().isoformat(), "source_hashes_verified": len(sources),
          "counts": summary["counts"], "terrain_missing_samples": summary["terrain"]["missing_samples"],
          "connected_components": summary["connected_components"], "weather": {}}
for mode in ("live", "historical"):
    data = json.loads((out / f"weather_settlements_{mode}.json").read_text(encoding="utf-8"))
    result["weather"][mode] = {"settlements": data["settlement_count"], "grid_cells": data["unique_grid_cells"],
        "hourly_records": sum(len(r["records"]) for r in data["locations"]),
        "missing_values": sum(r["missing_values"] for r in data["locations"])}
(out / "validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
