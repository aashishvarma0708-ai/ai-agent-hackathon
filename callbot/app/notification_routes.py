import asyncio
import os
import secrets
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.sms_sender import CivicResolveSMS, SMSError
from app.whatsapp_sender import CivicResolveWhatsApp, WhatsAppError

router = APIRouter()


class NotificationRequest(BaseModel):
    complaint_id: str
    phone_number: str
    notification_preference: str = "none"  # none, sms, whatsapp, both
    whatsapp_opt_in: bool = False
    tracking_token: Optional[str] = None
    evidence_url: Optional[str] = None


def get_public_app_url() -> str:
    host = os.getenv("PUBLIC_HOST", "127.0.0.1:8001").strip()
    for prefix in ("https://", "http://", "wss://", "ws://"):
        if host.startswith(prefix):
            host = host[len(prefix):]
    host = host.rstrip("/")

    # If running locally without HTTPS, default appropriately
    scheme = "https" if ("." in host and not host.startswith("127.0.0.1") and not host.startswith("localhost")) else "http"
    return f"{scheme}://{host}"


@router.post("/internal/notify")
async def internal_notify(
    payload: NotificationRequest,
    x_notification_secret: Optional[str] = Header(None, alias="X-Notification-Secret"),
    authorization: Optional[str] = Header(None),
):
    """
    Secure internal citizen notification dispatch endpoint.
    Protected by shared secret authentication.
    """
    expected_secret = os.getenv("NOTIFICATION_SHARED_SECRET", "cr_notify_secret_2026").strip()

    # Extract submitted secret from X-Notification-Secret or Authorization header
    submitted_secret = x_notification_secret
    if not submitted_secret and authorization:
        if authorization.startswith("Bearer "):
            submitted_secret = authorization[len("Bearer "):].strip()
        else:
            submitted_secret = authorization.strip()

    if not submitted_secret or not secrets.compare_digest(submitted_secret, expected_secret):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized. Invalid or missing notification secret."
        )

    cid = payload.complaint_id.strip().upper()
    phone = payload.phone_number.strip()
    pref = payload.notification_preference.strip().lower()
    wa_opt_in = payload.whatsapp_opt_in
    token = payload.tracking_token

    if not phone or pref == "none":
        return {
            "status": "skipped",
            "complaint_id": cid,
            "sms_status": "skipped",
            "whatsapp_status": "skipped",
            "message": "No phone number or notification preference is 'none'."
        }

    base_url = get_public_app_url()
    tracking_url = f"{base_url}/track/{token}" if token else None
    evidence_url = payload.evidence_url

    sms_status = "skipped"
    whatsapp_status = "skipped"
    sms_error = None
    whatsapp_error = None

    async def _send_sms():
        nonlocal sms_status, sms_error
        try:
            sms = CivicResolveSMS()
            await asyncio.to_thread(
                sms.send_complaint_links,
                phone,
                cid,
                evidence_url,
                tracking_url,
            )
            sms_status = "sent"
        except Exception as exc:
            sms_status = "failed"
            sms_error = str(exc)
            print(f"❌ SMS notification failed for {cid}: {exc}", flush=True)

    async def _send_whatsapp():
        nonlocal whatsapp_status, whatsapp_error
        if not wa_opt_in:
            whatsapp_status = "skipped_no_opt_in"
            return

        try:
            wa = CivicResolveWhatsApp()
            await asyncio.to_thread(
                wa.send_complaint_links,
                phone,
                cid,
                evidence_url,
                tracking_url,
            )
            whatsapp_status = "sent"
        except Exception as exc:
            whatsapp_status = "failed"
            whatsapp_error = str(exc)
            print(f"❌ WhatsApp notification failed for {cid}: {exc}", flush=True)

    tasks = []
    if pref in {"sms", "both"}:
        tasks.append(_send_sms())
    if pref in {"whatsapp", "both"}:
        tasks.append(_send_whatsapp())

    if tasks:
        # Isolate failures across channels
        await asyncio.gather(*tasks, return_exceptions=True)

    return {
        "status": "processed",
        "complaint_id": cid,
        "sms_status": sms_status,
        "whatsapp_status": whatsapp_status,
        "sms_error": sms_error,
        "whatsapp_error": whatsapp_error,
    }
