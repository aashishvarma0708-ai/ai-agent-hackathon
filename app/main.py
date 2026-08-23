import json
import os
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.db import init_db, get_complaint, list_complaints, update_status, get_history
from core.orchestrator import process_complaint
from core.voice import transcribe_audio

st.set_page_config(
    page_title="CivicResolve AI",
    page_icon="🏙️",
    layout="wide",
)

init_db()

st.title("🏙️ CivicResolve AI")
st.caption("One place to report. Intelligence to route. Accountability until resolution.")

tab_report, tab_voice, tab_track, tab_authority = st.tabs(
    ["📝 Report Issue", "🎙️ Voice Complaint", "🔎 Track", "🏛️ Authority Dashboard"]
)


def show_result(result):
    st.divider()

    if result["domain"] == "municipal":
        st.success(f"Complaint created: **{result['complaint_id']}**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Category", result["category"].replace("_", " ").title())
        c2.metric("Risk Score", f"{result['risk_score']}/100")
        c3.metric("Priority", result["priority"])
        c4.metric("SLA", f"{result['sla_hours']} h")

        st.write(f"**Department:** {result['department']}")
        st.write(f"**Summary:** {result['summary']}")
        st.write(f"**Location:** {result['location_text'] or 'Not confirmed'}")
        st.write(f"**AI confidence:** {round(result['confidence'] * 100)}%")

        if result.get("needs_clarification") or result["confidence"] < 0.55:
            st.warning(
                result.get("clarification_question")
                or "The complaint is uncertain. Citizen confirmation should be requested."
            )

        if result.get("duplicates"):
            st.warning(
                f"Probable duplicate(s) found: {', '.join(x['complaint_id'] for x in result['duplicates'][:3])}"
            )

        with st.expander("Why this priority?"):
            for r in result.get("risk_reasons", []):
                st.write("•", r)

    else:
        st.info(f"Case reference: **{result['complaint_id']}**")
        st.write(f"**Detected domain:** {result['domain'].replace('_', ' ').title()}")
        st.write(f"**Service type:** {result['service_type'].title()}")
        st.write(f"**Summary:** {result['summary']}")

        st.warning(
            "CivicResolve will not pretend this is a municipal complaint. "
            "It has routed the citizen to a configured verified public-service path."
        )

        st.write(f"**Recommended service:** {result.get('external_service_name', 'Human review')}")
        st.write(result.get("external_instruction", ""))

        url = result.get("external_service_url")
        if url:
            st.link_button("Open Official Service", url)

    with st.expander("🧠 Agent Activity"):
        for i, item in enumerate(result["agent_trace"], 1):
            st.write(f"{i}. {item}")


with tab_report:
    st.subheader("Submit a civic or public-service issue")
    st.caption("The AI first decides who actually owns the problem.")

    with st.form("report_form"):
        citizen_name = st.text_input("Name (optional)")
        complaint = st.text_area(
            "Describe the issue",
            height=130,
            placeholder="Example: Large pothole outside the school. Two bikes nearly crashed today.",
        )
        location = st.text_input(
            "Location / landmark",
            placeholder="Example: Main gate, Ward 12, Guntur",
        )
        image = st.file_uploader(
            "Upload evidence image (optional)",
            type=["jpg", "jpeg", "png", "webp"],
        )
        submitted = st.form_submit_button("Analyze & Submit", type="primary")

    if submitted:
        if not complaint.strip() and not image:
            st.error("Add a complaint description or an evidence image.")
        else:
            image_bytes = image.getvalue() if image else None
            image_mime = image.type if image else "image/jpeg"

            with st.spinner("CivicResolve is analyzing, triaging, scoring and routing..."):
                result = process_complaint(
                    complaint_text=complaint.strip() or "Citizen submitted image evidence without text.",
                    location_text=location,
                    source_channel="web",
                    citizen_name=citizen_name,
                    image_bytes=image_bytes,
                    image_mime=image_mime,
                )
            st.session_state["last_result"] = result
            show_result(result)


