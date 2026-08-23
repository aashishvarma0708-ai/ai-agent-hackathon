from typing import List, Dict, Any, Optional

BASE_RISK = {
    "roads": 32,
    "drainage": 30,
    "water": 30,
    "public_infrastructure": 26,
    "garbage": 22,
    "streetlights": 22,
    "unknown": 15,
}

# High severity safety indicators (+15 to +35)
SAFETY_HAZARD_TERMS = {
    "accident": 18,
    "crash": 18,
    "skidded": 14,
    "fall": 12,
    "injured": 20,
    "injury": 20,
    "danger": 14,
    "dangerous": 14,
    "fire": 25,
    "sparking": 22,
    "electrocution": 28,
    "live wire": 28,
    "transformer": 22,
    "flood": 18,
    "flooded": 18,
    "flooding": 18,
    "collapsed": 22,
    "sinkhole": 24,
    "open manhole": 25,
    "manhole": 20,
    "rupture": 16,
    "burst": 16,
}

# Sensitive / public safety locations (+10 to +20)
SENSITIVE_LOCATION_TERMS = {
    "school": 18,
    "college": 14,
    "university": 14,
    "hospital": 20,
    "clinic": 16,
    "kindergarten": 20,
    "children": 18,
    "playground": 14,
    "bus stop": 12,
    "metro": 14,
    "station": 12,
    "market": 12,
    "temple": 10,
    "cross junction": 12,
}

# General volume and severity signals (+4 to +12)
VOLUME_SEVERITY_TERMS = {
    "massive": 10,
    "huge": 8,
    "large": 6,
    "deep": 8,
    "blocked": 10,
    "obstruction": 10,
    "multiple": 8,
    "days": 6,
    "weeks": 10,
    "overflow": 8,
    "stagnant": 8,
    "smell": 6,
    "dark": 6,
    "pitch black": 10,
    "leakage": 8,
    "zero water": 12,
    "no water": 12,
}


def calculate_risk(
    category: str,
    text: str,
    location_text: str = "",
    indicators: Optional[List[str]] = None,
    duplicate_count: int = 0,
    hours_unresolved: float = 0.0
) -> Dict[str, Any]:
    """
    Deterministic Civic Risk Scoring Engine.
    Combines baseline risk, safety hazards, sensitive institutions, duplicate citizen volume, and unresolved duration.
    """
    category_key = (category or "unknown").lower()
    score = BASE_RISK.get(category_key, 15)
    reasons = [f"Base risk for {category_key.upper()} category: {score}"]

    combined = f"{text or ''} {location_text or ''} {' '.join([str(i) for i in (indicators or [])])}".lower()

    # 1. Safety Hazards Assessment
    safety_matches = []
    safety_add = 0
    for term, weight in SAFETY_HAZARD_TERMS.items():
        if term in combined:
            safety_matches.append(term)
            safety_add = max(safety_add, weight)
    
    if safety_matches:
        # Boost up to 35 max for multiple safety indicators
        total_safety = min(35, safety_add + max(0, (len(safety_matches) - 1) * 4))
        score += total_safety
        reasons.append(f"Immediate safety hazard (+{total_safety}): {', '.join(safety_matches[:4])}")

    # 2. Sensitive Location Proximity
    location_matches = []
    location_add = 0
    for term, weight in SENSITIVE_LOCATION_TERMS.items():
        if term in combined:
            location_matches.append(term)
            location_add = max(location_add, weight)

    if location_matches:
        total_loc = min(22, location_add + max(0, (len(location_matches) - 1) * 3))
        score += total_loc
        reasons.append(f"Near sensitive / high-density location (+{total_loc}): {', '.join(location_matches[:3])}")

    # 3. Severity & Scale Modifiers
    severity_matches = []
    for term, weight in VOLUME_SEVERITY_TERMS.items():
        if term in combined:
            severity_matches.append(term)
    
    if severity_matches:
        sev_add = min(15, 4 + len(severity_matches) * 2)
        score += sev_add
        reasons.append(f"Severity and impact keywords (+{sev_add}): {', '.join(severity_matches[:4])}")

    # 4. Duplicate / Citizen Volume Boost
    if duplicate_count > 0:
        dup_add = min(20, duplicate_count * 4)
        score += dup_add
        reasons.append(f"Citizen reports volume (+{dup_add}): {duplicate_count + 1} cumulative complaints filed")

    # 5. Duration Unresolved Aging Boost
    if hours_unresolved >= 48:
        score += 15
        reasons.append(f"Aging complaint (+15): Unresolved for {int(hours_unresolved)} hours")
    elif hours_unresolved >= 24:
        score += 8
        reasons.append(f"Aging complaint (+8): Unresolved for {int(hours_unresolved)} hours")

    # Normalize final score between 0 and 100
    final_score = max(0, min(100, int(score)))

    if final_score >= 76:
        priority = "CRITICAL"
    elif final_score >= 51:
        priority = "HIGH"
    elif final_score >= 26:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    return {
        "score": final_score,
        "priority": priority,
        "reasons": reasons
    }
