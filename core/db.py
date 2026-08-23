import json
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from .config import DB_PATH


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as conn:
        # 1. Primary complaints table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id TEXT PRIMARY KEY,
            source_channel TEXT NOT NULL,
            citizen_name TEXT,
            complaint_text TEXT NOT NULL,
            location_text TEXT,
            latitude REAL,
            longitude REAL,
            location_verified INTEGER DEFAULT 0,
            jurisdiction TEXT,
            language TEXT,
            domain TEXT,
            service_type TEXT,
            category TEXT,
            subcategory TEXT,
            summary TEXT,
            confidence REAL,
            risk_score INTEGER,
            priority TEXT,
            department TEXT,
            sla_hours INTEGER,
            sla_deadline TEXT,
            sla_state TEXT DEFAULT 'ON_TRACK',
            escalation_level INTEGER DEFAULT 0,
            simulated_hours_offset INTEGER DEFAULT 0,
            report_count INTEGER DEFAULT 1,
            parent_complaint_id TEXT,
            status TEXT,
            external_service_name TEXT,
            external_service_url TEXT,
            initial_image_url TEXT,
            resolution_image_url TEXT,
            resolution_summary TEXT,
            ai_verification_result TEXT,
            citizen_confirmation TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            agent_trace TEXT
        )
        """)

        # 2. Status history table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            note TEXT,
            changed_at TEXT NOT NULL
        )
        """)

        # 3. Escalations table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT NOT NULL,
            level INTEGER NOT NULL,
            reason TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        # 4. Evidence table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT NOT NULL,
            type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            metadata TEXT,
            created_at TEXT NOT NULL
        )
        """)

        # 5. Supporting reports (duplicates) table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS supporting_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_complaint_id TEXT NOT NULL,
            citizen_name TEXT,
            complaint_text TEXT,
            location_text TEXT,
            source_channel TEXT,
            image_url TEXT,
            similarity REAL,
            created_at TEXT NOT NULL
        )
        """)

        # 6. Safe idempotent column migrations for existing SQLite databases
        existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(complaints)").fetchall()}
        new_cols = {
            "latitude": "REAL",
            "longitude": "REAL",
            "location_verified": "INTEGER DEFAULT 0",
            "jurisdiction": "TEXT",
            "sla_deadline": "TEXT",
            "sla_state": "TEXT DEFAULT 'ON_TRACK'",
            "escalation_level": "INTEGER DEFAULT 0",
            "simulated_hours_offset": "INTEGER DEFAULT 0",
            "report_count": "INTEGER DEFAULT 1",
            "parent_complaint_id": "TEXT",
            "initial_image_url": "TEXT",
            "resolution_image_url": "TEXT",
            "resolution_summary": "TEXT",
            "ai_verification_result": "TEXT",
            "citizen_confirmation": "TEXT",
        }

        for col, col_type in new_cols.items():
            if col not in existing_cols:
                conn.execute(f"ALTER TABLE complaints ADD COLUMN {col} {col_type}")

        conn.commit()


