import re
from typing import List, Dict, Any, Optional
from .db import list_complaints
from .location import calculate_haversine_distance

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to",
    "of", "for", "and", "or", "near", "my", "our", "there", "this", "that",
    "please", "help", "we", "have", "been", "here", "with", "from", "very"
}

MAX_GEODIST_METERS = 300.0  # Max distance in meters for geographic similarity


def _tokens(text: str) -> set:
    words = re.findall(r"[a-zA-Z0-9]+", (text or "").lower())
    return {w for w in words if len(w) > 2 and w not in STOPWORDS}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def calculate_geographic_similarity(
    lat1: Optional[float], lon1: Optional[float],
    lat2: Optional[float], lon2: Optional[float],
    loc_text1: str = "", loc_text2: str = ""
) -> float:
    """
    Calculates geographic similarity (0.0 to 1.0).
    Uses Haversine distance if coordinates exist, otherwise falls back to text token similarity.
    """
    if lat1 is not None and lon1 is not None and lat2 is not None and lon2 is not None:
        dist = calculate_haversine_distance(lat1, lon1, lat2, lon2)
        if dist <= 50.0:
            return 1.0
        elif dist <= MAX_GEODIST_METERS:
            # Linear decay from 1.0 at 50m to 0.0 at 300m
            return max(0.0, 1.0 - ((dist - 50.0) / (MAX_GEODIST_METERS - 50.0)))
        else:
            return 0.0

    # Fallback to textual location token overlap
    t1 = _tokens(loc_text1)
    t2 = _tokens(loc_text2)
    return _jaccard(t1, t2)


def evaluate_duplicate(
    category: str,
    complaint_text: str,
    location_text: str = "",
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    threshold: float = 0.68
) -> Dict[str, Any]:
    """
    Deterministic duplicate scoring algorithm:
    duplicate_score = 0.50 * geo_sim + 0.35 * text_sim + 0.15 * cat_sim
    """
    current_tokens = _tokens(complaint_text)
    category_clean = (category or "").lower()
    
    matches = []

    for row in list_complaints(limit=150):
        # Only check open/active municipal complaints
        if row.get("domain") != "municipal":
            continue
        if row.get("status") in {"CLOSED", "REJECTED"}:
            continue

        existing_cat = (row.get("category") or "").lower()
        if existing_cat != category_clean and existing_cat != "unknown" and category_clean != "unknown":
            continue

        # 1. Category Similarity (15%)
        cat_sim = 1.0 if existing_cat == category_clean else 0.5

        # 2. Text Similarity (35%)
        existing_tokens = _tokens(row.get("complaint_text", ""))
        text_sim = _jaccard(current_tokens, existing_tokens)

        # 3. Geographic Proximity (50%)
        geo_sim = calculate_geographic_similarity(
            latitude, longitude,
            row.get("latitude"), row.get("longitude"),
            location_text, row.get("location_text", "")
        )

        # Weighted Deterministic Score
        combined_score = (0.50 * geo_sim) + (0.35 * text_sim) + (0.15 * cat_sim)
        
        # Proximity threshold override: If within 75 meters and same category with moderate text similarity
        if geo_sim >= 0.90 and cat_sim == 1.0 and text_sim >= 0.20:
            combined_score = max(combined_score, 0.85)

        if combined_score >= threshold:
            matches.append({
                "complaint_id": row["complaint_id"],
                "similarity": round(combined_score, 2),
                "status": row.get("status", "NEW"),
                "priority": row.get("priority", "MEDIUM"),
                "category": row.get("category", ""),
                "summary": row.get("summary", ""),
                "report_count": row.get("report_count", 1) or 1,
                "created_at": row.get("created_at", "")
            })

    matches.sort(key=lambda x: x["similarity"], reverse=True)

    if matches:
        top_match = matches[0]
        return {
            "duplicate": True,
            "matched_complaint_id": top_match["complaint_id"],
            "similarity": top_match["similarity"],
            "report_count": top_match["report_count"],
            "matches": matches
        }

    return {
        "duplicate": False,
        "matched_complaint_id": None,
        "similarity": 0.0,
        "report_count": 1,
        "matches": []
    }


# Backwards compatibility alias
def find_probable_duplicates(category: str, location_text: str, complaint_text: str, threshold=0.42):
    res = evaluate_duplicate(category, complaint_text, location_text, threshold=threshold)
    return res["matches"]
