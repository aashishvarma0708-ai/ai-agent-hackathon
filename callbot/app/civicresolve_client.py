import os
import asyncio
from typing import Optional, Dict, Any

import httpx

from app.call_state import CallState


class CivicResolveError(RuntimeError):
    """Raised when the CivicResolve backend cannot complete an action."""


class CivicResolveClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: float = 20.0,
    ):
        configured_url = (
            base_url
            or os.getenv(
                "CIVICRESOLVE_API_URL",
                "http://127.0.0.1:8000",
            )
        )

        self.base_url = (
            configured_url
            .strip()
            .rstrip("/")
        )

        if not self.base_url:
            self.base_url = (
                "http://127.0.0.1:8000"
            )

        self.timeout_seconds = (
            timeout_seconds
        )


    # =====================================================
    # BASIC HEALTH CHECK
    # =====================================================

    async def health(
        self,
    ) -> Dict[str, Any]:

        url = (
            f"{self.base_url}"
            "/api/health"
        )

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
            ) as client:

                response = await client.get(
                    url
                )

        except httpx.RequestError as exc:
            raise CivicResolveError(
                "Could not reach CivicResolve "
                f"backend at {self.base_url}: "
                f"{exc}"
            ) from exc

        if response.status_code != 200:
            raise CivicResolveError(
                "CivicResolve health check "
                f"returned HTTP "
                f"{response.status_code}"
            )

        try:
            data = response.json()

        except Exception as exc:
            raise CivicResolveError(
                "CivicResolve health response "
                "was not valid JSON."
            ) from exc

        if data.get("status") != "ok":
            raise CivicResolveError(
                "CivicResolve backend did not "
                "report healthy status."
            )

        return data


    # =====================================================
    # BUILD COMPLAINT TEXT
    # =====================================================

    def build_complaint_text(
        self,
        state: CallState,
    ) -> str:

        issue = (
            state.issue
            or "civic issue"
        ).strip()

        location = (
            state.location
            or ""
        ).strip()

        parts = [
            f"Citizen reported {issue}"
        ]

        if location:
            parts.append(
                f"near {location}"
            )

        sentence = " ".join(
            parts
        ).strip()

        if not sentence.endswith("."):
            sentence += "."

        if state.safety_risk is True:
            sentence += (
                " The caller reported an "
                "immediate safety risk."
            )

        elif state.safety_risk is False:
            sentence += (
                " The caller reported no "
                "immediate safety risk."
            )

        if state.severity:
            sentence += (
                f" Reported severity: "
                f"{state.severity}."
            )

        return sentence


    # =====================================================
    # LANGUAGE MAPPING
    # =====================================================

    def language_hint(
        self,
        state: CallState,
    ) -> str:

        mapping = {
            "en": "English",
            "hi": "Hindi",
            "mixed": "Hinglish",
        }

        return mapping.get(
            state.language,
            "English",
        )


    # =====================================================
    # CREATE REAL CIVICRESOLVE COMPLAINT
    # =====================================================

    async def submit_complaint(
        self,
        state: CallState,
        citizen_name: str = "",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        citizen_phone: Optional[str] = None,
        notification_preference: Optional[str] = None,
        whatsapp_opt_in: Optional[bool] = None,
    ) -> Dict[str, Any]:

        if state.route != "municipal":
            raise CivicResolveError(
                "Only municipal complaints "
                "may be submitted to this "
                "callbot complaint flow."
            )

        if not state.confirmed:
            raise CivicResolveError(
                "Caller has not confirmed "
                "complaint submission."
            )

        if not state.issue:
            raise CivicResolveError(
                "Complaint issue is missing."
            )

        if not state.location:
            raise CivicResolveError(
                "Complaint location is missing."
            )

        if state.safety_risk is None:
            raise CivicResolveError(
                "Safety question has not "
                "been resolved."
            )

        # Prevent accidental duplicate POSTs
        # from the same call state.
        if state.submitted:
            if state.complaint_id:
                return {
                    "complaint_id":
                        state.complaint_id,

                    "already_submitted":
                        True,
                }

            raise CivicResolveError(
                "Call state says submitted "
                "but no complaint ID exists."
            )

        payload = {
            "complaint_text":
                self.build_complaint_text(
                    state
                ),

            "location_text":
                state.location,

            "latitude":
                latitude,

            "longitude":
                longitude,

            "citizen_name":
                citizen_name,

            "source_channel":
                "phone",

            "language_hint":
                self.language_hint(
                    state
                ),

            "citizen_phone":
                citizen_phone,

            "notification_preference":
                notification_preference or "none",

            "whatsapp_opt_in":
                bool(whatsapp_opt_in),
        }

        url = (
            f"{self.base_url}"
            "/api/complaints"
        )

        print(
            "\n🏛️ Submitting complaint "
            "to CivicResolve...",
            flush=True,
        )

        print(
            "📍 Location:",
            state.location,
            flush=True,
        )

        print(
            "🛣️ Issue:",
            state.issue,
            flush=True,
        )

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
            ) as client:

                response = await client.post(
                    url,
                    json=payload,
                )

        except httpx.RequestError as exc:
            raise CivicResolveError(
                "Could not reach CivicResolve "
                f"backend: {exc}"
            ) from exc

        if response.status_code not in {
            200,
            201,
        }:
            detail = ""

            try:
                body = response.json()
                detail = str(
                    body.get(
                        "detail",
                        body,
                    )
                )

            except Exception:
                detail = (
                    response.text[:300]
                )

            raise CivicResolveError(
                "CivicResolve rejected "
                "the complaint. "
                f"HTTP {response.status_code}. "
                f"{detail}"
            )

        try:
            result = response.json()

        except Exception as exc:
            raise CivicResolveError(
                "CivicResolve returned "
                "invalid JSON."
            ) from exc

        complaint_id = (
            result.get(
                "complaint_id"
            )
        )

        if not complaint_id:
            raise CivicResolveError(
                "CivicResolve returned success "
                "but no complaint_id."
            )

        # Only mark submitted AFTER
        # CivicResolve has actually succeeded.
        state.complaint_id = (
            str(complaint_id)
        )

        state.submitted = True

        print(
            "✅ CivicResolve complaint "
            "registered:",
            state.complaint_id,
            flush=True,
        )

        if (
            result.get(
                "duplicate_link_info"
            )
        ):
            print(
                "🔗 Complaint matched "
                "to an existing issue",
                flush=True,
            )

        return result


# =========================================================
# OPTIONAL COMMAND-LINE HEALTH TEST
# =========================================================

async def _test_health():
    client = CivicResolveClient()

    print(
        "Checking:",
        client.base_url,
    )

    result = await client.health()

    print(
        "✅ CivicResolve connection working"
    )

    print(
        "Status:",
        result.get("status"),
    )

    print(
        "App:",
        result.get("app"),
    )

    print(
        "Version:",
        result.get("version"),
    )

    print(
        "Demo mode:",
        result.get("demo_mode"),
    )


if __name__ == "__main__":
    asyncio.run(
        _test_health()
    )

