"""Build a bounded connected graph and reference layers from cached real sources."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
import zipfile

import networkx as nx
import numpy as np
from pyproj import Transformer
import rasterio
from rasterio.merge import merge
from shapely.geometry import LineString, Point, mapping, shape
from shapely.ops import unary_union
from shapely import transform as shapely_transform

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine.clock import LiveClock

RAW, OUT = ROOT / "data/raw", ROOT / "data/processed"
PROJECT = Transformer.from_crs(4326, 32646, always_xy=True).transform


def transform(project, geometry):
    return shapely_transform(geometry, project, interleaved=False)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def feature(geometry, properties):
    return {"type": "Feature", "geometry": mapping(geometry), "properties": properties}


def collection(features):
    return {"type": "FeatureCollection", "features": features}


def dms(values):
    deg, minute, second = values
    if not 0 <= minute < 60 or not 0 <= second < 60:
        raise ValueError("Malformed DMS coordinate")
    return deg + minute / 60 + second / 3600


class Terrain:
    def __init__(self):
        self.tiles = [rasterio.open(p) for p in sorted(RAW.glob("dem_n27_e*.tif"))]
        if not self.tiles:
            raise ValueError("Terrain tiles missing")
        self.grid, self.affine = merge(self.tiles, masked=True)

    def sample(self, lon, lat):
        row, col = rasterio.transform.rowcol(self.affine, lon, lat)
        if row < 1 or col < 1 or row >= self.grid.shape[1]-1 or col >= self.grid.shape[2]-1:
            return None, None
        grid = self.grid[0, row-1:row+2, col-1:col+2]
        if grid.shape != (3, 3) or np.ma.getmaskarray(grid).any():
            return None, None
        dx = abs(self.affine.a) * 111320 * math.cos(math.radians(lat))
        dy = abs(self.affine.e) * 111320
        gx = (float(grid[1, 2]) - float(grid[1, 0])) / (2 * dx)
        gy = (float(grid[2, 1]) - float(grid[0, 1])) / (2 * dy)
        return round(float(grid[1, 1]), 2), round(math.degrees(math.atan(math.hypot(gx, gy))), 3)

    def close(self):
        for tile in self.tiles:
            tile.close()


def main():
    OUT.mkdir(exist_ok=True)
    now = LiveClock().now().isoformat()
    osm = read(RAW / "osm_extract.json")
    with zipfile.ZipFile(RAW / "district_nwic_geojson.zip") as archive:
        boundaries = json.loads(archive.read("district_nwic.GeoJSON"))
    source_crs = boundaries["crs"]["properties"]["name"]
    matches = [f for f in boundaries["features"] if f["properties"].get("district") == "Lakhimpur"
               and f["properties"].get("state_name") == "Assam"]
    if len(matches) != 1:
        raise ValueError("District must resolve unambiguously in official NWIC dataset")
    boundary = transform(Transformer.from_crs(source_crs, 4326, always_xy=True).transform, shape(matches[0]["geometry"]))
    if not boundary.is_valid:
        raise ValueError("Invalid district polygon")
    osm_meta = read(RAW / "north-eastern-zone.osm.pbf.metadata.json")
    static = {"source": "live", "recorded_at": osm_meta["retrieved_at"],
              "provider": "OpenStreetMap / Geofabrik", "snapshot_date": "2026-10-09",
              "label": "GEOGRAPHIC SNAPSHOT — road status unverified"}
    coords = {int(k): v for k, v in osm["nodes"].items()}
    roadways = [w for w in osm["ways"] if w["kind"] == "road"]
    counts = Counter(n for w in roadways for n in set(w["nodes"]))
    graph = nx.MultiGraph()
    for way in roadways:
        nodes, tags = way["nodes"], way["tags"]
        start = 0
        for i in range(1, len(nodes)):
            if counts[nodes[i]] <= 1 and i != len(nodes)-1:
                continue
            section = nodes[start:i+1]
            start = i
            line = LineString([coords[n] for n in section])
            if not boundary.covers(line) or line.length == 0:
                continue
            length = transform(PROJECT, line).length
            if length < 0.5 or section[0] == section[-1]:
                continue
            ident = f"osm-{way['id']}-{i-len(section)+1}-{i}"
            graph.add_edge(section[0], section[-1], key=ident, id=ident, osm_way_id=way["id"],
                           geometry=line, length_m=round(length, 2), road_type=tags["highway"],
                           name=tags.get("name", tags.get("ref", "Unnamed road")),
                           oneway=tags.get("oneway", "yes" if tags.get("junction") == "roundabout" else "no"),
                           original_from=section[0], original_to=section[-1],
                           bridge=tags.get("bridge", "no"), surface=tags.get("surface"),
                           maxspeed_tag=tags.get("maxspeed"), osm_updated_at=way["timestamp"])
    graph = graph.subgraph(max(nx.connected_components(graph), key=len)).copy()
    # Expand along real connected roads from Kadam; no fabricated linking edges.
    center = Point(PROJECT(94.14, 27.30))
    root = min(graph.nodes, key=lambda n: Point(PROJECT(*coords[n])).distance(center))
    distances, paths = nx.single_source_dijkstra(graph, root, weight="length_m")
    full_nodes = list(graph.nodes)
    full_xy = np.array([PROJECT(*coords[n]) for n in full_nodes])

    def nearest_node(lon, lat):
        delta = full_xy - np.array(PROJECT(lon, lat))
        idx = int(np.argmin(np.sum(delta * delta, axis=1)))
        return full_nodes[idx], float(np.linalg.norm(delta[idx]))

    places = []
    exclusions = read(ROOT / "config/data_quality_exclusions.json")
    with zipfile.ZipFile(RAW / "geonames_IN.zip") as archive:
        for rawline in archive.open("IN.txt"):
            fields = rawline.decode("utf-8").rstrip("\n").split("\t")
            if fields[0] in exclusions["geonames_ids"]:
                continue
            if fields[6] != "P" or fields[10] != "03" or fields[11] != "307" or fields[7] in {"PPLQ", "PPLH", "PPLW"}:
                continue
            lat, lon = float(fields[4]), float(fields[5])
            if not (93.85 <= lon <= 94.35 and 27 <= lat <= 27.42) or not boundary.covers(Point(lon, lat)):
                continue
            node, distance = nearest_node(lon, lat)
            if distance <= 1500:
                places.append({"id": fields[0], "name": fields[1], "lon": lon, "lat": lat,
                               "feature_code": fields[7], "modified": fields[18], "node": node,
                               "center_distance": Point(PROJECT(lon, lat)).distance(center)})
    places = sorted(places, key=lambda p: (p["center_distance"], p["id"]))[:20]
    if len(places) < 15:
        raise ValueError(f"Only {len(places)} verified gazetteer settlements near graph")
    reference = read(ROOT / "config/shelter_reference.json")
    # Ensure all selected communities and document-listed shelters are represented
    # before adding nearby edges for route alternatives.
    selected = {root}
    anchors = [p["node"] for p in places]
    for shelter in reference["shelters"]:
        node, distance = nearest_node(dms(shelter["lon_dms"]), dms(shelter["lat_dms"]))
        if distance > 1500:
            raise ValueError(f"Shelter too far from graph: {shelter['id']}")
        anchors.append(node)
    for anchor in anchors:
        selected.update(paths[anchor])
    for node in sorted(distances, key=lambda n: (distances[n], n)):
        selected.add(node)
        if graph.subgraph(selected).number_of_edges() >= 800:
            break
    graph = graph.subgraph(selected).copy()
    if not 300 <= graph.number_of_edges() <= 1000 or not nx.is_connected(graph):
        raise ValueError("Bounded graph constraint failed")
    physical_edges = list(graph.edges(keys=True, data=True))
    metric_lines = [transform(PROJECT, d["geometry"]) for *_, d in physical_edges]
    water = []
    river_lines = []
    for way in osm["ways"]:
        if way["kind"] != "water":
            continue
        line = LineString([coords[n] for n in way["nodes"]])
        clipped = line.intersection(boundary)
        if clipped.is_empty:
            continue
        water.append(feature(clipped, {"id": f"water-{way['id']}", "name": way["tags"].get("name", "Waterway"),
                                     "waterway": way["tags"]["waterway"], "provenance": static}))
        if way["tags"]["waterway"] == "river":
            river_lines.append(transform(PROJECT, line))
    rivers = unary_union(river_lines)
    if rivers.is_empty:
        raise ValueError("No river geometry available")
    terrain = Terrain()

    def attach(point):
        projected = transform(PROJECT, point)
        idx = min(range(len(metric_lines)), key=lambda i: projected.distance(metric_lines[i]))
        u, v, key, _ = physical_edges[idx]
        nearest = min((u, v), key=lambda n: projected.distance(Point(PROJECT(*coords[n]))))
        elev, slope = terrain.sample(point.x, point.y)
        return {"nearest_segment_id": key, "graph_node_id": str(nearest),
                "distance_to_road_m": round(projected.distance(metric_lines[idx]), 1),
                "distance_to_graph_node_m": round(projected.distance(Point(PROJECT(*coords[nearest]))), 1),
                "access_verified": False, "elevation_m": elev, "slope_degrees": slope,
                "distance_to_river_m": round(projected.distance(rivers), 1)}

    settlements = []
    place_meta = read(RAW / "geonames_IN.zip.metadata.json")
    for place in places:
        point = Point(place["lon"], place["lat"])
        attachment = attach(point)
        settlements.append(feature(point, {"id": f"geonames-{place['id']}", "name": place["name"],
            "place_type": place["feature_code"], "population": None, "gazetteer_modified": place["modified"],
            "provenance": {"source": "live", "recorded_at": place_meta["retrieved_at"],
                           "provider": "GeoNames", "label": "GAZETTEER REFERENCE — location not field-verified"}, **attachment}))

    shelters = []
    for shelter in reference["shelters"]:
        point = Point(dms(shelter["lon_dms"]), dms(shelter["lat_dms"]))
        if not boundary.covers(point):
            raise ValueError(f"Shelter outside district: {shelter['id']}")
        shelters.append(feature(point, {"id": shelter["id"], "name": shelter["name"],
            "published_capacity": shelter["published_capacity"], "reference_year": 2025,
            "current_capacity": None, "occupied": None, "operational_status": "unverified",
            "source_page": 48, "provenance": {"source": "live", "provider": reference["provider"],
                "recorded_at": read(RAW / "lakhimpur_ddmp_2025.pdf.metadata.json")["retrieved_at"],
                "label": "2025 PUBLISHED INVENTORY — not current shelter availability"}, **attach(point)}))
    roads = []
    for u, v, key, edge in physical_edges:
        line = edge["geometry"]
        midpoint = line.interpolate(0.5, normalized=True)
        elevation, slope = terrain.sample(midpoint.x, midpoint.y)
        attrs = {k: val for k, val in edge.items() if k != "geometry"}
        attrs.update({"from_node": str(edge["original_from"]), "to_node": str(edge["original_to"]),
                      "status": "unknown", "travel_minutes": None, "elevation_m": elevation,
                      "slope_degrees": slope, "distance_to_river_m": round(transform(PROJECT, midpoint).distance(rivers), 1),
                      "provenance": static})
        roads.append(feature(line, attrs))
    terrain.close()
    for f in roads + settlements + shelters:
        if f["properties"]["elevation_m"] is None:
            raise ValueError(f"Terrain void/outside coverage: {f['properties']['id']} at {shape(f['geometry']).centroid.wkt}; do not replace missing values with zero")
    layers = {"boundary": collection([feature(boundary, {"name": "Lakhimpur, Assam", "district_code": "295",
              "original_crs": source_crs, "provenance": {"source": "live", "provider": "NWIC / Survey of India",
                  "recorded_at": read(RAW / "district_nwic_geojson.zip.metadata.json")["retrieved_at"],
                  "label": "OFFICIAL PUBLISHED BOUNDARY — NWIC May 2025 snapshot"},
              "boundary_status": "Official NWIC dataset, source agency SOI; transformed EPSG:7755 to WGS84"})]),
              "roads": collection(roads), "settlements": collection(settlements), "shelters": collection(shelters),
              "waterways": collection(water)}
    for name, layer in layers.items():
        write(name + ".geojson", layer)
    write("graph.json", {"directed": False, "description": "Physical segments; respect oneway tags when constructing directed routing graph",
          "nodes": [{"id": str(n), "longitude": coords[n][0], "latitude": coords[n][1]} for n in sorted(graph.nodes)],
          "edges": [f["properties"] for f in roads]})
    extent = unary_union([e[3]["geometry"] for e in physical_edges]).bounds
    summary = {"generated_at": now, "district": "Lakhimpur", "state": "Assam", "hazard": "flood",
        "counts": {name: len(layer["features"]) for name, layer in layers.items()},
        "graph_nodes": len(graph), "connected_components": nx.number_connected_components(graph),
        "excluded_gazetteer_entries": exclusions,
        "study_bounds": list(extent), "boundary_area_km2": round(transform(PROJECT, boundary).area / 1e6, 1),
        "max_settlement_road_distance_m": max(f["properties"]["distance_to_road_m"] for f in settlements),
        "max_shelter_road_distance_m": max(f["properties"]["distance_to_road_m"] for f in shelters),
        "terrain": {"provider": "Copernicus DEM GLO-90 (2021)", "resolution_m": 90, "type": "digital surface model",
                    "missing_samples": 0, "road_sampling": "segment midpoint; local 3x3 slope"},
        "limitations": ["Road status and last-mile access are unverified; topology is not proof of usable access.",
            "Official GIS polygon area differs from the district profile's 2277 km² figure; published GIS boundary is used without reshaping to force an area match.",
            "Shelter capacities are published in 2025; occupancy and current availability are unknown.",
            "Population is unknown; no invented village counts.", "90m surface elevation cannot resolve road deck heights or small embankments.",
            "Current geography must not be treated as verified 2024 road topology."]}
    write("geography_summary.json", summary)
    manifest = [read(p) for p in sorted(RAW.glob("*.metadata.json"))]
    write("source_manifest.json", {"generated_at": now, "sources": manifest,
          "derived_files": [{"file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(OUT.glob("*.geojson"))]})
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
