import base64
import io
import json
import logging
import os
import secrets
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("civicresolve.backend")

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.db import (
    init_db, 
    get_complaint, 
    list_complaints, 
    update_status, 
    get_history,
    get_supporting_reports,
    update_simulated_time,
    save_ai_verification,
    save_citizen_confirmation,
    save_evidence,
    update_initial_evidence
)
from core.orchestrator import process_complaint
from core.voice import transcribe_audio
from core.sla import evaluate_sla_state
from core.escalation import record_escalation, get_escalations
from core.resolution_verifier import verify_resolution_evidence
from core.location import calculate_haversine_distance, parse_location

app = FastAPI(
    title="CivicResolve AI API",
    description="FastAPI Backend for CivicResolve AI Civic Triage and Routing Engine",
    version="0.2.0",
)

# Configure CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()


class StatusUpdateRequest(BaseModel):
    status: str
    note: Optional[str] = ""


class CitizenConfirmationRequest(BaseModel):
    resolved: bool
    comment: Optional[str] = ""


class SimulateTimeRequest(BaseModel):
    hours: int = 24



# ------------------------------------------------------------------
# Authority Command Center Authentication
# ------------------------------------------------------------------

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "").strip()
ADMIN_EMAIL_2 = os.getenv("ADMIN_EMAIL_2", "").strip()
ADMIN_PASSWORD_2 = os.getenv("ADMIN_PASSWORD_2", "").strip()


class AdminLoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/admin/login")
def admin_login(payload: AdminLoginRequest):
    """
    Authenticate CivicResolve Authority Command Center users.
    """

    admin_credentials = []

    if ADMIN_EMAIL and ADMIN_PASSWORD:
        admin_credentials.append((ADMIN_EMAIL, ADMIN_PASSWORD))

    if ADMIN_EMAIL_2 and ADMIN_PASSWORD_2:
        admin_credentials.append((ADMIN_EMAIL_2, ADMIN_PASSWORD_2))

    if not admin_credentials:
        raise HTTPException(
            status_code=503,
            detail="Authority authentication is not configured."
        )

    submitted_email = payload.email.strip().lower()
    submitted_password = payload.password

    matched_email = None
    for configured_email, configured_password in admin_credentials:
        email_valid = secrets.compare_digest(
            submitted_email,
            configured_email.lower()
        )
        password_valid = secrets.compare_digest(
            submitted_password,
            configured_password
        )
        if email_valid and password_valid:
            matched_email = configured_email
            break

    if matched_email is not None:
        return {
            "authenticated": True,
            "token": "cr_auth_" + secrets.token_hex(16),
            "user": {
                "email": matched_email,
                "name": "Municipal Chief Commissioner",
                "role": "MUNICIPAL_ADMIN"
            }
        }

    raise HTTPException(
        status_code=401,
        detail="Invalid authority credentials. Access denied."
    )


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": "CivicResolve AI",
        "version": "0.2.0",
        "tagline": "One place to report. Intelligence to route. Accountability until resolution.",
        "demo_mode": os.getenv("DEMO_MODE", "false").lower() == "true",
    }


@app.post("/api/complaints")
async def create_complaint(
    request: Request,
    complaint_text: Optional[str] = Form(None),
    location_text: Optional[str] = Form(""),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    citizen_name: Optional[str] = Form(""),
    source_channel: Optional[str] = Form("web"),
    language_hint: Optional[str] = Form(""),
    image: Optional[UploadFile] = File(None),
):
    """
    Accepts both multipart/form-data (with optional image file) and application/json.
    Coordinates AI parsing, location normalization, duplicate detection, risk scoring, and SLA.
    """
    content_type = request.headers.get("content-type", "")
    image_bytes = None
    image_mime = "image/jpeg"

    if "application/json" in content_type:
        try:
            body = await request.json()
            c_text = body.get("complaint_text", "")
            l_text = body.get("location_text", "")
            lat = body.get("latitude")
            lon = body.get("longitude")
            name = body.get("citizen_name", "")
            channel = body.get("source_channel", "web")
            lang = body.get("language_hint", "")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {e}")
    else:
        c_text = complaint_text or ""
        l_text = location_text or ""
        lat = latitude
        lon = longitude
        name = citizen_name or ""
        channel = source_channel or "web"
        lang = language_hint or ""

        if image:
            image_bytes = await image.read()
            image_mime = image.content_type or "image/jpeg"

    if not c_text.strip() and not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Either complaint_text or an evidence image must be provided.",
        )

    result = process_complaint(
        complaint_text=c_text.strip() or "Citizen submitted image evidence without text.",
        location_text=l_text.strip(),
        latitude=lat,
        longitude=lon,
        source_channel=channel.strip() or "web",
        citizen_name=name.strip(),
        image_bytes=image_bytes,
        image_mime=image_mime,
        language_hint=lang.strip(),
    )

    # Attach live SLA status
    sla_info = evaluate_sla_state(result)
    result["sla_info"] = sla_info

    return result


