import io
import json
import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from core.db import init_db, get_complaint, get_evidence, get_history, validate_status_transition, update_status

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_positive_resolution_lifecycle():
    """
    Tests complete happy path:
    NEW -> ACKNOWLEDGED -> ASSIGNED -> WORK_STARTED -> Mark Work Completed (complete-work)
    -> RESOLUTION_SUBMITTED -> AI Verification -> RESOLVED_PENDING_CITIZEN
    -> Citizen confirms -> CLOSED
    """
    uid = uuid.uuid4().hex[:6]
    # 1. Create a new municipal complaint
    create_res = client.post("/api/complaints", data={
        "complaint_text": f"Dangerous deep pothole on MG Road near bus stop {uid}.",
        "location_text": f"MG Road, Ward 12 {uid}",
        "citizen_name": "Rohan Patel",
        "source_channel": "web"
    })
    assert create_res.status_code == 200
    cid = create_res.json()["complaint_id"]
    assert create_res.json()["status"] == "NEW"

    # 2. Transition NEW -> ACKNOWLEDGED
    ack_res = client.put(f"/api/complaints/{cid}/status", json={
        "status": "ACKNOWLEDGED",
        "note": "Triage verified by ward control room."
    })
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "ACKNOWLEDGED"

    # 3. Transition ACKNOWLEDGED -> ASSIGNED
    assign_res = client.put(f"/api/complaints/{cid}/status", json={
        "status": "ASSIGNED",
        "note": "Assigned to Rapid Road Repair Unit #2."
    })
    assert assign_res.status_code == 200
    assert assign_res.json()["status"] == "ASSIGNED"

    # 4. Transition ASSIGNED -> WORK_STARTED
    work_res = client.put(f"/api/complaints/{cid}/status", json={
        "status": "WORK_STARTED",
        "note": "Crew arrived on site with asphalt leveling equipment."
    })
    assert work_res.status_code == 200
    assert work_res.json()["status"] == "WORK_STARTED"

    # 5. Submit Work Completion via dedicated endpoint
    fake_img = io.BytesIO(b"FAKE_AFTER_REPAIR_JPEG_BYTES")
    comp_res = client.post(
        f"/api/admin/complaints/{cid}/complete-work",
        data={
            "completion_note": "Pothole filled with high-grade bitumen asphalt, compacted and leveled.",
            "completed_by": "Crew Chief David"
        },
        files={"resolution_image": ("after_repair.jpg", fake_img, "image/jpeg")}
    )
    assert comp_res.status_code == 200
    comp_data = comp_res.json()

    # Status must NOT be CLOSED directly; must be RESOLVED_PENDING_CITIZEN (or AI_VERIFICATION_PENDING)
    assert comp_data["status"] == "RESOLVED_PENDING_CITIZEN"
    assert comp_data["resolution_image_url"] != ""
    assert comp_data["ai_verification_result"] is not None
    assert comp_data["ai_verification_result"]["appears_resolved"] is True

    # Check status history logs RESOLUTION_SUBMITTED and RESOLVED_PENDING_CITIZEN
    hist = get_history(cid)
    history_statuses = [h["new_status"] for h in hist]
    assert "RESOLUTION_SUBMITTED" in history_statuses
    assert "RESOLVED_PENDING_CITIZEN" in history_statuses

    # Check evidence table
    ev_rows = get_evidence(cid)
    resolution_ev = [e for e in ev_rows if e["type"] == "RESOLUTION"]
    assert len(resolution_ev) >= 1

    # 6. Citizen confirms resolution
    confirm_res = client.post(f"/api/complaints/{cid}/citizen-confirmation", json={
        "resolved": True,
        "comment": "Road is completely smooth now. Thank you!"
    })
    assert confirm_res.status_code == 200
    final_data = confirm_res.json()
    assert final_data["status"] == "CLOSED"
    assert final_data["citizen_confirmation"]["resolved"] is True


