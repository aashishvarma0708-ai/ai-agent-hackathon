from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from .db import _conn

ESCALATION_TIERS = {
    0: "Assigned Field Crew",
    1: "Ward Department Supervisor",
    2: "Zonal Municipal Commissioner",
    3: "Senior City Escalation Desk"
}


def record_escalation(complaint_id: str, new_level: int, reason: str) -> Dict[str, Any]:
    """
    Persists an escalation event to the database and updates the complaint record.
    """
    now = datetime.now(timezone.utc).isoformat()
    tier_name = ESCALATION_TIERS.get(new_level, f"Escalation Level {new_level}")

    with _conn() as conn:
        conn.execute("""
            INSERT INTO escalations (complaint_id, level, reason, created_at)
            VALUES (?, ?, ?, ?)
        """, (complaint_id, new_level, reason, now))

        conn.execute("""
            UPDATE complaints
            SET escalation_level = ?, sla_state = 'ESCALATED', updated_at = ?
            WHERE complaint_id = ?
        """, (new_level, now, complaint_id))

        conn.execute("""
            INSERT INTO status_history (complaint_id, old_status, new_status, note, changed_at)
            VALUES (?, 'BREACHED', 'ESCALATED', ?, ?)
        """, (complaint_id, f"🚨 Escalated to Level {new_level} ({tier_name}). Reason: {reason}", now))

        conn.commit()

    return {
        "complaint_id": complaint_id,
        "escalation_level": new_level,
        "tier_name": tier_name,
        "reason": reason,
        "created_at": now
    }


def get_escalations(complaint_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves all escalation records for a given complaint.
    """
    with _conn() as conn:
        rows = conn.execute("""
            SELECT id, complaint_id, level, reason, created_at
            FROM escalations
            WHERE complaint_id = ?
            ORDER BY id ASC
        """, (complaint_id,)).fetchall()
        return [dict(r) for r in rows]