@app.get("/api/complaints/{complaint_id}")
def fetch_complaint(complaint_id: str):
    complaint = get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint ID not found.")

    # Parse agent trace if string
    if isinstance(complaint.get("agent_trace"), str):
        try:
            complaint["agent_trace"] = json.loads(complaint["agent_trace"])
        except Exception:
            complaint["agent_trace"] = []

    # Parse AI verification result if present
    if isinstance(complaint.get("ai_verification_result"), str):
        try:
            complaint["ai_verification_result"] = json.loads(complaint["ai_verification_result"])
        except Exception:
            complaint["ai_verification_result"] = None

    # Parse citizen confirmation if present
    if isinstance(complaint.get("citizen_confirmation"), str):
        try:
            complaint["citizen_confirmation"] = json.loads(complaint["citizen_confirmation"])
        except Exception:
            complaint["citizen_confirmation"] = None

    # Attach history, supporting reports, escalations, and live SLA evaluation
    complaint["history"] = get_history(complaint_id)
    complaint["supporting_reports"] = get_supporting_reports(complaint_id)
    complaint["escalations"] = get_escalations(complaint_id)
    complaint["sla_info"] = evaluate_sla_state(complaint)

    return complaint


@app.get("/api/admin/complaints")
def fetch_all_complaints(limit: int = 200):
    rows = list_complaints(limit=limit)
    for r in rows:
        if isinstance(r.get("agent_trace"), str):
            try:
                r["agent_trace"] = json.loads(r["agent_trace"])
            except Exception:
                r["agent_trace"] = []
        if isinstance(r.get("ai_verification_result"), str):
            try:
                r["ai_verification_result"] = json.loads(r["ai_verification_result"])
            except Exception:
                r["ai_verification_result"] = None
        r["sla_info"] = evaluate_sla_state(r)
    return rows