with tab_voice:
    st.subheader("Speak your complaint")
    st.caption(
        "Expo MVP: browser voice recording → speech-to-text → the same CivicResolve pipeline. "
        "Real phone calls can be added later without changing the core agent."
    )

    audio = st.audio_input("Record a voice complaint", sample_rate=16000)
    voice_location = st.text_input("Location / landmark for voice complaint")
    voice_image = st.file_uploader(
        "Optional image evidence",
        type=["jpg", "jpeg", "png", "webp"],
        key="voice_image",
    )

    if audio:
        st.audio(audio)

        if st.button("Transcribe & Process Voice Complaint", type="primary"):
            try:
                with st.spinner("Transcribing voice..."):
                    transcription = transcribe_audio(audio)

                st.success("Voice transcribed")
                st.write(f"**Detected language:** {transcription['language']}")
                st.text_area(
                    "Transcript",
                    value=transcription["text"],
                    height=100,
                    disabled=True,
                )

                image_bytes = voice_image.getvalue() if voice_image else None
                image_mime = voice_image.type if voice_image else "image/jpeg"

                with st.spinner("Running CivicResolve workflow..."):
                    result = process_complaint(
                        complaint_text=transcription["text"],
                        location_text=voice_location,
                        source_channel="voice",
                        image_bytes=image_bytes,
                        image_mime=image_mime,
                        language_hint=transcription["language"],
                    )
                st.session_state["last_result"] = result
                show_result(result)

            except Exception as e:
                st.error(f"Voice processing failed: {e}")


with tab_track:
    st.subheader("Track a complaint")
    complaint_id = st.text_input(
        "Complaint ID",
        placeholder="CR-260820-1234",
        key="track_id",
    )

    if st.button("Track Complaint"):
        row = get_complaint(complaint_id)
        if not row:
            st.error("Complaint ID not found.")
        else:
            st.success(f"{row['complaint_id']} — {row['status']}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Priority", row["priority"])
            c2.metric("Risk", row["risk_score"])
            c3.metric("Category", row["category"].replace("_", " ").title())
            st.write(f"**Summary:** {row['summary']}")
            st.write(f"**Location:** {row['location_text'] or 'Not available'}")
            st.write(f"**Department:** {row['department'] or row['external_service_name'] or 'Human review'}")

            history = get_history(row["complaint_id"])
            st.write("**Status history**")
            st.dataframe(history, use_container_width=True, hide_index=True)


with tab_authority:
    st.subheader("Authority Command Center")

    rows = list_complaints()
    municipal = [r for r in rows if r["domain"] == "municipal"]
    open_cases = [r for r in municipal if r["status"] not in {"CLOSED", "REJECTED"}]
    critical = [r for r in open_cases if r["priority"] == "CRITICAL"]
    external = [r for r in rows if r["status"] == "EXTERNALLY_ROUTED"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Cases", len(rows))
    m2.metric("Open Municipal", len(open_cases))
    m3.metric("Critical", len(critical))
    m4.metric("Externally Routed", len(external))

    if rows:
        display_rows = []
        for r in rows:
            display_rows.append({
                "ID": r["complaint_id"],
                "Domain": r["domain"],
                "Category": r["category"],
                "Priority": r["priority"],
                "Status": r["status"],
                "Department / Service": r["department"] or r["external_service_name"],
                "Location": r["location_text"],
            })
        st.dataframe(display_rows, use_container_width=True, hide_index=True)

        st.divider()
        st.write("### Update municipal case")

        ids = [r["complaint_id"] for r in municipal]
        if ids:
            selected = st.selectbox("Complaint", ids)
            new_status = st.selectbox(
                "New status",
                ["ACKNOWLEDGED", "ASSIGNED", "WORK_STARTED", "RESOLUTION_SUBMITTED", "CLOSED", "REOPENED"],
            )
            note = st.text_input("Status note")

            if st.button("Update Status"):
                if update_status(selected, new_status, note):
                    st.success(f"{selected} updated to {new_status}.")
                    st.rerun()
        else:
            st.info("No municipal complaints yet.")
    else:
        st.info("No complaints yet. Submit one from the Report Issue tab.")

st.divider()
st.caption(
    "Hackathon MVP. External service links are controlled by a verified directory; "
    "the language model is not allowed to invent government contacts."
)
