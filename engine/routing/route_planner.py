"""Model-driven arrival-time route planner for Lakhimpur flood response operations."""
import itertools
import json
import math
from pathlib import Path
from typing import Any

import networkx as nx

from engine.config import ROOT, load_district

PROCESSED = ROOT / "data/processed"

SPEED_KMH_MAP = {
    "primary": 50.0,
    "secondary": 40.0,
    "tertiary": 30.0,
    "residential": 25.0,
    "unclassified": 20.0,
    "track": 15.0,
}
DEFAULT_SPEED_KMH = 20.0


class RoutePlanner:
    def __init__(self, data_dir: Path = PROCESSED):
        self.data_dir = data_dir
        self.graph_data = json.loads((data_dir / "graph.json").read_text(encoding="utf-8"))
        self.roads_data = json.loads((data_dir / "roads.geojson").read_text(encoding="utf-8"))
        self.settlements_data = json.loads((data_dir / "settlements.geojson").read_text(encoding="utf-8"))
        self.shelters_data = json.loads((data_dir / "shelters.geojson").read_text(encoding="utf-8"))

        self.district = load_district()
        self.basecamp = self.district.basecamp.model_dump() if self.district.basecamp else {
            "id": "basecamp-borimuri",
            "name": "Borimuri Basecamp",
            "plus_code": "748G+M62",
            "address": "Borimuri, North Lakhimpur, Assam 787032",
            "latitude": 27.2666,
            "longitude": 94.1255,
            "graph_node_id": "1698435895",
        }

        self._build_indexes()
        self._build_graph()

    def _build_indexes(self):
        self.nodes = {n["id"]: n for n in self.graph_data["nodes"]}
        self.edges = {e["id"]: e for e in self.graph_data["edges"]}
        self.road_features = {f["properties"]["id"]: f for f in self.roads_data["features"]}
        self.settlements = {f["properties"]["id"]: f for f in self.settlements_data["features"]}
        self.shelters = {f["properties"]["id"]: f for f in self.shelters_data["features"]}

    def _build_graph(self):
        self.G = nx.Graph()
        for e in self.graph_data["edges"]:
            speed_kmh = SPEED_KMH_MAP.get(e.get("road_type"), DEFAULT_SPEED_KMH)
            speed_ms = speed_kmh * 1000.0 / 3600.0
            length_m = float(e.get("length_m", 10.0))
            time_sec = length_m / speed_ms
            self.G.add_edge(
                e["from_node"],
                e["to_node"],
                id=e["id"],
                length_m=length_m,
                time_sec=time_sec,
                road_type=e.get("road_type", "unclassified"),
                name=e.get("name") or "Unnamed Road",
                elevation_m=e.get("elevation_m"),
                status=e.get("status", "unknown"),
            )

    def _get_edge_coordinates(self, edge_id: str, from_node: str, to_node: str) -> list[list[float]]:
        """Returns [lat, lon] coordinates in travel direction."""
        feat = self.road_features.get(edge_id)
        if not feat or "geometry" not in feat or "coordinates" not in feat["geometry"]:
            n1 = self.nodes.get(from_node)
            n2 = self.nodes.get(to_node)
            if n1 and n2:
                return [[n1["latitude"], n1["longitude"]], [n2["latitude"], n2["longitude"]]]
            return []

        coords = feat["geometry"]["coordinates"]  # [lon, lat]
        if not coords:
            return []

        lat_lons = [[c[1], c[0]] for c in coords]
        n1 = self.nodes.get(from_node)
        if n1:
            start_dist = (lat_lons[0][0] - n1["latitude"]) ** 2 + (lat_lons[0][1] - n1["longitude"]) ** 2
            end_dist = (lat_lons[-1][0] - n1["latitude"]) ** 2 + (lat_lons[-1][1] - n1["longitude"]) ** 2
            if end_dist < start_dist:
                lat_lons.reverse()
        return lat_lons

    def _select_eta_bucket(self, cumulative_eta_min: float) -> int:
        if cumulative_eta_min <= 45.0:
            return 30
        elif cumulative_eta_min <= 90.0:
            return 60
        else:
            return 120

    def evaluate_path(
        self,
        node_path: list[str],
        start_eta_offset_min: float = 0.0,
        predictions_by_eta: dict[int, dict[str, dict]] | None = None,
        confirmed_closures: set[str] | None = None,
    ) -> dict[str, Any]:
        """Evaluates a node sequence for travel time, distance, arrival ETA, and usability predictions."""
        confirmed_closures = confirmed_closures or set()
        segments = []
        cumulative_sec = 0.0
        total_dist_m = 0.0
        polyline = []
        reliability_product = 1.0
        rejection_reasons = []
        is_binding_closure = False
        has_high_risk = False

        for i in range(len(node_path) - 1):
            u, v = node_path[i], node_path[i + 1]
            edge = self.G[u][v]
            edge_id = edge["id"]
            name = edge["name"]
            length_m = edge["length_m"]
            time_sec = edge["time_sec"]

            cumulative_sec += time_sec
            arrival_eta_min = start_eta_offset_min + (cumulative_sec / 60.0)
            bucket = self._select_eta_bucket(arrival_eta_min)

            # Check model prediction
            pred_data = None
            p_unusable = 0.0
            risk_level = "LOW"
            road_status = edge.get("status", "unknown")
            quality = "OK"

            if predictions_by_eta and bucket in predictions_by_eta:
                pred = predictions_by_eta[bucket].get(edge_id)
                if pred:
                    pred_data = pred
                    p_unusable = float(pred.get("probability_unusable", 0.0))
                    risk_level = pred.get("risk_level", "LOW")
                    road_status = pred.get("road_status", road_status)
                    quality = pred.get("data_quality_status", "OK")

            # Binding closure check
            if edge_id in confirmed_closures or road_status == "closed":
                is_binding_closure = True
                p_unusable = 1.0
                risk_level = "HIGH"
                rejection_reasons.append(
                    f"Confirmed road closure on {name} ({edge_id}) at arrival ETA {arrival_eta_min:.0f}m"
                )

            # High flood risk check
            elif p_unusable >= 0.70 or risk_level == "HIGH":
                has_high_risk = True
                rejection_reasons.append(
                    f"High predicted flood risk ({p_unusable * 100:.1f}%) on {name} ({edge_id}) at arrival ETA {arrival_eta_min:.0f}m"
                )

            reliability_product *= max(0.001, 1.0 - p_unusable)
            coords = self._get_edge_coordinates(edge_id, u, v)

            if not polyline:
                polyline.extend(coords)
            else:
                if coords:
                    polyline.extend(coords[1:])

            total_dist_m += length_m
            segments.append({
                "road_id": edge_id,
                "name": name,
                "road_type": edge.get("road_type"),
                "length_m": round(length_m, 1),
                "time_sec": round(time_sec, 1),
                "travel_time_min": round(time_sec / 60.0, 1),
                "arrival_eta_min": round(arrival_eta_min, 1),
                "eta_bucket": bucket,
                "probability_unusable": round(p_unusable, 4),
                "risk_level": risk_level,
                "road_status": road_status,
                "quality": quality,
                "coordinates": coords,
            })

        reliability_pct = round(reliability_product * 100.0, 1)
        total_time_min = round(cumulative_sec / 60.0, 1)
        total_dist_km = round(total_dist_m / 1000.0, 2)

        status = "RECOMMENDED"
        if is_binding_closure:
            status = "REJECTED_CLOSED"
        elif has_high_risk:
            status = "REJECTED_FLOOD_RISK"
        elif reliability_pct < 60.0:
            status = "CAUTION_LOW_RELIABILITY"

        return {
            "status": status,
            "is_binding_closure": is_binding_closure,
            "has_high_risk": has_high_risk,
            "rejection_reasons": rejection_reasons,
            "total_distance_km": total_dist_km,
            "total_time_minutes": total_time_min,
            "reliability_pct": reliability_pct,
            "segments": segments,
            "polyline": polyline,
            "node_count": len(node_path),
        }

    def find_candidate_routes(
        self,
        start_node: str,
        dest_node: str,
        max_paths: int = 5,
        start_eta_offset_min: float = 0.0,
        predictions_by_eta: dict[int, dict[str, dict]] | None = None,
        confirmed_closures: set[str] | None = None,
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]]]:
        """Finds candidate routes and classifies them into recommended, alternatives, and rejected."""
        if not nx.has_path(self.G, start_node, dest_node):
            return None, [], [{
                "route_name": "No Physical Connection",
                "reason": "Graph network has no path between origin and destination nodes",
                "severity": "CRITICAL",
                "rejected_segments": [],
            }]

        raw_paths = list(itertools.islice(nx.shortest_simple_paths(self.G, start_node, dest_node, weight="time_sec"), max_paths))

        evaluated = []
        for p in raw_paths:
            ev = self.evaluate_path(p, start_eta_offset_min, predictions_by_eta, confirmed_closures)
            evaluated.append(ev)

        viable = [r for r in evaluated if not r["is_binding_closure"] and not r["has_high_risk"]]
        rejected = [r for r in evaluated if r["is_binding_closure"] or r["has_high_risk"]]

        # If no path is completely clear of high risk, keep least risky viable path with caution
        if not viable and evaluated:
            evaluated_no_closures = [r for r in evaluated if not r["is_binding_closure"]]
            if evaluated_no_closures:
                evaluated_no_closures.sort(key=lambda r: (-r["reliability_pct"], r["total_time_minutes"]))
                viable.append(evaluated_no_closures[0])
                rejected = [r for r in evaluated if r != evaluated_no_closures[0]]

        viable.sort(key=lambda r: (-r["reliability_pct"], r["total_time_minutes"]))

        recommended = viable[0] if viable else None
        alternatives = viable[1:] if len(viable) > 1 else []

        rejected_explanations = []
        for idx, r in enumerate(rejected):
            rejected_explanations.append({
                "route_name": f"Alternative Route {idx + 1}",
                "reason": "; ".join(r["rejection_reasons"]) if r["rejection_reasons"] else "Avoided due to lower reliability",
                "severity": "CRITICAL" if r["is_binding_closure"] else "HIGH_RISK",
                "reasons_list": r["rejection_reasons"],
                "total_time_minutes": r["total_time_minutes"],
                "total_distance_km": r["total_distance_km"],
                "reliability_pct": r["reliability_pct"],
                "polyline": r["polyline"],
            })

        return recommended, alternatives, rejected_explanations

    def find_closest_shelter(self, settlement_node: str) -> dict[str, Any] | None:
        """Finds closest relief shelter connected to the given settlement node."""
        candidates = []
        for feat in self.shelters_data["features"]:
            props = feat["properties"]
            sh_node = props.get("graph_node_id")
            if not sh_node or not nx.has_path(self.G, settlement_node, sh_node):
                continue
            path = nx.shortest_path(self.G, settlement_node, sh_node, weight="time_sec")
            dist_m = sum(self.G[path[i]][path[i + 1]]["length_m"] for i in range(len(path) - 1))
            time_sec = sum(self.G[path[i]][path[i + 1]]["time_sec"] for i in range(len(path) - 1))
            candidates.append({
                "shelter": props,
                "node_id": sh_node,
                "path": path,
                "distance_km": round(dist_m / 1000.0, 2),
                "time_minutes": round(time_sec / 60.0, 1),
            })

        if not candidates:
            return None
        candidates.sort(key=lambda c: c["time_minutes"])
        return candidates[0]

    def generate_navigation_steps(
        self,
        leg1_route: dict[str, Any],
        leg2_route: dict[str, Any] | None,
        dest_settlement_name: str,
        shelter_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Generates step-by-step turn/maneuver instructions for Google Maps style navigation."""
        steps = []
        step_idx = 1

        # Leg 1 steps: Basecamp -> Settlement
        l1_segs = leg1_route.get("segments", [])
        if l1_segs:
            # Group consecutive segments on same road
            grouped = []
            current = None
            for s in l1_segs:
                if current and current["name"] == s["name"]:
                    current["length_m"] += s["length_m"]
                    current["time_sec"] += s["time_sec"]
                    current["coordinates"].extend(s["coordinates"][1:])
                    current["probability_unusable"] = max(current["probability_unusable"], s["probability_unusable"])
                else:
                    if current:
                        grouped.append(current)
                    current = dict(s)
                    current["coordinates"] = list(s["coordinates"])
            if current:
                grouped.append(current)

            for i, g in enumerate(grouped):
                road_name = g["name"]
                dist_km = round(g["length_m"] / 1000.0, 2)
                dist_m = int(g["length_m"])
                dist_str = f"{dist_m} m" if dist_m < 1000 else f"{dist_km} km"
                mins = max(1, round(g["time_sec"] / 60.0))

                if i == 0:
                    instruction = f"Depart from Borimuri Basecamp onto {road_name} ({dist_str})"
                else:
                    instruction = f"Continue on {road_name} for {dist_str} (approx {mins} min)"

                steps.append({
                    "step_number": step_idx,
                    "leg": "rescue",
                    "instruction": instruction,
                    "road_name": road_name,
                    "distance_m": dist_m,
                    "duration_sec": int(g["time_sec"]),
                    "probability_unusable": g["probability_unusable"],
                    "risk_level": g["risk_level"],
                    "coordinates": g["coordinates"],
                })
                step_idx += 1

            # Arrival at settlement
            steps.append({
                "step_number": step_idx,
                "leg": "rescue",
                "instruction": f"Arrive at destination: {dest_settlement_name} Settlement",
                "road_name": "Destination",
                "distance_m": 0,
                "duration_sec": 0,
                "probability_unusable": 0.0,
                "risk_level": "LOW",
                "coordinates": grouped[-1]["coordinates"][-1:] if grouped else [],
            })
            step_idx += 1

        # Leg 2 steps: Settlement -> Shelter
        if leg2_route and shelter_name:
            l2_segs = leg2_route.get("segments", [])
            grouped2 = []
            current = None
            for s in l2_segs:
                if current and current["name"] == s["name"]:
                    current["length_m"] += s["length_m"]
                    current["time_sec"] += s["time_sec"]
                    current["coordinates"].extend(s["coordinates"][1:])
                    current["probability_unusable"] = max(current["probability_unusable"], s["probability_unusable"])
                else:
                    if current:
                        grouped2.append(current)
                    current = dict(s)
                    current["coordinates"] = list(s["coordinates"])
            if current:
                grouped2.append(current)

            for i, g in enumerate(grouped2):
                road_name = g["name"]
                dist_km = round(g["length_m"] / 1000.0, 2)
                dist_m = int(g["length_m"])
                dist_str = f"{dist_m} m" if dist_m < 1000 else f"{dist_km} km"
                mins = max(1, round(g["time_sec"] / 60.0))

                if i == 0:
                    instruction = f"Evacuate from {dest_settlement_name} onto {road_name} toward {shelter_name} ({dist_str})"
                else:
                    instruction = f"Follow {road_name} for {dist_str} (approx {mins} min)"

                steps.append({
                    "step_number": step_idx,
                    "leg": "evacuation",
                    "instruction": instruction,
                    "road_name": road_name,
                    "distance_m": dist_m,
                    "duration_sec": int(g["time_sec"]),
                    "probability_unusable": g["probability_unusable"],
                    "risk_level": g["risk_level"],
                    "coordinates": g["coordinates"],
                })
                step_idx += 1

            steps.append({
                "step_number": step_idx,
                "leg": "evacuation",
                "instruction": f"Arrive at Relief Camp: {shelter_name}",
                "road_name": "Relief Shelter",
                "distance_m": 0,
                "duration_sec": 0,
                "probability_unusable": 0.0,
                "risk_level": "LOW",
                "coordinates": grouped2[-1]["coordinates"][-1:] if grouped2 else [],
            })

        return steps

    def plan_mission(
        self,
        settlement_id: str,
        predictions_by_eta: dict[int, dict[str, dict]] | None = None,
        confirmed_closures: set[str] | None = None,
    ) -> dict[str, Any]:
        """Plans complete two-leg rescue & evacuation mission: Basecamp -> Settlement -> Shelter."""
        settlement_feat = self.settlements.get(settlement_id)
        if not settlement_feat:
            raise ValueError(f"Unknown settlement ID: {settlement_id}")

        dest_props = settlement_feat["properties"]
        dest_node = dest_props.get("graph_node_id")
        if not dest_node or dest_node not in self.G:
            raise ValueError(f"Settlement {settlement_id} is not mapped to a graph node")

        base_node = self.basecamp["graph_node_id"]

        # Leg 1: Basecamp -> Settlement
        recommended, alternatives, rejected = self.find_candidate_routes(
            start_node=base_node,
            dest_node=dest_node,
            max_paths=5,
            start_eta_offset_min=0.0,
            predictions_by_eta=predictions_by_eta,
            confirmed_closures=confirmed_closures,
        )

        if not recommended:
            raise RuntimeError(f"No navigable route found from Basecamp to settlement {dest_props.get('name')}")

        # Leg 2: Settlement -> Shelter
        shelter_match = self.find_closest_shelter(dest_node)
        leg2_route = None
        shelter_info = None

        if shelter_match:
            shelter_info = shelter_match["shelter"]
            sh_node = shelter_match["node_id"]
            leg1_arrival_time = recommended["total_time_minutes"]

            rec2, _, _ = self.find_candidate_routes(
                start_node=dest_node,
                dest_node=sh_node,
                max_paths=3,
                start_eta_offset_min=leg1_arrival_time,
                predictions_by_eta=predictions_by_eta,
                confirmed_closures=confirmed_closures,
            )
            leg2_route = rec2

        nav_steps = self.generate_navigation_steps(
            leg1_route=recommended,
            leg2_route=leg2_route,
            dest_settlement_name=dest_props.get("name", "Settlement"),
            shelter_name=shelter_info.get("name") if shelter_info else None,
        )

        total_mission_dist = recommended["total_distance_km"] + (leg2_route["total_distance_km"] if leg2_route else 0.0)
        total_mission_time = recommended["total_time_minutes"] + (leg2_route["total_time_minutes"] if leg2_route else 0.0)

        return {
            "basecamp": self.basecamp,
            "settlement": {
                "id": dest_props["id"],
                "name": dest_props.get("name"),
                "graph_node_id": dest_node,
                "coordinates": [settlement_feat["geometry"]["coordinates"][1], settlement_feat["geometry"]["coordinates"][0]],  # [lat, lon]
            },
            "shelter": shelter_info,
            "mission_summary": {
                "total_distance_km": round(total_mission_dist, 2),
                "total_time_minutes": round(total_mission_time, 1),
                "leg1_time_minutes": recommended["total_time_minutes"],
                "leg2_time_minutes": leg2_route["total_time_minutes"] if leg2_route else 0.0,
                "overall_reliability_pct": round((recommended["reliability_pct"] * (leg2_route["reliability_pct"] / 100.0 if leg2_route else 1.0)), 1),
            },
            "leg1_routes": {
                "recommended": recommended,
                "alternatives": alternatives,
                "rejected_routes": rejected,
            },
            "leg2_route": leg2_route,
            "navigation_steps": nav_steps,
        }