@app.put("/api/complaints/{complaint_id}/status")
def change_complaint_status(complaint_id: str, payload: StatusUpdateRequest):
    try:
        success = update_status(complaint_id, payload.status, payload.note or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not success:
        raise HTTPException(status_code=404, detail="Complaint ID not found or update failed.")
    return fetch_complaint(complaint_id)


@app.post("/api/admin/complaints/{complaint_id}/complete-work")
async def complete_work(
    complaint_id: str,
    request: Request,
    completion_note: Optional[str] = Form(None),
    resolution_image: Optional[UploadFile] = File(None),
    resolution_image_url: Optional[str] = Form(None),
    completed_by: Optional[str] = Form("")
):
    """
    Dedicated Municipal Complaint Completion Workflow Endpoint.
    1. Validates complaint state (must be ASSIGNED, WORK_STARTED, or REOPENED).
    2. Enforces required completion notes and captures resolution evidence image.
    3. Transitions status through RESOLUTION_SUBMITTED -> AI_VERIFICATION_PENDING.
    4. Runs Multimodal AI verification engine (core/resolution_verifier.py).
    5. Sets status to RESOLVED_PENDING_CITIZEN, REOPENED, or HUMAN_REVIEW_REQUIRED based on AI verdict.
    """
    complaint = get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint ID not found.")

    curr_status = complaint.get("status", "")
    allowed_statuses = {"ASSIGNED", "WORK_STARTED", "REOPENED"}
    if curr_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit work completion for complaint in status '{curr_status}'. Work completion is only permitted from: ASSIGNED, WORK_STARTED, or REOPENED."
        )

    # Check for JSON request payload fallback
    content_type = request.headers.get("content-type", "")
    note_val = completion_note
    worker_val = completed_by or ""
    res_url_val = resolution_image_url

    if "application/json" in content_type:
        try:
            body = await request.json()
            note_val = body.get("completion_note", "")
            worker_val = body.get("completed_by", "")
            res_url_val = body.get("resolution_image_url", "")
        except Exception:
            pass

    if not note_val or not str(note_val).strip():
        raise HTTPException(
            status_code=400,
            detail="Completion note is required to submit work completion."
        )

    note_clean = str(note_val).strip()
    worker_clean = str(worker_val).strip()

    # Process resolution image
    img_bytes = None
    final_res_url = res_url_val or ""

    if resolution_image:
        img_bytes = await resolution_image.read()
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        final_res_url = f"data:{resolution_image.content_type or 'image/jpeg'};base64,{b64}"

    # 1. First record status transition to RESOLUTION_SUBMITTED
    update_status(
        complaint_id=complaint_id,
        new_status="RESOLUTION_SUBMITTED",
        note=f"Work marked completed by {worker_clean or 'Municipal Field Crew'}: {note_clean}",
        force=True
    )

    # 2. Run multimodal resolution verifier pipeline
    verification = verify_resolution_evidence(
        complaint_category=complaint.get("category", "roads"),
        complaint_text=complaint.get("complaint_text", ""),
        resolution_image_bytes=img_bytes,
        resolution_image_url=final_res_url,
        authority_notes=note_clean
    )

    # 3. Save AI verification and outcome status
    save_ai_verification(
        complaint_id=complaint_id,
        verification=verification,
        resolution_img_url=final_res_url,
        completion_note=note_clean,
        completed_by=worker_clean
    )

    # 4. Save resolution evidence record
    ev_metadata = json.dumps({
        "note": note_clean,
        "completed_by": worker_clean,
        "verification": verification
    })
    save_evidence(complaint_id, "RESOLUTION", final_res_url, ev_metadata)

    return fetch_complaint(complaint_id)




