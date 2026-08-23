from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

# Base SLA hours matrix: [Category][Priority]
SLA_MATRIX = {
    "roads": {"CRITICAL": 12, "HIGH": 24, "MEDIUM": 48, "LOW": 72},
    "water": {"CRITICAL": 6, "HIGH": 12, "MEDIUM": 24, "LOW": 48},
    "drainage": {"CRITICAL": 8, "HIGH": 18, "MEDIUM": 36, "LOW": 72},
    "garbage": {"CRITICAL": 12, "HIGH": 24, "MEDIUM": 48, "LOW": 72},
    "streetlights": {"CRITICAL": 12, "HIGH": 24, "MEDIUM": 48, "LOW": 96},
    "public_infrastructure": {"CRITICAL": 24, "HIGH": 48, "MEDIUM": 96, "LOW": 168},
    "unknown": {"CRITICAL": 12, "HIGH": 24, "MEDIUM": 48, "LOW": 72},
}


def get_sla_hours(category: str, priority: str) -> int:
    """
    Returns deterministic SLA hours based on category and priority tier.
    """
    cat_clean = (category or "unknown").lower()
    prio_clean = (priority or "MEDIUM").upper()
    cat_dict = SLA_MATRIX.get(cat_clean, SLA_MATRIX["unknown"])
    return cat_dict.get(prio_clean, 48)


def calculate_sla_deadline(created_at_iso: str, sla_hours: int) -> str:
    """
    Computes ISO deadline timestamp given creation time and SLA hours.
    """
    try:
        dt = datetime.fromisoformat(created_at_iso.replace("Z", "+00:00"))
    except Exception:
        dt = datetime.now(timezone.utc)
    
    deadline_dt = dt + timedelta(hours=sla_hours)
    return deadline_dt.isoformat()


def evaluate_sla_state(complaint: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates current SLA consumption and state (ON_TRACK, WARNING, BREACHED, ESCALATED).
    Incorporates demo simulated_hours_offset without altering system clock.
    """
    status = complaint.get("status", "NEW")
    if status in {"CLOSED", "RESOLUTION_SUBMITTED", "EXTERNALLY_ROUTED", "REJECTED"}:
        return {
            "sla_state": "ON_TRACK",
            "hours_remaining": 0.0,
            "percent_consumed": 100.0,
            "is_breached": False,
            "escalation_level": complaint.get("escalation_level", 0),
            "simulated_offset": complaint.get("simulated_hours_offset", 0)
        }

    sla_hours = complaint.get("sla_hours", 24) or 24
    created_at_str = complaint.get("created_at") or datetime.now(timezone.utc).isoformat()
    
    try:
        created_dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
    except Exception:
        created_dt = datetime.now(timezone.utc)

    sim_offset = float(complaint.get("simulated_hours_offset", 0) or 0)
    now_dt = datetime.now(timezone.utc)
    
    # Effective elapsed time = real elapsed time + simulated offset
    real_elapsed_hours = (now_dt - created_dt).total_seconds() / 3600.0
    effective_elapsed = real_elapsed_hours + sim_offset
    
    hours_remaining = max(0.0, sla_hours - effective_elapsed)
    percent_consumed = min(500.0, (effective_elapsed / sla_hours) * 100.0)
    
    escalation_level = complaint.get("escalation_level", 0) or 0

    if effective_elapsed > sla_hours:
        sla_state = "ESCALATED" if escalation_level > 0 else "BREACHED"
        is_breached = True
    elif percent_consumed >= 75.0:
        sla_state = "WARNING"
        is_breached = False
    else:
        sla_state = "ON_TRACK"
        is_breached = False

    return {
        "sla_state": sla_state,
        "hours_remaining": round(hours_remaining, 1),
        "percent_consumed": round(percent_consumed, 1),
        "is_breached": is_breached,
        "effective_elapsed_hours": round(effective_elapsed, 1),
        "escalation_level": escalation_level,
        "simulated_offset": sim_offset
    }
