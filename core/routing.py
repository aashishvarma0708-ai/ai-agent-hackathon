ROUTING_RULES = {
    "roads": {
        "department": "Roads & Infrastructure Department",
        "sla_hours": 24,
    },
    "garbage": {
        "department": "Sanitation Department",
        "sla_hours": 12,
    },
    "drainage": {
        "department": "Drainage & Sewerage Department",
        "sla_hours": 12,
    },
    "water": {
        "department": "Water Supply Department",
        "sla_hours": 8,
    },
    "streetlights": {
        "department": "Electrical / Streetlight Maintenance",
        "sla_hours": 24,
    },
    "public_infrastructure": {
        "department": "Public Works / Infrastructure Department",
        "sla_hours": 48,
    },
    "unknown": {
        "department": "Civic Helpdesk — Human Review",
        "sla_hours": 24,
    },
}


def route_municipal_issue(category: str) -> dict:
    key = (category or "unknown").strip().lower()
    return ROUTING_RULES.get(key, ROUTING_RULES["unknown"])