def save_complaint(c: dict):
    now = datetime.now(timezone.utc).isoformat()
    sla_hours = c.get("sla_hours", 24) or 24
    sla_deadline = c.get("sla_deadline")
    if not sla_deadline:
        deadline_dt = datetime.now(timezone.utc) + timedelta(hours=sla_hours)
        sla_deadline = deadline_dt.isoformat()

    with _conn() as conn:
        conn.execute("""
        INSERT OR REPLACE INTO complaints (
            complaint_id, source_channel, citizen_name, complaint_text,
            location_text, latitude, longitude, location_verified, jurisdiction,
            language, domain, service_type, category, subcategory,
            summary, confidence, risk_score, priority, department,
            sla_hours, sla_deadline, sla_state, escalation_level, simulated_hours_offset,
            report_count, parent_complaint_id,
            status, external_service_name, external_service_url,
            initial_image_url, resolution_image_url, resolution_summary,
            ai_verification_result, citizen_confirmation,
            created_at, updated_at, agent_trace
        ) VALUES (
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?,
            ?, ?, ?
        )
        """, (
            c["complaint_id"], c.get("source_channel", "web"),
            c.get("citizen_name", ""), c.get("complaint_text", ""),
            c.get("location_text", ""), c.get("latitude"), c.get("longitude"),
            1 if c.get("location_verified") else 0, c.get("jurisdiction", ""),
            c.get("language", "English"),
            c.get("domain", "unknown"), c.get("service_type", "other"),
            c.get("category", "unknown"), c.get("subcategory", ""),
            c.get("summary", ""), c.get("confidence", 0),
            c.get("risk_score", 0), c.get("priority", "LOW"),
            c.get("department", ""), c.get("sla_hours", 0),
            sla_deadline, c.get("sla_state", "ON_TRACK"),
            c.get("escalation_level", 0), c.get("simulated_hours_offset", 0),
            c.get("report_count", 1) or 1, c.get("parent_complaint_id"),
            c.get("status", "NEW"),
            c.get("external_service_name", ""),
            c.get("external_service_url", ""),
            c.get("initial_image_url", ""),
            c.get("resolution_image_url", ""),
            c.get("resolution_summary", ""),
            json.dumps(c.get("ai_verification_result")) if c.get("ai_verification_result") else None,
            json.dumps(c.get("citizen_confirmation")) if c.get("citizen_confirmation") else None,
            c.get("created_at", now), now,
            json.dumps(c.get("agent_trace", []), ensure_ascii=False),
        ))

        # Initial status history log if new
        conn.execute("""
        INSERT INTO status_history (complaint_id, old_status, new_status, note, changed_at)
        VALUES (?, ?, ?, ?, ?)
        """, (c["complaint_id"], None, c.get("status", "NEW"), "Complaint created and AI triage completed", now))

        conn.commit()


def get_complaint(complaint_id: str) -> Optional[Dict[str, Any]]:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM complaints WHERE complaint_id = ?",
            (complaint_id.strip().upper(),)
        ).fetchone()
        return dict(row) if row else None