def test_citizen_rejects_resolution_and_escalates():
    """
    Tests citizen rejection path:
    WORK_STARTED -> complete-work -> RESOLVED_PENDING_CITIZEN
    -> Citizen rejects -> REOPENED + escalation level increased
    """
    uid = uuid.uuid4().hex[:6]
    create_res = client.post("/api/complaints", data={
        "complaint_text": f"Large pothole causing vehicle damage on Ring Road {uid}.",
        "location_text": f"Ring Road, Ward 8 {uid}",
        "citizen_name": "Ananya Sen"
    })
    cid = create_res.json()["complaint_id"]

    # Fast forward to WORK_STARTED
    client.put(f"/api/complaints/{cid}/status", json={"status": "ASSIGNED"})
    client.put(f"/api/complaints/{cid}/status", json={"status": "WORK_STARTED"})

    # Complete work with clear resolution notes
    fake_img = io.BytesIO(b"FAKE_AFTER_ROAD_REPAIR_JPEG_BYTES")
    comp_res = client.post(
        f"/api/admin/complaints/{cid}/complete-work",
        data={
            "completion_note": "Asphalt leveling and patch work completed over the reported pothole.",
            "completed_by": "Road Repair Crew #3"
        },
        files={"resolution_image": ("after_road_repair.jpg", fake_img, "image/jpeg")}
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "RESOLVED_PENDING_CITIZEN"

    # Citizen rejects resolution
    curr_level = comp_res.json().get("escalation_level", 0)
    reject_res = client.post(f"/api/complaints/{cid}/citizen-confirmation", json={
        "resolved": False,
        "comment": "Pothole was only partially filled, sharp edges still remain."
    })
    assert reject_res.status_code == 200
    rejected_data = reject_res.json()
    assert rejected_data["status"] == "REOPENED"
    assert rejected_data["escalation_level"] == curr_level + 1
    assert len(rejected_data["escalations"]) >= 1


def test_illegal_status_transitions_rejected():
    """
    Validates that invalid status transitions (e.g. ACKNOWLEDGED -> CLOSED) are rejected with 400.
    """
    uid = uuid.uuid4().hex[:6]
    create_res = client.post("/api/complaints", data={
        "complaint_text": f"Streetlight flickering at corner {uid}.",
        "location_text": f"Park Ave {uid}"
    })
    cid = create_res.json()["complaint_id"]

    # Direct NEW -> CLOSED is illegal
    bad_res = client.put(f"/api/complaints/{cid}/status", json={"status": "CLOSED"})
    assert bad_res.status_code == 400
    assert "Illegal status transition" in bad_res.json()["detail"]

    # Move to ACKNOWLEDGED
    client.put(f"/api/complaints/{cid}/status", json={"status": "ACKNOWLEDGED"})

    # Direct ACKNOWLEDGED -> CLOSED is illegal
    bad_res2 = client.put(f"/api/complaints/{cid}/status", json={"status": "CLOSED"})
    assert bad_res2.status_code == 400
    assert "Illegal status transition" in bad_res2.json()["detail"]

    # Complete work on ACKNOWLEDGED without ASSIGNED/WORK_STARTED should be rejected
    bad_work = client.post(
        f"/api/admin/complaints/{cid}/complete-work",
        data={"completion_note": "All done."}
    )
    assert bad_work.status_code == 400
    assert "Cannot submit work completion" in bad_work.json()["detail"]


def test_ai_verification_rejection_heuristic():
    """
    Tests that if completion notes contain reject/unresolved signals,
    AI verification marks appears_resolved=False and sets status to REOPENED or HUMAN_REVIEW_REQUIRED.
    """
    uid = uuid.uuid4().hex[:6]
    create_res = client.post("/api/complaints", data={
        "complaint_text": f"Sewer blockage causing overflow {uid}.",
        "location_text": f"Market Road {uid}"
    })
    cid = create_res.json()["complaint_id"]

    client.put(f"/api/complaints/{cid}/status", json={"status": "ASSIGNED"})
    client.put(f"/api/complaints/{cid}/status", json={"status": "WORK_STARTED"})

    comp_res = client.post(
        f"/api/admin/complaints/{cid}/complete-work",
        data={
            "completion_note": "Inspection completed but pending parts, blocked pipeline cannot fix today.",
            "completed_by": "Drainage Team"
        }
    )
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["status"] in {"REOPENED", "HUMAN_REVIEW_REQUIRED"}
    assert comp_data["ai_verification_result"]["appears_resolved"] is False


def test_generic_notes_do_not_auto_change_status():
    """
    Ensures typing words like 'finished', 'done', 'fixed' in routine update notes
    does NOT automatically jump to CLOSED or RESOLUTION_SUBMITTED.
    """
    uid = uuid.uuid4().hex[:6]
    create_res = client.post("/api/complaints", data={
        "complaint_text": f"Illegal commercial poster banner affixed on streetlamp {uid}.",
        "location_text": f"Remote Alleyway {uid}"
    })
    assert create_res.status_code == 200
    cid = create_res.json()["complaint_id"]
    curr_status = create_res.json()["status"]

    # Update with note containing 'finished' while keeping current status
    res = client.put(f"/api/complaints/{cid}/status", json={
        "status": curr_status,
        "note": "Worker said work is finished and completed."
    })
    assert res.status_code == 200
    # Status remains unchanged and does not auto-jump
    assert res.json()["status"] == curr_status
    assert res.json()["status"] not in {"CLOSED", "RESOLUTION_SUBMITTED"}


def test_reopened_resume_work_lifecycle():
    """
    Tests:
    Citizen rejects -> REOPENED -> 'Resume Work' (REOPENED -> WORK_STARTED)
    -> Mark Work Completed -> RESOLVED_PENDING_CITIZEN -> Citizen confirms -> CLOSED
    """
    uid = uuid.uuid4().hex[:6]
    create_res = client.post("/api/complaints", data={
        "complaint_text": f"Broken pavement on Sector 7 walkway {uid}.",
        "location_text": f"Sector 7 Walkway {uid}",
        "citizen_name": "Deepak Sharma"
    })
    cid = create_res.json()["complaint_id"]

    # Progress to WORK_STARTED
    client.put(f"/api/complaints/{cid}/status", json={"status": "ACKNOWLEDGED"})
    client.put(f"/api/complaints/{cid}/status", json={"status": "ASSIGNED"})
    client.put(f"/api/complaints/{cid}/status", json={"status": "WORK_STARTED"})

    # Complete work initial attempt
    client.post(
        f"/api/admin/complaints/{cid}/complete-work",
        data={"completion_note": "Pavement tiles replaced."}
    )

    # Citizen rejects -> REOPENED
    reject_res = client.post(f"/api/complaints/{cid}/citizen-confirmation", json={
        "resolved": False,
        "comment": "Tiles are loose and wobbly."
    })
    assert reject_res.json()["status"] == "REOPENED"

    # Worker clicks 'Resume Work' -> REOPENED to WORK_STARTED
    resume_res = client.put(f"/api/complaints/{cid}/status", json={
        "status": "WORK_STARTED",
        "note": "Resume Work: Crew returned to site to cement the loose tiles."
    })
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "WORK_STARTED"

    # Worker marks work completed again
    comp_res2 = client.post(
        f"/api/admin/complaints/{cid}/complete-work",
        data={
            "completion_note": "All tiles re-cemented and fixed with quick-cure concrete.",
            "completed_by": "Masonry Unit 1"
        }
    )
    assert comp_res2.status_code == 200
    assert comp_res2.json()["status"] == "RESOLVED_PENDING_CITIZEN"

    # Citizen confirms
    confirm_res = client.post(f"/api/complaints/{cid}/citizen-confirmation", json={
        "resolved": True,
        "comment": "Perfect now, thank you!"
    })
    assert confirm_res.json()["status"] == "CLOSED"