@app.post("/api/complaints/{complaint_id}/evidence")
async def attach_citizen_evidence(
    complaint_id: str,
    image: Optional[UploadFile] = File(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    gps_accuracy: Optional[float] = Form(None),
    location_confirmed: bool = Form(False),
):
    """
    Attach optional citizen photo and/or confirmed browser GPS
    to an already-existing complaint.

    This never creates a new complaint.
    """

    complaint = get_complaint(complaint_id)

    if not complaint:
        raise HTTPException(
            status_code=404,
            detail="Complaint ID not found.",
        )

    if complaint.get("domain") != "municipal":
        raise HTTPException(
            status_code=400,
            detail=(
                "Citizen evidence attachment is only "
                "available for municipal complaints."
            ),
        )

    image_url = None
    image_saved = False
    location_saved = False

    # -----------------------------------------------------
    # OPTIONAL PHOTO
    # -----------------------------------------------------

    if image:
        allowed_types = {
            "image/jpeg",
            "image/png",
            "image/webp",
        }

        mime = (
            image.content_type
            or "application/octet-stream"
        ).lower()

        if mime not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported image format. "
                    "Please upload JPEG, PNG, or WebP."
                ),
            )

        img_bytes = await image.read()

        if not img_bytes:
            raise HTTPException(
                status_code=400,
                detail="Uploaded image is empty.",
            )

        max_image_bytes = 8 * 1024 * 1024

        if len(img_bytes) > max_image_bytes:
            raise HTTPException(
                status_code=413,
                detail="Evidence image must be 8 MB or smaller.",
            )

        b64 = base64.b64encode(
            img_bytes
        ).decode("utf-8")

        image_url = (
            f"data:{mime};base64,{b64}"
        )

        save_evidence(
            complaint_id,
            "INITIAL",
            image_url,
            json.dumps({
                "source": "citizen_evidence_link",
                "mime_type": mime,
                "size_bytes": len(img_bytes),
            }),
        )

        image_saved = True

    # -----------------------------------------------------
    # OPTIONAL CONFIRMED GPS
    # -----------------------------------------------------

    if (
        latitude is not None
        or longitude is not None
    ):
        if (
            latitude is None
            or longitude is None
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Both latitude and longitude "
                    "must be provided together."
                ),
            )

        try:
            lat = float(latitude)
            lon = float(longitude)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Invalid GPS coordinates.",
            )

        if not (-90 <= lat <= 90):
            raise HTTPException(
                status_code=400,
                detail="Latitude is outside the valid range.",
            )

        if not (-180 <= lon <= 180):
            raise HTTPException(
                status_code=400,
                detail="Longitude is outside the valid range.",
            )

        if location_confirmed:
            loc_data = parse_location(
                complaint.get(
                    "location_text",
                    "",
                ),
                latitude=lat,
                longitude=lon,
            )

            update_initial_evidence(
                complaint_id=complaint_id,
                latitude=loc_data["latitude"],
                longitude=loc_data["longitude"],
                jurisdiction=loc_data["jurisdiction"],
                location_verified=True,
            )

            accuracy = None

            if gps_accuracy is not None:
                try:
                    accuracy = max(
                        0.0,
                        float(gps_accuracy),
                    )
                except (TypeError, ValueError):
                    accuracy = None

            save_evidence(
                complaint_id,
                "LOCATION",
                (
                    f"geo:{loc_data['latitude']},"
                    f"{loc_data['longitude']}"
                ),
                json.dumps({
                    "source": "citizen_evidence_link",
                    "confirmed": True,
                    "gps_accuracy_meters": accuracy,
                    "jurisdiction": (
                        loc_data["jurisdiction"]
                    ),
                }),
            )

            location_saved = True

    # -----------------------------------------------------
    # UPDATE INITIAL PHOTO FIELD
    # -----------------------------------------------------

    if image_url:
        update_initial_evidence(
            complaint_id=complaint_id,
            initial_image_url=image_url,
        )

    if not image_saved and not location_saved:
        raise HTTPException(
            status_code=400,
            detail=(
                "No evidence was attached. "
                "Upload a photo or confirm a GPS location."
            ),
        )

    return {
        "status": "ok",
        "complaint_id": complaint_id,
        "image_saved": image_saved,
        "location_saved": location_saved,
        "complaint": fetch_complaint(
            complaint_id
        ),
    }


@app.post("/api/complaints/{complaint_id}/citizen-confirmation")
def citizen_confirm(complaint_id: str, payload: CitizenConfirmationRequest):
    """
    Allows citizens to confirm or reject field resolution.
    """
    success = save_citizen_confirmation(complaint_id, payload.resolved, payload.comment or "")
    if not success:
        raise HTTPException(status_code=404, detail="Complaint ID not found.")
    return fetch_complaint(complaint_id)


@app.post("/api/admin/run-sla-check")
def run_sla_check():
    """
    Evaluates SLA deadlines across all open municipal complaints.
    Automatically flags breached cases and escalates tiers deterministically.
    """
    complaints = list_complaints(limit=300)
    evaluated = []
    breached_count = 0
    escalated_count = 0

    for c in complaints:
        if c.get("domain") == "municipal" and c.get("status") not in {"CLOSED", "RESOLUTION_SUBMITTED", "RESOLVED_PENDING_CITIZEN"}:
            sla_info = evaluate_sla_state(c)
            cid = c["complaint_id"]
            
            if sla_info["is_breached"]:
                breached_count += 1
                curr_level = c.get("escalation_level", 0) or 0
                new_level = min(3, curr_level + 1)
                
                if new_level > curr_level:
                    record_escalation(
                        complaint_id=cid,
                        new_level=new_level,
                        reason=f"SLA threshold exceeded by {abs(sla_info['hours_remaining'])}h (Effective: {sla_info['effective_elapsed_hours']}h / Max: {c.get('sla_hours', 24)}h)"
                    )
                    escalated_count += 1

            evaluated.append({"complaint_id": cid, "sla_state": sla_info["sla_state"], "percent_consumed": sla_info["percent_consumed"]})

    return {
        "status": "success",
        "evaluated_count": len(evaluated),
        "breached_count": breached_count,
        "newly_escalated": escalated_count,
        "details": evaluated
    }


