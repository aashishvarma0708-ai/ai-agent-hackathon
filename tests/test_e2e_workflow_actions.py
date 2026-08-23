import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from core.db import init_db, get_complaint, get_history, get_evidence

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_sequential_workflow_actions_happy_path():
    """
    Simulates the exact user actions on Authority Dashboard & Track page:
    1. Citizen submits grievance -> status: NEW
    2. Municipal officer clicks 'Acknowledge' -> status: ACKNOWLEDGED
    3. Municipal officer clicks 'Assign Work' -> status: ASSIGNED
    4. Municipal officer clicks 'Start Work' -> status: WORK_STARTED
    5. Municipal officer clicks 'Mark Work Completed' and submits note & photo
       -> status: RESOLUTION_SUBMITTED -> AI Verification -> RESOLVED_PENDING_CITIZEN
    6. Citizen tracks ticket and confirms resolution -> status: CLOSED
    """
    # 1. Citizen submission
    res = client.post("/api/complaints", data={
        "complaint_text": "Deep crater-like pothole outside St. Jude School causing motorcycle accidents.",
        "location_text": "St. Jude School Road, Ward 11",
        "citizen_name": "Aashish",
        "source_channel": "web"
    })
    assert res.status_code == 200
    cid = res.json()["complaint_id"]
    assert res.json()["status"] == "NEW"

    # 2. Officer clicks 'Acknowledge' (NEW -> ACKNOWLEDGED)
    ack_res = client.put(f"/api/complaints/{cid}/status", json={
        "status": "ACKNOWLEDGED",
        "note": "Acknowledge: Status updated to ACKNOWLEDGED via Municipal Action"
    })
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "ACKNOWLEDGED"

    # 3. Officer clicks 'Assign Work' (ACKNOWLEDGED -> ASSIGNED)
    assign_res = client.put(f"/api/complaints/{cid}/status", json={
        "status": "ASSIGNED",
        "note": "Assign Work: Status updated to ASSIGNED via Municipal Action"
    })
    assert assign_res.status_code == 200
    assert assign_res.json()["status"] == "ASSIGNED"

    # 4. Officer clicks 'Start Work' (ASSIGNED -> WORK_STARTED)
    start_res = client.put(f"/api/complaints/{cid}/status", json={
        "status": "WORK_STARTED",
        "note": "Start Work: Status updated to WORK_STARTED via Municipal Action"
    })
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "WORK_STARTED"

    # 5. Officer clicks 'Mark Work Completed' and submits completion modal
    fake_img = io.BytesIO(b"FAKE_AFTER_REPAIR_JPEG_BYTES")
    comp_res = client.post(
        f"/api/admin/complaints/{cid}/complete-work",
        data={
            "completion_note": "Pothole filled with hot-mix bitumen asphalt, compacted and leveled.",
            "completed_by": "Crew Chief David"
        },
        files={"resolution_image": ("after_repair.jpg", fake_img, "image/jpeg")}
    )
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["status"] == "RESOLVED_PENDING_CITIZEN"
    assert comp_data["ai_verification_result"]["appears_resolved"] is True

    # 6. Citizen confirms resolution (RESOLVED_PENDING_CITIZEN -> CLOSED)
    confirm_res = client.post(f"/api/complaints/{cid}/citizen-confirmation", json={
        "resolved": True,
        "comment": "Road is completely smooth now. Thank you!"
    })
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "CLOSED"

    # Verify audit history
    hist = get_history(cid)
    statuses = [h["new_status"] for h in hist]
    assert "ACKNOWLEDGED" in statuses
    assert "ASSIGNED" in statuses
    assert "WORK_STARTED" in statuses
    assert "RESOLUTION_SUBMITTED" in statuses
    assert "RESOLVED_PENDING_CITIZEN" in statuses
    assert "CLOSED" in statuses


def test_sequential_workflow_actions_reopened_path():
    """
    Simulates the rejection & resume work lifecycle:
    1. Intake -> NEW -> ACKNOWLEDGED -> ASSIGNED -> WORK_STARTED
    2. Complete work -> RESOLVED_PENDING_CITIZEN
    3. Citizen rejects resolution -> REOPENED
    4. Municipal officer sees 'Resume Work' button and clicks it -> WORK_STARTED
    5. Officer marks work completed again -> RESOLVED_PENDING_CITIZEN
    6. Citizen confirms -> CLOSED
    """
    res = client.post("/api/complaints", data={
        "complaint_text": "Water pipe rupture on 5th Main Road flooding street.",
        "location_text": "5th Main Road, Ward 04",
        "citizen_name": "Meera",
        "source_channel": "web"
    })
    cid = res.json()["complaint_id"]

    # Sequential progression
    client.put(f"/api/complaints/{cid}/status", json={"status": "ACKNOWLEDGED", "note": "Acknowledge"})
    client.put(f"/api/complaints/{cid}/status", json={"status": "ASSIGNED", "note": "Assign Work"})
    client.put(f"/api/complaints/{cid}/status", json={"status": "WORK_STARTED", "note": "Start Work"})

    # Complete work attempt 1
    fake_img = io.BytesIO(b"FAKE_AFTER_PIPE_REPAIR_BYTES")
    client.post(
        f"/api/admin/complaints/{cid}/complete-work",
        data={"completion_note": "Pipe patched with metal sleeve clamp."},
        files={"resolution_image": ("pipe_repair.jpg", fake_img, "image/jpeg")}
    )

    # Citizen rejects
    reject_res = client.post(f"/api/complaints/{cid}/citizen-confirmation", json={
        "resolved": False,
        "comment": "Water is still leaking around the clamp."
    })
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "REOPENED"

    # Officer clicks 'Resume Work' (REOPENED -> WORK_STARTED)
    resume_res = client.put(f"/api/complaints/{cid}/status", json={
        "status": "WORK_STARTED",
        "note": "Resume Work: Status updated to WORK_STARTED via Municipal Action"
    })
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "WORK_STARTED"

    # Complete work attempt 2
    comp_res2 = client.post(
        f"/api/admin/complaints/{cid}/complete-work",
        data={"completion_note": "Main pipe joint replaced with high-pressure reinforced coupling."},
        files={"resolution_image": ("pipe_coupling.jpg", fake_img, "image/jpeg")}
    )
    assert comp_res2.status_code == 200
    assert comp_res2.json()["status"] == "RESOLVED_PENDING_CITIZEN"

    # Citizen confirms
    confirm_res2 = client.post(f"/api/complaints/{cid}/citizen-confirmation", json={
        "resolved": True,
        "comment": "Leak has completely stopped. Great job!"
    })
    assert confirm_res2.status_code == 200
    assert confirm_res2.json()["status"] == "CLOSED"
