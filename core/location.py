import re
import math
from typing import Optional, Dict, Any

# Standard municipal reference landmarks and wards for expo / city bounds
KNOWN_LANDMARKS = [
    {
        "keywords": ["st. mary", "school road", "ward 14", "central zone", "st mary"],
        "address": "School Road, Near St. Mary's Gate, Ward 14 (Central Zone)",
        "latitude": 16.3065,
        "longitude": 80.4362,
        "jurisdiction": "Ward 14 (Central Zone)",
        "confidence": 0.95
    },
    {
        "keywords": ["green park", "4th cross", "ward 09", "pipeline", "green park extension"],
        "address": "4th Cross, Green Park Extension, Ward 09",
        "latitude": 16.3120,
        "longitude": 80.4410,
        "jurisdiction": "Ward 09 (Green Park)",
        "confidence": 0.94
    },
    {
        "keywords": ["sector 4b", "community center", "east zone", "4b"],
        "address": "Sector 4B, Behind Community Center, East Zone",
        "latitude": 16.3185,
        "longitude": 80.4520,
        "jurisdiction": "Sector 4B (East Zone)",
        "confidence": 0.92
    },
    {
        "keywords": ["vignan", "university", "main gate", "vadlamudi", "campus"],
        "address": "Near Main Gate, Vignan University Campus, Guntur-Tenali Road",
        "latitude": 16.2334,
        "longitude": 80.5518,
        "jurisdiction": "Ward 18 (Institutional Zone)",
        "confidence": 0.96
    },
    {
        "keywords": ["nehru park", "ward 07", "park view", "walkway"],
        "address": "Park View Avenue, Ward 07, Near Nehru Park",
        "latitude": 16.2990,
        "longitude": 80.4280,
        "jurisdiction": "Ward 07 (Nehru Park)",
        "confidence": 0.90
    },
    {
        "keywords": ["market", "ward 12", "commercial", "stormwater", "drain"],
        "address": "Main Market Road, Ward 12, Commercial Area",
        "latitude": 16.3040,
        "longitude": 80.4390,
        "jurisdiction": "Ward 12 (Market Zone)",
        "confidence": 0.91
    },
    {
        "keywords": ["south ext", "ward 03", "ashok nagar", "street 8"],
        "address": "Street 8, Block C, Ashok Nagar, Ward 03",
        "latitude": 16.2910,
        "longitude": 80.4310,
        "jurisdiction": "Ward 03 (South Ext)",
        "confidence": 0.90
    }
]

DEFAULT_CITY_CENTER = {"lat": 16.3060, "lon": 80.4360, "jurisdiction": "Central Municipal Zone"}


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in meters between two points 
    on the earth (specified in decimal degrees).
    """
    if None in (lat1, lon1, lat2, lon2):
        return float("inf")
    
    R = 6371000  # Radius of earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def parse_location(
    location_text: str = "",
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> Dict[str, Any]:
    """
    Normalizes coordinates, matches known landmarks/wards, and generates a structured location object.
    Never raises an exception or blocks complaint submission.
    """
    loc_clean = (location_text or "").strip()
    
    # 1. If explicit latitude & longitude provided by browser GPS
    if latitude is not None and longitude is not None:
        try:
            lat = float(latitude)
            lon = float(longitude)
            
            # Find closest known ward for jurisdiction mapping
            best_ward = DEFAULT_CITY_CENTER["jurisdiction"]
            min_dist = float("inf")
            for lm in KNOWN_LANDMARKS:
                dist = calculate_haversine_distance(lat, lon, lm["latitude"], lm["longitude"])
                if dist < min_dist:
                    min_dist = dist
                    best_ward = lm["jurisdiction"]

            return {
                "address": loc_clean or f"GPS: {lat:.5f}, {lon:.5f} ({best_ward})",
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "jurisdiction": best_ward,
                "location_verified": True,
                "confidence": 0.95
            }
        except (ValueError, TypeError):
            pass

    # 2. Check for coordinate pattern in location_text e.g. "16.3065, 80.4362"
    coord_match = re.search(r"(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)", loc_clean)
    if coord_match:
        try:
            lat = float(coord_match.group(1))
            lon = float(coord_match.group(2))
            return {
                "address": loc_clean,
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "jurisdiction": DEFAULT_CITY_CENTER["jurisdiction"],
                "location_verified": True,
                "confidence": 0.90
            }
        except Exception:
            pass

    # 3. Match against known city landmarks & wards
    loc_lower = loc_clean.lower()
    for lm in KNOWN_LANDMARKS:
        if any(kw in loc_lower for kw in lm["keywords"]):
            return {
                "address": loc_clean or lm["address"],
                "latitude": lm["latitude"],
                "longitude": lm["longitude"],
                "jurisdiction": lm["jurisdiction"],
                "location_verified": True,
                "confidence": lm["confidence"]
            }

    # 4. Fallback: preserve unverified location text gracefully without coordinates
    if loc_clean:
        # Extract potential ward name if mentioned
        ward_match = re.search(r"(ward\s*\d+|sector\s*\w+)", loc_lower)
        jurisdiction = ward_match.group(1).title() if ward_match else DEFAULT_CITY_CENTER["jurisdiction"]
        
        return {
            "address": loc_clean,
            "latitude": DEFAULT_CITY_CENTER["lat"],
            "longitude": DEFAULT_CITY_CENTER["lon"],
            "jurisdiction": jurisdiction,
            "location_verified": False,
            "confidence": 0.65
        }

    # 5. Empty location
    return {
        "address": "Central Municipal Ward",
        "latitude": DEFAULT_CITY_CENTER["lat"],
        "longitude": DEFAULT_CITY_CENTER["lon"],
        "jurisdiction": DEFAULT_CITY_CENTER["jurisdiction"],
        "location_verified": False,
        "confidence": 0.50
    }
