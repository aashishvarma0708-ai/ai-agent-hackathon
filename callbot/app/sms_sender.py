import os
import re
from typing import Any, Dict, Optional

from twilio.rest import Client


class SMSError(RuntimeError):
    """Raised when CivicResolve cannot send an SMS."""


def mask_phone(number: str) -> str:
    number = (number or "").strip()

    if len(number) <= 4:
        return "****"

    return "*" * max(0, len(number) - 4) + number[-4:]


def normalize_phone(number: str) -> str:
    """
    Require international E.164-style numbers or Indian 10-digit numbers.

    Example:
        +919876543210 or 9876543210 -> +919876543210
    """
    number = (number or "").strip()
    number = re.sub(r"[\s\-\(\)\.]", "", number)

    if re.fullmatch(r"[6-9]\d{9}", number):
        return f"+91{number}"

    if re.fullmatch(r"0[6-9]\d{9}", number):
        return f"+91{number[1:]}"

    if re.fullmatch(r"91[6-9]\d{9}", number):
        return f"+{number}"

    if not re.fullmatch(r"\+[1-9]\d{6,14}", number):
        raise SMSError(
            "Recipient phone number must use international "
            "format, for example +919876543210."
        )

    return number


class CivicResolveSMS:
    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
    ):
        self.account_sid = (
            account_sid
            or os.getenv("TWILIO_ACCOUNT_SID", "")
        ).strip()

        self.auth_token = (
            auth_token
            or os.getenv("TWILIO_AUTH_TOKEN", "")
        ).strip()

        self.from_number = (
            from_number
            or os.getenv("TWILIO_PHONE_NUMBER", "")
        ).strip()

        if not self.account_sid:
            raise SMSError(
                "TWILIO_ACCOUNT_SID is missing."
            )

        if not self.auth_token:
            raise SMSError(
                "TWILIO_AUTH_TOKEN is missing."
            )

        if not self.from_number:
            raise SMSError(
                "TWILIO_PHONE_NUMBER is missing."
            )

        self.client = Client(
            self.account_sid,
            self.auth_token,
        )


    def send_message(
        self,
        to_number: str,
        body: str,
    ) -> Dict[str, Any]:

        recipient = normalize_phone(
            to_number
        )

        body = (body or "").strip()

        if not body:
            raise SMSError(
                "SMS body cannot be empty."
            )

        print(
            "📨 Sending CivicResolve SMS to",
            mask_phone(recipient),
            flush=True,
        )

        try:
            message = self.client.messages.create(
                body=body,
                from_=self.from_number,
                to=recipient,
            )

        except Exception as exc:
            raise SMSError(
                f"Twilio SMS failed: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        print(
            "✅ Twilio accepted SMS:",
            message.sid,
            flush=True,
        )

        return {
            "sid": message.sid,
            "status": getattr(
                message,
                "status",
                None,
            ),
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
            raise SMSError("Complaint ID is required.")

        body_parts = [f"CivicResolve\n\nComplaint {cid} has been registered."]

        if evidence_url and str(evidence_url).strip():
            body_parts.append(f"\nAdd optional evidence:\n{str(evidence_url).strip()}")

        if tracking_url and str(tracking_url).strip():
            body_parts.append(f"\nTrack your complaint:\n{str(tracking_url).strip()}")

        body = "\n".join(body_parts)
        return self.send_message(to_number, body)


    def send_evidence_link(
        self,
        to_number: str,
        complaint_id: str,
        evidence_url: str,
    ) -> Dict[str, Any]:

        complaint_id = (
            complaint_id or ""
        ).strip()

        evidence_url = (
            evidence_url or ""
        ).strip()

        if not complaint_id:
            raise SMSError(
                "Complaint ID is required."
            )

        if not evidence_url.startswith(
            "https://"
        ):
            raise SMSError(
                "Evidence URL must use HTTPS."
            )

        body = (
            "CivicResolve: Your complaint "
            f"{complaint_id} has been registered. "
            "You may optionally add a photo and "
            "precise location using this secure link: "
            f"{evidence_url}"
        )

        return self.send_message(
            to_number,
            body,
        )