@app.post("/api/admin/complaints/{complaint_id}/simulate-time")
def simulate_time(complaint_id: str, payload: Optional[SimulateTimeRequest] = Body(None), hours: Optional[int] = Query(None)):
    """
    Demo / Expo mode time simulator.
    Advances virtual time for testing SLA warnings, breaches, and automatic escalations.
    """
    hours_to_add = hours if hours is not None else (payload.hours if payload else 24)
    updated = update_simulated_time(complaint_id, hours_to_add)
    if not updated:
        raise HTTPException(status_code=404, detail="Complaint ID not found.")

    # Evaluate SLA after simulation
    sla_info = evaluate_sla_state(updated)
    if sla_info["is_breached"]:
        curr_level = updated.get("escalation_level", 0) or 0
        new_level = min(3, curr_level + 1)
        record_escalation(
            complaint_id=complaint_id,
            new_level=new_level,
            reason=f"Demo Time Simulation: +{hours_to_add}h elapsed triggered automatic tier escalation."
        )

    return fetch_complaint(complaint_id)


@app.post("/api/admin/complaints/{complaint_id}/verify-resolution")
async def verify_resolution(
    complaint_id: str,
    notes: Optional[str] = Form(""),
    resolution_image: Optional[UploadFile] = File(None),
    resolution_image_url: Optional[str] = Form(None)
):
    """
    Multimodal AI Resolution Verification Endpoint.
    Compares initial complaint evidence against field resolution image.
    """
    complaint = get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint ID not found.")

    img_bytes = None
    final_res_url = resolution_image_url or ""
    
    if resolution_image:
        img_bytes = await resolution_image.read()
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        final_res_url = f"data:{resolution_image.content_type or 'image/jpeg'};base64,{b64}"

    # Perform AI Resolution Verification
    verification = verify_resolution_evidence(
        complaint_category=complaint.get("category", "roads"),
        complaint_text=complaint.get("complaint_text", ""),
        resolution_image_bytes=img_bytes,
        resolution_image_url=final_res_url,
        authority_notes=notes or "Repairs verified completed on site."
    )

    save_ai_verification(complaint_id, verification, final_res_url)
    save_evidence(complaint_id, "RESOLUTION", final_res_url, f"Resolution evidence: {verification.get('summary')}")

    return fetch_complaint(complaint_id)


@app.post("/api/voice/transcribe")
async def voice_transcribe(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None)
):
    """
    Transcribes audio using Groq Whisper STT via core/voice.py.
    Accepts audio upload and optional language code (e.g. en, te, hi, ta, kn).
    Returns {"success": bool, "transcript": str, "text": str, "detected_language": str, "language": str}.
    """
    try:
        if not audio:
            raise HTTPException(status_code=400, detail="No audio file uploaded.")

        audio_bytes = await audio.read()
        if not audio_bytes or len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio recording received. Please speak into the microphone and record again.")

        filename = audio.filename or "voice.webm"
        content_type = audio.content_type or "audio/webm"
        
        print("VOICE LANGUAGE SELECTED:", language, flush=True)
        print("AUDIO MIME:", content_type, flush=True)
        print("AUDIO SIZE:", len(audio_bytes), flush=True)
        
        logger.info(
            f"Received voice transcription request: filename='{filename}', content_type='{content_type}', bytes={len(audio_bytes)}, language='{language}'"
        )

        audio_stream = io.BytesIO(audio_bytes)
        transcription = transcribe_audio(
            audio_stream, 
            filename=filename, 
            language=language
        )
        return transcription
    except HTTPException:
        raise
    except Exception as e:
        print("GROQ TRANSCRIPTION EXCEPTION:", str(e), flush=True)
        logger.error(f"Voice transcription error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Voice transcription failed: {str(e)}")


