from typing import Optional, Tuple, Dict, Any, List

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


MUNICIPAL_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "streetlights": {
        "keywords": [
            "streetlight", "street light", "street lights", "streetlights",
            "streetlamp", "street lamp", "street lamps", "lamp post", "lamppost",
            "light pole", "lightpole", "road light", "road lights", "public light",
            "public lights", "broken light", "broken lights", "light not working",
            "light is not working", "lights not working", "lights are not working",
            "light went out", "lights went out", "dark street due to light",
            "dark street", "dark road", "street dark", "dark lane",
            "flickering light", "flickering streetlight", "pole light",
            "non working light", "non-working light", "no street light",
            "no street lights", "street lighting", "bulb fused", "light bulb",
            "lamp broken", "damaged lamp", "damaged light pole", "broken streetlight"
        ],
        "default_subcategory": "broken_streetlight"
    },
    "roads": {
        "keywords": [
            "pothole", "potholes", "road damage", "damaged road", "broken road",
            "road crack", "road cracks", "crater", "craters", "bad road", "road broken",
            "asphalt damage", "tar road", "footpath", "footpath damage", "damaged footpath",
            "broken footpath", "sidewalk", "damaged sidewalk", "broken sidewalk",
            "street damaged", "damaged street", "pavement", "damaged pavement",
            "road cave in", "cave in", "sinkhole", "speed breaker", "broken divider",
            "road divider", "kerb", "curb", "uneven road"
        ],
        "default_subcategory": "pothole"
    },
    "garbage": {
        "keywords": [
            "garbage", "trash", "waste", "dumping", "illegal dumping", "dumped waste",
            "garbage dump", "garbage pile", "rubbish", "dustbin", "overflowing bin",
            "overflowing dustbin", "litter", "littering", "debris", "waste pile",
            "uncollected garbage", "filth", "dead animal", "animal carcass",
            "refuse", "sweepings", "sanitation", "stench from garbage", "garbage accumulation"
        ],
        "default_subcategory": "garbage_accumulation"
    },
    "drainage": {
        "keywords": [
            "drain", "drainage", "blocked drain", "clogged drain", "choked drain",
            "drain overflow", "overflowing drain", "sewage", "sewage overflow", "sewer",
            "sewerage", "sewer line", "manhole", "open manhole", "manhole cover",
            "broken manhole", "missing manhole", "gutter", "open gutter", "drain block",
            "waterlogging", "water logging", "flooding", "flooded street", "submerged road",
            "standing water", "water stagnation", "flooded road", "stagnant water"
        ],
        "default_subcategory": "blocked_drain"
    },
    "water": {
        "keywords": [
            "water leak", "water leakage", "pipe leak", "leaking pipe", "pipe leaking",
            "water supply", "no water supply", "no water", "burst pipe", "pipe burst",
            "pipeline leak", "pipeline burst", "pipeline broken", "broken pipe",
            "low water pressure", "contaminated water", "dirty water supply",
            "water pipeline", "drinking water", "water line", "water pipe"
        ],
        "default_subcategory": "water_leak"
    },
    "public_infrastructure": {
        "keywords": [
            "public building", "bus stop", "bus shelter", "park", "public park",
            "bridge", "broken bridge", "railing", "broken railing", "foot over bridge",
            "public bench", "fallen tree", "tree branch blocking", "damaged divider",
            "public wall", "community hall", "public asset", "damaged structure"
        ],
        "default_subcategory": "damaged_public_infrastructure"
    }
}


