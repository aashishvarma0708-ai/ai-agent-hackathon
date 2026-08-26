import uuid
import pytest
from core.orchestrator import process_complaint
from core.routing import (
    detect_municipal_category,
    is_explicit_emergency,
    detect_external_service,
    route_municipal_issue
)
from core.risk import calculate_risk
from core.db import init_db


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_broken_light_near_house():
    """1. 'broken light near my house' -> municipal/streetlights"""
    u = uuid.uuid4().hex[:6]
    res = process_complaint(f"broken light near my house {u}", location_text=f"Sector 4, Green Park {u}")
    assert res["domain"] == "municipal"
    assert res["category"] == "streetlights"
    assert res["service_type"] == "municipal"
    assert res["status"] == "NEW"
    assert res["department"] == "Electrical / Streetlight Maintenance"


def test_street_light_not_working():
    """2. 'street light is not working' -> municipal/streetlights"""
    u = uuid.uuid4().hex[:6]
    res = process_complaint(f"street light is not working on 5th main road {u}", location_text=f"5th Main Road {u}")
    assert res["domain"] == "municipal"
    assert res["category"] == "streetlights"
    assert res["service_type"] == "municipal"
    assert res["status"] == "NEW"
    assert res["department"] == "Electrical / Streetlight Maintenance"


def test_broken_streetlight_dangerous():
    """3. 'broken streetlight and it is dangerous' -> municipal/streetlights, elevated risk"""
    u = uuid.uuid4().hex[:6]
    res = process_complaint(
        f"broken streetlight and it is dangerous {u}",
        location_text=f"Market Street {u}",
        latitude=28.6139 + hash(u) % 10,
        longitude=77.2090 + hash(u) % 10
    )
    assert res["domain"] == "municipal"
    assert res["category"] == "streetlights"
    assert res["service_type"] == "municipal"
    assert res["status"] == "NEW"
    assert res["risk_score"] >= 50
    assert res["priority"] in {"HIGH", "CRITICAL"}
    assert any("safety" in r.lower() or "danger" in r.lower() for r in res.get("risk_reasons", []))


def test_pothole_cars_swerving():
    """4. 'pothole and cars are swerving' -> municipal/roads, elevated risk"""
    u = uuid.uuid4().hex[:6]
    res = process_complaint(
        f"pothole and cars are swerving {u}",
        location_text=f"Outer Ring Road Segment {u}",
        latitude=28.7139,
        longitude=77.3090
    )
    assert res["domain"] == "municipal"
    assert res["category"] == "roads"
    assert res["service_type"] == "municipal"
    assert res["status"] == "NEW"
    assert res["risk_score"] >= 50
    assert res["priority"] in {"HIGH", "CRITICAL"}
    assert res["department"] == "Roads & Infrastructure Department"


def test_open_manhole_someone_may_fall():
    """5. 'open manhole someone may fall' -> municipal/drainage, elevated risk"""
    u = uuid.uuid4().hex[:6]
    res = process_complaint(
        f"open manhole someone may fall {u}",
        location_text=f"School Lane Cross {u}",
        latitude=28.8139,
        longitude=77.4090
    )
    assert res["domain"] == "municipal"
    assert res["category"] == "drainage"
    assert res["service_type"] == "municipal"
    assert res["status"] == "NEW"
    assert res["risk_score"] >= 50
    assert res["priority"] in {"HIGH", "CRITICAL"}
    assert res["department"] == "Drainage & Sewerage Department"


def test_active_house_fire_emergency():
    """6. 'there is an active house fire' -> emergency/external"""
    u = uuid.uuid4().hex[:6]
    res = process_complaint(f"there is an active house fire {u}", location_text=f"Oak Street {u}")
    assert res["domain"] == "emergency"
    assert res["service_type"] == "fire"
    assert res["status"] == "EMERGENCY_DISPATCHED"
    assert "112" in res["external_service_name"] or "ERSS" in res["external_service_name"]


def test_heart_attack_emergency():
    """7. 'someone is having a heart attack' -> emergency/external"""
    u = uuid.uuid4().hex[:6]
    res = process_complaint(f"someone is having a heart attack {u}", location_text=f"Community Hall {u}")
    assert res["domain"] == "emergency"
    assert res["service_type"] == "medical"
    assert res["status"] == "EMERGENCY_DISPATCHED"
    assert "112" in res["external_service_name"] or "ERSS" in res["external_service_name"]


def test_robbery_happening_now_emergency():
    """8. 'there is a robbery happening now' -> emergency/external"""
    u = uuid.uuid4().hex[:6]
    res = process_complaint(f"there is a robbery happening now {u}", location_text=f"Main Bank Branch {u}")
    assert res["domain"] == "emergency"
    assert res["service_type"] == "police"
    assert res["status"] == "EMERGENCY_DISPATCHED"
    assert "112" in res["external_service_name"] or "ERSS" in res["external_service_name"]


def test_user_reported_bug_case():
    """
    Exact case from user:
    'Citizen reported broken light near my house. The caller reported an immediate safety risk.'
    Must route to municipal/streetlights with elevated safety risk.
    """
    u = uuid.uuid4().hex[:6]
    text = f"Citizen reported broken light near my house. The caller reported an immediate safety risk. {u}"
    res = process_complaint(text, location_text=f"Koramangala 4th Block {u}")
    
    assert res["domain"] == "municipal"
    assert res["category"] == "streetlights"
    assert res["service_type"] == "municipal"
    assert res["status"] == "NEW"
    assert res["department"] == "Electrical / Streetlight Maintenance"
    assert res["risk_score"] >= 50
    assert res["priority"] in {"HIGH", "CRITICAL"}
    
    trace_str = " ".join(res["agent_trace"])
    assert "MUNICIPAL" in trace_str
    assert "STREETLIGHTS" in trace_str
    assert "Non-municipal [UNKNOWN / OTHER]" not in trace_str


def test_additional_streetlight_variants():
    """Verify common citizen streetlight synonyms map cleanly to municipal/streetlights"""
    variants = [
        "broken light pole",
        "street light not working",
        "road light is broken",
        "lamp post not working",
        "streetlamp went out",
        "dark street due to light failure"
    ]
    for idx, text in enumerate(variants):
        u = uuid.uuid4().hex[:6]
        res = process_complaint(f"{text} {u}", location_text=f"Ward Test {u}")
        assert res["domain"] == "municipal", f"Failed on '{text}'"
        assert res["category"] == "streetlights", f"Failed category on '{text}'"
        assert res["status"] == "NEW"


def test_domain_and_safety_risk_independence():
    """
    Verify that safety hazard keywords do not turn municipal complaints into emergency domain,
    but elevate risk score and priority.
    """
    cases = [
        ("deep crater on highway and cars may crash", "roads"),
        ("broken light and people may get hurt in dark", "streetlights"),
        ("open sewer drain hazard where children play", "drainage"),
        ("burst drinking water pipeline causing flooded street", "water"),
    ]
    for text, expected_cat in cases:
        u = uuid.uuid4().hex[:6]
        res = process_complaint(f"{text} {u}", location_text=f"Unique Loc {u}")
        assert res["domain"] == "municipal", f"Expected municipal domain for '{text}'"
        assert res["category"] == expected_cat, f"Expected category {expected_cat} for '{text}'"
        assert res["risk_score"] >= 45, f"Expected elevated risk for '{text}'"