@app.get("/api/admin/analytics")
def get_analytics():
    """
    Aggregates municipal command center analytics, department KPIs, and geographic hotspots.
    """
    complaints = list_complaints(limit=300)
    
    total = len(complaints)
    municipal = [c for c in complaints if c.get("domain") == "municipal"]
    open_cases = [c for c in municipal if c.get("status") not in {"CLOSED", "REJECTED"}]
    critical_cases = [c for c in open_cases if c.get("priority") == "CRITICAL"]
    resolved_today = [c for c in municipal if c.get("status") in {"CLOSED", "RESOLVED_PENDING_CITIZEN"}]

    breached_count = 0
    for c in open_cases:
        if evaluate_sla_state(c)["is_breached"]:
            breached_count += 1

    # Issues by Category
    cat_counts = {}
    for c in municipal:
        cat = (c.get("category") or "unknown").upper()
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    # Department Performance KPIs
    dept_stats = {}
    for c in municipal:
        dept = c.get("department") or "General Works"
        if dept not in dept_stats:
            dept_stats[dept] = {"total": 0, "open": 0, "resolved": 0, "breached": 0, "total_sla_hours": 0}
        
        dept_stats[dept]["total"] += 1
        is_open = c.get("status") not in {"CLOSED", "REJECTED"}
        if is_open:
            dept_stats[dept]["open"] += 1
            if evaluate_sla_state(c)["is_breached"]:
                dept_stats[dept]["breached"] += 1
        else:
            dept_stats[dept]["resolved"] += 1
        
        dept_stats[dept]["total_sla_hours"] += (c.get("sla_hours", 24) or 24)

    # Compute SLA compliance percentage
    for dept, s in dept_stats.items():
        total_open = s["open"]
        s["sla_compliance"] = round(100.0 - ((s["breached"] / total_open * 100.0) if total_open > 0 else 0.0), 1)
        s["avg_sla_hours"] = round(s["total_sla_hours"] / max(1, s["total"]), 1)

    # Geographic Hotspot Clustering
    hotspots = []
    jurisdiction_clusters = {}
    for c in open_cases:
        jur = c.get("jurisdiction") or "Central Municipal Zone"
        if jur not in jurisdiction_clusters:
            jurisdiction_clusters[jur] = {
                "jurisdiction": jur,
                "latitude": c.get("latitude", 16.306),
                "longitude": c.get("longitude", 80.436),
                "count": 0,
                "categories": {},
                "max_risk": 0,
                "critical_count": 0
            }
        
        cl = jurisdiction_clusters[jur]
        cl["count"] += 1
        cat = c.get("category", "roads")
        cl["categories"][cat] = cl["categories"].get(cat, 0) + 1
        cl["max_risk"] = max(cl["max_risk"], c.get("risk_score", 0))
        if c.get("priority") == "CRITICAL":
            cl["critical_count"] += 1

    for jur, cl in jurisdiction_clusters.items():
        top_cat = max(cl["categories"].items(), key=lambda x: x[1])[0] if cl["categories"] else "roads"
        hotspots.append({
            "area": jur,
            "latitude": cl["latitude"],
            "longitude": cl["longitude"],
            "radius_m": min(500, 150 + cl["count"] * 50),
            "complaint_count": cl["count"],
            "top_category": top_cat,
            "max_risk": cl["max_risk"],
            "critical_count": cl["critical_count"]
        })

    hotspots.sort(key=lambda x: (x["critical_count"], x["complaint_count"]), reverse=True)

    return {
        "summary": {
            "total_complaints": total,
            "open_cases": len(open_cases),
            "critical_cases": len(critical_cases),
            "sla_breaches": breached_count,
            "resolved_today": len(resolved_today),
        },
        "issues_by_category": cat_counts,
        "department_performance": dept_stats,
        "hotspots": hotspots
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
