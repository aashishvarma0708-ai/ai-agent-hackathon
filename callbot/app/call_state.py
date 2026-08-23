from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CallState:
    # Twilio
    call_sid: Optional[str] = None
    stream_sid: Optional[str] = None

    # Public-service routing
    route: str = "unknown"
    route_reason: Optional[str] = None

    # Complaint information
    issue: Optional[str] = None
    location: Optional[str] = None
    severity: Optional[str] = None
    safety_risk: Optional[bool] = None

    # Conversation gates
    awaiting_safety_answer: bool = False
    awaiting_confirmation: bool = False
    awaiting_evidence_permission: bool = False

    # Complaint submission
    confirmed: bool = False
    submitted: bool = False
    complaint_id: Optional[str] = None

    # Photo/location evidence
    evidence_opt_in: Optional[bool] = None
    evidence_link_sent: bool = False

    # Conversation metadata
    language: str = "en"
    turn_count: int = 0
    last_user_text: str = ""
    last_bot_text: str = ""

    history: list = field(
        default_factory=list
    )

    def add_history(
        self,
        role: str,
        content: str,
    ):
        self.history.append(
            {
                "role": role,
                "content": content,
            }
        )

        # Keep the phone conversation small
        # and inexpensive for the LLM.
        self.history = self.history[-12:]

    def ready_for_confirmation(
        self,
    ) -> bool:
        return (
            self.route == "municipal"
            and bool(self.issue)
            and bool(self.location)
            and self.safety_risk is not None
        )

    def ready_to_submit(
        self,
    ) -> bool:
        return (
            self.ready_for_confirmation()
            and self.confirmed
            and not self.submitted
        )

    def complaint_summary(
        self,
    ) -> str:
        parts = []

        if self.issue:
            parts.append(
                f"issue: {self.issue}"
            )

        if self.location:
            parts.append(
                f"location: {self.location}"
            )

        if self.severity:
            parts.append(
                f"severity: {self.severity}"
            )

        if self.safety_risk is True:
            parts.append(
                "there is an immediate safety risk"
            )

        elif self.safety_risk is False:
            parts.append(
                "there is no immediate safety risk"
            )

        return ", ".join(parts)

    def natural_summary(
        self,
    ) -> str:
        issue = (
            self.issue
            or "civic issue"
        )

        location = (
            self.location
            or "the reported location"
        )

        summary = (
            (
                f"{issue} {location}"
                if location.lower().startswith("near ")
                else f"{issue} near {location}"
            )
        )

        if self.safety_risk is True:
            summary += (
                " that is creating an "
                "immediate safety risk"
            )

        elif self.safety_risk is False:
            summary += (
                " with no immediate "
                "safety risk reported"
            )

        return summary

    def prompt_context(
        self,
    ) -> str:
        return str(
            {
                "route":
                    self.route,

                "issue":
                    self.issue,

                "location":
                    self.location,

                "severity":
                    self.severity,

                "safety_risk":
                    self.safety_risk,

                "awaiting_safety_answer":
                    self.awaiting_safety_answer,

                "awaiting_confirmation":
                    self.awaiting_confirmation,

                "confirmed":
                    self.confirmed,

                "submitted":
                    self.submitted,

                "awaiting_evidence_permission":
                    self.awaiting_evidence_permission,

                "evidence_opt_in":
                    self.evidence_opt_in,

                "evidence_link_sent":
                    self.evidence_link_sent,

                "language":
                    self.language,
            }
        )

    def to_dict(
        self,
    ) -> dict:
        return {
            "call_sid":
                self.call_sid,

            "stream_sid":
                self.stream_sid,

            "route":
                self.route,

            "route_reason":
                self.route_reason,

            "issue":
                self.issue,

            "location":
                self.location,

            "severity":
                self.severity,

            "safety_risk":
                self.safety_risk,

            "awaiting_safety_answer":
                self.awaiting_safety_answer,

            "awaiting_confirmation":
                self.awaiting_confirmation,

            "confirmed":
                self.confirmed,

            "submitted":
                self.submitted,

            "complaint_id":
                self.complaint_id,

            "awaiting_evidence_permission":
                self.awaiting_evidence_permission,

            "evidence_opt_in":
                self.evidence_opt_in,

            "evidence_link_sent":
                self.evidence_link_sent,

            "language":
                self.language,

            "turn_count":
                self.turn_count,
        }
