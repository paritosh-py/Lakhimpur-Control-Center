"""Unit tests for the model-driven arrival-time route planner."""
import pytest
from engine.routing.route_planner import RoutePlanner


@pytest.fixture
def planner():
    return RoutePlanner()


def test_basecamp_configuration(planner):
    bc = planner.basecamp
    assert bc["name"] == "Borimuri Basecamp"
    assert bc["plus_code"] == "748G+M62"
    assert bc["graph_node_id"] == "1698435895"
    assert abs(bc["latitude"] - 27.2666) < 0.001
    assert abs(bc["longitude"] - 94.1255) < 0.001


def test_plan_mission_basic(planner):
    settlements = planner.settlements_data["features"]
    first_settlement_id = settlements[0]["properties"]["id"]
    
    plan = planner.plan_mission(first_settlement_id)
    assert plan["basecamp"]["name"] == "Borimuri Basecamp"
    assert plan["settlement"]["id"] == first_settlement_id
    assert plan["mission_summary"]["total_distance_km"] > 0
    assert plan["mission_summary"]["total_time_minutes"] > 0
    
    # Leg 1 recommended route
    rec = plan["leg1_routes"]["recommended"]
    assert rec is not None
    assert rec["total_distance_km"] > 0
    assert rec["total_time_minutes"] > 0
    assert len(rec["segments"]) > 0
    assert len(rec["polyline"]) > 0
    
    # Leg 2 shelter route
    assert plan["shelter"] is not None
    assert plan["shelter"]["published_capacity"] > 0
    if plan["leg2_route"]:
        assert plan["leg2_route"]["total_distance_km"] >= 0
    
    # Navigation steps
    steps = plan["navigation_steps"]
    assert len(steps) >= 2
    assert "Borimuri Basecamp" in steps[0]["instruction"]
    assert any("Arrive at destination" in s["instruction"] for s in steps)


def test_reachability_all_settlements(planner):
    for feat in planner.settlements_data["features"]:
        sid = feat["properties"]["id"]
        plan = planner.plan_mission(sid)
        assert plan["leg1_routes"]["recommended"] is not None
        assert plan["leg1_routes"]["recommended"]["total_distance_km"] > 0


def test_confirmed_closure_is_binding(planner):
    first_settlement_id = planner.settlements_data["features"][0]["properties"]["id"]
    plan_clean = planner.plan_mission(first_settlement_id)
    first_segment_id = plan_clean["leg1_routes"]["recommended"]["segments"][0]["road_id"]

    # Close that segment
    plan_closed = planner.plan_mission(first_settlement_id, confirmed_closures={first_segment_id})
    # The clean route must be rejected or alternative route chosen
    clean_seg_ids = [s["road_id"] for s in plan_clean["leg1_routes"]["recommended"]["segments"]]
    new_seg_ids = [s["road_id"] for s in plan_closed["leg1_routes"]["recommended"]["segments"]]
    
    # The closed segment cannot be in the new recommended route
    assert first_segment_id not in new_seg_ids
    # And rejection explanations must cite the closure
    rejected = plan_closed["leg1_routes"]["rejected_routes"]
    assert any(first_segment_id in r["reason"] for r in rejected)


def test_arrival_time_eta_bucket_mapping(planner):
    first_settlement_id = planner.settlements_data["features"][0]["properties"]["id"]
    
    # Mock high risk at 30 min bucket for the first segment
    clean_plan = planner.plan_mission(first_settlement_id)
    target_seg_id = clean_plan["leg1_routes"]["recommended"]["segments"][0]["road_id"]

    mock_preds = {
        30: {
            target_seg_id: {
                "road_id": target_seg_id,
                "probability_unusable": 0.85,
                "risk_level": "HIGH",
                "road_status": "flooded",
                "data_quality_status": "OK",
            }
        },
        60: {},
        120: {},
    }

    plan_with_preds = planner.plan_mission(first_settlement_id, predictions_by_eta=mock_preds)
    # The high risk segment should trigger avoidance or explicit rejection reason
    rejected = plan_with_preds["leg1_routes"]["rejected_routes"]
    assert any(target_seg_id in r["reason"] or "flood" in r["reason"].lower() for r in rejected)
