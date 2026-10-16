"""Generate reproducible synthetic flood scenarios for Phase 2 (Task 4 & 5).

Generates 40 reproducible events split deterministically by event ID:
  - train (60%, 24 events)
  - calibration (15%, 6 events)
  - held_out (25%, 10 events)

Observable records and ground truth are written to separate files so later
feature builders and models can never leak future truth.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.config import ROOT as CONFIG_ROOT
from data.generators.flood_scenario import (
    generate_event_batch,
    load_graph,
    load_settlements,
    load_shelters,
    save_events,
    split_events,
)


def main() -> None:
    processed_dir = CONFIG_ROOT / "data" / "processed"
    replays_dir = CONFIG_ROOT / "data" / "replays" / "synthetic"
    replays_dir.mkdir(parents=True, exist_ok=True)

    print("Loading geography datasets...")
    graph = load_graph(processed_dir / "graph.json")
    settlements = load_settlements(processed_dir / "settlements.geojson")
    shelters = load_shelters(processed_dir / "shelters.geojson")

    print(f"Loaded {len(graph['edges'])} edges, {len(settlements)} settlements, {len(shelters)} shelters.")
    print("Generating batch of 40 reproducible events (base seed: 42)...")
    events = generate_event_batch(
        edges=graph["edges"],
        settlements=settlements,
        shelters=shelters,
        num_events=40,
        base_seed=42,
    )

    splits = split_events(events)
    print(f"Splits: train={len(splits['train'])}, calibration={len(splits['calibration'])}, held_out={len(splits['held_out'])}")

    manifest_file = save_events(events, replays_dir, include_truth=True)

    # Save split manifest
    split_manifest = {
        "train": [e.config.event_id for e in splits["train"]],
        "calibration": [e.config.event_id for e in splits["calibration"]],
        "held_out": [e.config.event_id for e in splits["held_out"]],
    }
    split_file = replays_dir / "splits.json"
    split_file.write_text(json.dumps(split_manifest, indent=2), encoding="utf-8")

    print(f"Saved {len(events)} events to {replays_dir}")
    print(f"Manifest: {manifest_file}")
    print(f"Splits saved to {split_file}")


if __name__ == "__main__":
    main()
