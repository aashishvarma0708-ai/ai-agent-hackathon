import json
import os
import re
from typing import Any, Dict, Optional

from twilio.rest import Client


class WhatsAppError(RuntimeError):
    """Raised when CivicResolve cannot send a WhatsApp message."""


def mask_phone(number: str) -> str:
    num = (number or "").strip()
    if num.startswith("whatsapp:"):
        prefix = "whatsapp:"
        num = num[len("whatsapp:"):]
    else:
        prefix = ""

    if len(num) <= 4:
        return f"{prefix}****"

    return f"{prefix}{'*' * max(0, len(num) - 4)}{num[-4:]}"


def normalize_whatsapp_phone(number: str) -> str:
    """
    Normalizes a destination phone number to Twilio WhatsApp format:
    'whatsapp:+919876543210'
    """
    number = (number or "").strip()
    if number.startswith("whatsapp:"):
        number = number[len("whatsapp:"):]

    number = re.sub(r"[\s\-\(\)\.]", "", number)

    if re.fullmatch(r"[6-9]\d{9}", number):
        number = f"+91{number}"
    elif re.fullmatch(r"0[6-9]\d{9}", number):
        number = f"+91{number[1:]}"
    elif re.fullmatch(r"91[6-9]\d{9}", number):
        number = f"+{number}"

    if not re.fullmatch(r"\+[1-9]\d{6,14}", number):
        raise WhatsAppError(
            f"Invalid WhatsApp destination number: '{number}'. "
            "Please provide a valid 10-digit mobile number or international E.164 format (e.g. +919876543210)."
        )

    return f"whatsapp:{number}"


class CivicResolveWhatsApp:
    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
        sandbox_mode: Optional[bool] = None,
    ):
        self.account_sid = (
            account_sid
            or os.getenv("TWILIO_ACCOUNT_SID", "")
        ).strip()

        self.auth_token = (
            auth_token
            or os.getenv("TWILIO_AUTH_TOKEN", "")
        ).strip()

        raw_from = (
            from_number
            or os.getenv("TWILIO_WHATSAPP_FROM", "")
            or os.getenv("TWILIO_PHONE_NUMBER", "")
        ).strip()

        if raw_from and not raw_from.startswith("whatsapp:"):
            self.from_number = f"whatsapp:{raw_from}"
        else:
            self.from_number = raw_from

        if sandbox_mode is not None:
            self.sandbox_mode = sandbox_mode
        else:
            self.sandbox_mode = os.getenv("WHATSAPP_SANDBOX_MODE", "true").strip().lower() in {"true", "1", "yes"}

        self.call_content_sid = os.getenv("TWILIO_WHATSAPP_CALL_CONTENT_SID", "").strip()
        self.track_content_sid = os.getenv("TWILIO_WHATSAPP_TRACK_CONTENT_SID", "").strip()

        if not self.account_sid:
            raise WhatsAppError("TWILIO_ACCOUNT_SID is missing.")

        if not self.auth_token:
            raise WhatsAppError("TWILIO_AUTH_TOKEN is missing.")

        if not self.from_number:
            raise WhatsAppError("TWILIO_WHATSAPP_FROM is missing.")

        self.client = Client(
            self.account_sid,
            self.auth_token,
        )

    def send_message(
        self,
        to_number: str,
        body: Optional[str] = None,
        content_sid: Optional[str] = None,
        content_variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        recipient = normalize_whatsapp_phone(to_number)

        print(
            "💬 Sending CivicResolve WhatsApp to",
            mask_phone(recipient),
            flush=True,
        )

        create_kwargs: Dict[str, Any] = {
            "from_": self.from_number,
            "to": recipient,
        }

        # Template Mode vs Sandbox/Free-form Mode
        if content_sid:
            create_kwargs["content_sid"] = content_sid
            if content_variables:
                create_kwargs["content_variables"] = json.dumps(content_variables)
        elif body and body.strip():
            create_kwargs["body"] = body.strip()
        else:
            raise WhatsAppError("Either WhatsApp body or ContentSid must be provided.")

        try:
            message = self.client.messages.create(**create_kwargs)
        except Exception as exc:
            raise WhatsAppError(
                f"Twilio WhatsApp failed: {type(exc).__name__}: {exc}"
            ) from exc

        print(
            "✅ Twilio accepted WhatsApp message:",
            message.sid,
            flush=True,
        )

        return {
            "sid": message.sid,
            "status": getattr(message, "status", None),
            "to": recipient,
        }

    def send_complaint_links(
        self,
        to_number: str,
        complaint_id: str,
        evidence_url: Optional[str] = None,
        tracking_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        cid = (complaint_id or "").strip()
        if not cid:
            raise WhatsAppError("Complaint ID is required.")

        has_evidence = bool(evidence_url and str(evidence_url).strip())
        has_tracking = bool(tracking_url and str(tracking_url).strip())

        # Check if Production Template ContentSid is available and configured
        if not self.sandbox_mode:
            if has_evidence and self.call_content_sid:
                return self.send_message(
                    to_number=to_number,
                    content_sid=self.call_content_sid,
                    content_variables={
                        "1": cid,
                        "2": str(evidence_url).strip(),
                        "3": str(tracking_url or "").strip(),
                    }
                )
            elif has_tracking and self.track_content_sid:
                return self.send_message(
                    to_number=to_number,
                    content_sid=self.track_content_sid,
                    content_variables={
                        "1": cid,
                        "2": str(tracking_url).strip(),
                    }
                )

        # Sandbox / Development Free-form Message
        body_parts = [
            "CivicResolve AI\n",
            f"Your complaint {cid} has been registered."
        ]

        if has_evidence:
            body_parts.append(f"\nAdd optional photo/location:\n{str(evidence_url).strip()}")

        if has_tracking:
            body_parts.append(f"\nTrack your complaint:\n{str(tracking_url).strip()}")

        body = "\n".join(body_parts)
        return self.send_message(to_number=to_number, body=body)
