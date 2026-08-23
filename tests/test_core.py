from core.risk import calculate_risk
from core.routing import route_municipal_issue


def test_risk_is_deterministic():
    r = calculate_risk("roads", "Large pothole outside school, bikes nearly crashed")
    assert r["score"] >= 50
    assert r["priority"] in {"HIGH", "CRITICAL"}


def test_route_roads():
    route = route_municipal_issue("roads")
    assert "Roads" in route["department"]
    assert route["sla_hours"] > 0