def is_explicit_emergency(text: str) -> Optional[Tuple[str, str]]:
    """
    Identifies genuine non-municipal life-threatening emergencies requiring ERSS 112 dispatch.
    Returns (domain, service_type) if explicit emergency, else None.
    """
    t = (text or "").lower()

    # Explicit fire emergencies
    fire_signals = [
        "active fire", "house fire", "building on fire", "flames", "burning building",
        "gas cylinder blast", "cylinder blast", "forest fire", "building burning",
        "active house fire", "fire broke out"
    ]
    if any(sig in t for sig in fire_signals):
        return ("emergency", "fire")

    # Explicit medical emergencies
    medical_signals = [
        "heart attack", "cardiac arrest", "stroke", "unconscious person", "unconscious",
        "severe bleeding", "patient collapsed", "stopped breathing", "respiratory arrest",
        "someone is having a heart attack", "having a stroke"
    ]
    if any(sig in t for sig in medical_signals):
        return ("emergency", "medical")

    # Explicit violent crime / active police emergencies
    crime_signals = [
        "robbery happening now", "active robbery", "armed robbery", "shooting",
        "active shooter", "stabbed", "someone is attacking", "attacking me",
        "hostage", "kidnapping in progress", "gunshots", "murder in progress",
        "robbery in progress", "someone broke in with weapon"
    ]
    if any(sig in t for sig in crime_signals):
        return ("emergency", "police")

    return None


def detect_municipal_category(text: str) -> Optional[Tuple[str, str]]:
    """
    Deterministic municipal keyword and phrase classifier.
    Returns (category, subcategory) if text matches a municipal issue, else None.
    """
    t = (text or "").lower()

    # Prioritized category evaluation: Streetlights -> Water -> Roads -> Drainage -> Garbage -> Public Infrastructure
    eval_order = ["streetlights", "water", "roads", "drainage", "garbage", "public_infrastructure"]

    for category in eval_order:
        config = MUNICIPAL_TAXONOMY[category]
        for kw in config["keywords"]:
            if kw in t:
                subcat = config["default_subcategory"]
                # Refine subcategory based on specific cues
                if category == "streetlights":
                    if "pole" in t:
                        subcat = "damaged_light_pole"
                    else:
                        subcat = "broken_streetlight"
                elif category == "water":
                    if "burst" in t or "broken pipe" in t:
                        subcat = "pipe_burst"
                    elif "no water" in t or "pressure" in t:
                        subcat = "no_water_supply"
                    else:
                        subcat = "water_leak"
                elif category == "roads":
                    if "footpath" in t or "sidewalk" in t:
                        subcat = "footpath_damage"
                    elif "crack" in t:
                        subcat = "road_crack"
                    elif "pothole" in t or "crater" in t:
                        subcat = "pothole"
                    else:
                        subcat = "damaged_road"
                elif category == "drainage":
                    if "manhole" in t:
                        subcat = "open_drain"
                    elif "waterlog" in t or "flood" in t or "stagnan" in t:
                        subcat = "waterlogging"
                    elif "sewage" in t or "sewer" in t:
                        subcat = "sewage_overflow"
                    else:
                        subcat = "blocked_drain"
                elif category == "garbage":
                    if "dump" in t:
                        subcat = "illegal_dumping"
                    elif "overflow" in t or "bin" in t:
                        subcat = "overflowing_bin"
                    else:
                        subcat = "garbage_accumulation"
                return (category, subcat)

    return None



def detect_external_service(text: str) -> Optional[Tuple[str, str, str]]:
    """
    Identifies non-municipal public service referrals (police, legal, consumer, health).
    Returns (domain, service_type, subcategory) if matched, else None.
    """
    t = (text or "").lower()

    police_terms = ["stolen", "theft", "robbery", "burglary", "assault", "harassment", "crime", "threat", "police complaint"]
    legal_terms = ["legal aid", "lawyer", "court", "legal case", "property dispute", "nalsa"]
    consumer_terms = ["seller", "refund", "online order", "consumer", "defective product", "company complaint", "consumer court"]
    medical_terms = ["doctor", "hospital complaint", "medical complaint", "health complaint", "hospital overcharge"]

    if any(w in t for w in police_terms):
        return ("other_public_service", "police", "police_or_crime")
    if any(w in t for w in legal_terms):
        return ("other_public_service", "legal", "legal_help")
    if any(w in t for w in consumer_terms):
        return ("other_public_service", "consumer", "consumer_grievance")
    if any(w in t for w in medical_terms):
        return ("other_public_service", "medical", "health_service")

    return None


def route_municipal_issue(category: str) -> dict:
    key = (category or "unknown").strip().lower()
    return ROUTING_RULES.get(key, ROUTING_RULES["unknown"])

