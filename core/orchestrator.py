import secrets
import base64
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from .agent import analyze_complaint
from .location import parse_location
from .risk import calculate_risk
from .routing import route_municipal_issue
from .services import get_external_service
from .duplicates import evaluate_duplicate
from .sla import get_sla_hours, calculate_sla_deadline, evaluate_sla_state
from .db import (
    save_complaint, 
    get_complaint, 
    add_supporting_report, 
    save_evidence
)


def generate_complaint_id() -> str:
    date_part = datetime.now(timezone.utc).strftime("%y%m%d")
    random_part = secrets.randbelow(9000) + 1000
    return f"CR-{date_part}-{random_part}"


def process_complaint(
    complaint_text: str,
    location_text: str = "",
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    source_channel: str = "web",
    citizen_name: str = "",
    image_bytes: Optional[bytes] = None,
    image_mime: str = "image/jpeg",
    language_hint: str = "",
) -> Dict[str, Any]:
    """
    Main CivicResolve AI Orchestrator.
    Coordinates AI interpretation, location intelligence, duplicate detection,
    deterministic risk scoring, and SLA assignment.
    """
    trace = [f"Received complaint from channel: {source_channel.upper()}"]

    # 1. AI Multimodal Fact Extraction (Separate from deterministic enforcement)
    analysis, used_ai = analyze_complaint(
        complaint_text,
        image_bytes=image_bytes,
        image_mime=image_mime,
    )
    trace.append("AI multimodal entity extraction completed" if used_ai else "Deterministic fallback analyzer applied")

    # 2. Location Intelligence & Coordinate Normalization
    raw_loc = location_text.strip() or analysis.get("location_text", "")
    loc_data = parse_location(raw_loc, latitude=latitude, longitude=longitude)
    trace.append(f"Location normalized: {loc_data['jurisdiction']} ({'Verified' if loc_data['location_verified'] else 'Citizen landmark'})")

    # 3. Language Handling
    lang = language_hint.strip() or analysis.get("language", "English")
    if lang.lower() != "english":
        trace.append(f"Language identified: {lang} (Preserved original text + translated)")

    # 4. Domain Separation Guardrails
    domain = analysis.get("domain", "municipal")
    service_type = analysis.get("service_type", "municipal")
    category = analysis.get("category", "roads")
    summary = analysis.get("summary", "") or complaint_text[:140]

    # Process image URL representation if uploaded
    initial_img_url = ""
    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        initial_img_url = f"data:{image_mime};base64,{b64}"

    # 5. MUNICIPAL DOMAIN PIPELINE
    if domain == "municipal":
        trace.append(f"Public-service triage → MUNICIPAL domain [{category.upper()}]")

        # Duplicate Detection Engine
        dup_eval = evaluate_duplicate(
            category=category,
            complaint_text=complaint_text,
            location_text=loc_data["address"],
            latitude=loc_data["latitude"],
            longitude=loc_data["longitude"],
            threshold=0.68
        )

        # If duplicate detected, link report to primary parent complaint
        if dup_eval["duplicate"] and dup_eval["matched_complaint_id"]:
            parent_id = dup_eval["matched_complaint_id"]
            sim_score = dup_eval["similarity"]
            trace.append(f"⚠️ Probable duplicate detected (Similarity {int(sim_score * 100)}% with {parent_id})")
            trace.append(f"Linked as supporting report to existing primary complaint: {parent_id}")

            add_supporting_report(
                parent_complaint_id=parent_id,
                citizen_name=citizen_name or "Anonymous Citizen",
                complaint_text=complaint_text,
                location_text=loc_data["address"],
                source_channel=source_channel,
                image_url=initial_img_url,
                similarity=sim_score
            )

            parent_complaint = get_complaint(parent_id)
            if parent_complaint:
                # Re-score risk on parent with updated report count
                updated_count = parent_complaint.get("report_count", 2)
                re_risk = calculate_risk(
                    category=parent_complaint.get("category", category),
                    text=parent_complaint.get("complaint_text", ""),
                    location_text=parent_complaint.get("location_text", ""),
                    duplicate_count=updated_count
                )
                trace.append(f"Primary complaint risk boosted to {re_risk['score']}/100 based on {updated_count} citizen reports")
                
                parent_complaint["agent_trace"] = trace
                parent_complaint["duplicate_link_info"] = {
                    "is_duplicate": True,
                    "primary_complaint_id": parent_id,
                    "similarity": sim_score,
                    "report_count": updated_count,
                    "message": f"This grievance was matched with existing complaint {parent_id} and registered as a supporting report."
                }
                return parent_complaint

        # New Independent Municipal Issue
        complaint_id = generate_complaint_id()
        trace.append(f"Duplicate scan cleared. Generating new Ticket ID: {complaint_id}")

        # Deterministic Risk Engine
        risk = calculate_risk(
            category=category,
            text=complaint_text,
            location_text=loc_data["address"],
            indicators=analysis.get("severity_indicators", []),
            duplicate_count=0
        )
        trace.append(f"Deterministic risk engine → {risk['score']}/100 [{risk['priority']}]")

        # Routing & Department Dispatch
        route = route_municipal_issue(category)
        department = route["department"]
        sla_hours = get_sla_hours(category, risk["priority"])
        created_at_now = datetime.now(timezone.utc).isoformat()
        sla_deadline = calculate_sla_deadline(created_at_now, sla_hours)

        trace.append(f"Routing lookup → {department}")
        trace.append(f"SLA locked → {sla_hours} hours (Deadline: {sla_deadline[:16].replace('T', ' ')})")

        complaint_obj = {
            "complaint_id": complaint_id,
            "source_channel": source_channel,
            "citizen_name": citizen_name or "Anonymous Citizen",
            "complaint_text": complaint_text,
            "location_text": loc_data["address"],
            "latitude": loc_data["latitude"],
            "longitude": loc_data["longitude"],
            "location_verified": loc_data["location_verified"],
            "jurisdiction": loc_data["jurisdiction"],
            "language": lang,
            "domain": "municipal",
            "service_type": "municipal",
            "category": category,
            "subcategory": analysis.get("subcategory", "general_works"),
            "summary": summary,
            "confidence": analysis.get("confidence", 0.92),
            "risk_score": risk["score"],
            "priority": risk["priority"],
            "risk_reasons": risk["reasons"],
            "department": department,
            "sla_hours": sla_hours,
            "sla_deadline": sla_deadline,
            "sla_state": "ON_TRACK",
            "escalation_level": 0,
            "simulated_hours_offset": 0,
            "report_count": 1,
            "status": "NEW",
            "external_service_name": "",
            "external_service_url": "",
            "initial_image_url": initial_img_url,
            "created_at": created_at_now,
            "agent_trace": trace,
        }

        save_complaint(complaint_obj)
        if initial_img_url:
            save_evidence(complaint_id, "INITIAL", initial_img_url, "Citizen uploaded photo evidence")

        trace.append("Complaint saved to SQLite with SLA timeline tracking")
        complaint_obj["agent_trace"] = trace
        return complaint_obj

    # 6. EXTERNAL PUBLIC SERVICE & EMERGENCY PIPELINE
    else:
        complaint_id = generate_complaint_id()
        service = get_external_service(service_type)
        is_emergency = domain == "emergency"
        created_at_now = datetime.now(timezone.utc).isoformat()

        trace.append(f"Domain separation guardrail → Non-municipal [{domain.upper()} / {service_type.upper()}]")
        trace.append(f"Mapped to verified national directory → {service['name']}")
        trace.append(f"Official portal attached: {service['url']}")

        complaint_obj = {
            "complaint_id": complaint_id,
            "source_channel": source_channel,
            "citizen_name": citizen_name or "Anonymous Citizen",
            "complaint_text": complaint_text,
            "location_text": loc_data["address"],
            "latitude": loc_data["latitude"],
            "longitude": loc_data["longitude"],
            "location_verified": loc_data["location_verified"],
            "jurisdiction": loc_data["jurisdiction"],
            "language": lang,
            "domain": domain,
            "service_type": service_type,
            "category": "unknown",
            "subcategory": f"{service_type}_referral",
            "summary": summary,
            "confidence": analysis.get("confidence", 0.95),
            "risk_score": 99 if is_emergency else 0,
            "priority": "CRITICAL" if is_emergency else "EXTERNAL",
            "risk_reasons": ["Urgent public safety referral"] if is_emergency else ["Routed to external national authority"],
            "department": service["name"],
            "sla_hours": 1 if is_emergency else 0,
            "sla_deadline": calculate_sla_deadline(created_at_now, 1 if is_emergency else 0),
            "sla_state": "ON_TRACK",
            "escalation_level": 0,
            "simulated_hours_offset": 0,
            "report_count": 1,
            "status": "EMERGENCY_DISPATCHED" if is_emergency else "EXTERNALLY_ROUTED",
            "external_service_name": service["name"],
            "external_service_url": service["url"],
            "external_instruction": service["instruction"],
            "external_scope": service["verified_scope"],
            "initial_image_url": initial_img_url,
            "created_at": created_at_now,
            "agent_trace": trace,
        }

        save_complaint(complaint_obj)
        trace.append(f"External grievance registered with Tracking ID: {complaint_id}")
        complaint_obj["agent_trace"] = trace
        return complaint_obj
