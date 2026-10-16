"""Extract real OSM entities from the dated regional PBF without remote queries."""
import json
from pathlib import Path

import osmium

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
BBOX = (93.85, 27.00, 94.35, 27.42)
EXCLUDED = {"footway", "path", "steps", "cycleway", "construction", "proposed", "pedestrian", "platform", "raceway"}


def inside(lon, lat):
    return BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]


class Extract(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.nodes = {}
        self.ways = []
        self.places = []

    def node(self, node):
        if node.location.valid() and inside(node.location.lon, node.location.lat):
            tags = dict(node.tags)
            if tags.get("place") in {"city", "town", "village", "hamlet"}:
                self.places.append({"id": node.id, "lon": node.location.lon, "lat": node.location.lat,
                                    "tags": tags, "timestamp": node.timestamp.isoformat()})

    def way(self, way):
        tags = dict(way.tags)
        road = tags.get("highway") and tags["highway"] not in EXCLUDED and tags.get("area") != "yes"
        water = tags.get("waterway") in {"river", "stream", "canal"}
        if not (road or water):
            return
        if road and (tags.get("access") in {"no", "private"} or tags.get("motor_vehicle") == "no"):
            return
        coords = [(n.ref, n.location.lon, n.location.lat) for n in way.nodes if n.location.valid()]
        if len(coords) != len(way.nodes) or not any(inside(lon, lat) for _, lon, lat in coords):
            return
        for ident, lon, lat in coords:
            self.nodes[str(ident)] = [lon, lat]
        self.ways.append({"id": way.id, "nodes": [n[0] for n in coords], "tags": tags,
                          "timestamp": way.timestamp.isoformat(), "kind": "road" if road else "water"})


if __name__ == "__main__":
    handler = Extract()
    handler.apply_file(str(RAW / "north-eastern-zone.osm.pbf"), locations=True, idx="flex_mem")
    output = {"bbox": BBOX, "nodes": handler.nodes, "ways": handler.ways, "places": handler.places}
    (RAW / "osm_extract.json").write_text(json.dumps(output), encoding="utf-8")
    print({"nodes": len(handler.nodes), "ways": len(handler.ways), "places": len(handler.places)})