def list_complaints(limit: int = 200) -> List[Dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute("""
            SELECT * FROM complaints
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


VALID_TRANSITIONS = {
    "NEW": {"ACKNOWLEDGED", "ASSIGNED", "REJECTED", "EXTERNALLY_ROUTED", "EMERGENCY_DISPATCHED"},
    "ACKNOWLEDGED": {"ASSIGNED", "WORK_STARTED", "REJECTED", "EXTERNALLY_ROUTED", "EMERGENCY_DISPATCHED"},
    "ASSIGNED": {"WORK_STARTED", "RESOLUTION_SUBMITTED", "ACKNOWLEDGED", "REJECTED"},
    "WORK_STARTED": {"RESOLUTION_SUBMITTED", "ASSIGNED", "REOPENED"},
    "RESOLUTION_SUBMITTED": {"AI_VERIFICATION_PENDING", "RESOLVED_PENDING_CITIZEN", "HUMAN_REVIEW_REQUIRED", "REOPENED"},
    "AI_VERIFICATION_PENDING": {"RESOLVED_PENDING_CITIZEN", "HUMAN_REVIEW_REQUIRED", "REOPENED"},
    "HUMAN_REVIEW_REQUIRED": {"RESOLVED_PENDING_CITIZEN", "REOPENED", "ASSIGNED", "WORK_STARTED", "CLOSED"},
    "RESOLVED_PENDING_CITIZEN": {"CLOSED", "REOPENED"},
    "REOPENED": {"ASSIGNED", "WORK_STARTED", "RESOLUTION_SUBMITTED"},
    "CLOSED": {"REOPENED"},
    "REJECTED": {"NEW", "REOPENED"},
    "EXTERNALLY_ROUTED": {"NEW"},
    "EMERGENCY_DISPATCHED": {"CLOSED"},
}


def validate_status_transition(old_status: Optional[str], new_status: str) -> tuple[bool, str]:
    if not old_status or old_status == new_status:
        return True, ""

    old_upper = old_status.upper()
    new_upper = new_status.upper()

    allowed = VALID_TRANSITIONS.get(old_upper)
    if allowed is None:
        return True, ""

    if new_upper not in allowed:
        return False, f"Illegal status transition from '{old_upper}' to '{new_upper}'. Allowed transitions: {sorted(list(allowed))}"

    return True, ""


def update_status(complaint_id: str, new_status: str, note: str = "", force: bool = False) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    cid = complaint_id.strip().upper()
    with _conn() as conn:
        row = conn.execute(
            "SELECT status FROM complaints WHERE complaint_id = ?",
            (cid,)
        ).fetchone()
        if not row:
            return False
        old_status = row["status"]
        if not force:
            valid, err = validate_status_transition(old_status, new_status)
            if not valid:
                raise ValueError(err)

        conn.execute("""
            UPDATE complaints
            SET status = ?, updated_at = ?
            WHERE complaint_id = ?
        """, (new_status, now, cid))
        conn.execute("""
            INSERT INTO status_history (complaint_id, old_status, new_status, note, changed_at)
            VALUES (?, ?, ?, ?, ?)
        """, (cid, old_status, new_status, note, now))
        conn.commit()
        return True


def get_history(complaint_id: str) -> List[Dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute("""
            SELECT old_status, new_status, note, changed_at
            FROM status_history
            WHERE complaint_id = ?
            ORDER BY id ASC
        """, (complaint_id,)).fetchall()
        return [dict(r) for r in rows]


def add_supporting_report(
    parent_complaint_id: str,
    citizen_name: str,
    complaint_text: str,
    location_text: str,
    source_channel: str = "web",
    image_url: str = "",
    similarity: float = 0.85
):
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as conn:
        conn.execute("""
            INSERT INTO supporting_reports (
                parent_complaint_id, citizen_name, complaint_text,
                location_text, source_channel, image_url, similarity, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            parent_complaint_id, citizen_name, complaint_text,
            location_text, source_channel, image_url, similarity, now
        ))

        # Increment report count on primary complaint
        conn.execute("""
            UPDATE complaints
            SET report_count = COALESCE(report_count, 1) + 1, updated_at = ?
            WHERE complaint_id = ?
        """, (now, parent_complaint_id))

        conn.execute("""
            INSERT INTO status_history (complaint_id, old_status, new_status, note, changed_at)
            VALUES (?, 'SUPPORTING_REPORT', 'UPDATED', ?, ?)
        """, (
            parent_complaint_id,
            f"Linked citizen report (+1). Citizen: {citizen_name or 'Anonymous'} (Similarity: {int(similarity * 100)}%)",
            now
        ))

        conn.commit()


def get_supporting_reports(parent_complaint_id: str) -> List[Dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute("""
            SELECT id, parent_complaint_id, citizen_name, complaint_text,
                   location_text, source_channel, image_url, similarity, created_at
            FROM supporting_reports
            WHERE parent_complaint_id = ?
            ORDER BY id ASC
        """, (parent_complaint_id,)).fetchall()
        return [dict(r) for r in rows]


def save_evidence(complaint_id: str, ev_type: str, file_path: str, metadata: str = ""):
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as conn:
        conn.execute("""
            INSERT INTO evidence (complaint_id, type, file_path, metadata, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (complaint_id, ev_type, file_path, metadata, now))
        conn.commit()


def get_evidence(complaint_id: str) -> List[Dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute("""
            SELECT id, complaint_id, type, file_path, metadata, created_at
            FROM evidence
            WHERE complaint_id = ?
            ORDER BY id ASC
        """, (complaint_id,)).fetchall()
        return [dict(r) for r in rows]


def update_simulated_time(complaint_id: str, additional_hours: int) -> Optional[Dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as conn:
        row = conn.execute(
            "SELECT simulated_hours_offset FROM complaints WHERE complaint_id = ?",
            (complaint_id,)
        ).fetchone()
        if not row:
            return None
        current_offset = row["simulated_hours_offset"] or 0
        new_offset = current_offset + additional_hours

        conn.execute("""
            UPDATE complaints
            SET simulated_hours_offset = ?, updated_at = ?
            WHERE complaint_id = ?
        """, (new_offset, now, complaint_id))

        conn.execute("""
            INSERT INTO status_history (complaint_id, old_status, new_status, note, changed_at)
            VALUES (?, 'SIMULATION', 'TIME_ADVANCED', ?, ?)
        """, (complaint_id, f"Demo Time Simulation: +{additional_hours}h simulated (Total offset: {new_offset}h)", now))

        conn.commit()

    return get_complaint(complaint_id)


def save_ai_verification(
    complaint_id: str,
    verification: Dict[str, Any],
    resolution_img_url: str = "",
    completion_note: str = "",
    completed_by: str = ""
):
    now = datetime.now(timezone.utc).isoformat()
    v_json = json.dumps(verification)
    
    if verification.get("requires_human_review"):
        new_status = "HUMAN_REVIEW_REQUIRED"
    elif verification.get("appears_resolved"):
        new_status = "RESOLVED_PENDING_CITIZEN"
    else:
        new_status = "REOPENED"

    cid = complaint_id.strip().upper()
    with _conn() as conn:
        conn.execute("""
            UPDATE complaints
            SET ai_verification_result = ?, resolution_image_url = ?, resolution_summary = ?, status = ?, updated_at = ?
            WHERE complaint_id = ?
        """, (v_json, resolution_img_url, verification.get("summary", ""), new_status, now, cid))

        conf_pct = int(verification.get("confidence", 0) * 100)
        note = f"AI Verification [{new_status}]: {verification.get('summary', '')} (Confidence: {conf_pct}%)"
        if completed_by:
            note = f"{note} — Completed by: {completed_by}"
        if completion_note:
            note = f"{note} — Note: {completion_note}"

        conn.execute("""
            INSERT INTO status_history (complaint_id, old_status, new_status, note, changed_at)
            VALUES (?, 'RESOLUTION_SUBMITTED', ?, ?, ?)
        """, (cid, new_status, note, now))

        conn.commit()


def save_citizen_confirmation(complaint_id: str, resolved: bool, comment: str = "") -> bool:
    now = datetime.now(timezone.utc).isoformat()
    conf_data = json.dumps({"resolved": resolved, "comment": comment, "confirmed_at": now})
    new_status = "CLOSED" if resolved else "REOPENED"
    cid = complaint_id.strip().upper()

    with _conn() as conn:
        row = conn.execute("SELECT escalation_level FROM complaints WHERE complaint_id = ?", (cid,)).fetchone()
        curr_esc = (row["escalation_level"] if row else 0) or 0
        new_esc = curr_esc + (0 if resolved else 1)

        conn.execute("""
            UPDATE complaints
            SET citizen_confirmation = ?, status = ?, escalation_level = ?,
                sla_state = CASE WHEN ? = 0 THEN 'ESCALATED' ELSE sla_state END,
                updated_at = ?
            WHERE complaint_id = ?
        """, (conf_data, new_status, new_esc, 1 if resolved else 0, now, cid))

        note = f"Citizen Confirmation: {'Confirmed resolved by citizen' if resolved else 'Citizen contested resolution — Issue still unresolved'} (Note: {comment or 'None'})"
        conn.execute("""
            INSERT INTO status_history (complaint_id, old_status, new_status, note, changed_at)
            VALUES (?, 'RESOLVED_PENDING_CITIZEN', ?, ?, ?)
        """, (cid, new_status, note, now))

        if not resolved:
            reason = f"Citizen rejected resolution on Track page: '{comment or 'Issue still persists on site'}'"
            conn.execute("""
                INSERT INTO escalations (complaint_id, level, reason, created_at)
                VALUES (?, ?, ?, ?)
            """, (cid, new_esc, reason, now))

        conn.commit()
        return True


def update_initial_evidence(
    complaint_id: str,
    initial_image_url: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    jurisdiction: Optional[str] = None,
    location_verified: Optional[bool] = None,
) -> bool:
    """
    Attach optional citizen evidence to an existing complaint
    without creating a second complaint.
    """
    complaint_id = (complaint_id or "").strip().upper()

    if not complaint_id:
        return False

    updates = []
    values = []

    if initial_image_url is not None:
        updates.append("initial_image_url = ?")
        values.append(initial_image_url)

    if latitude is not None:
        updates.append("latitude = ?")
        values.append(float(latitude))

    if longitude is not None:
        updates.append("longitude = ?")
        values.append(float(longitude))

    if jurisdiction is not None:
        updates.append("jurisdiction = ?")
        values.append(str(jurisdiction))

    if location_verified is not None:
        updates.append("location_verified = ?")
        values.append(1 if location_verified else 0)

    if not updates:
        return False

    now = datetime.now(timezone.utc).isoformat()

    updates.append("updated_at = ?")
    values.append(now)

    values.append(complaint_id)

    with _conn() as conn:
        cursor = conn.execute(
            f"""
            UPDATE complaints
            SET {", ".join(updates)}
            WHERE complaint_id = ?
            """,
            values,
        )

        conn.commit()

        return cursor.rowcount > 0
